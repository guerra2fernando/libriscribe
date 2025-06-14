"""
Test suite for ProjectKnowledgeBase functionality.

These tests verify the core functionality of the ProjectKnowledgeBase class,
focusing on project metadata management and character handling. The tests use
mock implementations to isolate the testing of business logic from external
dependencies.
"""

import pytest

from tests.conftest import MockCharacter, MockProjectKnowledgeBase


def test_project_knowledge_base_creation() -> None:
    """
    Test basic creation of a ProjectKnowledgeBase instance.
    
    Verifies that:
    1. The knowledge base can be instantiated with valid parameters
    2. Basic attributes are correctly stored and accessible
    This is a fundamental test that should pass before running more complex scenarios.
    """
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
