"""Tests for narrative graph models: deduplication, negation resolution, empty load."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.narrative.models import NarrativeFact, NarrativeGraph
from libriscribe.narrative.graph_builder import NarrativeGraphBuilder
from libriscribe.knowledge_base import ProjectKnowledgeBase


def _make_fact(entity: str, predicate: str, value: str, chapter: int = 1, negated: bool = False) -> NarrativeFact:
    return NarrativeFact(
        fact_id=NarrativeFact.make_id(entity, predicate, value),
        entity=entity,
        entity_type="character",
        predicate=predicate,
        value=value,
        chapter=chapter,
        evidence_quote="some quote",
        negated=negated,
    )


class TestNarrativeGraphEmpty(unittest.TestCase):
    def test_empty_graph_loads_without_error(self) -> None:
        graph = NarrativeGraph.empty("test-project")
        self.assertEqual(graph.project_name, "test-project")
        self.assertEqual(graph.facts, [])
        self.assertEqual(graph.last_chapter_processed, 0)

    def test_empty_graph_save_and_load_roundtrip(self) -> None:
        graph = NarrativeGraph.empty("roundtrip")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "narrative_graph.json"
            graph.save(path)
            loaded = NarrativeGraph.load(path)
        self.assertEqual(loaded.project_name, "roundtrip")
        self.assertEqual(loaded.facts, [])


class TestNarrativeGraphDeduplication(unittest.TestCase):
    def test_duplicate_facts_not_added_by_builder(self) -> None:
        pkb = ProjectKnowledgeBase(project_name="dup-test")

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            chapter_path = project_dir / "chapter_1.md"
            chapter_path.write_text("Elena looked out at the burning tower.", encoding="utf-8")

            llm_mock = MagicMock()
            raw_facts = json.dumps([
                {
                    "entity": "Elena",
                    "entity_type": "character",
                    "predicate": "is_injured",
                    "value": "left arm",
                    "evidence_quote": "Elena clutched her arm.",
                    "negated": False,
                },
                {
                    "entity": "Elena",
                    "entity_type": "character",
                    "predicate": "is_injured",
                    "value": "left arm",
                    "evidence_quote": "Her arm still ached.",
                    "negated": False,
                },
            ])
            llm_mock.generate_content_with_json_repair.return_value = raw_facts

            builder = NarrativeGraphBuilder(llm_mock, project_dir, pkb)
            new_facts = builder.extract_from_chapter(1)

        self.assertEqual(len(new_facts), 1)

    def test_builder_deduplicates_across_chapters(self) -> None:
        pkb = ProjectKnowledgeBase(project_name="cross-chapter-dup")

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            existing_graph = NarrativeGraph.empty("cross-chapter-dup")
            existing_fact = _make_fact("Elena", "is_injured", "left arm", chapter=1)
            existing_graph.add_fact(existing_fact)
            existing_graph.save(project_dir / "narrative_graph.json")

            chapter_path = project_dir / "chapter_2.md"
            chapter_path.write_text("Elena still struggled with her arm.", encoding="utf-8")

            llm_mock = MagicMock()
            same_fact = json.dumps([
                {
                    "entity": "Elena",
                    "entity_type": "character",
                    "predicate": "is_injured",
                    "value": "left arm",
                    "evidence_quote": "still struggled",
                    "negated": False,
                }
            ])
            llm_mock.generate_content_with_json_repair.return_value = same_fact

            builder = NarrativeGraphBuilder(llm_mock, project_dir, pkb)
            new_facts = builder.extract_from_chapter(2)

        self.assertEqual(new_facts, [])


class TestNarrativeGraphNegation(unittest.TestCase):
    def test_negated_fact_cancels_prior_fact(self) -> None:
        graph = NarrativeGraph.empty("neg-test")
        injury = _make_fact("Elena", "is_injured", "left arm", chapter=1, negated=False)
        recovery = _make_fact("Elena", "is_injured", "left arm", chapter=3, negated=True)
        graph.add_fact(injury)
        graph.add_fact(recovery)

        active = graph.get_active_facts()
        active_predicates = [(f.entity, f.predicate) for f in active]
        self.assertNotIn(("Elena", "is_injured"), active_predicates)

    def test_unrelated_fact_not_cancelled(self) -> None:
        graph = NarrativeGraph.empty("neg-test2")
        dead = _make_fact("Kael", "is_dead", "killed in battle", chapter=2)
        recovery = _make_fact("Elena", "is_injured", "left arm", chapter=3, negated=True)
        graph.add_fact(dead)
        graph.add_fact(recovery)

        active = graph.get_active_facts()
        entities = [f.entity for f in active]
        self.assertIn("Kael", entities)

    def test_later_positive_fact_not_cancelled_by_unrelated_negation(self) -> None:
        graph = NarrativeGraph.empty("neg-test3")
        fact1 = _make_fact("Elena", "knows", "Kael is a traitor", chapter=4, negated=False)
        negation = _make_fact("Elena", "is_injured", "arm", chapter=5, negated=True)
        graph.add_fact(fact1)
        graph.add_fact(negation)

        active = graph.get_active_facts()
        knows_facts = [f for f in active if f.predicate == "knows"]
        self.assertEqual(len(knows_facts), 1)

    def test_negated_facts_excluded_from_active(self) -> None:
        graph = NarrativeGraph.empty("neg-test4")
        negation = _make_fact("Elena", "is_injured", "arm", chapter=2, negated=True)
        graph.add_fact(negation)

        active = graph.get_active_facts()
        negated_active = [f for f in active if f.negated]
        self.assertEqual(negated_active, [])


if __name__ == "__main__":
    unittest.main()
