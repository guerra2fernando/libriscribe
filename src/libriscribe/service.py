"""Shared, path-confined application service for CLI and MCP operations."""
from __future__ import annotations

import logging
import re
import threading
from pathlib import Path
from typing import Any, Callable

from libriscribe.agents.project_manager import ProjectManagerAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.narrative.invariant_checker import InvariantChecker
from libriscribe.narrative.models import NarrativeGraph
from libriscribe.settings import Settings
from libriscribe.utils.project_status import load_project_status
from libriscribe.workflow_state import inspect_project_progress

logger = logging.getLogger(__name__)

_PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,99}$")
_WRITE_LOCKS: dict[str, threading.Lock] = {}
_WRITE_LOCKS_GUARD = threading.Lock()
_MAX_CHAPTER_CHARS = 20_000


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
        }

    def search_project(self, project: str, query: str, top_k: int = 6, mode: str = "keyword") -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ServiceError("invalid_argument", "query must contain 1 to 2000 non-whitespace characters.")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ServiceError("invalid_argument", "top_k must be between 1 and 20.")
        if mode != "keyword":
            raise ServiceError("unsupported_mode", "Only local keyword search is currently supported.")
        manager, path, kb = self._manager(project)
        if not kb.retrieval.enabled:
            raise ServiceError("capability_disabled", "Retrieval is disabled for this project.")
        from libriscribe.retrieval.config import get_retrieval_dir
        try:
            retrieval_dir = get_retrieval_dir(path, kb.retrieval).resolve()
            retrieval_dir.relative_to(path)
            index_file = retrieval_dir / "keyword_index.json"
            index_file.resolve(strict=True).relative_to(path)
        except (OSError, ValueError):
            raise ServiceError("index_unavailable", "The configured local retrieval index is outside the project or unavailable.") from None
        if not index_file.is_file():
            raise ServiceError("index_unavailable", "The local retrieval index is unavailable; search does not rebuild indexes.")
        try:
            from libriscribe.retrieval.search_service import SearchServiceImpl
            search = SearchServiceImpl(path, kb.retrieval)
            results = search.search(query.strip(), mode=mode, top_k=top_k)
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

    def _run_write(self, project: str, operation: Callable[[ProjectManagerAgent, Path, ProjectKnowledgeBase], dict[str, Any]]) -> dict[str, Any]:
        # Resolve before locking, then acquire a process-local nonblocking write lock.
        path, _ = self._resolve_project(project)
        lock = _project_lock(path)
        if not lock.acquire(blocking=False):
            raise ServiceError("project_busy", "Another write operation is already running for this project.")
        try:
            manager, path, kb = self._manager(project, llm=True)
            try:
                result = operation(manager, path, kb)
            except ServiceError:
                raise
            except Exception:
                logger.exception("Project operation failed")
                raise ServiceError("operation_failed", "The project operation failed. Check the local LibriScribe log for details.") from None
            return result
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
    def _clear_artifacts(paths: list[Path]) -> None:
        """Remove explicit overwrite targets so a swallowed failure cannot look successful."""
        for path in paths:
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                raise ServiceError("artifact_unavailable", f"Output target {path.name} is not a regular file.")

    @staticmethod
    def _verify_artifact(path: Path) -> dict[str, Any]:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(path.parent.resolve(strict=True))
            if not resolved.is_file() or resolved.stat().st_size == 0:
                raise ValueError("empty")
            if resolved.suffix.lower() != ".pdf" and not resolved.read_text(encoding="utf-8").strip():
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
            self._clear_artifacts([artifact])
            manager.generate_outline()
            self._verify_provider(manager)
            return {"project": project, "status": "complete", "artifact": self._verify_artifact(artifact)}
        return self._run_write(project, action)

    def write_chapter(self, project: str, chapter_number: int, overwrite: bool = False) -> dict[str, Any]:
        number = self._positive_chapter(chapter_number)
        self._validate_overwrite(overwrite)
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            self._check_chapter_range(kb, number)
            artifact = path / f"chapter_{number}.md"
            self._check_overwrite([artifact], overwrite)
            self._clear_artifacts([artifact])
            manager.write_chapter(number)
            self._verify_provider(manager)
            return {"project": project, "chapter_number": number, "status": "complete", "artifact": self._verify_artifact(artifact)}
        return self._run_write(project, action)

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
            self._clear_artifacts([revised])
            manager.edit_chapter(number)
            self._verify_provider(manager)
            return {"project": project, "chapter_number": number, "status": "complete", "artifact": self._verify_artifact(revised)}
        return self._run_write(project, action)

    def format_book(self, project: str, format: str, overwrite: bool = False) -> dict[str, Any]:
        if format not in {"md", "pdf"}:
            raise ServiceError("invalid_argument", "format must be 'md' or 'pdf'.")
        self._validate_overwrite(overwrite)
        extension = format
        def action(manager: ProjectManagerAgent, path: Path, kb: ProjectKnowledgeBase) -> dict[str, Any]:
            output = path / f"manuscript.{extension}"
            original = path / f"manuscript_original.{extension}"
            self._check_overwrite([output, original], overwrite)
            self._clear_artifacts([output, original])
            manager.format_book(str(output))
            self._verify_provider(manager)
            artifacts = []
            for artifact in (output, original):
                if artifact.exists():
                    artifacts.append(self._verify_artifact(artifact))
            if not artifacts:
                raise ServiceError("operation_failed", "Formatting did not create a nonempty manuscript artifact.")
            return {"project": project, "format": extension, "status": "complete", "artifacts": artifacts}
        return self._run_write(project, action)
