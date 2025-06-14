import pytest
from unittest.mock import Mock
from pydantic import BaseModel

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
    characters: list[MockCharacter] = []

    def add_character(self, character: MockCharacter) -> None:
        self.characters.append(character)

    def get_character(self, character_name: str) -> MockCharacter | None:
        for character in self.characters:
            if character.name == character_name:
                return character
        return None

@pytest.fixture
def mock_llm_client():
    mock_client = Mock()
    mock_client.generate_content.return_value = "Mock response"
    return mock_client

@pytest.fixture
def sample_project_knowledge_base():
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
