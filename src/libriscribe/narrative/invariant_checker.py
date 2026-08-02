"""Checks scene plans against active narrative facts to surface continuity violations."""
from __future__ import annotations

import logging

from pydantic import BaseModel

from libriscribe.knowledge_base import ProjectKnowledgeBase, Scene
from libriscribe.narrative.models import NarrativeGraph

logger = logging.getLogger(__name__)

_DEAD_PREDICATES = {"is_dead", "died", "was_killed", "killed"}
_DESTROYED_PREDICATES = {"is_destroyed", "destroyed", "burned_down", "collapsed"}


class Violation(BaseModel):
    severity: str
    entity: str
    description: str
    established_chapter: int
    evidence_quote: str


class InvariantChecker:
    """Checks a scene's characters and setting against active narrative facts."""

    def __init__(self, graph: NarrativeGraph) -> None:
        self.graph = graph
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_scene(
        self,
        scene: Scene,
        chapter_number: int,
        project_knowledge_base: ProjectKnowledgeBase,
    ) -> list[Violation]:
        """Return violations for the scene given current active facts."""
        # Only consider facts established before this chapter
        active = [f for f in self.graph.get_active_facts() if f.chapter < chapter_number]
        known_characters = set(project_knowledge_base.characters.keys())
        violations: list[Violation] = []

        # Resolve canonical name when KB has it (handles partial name matches)
        def _canonical(name: str) -> str:
            for kb_name in known_characters:
                if name.lower() in kb_name.lower() or kb_name.lower() in name.lower():
                    return kb_name
            return name

        for character in scene.characters:
            char_lower = _canonical(character).lower()
            for fact in active:
                if fact.entity.lower() != char_lower:
                    continue
                pred = fact.predicate.lower()
                if pred in _DEAD_PREDICATES:
                    violations.append(
                        Violation(
                            severity="hard",
                            entity=character,
                            description=(
                                f"{character} is dead (established ch{fact.chapter}): "
                                f"cannot appear in scene {scene.scene_number}"
                            ),
                            established_chapter=fact.chapter,
                            evidence_quote=fact.evidence_quote,
                        )
                    )
                elif pred == "is_injured":
                    goal_lower = (scene.goal or "").lower()
                    if any(kw in goal_lower for kw in ("fight", "battle", "combat", "run", "escape")):
                        violations.append(
                            Violation(
                                severity="soft",
                                entity=character,
                                description=(
                                    f"{character} has injury '{fact.value}' (ch{fact.chapter}) "
                                    f"but scene goal implies physical activity"
                                ),
                                established_chapter=fact.chapter,
                                evidence_quote=fact.evidence_quote,
                            )
                        )

        if scene.setting:
            setting_lower = scene.setting.lower()
            for fact in active:
                if fact.entity.lower() not in setting_lower:
                    continue
                pred = fact.predicate.lower()
                if pred in _DESTROYED_PREDICATES:
                    violations.append(
                        Violation(
                            severity="hard",
                            entity=fact.entity,
                            description=(
                                f"Location '{fact.entity}' is destroyed (ch{fact.chapter}): "
                                f"cannot be used as setting"
                            ),
                            established_chapter=fact.chapter,
                            evidence_quote=fact.evidence_quote,
                        )
                    )

        return violations

    def format_violations_for_prompt(self, violations: list[Violation]) -> str:
        """Format violations as a compact constraint block for scene prompts."""
        if not violations:
            return ""
        lines = ["NARRATIVE CONSTRAINTS:"]
        for v in violations:
            tag = "[HARD]" if v.severity == "hard" else "[SOFT]"
            lines.append(
                f"- {tag} {v.description} (ch{v.established_chapter}: '{v.evidence_quote}')"
            )
        return "\n".join(lines)
