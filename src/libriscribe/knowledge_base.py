# src/libriscribe/knowledge_base.py
"""
Core knowledge base implementation for LibriScribe.

This module provides the ProjectKnowledgeBase class which manages project metadata
and character information for book writing projects.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Character(BaseModel):
    """A character in the book project."""
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    background: str = Field(..., min_length=1)
    goals: str = Field(..., min_length=1)
    personality: str = Field(..., min_length=1)

class ProjectKnowledgeBase(BaseModel):
    """Manages metadata and character information for a book project."""
    project_name: str = Field(..., min_length=1)
    book_title: str = Field(..., min_length=1)
    category: str = Field(..., regex="^(fiction|non-fiction)$")
    genre: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    language: str = Field(..., regex="^[a-z]{2}$")
    book_length: str = Field(..., regex="^(short|medium|long)$")
    num_characters: str = Field(..., min_length=1)
    num_chapters: int = Field(..., gt=0)
    characters: List[Character] = []

    def add_character(self, character: Character) -> None:
        """Add a character to the knowledge base."""
        self.characters.append(character)

    def get_character(self, character_name: str) -> Optional[Character]:
        """Retrieve a character by name."""
        for character in self.characters:
            if character.name == character_name:
                return character
        return None
