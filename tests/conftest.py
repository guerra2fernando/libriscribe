from typing import List, Optional

import pytest
from pydantic import BaseModel
from unittest.mock import Mock


class MockCharacter(BaseModel):
    name: str
    role: str
    description: str
    background: str
    goals: str
    personality: str

class MockProjectKnowledgeBase(BaseModel):
    project_name: str
    book_title: str
    category: str
    genre: str
    description: str
    language: str
    book_length: str
    num_characters: str
    num_chapters: int
    characters: List[MockCharacter] = []

    def add_character(self, character: MockCharacter) -> None:
        self.characters.append(character)

    def get_character(self, character_name: str) -> Optional[MockCharacter]:
        for character in self.characters:
            if character.name == character_name:
                return character
        return None

@pytest.fixture
def mock_llm_client() -> Mock:
    mock_client = Mock()
    mock_client.generate_content.return_value = "Mock response"
    return mock_client

@pytest.fixture
def sample_project_knowledge_base() -> MockProjectKnowledgeBase:
    return MockProjectKnowledgeBase(
        project_name="Test Project",
        book_title="Test Book",
        category="fiction",
        genre="fantasy",
        description="A test book description",
        language="en",
        book_length="medium",
        num_characters="2-3",
        num_chapters=3
    )
