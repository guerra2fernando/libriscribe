from __future__ import annotations

# src/libriscribe/retrieval/index_manager.py

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libriscribe.knowledge_base import ProjectKnowledgeBase

from libriscribe.retrieval.config import get_retrieval_dir, validate_index_path
from libriscribe.retrieval.models import RetrievalDocument, RetrievalChunk, RetrievalConfig
from libriscribe.retrieval.document_builder import DocumentBuilder
from libriscribe.retrieval.chunking import chunk_document
from libriscribe.retrieval.keyword_index import KeywordIndex
from libriscribe.retrieval.cross_reference import CrossReferenceIndex

logger = logging.getLogger(__name__)


class IndexManager:
    """Manages the end-to-end indexing flow: builder -> chunker -> persistence -> indexes fitting."""

    def __init__(self, kb: ProjectKnowledgeBase, project_dir: Path, config: RetrievalConfig | None = None):
        self.kb = kb
        self.project_dir = project_dir
        self.config = config or kb.retrieval or RetrievalConfig()
        self.retrieval_dir = get_retrieval_dir(project_dir, self.config)

        # Paths
        self.docs_file = validate_index_path(project_dir, self.retrieval_dir / "documents.jsonl")
        self.chunks_file = validate_index_path(project_dir, self.retrieval_dir / "chunks.jsonl")
        self.keyword_index_file = validate_index_path(project_dir, self.retrieval_dir / "keyword_index.json")
        self.semantic_index_file = validate_index_path(project_dir, self.retrieval_dir / "semantic_index.json")
        self.xref_index_file = validate_index_path(project_dir, self.retrieval_dir / "cross_references.json")
        self.manifest_file = validate_index_path(project_dir, self.retrieval_dir / "manifests" / "index_state.json")

        # Indexes
        self.keyword_index = KeywordIndex(project_dir)
        self.xref_index = CrossReferenceIndex()

    def rebuild_index(self) -> None:
        """Forces a clean, complete rebuild of all local retrieval files and indexes."""
        self.retrieval_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Build documents
        builder = DocumentBuilder(self.kb, self.project_dir)
        docs = builder.build_all()

        # 2. Chunk documents
        chunks: list[RetrievalChunk] = []
        for doc in docs:
            doc_chunks = chunk_document(
                doc,
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
            chunks.extend(doc_chunks)

        # Build every configured index before replacing any existing index files.
        self.keyword_index.build(chunks)
        semantic_index = None
        if self.config.mode.value in {"semantic", "hybrid"}:
            from libriscribe.retrieval.semantic_index import SemanticIndex
            semantic_index = SemanticIndex(
                self.config.embedding_model,
                local_files_only=self.config.embedding_local_files_only,
            )
            semantic_index.build(chunks)

        # Prepare the cross-reference index before committing files.
        entity_defs = self._get_entity_definitions()
        self.xref_index.build(chunks, entity_defs)

        self._write_jsonl(self.docs_file, [d.model_dump(mode="json") for d in docs])
        self._write_jsonl(self.chunks_file, [c.model_dump(mode="json") for c in chunks])
        self.keyword_index.save_to_file(self.keyword_index_file)
        self.xref_index.save_to_file(self.xref_index_file)
        if semantic_index is not None:
            semantic_index.save_to_file(self.semantic_index_file)
        else:
            self.semantic_index_file.unlink(missing_ok=True)

        # 6. Save build manifest
        self._write_manifest(docs)

    def refresh_index(self) -> bool:
        """Refreshes the index incrementally if changes are detected in sources.

        Returns True if a rebuild/update was executed, False otherwise.
        """
        if (not self.manifest_file.exists() or not self.keyword_index_file.exists()
                or not self.xref_index_file.exists()
                or (self.config.mode.value in {"semantic", "hybrid"} and not self.semantic_index_file.exists())):
            self.rebuild_index()
            return True

        # Check hashes
        builder = DocumentBuilder(self.kb, self.project_dir)
        current_docs = builder.build_all()

        # Load manifest
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            stored_hashes = manifest.get("hashes", {})
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load manifest: %s", e)
            stored_hashes = {}

        # Compare hashes of current docs against stored hashes
        has_changed = False
        if len(current_docs) != len(stored_hashes):
            has_changed = True
        else:
            for doc in current_docs:
                if stored_hashes.get(doc.document_id) != doc.hash:
                    has_changed = True
                    break

        if has_changed:
            self.rebuild_index()
            return True

        return False

    def load_indexes(self) -> None:
        """Loads fitted indexes from local JSON files."""
        self.keyword_index.load_from_file(self.keyword_index_file)
        self.xref_index.load_from_file(self.xref_index_file)
        if self.config.mode.value in {"semantic", "hybrid"}:
            from libriscribe.retrieval.semantic_index import SemanticIndex
            self.semantic_index = SemanticIndex(
                self.config.embedding_model,
                local_files_only=self.config.embedding_local_files_only,
            )
            try:
                self.semantic_index.load_from_file(self.semantic_index_file)
                self.semantic_error = None
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                self.semantic_index = None
                self.semantic_error = str(exc)
        else:
            self.semantic_index = None
            self.semantic_error = None

    def _get_entity_definitions(self) -> dict[str, str]:
        """Assembles the dictionary of entity names and types from characters and worldbuilding."""
        defs = {}
        # Characters
        for char_name in self.kb.characters:
            defs[char_name] = "character"

        # Worldbuilding locations
        if self.kb.worldbuilding and hasattr(self.kb.worldbuilding, "key_locations"):
            locs_text = self.kb.worldbuilding.key_locations or ""
            locations = [loc.strip() for loc in locs_text.replace("\n", ",").split(",") if loc.strip()]
            for loc in locations:
                defs[loc] = "location"

        return defs

    def _write_jsonl(self, file_path: Path, items: list[dict]) -> None:
        """Helper to write a list of dictionaries to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item) + "\n")

    def _write_manifest(self, docs: list[RetrievalDocument]) -> None:
        """Helper to save the indexing state manifest."""
        manifest = {
            "project_name": self.kb.project_name,
            "updated_at": docs[0].updated_at if docs else "",
            "document_count": len(docs),
            "hashes": {doc.document_id: doc.hash for doc in docs},
        }
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)
