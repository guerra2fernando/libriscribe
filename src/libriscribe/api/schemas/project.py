from __future__ import annotations

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    project_name: str
    title: str = "Untitled"
    genre: str = "Unknown Genre"
    description: str = "No description provided."
    category: str = "Fiction"
    language: str = "English"
    num_characters: int | str = 0
    worldbuilding_needed: bool = False
    review_preference: str = "AI"
    book_length: str = "Novel"
    tone: str = "Informative"
    target_audience: str = "General"
    num_chapters: int | str = 1
    llm_provider: str = "openai"
    model: str = ""
    fallback_chain: list[str] = Field(default_factory=list)
    chapter_writing_mode: str = "prompt"
    chapter_error_mode: str = "stop"
    dynamic_questions: dict[str, str] = Field(default_factory=dict)


class ProjectSummary(BaseModel):
    project_name: str
    title: str
    genre: str
    category: str
    language: str
    next_step: str = "concept"
    chapter_count: int = 0
    total_chapters: int = 0


class ProjectDetail(BaseModel):
    project_name: str
    title: str
    genre: str
    description: str
    category: str
    language: str
    num_characters: int | tuple[int, int] | str = 0
    worldbuilding_needed: bool = False
    review_preference: str = "AI"
    book_length: str = "Novel"
    logline: str = ""
    tone: str = "Informative"
    target_audience: str = "General"
    num_chapters: int | tuple[int, int] | str = 1
    target_word_count: int | None = None
    llm_provider: str = "openai"
    model: str = ""
    utility_model: str = ""
    outline: str = ""
    next_step: str = "concept"
    chapter_count: int = 0
    stage_statuses: dict[str, str] = Field(default_factory=dict)


class ProjectProgress(BaseModel):
    concept_complete: bool = False
    outline_complete: bool = False
    characters_required: bool = False
    characters_complete: bool = False
    worldbuilding_required: bool = False
    worldbuilding_complete: bool = False
    chapter_numbers_complete: list[int] = Field(default_factory=list)
    missing_chapters: list[int] = Field(default_factory=list)
    manuscript_exists: bool = False
    next_step: str = "concept"
    stage_statuses: dict[str, str] = Field(default_factory=dict)


class ChapterMeta(BaseModel):
    chapter_number: int
    title: str = ""
    has_content: bool = False
    has_revised: bool = False
    word_count: int = 0


class ChapterContent(BaseModel):
    chapter_number: int
    title: str = ""
    content: str = ""
    word_count: int = 0


class ProjectFile(BaseModel):
    name: str
    size: int = 0
    modified_at: str = ""


class CostEntry(BaseModel):
    timestamp: str = ""
    provider: str = ""
    model: str = ""
    operation: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


class CostSummary(BaseModel):
    entries: list[CostEntry] = Field(default_factory=list)
    total_cost: float = 0.0
    total_tokens: int = 0
