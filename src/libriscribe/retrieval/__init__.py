# src/libriscribe/retrieval/__init__.py

from libriscribe.retrieval.models import (
    RetrievalMode,
    RetrievalBackend,
    EmbeddingProviderType,
    RetrievalConfig,
    RetrievalDocument,
    RetrievalChunk,
    SearchResult,
    CrossReferenceEntry,
    RetrievalContextPack,
)

from libriscribe.retrieval.search_service import (
    SearchService,
    NullSearchService,
    SearchServiceImpl,
)


