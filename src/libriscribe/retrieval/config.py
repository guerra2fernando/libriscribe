# src/libriscribe/retrieval/config.py

import json
from pathlib import Path
from typing import Any, Dict
from libriscribe.retrieval.models import RetrievalConfig


def get_retrieval_dir(project_dir: Path, config: RetrievalConfig) -> Path:
    """Gets the path to the project's retrieval directory."""
    return project_dir / config.projects_subdir


def load_retrieval_config(project_dir: Path) -> RetrievalConfig:
    """Loads a retrieval configuration from a project directory if it exists, otherwise returns a default."""
    # First find defaults
    default_config = RetrievalConfig()
    config_path = project_dir / default_config.projects_subdir / "retrieval_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RetrievalConfig.model_validate(data)
        except Exception:
            pass
    return default_config


def save_retrieval_config(project_dir: Path, config: RetrievalConfig) -> None:
    """Saves a retrieval configuration to a project directory."""
    retrieval_dir = get_retrieval_dir(project_dir, config)
    retrieval_dir.mkdir(parents=True, exist_ok=True)
    config_path = retrieval_dir / "retrieval_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(mode="json"), f, indent=4)
