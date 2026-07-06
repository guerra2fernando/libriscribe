"""Project CRUD operations."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from libriscribe.knowledge_base import ProjectKnowledgeBase, Location
from libriscribe.settings import Settings
from libriscribe.workflow_state import inspect_project_progress
from libriscribe.utils.file_utils import get_existing_chapter_numbers, resolve_chapter_path

EXPORT_SCHEMA_VERSION = 1


def get_projects_dir() -> Path:
    settings = Settings()
    return Path(settings.projects_dir)


def create_llm_client(kb):
    """Build an LLMClient configured for a project (provider + optional model). Single home
    for the provider/model construction previously repeated across routers."""
    from libriscribe.utils.llm_client import LLMClient

    client = LLMClient(kb.llm_provider)
    if kb.model:
        client.set_model(kb.model)
    return client


def create_utility_client(kb):
    """LLMClient for STRUCTURED tasks (lore intake, classification). Uses the project's
    ``utility_model`` when set, else falls back to the Writing model — so uncensored prose can use
    an aggressive model while lore extraction uses a clean instruct model. Same provider."""
    from libriscribe.utils.llm_client import LLMClient

    client = LLMClient(kb.llm_provider)
    model = (getattr(kb, "utility_model", "") or "").strip() or (kb.model or "").strip()
    if model:
        client.set_model(model)
    return client


_PLACEHOLDER_KEYS = {"", "your_api_key_here", "your-api-key-here", "changeme"}


def resolve_active_model(project_name: str) -> dict[str, Any] | None:
    """Resolve the model that will ACTUALLY run for a project, and where it comes from — so the
    UI can show it plainly (project override vs. the provider default from Settings) instead of a
    silent fallback. Returns None if the project doesn't exist."""
    kb = load_kb(project_name)
    if kb is None:
        return None
    s = Settings()
    provider = kb.llm_provider or "openai"
    default_model = getattr(s, f"{provider}_model", "") or ""
    model = kb.model or default_model
    if provider == "local":
        configured = bool(getattr(s, "local_base_url", ""))
    else:
        key = (getattr(s, f"{provider}_api_key", "") or "").strip()
        configured = bool(key) and key.lower() not in _PLACEHOLDER_KEYS
    utility_set = bool((getattr(kb, "utility_model", "") or "").strip())
    return {
        "provider": provider,
        "model": model,
        "source": "project" if kb.model else "provider default",
        "configured": configured,
        "utility_model": (kb.utility_model.strip() if utility_set else model),
        "utility_source": "utility" if utility_set else "same as writing",
    }


def list_projects() -> list[dict[str, Any]]:
    """Lists all projects with summary info."""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []

    summaries = []
    for entry in sorted(projects_dir.iterdir()):
        if not entry.is_dir():
            continue
        project_data_path = entry / "project_data.json"
        if not project_data_path.exists():
            continue
        kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
        if not kb:
            continue

        progress = inspect_project_progress(entry, kb)
        existing_chapters = get_existing_chapter_numbers(entry)
        total = kb.num_chapters
        if isinstance(total, tuple):
            total = total[1]

        summaries.append({
            "project_name": kb.project_name,
            "title": kb.title,
            "genre": kb.genre,
            "category": kb.category,
            "language": kb.language,
            "next_step": progress.next_step,
            "chapter_count": len(existing_chapters),
            "total_chapters": total if isinstance(total, int) else 0,
        })
    return summaries


def get_project_detail(project_name: str) -> dict[str, Any] | None:
    """Returns detailed project info."""
    project_dir = get_projects_dir() / project_name
    project_data_path = project_dir / "project_data.json"
    if not project_data_path.exists():
        return None
    kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
    if not kb:
        return None

    progress = inspect_project_progress(project_dir, kb)
    existing_chapters = get_existing_chapter_numbers(project_dir)

    return {
        "project_name": kb.project_name,
        "title": kb.title,
        "genre": kb.genre,
        "description": kb.description,
        "category": kb.category,
        "language": kb.language,
        "num_characters": kb.num_characters,
        "worldbuilding_needed": kb.worldbuilding_needed,
        "review_preference": kb.review_preference,
        "book_length": kb.book_length,
        "logline": kb.logline,
        "tone": kb.tone,
        "target_audience": kb.target_audience,
        "num_chapters": kb.num_chapters,
        "target_word_count": kb.target_word_count,
        "llm_provider": kb.llm_provider,
        "model": kb.model,
        "utility_model": kb.utility_model,
        "outline": kb.outline,
        "next_step": progress.next_step,
        "chapter_count": len(existing_chapters),
        "stage_statuses": progress.stage_statuses,
    }


def create_project(data: dict[str, Any]) -> dict[str, Any]:
    """Creates a new project on disk."""
    from libriscribe.agents.project_manager import ProjectManagerAgent

    kb = ProjectKnowledgeBase(**data)
    pm = ProjectManagerAgent()
    pm.initialize_project_with_data(kb)

    # Backfill locations from worldbuilding
    backfill_locations(kb)
    if kb.locations:
        pm.save_project_data()

    return get_project_detail(kb.project_name) or {"project_name": kb.project_name}


def delete_project(project_name: str) -> bool:
    """Deletes a project directory."""
    import shutil
    project_dir = get_projects_dir() / project_name
    if project_dir.exists():
        shutil.rmtree(project_dir)
        return True
    return False


def load_kb(project_name: str) -> ProjectKnowledgeBase | None:
    """Loads and returns the KB for a project."""
    project_dir = get_projects_dir() / project_name
    project_data_path = project_dir / "project_data.json"
    if not project_data_path.exists():
        return None
    return ProjectKnowledgeBase.load_from_file(str(project_data_path))


def save_kb(project_name: str, kb: ProjectKnowledgeBase) -> None:
    """Saves the KB to disk."""
    project_dir = get_projects_dir() / project_name
    kb.project_dir = project_dir
    file_path = str(project_dir / "project_data.json")
    kb.save_to_file(file_path)


def backfill_locations(kb: ProjectKnowledgeBase) -> None:
    """Auto-populate locations from worldbuilding.key_locations."""
    if kb.worldbuilding and kb.worldbuilding.key_locations and not kb.locations:
        for loc_name in kb.worldbuilding.key_locations.replace("\n", ",").split(","):
            loc_name = loc_name.strip()
            if loc_name and loc_name not in kb.locations:
                kb.locations[loc_name] = Location(name=loc_name)


# ─── Import / Export ──────────────────────────────────────────────────────────

def _safe_filename(fname: Any) -> bool:
    return (
        isinstance(fname, str)
        and "/" not in fname
        and "\\" not in fname
        and ".." not in fname
        and not fname.startswith(".")
    )


def export_project_bundle(project_name: str) -> dict[str, Any] | None:
    """Build a single self-contained bundle: the KB plus all prose .md files inlined.

    Excludes API keys (they live outside the project) and retrieval indexes (rebuilt).
    """
    project_dir = get_projects_dir() / project_name
    data_path = project_dir / "project_data.json"
    if not data_path.exists():
        return None

    project_data = json.loads(data_path.read_text(encoding="utf-8"))
    files: dict[str, str] = {}
    for path in sorted(project_dir.glob("*.md")):
        try:
            files[path.name] = path.read_text(encoding="utf-8")
        except Exception:
            pass

    extras: dict[str, str] = {}
    chat = project_dir / "chat_history.json"
    if chat.exists():
        try:
            extras["chat_history.json"] = chat.read_text(encoding="utf-8")
        except Exception:
            pass

    return {
        "app": "libriscribe",
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project_name": project_name,
        "project_data": project_data,
        "files": files,
        "extras": extras,
    }


def import_project_bundle(bundle: dict[str, Any], target_name: str | None = None) -> dict[str, Any]:
    """Recreate a project from an export bundle. Auto-renames on name collision."""
    if not isinstance(bundle, dict) or "project_data" not in bundle:
        raise ValueError("Not a LibriScribe project bundle (missing project_data).")

    schema = bundle.get("schema_version", 1)
    if isinstance(schema, int) and schema > EXPORT_SCHEMA_VERSION:
        raise ValueError(
            f"This bundle was made by a newer version (schema {schema}); supported up to {EXPORT_SCHEMA_VERSION}."
        )

    project_data = bundle.get("project_data")
    if not isinstance(project_data, dict):
        raise ValueError("Bundle 'project_data' is malformed.")

    base = (target_name or project_data.get("project_name") or "imported_project").strip() or "imported_project"
    name = base
    counter = 2
    while (get_projects_dir() / name).exists():
        name = f"{base}-{counter}"
        counter += 1
    renamed = name != base

    project_dir = get_projects_dir() / name
    project_dir.mkdir(parents=True, exist_ok=True)

    project_data = dict(project_data)
    project_data["project_name"] = name
    try:
        kb = ProjectKnowledgeBase.model_validate(project_data)
    except Exception as exc:
        raise ValueError(f"Could not read the project data: {exc}")
    save_kb(name, kb)  # writes project_data.json

    for fname, content in {**(bundle.get("files") or {}), **(bundle.get("extras") or {})}.items():
        if _safe_filename(fname) and isinstance(content, str):
            try:
                (project_dir / fname).write_text(content, encoding="utf-8")
            except Exception:
                pass

    return {"project_name": name, "renamed": renamed, "requested_name": base}


_MD_PATTERNS = [
    (re.compile(r"^#{1,6}\s*", re.M), ""),          # headings
    (re.compile(r"\*\*(.+?)\*\*", re.S), r"\1"),     # bold
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)\*", re.S), r"\1"),  # italic *
    (re.compile(r"__(.+?)__", re.S), r"\1"),         # bold _
    (re.compile(r"(?<!_)_(?!_)(.+?)_", re.S), r"\1"),  # italic _
    (re.compile(r"`(.+?)`", re.S), r"\1"),           # inline code
    (re.compile(r"\[(.+?)\]\((.*?)\)"), r"\1"),       # links -> text
]


def _strip_markdown(text: str) -> str:
    for pattern, repl in _MD_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def export_story_text(project_name: str) -> str | None:
    """Assemble the story as plain text from the chapters as they currently stand."""
    project_dir = get_projects_dir() / project_name
    kb = load_kb(project_name)
    if not kb:
        return None

    parts = [kb.title or project_name, ""]
    for n in sorted(get_existing_chapter_numbers(project_dir)):
        path = resolve_chapter_path(project_dir, n)
        if not path.exists():
            continue
        prose = _strip_markdown(path.read_text(encoding="utf-8")).strip()
        if not prose:
            continue
        chapter = kb.get_chapter(n)
        title = (chapter.title if chapter else "") or ""
        header = f"Chapter {n}: {title}".rstrip(": ").strip()
        parts.extend([header, "", prose, ""])

    return "\n".join(parts).strip() + "\n"


# ─── Version snapshots / rollback (B4 Phase 1) ────────────────────────────────

def _versions_dir(project_name: str) -> Path:
    return get_projects_dir() / project_name / "versions"


def _versions_index_path(project_name: str) -> Path:
    return _versions_dir(project_name) / "versions.json"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")[:40] or "project"


def _load_versions_index(project_name: str) -> list[dict[str, Any]]:
    path = _versions_index_path(project_name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_versions_index(project_name: str, entries: list[dict[str, Any]]) -> None:
    _versions_dir(project_name).mkdir(parents=True, exist_ok=True)
    _versions_index_path(project_name).write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _project_summary_counts(project_name: str) -> dict[str, int]:
    project_dir = get_projects_dir() / project_name
    kb = load_kb(project_name)
    counts = {"chapters": 0, "words": 0, "characters": 0, "locations": 0, "lore": 0, "arcs": 0}
    if kb:
        counts["characters"] = len(kb.characters)
        counts["locations"] = len(kb.locations)
        counts["lore"] = len(kb.lore_entries)
        counts["arcs"] = len(kb.story_arcs)
    counts["chapters"] = len(get_existing_chapter_numbers(project_dir))
    words = 0
    for path in project_dir.glob("chapter_*.md"):
        if path.name.endswith("_original.md"):
            continue
        try:
            words += len(path.read_text(encoding="utf-8").split())
        except Exception:
            pass
    counts["words"] = words
    return counts


def save_project_version(project_name: str, label: str | None = None) -> dict[str, Any]:
    """Snapshot the project as a versioned export bundle in versions/."""
    bundle = export_project_bundle(project_name)
    if bundle is None:
        raise ValueError("Project not found")

    entries = _load_versions_index(project_name)
    version = max((e.get("version", 0) for e in entries), default=0) + 1
    fname = f"{_slug(project_name)}_v{version:03d}_{datetime.now(timezone.utc).strftime('%y%m%d')}.libriscribe.json"

    _versions_dir(project_name).mkdir(parents=True, exist_ok=True)
    (_versions_dir(project_name) / fname).write_text(json.dumps(bundle), encoding="utf-8")

    entry = {
        "version": version,
        "file": fname,
        "label": (label or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": _project_summary_counts(project_name),
    }
    entries.append(entry)
    _save_versions_index(project_name, entries)
    return entry


def list_project_versions(project_name: str) -> list[dict[str, Any]]:
    return sorted(_load_versions_index(project_name), key=lambda e: e.get("version", 0), reverse=True)


def _restore_bundle_in_place(project_name: str, bundle: dict[str, Any]) -> None:
    project_dir = get_projects_dir() / project_name
    project_data = bundle.get("project_data")
    if not isinstance(project_data, dict):
        raise ValueError("Version bundle is malformed")

    project_data = dict(project_data)
    project_data["project_name"] = project_name
    kb = ProjectKnowledgeBase.model_validate(project_data)
    save_kb(project_name, kb)

    # Replace prose: drop current top-level .md, then write the version's files.
    for path in project_dir.glob("*.md"):
        try:
            path.unlink()
        except Exception:
            pass
    for fname, content in {**(bundle.get("files") or {}), **(bundle.get("extras") or {})}.items():
        if _safe_filename(fname) and isinstance(content, str):
            try:
                (project_dir / fname).write_text(content, encoding="utf-8")
            except Exception:
                pass


def restore_project_version(project_name: str, version: int) -> dict[str, Any]:
    """Roll the project back to a saved version. Auto-snapshots current state first."""
    entry = next((e for e in _load_versions_index(project_name) if e.get("version") == version), None)
    if not entry:
        raise ValueError("Version not found")
    bundle_path = _versions_dir(project_name) / entry["file"]
    if not bundle_path.exists():
        raise ValueError("Version file is missing")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    # Safety: snapshot current state so the rollback is itself reversible.
    try:
        save_project_version(project_name, label=f"auto: before restore to v{version:03d}")
    except Exception:
        pass

    _restore_bundle_in_place(project_name, bundle)
    return {"restored_version": version}
