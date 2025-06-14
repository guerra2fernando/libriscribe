# src/libriscribe/agents/agent_base.py
import logging
from typing import Any, Optional

from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

class Agent:
    """Base class for all agents."""

    def __init__(self, name: str, llm_client: LLMClient):  # Receive LLMClient
        self.name = name
        self.llm_client = llm_client  # Use the passed LLMClient
        self.logger = logging.getLogger(self.name)

    def execute(self, *args, **kwargs) -> Any:
        """Executes the agent's main task. Must be implemented by subclasses."""
        raise NotImplementedError
