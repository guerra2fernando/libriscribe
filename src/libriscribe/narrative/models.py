"""Pydantic models for the narrative graph: facts and the graph container."""
from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel, Field


class NarrativeFact(BaseModel):
    fact_id: str
    entity: str
    entity_type: str
    predicate: str
    value: str
    chapter: int
    evidence_quote: str
    negated: bool = False

    @classmethod
    def make_id(cls, entity: str, predicate: str, value: str) -> str:
        raw = f"{entity}|{predicate}|{value}"
        return hashlib.sha1(raw.encode()).hexdigest()[:8]


class NarrativeGraph(BaseModel):
    project_name: str
    facts: list[NarrativeFact] = Field(default_factory=list)
    last_chapter_processed: int = 0

    def add_fact(self, fact: NarrativeFact) -> None:
        self.facts.append(fact)

    def get_facts_for_entity(self, entity: str) -> list[NarrativeFact]:
        return [f for f in self.facts if f.entity.lower() == entity.lower()]

    def get_active_facts(self) -> list[NarrativeFact]:
        """Return facts not cancelled by a later negated=True fact for same entity+predicate."""
        cancelled: set[tuple[str, str]] = set()
        for fact in reversed(self.facts):
            if fact.negated:
                cancelled.add((fact.entity.lower(), fact.predicate.lower()))
        return [
            f for f in self.facts
            if not f.negated and (f.entity.lower(), f.predicate.lower()) not in cancelled
        ]

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=4), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> NarrativeGraph:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def empty(cls, project_name: str) -> NarrativeGraph:
        return cls(project_name=project_name)
