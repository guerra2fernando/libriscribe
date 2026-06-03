# src/libriscribe/agents/editor.py

import logging
from pathlib import Path

from libriscribe.agents.agent_base import Agent
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import read_markdown_file, write_markdown_file
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils.llm_client import LLMClient
from libriscribe.agents.content_reviewer import ContentReviewerAgent
# Add this import
from rich.console import Console
console = Console()


logger = logging.getLogger(__name__)

class EditorAgent(Agent):
    """Edits and refines chapters."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("EditorAgent", llm_client)

    def execute(self, project_knowledge_base: ProjectKnowledgeBase, chapter_number: int) -> None:
        """Edits a chapter and saves the revised version."""
        try:
            #--- FIX: Construct the path correctly using project_dir ---
            chapter_path = str(Path(project_knowledge_base.project_dir) / f"chapter_{chapter_number}.md")
            chapter_content = read_markdown_file(chapter_path)
            if not chapter_content:
                print(f"ERROR: Chapter file is empty: {chapter_path}")
                return
            chapter_title = self.extract_chapter_title(chapter_content)

            # Get the review results first
            reviewer_agent = ContentReviewerAgent(self.llm_client)
            review_results = reviewer_agent.execute(chapter_path)

            scene_titles = self.extract_scene_titles(chapter_content)
            scene_titles_instruction = ""
            if scene_titles:
                scene_titles_str = "\n".join(f"- {title}" for title in scene_titles)
                scene_titles_instruction = f"""
                    IMPORTANT: This chapter contains scene titles that must be preserved in your edit.
                    Make sure each scene begins with its title in bold format (using **Scene X: Title**).
                    Here are the scene titles to preserve:

                    {scene_titles_str}

                    If any scene is missing a title in the format "**Scene X: Title**", please add an appropriate title.
                    """
            prompt_data = {
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "book_title": project_knowledge_base.title,
                "genre": project_knowledge_base.genre,
                "language": project_knowledge_base.language,
                "chapter_content": chapter_content,
                "review_feedback": review_results.get("review", "")
            }

            console.print(f"✏️ [cyan]Editing Chapter {chapter_number} based on feedback...[/cyan]")
            prompt = prompts.EDITOR_PROMPT.format(**prompt_data) + scene_titles_instruction
            edited_response = self.llm_client.generate_content(prompt, max_tokens=8000)
            # --- KEY FIX: Use extract_json_from_markdown and check for None ---
            if "```" in edited_response:
                start = edited_response.find("```") + 3
                end = edited_response.rfind("```")
                
                # Skip the language identifier if present (e.g., ```markdown)
                next_newline = edited_response.find("\n", start)
                if next_newline < end and next_newline != -1:
                    start = next_newline + 1
                
                revised_chapter = edited_response[start:end].strip()
            else:
                # If no code blocks, try to extract the content after a leading explanation
                lines = edited_response.split("\n")
                content_start = 0
                for i, line in enumerate(lines):
                    if line.startswith("#") or line.startswith("Chapter"):
                        content_start = i
                        break
                
                if content_start > 0:
                    revised_chapter = "\n".join(lines[content_start:])
                else:
                    revised_chapter = edited_response
                    
                    
            if revised_chapter:
                 #--- FIX: Save as chapter_{chapter_number}_revised.md ---
                revised_chapter_path = str(Path(project_knowledge_base.project_dir) / f"chapter_{chapter_number}_revised.md")
                write_markdown_file(revised_chapter_path, revised_chapter)
                console.print(f"[green]✅ Edited chapter saved![/green]")
            else:
                print("ERROR: Could not extract revised chapter from editor output.")
                self.logger.error("Could not extract revised chapter content.")
                # --- ADD THIS: Log the raw response for debugging ---
                self.logger.error(f"Raw editor response: {edited_response}")


        except Exception as e:
            self.logger.exception(f"Error editing chapter {chapter_path}: {e}")
            print(f"ERROR: Failed to edit chapter. See log.")

    def extract_chapter_number(self, chapter_path: str) -> int:
        """Extracts chapter number."""
        try:
            return int(chapter_path.split("_")[1].split(".")[0])
        except:
            return -1

    def extract_chapter_title(self, chapter_content: str) -> str:
        """Extracts chapter title."""
        lines = chapter_content.split("\n")
        for line in lines:
            if line.startswith("#"):
                return line.replace("#", "").strip()
        return "Untitled Chapter"