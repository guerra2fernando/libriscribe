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
    """
    Test character addition to the knowledge base.
    
    Verifies that:
    1. A character can be successfully added to the knowledge base
    2. The character can be retrieved by name after addition
    3. The retrieved character maintains all its original properties
    
    This test is crucial for ensuring the basic character management 
    functionality works correctly.
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
    """
    Test behavior when requesting a non-existent character.
    
    Verifies that:
    1. Requesting a character that doesn't exist returns None
    2. The system handles missing characters gracefully
    
    This test ensures proper error handling and prevents issues with
    undefined character references.
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
    
    retrieved_character = kb.get_character("Nonexistent Character")
    assert retrieved_character is None

def test_multiple_characters() -> None:
    """
    Test handling of multiple characters in the knowledge base.
    
    Verifies that:
    1. Multiple characters can be added successfully
    2. All characters are stored and maintained separately
    3. Each character can be retrieved individually
    4. Character count is accurately tracked
    
    This test ensures the system can handle realistic book scenarios
    with multiple characters.
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
    """
    Test input validation for project knowledge base creation.
    
    Verifies that:
    1. Invalid inputs (empty project name) are rejected
    2. The system raises appropriate validation errors
    
    This test ensures data integrity by preventing the creation of
    invalid or incomplete project knowledge bases.
    """
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
