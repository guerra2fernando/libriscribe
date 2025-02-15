# src/libriscribe/agents/character_generator.py
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils import prompts_context as prompts
from libriscribe.agents.agent_base import Agent
from libriscribe.utils.file_utils import write_json_file, read_json_file, extract_json_from_markdown # Modified import
#MODIFIED
from libriscribe.knowledge_base import ProjectKnowledgeBase, Character


logger = logging.getLogger(__name__)

class CharacterGeneratorAgent(Agent):
    """Generates character profiles."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("CharacterGeneratorAgent", llm_client)

    def execute(self, project_knowledge_base: ProjectKnowledgeBase, output_path: Optional[str] = None) -> None: # Use project data
        """Generates character profiles, handling Markdown-wrapped JSON."""
        try:
            prompt = prompts.CHARACTER_PROMPT.format(**project_knowledge_base.model_dump()) # Use model_dump
            character_json_str = self.llm_client.generate_content_with_json_repair(prompt, max_tokens=4000) # Use repair
            if not character_json_str:
                print("ERROR: Character generation failed. See Log")
                return

            characters = extract_json_from_markdown(character_json_str)
            if characters is None:  # Parsing failed
                print("ERROR: Invalid character data received. Cannot save.")
                return

            if not isinstance(characters, list):
                self.logger.warning("Character data is not a list.")
                characters = []
            else:
                # Process and store characters in knowledge base
                for char_data in characters:
                    try:
                        character = Character(**char_data)
                        project_knowledge_base.add_character(character)
                    except Exception as e:
                        logger.warning(f"Skipping a character because: {e}")
                        continue

            if output_path is None:
                output_path = str(Path(project_knowledge_base.project_name).parent / "characters.json")
            write_json_file(output_path, characters) # Save data

        except Exception as e:
            self.logger.exception(f"Error generating character profiles: {e}")
            print(f"ERROR: Failed to generate character profiles. See log.")