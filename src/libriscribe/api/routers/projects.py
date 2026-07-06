"""Project CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from libriscribe.api.schemas.project import (
    CreateProjectRequest,
    ProjectSummary,
    ProjectDetail,
    ProjectProgress,
    ChapterMeta,
    ChapterContent,
    ProjectFile,
    CostSummary,
    CostEntry,
)
from libriscribe.services import project_service
from libriscribe.workflow_state import inspect_project_progress
from libriscribe.utils.file_utils import (
    read_markdown_file,
    write_markdown_file,
    is_nonempty_file,
    get_existing_chapter_numbers,
)
from libriscribe.utils.token_utils import estimate_tokens

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ProjectSummary])
def list_projects():
    return project_service.list_projects()


@router.post("", response_model=ProjectDetail)
def create_project(req: CreateProjectRequest):
    data = req.model_dump()
    result = project_service.create_project(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create project")
    return result


class ImportProjectRequest(BaseModel):
    bundle: dict
    target_name: str | None = None


@router.post("/import")
def import_project(body: ImportProjectRequest):
    """Import a project from a .libriscribe.json bundle. Auto-renames on collision."""
    try:
        result = project_service.import_project_bundle(body.bundle, body.target_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result["detail"] = project_service.get_project_detail(result["project_name"])
    return result


@router.get("/{name}", response_model=ProjectDetail)
def get_project(name: str):
    detail = project_service.get_project_detail(name)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.get("/{name}/active-model")
def get_active_model(name: str):
    """The model that will actually run for this project, and where it comes from (the project's
    own override, or the provider default from Settings when the project's model is blank)."""
    resolved = project_service.resolve_active_model(name)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return resolved


@router.get("/{name}/export")
def export_project(name: str):
    """Download the whole project as a single self-contained .libriscribe.json bundle."""
    bundle = project_service.export_project_bundle(name)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return JSONResponse(
        content=bundle,
        headers={"Content-Disposition": f'attachment; filename="{name}.libriscribe.json"'},
    )


@router.get("/{name}/export/story")
def export_story(name: str):
    """Download the story as plain text (chapters as they currently stand)."""
    text = project_service.export_story_text(name)
    if text is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return PlainTextResponse(
        content=text,
        headers={"Content-Disposition": f'attachment; filename="{name}.txt"'},
    )


class SaveVersionRequest(BaseModel):
    label: str | None = None


@router.get("/{name}/versions")
def list_versions(name: str):
    return project_service.list_project_versions(name)


@router.post("/{name}/versions")
def save_version(name: str, body: SaveVersionRequest):
    try:
        return project_service.save_project_version(name, body.label)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{name}/versions/{version}/restore")
def restore_version(name: str, version: int):
    """Roll the project back to a saved version (auto-snapshots current state first)."""
    try:
        result = project_service.restore_project_version(name, version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result["detail"] = project_service.get_project_detail(name)
    return result


class UpdateProjectSettings(BaseModel):
    llm_provider: str | None = None
    model: str | None = None
    utility_model: str | None = None
    fallback_chain: list[str] | None = None


@router.put("/{name}/settings", response_model=ProjectDetail)
def update_project_settings(name: str, body: UpdateProjectSettings):
    """Update a project's LLM configuration (provider / model / fallback chain).

    Lets the user switch the AI for an existing project when a model is no longer
    valid, available, or useful.
    """
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.llm_provider is not None:
        kb.llm_provider = body.llm_provider
    if body.model is not None:
        kb.model = body.model
    if body.utility_model is not None:
        kb.utility_model = body.utility_model
    if body.fallback_chain is not None:
        kb.fallback_chain = body.fallback_chain
    project_service.save_kb(name, kb)
    return project_service.get_project_detail(name)


def _coerce_chapter_count(value) -> int | tuple[int, int]:
    """Coerce "12" / "10-14" / "3+" to the KB's int|tuple shape (no validate_assignment on the KB)."""
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if "-" in s:
        try:
            lo, hi = map(int, s.split("-"))
            return (lo, hi)
        except ValueError:
            return 0
    try:
        return int(s.replace("+", ""))
    except ValueError:
        return 0


class UpdateProjectMeta(BaseModel):
    """Editable primary details of a story. All optional — only provided fields are written.
    The project's folder name / URL id (`project_name`) is intentionally NOT editable here."""
    title: str | None = None
    genre: str | None = None
    category: str | None = None
    language: str | None = None
    description: str | None = None
    num_chapters: int | str | None = None  # target chapter count
    target_word_count: int | None = None
    logline: str | None = None
    tone: str | None = None
    target_audience: str | None = None
    book_length: str | None = None


@router.put("/{name}/meta", response_model=ProjectDetail)
def update_project_meta(name: str, body: UpdateProjectMeta):
    """Update a project's primary story details (title, genre, targets, creative brief)."""
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        if field == "num_chapters":
            # No validate_assignment on the KB, so coerce "5"/"3-5"/"2+" like the model would.
            value = _coerce_chapter_count(value)
        setattr(kb, field, value)
    project_service.save_kb(name, kb)
    return project_service.get_project_detail(name)


# ─── Retrieval / semantic search (B17) ────────────────────────────────────────

_VALID_RETRIEVAL_MODES = {"disabled", "keyword", "semantic", "hybrid"}


class UpdateRetrievalRequest(BaseModel):
    mode: str  # disabled | keyword | semantic | hybrid


def _retrieval_status(name: str, kb) -> dict:
    """Report the project's retrieval mode + whether a semantic index is ready to serve."""
    from libriscribe.retrieval.models import RetrievalConfig
    from libriscribe.retrieval.embedder import build_embedder
    from libriscribe.settings import Settings

    settings = Settings()
    embedder = build_embedder(settings)
    cfg = kb.retrieval or RetrievalConfig()
    mode = getattr(cfg.mode, "value", str(cfg.mode))
    semantic_ready, chunk_count = False, 0
    try:
        from libriscribe.retrieval.index_manager import IndexManager

        project_dir = project_service.get_projects_dir() / name
        im = IndexManager(kb, project_dir, cfg, embedder=embedder)
        im.load_indexes()
        chunk_count = len(im.keyword_index.chunks_map)
        semantic_ready = im.semantic_index.is_ready(embedder)
    except Exception:
        pass
    return {
        "mode": mode,
        "enabled": bool(cfg.enabled),
        "embedding_provider": settings.retrieval_embedding_provider or "off",
        "embedder_configured": embedder is not None,
        "semantic_ready": semantic_ready,
        "chunk_count": chunk_count,
    }


@router.get("/{name}/retrieval")
def get_retrieval(name: str):
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    return _retrieval_status(name, kb)


@router.put("/{name}/retrieval")
def set_retrieval(name: str, body: UpdateRetrievalRequest):
    """Set the project's search mode and (re)build the index. Semantic/hybrid need an
    embedding source configured in Settings; without one they fall back to keyword."""
    from libriscribe.retrieval.models import RetrievalConfig

    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")

    mode = (body.mode or "").strip().lower()
    if mode not in _VALID_RETRIEVAL_MODES:
        raise HTTPException(status_code=400, detail=f"mode must be one of {sorted(_VALID_RETRIEVAL_MODES)}")

    data = (kb.retrieval.model_dump() if kb.retrieval else RetrievalConfig().model_dump())
    data.update({"enabled": mode != "disabled", "mode": mode})
    kb.retrieval = RetrievalConfig(**data)
    project_service.save_kb(name, kb)

    # Rebuild the index so the chosen mode is immediately queryable.
    try:
        from libriscribe.services.retrieval_service import rebuild_project_index
        rebuild_project_index(kb, project_service.get_projects_dir() / name)
    except Exception:
        logger.warning("Retrieval reindex failed for %s", name, exc_info=True)

    return _retrieval_status(name, kb)


# ─── Manuscript stats (B14) ───────────────────────────────────────────────────

@router.get("/{name}/stats")
def get_stats(name: str):
    """Readability + count metrics per chapter and for the whole book (no LLM)."""
    from libriscribe.services import stats_service

    stats = stats_service.project_stats(name)
    if stats is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return stats


# ─── Prompt / context preview (B15) ───────────────────────────────────────────

@router.get("/{name}/preview-context/{chapter_number}")
def preview_context(name: str, chapter_number: int):
    """Dry-run the generation context assembly for a chapter — the exact lore/context that
    ContextBuilder + TokenBudget would inject into the chapter-writing prompt. No LLM call."""
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    chapter = kb.get_chapter(chapter_number)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    from libriscribe.knowledge_base import Scene
    from libriscribe.services.context_builder import ContextBuilder

    scene = chapter.scenes[0] if chapter.scenes else Scene(
        scene_number=1, summary=chapter.summary or chapter.title or "", setting="", characters=[],
    )

    svc = None
    try:
        from libriscribe.services.retrieval_service import search_service_for
        svc = search_service_for(project_service.get_projects_dir() / name, kb)
    except Exception:
        svc = None

    context = ContextBuilder(kb, svc).build_scene_context(chapter_number, scene, chapter)
    return {
        "chapter_number": chapter_number,
        "scene_number": scene.scene_number,
        "context": context,
        "token_estimate": estimate_tokens(context),
    }


@router.delete("/{name}", status_code=204)
def delete_project(name: str):
    if not project_service.delete_project(name):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{name}/status")
def get_project_status(name: str):
    """Returns stage statuses from .libriscribe_status.json."""
    from libriscribe.utils.project_status import load_project_status
    project_dir = project_service.get_projects_dir() / name
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return load_project_status(project_dir)


@router.get("/{name}/progress", response_model=ProjectProgress)
def get_project_progress(name: str):
    project_dir = project_service.get_projects_dir() / name
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    progress = inspect_project_progress(project_dir, kb)
    return {
        "concept_complete": progress.concept_complete,
        "outline_complete": progress.outline_complete,
        "characters_required": progress.characters_required,
        "characters_complete": progress.characters_complete,
        "worldbuilding_required": progress.worldbuilding_required,
        "worldbuilding_complete": progress.worldbuilding_complete,
        "chapter_numbers_complete": progress.chapter_numbers_complete,
        "missing_chapters": progress.missing_chapters,
        "manuscript_exists": progress.manuscript_exists,
        "next_step": progress.next_step,
        "stage_statuses": progress.stage_statuses,
    }


@router.get("/{name}/chapters", response_model=list[ChapterMeta])
def list_chapters(name: str):
    project_dir = project_service.get_projects_dir() / name
    kb = project_service.load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")

    total = kb.num_chapters
    if isinstance(total, tuple):
        total = total[1]
    if not isinstance(total, int) or total < 1:
        total = 0

    chapters = []
    for ch_num in range(1, total + 1):
        ch_path = project_dir / f"chapter_{ch_num}.md"
        revised_path = project_dir / f"chapter_{ch_num}_revised.md"
        has_content = is_nonempty_file(ch_path)
        has_revised = is_nonempty_file(revised_path)
        word_count = 0
        title = ""
        if has_content:
            content = read_markdown_file(str(ch_path))
            word_count = len(content.split())
            for line in content.split("\n"):
                if line.startswith("#"):
                    title = line.replace("#", "").strip()
                    break

        chapter_data = kb.get_chapter(ch_num)
        if chapter_data and chapter_data.title:
            title = chapter_data.title

        chapters.append({
            "chapter_number": ch_num,
            "title": title,
            "has_content": has_content,
            "has_revised": has_revised,
            "word_count": word_count,
        })
    return chapters


@router.get("/{name}/chapters/{n}", response_model=ChapterContent)
def get_chapter(name: str, n: int):
    project_dir = project_service.get_projects_dir() / name
    ch_path = project_dir / f"chapter_{n}.md"
    if not ch_path.exists():
        raise HTTPException(status_code=404, detail=f"Chapter {n} not found")
    content = read_markdown_file(str(ch_path))
    title = ""
    for line in content.split("\n"):
        if line.startswith("#"):
            title = line.replace("#", "").strip()
            break
    return {
        "chapter_number": n,
        "title": title,
        "content": content,
        "word_count": len(content.split()),
    }


@router.put("/{name}/chapters/{n}", response_model=ChapterContent)
def save_chapter(name: str, n: int, body: ChapterContent):
    project_dir = project_service.get_projects_dir() / name
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    ch_path = str(project_dir / f"chapter_{n}.md")
    write_markdown_file(ch_path, body.content)
    return {
        "chapter_number": n,
        "title": body.title,
        "content": body.content,
        "word_count": len(body.content.split()),
    }


@router.get("/{name}/files", response_model=list[ProjectFile])
def list_files(name: str):
    project_dir = project_service.get_projects_dir() / name
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    files = []
    for p in sorted(project_dir.iterdir()):
        if p.is_file() and not p.name.startswith("."):
            stat = p.stat()
            files.append({
                "name": p.name,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    return files


@router.get("/{name}/download/{filename}")
def download_file(name: str, filename: str):
    from fastapi.responses import FileResponse
    project_dir = project_service.get_projects_dir() / name
    file_path = project_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Ensure the file is inside the project dir (path traversal prevention)
    if not str(file_path.resolve()).startswith(str(project_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(str(file_path), filename=filename)


@router.post("/{name}/format")
async def trigger_format(name: str):
    """Triggers a formatting job."""
    from libriscribe.api.dependencies import get_generation_service
    svc = get_generation_service()
    job = await svc.start_generation(name, start_from_stage="formatting", streaming=False)
    return {"status": job.status, "message": "Formatting started"}


@router.get("/{name}/cost", response_model=CostSummary)
def get_cost(name: str):
    """Parses llm_usage.jsonl for cost info."""
    from libriscribe.utils.paths import get_app_data_dir

    project_dir = project_service.get_projects_dir() / name
    usage_file = project_dir / "llm_usage.jsonl"
    cwd_usage = Path("llm_usage.jsonl")            # legacy location (older builds)
    appdata_usage = get_app_data_dir() / "llm_usage.jsonl"  # where CostTracker writes now

    entries = []
    total_cost = 0.0
    total_tokens = 0

    seen: set[str] = set()
    for path in [usage_file, cwd_usage, appdata_usage]:
        try:
            key = str(path.resolve())
        except Exception:
            key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entry = json.loads(line)
                        entries.append(entry)
                        total_cost += entry.get("cost", 0.0)
                        total_tokens += entry.get("total_tokens", 0)
            except Exception:
                pass

    return {
        "entries": entries,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
    }
