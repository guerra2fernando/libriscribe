# src/libriscribe/retrieval/search_service.py

from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from libriscribe.retrieval.models import SearchResult, CrossReferenceEntry, RetrievalConfig
from libriscribe.retrieval.keyword_index import matches_filters


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
            _loaded = ProjectKnowledgeBase.load_from_file(str(project_data_path))
            kb = _loaded if _loaded is not None else ProjectKnowledgeBase(project_name=project_dir.name)
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
        """Searches with keyword, semantic, or weighted normalized hybrid ranking."""
        if mode == "keyword":
            return self.index_manager.keyword_index.search(query, top_k=top_k, filters=filters)
        if mode not in {"semantic", "hybrid"}:
            raise ValueError("mode must be keyword, semantic, or hybrid")
        semantic_index = getattr(self.index_manager, "semantic_index", None)
        if semantic_index is None:
            detail = getattr(self.index_manager, "semantic_error", None)
            raise RuntimeError(detail or "Semantic index is not configured; rebuild in semantic or hybrid mode.")

        keyword_results = self.index_manager.keyword_index.search(
            query, top_k=max(top_k, len(self.index_manager.keyword_index.corpus)), filters=filters
        )
        keyword_by_id = {result.chunk_id: result for result in keyword_results}
        semantic_scores = semantic_index.score(query)
        chunks = self.index_manager.keyword_index.chunks_map
        candidate_ids = set(semantic_scores)
        if mode == "hybrid":
            candidate_ids.update(keyword_by_id)
        if filters:
            candidate_ids = {cid for cid in candidate_ids if cid in chunks and matches_filters(chunks[cid], filters)}

        max_keyword = max((result.score for result in keyword_by_id.values()), default=0.0)
        keyword_weight = self.config.hybrid_keyword_weight
        ranked: list[SearchResult] = []
        for chunk_id in candidate_ids:
            chunk = chunks.get(chunk_id)
            if chunk is None:
                continue
            keyword_score = keyword_by_id.get(chunk_id).score if chunk_id in keyword_by_id else 0.0
            normalized_keyword = keyword_score / max_keyword if max_keyword else 0.0
            cosine = semantic_scores.get(chunk_id, -1.0)
            normalized_semantic = max(0.0, min(1.0, (cosine + 1.0) / 2.0))
            score = normalized_semantic if mode == "semantic" else (
                keyword_weight * normalized_keyword + (1.0 - keyword_weight) * normalized_semantic
            )
            ranked.append(SearchResult(
                chunk_id=chunk.chunk_id, document_id=chunk.document_id, text=chunk.text,
                source_type=chunk.source_type, score=score,
                score_breakdown={"keyword_score": normalized_keyword, "semantic_score": normalized_semantic},
                chapter_number=chunk.chapter_number, scene_number=chunk.scene_number,
                entity_name=chunk.entity_name, tags=chunk.tags, characters=chunk.characters,
                locations=chunk.locations, themes=chunk.themes,
            ))
        ranked.sort(key=lambda result: (-result.score, result.chunk_id))
        return ranked[:top_k]

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
