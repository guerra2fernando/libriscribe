"""Unit tests for PacingAgent."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from libriscribe.agents.pacing_agent import PacingAgent, PacingAxis, PacingReport


def _make_llm_client(response: str) -> MagicMock:
    client = MagicMock()
    client.generate_content_with_json_repair.return_value = response
    return client


VALID_RESPONSE = json.dumps({
    "axes": [
        {"name": "tension_escalation", "score": 0.7, "chapter_assessments": ["Ch1 good", "Ch3 drops"], "recommendation": "Raise stakes in ch3"},
        {"name": "act_structure", "score": 0.6, "chapter_assessments": ["Act 2 sags"], "recommendation": "Compress act 2 midpoint"},
        {"name": "chapter_length_consistency", "score": 0.9, "chapter_assessments": [], "recommendation": "Lengths are consistent"},
        {"name": "emotional_beat_variety", "score": 0.5, "chapter_assessments": ["Three consecutive sad beats"], "recommendation": "Insert relief beat after ch4"},
        {"name": "narrative_momentum", "score": 0.8, "chapter_assessments": [], "recommendation": "Good forward momentum"},
    ]
})


def _make_pkb(tmp_path: Path) -> MagicMock:
    pkb = MagicMock()
    pkb.project_dir = str(tmp_path)
    pkb.title = "Test Book"
    pkb.genre = "Fantasy"
    pkb.language = "English"
    return pkb


def test_pacing_agent_returns_report(tmp_path: Path) -> None:
    pkb = _make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")
    (tmp_path / "chapter_2.md").write_text("Chapter 2 content.")

    agent = PacingAgent(_make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1, 2])

    assert report is not None
    assert isinstance(report, PacingReport)
    assert len(report.axes) == 5
    assert 0.0 <= report.overall_score <= 1.0
    assert report.priority_fix != ""
    assert (tmp_path / "pacing_report.json").exists()


def test_pacing_agent_returns_none_on_empty_chapters(tmp_path: Path) -> None:
    pkb = _make_pkb(tmp_path)
    agent = PacingAgent(_make_llm_client(VALID_RESPONSE))
    # chapter_1.md does not exist -> no text loaded -> should return None
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is None


def test_pacing_agent_prefers_revised_chapters(tmp_path: Path) -> None:
    pkb = _make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Original chapter 1.")
    (tmp_path / "chapter_1_revised.md").write_text("Revised chapter 1.")

    agent = PacingAgent(_make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None
    call_args = agent.llm_client.generate_content_with_json_repair.call_args[0][0]
    assert "Revised chapter 1." in call_args


def test_get_editor_guidance_contains_low_axes(tmp_path: Path) -> None:
    pkb = _make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")

    agent = PacingAgent(_make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None

    guidance = PacingAgent.get_editor_guidance(report)
    assert "PACING GUIDANCE" in guidance
    assert "emotional_beat_variety" in guidance  # lowest score = 0.5


def test_get_editor_guidance_empty_when_all_scores_high(tmp_path: Path) -> None:
    all_high = json.dumps({"axes": [
        {"name": "tension_escalation", "score": 0.9, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "act_structure", "score": 0.85, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "chapter_length_consistency", "score": 0.95, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "emotional_beat_variety", "score": 0.80, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "narrative_momentum", "score": 0.90, "chapter_assessments": [], "recommendation": "Good"},
    ]})
    pkb = _make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")

    agent = PacingAgent(_make_llm_client(all_high))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None

    guidance = PacingAgent.get_editor_guidance(report)
    assert guidance == ""
