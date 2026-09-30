"""Shared, path-confined application service for CLI and MCP operations."""
from __future__ import annotations

import logging
import hashlib
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from libriscribe.agents.project_manager import ProjectManagerAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.narrative.invariant_checker import InvariantChecker
from libriscribe.narrative.models import NarrativeGraph
from libriscribe.settings import Settings
from libriscribe.utils.project_status import ProjectWriteBusy, load_project_status, project_write_lock, save_project_status, update_operation_status
from libriscribe.workflow_state import inspect_project_progress

logger = logging.getLogger(__name__)

_PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,99}$")
_WRITE_LOCKS: dict[str, threading.Lock] = {}
_WRITE_LOCKS_GUARD = threading.Lock()
_MAX_CHAPTER_CHARS = 20_000
_MAX_MANUAL_EDIT_CHARS = 100_000


class ServiceError(Exception):
    """Expected service failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _project_lock(project_path: Path) -> threading.Lock:
    key = str(project_path)
    with _WRITE_LOCKS_GUARD:
        return _WRITE_LOCKS.setdefault(key, threading.Lock())


def _revision_token(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class LibriScribeService:
    """Owns project validation, workflow calls, and bounded structured results."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        configured_root = Path(self.settings.projects_dir).expanduser()
        if not configured_root.is_absolute():
            # Relative configuration is anchored to the installed package/repository,
            # never to whichever directory happened to launch an MCP client.
            configured_root = Path(__file__).resolve().parents[2] / configured_root
        self.projects_root = configured_root.resolve()

    def _resolve_project(self, project: str) -> tuple[Path, ProjectKnowledgeBase]:
        if not isinstance(project, str) or not project.strip():
            raise ServiceError("invalid_project", "Project identifier must not be empty.")
        if (
            project in {".", ".."}
            or not _PROJECT_ID.fullmatch(project)
            or "/" in project
            or "\\" in project
            or Path(project).is_absolute()
        ):
            raise ServiceError("invalid_project", "Project must be a simple project identifier.")
        try:
            candidate = (self.projects_root / project).resolve(strict=True)
            candidate.relative_to(self.projects_root)
        except (OSError, ValueError):
            raise ServiceError("project_not_found", f"Project '{project}' was not found under the configured projects directory.") from None
        if not candidate.is_dir():
            raise ServiceError("project_not_found", f"Project '{project}' was not found under the configured projects directory.")
        data_path = candidate / "project_data.json"
        try:
            data_resolved = data_path.resolve(strict=True)
            data_resolved.relative_to(candidate)
        except (OSError, ValueError):
            raise ServiceError("project_not_found", f"Project '{project}' has no accessible project_data.json.") from None
        kb = ProjectKnowledgeBase.load_from_file(str(data_resolved))
        if kb is None:
            raise ServiceError("invalid_project_data", f"Project '{project}' metadata could not be loaded.")
        self._validate_project_entries(candidate)
        # The metadata name is not trusted as a path. Normalize it to the selected folder.
        kb.project_name = project
        kb.project_dir = candidate
        return candidate, kb

    @staticmethod
    def _validate_project_entries(project_path: Path) -> None:
        """Reject links that let project workflows inspect another directory."""
        try:
            for entry in project_path.iterdir():
                try:
                    resolved = entry.resolve(strict=True)
                    resolved.relative_to(project_path)
                except (OSError, ValueError):
                    raise ServiceError(
                        "project_escape",
                        "The project contains a broken link or an entry that resolves outside the selected project directory.",
                    ) from None
        except OSError:
            raise ServiceError("project_unavailable", "The selected project directory could not be inspected safely.") from None

    def _manager(self, project: str, *, llm: bool = False) -> tuple[ProjectManagerAgent, Path, ProjectKnowledgeBase]:
        path, kb = self._resolve_project(project)
        manager = ProjectManagerAgent()
        manager.settings = self.settings
        manager.project_dir = path
        manager.project_knowledge_base = kb
        manager._service_write_lock_held = llm
        if llm:
            try:
                manager.initialize_llm_client(kb.llm_provider, kb.model)
            except Exception:
                logger.exception("Could not initialize project provider")
                raise ServiceError("provider_failure", "Could not initialize the configured provider.") from None
        return manager, path, kb

    @staticmethod
    def _positive_chapter(chapter_number: int) -> int:
        if isinstance(chapter_number, bool) or not isinstance(chapter_number, int) or chapter_number < 1:
            raise ServiceError("invalid_argument", "chapter_number must be a positive integer.")
        return chapter_number

    @staticmethod
    def _check_chapter_range(kb: ProjectKnowledgeBase, chapter_number: int) -> None:
        # Respect an explicitly configured range/count. Otherwise the outline may
        # define the actual count and the model default of one is not authoritative.
        if kb.num_chapters_str:
            configured = kb.num_chapters
            maximum = max(configured) if isinstance(configured, tuple) else configured
            if isinstance(maximum, int) and maximum > 0 and chapter_number > maximum:
                raise ServiceError("invalid_argument", f"chapter_number exceeds the configured maximum ({maximum}).")

    @staticmethod
    def _validate_project_identifier(project: str) -> None:
        if (
            not isinstance(project, str)
            or project in {".", ".."}
            or not _PROJECT_ID.fullmatch(project)
            or "/" in project
            or "\\" in project
            or Path(project).is_absolute()
        ):
            raise ServiceError("invalid_project", "Project must be a simple project identifier (1–100 letters, numbers, spaces, dots, underscores, or hyphens).")

    def create_project(
        self,
        project: str,
        title: str,
        description: str = "",
        category: str = "Fiction",
        genre: str = "Unknown Genre",
        language: str = "English",
        chapter_count: int = 1,
        llm_provider: str = "openai",
        model: str = "",
    ) -> dict[str, Any]:
        """Create a usable local project without initializing or calling an LLM."""
        self._validate_project_identifier(project)
        for field, value, maximum in (
            ("title", title, 300), ("description", description, 5_000),
            ("category", category, 100), ("genre", genre, 200),
            ("language", language, 100), ("llm_provider", llm_provider, 100),
            ("model", model, 200),
        ):
            if not isinstance(value, str) or len(value) > maximum or not value.strip():
                if field in {"description", "model"} and isinstance(value, str) and not value.strip():
                    continue
                raise ServiceError("invalid_argument", f"{field} must be a nonempty string of at most {maximum} characters.")
        if isinstance(chapter_count, bool) or not isinstance(chapter_count, int) or not 1 <= chapter_count <= 500:
            raise ServiceError("invalid_argument", "chapter_count must be an integer from 1 to 500.")
        try:
            self.projects_root.mkdir(parents=True, exist_ok=True)
            root = self.projects_root.resolve(strict=True)
            if not root.is_dir():
                raise OSError("projects root is not a directory")
            target = root / project
            if target.exists() or target.is_symlink():
                raise ServiceError("project_exists", f"Project '{project}' already exists; no files were changed.")
            temporary = Path(tempfile.mkdtemp(prefix=".libriscribe-create-", dir=root))
            target_created = False
            try:
                kb = ProjectKnowledgeBase(
                    project_name=project,
                    title=title.strip(),
                    description=description.strip() or "No description provided.",
                    category=category.strip(),
                    genre=genre.strip(),
                    language=language.strip(),
                    num_chapters=chapter_count,
                    num_chapters_str=str(chapter_count),
                    llm_provider=llm_provider.strip().lower(),
                    model=model.strip(),
                    project_dir=temporary,
                )
                kb.save_to_file(str(temporary / "project_data.json"))
                save_project_status(temporary, {
                    "version": 2,
                    "stages": {},
                    "operation": {
                        "name": "create_project", "status": "complete",
                        "artifact": "project_data.json", "started_at": datetime.now(timezone.utc).isoformat(),
                        "ended_at": datetime.now(timezone.utc).isoformat(), "error": None,
                    },
                })
                (temporary / "project_data.json").resolve(strict=True).relative_to(temporary.resolve(strict=True))
                try:
                    target.mkdir()
                except FileExistsError:
                    raise ServiceError("project_exists", f"Project '{project}' already exists; no files were changed.") from None
                target_created = True
                # Publish status first and project_data.json last. Readers only treat
                # a directory as a project after its metadata sentinel is present.
                os.replace(temporary / ".libriscribe_status.json", target / ".libriscribe_status.json")
                os.replace(temporary / "project_data.json", target / "project_data.json")
                try:
                    temporary.rmdir()
                except OSError:
                    logger.warning("Could not remove an empty temporary project directory")
            except Exception:
                if temporary.exists():
                    shutil.rmtree(temporary, ignore_errors=True)
                if target_created and target.exists() and not (target / "project_data.json").exists():
                    shutil.rmtree(target, ignore_errors=True)
                raise
        except ServiceError:
            raise
        except Exception:
            logger.exception("Project creation failed")
            raise ServiceError("write_failed", "Project creation failed; no complete project was published.") from None
        return {
            "project": project,
            "status": "complete",
            "summary": f"Created '{title.strip()}' ({category.strip()}, {genre.strip()}, {chapter_count} chapters, {language.strip()}). No LLM was called.",
        }

    def list_projects(self, limit: int = 50) -> dict[str, Any]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ServiceError("invalid_argument", "limit must be between 1 and 100.")
        projects: list[dict[str, Any]] = []
        try:
            if not self.projects_root.is_dir():
                return {"projects": [], "count": 0}
            for entry in sorted(self.projects_root.iterdir(), key=lambda item: item.name.casefold()):
                if len(projects) >= limit:
                    break
                if not _PROJECT_ID.fullmatch(entry.name):
                    continue
                try:
                    resolved = entry.resolve(strict=True)
                    resolved.relative_to(self.projects_root)
                    data_path = (resolved / "project_data.json").resolve(strict=True)
                    data_path.relative_to(resolved)
                    if not resolved.is_dir():
                        continue
                    kb = ProjectKnowledgeBase.load_from_file(str(data_path))
                    if kb is None:
                        continue
                    projects.append({
                        "project": entry.name,
                        "title": kb.title,
                        "genre": kb.genre,
                        "category": kb.category,
                    })
                except (OSError, ValueError):
                    # Symlink escapes and unrelated directories are intentionally invisible.
                    continue
        except OSError:
            raise ServiceError("internal_error", "Could not list the configured projects directory.") from None
        return {"projects": projects, "count": len(projects)}

    def get_project_status(self, project: str) -> dict[str, Any]:
        path, kb = self._resolve_project(project)
        progress = inspect_project_progress(path, kb)
        status = load_project_status(path)
        failed = [name for name, value in progress.stage_statuses.items() if value == "failed"]
        stage_states = {
            "concept": "complete" if progress.concept_complete else "pending",
            "outline": "complete" if progress.outline_complete else "pending",
            "characters": "complete" if progress.characters_complete else "pending",
            "worldbuilding": "complete" if progress.worldbuilding_complete else "pending",
            "chapters": "complete" if not progress.missing_chapters and progress.chapter_numbers_complete else ("in_progress" if progress.chapter_numbers_complete else "pending"),
            "formatting": "complete" if progress.manuscript_exists else "pending",
        }
        if not progress.characters_required:
            stage_states["characters"] = "skipped"
        if not progress.worldbuilding_required:
            stage_states["worldbuilding"] = "skipped"
        # Retain explicit interrupted and failed statuses from the workflow file.
        for name, state in progress.stage_statuses.items():
            if state in {"in_progress", "failed"}:
                stage_states[name] = state
        operation = status.get("operation") if isinstance(status.get("operation"), dict) else None
        operation_state = operation.get("status") if operation else None
        if operation_state == "in_progress":
            recovery = "The last operation may have been interrupted. Inspect its artifact, then explicitly retry one operation if needed."
        elif operation_state == "failed":
            recovery = "Inspect the reported artifact and error, then explicitly retry one operation if appropriate."
        else:
            recovery = "No incomplete service operation is recorded. Choose the next explicit workflow action."
        return {
            "project": project,
            "progress": {
                "concept_complete": progress.concept_complete,
                "outline_complete": progress.outline_complete,
                "characters_required": progress.characters_required,
                "characters_complete": progress.characters_complete,
                "worldbuilding_required": progress.worldbuilding_required,
                "worldbuilding_complete": progress.worldbuilding_complete,
                "manuscript_exists": progress.manuscript_exists,
            },
            "stage_states": stage_states,
            "completed_chapters": progress.chapter_numbers_complete,
            "missing_chapters": progress.missing_chapters,
            "next_step": progress.next_step,
            "interrupted_stage": progress.interrupted_stage,
            "failed_stages": failed,
            "status_updated_at": status.get("updated_at"),
            "operation": operation,
            "operation_state": operation_state or "unknown",
            "recovery_guidance": recovery,
        }

    def get_chapter(
        self, project: str, chapter_number: int, version: str = "original", start_char: int = 0, max_chars: int = 20_000
    ) -> dict[str, Any]:
        number = self._positive_chapter(chapter_number)
        if version not in {"original", "revised"}:
            raise ServiceError("invalid_argument", "version must be 'original' or 'revised'.")
        if isinstance(start_char, bool) or not isinstance(start_char, int) or start_char < 0:
            raise ServiceError("invalid_argument", "start_char must be a nonnegative integer.")
        if isinstance(max_chars, bool) or not isinstance(max_chars, int) or not 1 <= max_chars <= _MAX_CHAPTER_CHARS:
            raise ServiceError("invalid_argument", f"max_chars must be between 1 and {_MAX_CHAPTER_CHARS}.")
        path, kb = self._resolve_project(project)
        suffix = "_revised" if version == "revised" else ""
        artifact = path / f"chapter_{number}{suffix}.md"
        try:
            artifact_resolved = artifact.resolve(strict=True)
            artifact_resolved.relative_to(path)
            content = artifact_resolved.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ServiceError("artifact_not_found", f"The {version} version of chapter {number} does not exist.") from None
        except (OSError, ValueError, UnicodeError):
            raise ServiceError("artifact_unavailable", f"The {version} version of chapter {number} could not be read safely.") from None
        if start_char > len(content):
            raise ServiceError("invalid_argument", "start_char is beyond the end of the chapter.")
        end_char = min(start_char + max_chars, len(content))
        chapter = kb.get_chapter(number)
        return {
            "project": project,
            "chapter_number": number,
            "version": version,
            "title": chapter.title if chapter else None,
            "text": content[start_char:end_char],
            "start_char": start_char,
            "end_char": end_char,
            "total_chars": len(content),
            "has_more": end_char < len(content),
            "revision_token": _revision_token(content),
        }

    def replace_chapter_text(
        self,
        project: str,
        chapter_number: int,
        version: str,
        text: str,
        expected_revision_token: str,
    ) -> dict[str, Any]:
        """Atomically replace one existing chapter version using optimistic concurrency."""
        number = self._positive_chapter(chapter_number)
        if version not in {"original", "revised"}:
            raise ServiceError("invalid_argument", "version must be 'original' or 'revised'.")
        if not isinstance(text, str) or not text.strip() or len(text) > _MAX_MANUAL_EDIT_CHARS:
            raise ServiceError("invalid_argument", f"text must contain 1 to {_MAX_MANUAL_EDIT_CHARS} non-whitespace characters.")
        if not isinstance(expected_revision_token, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_revision_token):
            raise ServiceError("invalid_argument", "expected_revision_token must be the SHA-256 revision_token returned by get_chapter.")
        path, _ = self._resolve_project(project)
        lock = _project_lock(path)
        if not lock.acquire(blocking=False):
            raise ServiceError("project_busy", "Another write operation is already running for this project.")
        artifact = path / f"chapter_{number}{'_revised' if version == 'revised' else ''}.md"
        started = datetime.now(timezone.utc).isoformat()
        try:
            with project_write_lock(path):
                try:
                    current = artifact.resolve(strict=True)
                    current.relative_to(path)
                    original = current.read_text(encoding="utf-8")
                    if not original.strip():
                        raise ServiceError("artifact_not_found", f"The {version} chapter {number} is empty and cannot be edited safely.")
                except FileNotFoundError:
                    raise ServiceError("artifact_not_found", f"The {version} chapter {number} does not exist; manual edits cannot create a version.") from None
                except (OSError, ValueError, UnicodeError):
                    raise ServiceError("artifact_not_found", "The chapter artifact could not be read safely.") from None
                if _revision_token(original) != expected_revision_token:
                    raise ServiceError("stale_revision", "The chapter changed since it was read. Call get_chapter again before editing.")
                update_operation_status(path, operation="replace_chapter_text", status="in_progress", artifact=artifact.name, started_at=started)
                temp_path: Path | None = None
                try:
                    fd, temp_name = tempfile.mkstemp(prefix=".libriscribe-edit-", suffix=".tmp", dir=path)
                    temp_path = Path(temp_name)
                    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                        stream.write(text)
                        stream.flush()
                        os.fsync(stream.fileno())
                    if not temp_path.read_text(encoding="utf-8").strip():
                        raise OSError("empty staged edit")
                    os.replace(temp_path, artifact)
                except ServiceError:
                    raise
                except Exception:
                    logger.exception("Manual chapter update failed")
                    raise ServiceError("write_failed", "The revised chapter could not be saved; the previous artifact was preserved.") from None
                finally:
                    if temp_path and temp_path.exists():
                        temp_path.unlink(missing_ok=True)
                token = _revision_token(text)
                try:
                    update_operation_status(path, operation="replace_chapter_text", status="complete", artifact=artifact.name, started_at=started)
                except OSError:
                    logger.exception("Manual edit succeeded but completion status could not be recorded")
                return {"project": project, "chapter_number": number, "version": version, "status": "complete", "revision_token": token, "artifact": {"path": artifact.name, "size_bytes": artifact.stat().st_size}}
        except ProjectWriteBusy:
            raise ServiceError("project_busy", "Another write operation is already running for this project.") from None
        except ServiceError as exc:
            if exc.code != "stale_revision" and exc.code != "artifact_not_found":
                try:
                    update_operation_status(path, operation="replace_chapter_text", status="failed", artifact=artifact.name, started_at=started, error=exc.code)
                except OSError:
                    logger.exception("Could not record failed manual edit")
            raise
        finally:
            lock.release()

    def search_project(self, project: str, query: str, top_k: int = 6, mode: str = "keyword") -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ServiceError("invalid_argument", "query must contain 1 to 2000 non-whitespace characters.")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ServiceError("invalid_argument", "top_k must be between 1 and 20.")
        if not isinstance(mode, str) or mode not in {"keyword", "semantic", "hybrid"}:
            raise ServiceError("unsupported_mode", "mode must be keyword, semantic, or hybrid.")
        manager, path, kb = self._manager(project)
        if not kb.retrieval.enabled:
            raise ServiceError("capability_disabled", "Retrieval is disabled for this project.")
        from libriscribe.retrieval.config import get_retrieval_dir
        try:
            retrieval_dir = get_retrieval_dir(path, kb.retrieval).resolve()
            retrieval_dir.relative_to(path)
            index_file = retrieval_dir / "keyword_index.json"
            index_file.resolve(strict=True).relative_to(path)
            if mode in {"semantic", "hybrid"}:
                semantic_file = retrieval_dir / "semantic_index.json"
                semantic_file.resolve(strict=True).relative_to(path)
        except (OSError, ValueError):
            raise ServiceError("index_unavailable", "The configured local retrieval index is outside the project or unavailable. Check its path and rebuild it if needed.") from None
        if not index_file.is_file():
            raise ServiceError("index_unavailable", "The local retrieval index is unavailable; search does not rebuild indexes.")
        try:
            from libriscribe.retrieval.search_service import SearchServiceImpl
            search = SearchServiceImpl(path, kb.retrieval)
            results = search.search(query.strip(), mode=mode, top_k=top_k)
        except RuntimeError as exc:
            logger.info("Optional semantic retrieval is unavailable: %s", exc)
            raise ServiceError("semantic_unavailable", str(exc)) from None
        except Exception:
            logger.exception("Local project search failed")
            raise ServiceError("index_unavailable", "The local retrieval index could not be read.") from None
        matches = []
        for result in results:
            matches.append({
                "source_type": result.source_type,
                "score": result.score,
                "chapter_number": result.chapter_number,
                "scene_number": result.scene_number,
                "excerpt": result.text[:800],
                "excerpt_truncated": len(result.text) > 800,
            })
        return {"project": project, "query": query.strip(), "mode": mode, "matches": matches, "count": len(matches)}

    def rebuild_project_index(
        self, project: str, *, mode: str | None = None, embedding_model: str | None = None,
        hybrid_keyword_weight: float | None = None,
    ) -> dict[str, Any]:
        """Rebuild local project indexes, optionally selecting the semantic mode/model."""
        path, kb = self._resolve_project(project)
        from libriscribe.retrieval.models import RetrievalMode
        config = kb.retrieval.model_copy(deep=True)
        if mode is None and config.mode == RetrievalMode.DISABLED:
            config.mode = RetrievalMode.KEYWORD
        if mode is not None:
            if not isinstance(mode, str) or mode not in {"keyword", "semantic", "hybrid"}:
                raise ServiceError("invalid_argument", "mode must be keyword, semantic, or hybrid.")
            config.mode = RetrievalMode(mode)
        if embedding_model is not None:
            if not isinstance(embedding_model, str) or not embedding_model.strip() or len(embedding_model) > 500:
                raise ServiceError("invalid_argument", "embedding_model must contain 1 to 500 characters.")
            config.embedding_model = embedding_model.strip()
        if hybrid_keyword_weight is not None:
            if isinstance(hybrid_keyword_weight, bool) or not isinstance(hybrid_keyword_weight, (int, float)) or not 0.0 <= hybrid_keyword_weight <= 1.0:
                raise ServiceError("invalid_argument", "hybrid_keyword_weight must be between 0 and 1.")
            config.hybrid_keyword_weight = float(hybrid_keyword_weight)
        config.enabled = True
        try:
            from libriscribe.retrieval.index_manager import IndexManager
            IndexManager(kb, path, config).rebuild_index()
            kb.retrieval = config
            kb.save_to_file(str(path / "project_data.json"))
        except RuntimeError as exc:
            logger.info("Local retrieval index rebuild could not load its optional embedder: %s", exc)
            raise ServiceError("semantic_unavailable", str(exc)) from None
        except Exception:
            logger.exception("Local project index rebuild failed")
            raise ServiceError("index_rebuild_failed", "The local retrieval index could not be rebuilt; existing searchable artifacts were retained where possible.") from None
        return {"project": project, "mode": config.mode.value, "status": "complete"}

    def check_narrative(self, project: str, chapter_number: int) -> dict[str, Any]:
        number = self._positive_chapter(chapter_number)
        path, kb = self._resolve_project(project)
        chapter = kb.get_chapter(number)
        if chapter is None:
            raise ServiceError("chapter_unavailable", f"Chapter {number} has no scene outline in project metadata.")
        graph_path = path / "narrative_graph.json"
        if not graph_path.is_file():
            raise ServiceError("graph_unavailable", "The narrative graph is unavailable for this project.")
        try:
            resolved = graph_path.resolve(strict=True)
            resolved.relative_to(path)
            graph = NarrativeGraph.load(resolved)
        except Exception:
            raise ServiceError("graph_unavailable", "The narrative graph could not be read.") from None
        checker = InvariantChecker(graph)
        violations = []
        for scene in chapter.scenes:
            for violation in checker.check_scene(scene, number, kb):
                violations.append({
                    "severity": violation.severity,
                    "entity": violation.entity,
                    "description": violation.description,
                    "established_chapter": violation.established_chapter,
                    "evidence": violation.evidence_quote,
                    "scene_number": scene.scene_number,
                })
        return {"project": project, "chapter_number": number, "violations": violations, "count": len(violations)}

    def _run_write(
        self,
        project: str,
        operation_name: str,
        artifact_name: str,
        operation: Callable[[ProjectManagerAgent, Path, ProjectKnowledgeBase], dict[str, Any]],
    ) -> dict[str, Any]:
        path, _ = self._resolve_project(project)
        lock = _project_lock(path)
        if not lock.acquire(blocking=False):
            raise ServiceError("project_busy", "Another write operation is already running for this project.")
        started = datetime.now(timezone.utc).isoformat()
        try:
            with project_write_lock(path):
                update_operation_status(path, operation=operation_name, status="in_progress", artifact=artifact_name, started_at=started)
                try:
                    manager, path, kb = self._manager(project, llm=True)
                    result = operation(manager, path, kb)
                    try:
                        update_operation_status(path, operation=operation_name, status="complete", artifact=artifact_name, started_at=started)
                    except OSError:
                        logger.exception("Project operation succeeded but completion status could not be recorded")
                    return result
                except ServiceError as exc:
                    update_operation_status(path, operation=operation_name, status="failed", artifact=artifact_name, started_at=started, error=exc.code)
                    raise
                except Exception:
                    logger.exception("Project operation failed")
                    update_operation_status(path, operation=operation_name, status="failed", artifact=artifact_name, started_at=started, error="operation_failed")
                    raise ServiceError("operation_failed", "The project operation failed. Check the local LibriScribe log for details.") from None
        except ProjectWriteBusy:
            raise ServiceError("project_busy", "Another write operation is already running for this project.") from None
        finally:
            lock.release()

    @staticmethod
    def _check_overwrite(paths: list[Path], overwrite: bool) -> None:
        LibriScribeService._validate_overwrite(overwrite)
        existing = [p.name for p in paths if p.exists() or p.is_symlink()]
        if existing and not overwrite:
            raise ServiceError("overwrite_refused", f"Refusing to replace existing artifact(s): {', '.join(existing)}. Set overwrite=true to replace them.")

    @staticmethod
    def _validate_overwrite(overwrite: bool) -> None:
        if not isinstance(overwrite, bool):
            raise ServiceError("invalid_argument", "overwrite must be a boolean.")

    @staticmethod
    def _stage_directory(project_path: Path) -> Path:
        try:
            return Path(tempfile.mkdtemp(prefix=".libriscribe-stage-", dir=project_path))
        except OSError:
            raise ServiceError("write_failed", "Could not create a private staging area inside the project.") from None

    @staticmethod
    def _promote(staged: Path, target: Path) -> dict[str, Any]:
        LibriScribeService._verify_artifact(staged)
        try:
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise OSError("output target is not a regular file")
            os.replace(staged, target)
        except OSError:
            raise ServiceError("write_failed", f"Could not atomically publish {target.name}; the previous artifact was preserved.") from None
        return LibriScribeService._verify_artifact(target)

    @staticmethod
    def _promote_many(staged_artifacts: list[tuple[Path, Path]], backup_dir: Path) -> list[dict[str, Any]]:
        """Publish a related export set together and restore old files on failure."""
        for staged, target in staged_artifacts:
            LibriScribeService._verify_artifact(staged)
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise ServiceError("write_failed", f"Could not safely publish {target.name}; the previous artifact was preserved.")
        backups: dict[Path, Path] = {}
        published: list[Path] = []
        try:
            for _staged, target in staged_artifacts:
                if target.exists():
                    backup = backup_dir / f"{target.name}.previous"
                    os.replace(target, backup)
                    backups[target] = backup
            for staged, target in staged_artifacts:
                os.replace(staged, target)
                published.append(target)
        except OSError:
            for target in published:
                target.unlink(missing_ok=True)
            for target, backup in backups.items():
                if backup.exists():
                    os.replace(backup, target)
            raise ServiceError("write_failed", "Could not publish the complete export set; previous artifacts were restored.") from None
        for backup in backups.values():
            backup.unlink(missing_ok=True)
        return [LibriScribeService._verify_artifact(target) for _staged, target in staged_artifacts]

    @staticmethod
    def _verify_artifact(path: Path) -> dict[str, Any]:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(path.parent.resolve(strict=True))
            if not resolved.is_file() or resolved.stat().st_size == 0:
                raise ValueError("empty")
            if resolved.suffix.lower() == ".pdf":
                with resolved.open("rb") as stream:
                    if not stream.read(5).startswith(b"%PDF-"):
                        raise ValueError("invalid PDF header")
                    stream.seek(max(0, resolved.stat().st_size - 1024))
                    if b"%%EOF" not in stream.read():
                        raise ValueError("invalid PDF footer")
            elif not resolved.read_text(encoding="utf-8").strip():
                raise ValueError("empty")
        except Exception:
            raise ServiceError("operation_failed", f"Expected artifact {path.name} was not created or is empty.") from None
        return {"path": path.name, "size_bytes": resolved.stat().st_size}

    @staticmethod
    def _verify_provider(manager: ProjectManagerAgent) -> None:
        failure_type = getattr(manager.llm_client, "last_failure_type", None)
        if failure_type:
            raise ServiceError(
                "provider_failure",
                f"The configured LLM provider failed ({failure_type}); check the local LibriScribe log.",
            )

    def generate_outline(self, project: str, overwrite: bool = False) -> dict[str, Any]:
        self._validate_overwrite(overwrite)
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            artifact = path / "outline.md"
            self._check_overwrite([artifact], overwrite)
            stage = self._stage_directory(path)
            staged = stage / artifact.name
            try:
                manager.generate_outline(output_path=str(staged))
                self._verify_provider(manager)
                metadata = self._promote(staged, artifact)
                return {"project": project, "status": "complete", "artifact": metadata}
            finally:
                shutil.rmtree(stage, ignore_errors=True)
        return self._run_write(project, "generate_outline", "outline.md", action)

    def write_chapter(self, project: str, chapter_number: int, overwrite: bool = False) -> dict[str, Any]:
        number = self._positive_chapter(chapter_number)
        self._validate_overwrite(overwrite)
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            self._check_chapter_range(kb, number)
            artifact = path / f"chapter_{number}.md"
            self._check_overwrite([artifact], overwrite)
            stage = self._stage_directory(path)
            staged = stage / artifact.name
            try:
                manager.write_chapter(number, output_path=str(staged))
                self._verify_provider(manager)
                metadata = self._promote(staged, artifact)
                return {"project": project, "chapter_number": number, "status": "complete", "artifact": metadata}
            finally:
                shutil.rmtree(stage, ignore_errors=True)
        return self._run_write(project, "write_chapter", f"chapter_{number}.md", action)

    def edit_chapter(self, project: str, chapter_number: int, overwrite: bool = False) -> dict[str, Any]:
        number = self._positive_chapter(chapter_number)
        self._validate_overwrite(overwrite)
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            self._check_chapter_range(kb, number)
            source = path / f"chapter_{number}.md"
            if not source.is_file() or not source.read_text(encoding="utf-8").strip():
                raise ServiceError("artifact_not_found", f"Original chapter {number} does not exist or is empty.")
            revised = path / f"chapter_{number}_revised.md"
            self._check_overwrite([revised], overwrite)
            stage = self._stage_directory(path)
            staged = stage / revised.name
            try:
                manager.edit_chapter(number, output_path=str(staged))
                self._verify_provider(manager)
                metadata = self._promote(staged, revised)
                return {"project": project, "chapter_number": number, "status": "complete", "artifact": metadata}
            finally:
                shutil.rmtree(stage, ignore_errors=True)
        return self._run_write(project, "edit_chapter", f"chapter_{number}_revised.md", action)

    def format_book(self, project: str, format: str, overwrite: bool = False) -> dict[str, Any]:
        if format not in {"md", "pdf"}:
            raise ServiceError("invalid_argument", "format must be 'md' or 'pdf'.")
        self._validate_overwrite(overwrite)
        extension = format
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            output = path / f"manuscript.{extension}"
            original = path / f"manuscript_original.{extension}"
            self._check_overwrite([output, original], overwrite)
            stage = self._stage_directory(path)
            staged_output = stage / output.name
            staged_original = stage / original.name
            try:
                manager.format_book(str(staged_output))
                self._verify_provider(manager)
                staged_artifacts = [(staged_output, output), (staged_original, original)]
                ready = [(source, target) for source, target in staged_artifacts if source.exists()]
                if not ready:
                    raise ServiceError("operation_failed", "Formatting did not create a nonempty manuscript artifact.")
                artifacts = self._promote_many(ready, stage)
                return {"project": project, "format": extension, "status": "complete", "artifacts": artifacts}
            finally:
                shutil.rmtree(stage, ignore_errors=True)
        return self._run_write(project, "format_book", f"manuscript.{extension}", action)
