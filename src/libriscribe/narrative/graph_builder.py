"""Extracts narrative facts from chapter prose and maintains the persistent narrative graph."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.narrative.models import NarrativeFact, NarrativeGraph
from libriscribe.utils.file_utils import extract_json_from_markdown, read_markdown_file
from libriscribe.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """\
You are a narrative continuity analyst. Given the chapter prose below, extract every \
fact that could affect future chapters: character states (alive/dead/injured/recovered), \
knowledge gained or lost, relationship changes, object status changes, location states, \
and significant events with lasting consequences.

Do NOT extract plot events that have no future implication.

For each fact produce a JSON object with these exact fields:
  "entity"        : string — the character, object, or location this fact is about
  "entity_type"   : one of "character", "object", "location", "event"
  "predicate"     : short verb phrase, e.g. "is_dead", "knows", "is_injured", "is_located_at", "relationship_with"
  "value"         : concise description of the state, e.g. "injured left arm", "Kael is a traitor"
  "evidence_quote": an exact short quote (<=60 words) from the prose that establishes this fact
  "negated"       : boolean — true ONLY if this fact CANCELS a prior state \
(e.g. "recovered from injury" negates a prior injury fact)

Return ONLY a JSON array of these objects, with no other text.

Chapter {chapter_number} prose:
---
{prose}
---
"""


class NarrativeGraphBuilder:
    """Builds and updates the narrative fact graph from chapter prose."""

    def __init__(
        self,
        llm_client: LLMClient,
        project_dir: Path,
        project_knowledge_base: ProjectKnowledgeBase,
    ) -> None:
        self.llm_client = llm_client
        self.project_dir = project_dir
        self.project_knowledge_base = project_knowledge_base
        self.logger = logging.getLogger(self.__class__.__name__)
        self._graph_path = project_dir / "narrative_graph.json"

    def _load_graph(self) -> NarrativeGraph:
        if self._graph_path.exists():
            try:
                return NarrativeGraph.load(self._graph_path)
            except Exception:
                self.logger.exception("Could not load narrative graph; starting fresh.")
        return NarrativeGraph.empty(self.project_knowledge_base.project_name)

    def _is_duplicate(self, graph: NarrativeGraph, fact: NarrativeFact) -> bool:
        for existing in graph.facts:
            if (
                existing.entity.lower() == fact.entity.lower()
                and existing.predicate.lower() == fact.predicate.lower()
                and existing.value.lower() == fact.value.lower()
            ):
                return True
        return False

    def extract_from_chapter(self, chapter_number: int) -> list[NarrativeFact]:
        """Extract facts from chapter prose and persist them to the graph."""
        chapter_path = self.project_dir / f"chapter_{chapter_number}.md"
        prose = read_markdown_file(str(chapter_path))
        if not prose.strip():
            self.logger.warning(
                "Chapter %d file empty or missing; skipping extraction.", chapter_number
            )
            return []

        prompt = _EXTRACT_PROMPT.format(chapter_number=chapter_number, prose=prose)
        raw = self.llm_client.generate_content_with_json_repair(prompt, max_tokens=2000)

        parsed = extract_json_from_markdown(raw)
        if parsed is None:
            try:
                parsed = json.loads(raw)
            except Exception:
                self.logger.error(
                    "Could not parse fact extraction response for chapter %d.", chapter_number
                )
                return []

        if not isinstance(parsed, list):
            self.logger.error(
                "Expected JSON array from fact extraction, got %s.", type(parsed).__name__
            )
            return []

        graph = self._load_graph()
        new_facts: list[NarrativeFact] = []

        for item in parsed:
            if not isinstance(item, dict):
                continue
            try:
                fact = NarrativeFact(
                    fact_id=NarrativeFact.make_id(
                        item.get("entity", ""),
                        item.get("predicate", ""),
                        item.get("value", ""),
                    ),
                    entity=item.get("entity", ""),
                    entity_type=item.get("entity_type", "character"),
                    predicate=item.get("predicate", ""),
                    value=item.get("value", ""),
                    chapter=chapter_number,
                    evidence_quote=item.get("evidence_quote", ""),
                    negated=bool(item.get("negated", False)),
                )
            except Exception:
                self.logger.exception("Skipping malformed fact item: %s", item)
                continue

            if self._is_duplicate(graph, fact):
                continue

            graph.add_fact(fact)
            new_facts.append(fact)

        graph.last_chapter_processed = max(graph.last_chapter_processed, chapter_number)
        graph.save(self._graph_path)
        self.logger.info(
            "Narrative graph updated: %d new facts from chapter %d.", len(new_facts), chapter_number
        )
        return new_facts
