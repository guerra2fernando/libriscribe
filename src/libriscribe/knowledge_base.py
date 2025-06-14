# src/libriscribe/knowledge_base.py
"""
Core knowledge base implementation for LibriScribe.

This module provides the ProjectKnowledgeBase class which manages project metadata
and character information for book writing projects.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Scene(BaseModel):
    """A scene within a chapter."""
    scene_number: int
    summary: str
    characters: List[str]
    setting: str
    goal: str
    emotional_beat: str

class Chapter(BaseModel):
    """A chapter in the book."""
    chapter_number: int
    title: str
    summary: str
    scenes: List[Scene] = []

class Character(BaseModel):
    """A character in the book project."""
    name: str = Field(..., min_length=1)
    age: str
    physical_description: str
    personality_traits: str
    background: str
    motivations: str
    relationships: dict
    role: str
    internal_conflicts: str
    external_conflicts: str
    character_arc: str

class ProjectKnowledgeBase(BaseModel):
    """Manages metadata and story information for a book project."""
    project_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    category: str = Field(..., regex="^(fiction|non-fiction)$")
    genre: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    language: str = Field(..., regex="^[a-z]{2}$")
    book_length: str = Field(..., regex="^(Short Story|Novella|Novel)$")
    num_characters: str = Field(..., min_length=1)
    num_chapters: int = Field(..., gt=0)
    logline: str = ""
    outline: str = ""
    characters: List[Character] = []
    chapters: dict[int, Chapter] = {}
    project_dir: Optional[str] = None

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the knowledge base."""
        self.chapters[chapter.chapter_number] = chapter

    def add_character(self, character: Character) -> None:
        """Add a character to the knowledge base."""
        self.characters.append(character)

    def get_character(self, character_name: str) -> Optional[Character]:
        """Retrieve a character by name."""
        for character in self.characters:
            if character.name == character_name:
                return character
        return None
