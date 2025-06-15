# src/libriscribe/agents/character_generator.py

import json
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import Character, ProjectKnowledgeBase
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import extract_json_from_markdown, write_json_file
from libriscribe.utils.llm_client import LLMClient

console = Console()

logger = logging.getLogger(__name__)


class CharacterGeneratorAgent(Agent):
    """Generates character profiles."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("CharacterGeneratorAgent", llm_client)

    def execute(
        self, project_knowledge_base: ProjectKnowledgeBase, output_path: Optional[str] = None
    ) -> None:
        try:
            console.print("👥 [cyan]Creating character profiles...[/cyan]")
            prompt = prompts.CHARACTER_PROMPT.format(
                title=project_knowledge_base.title,
                genre=project_knowledge_base.genre,
                category=project_knowledge_base.category,
                language=project_knowledge_base.language,
                description=project_knowledge_base.description,
                num_characters=project_knowledge_base.num_characters,
                # ... other relevant fields
            )

            # Lower temperature for more structured output
            character_json_str = self.llm_client.generate_content_with_json_repair(
                prompt, max_tokens=4000, temperature=0.5
            )

            if not character_json_str:
                print("ERROR: Character generation failed. See Log")
                return
            try:
                characters = extract_json_from_markdown(character_json_str)
                if not characters or not isinstance(characters, list):
                    print("ERROR: Failed to parse character data")
                    return

                # Process and store characters in knowledge base
                processed_characters = []  # List to store processed characters
                for char_data in characters:
                    try:
                        # Normalize keys to lowercase
                        char_data = {k.lower(): v for k, v in char_data.items()}

                        # --- FIX for relationships and Nested Data ---
                        relationships = char_data.get("relationships", {}) or char_data.get(
                            "relationships with other characters", {}
                        )
                        if isinstance(relationships, str):
                            relationships = {"general": relationships}
                        elif isinstance(relationships, dict):
                            # Flatten nested relationships (if any)
                            flattened_relationships = {}
                            for rel_key, rel_value in relationships.items():
                                if isinstance(rel_value, str):
                                    flattened_relationships[rel_key] = rel_value
                                elif isinstance(rel_value, dict):
                                    # Flatten if it's a nested dict (unlikely, but handle it)
                                    flat_rel_value = ""
                                    for sub_key, sub_value in rel_value.items():
                                        if isinstance(sub_value, str):
                                            flat_rel_value += f"{sub_key}: {sub_value} "
                                        else:
                                            flat_rel_value += f"{sub_key}: {json.dumps(sub_value)} "
                                    flattened_relationships[rel_key] = flat_rel_value.strip()
                                else:
                                    flattened_relationships[rel_key] = json.dumps(rel_value)
                            relationships = flattened_relationships

                        # Flatten any other nested dictionaries (like we did for worldbuilding)
                        flattened_char_data = {}
                        for key, value in char_data.items():
                            if (
                                isinstance(value, dict) and key != "relationships"
                            ):  # Don't flatten relationships again
                                flattened_value = ""
                                for sub_key, sub_value in value.items():
                                    if isinstance(sub_value, str):
                                        flattened_value += f"{sub_key}: {sub_value} "
                                    else:
                                        flattened_value += f"{sub_key} : {json.dumps(sub_value)} "
                                flattened_char_data[key] = flattened_value.strip()

                            elif isinstance(value, str):
                                flattened_char_data[key] = value
                            elif isinstance(value, list):  # Handle lists (like personality_traits)
                                flattened_char_data[key] = [
                                    item.strip() if isinstance(item, str) else item
                                    for item in value
                                ]
                            else:
                                flattened_char_data[key] = json.dumps(value)

                        # --- MODIFIED PERSONALITY TRAITS HANDLING ---
                        personality_traits = flattened_char_data.get("personality_traits", "")

                        # Convert to string format instead of array
                        if isinstance(personality_traits, list):
                            # Join list into a comma-separated string
                            personality_traits = ", ".join(
                                [str(trait).strip() for trait in personality_traits if trait]
                            )
                        elif isinstance(personality_traits, str):
                            # Keep it as a string, just ensure it's properly formatted
                            personality_traits = personality_traits.strip()

                        # Only use default if we have an empty string after processing
                        if not personality_traits:
                            personality_traits = (
                                "Resourceful, Cautious, Determined"  # Default traits as string
                            )

                        # Create character using the flattened data
                        character = Character(
                            name=flattened_char_data.get("name", ""),
                            age=str(flattened_char_data.get("age", "")),
                            physical_description=flattened_char_data.get(
                                "physical description", ""
                            ),
                            personality_traits=personality_traits,  # Now using string instead of list
                            background=flattened_char_data.get("background", "")
                            or flattened_char_data.get("background/backstory", ""),
                            motivations=flattened_char_data.get("motivations", ""),
                            relationships=relationships,
                            role=flattened_char_data.get("role", "")
                            or flattened_char_data.get("role in the story", ""),
                            internal_conflicts=flattened_char_data.get("internal conflicts", "")
                            or flattened_char_data.get("internal_conflicts", ""),
                            external_conflicts=flattened_char_data.get("external conflicts", "")
                            or flattened_char_data.get("external_conflicts", ""),
                            character_arc=flattened_char_data.get("character arc", "")
                            or flattened_char_data.get("character_arc", ""),
                        )

                        # --- Update/Add Character ---
                        existing_character = project_knowledge_base.get_character(character.name)
                        if existing_character:
                            for key, value in character.model_dump().items():
                                if hasattr(existing_character, key):
                                    setattr(existing_character, key, value)
                        else:
                            project_knowledge_base.add_character(character)

                        processed_characters.append(character.model_dump())
                        console.print(f"[green]✅ Created character: {character.name}[/green]")

                        # Print all fields for verification
                        for key, value in character.model_dump().items():
                            console.print(
                                f"  - [cyan]{key.replace('_', ' ').title()}:[/cyan] {value}"
                            )

                    except Exception as e:
                        logger.warning(f"Skipping a character due to error: {str(e)}")
                        continue
            except json.JSONDecodeError:
                print("ERROR: Invalid JSON data received after repair attempts.")
                return
            except Exception as e:
                print("Error:", e)
                return
            if output_path is None:
                output_path = str(Path(project_knowledge_base.project_dir) / "characters.json")
            write_json_file(output_path, processed_characters)  # Save characters
            console.print("[green]💾 Character profiles saved![/green]")

        except Exception as e:
            self.logger.exception(f"Error generating character profiles: {e}")
            print("ERROR: Failed to generate character profiles. See log.")
