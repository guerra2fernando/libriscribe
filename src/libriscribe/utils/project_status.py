import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

STATUS_FILE_NAME = ".libriscribe_status.json"
STAGE_NAMES = (
    "concept",
    "outline",
    "characters",
    "worldbuilding",
    "chapters",
    "formatting",
)


class ProjectWriteBusy(RuntimeError):
    """Raised when another process already owns the project's write lock."""


@contextmanager
def project_write_lock(project_dir: Path) -> Iterator[None]:
    """Cross-process advisory lock; the OS releases it if the process exits."""
    lock_path = project_dir / ".libriscribe-write.lock"
    handle = lock_path.open("a+b")
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt
            if lock_path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                acquired = True
            except OSError:
                raise ProjectWriteBusy from None
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                raise ProjectWriteBusy from None
        yield
    finally:
        if acquired:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        handle.close()


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
    payload.setdefault("version", 1)
    payload["updated_at"] = _utc_now()
    status_path = get_project_status_path(project_dir)
    fd, temporary_name = tempfile.mkstemp(prefix=".libriscribe-status-", suffix=".tmp", dir=project_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, status_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return status_path


def update_operation_status(
    project_dir: Path,
    *,
    operation: str,
    status: str,
    artifact: str | None = None,
    started_at: str | None = None,
    error: str | None = None,
) -> Path:
    """Record one synchronous service operation without storing prompts or content."""
    payload = load_project_status(project_dir)
    operation_payload: dict[str, Any] = {
        "name": operation,
        "status": status,
        "artifact": artifact,
        "started_at": started_at or _utc_now(),
        "ended_at": _utc_now() if status in {"complete", "failed"} else None,
    }
    if error:
        operation_payload["error"] = error[:300]
    else:
        operation_payload["error"] = None
    payload["operation"] = operation_payload
    return save_project_status(project_dir, payload)


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
