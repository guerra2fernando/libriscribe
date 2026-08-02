# PacingAgent + ResearchContext + Pyright Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PacingAgent (cross-chapter arc analysis injected before editing), wire research_results.md into scene prompts via ChapterWriterAgent, and eliminate all 39 Pyright errors across the codebase.

**Architecture:** PacingAgent is a standalone agent called once per chapter in AI-review mode (analysing all chapters written so far), producing a `pacing_report.json` and a `PACING GUIDANCE:` block injected into the editor prompt. ResearchContext wiring reads `research_results.md` from the project directory inside `_write_scene()` and prepends a truncated block to the scene prompt prefix_parts. Pyright fixes are surgical null-guards and type annotations — no architectural changes.

**Tech Stack:** Python 3.10+, Pydantic v2, Rich console, LLMClient (existing), ProjectKnowledgeBase (existing), existing agent patterns from `content_quality.py`.

## Global Constraints

- Python >=3.10 — f-strings OK, walrus operator OK
- Pydantic v2 — `model_dump_json`, `model_dump`, `Field(default_factory=...)`, `BaseModel`
- All agents: `class XAgent(Agent)`, `__init__(self, llm_client: LLMClient)`, `execute(self, project_knowledge_base: ProjectKnowledgeBase, ...) -> ...`
- max_tokens for new LLM analysis calls: 4000 minimum
- No new dependencies — only packages in setup.py
- Tests in `tests/` — pytest, mock LLMClient with `unittest.mock.MagicMock`
- Docusaurus docs: `docs/docs/agents/<name>.md`, sidebar_position must not conflict with existing 1–17
- gh-pages deploy: `cd docs && npm run build && npx gh-pages -d build`
- Commit style: conventional commits (`feat:`, `fix:`, `docs:`)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/libriscribe/agents/pacing_agent.py` | **Create** | PacingAgent class, PacingReport/PacingAxis models, LLM prompt |
| `src/libriscribe/agents/chapter_writer.py` | **Modify** | `_write_scene()` — add research_results block to prefix_parts; `execute()` — build research block |
| `src/libriscribe/agents/project_manager.py` | **Modify** | Register pacing agent; add `run_pacing_analysis()`; update `write_and_review_chapter()` and `edit_chapter()` |
| `src/libriscribe/agents/editor.py` | **Modify** | Accept `pacing_guidance: str = ""` param; inject before prompt; fix Path\|None lines 30, 95; add `extract_scene_titles` |
| `src/libriscribe/agents/character_generator.py` | **Modify** | Fix line 55 (str has no .items()), line 155 (Path\|None), line 156 (list vs dict) |
| `src/libriscribe/agents/formatting_optimized.py` | **Modify** | Fix line 26 (PKB\|None null guard) |
| `src/libriscribe/agents/worldbuilding.py` | **Modify** | Fix line 135 (Path\|None) |
| `src/libriscribe/agents/style_editor.py` | **Modify** | Fix line 23 (Path\|None) |
| `src/libriscribe/main.py` | **Modify** | Fix line 1453 (RetrievalMode.KEYWORD); fix line 1500 (SearchResult.text not .title) |
| `src/libriscribe/retrieval/search_service.py` | **Modify** | Fix line 73 (PKB\|None null guard) |
| `src/libriscribe/utils/llm_client.py` | **Modify** | Fix lines 303, 319 (type narrowing for client), 325 (union .text), 331 (google models), 7 (genai import) |
| `src/libriscribe/utils/prompt_integration.py` | **Modify** | Fix line 49 (llm_client not on mixin — use getattr) |
| `tests/test_pacing_agent.py` | **Create** | Unit tests for PacingAgent |
| `tests/test_chapter_writer_research.py` | **Create** | Unit test: research block injection |
| `docs/docs/agents/pacing-agent.md` | **Create** | Docusaurus agent doc (sidebar_position: 18) |
| `docs/docs/agents/chapter-writer.md` | **Modify** | Add research context + pacing guidance sections |
| `docs/docs/agents/researcher.md` | **Modify** | Add downstream usage section |
| `README.md` | **Modify** | Add PacingAgent to architecture diagram and agent table |

---

## Task 1: PacingAgent — model and LLM prompt

**Files:**
- Create: `src/libriscribe/agents/pacing_agent.py`
- Test: `tests/test_pacing_agent.py`

**Interfaces:**
- Produces: `PacingAxis(name, score, chapter_assessments, recommendation)` Pydantic model
- Produces: `PacingReport(chapter_numbers, axes, overall_score, priority_fix)` Pydantic model
- Produces: `PacingAgent.execute(project_knowledge_base: ProjectKnowledgeBase, chapter_numbers: list[int]) -> Optional[PacingReport]`
- Produces: `PacingAgent.get_editor_guidance(report: PacingReport) -> str` — returns `PACING GUIDANCE:` block

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pacing_agent.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from libriscribe.agents.pacing_agent import PacingAgent, PacingReport, PacingAxis


def make_llm_client(response: str) -> MagicMock:
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


def make_pkb(tmp_path: Path) -> MagicMock:
    pkb = MagicMock()
    pkb.project_dir = tmp_path
    pkb.title = "Test Book"
    pkb.genre = "Fantasy"
    pkb.language = "English"
    return pkb


def test_pacing_agent_returns_report(tmp_path):
    pkb = make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")
    (tmp_path / "chapter_2.md").write_text("Chapter 2 content.")

    agent = PacingAgent(make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1, 2])

    assert report is not None
    assert isinstance(report, PacingReport)
    assert len(report.axes) == 5
    assert 0.0 <= report.overall_score <= 1.0
    assert report.priority_fix != ""
    assert (tmp_path / "pacing_report.json").exists()


def test_pacing_agent_returns_none_on_empty_chapters(tmp_path):
    pkb = make_pkb(tmp_path)
    agent = PacingAgent(make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is None


def test_pacing_agent_prefers_revised_chapters(tmp_path):
    pkb = make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Original chapter 1.")
    (tmp_path / "chapter_1_revised.md").write_text("Revised chapter 1.")

    agent = PacingAgent(make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None
    # Verify the revised text was used (check via LLM call args)
    call_args = agent.llm_client.generate_content_with_json_repair.call_args[0][0]
    assert "Revised chapter 1." in call_args


def test_get_editor_guidance_contains_low_axes(tmp_path):
    pkb = make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")

    agent = PacingAgent(make_llm_client(VALID_RESPONSE))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None

    guidance = PacingAgent.get_editor_guidance(report)
    assert "PACING GUIDANCE" in guidance
    assert "emotional_beat_variety" in guidance  # lowest score = 0.5


def test_get_editor_guidance_empty_when_all_scores_high(tmp_path):
    all_high = json.dumps({"axes": [
        {"name": "tension_escalation", "score": 0.9, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "act_structure", "score": 0.85, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "chapter_length_consistency", "score": 0.95, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "emotional_beat_variety", "score": 0.80, "chapter_assessments": [], "recommendation": "Good"},
        {"name": "narrative_momentum", "score": 0.90, "chapter_assessments": [], "recommendation": "Good"},
    ]})
    pkb = make_pkb(tmp_path)
    (tmp_path / "chapter_1.md").write_text("Chapter 1 content.")

    agent = PacingAgent(make_llm_client(all_high))
    report = agent.execute(pkb, chapter_numbers=[1])
    assert report is not None

    guidance = PacingAgent.get_editor_guidance(report)
    assert guidance == ""
```

- [ ] **Step 2: Run to confirm fail**

```bash
cd C:\Users\smikl\Desktop\Work\libriscribe
python -m pytest tests/test_pacing_agent.py -v
```
Expected: `ModuleNotFoundError: No module named 'libriscribe.agents.pacing_agent'`

- [ ] **Step 3: Create pacing_agent.py**

```python
# src/libriscribe/agents/pacing_agent.py
"""PacingAgent: cross-chapter arc analysis across 5 pacing axes."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils.file_utils import extract_json_from_markdown, read_markdown_file
from libriscribe.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

_PACING_THRESHOLD = 0.70

_PACING_PROMPT = """\
You are an expert developmental editor analysing pacing across a multi-chapter manuscript.

Book: "{title}" | Genre: {genre} | Language: {language}

Evaluate the chapters below across exactly 5 pacing axes.
For each axis produce ONLY a JSON object with these exact fields:
  "name"                : axis name (exactly as listed)
  "score"               : float 0.0-1.0, 1.0 = ideal pacing
  "chapter_assessments" : list of up to 3 short strings noting chapter-specific issues
  "recommendation"      : one actionable sentence for the editor

Axes:
1. tension_escalation — do stakes/tension rise meaningfully from chapter to chapter? Flat or declining = low score.
2. act_structure — are inciting incident (~ch1-2), midpoint (~50%), dark night (~75%), climax (~90%) structurally clear? Score 1.0 = clean three-act shape.
3. chapter_length_consistency — are chapter word-counts within 30% of each other? Outliers = low score. Score 1.0 = uniform lengths.
4. emotional_beat_variety — do consecutive chapters vary emotional register (tense/tender/comic/tragic)? Three+ identical beats in a row = low score.
5. narrative_momentum — does each chapter end with a hook or open question pulling the reader forward? Score 1.0 = all chapters have forward pull.

Return ONLY a JSON object with a single key "axes" whose value is a list of 5 axis objects in the order above. No other text.

Chapters (ordered):
---
{chapter_texts}
---
"""

_CHAPTER_SEPARATOR = "\n\n### CHAPTER {n} ###\n\n"


class PacingAxis(BaseModel):
    name: str
    score: float
    chapter_assessments: list[str]
    recommendation: str


class PacingReport(BaseModel):
    chapter_numbers: list[int]
    axes: list[PacingAxis]
    overall_score: float
    priority_fix: str


class PacingAgent(Agent):
    """Analyses cross-chapter arc for tension, structure, momentum, and beat variety."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__("PacingAgent", llm_client)

    def execute(
        self,
        project_knowledge_base: ProjectKnowledgeBase,
        chapter_numbers: list[int],
    ) -> Optional[PacingReport]:
        """Analyse pacing across given chapters. Returns None on failure."""
        if not project_knowledge_base.project_dir:
            self.logger.error("project_dir not set on knowledge base.")
            return None

        project_dir = Path(project_knowledge_base.project_dir)
        chapter_texts = self._load_chapters(project_dir, chapter_numbers)
        if not chapter_texts:
            self.logger.warning("No chapter text found for pacing analysis.")
            return None

        combined = "".join(
            _CHAPTER_SEPARATOR.format(n=n) + text
            for n, text in chapter_texts.items()
        )

        prompt = _PACING_PROMPT.format(
            title=project_knowledge_base.title,
            genre=project_knowledge_base.genre,
            language=project_knowledge_base.language,
            chapter_texts=combined,
        )

        try:
            raw = self.llm_client.generate_content_with_json_repair(prompt, max_tokens=4000)
        except Exception:
            self.logger.exception("LLM call failed for pacing analysis.")
            return None

        parsed = extract_json_from_markdown(raw)
        if parsed is None:
            try:
                parsed = json.loads(raw)
            except Exception:
                self.logger.error("Could not parse pacing analysis response.")
                return None

        if not isinstance(parsed, dict) or "axes" not in parsed:
            self.logger.error("Unexpected pacing response shape.")
            return None

        axes: list[PacingAxis] = []
        for item in parsed.get("axes", []):
            if not isinstance(item, dict):
                continue
            try:
                axes.append(PacingAxis(
                    name=str(item.get("name", "")),
                    score=float(item.get("score", 0.0)),
                    chapter_assessments=[str(a) for a in item.get("chapter_assessments", [])],
                    recommendation=str(item.get("recommendation", "")),
                ))
            except Exception:
                self.logger.exception("Skipping malformed pacing axis: %s", item)

        if not axes:
            self.logger.error("No valid axes parsed for pacing analysis.")
            return None

        overall = sum(a.score for a in axes) / len(axes)
        worst = min(axes, key=lambda a: a.score)

        report = PacingReport(
            chapter_numbers=list(chapter_texts.keys()),
            axes=axes,
            overall_score=round(overall, 3),
            priority_fix=worst.recommendation,
        )

        report_path = project_dir / "pacing_report.json"
        report_path.write_text(report.model_dump_json(indent=4), encoding="utf-8")
        self.logger.info("Pacing report saved (overall=%.3f).", overall)
        return report

    @staticmethod
    def get_editor_guidance(report: PacingReport) -> str:
        """Return a PACING GUIDANCE block for injection into the editor prompt."""
        low_axes = [a for a in report.axes if a.score < _PACING_THRESHOLD]
        if not low_axes:
            return ""
        lines = ["PACING GUIDANCE (cross-chapter arc issues to address in this chapter):"]
        for axis in sorted(low_axes, key=lambda a: a.score):
            lines.append(f"- [{axis.name} score={axis.score:.2f}] {axis.recommendation}")
            for note in axis.chapter_assessments[:2]:
                lines.append(f"  Context: {note}")
        return "\n".join(lines)

    def _load_chapters(
        self, project_dir: Path, chapter_numbers: list[int]
    ) -> dict[int, str]:
        """Load chapter files, preferring _revised.md over original."""
        result: dict[int, str] = {}
        for n in chapter_numbers:
            revised = project_dir / f"chapter_{n}_revised.md"
            original = project_dir / f"chapter_{n}.md"
            path = revised if revised.exists() else original
            if path.exists():
                text = read_markdown_file(str(path))
                if text.strip():
                    result[n] = text
        return result
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pacing_agent.py -v
```
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/libriscribe/agents/pacing_agent.py tests/test_pacing_agent.py
git commit -m "feat: add PacingAgent with 5-axis cross-chapter arc analysis"
```

---

## Task 2: Register PacingAgent + wire into pipeline

**Files:**
- Modify: `src/libriscribe/agents/project_manager.py`
- Modify: `src/libriscribe/agents/editor.py`
- Test: append to `tests/test_project_manager.py`

**Interfaces:**
- Consumes: `PacingAgent`, `PacingReport`, `PacingAgent.get_editor_guidance()` from Task 1
- Produces: `ProjectManagerAgent.run_pacing_analysis(chapter_numbers: list[int]) -> Optional[PacingReport]`
- Produces: `ProjectManagerAgent.edit_chapter(chapter_number: int, pacing_guidance: str = "") -> None`
- Produces: `EditorAgent.execute(..., pacing_guidance: str = "") -> None`

- [ ] **Step 1: Write failing test**

Append to `tests/test_project_manager.py`:

```python
# --- PacingAgent integration tests ---
from libriscribe.agents.pacing_agent import PacingReport, PacingAxis


def _make_pacing_report() -> PacingReport:
    return PacingReport(
        chapter_numbers=[1, 2],
        axes=[
            PacingAxis(name="tension_escalation", score=0.5, chapter_assessments=["flat"], recommendation="Raise stakes"),
            PacingAxis(name="act_structure", score=0.8, chapter_assessments=[], recommendation="Good"),
            PacingAxis(name="chapter_length_consistency", score=0.9, chapter_assessments=[], recommendation="Good"),
            PacingAxis(name="emotional_beat_variety", score=0.6, chapter_assessments=[], recommendation="Vary beats"),
            PacingAxis(name="narrative_momentum", score=0.7, chapter_assessments=[], recommendation="OK"),
        ],
        overall_score=0.70,
        priority_fix="Raise stakes",
    )


def test_run_pacing_analysis_calls_agent(tmp_path):
    from libriscribe.agents.project_manager import ProjectManagerAgent
    from unittest.mock import MagicMock

    pm = ProjectManagerAgent()
    pm.project_dir = tmp_path
    pm.project_knowledge_base = MagicMock()
    pm.project_knowledge_base.project_dir = tmp_path

    mock_pacing = MagicMock()
    mock_pacing.execute.return_value = _make_pacing_report()
    pm.agents = {"pacing": mock_pacing}
    pm.llm_client = MagicMock()
    pm.llm_client.model = "gpt-4o"
    pm.llm_client.settings = MagicMock()
    pm.llm_client.settings.fallback_chain = ""

    report = pm.run_pacing_analysis([1, 2])
    assert report is not None
    mock_pacing.execute.assert_called_once_with(
        project_knowledge_base=pm.project_knowledge_base,
        chapter_numbers=[1, 2],
    )
```

- [ ] **Step 2: Run to confirm fail**

```bash
python -m pytest tests/test_project_manager.py::test_run_pacing_analysis_calls_agent -v
```
Expected: `AttributeError: 'ProjectManagerAgent' object has no attribute 'run_pacing_analysis'`

- [ ] **Step 3: Add PacingAgent import to project_manager.py**

```python
from libriscribe.agents.pacing_agent import PacingAgent, PacingReport
```

- [ ] **Step 4: Register in initialize_llm_client**

In the `self.agents` dict inside `initialize_llm_client()`, add:
```python
"pacing": PacingAgent(self.llm_client),
```

- [ ] **Step 5: Add run_pacing_analysis method**

After the `analyze_quality()` method, add:

```python
def run_pacing_analysis(self, chapter_numbers: list[int]) -> Optional[PacingReport]:
    """Runs PacingAgent over given chapters and returns the report."""
    if not self.project_knowledge_base:
        console.print("[red]ERROR: Project not initialized.[/red]")
        return None
    agent = self.agents.get("pacing")
    if agent is None:
        console.print("[red]ERROR: pacing agent not registered.[/red]")
        return None
    if self.llm_client:
        selected_model = self._get_model_for_agent("pacing")
        if selected_model:
            self.llm_client.set_model(selected_model)
        self.llm_client.set_fallback_chain(
            self._get_fallback_chain_for_agent("pacing")
        )
    return cast(Any, agent).execute(
        project_knowledge_base=self.project_knowledge_base,
        chapter_numbers=chapter_numbers,
    )
```

Add `Optional` to the import at the top of `project_manager.py` if not already present:
```python
from typing import Any, Optional, cast
```

- [ ] **Step 6: Update write_and_review_chapter to run pacing and pass guidance**

Replace the current AI-review block:
```python
# BEFORE:
if (
    self.project_knowledge_base
    and self.project_knowledge_base.review_preference == "AI"
):
    self.edit_chapter(chapter_number)
    self.edit_style(chapter_number)
```

With:
```python
if (
    self.project_knowledge_base
    and self.project_knowledge_base.review_preference == "AI"
):
    written = [
        i for i in range(1, chapter_number + 1)
        if self.does_chapter_exist(i)
    ]
    pacing_report = self.run_pacing_analysis(written) if written else None
    pacing_guidance = ""
    if pacing_report:
        pacing_guidance = PacingAgent.get_editor_guidance(pacing_report)
    self.edit_chapter(chapter_number, pacing_guidance=pacing_guidance)
    self.edit_style(chapter_number)
```

- [ ] **Step 7: Update edit_chapter signature**

```python
def edit_chapter(self, chapter_number: int, pacing_guidance: str = "") -> None:
    """Refines an existing chapter (Editor Agent)."""
    self.run_agent("editor", chapter_number=chapter_number, pacing_guidance=pacing_guidance)
    self.save_project_data()
```

- [ ] **Step 8: Update EditorAgent.execute to accept and use pacing_guidance**

In `src/libriscribe/agents/editor.py`, update signature:
```python
def execute(
    self,
    project_knowledge_base: ProjectKnowledgeBase,
    chapter_number: int,
    pacing_guidance: str = "",
) -> None:
```

After building the `prompt` string from `prompts.EDITOR_PROMPT.format(**prompt_data)`, inject pacing guidance:
```python
prompt = prompts.EDITOR_PROMPT.format(**prompt_data) + scene_titles_instruction
if pacing_guidance:
    prompt = pacing_guidance + "\n\n" + prompt
```

- [ ] **Step 9: Run tests**

```bash
python -m pytest tests/test_project_manager.py tests/test_pacing_agent.py -v
```
Expected: all PASS

- [ ] **Step 10: Commit**

```bash
git add src/libriscribe/agents/project_manager.py src/libriscribe/agents/editor.py tests/test_project_manager.py
git commit -m "feat: wire PacingAgent into AI review pipeline with editor pacing guidance injection"
```

---

## Task 3: ResearchContext — wire research_results.md into scene prompts

**Files:**
- Modify: `src/libriscribe/agents/chapter_writer.py`
- Create: `tests/test_chapter_writer_research.py`

**Interfaces:**
- Consumes: `project_dir / "research_results.md"` (written by ResearcherAgent)
- Produces: `RESEARCH CONTEXT (relevant background for this scene):` block as 7th item in `prefix_parts`
- Produces: `ChapterWriterAgent._build_research_block(project_dir: Path | None) -> str`
- Modifies: `_write_scene(... research_block: str = "") -> str`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_chapter_writer_research.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_pkb(project_dir: Path) -> MagicMock:
    pkb = MagicMock()
    pkb.project_dir = project_dir
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
    pkb.get_character.return_value = None
    return pkb


def _make_scene_and_chapter():
    from libriscribe.knowledge_base import Scene, Chapter
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
    return scene, chapter


def _run_chapter_writer(pkb, tmp_path):
    from libriscribe.agents.chapter_writer import ChapterWriterAgent
    from libriscribe.narrative.models import NarrativeGraph

    captured: list[str] = []
    llm = MagicMock()
    llm.generate_content.side_effect = lambda prompt, max_tokens=2000: (
        captured.append(prompt) or "Scene content."
    )
    llm.generate_content_with_json_repair.return_value = '{"axes": []}'

    agent = ChapterWriterAgent(llm)

    _, chapter = _make_scene_and_chapter()
    pkb.get_chapter = MagicMock(return_value=chapter)
    pkb.chapters = {1: chapter}

    empty_graph = NarrativeGraph(project_name="test_proj", facts=[])

    with patch.object(agent, '_load_narrative_graph', return_value=empty_graph), \
         patch.object(agent, '_build_style_hints', return_value=""), \
         patch.object(agent, '_maybe_rewrite_scene', side_effect=lambda scene_content, **kw: scene_content), \
         patch.object(agent, '_update_narrative_graph_after_chapter', return_value=None):
        agent.execute(pkb, chapter_number=1, output_path=str(tmp_path / "chapter_1.md"))

    return captured


def test_research_block_injected_when_file_present(tmp_path):
    research_text = "## AI-Generated Summary\n\nMagic systems require internal consistency and a clear cost."
    (tmp_path / "research_results.md").write_text(research_text)

    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    assert any("RESEARCH CONTEXT" in p for p in captured), (
        f"Expected 'RESEARCH CONTEXT' in scene prompt. First prompt preview: {captured[0][:400] if captured else 'none'}"
    )


def test_research_block_absent_when_file_missing(tmp_path):
    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    assert not any("RESEARCH CONTEXT" in p for p in captured)


def test_research_block_truncated_at_1200_chars(tmp_path):
    long_text = "X" * 2000
    (tmp_path / "research_results.md").write_text(long_text)

    pkb = _make_pkb(tmp_path)
    captured = _run_chapter_writer(pkb, tmp_path)

    research_blocks = [p for p in captured if "RESEARCH CONTEXT" in p]
    assert research_blocks
    block = research_blocks[0]
    # The injected content should be truncated (original 2000 chars not fully present)
    assert "[...truncated]" in block
```

- [ ] **Step 2: Run to confirm fail**

```bash
python -m pytest tests/test_chapter_writer_research.py -v
```
Expected: `test_research_block_injected_when_file_present` FAIL (no RESEARCH CONTEXT)

- [ ] **Step 3: Add _build_research_block to ChapterWriterAgent**

In `src/libriscribe/agents/chapter_writer.py`, after `_build_style_hints`:

```python
def _build_research_block(self, project_dir: Optional[Path]) -> str:
    """Load research_results.md and return a RESEARCH CONTEXT block (truncated)."""
    if project_dir is None:
        return ""
    research_path = project_dir / "research_results.md"
    if not research_path.exists():
        return ""
    try:
        text = read_markdown_file(str(research_path))
        if not text.strip():
            return ""
        snippet = text[:1200].rstrip()
        if len(text) > 1200:
            snippet += "\n[...truncated]"
        return "RESEARCH CONTEXT (relevant background for this scene):\n" + snippet
    except Exception:
        self.logger.warning("Could not read research_results.md.")
        return ""
```

- [ ] **Step 4: Call _build_research_block in execute()**

In `execute()`, after `style_block = self._build_style_hints(chapter_number, project_dir)`:
```python
research_block = self._build_research_block(project_dir)
```

Update `_write_scene` call:
```python
scene_content = self._write_scene(
    scene=scene,
    chapter=chapter,
    chapter_number=chapter_number,
    project_knowledge_base=project_knowledge_base,
    ordered_scenes=ordered_scenes,
    checker=checker,
    style_block=style_block,
    research_block=research_block,
)
```

- [ ] **Step 5: Update _write_scene signature and prefix_parts**

Add `research_block: str = ""` to `_write_scene` parameters.

Update the prefix_parts line:
```python
prefix_parts = [p for p in [
    constraint_block, style_block, style_profile_block,
    dq_block, char_profiles_block, worldbuilding_block, research_block
] if p]
```

- [ ] **Step 6: Run tests**

```bash
python -m pytest tests/test_chapter_writer_research.py -v
```
Expected: all 3 PASS

- [ ] **Step 7: Commit**

```bash
git add src/libriscribe/agents/chapter_writer.py tests/test_chapter_writer_research.py
git commit -m "feat: inject research_results.md as RESEARCH CONTEXT block into scene prompts"
```

---

## Task 4: Fix all 39 Pyright errors

**Files:** See file map above — 9 files.

Run Pyright before starting to get current baseline:
```bash
python -m pyright src/ 2>&1 | grep "error:" | wc -l
```
Expected baseline: 39

- [ ] **Step 1: Fix character_generator.py — 4 errors**

Read `src/libriscribe/agents/character_generator.py` fully first.

**Line 55** — `str` has no `.items()`. Guard `char_data` is a dict:
```python
# Before the dict comprehension on line 55
if not isinstance(char_data, dict):
    self.logger.warning("Skipping non-dict character entry: %s", type(char_data).__name__)
    continue
char_data = {k.lower(): v for k, v in char_data.items()}
```

**Lines 155-156** — `Path | None` and `list` vs `dict`. Add null guard and check `write_json_file` signature (it expects `dict`):
```python
if not project_knowledge_base.project_dir:
    self.logger.error("project_dir not set; cannot save characters.")
    return
char_file_path = Path(project_knowledge_base.project_dir) / "characters.json"
write_json_file(str(char_file_path), {"characters": processed_characters})
```

- [ ] **Step 2: Fix editor.py — 5 errors**

Read `src/libriscribe/agents/editor.py` fully.

**Lines 30, 95** — `Path | None`. Add null guard at top of `execute()`:
```python
if not project_knowledge_base.project_dir:
    self.logger.error("project_dir not set on knowledge base.")
    return
project_dir = Path(project_knowledge_base.project_dir)
chapter_path = str(project_dir / f"chapter_{chapter_number}.md")
```

Update line 95 to use the already-defined `project_dir` variable:
```python
revised_chapter_path = str(project_dir / f"chapter_{chapter_number}_revised.md")
```

**Line 41** — `extract_scene_titles` not found. Add the method to `EditorAgent`:
```python
def extract_scene_titles(self, chapter_content: str) -> list[str]:
    """Extract scene title labels from chapter content."""
    import re
    return re.findall(r'\*\*Scene \d+: (.+?)\*\*', chapter_content)
```

- [ ] **Step 3: Fix formatting_optimized.py — 1 error**

Read `src/libriscribe/agents/formatting_optimized.py`.

**Line 26** — `ProjectKnowledgeBase | None` passed to `_create_formatted_book` which expects `ProjectKnowledgeBase`. Add null guard:
```python
project_knowledge_base = ProjectKnowledgeBase.load_from_file(str(project_data_path))
if project_knowledge_base is None:
    print("ERROR: Could not load project data for formatting.")
    return
formatted_content = self._create_formatted_book(project_dir, project_knowledge_base)
```

- [ ] **Step 4: Fix style_editor.py — 2 errors**

Read `src/libriscribe/agents/style_editor.py`.

**Line 23** — `Path | None`. Add null guard:
```python
if not project_knowledge_base.project_dir:
    self.logger.error("project_dir not set on knowledge base.")
    return
chapter_path = str(Path(project_knowledge_base.project_dir) / f"chapter_{chapter_number}.md")
```

- [ ] **Step 5: Fix worldbuilding.py — 2 errors**

Read `src/libriscribe/agents/worldbuilding.py` around line 135.

**Line 135** — `Path | None`. Add null guard before the Path construction:
```python
if not project_knowledge_base.project_dir:
    self.logger.error("project_dir not set; cannot save worldbuilding.")
    return
worldbuilding_path = Path(project_knowledge_base.project_dir) / "worldbuilding.json"
```

- [ ] **Step 6: Fix main.py — 2 errors**

Read `src/libriscribe/main.py` lines 1448-1505.

**Line 1453** — `Literal['keyword']` not assignable to `RetrievalMode`. Add import and fix:
```python
from libriscribe.retrieval.models import RetrievalMode
# Change: mode="keyword"
# To:
mode=RetrievalMode.KEYWORD
```

**Line 1500** — `SearchResult` has no `.title`. `SearchResult` has `.text`, `.source_type`, `.score`. Replace:
```python
# BEFORE: result.title
# AFTER: result.text[:80]
```

- [ ] **Step 7: Fix retrieval/search_service.py — 1 error**

Read `src/libriscribe/retrieval/search_service.py` lines 65-75.

**Line 73** — `ProjectKnowledgeBase | None` passed where `ProjectKnowledgeBase` required. Add null guard:
```python
kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
if kb is None:
    kb = ProjectKnowledgeBase(project_name=project_dir.name)
self.index_manager = IndexManager(kb, project_dir, config)
```

- [ ] **Step 8: Fix llm_client.py — 14 errors**

Read `src/libriscribe/utils/llm_client.py` fully.

**Line 7** — `genai` import unresolved. Read line 7 to see current import. If it's `from google import genai`, try:
```python
try:
    from google import genai  # type: ignore[reportAttributeAccessIssue]
    import google.generativeai.types as google_genai_types  # type: ignore[reportAttributeAccessIssue]
except ImportError:
    genai = None  # type: ignore[assignment]
    google_genai_types = None  # type: ignore[assignment]
```

**Lines 303-314** — `.chat` on wrong type. Read `_get_client_for_provider()` return type. Narrow with `isinstance`:
```python
from openai import OpenAI as _OpenAI
client = self._get_client_for_provider(provider)
assert isinstance(client, _OpenAI), f"Expected OpenAI client, got {type(client)}"
response = client.chat.completions.create(...)
```

**Lines 317-327** — `.messages` and `.text` on wrong types. Same pattern for Claude:
```python
from anthropic import Anthropic as _Anthropic
client = self._get_client_for_provider(provider)
assert isinstance(client, _Anthropic), f"Expected Anthropic client, got {type(client)}"
response = client.messages.create(...)
block = response.content[0]
text_content = block.text.strip() if hasattr(block, "text") else ""  # type: ignore[union-attr]
```

**Lines 329-342** — `.models` and `.generate_content` on google client. Since google-genai lacks Pyright stubs:
```python
client = self._get_client_for_provider(provider)
response = client.models.generate_content(  # type: ignore[attr-defined]
    model=model,
    contents=prompt,
    ...
)
```

- [ ] **Step 9: Fix prompt_integration.py — 1 error**

Read `src/libriscribe/utils/prompt_integration.py` fully.

**Line 49** — `llm_client` not on `ExternalPromptMixin`. Fix by using `getattr` with a clear error:
```python
# BEFORE: self.llm_client.generate_content(...)
# AFTER:
llm = getattr(self, "llm_client", None)
if llm is None:
    raise AttributeError(
        f"{type(self).__name__} must have an llm_client attribute to use ExternalPromptMixin"
    )
result = llm.generate_content(...)
```

- [ ] **Step 10: Run Pyright and verify 0 errors**

```bash
python -m pyright src/ 2>&1 | tail -3
```
Expected: `0 errors, 0 warnings, 0 informations`

If errors remain, read the specific error line and fix, then re-run.

- [ ] **Step 11: Run full test suite**

```bash
python -m pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 12: Commit**

```bash
git add \
  src/libriscribe/agents/character_generator.py \
  src/libriscribe/agents/editor.py \
  src/libriscribe/agents/formatting_optimized.py \
  src/libriscribe/agents/worldbuilding.py \
  src/libriscribe/agents/style_editor.py \
  src/libriscribe/main.py \
  src/libriscribe/retrieval/search_service.py \
  src/libriscribe/utils/llm_client.py \
  src/libriscribe/utils/prompt_integration.py
git commit -m "fix: resolve all Pyright type errors across codebase"
```

---

## Task 5: Docs — PacingAgent page + update existing pages + README

**Files:**
- Create: `docs/docs/agents/pacing-agent.md`
- Modify: `docs/docs/agents/chapter-writer.md`
- Modify: `docs/docs/agents/researcher.md`
- Modify: `README.md`

- [ ] **Step 1: Create docs/docs/agents/pacing-agent.md**

Read `docs/docs/agents/content-quality-agent.md` first to match style conventions.

```markdown
---
sidebar_position: 18
---

# Pacing Agent

The Pacing Agent analyses cross-chapter arc quality across 5 axes and injects actionable guidance into the Editor Agent prompt for the current chapter.

## Overview

After each chapter is written in AI-review mode, the Pacing Agent receives all chapters written so far and scores the manuscript's pacing. Any axis scoring below **0.70** contributes a line to a `PACING GUIDANCE:` block that is prepended to the editor prompt.

## Quality Axes

| Axis | Description | Score 1.0 means |
|------|-------------|-----------------|
| `tension_escalation` | Stakes/tension rise meaningfully from chapter to chapter | Sustained upward arc |
| `act_structure` | Inciting incident (~ch1-2), midpoint (~50%), dark night (~75%), climax (~90%) are structurally clear | Clean three-act shape |
| `chapter_length_consistency` | Chapter word-counts are within 30% of each other | Uniform lengths |
| `emotional_beat_variety` | Consecutive chapters vary emotional register (tense, tender, comic, tragic) | No 3+ identical beats in a row |
| `narrative_momentum` | Each chapter ends with a hook or open question | All chapters have forward pull |

## Output Files

| File | Description |
|------|-------------|
| `pacing_report.json` | Full report with per-axis scores, chapter assessments, and recommendations |

## Pipeline Placement

```
ChapterWriter → ContentReviewer → NarrativeGraph → NarrativeViolations
  → PacingAgent (analyses all chapters written so far)
  → EditorAgent (receives PACING GUIDANCE block prepended to prompt)
  → StyleEditor
```

## PACING GUIDANCE Block Example

```
PACING GUIDANCE (cross-chapter arc issues to address in this chapter):
- [tension_escalation score=0.50] Raise stakes at the end of this chapter with an unresolved threat.
  Context: Ch1 good, Ch3 tension drops after battle resolves cleanly.
- [emotional_beat_variety score=0.60] Follow this grief beat with a moment of unexpected humour or relief.
  Context: Three consecutive chapters end on grief beats.
```

## Threshold

`_PACING_THRESHOLD = 0.70` in `pacing_agent.py`. Axes at or above this value are not reported.

## Error Handling

- No readable chapter files: returns `None`, pipeline continues without pacing guidance.
- LLM response unparseable: logs error, returns `None`, editor runs without pacing guidance.
- `pacing_report.json` write failure: does not abort chapter writing.
```

- [ ] **Step 2: Append to docs/docs/agents/chapter-writer.md**

Read the file first to find the correct insertion point (after the last section before a final line break).

Append these two sections:

```markdown
### Research Context in Scene Prompts

If `research_results.md` exists in the project directory (produced by the **Researcher Agent**), its first 1 200 characters are injected as a `RESEARCH CONTEXT (relevant background for this scene):` block prepended to every scene prompt. The content is truncated to avoid displacing other context blocks. If the file is absent, the block is silently skipped.

Run the Researcher before starting chapter writing to give every scene factual grounding:

```bash
libriscribe research --query "Victorian-era social norms in London"
```

### Pacing Guidance in Editor Prompt

After all scenes for a chapter are written, the AI-review pipeline runs the **Pacing Agent** across all chapters written so far. Any axes scoring below 0.70 produce a `PACING GUIDANCE:` block prepended to the Editor Agent's prompt, directing it to address cross-chapter arc problems during this editing pass.
```

- [ ] **Step 3: Append to docs/docs/agents/researcher.md**

Read the file first. Append:

```markdown
## Downstream Usage in Chapter Writing

The `research_results.md` file produced by this agent is automatically read by the **Chapter Writer Agent** when generating each scene. The first 1 200 characters are injected as a `RESEARCH CONTEXT` block in the scene prompt, providing the LLM with factual grounding from your research.

Run the Researcher before or during chapter writing for best results:

```bash
libriscribe research --query "your research topic here"
```

The research file persists across sessions — re-run to update it with new findings.
```

- [ ] **Step 4: Update README.md**

Read README.md first to find the Mermaid diagram and agent table.

Add to Mermaid diagram (insert after `ContentQualityAgent` node):
```
PacingAgent["PacingAgent\n(cross-chapter arc)"]
ChapterWriter --> PacingAgent
PacingAgent --> Editor
```

Add row to the agent table:
```markdown
| **PacingAgent** | Analyses tension escalation, act structure, chapter length consistency, emotional beat variety, and narrative momentum across all written chapters; injects `PACING GUIDANCE:` into the editor prompt |
```

- [ ] **Step 5: Commit docs**

```bash
git add \
  docs/docs/agents/pacing-agent.md \
  docs/docs/agents/chapter-writer.md \
  docs/docs/agents/researcher.md \
  README.md
git commit -m "docs: add PacingAgent page, update ChapterWriter and Researcher docs, update README"
```

---

## Task 6: Build Docusaurus and deploy to gh-pages

- [ ] **Step 1: Install docs dependencies**

```bash
cd docs
npm install
```

- [ ] **Step 2: Build Docusaurus**

```bash
npm run build
```
Expected: `docs/build/` created, no errors or warnings.

If build fails, read the error. Common causes: broken markdown frontmatter, missing sidebar_position conflict. Fix and re-run.

- [ ] **Step 3: Verify pacing-agent page in build output**

```bash
ls build/docs/agents/
```
Expected: `pacing-agent/` directory present.

- [ ] **Step 4: Deploy to gh-pages**

```bash
npx gh-pages -d build --message "docs: deploy PacingAgent + research context + Pyright-clean release [skip ci]"
```
Expected: `Published` message. Site updates at https://guerra2fernando.github.io/libriscribe/ within ~1 minute.

- [ ] **Step 5: Return to main branch and verify clean state**

```bash
cd ..
git status
git log --oneline -6
```
Expected: clean working tree, 6 commits visible: pacing_agent, wire pacing, research context, pyright fixes, docs, (plus prior commits).

---

## Self-Review

**Spec coverage:**

| User requirement | Covered by |
|---|---|
| PacingAgent | Tasks 1, 2, 5 |
| PacingAgent on the pipeline | Task 2 |
| Fix ResearcherAgent output wiring | Task 3 |
| Update README | Task 5 |
| Update docs | Task 5 |
| Commit | All tasks |
| Deploy to gh-pages / Docusaurus | Task 6 |
| Fix Pyright issues across codebase | Task 4 |
| Production ready | Tasks 1-4 (tests, null guards, type safety) |

**Placeholder scan:** No TBDs, no "implement later", all code blocks contain complete runnable code.

**Type consistency:**
- `PacingAxis` defined Task 1, used in `get_editor_guidance` Task 1 ✓
- `PacingReport` defined Task 1, returned by `run_pacing_analysis` Task 2 ✓
- `PacingAgent.execute(pkb, chapter_numbers: list[int])` matches mock call in Task 2 test ✓
- `research_block: str = ""` added to `_write_scene` — matches `execute()` call in Task 3 ✓
- `edit_chapter(chapter_number, pacing_guidance="")` matches `run_agent("editor", ..., pacing_guidance=...)` Task 2 ✓
- `EditorAgent.execute(..., pacing_guidance: str = "")` matches Task 2 wire ✓
