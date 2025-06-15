"""
LibriScribe package initialization.

Exposes core classes and functionality for the LibriScribe book writing assistant.
"""

from .agents.agent_base import Agent
from .knowledge_base import Character, ProjectKnowledgeBase

__all__ = ["Character", "ProjectKnowledgeBase", "Agent"]
