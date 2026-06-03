from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.knowledge_base import ProjectKnowledgeBase, Character, Chapter, Scene, Worldbuilding
from libriscribe.retrieval.models import (
    RetrievalConfig,
    RetrievalMode,
    RetrievalDocument,
    RetrievalChunk,
)
from libriscribe.retrieval.chunking import chunk_document
from libriscribe.retrieval.document_builder import DocumentBuilder
from libriscribe.retrieval.keyword_index import KeywordIndex
from libriscribe.retrieval.cross_reference import CrossReferenceIndex
from libriscribe.retrieval.index_manager import IndexManager


class RetrievalPipelineTests(unittest.TestCase):
    def test_models_parsing_and_defaults(self) -> None:
        """Verifies model loading, validation, and serialization defaults."""
        config = RetrievalConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.mode, RetrievalMode.DISABLED)
        self.assertEqual(config.chunk_size, 800)

        doc = RetrievalDocument(
            document_id="doc-1",
            project_name="test-project",
            source_type="character_profile",
            title="Protagonist Profile",
            text="Mira Thorn was born in the Floating Isles.",
            updated_at="2026-06-03T22:00:00Z",
            hash="abc123hash",
        )
        self.assertEqual(doc.document_id, "doc-1")
        self.assertEqual(doc.tags, [])

        chunk = RetrievalChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            project_name="test-project",
            text="Mira Thorn was born.",
            source_type="character_profile",
            chunk_index=0,
            hash="xyzchunkhash",
        )
        self.assertEqual(chunk.chunk_index, 0)

    def test_document_builder_pipeline(self) -> None:
        """Ensures DocumentBuilder parses KB fields and prose files properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Setup ProjectKnowledgeBase
            kb = ProjectKnowledgeBase(
                project_name="builder-test",
                title="Mira's Odyssey",
                description="An epic fantasy story.",
                genre="Fantasy",
                category="Fiction",
                worldbuilding_needed=True,
            )
            # Add character
            mira = Character(
                name="Mira Thorn",
                role="Protagonist",
                age="19",
                background="Raised on a flying vessel.",
            )
            kb.add_character(mira)

            kb.worldbuilding = Worldbuilding(
                geography="The Floating Isles are a chain of levitating rocks.",
                key_locations="Castle Iron, The Archive Vault, vessel deck",
            )

            # Add chapter with scene
            ch = Chapter(chapter_number=1, title="The Descent", summary="Mira falls to the surface.")
            sc = Scene(scene_number=1, summary="Mira fights wind-spirits.", setting="Vessel deck")
            ch.scenes.append(sc)
            kb.add_chapter(ch)

            # Add a chapter prose file
            chapter_file = project_dir / "chapter_1.md"
            chapter_file.write_text(
                "Mira Thorn stepped onto the vessel deck. Inside the Archive Vault, everything was quiet.",
                encoding="utf-8",
            )

            builder = DocumentBuilder(kb, project_dir)
            docs = builder.build_all()

            # Verify that expected documents were built
            doc_ids = {d.document_id for d in docs}
            self.assertIn("project_metadata", doc_ids)
            self.assertIn("char_mira_thorn", doc_ids)
            self.assertIn("world_geography", doc_ids)
            self.assertIn("world_key_locations", doc_ids)
            self.assertIn("chapter_1_summary", doc_ids)
            self.assertIn("chapter_1_scene_1_summary", doc_ids)
            self.assertIn("prose_chapter_1_md", doc_ids)

            # Verify entity tagging enrichment
            char_doc = next(d for d in docs if d.document_id == "char_mira_thorn")
            self.assertIn("character", char_doc.tags)

            prose_doc = next(d for d in docs if d.document_id == "prose_chapter_1_md")
            self.assertIn("Mira Thorn", prose_doc.characters)
            self.assertIn("vessel deck", prose_doc.locations)

    def test_chunking_integrity(self) -> None:
        """Verifies text chunk splitter respects limits and paragraph boundaries."""
        doc = RetrievalDocument(
            document_id="doc-chunk-test",
            project_name="chunk-test",
            source_type="worldbuilding",
            title="History",
            text="First sentence. Second sentence.\n\nAnother paragraph here.",
            updated_at="2026-06-03",
            hash="123",
        )
        # Small chunk size to force split
        chunks = chunk_document(doc, chunk_size=30, chunk_overlap=10)
        self.assertTrue(len(chunks) >= 2)
        for chunk in chunks:
            self.assertEqual(chunk.document_id, "doc-chunk-test")
            self.assertTrue(len(chunk.text) <= 50)  # rough limit check

    def test_keyword_and_fallback_search(self) -> None:
        """Validates BM25 and Custom TF-IDF fallbacks and filters."""
        # Setup dummy chunks
        chunks = [
            RetrievalChunk(
                chunk_id="c1",
                document_id="doc1",
                project_name="search-test",
                text="Mira Thorn was exploring Castle Iron.",
                source_type="prose",
                chunk_index=0,
                hash="h1",
                characters=["Mira Thorn"],
                locations=["Castle Iron"],
            ),
            RetrievalChunk(
                chunk_id="c2",
                document_id="doc2",
                project_name="search-test",
                text="The Archive Vault holds ancient keys.",
                source_type="worldbuilding",
                chunk_index=0,
                hash="h2",
                locations=["Archive Vault"],
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            keyword_index = KeywordIndex(Path(tmpdir))
            keyword_index.build(chunks)

            # Search "Mira"
            results = keyword_index.search("Mira", top_k=5)
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0].chunk_id, "c1")

            # Search with filter
            results_filtered = keyword_index.search("keys", filters={"source_type": "prose"})
            self.assertEqual(len(results_filtered), 0)

            results_wb = keyword_index.search("keys", filters={"source_type": "worldbuilding"})
            self.assertEqual(len(results_wb), 1)
            self.assertEqual(results_wb[0].chunk_id, "c2")

    def test_cross_reference_index(self) -> None:
        """Ensures cross-referencing maps entity occurrences and relations correctly."""
        chunks = [
            RetrievalChunk(
                chunk_id="c1",
                document_id="doc1",
                project_name="xref-test",
                text="Mira Thorn and Caleb met in Castle Iron.",
                source_type="prose",
                chunk_index=0,
                chapter_number=1,
                hash="h1",
                characters=["Mira Thorn", "Caleb"],
                locations=["Castle Iron"],
            )
        ]
        entity_defs = {
            "Mira Thorn": "character",
            "Caleb": "character",
            "Castle Iron": "location",
        }

        xref = CrossReferenceIndex()
        xref.build(chunks, entity_defs)

        mira_entry = xref.lookup("Mira Thorn")
        self.assertIsNotNone(mira_entry)
        assert mira_entry is not None
        self.assertEqual(mira_entry.entity_type, "character")
        self.assertIn(1, mira_entry.referenced_in_chapters)
        self.assertIn("Caleb", mira_entry.related_entities)
        self.assertIn("Castle Iron", mira_entry.related_entities)

    def test_index_manager_e2e_rebuild_and_refresh(self) -> None:
        """Tests end-to-end IndexManager rebuild and incremental hash-based updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            kb = ProjectKnowledgeBase(
                project_name="e2e-project",
                title="The Black Key",
                worldbuilding_needed=True,
            )
            kb.worldbuilding = Worldbuilding(
                geography="The Dark Lands are full of ash.",
                key_locations="Castle Iron",
            )
            chapter_file = project_dir / "chapter_1.md"
            chapter_file.write_text("The wind was howling around Castle Iron.", encoding="utf-8")

            config = RetrievalConfig(enabled=True, mode=RetrievalMode.KEYWORD)
            manager = IndexManager(kb, project_dir, config)

            # Rebuild
            manager.rebuild_index()

            # Verify files created
            self.assertTrue(manager.docs_file.exists())
            self.assertTrue(manager.chunks_file.exists())
            self.assertTrue(manager.keyword_index_file.exists())
            self.assertTrue(manager.xref_index_file.exists())
            self.assertTrue(manager.manifest_file.exists())

            # Load indexes to verify they exist and match
            manager.load_indexes()
            results = manager.keyword_index.search("howling")
            self.assertEqual(len(results), 1)

            # Refresh without changes -> should return False (no rebuild)
            refreshed = manager.refresh_index()
            self.assertFalse(refreshed)

            # Modify chapter file -> refresh should detect change and rebuild (return True)
            chapter_file.write_text("The wind was quiet around Castle Iron.", encoding="utf-8")
            refreshed = manager.refresh_index()
            self.assertTrue(refreshed)

            # Verify newly indexed word
            manager.load_indexes()
            results_quiet = manager.keyword_index.search("quiet")
            self.assertEqual(len(results_quiet), 1)


if __name__ == "__main__":
    unittest.main()
