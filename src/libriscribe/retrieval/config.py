# src/libriscribe/retrieval/config.py

import json
import logging
from pathlib import Path, PurePath
from libriscribe.retrieval.models import RetrievalConfig

logger = logging.getLogger(__name__)


def get_retrieval_dir(project_dir: Path, config: RetrievalConfig) -> Path:
    """Return a project-confined index directory, rejecting traversal and links."""
    root = project_dir.resolve()
    relative = Path(config.projects_subdir)
    if not config.projects_subdir or relative.is_absolute() or PurePath(config.projects_subdir).is_absolute():
        raise ValueError("Retrieval index directory must be a nonempty relative path.")
    if any(part in {"..", ""} for part in relative.parts):
        raise ValueError("Retrieval index directory must not contain traversal components.")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root)
        current = root
        for part in relative.parts:
            current = current / part
            if current.exists() or current.is_symlink():
                current.resolve(strict=True).relative_to(root)
    except (OSError, ValueError):
        raise ValueError("Retrieval index directory must stay inside the project directory.") from None
    return candidate


def validate_index_path(project_dir: Path, path: Path) -> Path:
    """Validate an index file path, including existing files and symlink targets."""
    root = project_dir.resolve()
    try:
        path.resolve(strict=False).relative_to(root)
    except (OSError, ValueError):
        raise ValueError("Retrieval index paths must stay inside the project directory.") from None
    return path


def load_retrieval_config(project_dir: Path) -> RetrievalConfig:
    """Loads a retrieval configuration from a project directory if it exists, otherwise returns a default."""
    # First find defaults
    default_config = RetrievalConfig()
    config_path = validate_index_path(
        project_dir,
        get_retrieval_dir(project_dir, default_config) / "retrieval_config.json",
    )
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RetrievalConfig.model_validate(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load retrieval config from %s: %s", config_path, e)
    return default_config


def save_retrieval_config(project_dir: Path, config: RetrievalConfig) -> None:
    """Saves a retrieval configuration to a project directory."""
    retrieval_dir = get_retrieval_dir(project_dir, config)
    retrieval_dir.mkdir(parents=True, exist_ok=True)
    config_path = validate_index_path(project_dir, retrieval_dir / "retrieval_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(mode="json"), f, indent=4)
