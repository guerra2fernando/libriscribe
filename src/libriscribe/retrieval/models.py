from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RetrievalMode(str, Enum):
    DISABLED = "disabled"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class RetrievalBackend(str, Enum):
    LOCAL = "local"
    CHROMA = "chroma"
    MONGODB = "mongodb"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class EmbeddingProviderType(str, Enum):
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OPENAI = "openai"


class RetrievalConfig(BaseModel):
    enabled: bool = False
    mode: RetrievalMode = RetrievalMode.DISABLED
    backend: RetrievalBackend = RetrievalBackend.LOCAL
    auto_index: bool = True
    top_k: int = 6
    max_context_tokens: int = 1800
    embedding_provider: EmbeddingProviderType = EmbeddingProviderType.SENTENCE_TRANSFORMERS
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 800
    chunk_overlap: int = 120
    include_chapter_text: bool = True
    include_chapter_summaries: bool = True
    include_outline: bool = True
    include_characters: bool = True
    include_worldbuilding: bool = True
    include_cross_references: bool = True
    projects_subdir: str = ".libriscribe_retrieval"


class RetrievalDocument(BaseModel):
    document_id: str
    project_name: str
    source_type: str
    title: str
    text: str
    source_path: str | None = None
    chapter_number: int | None = None
    scene_number: int | None = None
    entity_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    updated_at: str
    hash: str


class RetrievalChunk(BaseModel):
    chunk_id: str
    document_id: str
    project_name: str
    text: str
    source_type: str
    chunk_index: int
    chapter_number: int | None = None
    scene_number: int | None = None
    entity_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    token_estimate: int = 0
    hash: str


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    source_type: str
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    chapter_number: int | None = None
    scene_number: int | None = None
    entity_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)


class CrossReferenceEntry(BaseModel):
    entity_name: str
    entity_type: str
    referenced_in_chunks: list[str] = Field(default_factory=list)
    referenced_in_chapters: list[int] = Field(default_factory=list)
    related_entities: list[str] = Field(default_factory=list)


class RetrievalContextPack(BaseModel):
    task_type: str
    project_context: str
    query: str | None = None
    selected_results: list[SearchResult] = Field(default_factory=list)
    continuity_notes: list[str] = Field(default_factory=list)
    character_state_notes: list[str] = Field(default_factory=list)
    unresolved_threads: list[str] = Field(default_factory=list)
    token_estimate: int = 0
