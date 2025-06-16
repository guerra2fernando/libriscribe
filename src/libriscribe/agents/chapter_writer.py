# src/libriscribe/agents/chapter_writer.py

import logging
from pathlib import Path
from typing import Optional
from libriscribe.agents.agent_base import Agent
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import write_markdown_file
from libriscribe.knowledge_base import ProjectKnowledgeBase, Chapter, Scene
from libriscribe.utils.llm_client import LLMClient

from rich.console import Console

console = Console()

logger = logging.getLogger(__name__)

class ChapterWriterAgent(Agent):
    """Writes chapters."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("ChapterWriterAgent", llm_client)


    def execute(self, project_knowledge_base: ProjectKnowledgeBase, chapter_number: int, output_path: Optional[str] = None) -> None:
        """Writes a chapter scene by scene."""
        try:
            # Get chapter data
            chapter = project_knowledge_base.get_chapter(chapter_number)
            if not chapter:
                console.print(f"[red]ERROR: Chapter {chapter_number} not found in knowledge base.[/red]")
                # Create a default chapter if not found
                chapter = Chapter(
                    chapter_number=chapter_number,
                    title=f"Chapter {chapter_number}",
                    summary="A new chapter in the unfolding story."
                )
                # Add a default scene
                default_scene = Scene(
                    scene_number=1,
                    summary="The story continues with new developments.",
                    characters=["Shade"],
                    setting="Neo-London",
                    goal="Advance the plot",
                    emotional_beat="Tension"
                )
                chapter.scenes.append(default_scene)
                project_knowledge_base.add_chapter(chapter)
                console.print(f"[yellow]Created default chapter {chapter_number} to proceed.[/yellow]")

            console.print(f"\n[cyan]📝 Writing Chapter {chapter_number}: {chapter.title}[/cyan]")

            
            # Make sure there's at least one scene
            if not chapter.scenes:
                console.print(f"[yellow]No scenes found for Chapter {chapter_number}. Creating a default scene.[/yellow]")
                default_scene = Scene(
                    scene_number=1,
                    summary="The story continues with new developments.",
                    characters=["Shade"],
                    setting="Neo-London",
                    goal="Advance the plot",
                    emotional_beat="Tension"
                )
                chapter.scenes.append(default_scene)
            
            # Make sure scenes are ordered by scene number
            ordered_scenes = sorted(chapter.scenes, key=lambda s: s.scene_number)
            # Process each scene individually
            scene_contents = []
            
            for scene in ordered_scenes:
                console.print(f"🎬 Creating Scene/Section {scene.scene_number} of {len(ordered_scenes)}...")

                # Generate a scene title if none exists
                scene_title = f"Scene {scene.scene_number}: {scene.summary[:30]}..." if len(scene.summary) > 30 else f"Scene {scene.scene_number}: {scene.summary}"
                
                # Create a prompt for this specific scene
                scene_prompt = prompts.SCENE_PROMPT.format(
                    chapter_number=chapter_number,
                    chapter_title=chapter.title,
                    book_title=project_knowledge_base.title,
                    genre=project_knowledge_base.genre,
                    category=project_knowledge_base.category,
                    language=project_knowledge_base.language,  # Add language parameter
                    chapter_summary=chapter.summary,
                    scene_number=scene.scene_number,
                    scene_summary=scene.summary,
                    characters=", ".join(scene.characters) if scene.characters else "None specified",
                    setting=scene.setting if scene.setting else "None specified",
                    goal=scene.goal if scene.goal else "None specified",
                    emotional_beat=scene.emotional_beat if scene.emotional_beat else "None specified",
                    total_scenes=len(ordered_scenes)
                )
                
                scene_prompt += f"\n\nIMPORTANT: Begin the scene with the title: **{scene_title}**"

                
                # Generate the scene content
                scene_content = self.llm_client.generate_content(scene_prompt, max_tokens=2000)
                if not scene_content:
                    console.print(f"[yellow]Warning: Failed to generate content for Scene {scene.scene_number}. Using placeholder.[/yellow]")
                    scene_content = f"[Scene {scene.scene_number} content unavailable]"
                
                # Ensure the scene title is included
                if not scene_content.startswith(f"**{scene_title}**") and not scene_content.startswith(f"# {scene_title}"):
                    scene_content = f"**{scene_title}**\n\n{scene_content}"
                
                scene_contents.append(scene_content)
            
            
            # Combine scenes into a complete chapter
            chapter_content = f"## Chapter {chapter_number}: {chapter.title}\n\n"
            chapter_content += "\n\n".join(scene_contents)
            
            # Save the chapter
            if output_path is None:
                output_path = str(Path(project_knowledge_base.project_dir) / f"chapter_{chapter_number}.md")
            write_markdown_file(output_path, chapter_content)
            
            console.print(f"[green]✅ Chapter {chapter_number} completed with {len(ordered_scenes)} scenes![/green]")
            
        except Exception as e:
            self.logger.exception(f"Error writing chapter {chapter_number}: {e}")
            console.print(f"[red]ERROR: Failed to write chapter {chapter_number}. See log for details.[/red]")