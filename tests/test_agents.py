import pytest
from libriscribe.agents.agent_base import Agent
from libriscribe.agents.concept_generator import ConceptGeneratorAgent
from libriscribe.agents.character_generator import CharacterGeneratorAgent
from libriscribe.agents.outliner import OutlinerAgent

def test_base_agent_initialization(mock_llm_client):
    agent = Agent("test_agent", mock_llm_client)
    assert agent.name == "test_agent"
    assert agent.llm_client == mock_llm_client

def test_concept_generator(mock_llm_client, sample_project_knowledge_base):
    agent = ConceptGeneratorAgent(mock_llm_client)
    mock_llm_client.generate_content.return_value = "Generated concept"
    agent.execute(sample_project_knowledge_base)
    assert mock_llm_client.generate_content.called

def test_character_generator(mock_llm_client, sample_project_knowledge_base):
    agent = CharacterGeneratorAgent(mock_llm_client)
    mock_llm_client.generate_content_with_json_repair.return_value = '''
    {
        "characters": [
            {
                "name": "Test Character",
                "role": "protagonist",
                "description": "A test character",
                "background": "Test background",
                "goals": "Test goals",
                "personality": "Test personality"
            }
        ]
    }
    '''
    agent.execute(sample_project_knowledge_base)
    assert mock_llm_client.generate_content_with_json_repair.called
    assert len(sample_project_knowledge_base.characters) > 0

def test_outliner_agent(mock_llm_client, sample_project_knowledge_base):
    agent = OutlinerAgent(mock_llm_client)
    mock_llm_client.generate_content.return_value = "# Chapter 1\nTest outline"
    agent.execute(sample_project_knowledge_base)
    assert mock_llm_client.generate_content.called
