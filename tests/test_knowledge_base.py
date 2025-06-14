import pytest
from libriscribe.knowledge_base import ProjectKnowledgeBase, Character

def test_project_knowledge_base_creation():
    kb = ProjectKnowledgeBase(
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

def test_add_character():
    kb = ProjectKnowledgeBase(
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
    
    character = Character(
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
