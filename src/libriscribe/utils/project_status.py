import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_FILE_NAME = ".libriscribe_status.json"
STAGE_NAMES = (
    "concept",
    "outline",
    "characters",
    "worldbuilding",
    "chapters",
    "formatting",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_project_status_path(project_dir: Path) -> Path:
    return project_dir / STATUS_FILE_NAME


def load_project_status(project_dir: Path) -> dict[str, Any]:
    status_path = get_project_status_path(project_dir)
    if not status_path.exists():
        return {"version": 1, "updated_at": None, "stages": {}}

    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "updated_at": None, "stages": {}}

    if not isinstance(payload, dict):
        return {"version": 1, "updated_at": None, "stages": {}}

    payload.setdefault("version", 1)
    payload.setdefault("updated_at", None)
    payload.setdefault("stages", {})
    return payload


def save_project_status(project_dir: Path, payload: dict[str, Any]) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    payload["version"] = 1
    payload["updated_at"] = _utc_now()
    status_path = get_project_status_path(project_dir)
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return status_path


def update_stage_status(
    project_dir: Path, stage_name: str, status: str, **extra: Any
) -> Path:
    payload = load_project_status(project_dir)
    stages = payload.setdefault("stages", {})
    stage_payload = stages.get(stage_name, {})
    if not isinstance(stage_payload, dict):
        stage_payload = {}

    stage_payload.update(extra)
    stage_payload["status"] = status
    stage_payload["updated_at"] = _utc_now()
    stages[stage_name] = stage_payload
    return save_project_status(project_dir, payload)


def get_stage_status(project_dir: Path, stage_name: str) -> dict[str, Any]:
    payload = load_project_status(project_dir)
    stages = payload.get("stages", {})
    stage_payload = stages.get(stage_name, {})
    if isinstance(stage_payload, dict):
        return stage_payload
    return {}


def get_interrupted_stage(project_dir: Path) -> str | None:
    stages = load_project_status(project_dir).get("stages", {})
    if not isinstance(stages, dict):
        return None

    for stage_name in STAGE_NAMES:
        stage_payload = stages.get(stage_name, {})
        if isinstance(stage_payload, dict) and stage_payload.get("status") in {
            "in_progress",
            "failed",
        }:
            return stage_name
    return None
