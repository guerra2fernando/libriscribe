"""Tests for StyleResearchAgent and format_style_profile_block."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.agents.style_research import StyleResearchAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase, StyleProfile
from libriscribe.utils.prompts_context import format_style_profile_block


def _make_pkb(inspired_by: str = "") -> ProjectKnowledgeBase:
    return ProjectKnowledgeBase(
        project_name="style-test",
        title="My Book",
        genre="Fantasy",
        description="A hero's journey.",
        language="English",
        inspired_by=inspired_by,
    )


def _make_valid_json_response() -> str:
    return json.dumps({
        "point_of_view": "Close third-person limited, single protagonist.",
        "sentence_length": "Short declarative sentences, rarely exceeding 15 words.",
        "pacing": "Slow burn with sudden violent accelerations.",
        "dialogue_style": "Sparse, unattributed, subtext-heavy.",
        "prose_tone": "Bleak, lyrical, biblical cadence.",
        "structural_patterns": "Non-linear timeline with chapter-length vignettes.",
        "thematic_preoccupations": "Violence, grace, fate, the American West.",
        "what_to_avoid": "Purple prose, extended exposition, comic relief.",
    })


class TestStyleResearchAgentExecute(unittest.TestCase):
    def test_populates_profile_when_inspired_by_set(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        llm_mock.generate_content.return_value = _make_valid_json_response()

        agent = StyleResearchAgent(llm_mock)
        agent.execute(pkb)

        self.assertIsNotNone(pkb.style_profile)
        assert pkb.style_profile is not None
        self.assertEqual(pkb.style_profile.source, "Cormac McCarthy")
        self.assertNotEqual(pkb.style_profile.point_of_view, "")
        self.assertNotEqual(pkb.style_profile.what_to_avoid, "")

    def test_all_eight_fields_populated(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        llm_mock.generate_content.return_value = _make_valid_json_response()

        StyleResearchAgent(llm_mock).execute(pkb)

        sp = pkb.style_profile
        assert sp is not None
        for field in ["point_of_view", "sentence_length", "pacing", "dialogue_style",
                      "prose_tone", "structural_patterns", "thematic_preoccupations", "what_to_avoid"]:
            self.assertNotEqual(getattr(sp, field), "", f"{field} should not be empty")

    def test_noop_when_inspired_by_empty(self) -> None:
        pkb = _make_pkb("")
        llm_mock = MagicMock()

        StyleResearchAgent(llm_mock).execute(pkb)

        llm_mock.generate_content.assert_not_called()
        self.assertIsNone(pkb.style_profile)

    def test_noop_when_inspired_by_whitespace(self) -> None:
        pkb = _make_pkb("   ")
        llm_mock = MagicMock()

        StyleResearchAgent(llm_mock).execute(pkb)

        llm_mock.generate_content.assert_not_called()
        self.assertIsNone(pkb.style_profile)

    def test_noop_when_profile_already_set(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        existing = StyleProfile(source="Cormac McCarthy", point_of_view="existing")
        pkb.style_profile = existing
        llm_mock = MagicMock()

        StyleResearchAgent(llm_mock).execute(pkb)

        llm_mock.generate_content.assert_not_called()
        self.assertEqual(pkb.style_profile.point_of_view, "existing")

    def test_graceful_on_llm_exception(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        llm_mock.generate_content.side_effect = RuntimeError("LLM down")

        agent = StyleResearchAgent(llm_mock)
        agent.execute(pkb)  # must not raise

        self.assertIsNone(pkb.style_profile)

    def test_graceful_on_malformed_json(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        llm_mock.generate_content.return_value = "this is not json at all"

        agent = StyleResearchAgent(llm_mock)
        agent.execute(pkb)

        self.assertIsNone(pkb.style_profile)

    def test_json_embedded_in_prose_is_extracted(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        raw = "Sure! Here is the style profile:\n" + _make_valid_json_response() + "\nHope that helps."
        llm_mock.generate_content.return_value = raw

        StyleResearchAgent(llm_mock).execute(pkb)

        self.assertIsNotNone(pkb.style_profile)

    def test_extra_json_keys_ignored(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        data = json.loads(_make_valid_json_response())
        data["unexpected_key"] = "should be ignored"
        llm_mock = MagicMock()
        llm_mock.generate_content.return_value = json.dumps(data)

        StyleResearchAgent(llm_mock).execute(pkb)

        self.assertIsNotNone(pkb.style_profile)
        self.assertFalse(hasattr(pkb.style_profile, "unexpected_key"))

    def test_llm_empty_response_sets_no_profile(self) -> None:
        pkb = _make_pkb("Cormac McCarthy")
        llm_mock = MagicMock()
        llm_mock.generate_content.return_value = ""

        StyleResearchAgent(llm_mock).execute(pkb)

        self.assertIsNone(pkb.style_profile)


class TestStyleProfilePydanticRoundtrip(unittest.TestCase):
    def test_style_profile_serialises_to_json_and_back(self) -> None:
        pkb = _make_pkb("Tolkien")
        pkb.style_profile = StyleProfile(
            source="Tolkien",
            point_of_view="Omniscient third-person.",
            prose_tone="Epic, archaic, richly descriptive.",
        )
        json_str = pkb.model_dump_json()
        loaded = ProjectKnowledgeBase.model_validate_json(json_str)

        self.assertIsNotNone(loaded.style_profile)
        assert loaded.style_profile is not None
        self.assertEqual(loaded.style_profile.source, "Tolkien")
        self.assertEqual(loaded.style_profile.point_of_view, "Omniscient third-person.")
        self.assertEqual(loaded.style_profile.prose_tone, "Epic, archaic, richly descriptive.")

    def test_no_style_profile_serialises_as_null(self) -> None:
        pkb = _make_pkb()
        data = pkb.model_dump()
        self.assertIsNone(data["style_profile"])

    def test_round_trip_with_null_profile(self) -> None:
        pkb = _make_pkb()
        json_str = pkb.model_dump_json()
        loaded = ProjectKnowledgeBase.model_validate_json(json_str)
        self.assertIsNone(loaded.style_profile)


class TestFormatStyleProfileBlock(unittest.TestCase):
    def test_returns_empty_string_for_none(self) -> None:
        self.assertEqual(format_style_profile_block(None), "")

    def test_returns_empty_string_for_all_empty_fields(self) -> None:
        sp = StyleProfile(source="nobody")
        self.assertEqual(format_style_profile_block(sp), "")

    def test_includes_all_non_empty_fields(self) -> None:
        sp = StyleProfile(
            source="Cormac McCarthy",
            point_of_view="Close third.",
            prose_tone="Bleak.",
            what_to_avoid="Purple prose.",
        )
        block = format_style_profile_block(sp)
        self.assertIn("STYLE REFERENCE", block)
        self.assertIn("Cormac McCarthy", block)
        self.assertIn("Point of view", block)
        self.assertIn("Prose tone", block)
        self.assertIn("Avoid", block)

    def test_omits_empty_fields(self) -> None:
        sp = StyleProfile(source="Author", point_of_view="First person.")
        block = format_style_profile_block(sp)
        self.assertNotIn("Sentence length", block)
        self.assertNotIn("Pacing", block)

    def test_block_starts_with_style_reference_header(self) -> None:
        sp = StyleProfile(source="Author", prose_tone="Dark.")
        block = format_style_profile_block(sp)
        self.assertTrue(block.startswith("STYLE REFERENCE"))


if __name__ == "__main__":
    unittest.main()
