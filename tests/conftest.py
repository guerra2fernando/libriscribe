"""
Pytest fixtures and mock classes for LibriScribe testing.

This module provides reusable test fixtures and mock implementations of core classes
to enable consistent and isolated testing across the LibriScribe test suite.
"""

from typing import List, Optional

import pytest
from pydantic import BaseModel
from unittest.mock import Mock


class MockCharacter(BaseModel):
    """
    Mock implementation of a book character for testing.
    
    This simplified version contains only the essential attributes needed for testing
    character-related functionality without the complexity of the full Character model.
    """
    name: str
    role: str
    description: str
    background: str
    goals: str
    personality: str


class MockProjectKnowledgeBase(BaseModel):
    """
    Mock implementation of the ProjectKnowledgeBase for testing.
    
    Provides a lightweight version of the knowledge base with just enough functionality
    to test character management and basic project properties. This mock helps isolate
    tests from the complexity of the full ProjectKnowledgeBase implementation.
    """
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
        """
        Add a character to the knowledge base.
        
        This simplified implementation just appends to a list, whereas the real
        implementation might handle additional validation and relationships.
        
        Args:
            character: The MockCharacter instance to add
        """
        self.characters.append(character)

    def get_character(self, character_name: str) -> Optional[MockCharacter]:
        """
        Retrieve a character by name from the knowledge base.
        
        Implements basic character lookup without the complexity of the full system's
        potential caching or database interactions.
        
        Args:
            character_name: Name of the character to find
            
        Returns:
            MockCharacter if found, None otherwise
        """
        for character in self.characters:
            if character.name == character_name:
                return character
        return None


@pytest.fixture
def mock_llm_client() -> Mock:
    """
    Fixture providing a mock LLM client for testing.
    
    Creates a Mock object that simulates the LLMClient's behavior without making
    actual API calls. This ensures tests are fast and don't require external services.
    
    Returns:
        Mock object configured with basic LLM client behavior
    """
    mock_client = Mock()
    mock_client.generate_content.return_value = "Mock response"
    return mock_client


@pytest.fixture
def sample_project_knowledge_base() -> MockProjectKnowledgeBase:
    """
    Fixture providing a sample project knowledge base for testing.
    
    Creates a consistent, pre-configured knowledge base instance that can be used
    across multiple tests. This helps maintain test consistency and reduces
    duplicate setup code.
    
    Returns:
        MockProjectKnowledgeBase instance with sample fantasy project data
    """
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
