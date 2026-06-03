import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, ValidationError, validator

from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.settings import Settings


class StageMode(str, Enum):
    AUTO = "auto"
    PROMPT = "prompt"
    SKIP = "skip"


class ApprovalMode(str, Enum):
    AUTO = "auto"
    PROMPT = "prompt"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"


class ExpertProjectConfig(BaseModel):
    project_name: str
    title: str = "Untitled"
    genre: str = "Unknown Genre"
    description: str = "No description provided."
    category: str = "Unknown Category"
    language: str = "English"
    num_characters: Union[int, str] = 0
    num_characters_str: str = ""
    worldbuilding_needed: bool = False
    review_preference: str = "AI"
    book_length: str = ""
    logline: str = "No logline available"
    tone: str = "Informative"
    target_audience: str = "General"
    num_chapters: Union[int, str] = 1
    num_chapters_str: str = ""
    llm_provider: str = "openai"
    dynamic_questions: Dict[str, str] = Field(default_factory=dict)

    @validator("review_preference", pre=True)
    def normalize_review_preference(cls, value: Any) -> str:
        if value is None:
            return "AI"

        normalized = str(value).strip().lower()
        if normalized.startswith("human"):
            return "Human"
        if normalized.startswith("ai"):
            return "AI"
        raise ValueError("review_preference must be 'AI' or 'Human'")

    @validator("llm_provider", pre=True)
    def normalize_llm_provider(cls, value: Any) -> str:
        if value is None:
            return "openai"
        return str(value).strip().lower()


class ExpertWorkflowConfig(BaseModel):
    concept_approval: ApprovalMode = ApprovalMode.AUTO
    outline_review: ApprovalMode = ApprovalMode.AUTO
    character_generation: StageMode = StageMode.AUTO
    worldbuilding_generation: StageMode = StageMode.AUTO
    chapter_writing: StageMode = StageMode.AUTO
    formatting: StageMode = StageMode.AUTO
    output_format: OutputFormat = OutputFormat.MARKDOWN


class ExpertConfig(BaseModel):
    version: int = 1
    project: ExpertProjectConfig
    workflow: ExpertWorkflowConfig = Field(default_factory=ExpertWorkflowConfig)


def _load_raw_config(file_path: Path) -> Dict[str, Any]:
    content = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        payload = json.loads(content)
    elif suffix in {".yml", ".yaml"}:
        payload = yaml.safe_load(content) or {}
    else:
        raise ValueError("Unsupported config format. Use .json, .yml, or .yaml.")

    if not isinstance(payload, dict):
        raise ValueError(
            "Configuration file must contain a JSON/YAML object at the top level."
        )

    return payload


def load_expert_config(config_path: str) -> ExpertConfig:
    file_path = Path(config_path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    payload = _load_raw_config(file_path)
    return ExpertConfig.model_validate(payload)


def build_project_knowledge_base(config: ExpertConfig) -> ProjectKnowledgeBase:
    return ProjectKnowledgeBase(**config.project.model_dump())


def get_recent_expert_config_path(settings: Optional[Settings] = None) -> Path:
    settings = settings or Settings()
    return Path(settings.projects_dir).parent / ".libriscribe_last_config.json"


def save_recent_expert_config(
    config: ExpertConfig, settings: Optional[Settings] = None
) -> Path:
    state_path = get_recent_expert_config_path(settings)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(config.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return state_path


def load_recent_expert_config(
    settings: Optional[Settings] = None,
) -> Optional[ExpertConfig]:
    state_path = get_recent_expert_config_path(settings)
    if not state_path.exists():
        return None

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        return ExpertConfig.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return None
