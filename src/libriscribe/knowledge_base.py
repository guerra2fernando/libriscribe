# src/libriscribe/knowledge_base.py

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator


class Character(BaseModel):
    name: str
    age: str = ""
    physical_description: str = ""
    personality_traits: str = ""
    background: str = ""
    motivations: str = ""
    relationships: Dict[str, str] = {}  # Character name -> Relationship description
    role: str = ""
    internal_conflicts: str = ""
    external_conflicts: str = ""
    character_arc: str = ""


class Scene(BaseModel):
    scene_number: int
    summary: str = ""
    characters: List[str] = []  # List of character names
    setting: str = ""
    goal: str = ""  # What's the purpose of this scene?
    emotional_beat: str = ""  # What's the primary emotion conveyed?


class Chapter(BaseModel):
    chapter_number: int
    title: str = ""
    summary: str = ""
    scenes: List[Scene] = []
    # We don't store the full chapter text *here*, just metadata and scenes.


class Worldbuilding(BaseModel):
    # Keep this empty for now, and we will use it on the agents
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
    # Non fiction
    setting_context: str = ""
    key_figures: str = ""
    major_events: str = ""
    underlying_causes: str = ""
    consequences: str = ""
    relevant_data: str = ""
    different_perspectives: str = ""
    key_concepts: str = ""
    # business
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
    # research
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
    num_characters: Union[int, Tuple[int, int]] = 0  # Keep, used by character generator
    num_characters_str: str = ""  # Keep for advanced
    worldbuilding_needed: bool = False  # Keep, used by worldbuilding generator
    review_preference: str = "AI"
    book_length: str = ""
    logline: str = "No logline available"
    tone: str = "Informative"
    target_audience: str = "General"
    num_chapters: Union[int, Tuple[int, int]] = (
        1  # Keep for chapter generation, advanced mode
    )
    num_chapters_str: str = ""  # Keep for advanced
    llm_provider: str = "openai"
    model: str = ""
    agent_models: Dict[str, str] = {}
    chapter_writing_mode: str = "prompt"
    chapter_error_mode: str = "stop"
    dynamic_questions: Dict[str, str] = {}  # Keep for advanced

    characters: Dict[str, Character] = {}  # Character name -> Character object
    worldbuilding: Worldbuilding = Field(default_factory=Worldbuilding)
    chapters: Dict[int, Chapter] = {}  # Chapter number -> Chapter object
    outline: str = ""  # Store outline as markdown
    project_dir: Optional[Path] = None

    @validator("num_characters", "num_chapters", pre=True)
    def parse_range_or_plus(cls, value):
        if isinstance(value, str):
            if "-" in value:
                try:
                    min_val, max_val = map(int, value.split("-"))
                    return (min_val, max_val)
                except ValueError:
                    return 0  # Default value
            elif "+" in value:
                try:
                    return int(value.replace("+", ""))
                except ValueError:
                    return 0  # Default
            else:
                try:
                    return int(value)
                except ValueError:
                    return 0
        return value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)

    def add_character(self, character: Character):
        self.characters[character.name] = character

    def get_character(self, character_name: str) -> Optional[Character]:
        return self.characters.get(character_name)

    def add_chapter(self, chapter: Chapter):
        self.chapters[chapter.chapter_number] = chapter

    def get_chapter(self, chapter_number: int) -> Optional[Chapter]:
        return self.chapters.get(chapter_number)

    def add_scene_to_chapter(self, chapter_number: int, scene: Scene):
        if chapter_number not in self.chapters:
            self.chapters[chapter_number] = Chapter(chapter_number=chapter_number)
        self.chapters[chapter_number].scenes.append(scene)

    def to_json(self) -> str:
        """Serializes the knowledge base to a JSON string."""
        return self.model_dump_json(indent=4)  # Use model_dump_json

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectKnowledgeBase":
        """Deserializes the knowledge base from a JSON string."""
        return cls.model_validate_json(json_str)  # Use model_validate_json

    def save_to_file(self, file_path: str):
        """Saves the knowledge base to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["ProjectKnowledgeBase"]:
        """Loads the knowledge base from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return cls.from_json(f.read())
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {file_path}")
            return None
        except Exception as e:
            print(f"ERROR loading knowledge base from {file_path}: {e}")
            return None

    worldbuilding_needed: bool = False
    # Make worldbuilding conditional on worldbuilding_needed
    worldbuilding: Optional[Worldbuilding] = None

    # Add a validator to ensure worldbuilding is None when not needed
    @validator("worldbuilding", pre=True, always=True)
    def set_worldbuilding(cls, v, values):
        if not values.get("worldbuilding_needed", False):
            return None
        if v is None and values.get("worldbuilding_needed", False):
            return Worldbuilding()
        return v
