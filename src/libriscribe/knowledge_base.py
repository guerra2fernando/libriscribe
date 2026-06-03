from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Character(BaseModel):
    name: str
    age: str = ""
    physical_description: str = ""
    personality_traits: str = ""
    background: str = ""
    motivations: str = ""
    relationships: dict[str, str] = Field(default_factory=dict)
    role: str = ""
    internal_conflicts: str = ""
    external_conflicts: str = ""
    character_arc: str = ""


class Scene(BaseModel):
    scene_number: int
    summary: str = ""
    characters: list[str] = Field(default_factory=list)
    setting: str = ""
    goal: str = ""
    emotional_beat: str = ""


class Chapter(BaseModel):
    chapter_number: int
    title: str = ""
    summary: str = ""
    scenes: list[Scene] = Field(default_factory=list)


class Worldbuilding(BaseModel):
    geography: str = ""
    culture_and_society: str = ""
    history: str = ""
    rules_and_laws: str = ""
    technology_level: str = ""
    magic_system: str = ""
    key_locations: str = ""
    important_organizations: str = ""
    flora_and_fauna: str = ""
    languages: str = ""
    religions_and_beliefs: str = ""
    economy: str = ""
    conflicts: str = ""
    setting_context: str = ""
    key_figures: str = ""
    major_events: str = ""
    underlying_causes: str = ""
    consequences: str = ""
    relevant_data: str = ""
    different_perspectives: str = ""
    key_concepts: str = ""
    industry_overview: str = ""
    target_audience: str = ""
    market_analysis: str = ""
    business_model: str = ""
    marketing_and_sales_strategy: str = ""
    operations: str = ""
    financial_projections: str = ""
    management_team: str = ""
    legal_and_regulatory_environment: str = ""
    risks_and_challenges: str = ""
    opportunities_for_growth: str = ""
    introduction: str = ""
    literature_review: str = ""
    methodology: str = ""
    results: str = ""
    discussion: str = ""
    conclusion: str = ""
    references: str = ""
    appendices: str = ""


class ProjectKnowledgeBase(BaseModel):
    project_name: str
    title: str = "Untitled"
    genre: str = "Unknown Genre"
    description: str = "No description provided."
    category: str = "Unknown Category"
    language: str = "English"
    num_characters: int | tuple[int, int] = 0
    num_characters_str: str = ""
    worldbuilding_needed: bool = False
    review_preference: str = "AI"
    book_length: str = ""
    logline: str = "No logline available"
    tone: str = "Informative"
    target_audience: str = "General"
    num_chapters: int | tuple[int, int] = 1
    num_chapters_str: str = ""
    llm_provider: str = "openai"
    model: str = ""
    agent_models: dict[str, str] = Field(default_factory=dict)
    fallback_chain: list[str] = Field(default_factory=list)
    agent_fallback_chains: dict[str, list[str]] = Field(default_factory=dict)
    chapter_writing_mode: str = "prompt"
    chapter_error_mode: str = "stop"
    dynamic_questions: dict[str, str] = Field(default_factory=dict)

    characters: dict[str, Character] = Field(default_factory=dict)
    worldbuilding: Worldbuilding | None = None
    chapters: dict[int, Chapter] = Field(default_factory=dict)
    outline: str = ""
    project_dir: Path | None = None

    @field_validator("num_characters", "num_chapters", mode="before")
    @classmethod
    def parse_range_or_plus(cls, value: Any) -> int | tuple[int, int]:
        if isinstance(value, str):
            if "-" in value:
                try:
                    min_val, max_val = map(int, value.split("-"))
                    return (min_val, max_val)
                except ValueError:
                    return 0
            if "+" in value:
                try:
                    return int(value.replace("+", ""))
                except ValueError:
                    return 0
            try:
                return int(value)
            except ValueError:
                return 0
        if isinstance(value, tuple):
            return value
        if isinstance(value, int):
            return value
        return 0

    @field_validator("fallback_chain", mode="before")
    @classmethod
    def normalize_fallback_chain(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @field_validator("agent_fallback_chains", mode="before")
    @classmethod
    def normalize_agent_fallback_chains(cls, value: Any) -> dict[str, list[str]]:
        if value is None or not isinstance(value, dict):
            return {}

        normalized: dict[str, list[str]] = {}
        for agent_name, chain in value.items():
            if isinstance(chain, str):
                items = [item.strip() for item in chain.split(",") if item.strip()]
            elif isinstance(chain, list):
                items = [str(item).strip() for item in chain if str(item).strip()]
            else:
                items = []
            normalized[str(agent_name).strip()] = items
        return normalized

    @model_validator(mode="after")
    def ensure_worldbuilding_state(self) -> ProjectKnowledgeBase:
        if not self.worldbuilding_needed:
            self.worldbuilding = None
        elif self.worldbuilding is None:
            self.worldbuilding = Worldbuilding()
        return self

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)

    def add_character(self, character: Character) -> None:
        self.characters[character.name] = character

    def get_character(self, character_name: str) -> Character | None:
        return self.characters.get(character_name)

    def add_chapter(self, chapter: Chapter) -> None:
        self.chapters[chapter.chapter_number] = chapter

    def get_chapter(self, chapter_number: int) -> Chapter | None:
        return self.chapters.get(chapter_number)

    def add_scene_to_chapter(self, chapter_number: int, scene: Scene) -> None:
        if chapter_number not in self.chapters:
            self.chapters[chapter_number] = Chapter(chapter_number=chapter_number)
        self.chapters[chapter_number].scenes.append(scene)

    def to_json(self) -> str:
        return self.model_dump_json(indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> ProjectKnowledgeBase:
        return cls.model_validate_json(json_str)

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(self.to_json())

    @classmethod
    def load_from_file(cls, file_path: str) -> ProjectKnowledgeBase | None:
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                return cls.from_json(file_handle.read())
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {file_path}")
            return None
        except Exception as exc:
            print(f"ERROR loading knowledge base from {file_path}: {exc}")
            return None
