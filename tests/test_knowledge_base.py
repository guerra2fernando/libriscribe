import pytest

from tests.conftest import MockCharacter, MockProjectKnowledgeBase


def test_project_knowledge_base_creation() -> None:
    kb = MockProjectKnowledgeBase(
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
    assert kb.project_name == "Test Project"
    assert kb.book_title == "Test Book"

def test_add_character() -> None:
    kb = MockProjectKnowledgeBase(
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
    
    character = MockCharacter(
        name="Test Character",
        role="protagonist",
        description="A test character",
        background="Test background",
        goals="Test goals",
        personality="Test personality"
    )
    
    kb.add_character(character)
    retrieved_character = kb.get_character("Test Character")
    assert retrieved_character is not None
    assert retrieved_character.name == "Test Character"

def test_get_nonexistent_character() -> None:
    kb = MockProjectKnowledgeBase(
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
    
    retrieved_character = kb.get_character("Nonexistent Character")
    assert retrieved_character is None

def test_multiple_characters() -> None:
    kb = MockProjectKnowledgeBase(
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
    
    characters = [
        MockCharacter(
            name=f"Character {i}",
            role=f"role {i}",
            description=f"description {i}",
            background=f"background {i}",
            goals=f"goals {i}",
            personality=f"personality {i}"
        )
        for i in range(3)
    ]
    
    for character in characters:
        kb.add_character(character)
    
    assert len(kb.characters) == 3
    for i in range(3):
        retrieved = kb.get_character(f"Character {i}")
        assert retrieved is not None
        assert retrieved.role == f"role {i}"

def test_project_knowledge_base_validation() -> None:
    with pytest.raises(ValueError):
        MockProjectKnowledgeBase(
            project_name="",  # Empty project name should raise error
            book_title="Test Book",
            category="fiction",
            genre="fantasy",
            description="A test book description",
            language="en",
            book_length="medium",
            num_characters="2-3",
            num_chapters=3
        )
