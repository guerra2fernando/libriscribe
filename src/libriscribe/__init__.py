"""
LibriScribe package initialization.

Exposes core classes and functionality for the LibriScribe book writing assistant.
"""

from .knowledge_base import Character, ProjectKnowledgeBase
from .agents.agent_base import Agent

__all__ = ['Character', 'ProjectKnowledgeBase', 'Agent']
