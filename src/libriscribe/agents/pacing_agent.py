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
