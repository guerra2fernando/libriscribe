import pytest
from unittest.mock import Mock
from libriscribe.knowledge_base import ProjectKnowledgeBase

@pytest.fixture
def mock_llm_client():
    mock_client = Mock()
    mock_client.generate_content.return_value = "Mock response"
    return mock_client

@pytest.fixture
def sample_project_knowledge_base():
    return ProjectKnowledgeBase(
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
