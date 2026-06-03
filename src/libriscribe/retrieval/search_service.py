# src/libriscribe/retrieval/search_service.py

from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from libriscribe.retrieval.models import SearchResult, CrossReferenceEntry, RetrievalConfig


@runtime_checkable
class SearchService(Protocol):
    def search(
        self,
        query: str,
        *,
        mode: str,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
        task_type: str | None = None,
    ) -> list[SearchResult]:
        """Performs a search over the index."""
        ...

    def search_cross_references(
        self,
        entity_name: str,
        *,
        entity_type: str | None = None,
    ) -> CrossReferenceEntry | None:
        """Looks up an entity in the cross-reference index."""
        ...


class NullSearchService:
    """A no-op search service used when retrieval is disabled or fails to initialize."""

    def search(
        self,
        query: str,
        *,
        mode: str,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
        task_type: str | None = None,
    ) -> list[SearchResult]:
        return []

    def search_cross_references(
        self,
        entity_name: str,
        *,
        entity_type: str | None = None,
    ) -> CrossReferenceEntry | None:
        return None


class SearchServiceImpl:
    """Core local search engine orchestrating keyword index and cross-references queries."""

    def __init__(self, project_dir: Path, config: RetrievalConfig):
        self.project_dir = project_dir
        self.config = config

        # Delayed imports to avoid loading index manager during module import phase
        from libriscribe.retrieval.index_manager import IndexManager
        from libriscribe.knowledge_base import ProjectKnowledgeBase

        # Let's read from the project_data.json if present
        project_data_path = project_dir / "project_data.json"
        if project_data_path.exists():
            kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
        else:
            kb = ProjectKnowledgeBase(project_name=project_dir.name)

        self.index_manager = IndexManager(kb, project_dir, config)
        self.index_manager.load_indexes()

    def search(
        self,
        query: str,
        *,
        mode: str,
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
        task_type: str | None = None,
    ) -> list[SearchResult]:
        """Performs search. For Phase 1, we use Keyword search exclusively."""
        return self.index_manager.keyword_index.search(
            query, top_k=top_k, filters=filters
        )

    def search_cross_references(
        self,
        entity_name: str,
        *,
        entity_type: str | None = None,
    ) -> CrossReferenceEntry | None:
        """Looks up cross-reference entry of an entity."""
        entry = self.index_manager.xref_index.lookup(entity_name)
        if entry and entity_type:
            if entry.entity_type != entity_type:
                return None
        return entry
