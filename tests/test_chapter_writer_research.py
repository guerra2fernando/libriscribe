"""Tests for research_results.md injection in ChapterWriterAgent._write_scene."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from libriscribe.agents.chapter_writer import ChapterWriterAgent


def _make_pkb(project_dir: Path) -> MagicMock:
    pkb = MagicMock()
    pkb.project_dir = str(project_dir)
    pkb.project_name = "test_proj"
    pkb.title = "Test Book"
    pkb.genre = "Fantasy"
    pkb.category = "Fiction"
    pkb.language = "English"
    pkb.tone = "Serious"
    pkb.target_audience = "Adults"
    pkb.dynamic_questions = {}
    pkb.style_profile = None
    pkb.worldbuilding = None
    pkb.characters = {}
    pkb.get_character = MagicMock(return_value=None)
    return pkb


def _run_chapter_writer(pkb: MagicMock, tmp_path: Path) -> list[str]:
    from libriscribe.knowledge_base import Chapter, Scene
    from libriscribe.narrative.models import NarrativeGraph

    captured: list[str] = []

    llm = MagicMock()
    llm.generate_content.side_effect = lambda prompt, max_tokens=2000: (
        captured.append(prompt) or "Scene content."
    )
    llm.generate_content_with_json_repair.return_value = '{"axes": []}'

    agent = ChapterWriterAgent(llm)

    scene = Scene(
        scene_number=1,
        summary="Hero enters the cave",
        characters=[],
        setting="cave",
        goal="find artifact",
        emotional_beat="curious",
    )
    chapter = Chapter(
        chapter_number=1,
        title="The Cave",
        summary="Hero explores the cave",
        scenes=[scene],
    )
    pkb.get_chapter = MagicMock(return_value=chapter)
    pkb.chapters = {1: chapter}

    empty_graph = NarrativeGraph(project_name="test_proj", facts=[])

    with (
        patch.object(agent, "_load_narrative_graph", return_value=empty_graph),
        patch.object(agent, "_build_style_hints", return_value=""),
        patch.object(agent, "_maybe_rewrite_scene", side_effect=lambda scene_content, **kw: scene_content),
    ):
        agent.execute(pkb, chapter_number=1, output_path=str(tmp_path / "chapter_1.md"))

    return captured


def test_research_block_injected_when_file_present(tmp_path: Path) -> None:
    research_text = "## AI-Generated Summary\n\nMagic systems require internal consistency."
    (tmp_path / "research_results.md").write_text(research_text)

    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    assert any("RESEARCH CONTEXT" in p for p in captured), (
        f"Expected 'RESEARCH CONTEXT' in scene prompt. Prompts captured: {len(captured)}"
    )


def test_research_block_absent_when_file_missing(tmp_path: Path) -> None:
    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    assert not any("RESEARCH CONTEXT" in p for p in captured)


def test_research_block_truncated_at_1200_chars(tmp_path: Path) -> None:
    long_text = "X" * 2000
    (tmp_path / "research_results.md").write_text(long_text)

    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    research_prompts = [p for p in captured if "RESEARCH CONTEXT" in p]
    assert research_prompts, "RESEARCH CONTEXT block should appear in prompt"
    assert "[...truncated]" in research_prompts[0]
