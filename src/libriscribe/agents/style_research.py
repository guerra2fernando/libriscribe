"""StyleResearchAgent: extracts concrete style attributes from an inspired_by reference."""

import json
import logging
import re
from typing import Optional

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import ProjectKnowledgeBase, StyleProfile
from libriscribe.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

_RESEARCH_PROMPT = """\
You are a literary critic and style analyst.

The author of a book project says they want their writing to be inspired by:
  "{inspired_by}"

Extract concrete, actionable style attributes from this reference. If the reference is an author name, base your analysis on their most well-known published work. If it is a specific book title, base your analysis on that book.

Return a JSON object with EXACTLY these keys — no extras, no omissions:

{{
  "point_of_view": "...",
  "sentence_length": "...",
  "pacing": "...",
  "dialogue_style": "...",
  "prose_tone": "...",
  "structural_patterns": "...",
  "thematic_preoccupations": "...",
  "what_to_avoid": "..."
}}

Rules:
- Each value must be a concrete, specific description (1-2 sentences maximum).
- Do NOT write vague answers like "varies" or "depends on the scene".
- Do NOT include JSON keys other than the eight listed above.
- Do NOT include markdown fences or any text outside the JSON object.
"""


class StyleResearchAgent(Agent):
    """Runs once pre-pipeline to extract style attributes from inspired_by."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__("StyleResearchAgent", llm_client)

    def execute(self, project_knowledge_base: ProjectKnowledgeBase) -> None:
        """Populate pkb.style_profile if inspired_by is set and profile not yet built."""
        inspired_by: str = project_knowledge_base.inspired_by or ""
        if not inspired_by.strip():
            return

        if project_knowledge_base.style_profile is not None:
            self.logger.info("Style profile already present; skipping research.")
            return

        self.logger.info("Running style research for: %s", inspired_by)
        prompt = _RESEARCH_PROMPT.format(inspired_by=inspired_by)

        try:
            raw = self.llm_client.generate_content(prompt, max_tokens=600)
        except Exception:
            self.logger.exception("Style research LLM call failed; continuing without style profile.")
            return

        profile = self._parse_profile(raw, inspired_by)
        if profile:
            project_knowledge_base.style_profile = profile
            self.logger.info("Style profile populated for: %s", inspired_by)

    def _parse_profile(self, raw: Optional[str], source: str) -> Optional[StyleProfile]:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                self.logger.warning("Could not parse style research JSON; skipping.")
                return None
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                self.logger.warning("Could not parse style research JSON after extraction; skipping.")
                return None

        valid_keys = set(StyleProfile.model_fields) - {"source"}
        return StyleProfile(source=source, **{k: str(v) for k, v in data.items() if k in valid_keys})
