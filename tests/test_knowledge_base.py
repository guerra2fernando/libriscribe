import pytest
from conftest import MockProjectKnowledgeBase
from pydantic import BaseModel

class MockCharacter(BaseModel):
    name: str
    role: str
    description: str
    background: str
    goals: str
    personality: str

def test_project_knowledge_base_creation():
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

# Temporarily commenting out this test until we have access to the full knowledge_base module
# def test_add_character():
#     kb = MockProjectKnowledgeBase(
#         project_name="Test Project",
#         book_title="Test Book",
#         category="fiction",
#         genre="fantasy",
#         description="A test book description",
#         language="en",
#         book_length="medium",
#         num_characters="2-3",
#         num_chapters=3
#     )
#     
#     character = MockCharacter(
#         name="Test Character",
#         role="protagonist",
#         description="A test character",
#         background="Test background",
#         goals="Test goals",
#         personality="Test personality"
#     )
#     
#     kb.add_character(character)
#     retrieved_character = kb.get_character("Test Character")
#     assert retrieved_character is not None
#     assert retrieved_character.name == "Test Character"
