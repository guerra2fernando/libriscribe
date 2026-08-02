"""ContentQualityAgent: measures prose quality across 5 axes for a single chapter."""
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

_QUALITY_PROMPT = """\
You are an expert literary editor. Analyse the chapter prose below across exactly 5 quality axes.
For each axis produce ONLY a JSON object with these exact fields:
  "name"              : the axis name (exactly as listed below)
  "score"             : float 0.0-1.0, where 1.0 = best possible
  "flagged_excerpts"  : list of up to 3 exact short quotes (<=40 words each) from the text that illustrate problems
  "recommendation"    : one actionable sentence

Axes to evaluate:
1. cliche_density - AI-obvious or overused phrases ("the air was thick with tension", "he let out a breath he didn't know he was holding", "her heart raced"). Score 1.0 = no cliches found.
2. show_dont_tell_ratio - direct statement of emotion vs. demonstrated through action/dialogue. "She was angry" = bad. "She slammed the door without looking back" = good. Score 1.0 = all shown.
3. dialogue_voice_consistency - does each character's dialogue match their established voice?{voice_section} Score 1.0 = all voices consistent.
4. sentence_variety - does the chapter vary sentence length and structure? Monotony = sequences of similarly structured sentences. Score 1.0 = high variety.
5. scene_function_clarity - does each scene clearly advance plot, character, or theme? Score 1.0 = all scenes earn their place.

Return ONLY a JSON object with a single key "axes" whose value is a list of 5 axis objects in the order above. No other text.

Chapter {chapter_number} prose:
---
{prose}
---
"""

_VOICE_BLOCK = """
Character voice profiles:
{profiles}
"""


class QualityAxis(BaseModel):
    name: str
    score: float
    flagged_excerpts: list[str]
    recommendation: str


class QualityReport(BaseModel):
    chapter_number: int
    axes: list[QualityAxis]
    overall_score: float
    priority_fix: str


class ContentQualityAgent(Agent):
    """Measures prose quality across 5 axes for a single chapter."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__("ContentQualityAgent", llm_client)

    def execute(
        self,
        project_knowledge_base: ProjectKnowledgeBase,
        chapter_number: int,
        output_path: Optional[str] = None,
    ) -> Optional[QualityReport]:
        """Run quality analysis on a chapter. Returns None on failure."""
        if not project_knowledge_base.project_dir:
            self.logger.error("project_dir not set on knowledge base.")
            return None

        chapter_path = Path(project_knowledge_base.project_dir) / f"chapter_{chapter_number}.md"
        prose = read_markdown_file(str(chapter_path))
        if not prose.strip():
            self.logger.warning("Chapter %d file empty or missing.", chapter_number)
            return None

        voice_section = self._build_voice_section(project_knowledge_base, prose)
        prompt = _QUALITY_PROMPT.format(
            chapter_number=chapter_number,
            prose=prose,
            voice_section=voice_section,
        )

        try:
            raw = self.llm_client.generate_content_with_json_repair(prompt, max_tokens=2000)
        except Exception:
            self.logger.exception("LLM call failed for chapter %d quality analysis.", chapter_number)
            return None

        parsed = extract_json_from_markdown(raw)
        if parsed is None:
            try:
                parsed = json.loads(raw)
            except Exception:
                self.logger.error("Could not parse quality analysis response for chapter %d.", chapter_number)
                return None

        if not isinstance(parsed, dict) or "axes" not in parsed:
            self.logger.error("Unexpected quality analysis response shape for chapter %d.", chapter_number)
            return None

        axes: list[QualityAxis] = []
        for item in parsed["axes"]:
            if not isinstance(item, dict):
                continue
            try:
                axes.append(
                    QualityAxis(
                        name=str(item.get("name", "")),
                        score=float(item.get("score", 0.0)),
                        flagged_excerpts=[str(e) for e in item.get("flagged_excerpts", [])],
                        recommendation=str(item.get("recommendation", "")),
                    )
                )
            except Exception:
                self.logger.exception("Skipping malformed axis item: %s", item)

        if not axes:
            self.logger.error("No valid axes parsed for chapter %d.", chapter_number)
            return None

        scoreable = [a for a in axes if a.name != "dialogue_voice_consistency" or a.score > 0]
        overall = sum(a.score for a in scoreable) / len(scoreable) if scoreable else 0.0

        worst = min(axes, key=lambda a: a.score)
        priority_fix = worst.recommendation

        report = QualityReport(
            chapter_number=chapter_number,
            axes=axes,
            overall_score=round(overall, 3),
            priority_fix=priority_fix,
        )

        project_dir = Path(project_knowledge_base.project_dir)
        default_path = project_dir / f"quality_chapter_{chapter_number}.json"
        default_path.write_text(report.model_dump_json(indent=4), encoding="utf-8")

        if output_path:
            Path(output_path).write_text(report.model_dump_json(indent=4), encoding="utf-8")

        self.logger.info(
            "Quality report saved for chapter %d (overall=%.3f).", chapter_number, overall
        )
        return report

    def score_prose(self, prose: str, scene_label: str = "scene") -> Optional[QualityReport]:
        """Score raw prose text (no file I/O). Used for inline rewrite loop."""
        prompt = _QUALITY_PROMPT.format(
            chapter_number=scene_label,
            prose=prose,
            voice_section=" No character voice data available; skip this axis if insufficient data.",
        )
        try:
            raw = self.llm_client.generate_content_with_json_repair(prompt, max_tokens=1500)
        except Exception:
            self.logger.exception("LLM call failed scoring prose for %s.", scene_label)
            return None

        parsed = extract_json_from_markdown(raw)
        if parsed is None:
            try:
                parsed = json.loads(raw)
            except Exception:
                self.logger.error("Could not parse score_prose response for %s.", scene_label)
                return None

        if not isinstance(parsed, dict) or "axes" not in parsed:
            return None

        axes: list[QualityAxis] = []
        for item in parsed.get("axes", []):
            if not isinstance(item, dict):
                continue
            try:
                axes.append(
                    QualityAxis(
                        name=str(item.get("name", "")),
                        score=float(item.get("score", 0.0)),
                        flagged_excerpts=[str(e) for e in item.get("flagged_excerpts", [])],
                        recommendation=str(item.get("recommendation", "")),
                    )
                )
            except Exception:
                self.logger.exception("Skipping malformed axis: %s", item)

        if not axes:
            return None

        overall = sum(a.score for a in axes) / len(axes)
        worst = min(axes, key=lambda a: a.score)
        return QualityReport(
            chapter_number=0,
            axes=axes,
            overall_score=round(overall, 3),
            priority_fix=worst.recommendation,
        )

    def _build_voice_section(
        self, project_knowledge_base: ProjectKnowledgeBase, prose: str
    ) -> str:
        profiles: list[str] = []
        for name, char in project_knowledge_base.characters.items():
            if not char.personality_traits:
                continue
            if name.lower() not in prose.lower():
                continue
            parts = [f"- {name}: personality={char.personality_traits}"]
            if char.background:
                parts.append(f"  background={char.background}")
            profiles.append("\n".join(parts))

        if not profiles:
            return " No character voice data available; skip this axis if insufficient data."
        return _VOICE_BLOCK.format(profiles="\n".join(profiles))
