# src/libriscribe/agents/content_reviewer.py
import logging
from typing import Any, Dict

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils.file_utils import read_markdown_file
from rich.console import Console
console = Console()
logger = logging.getLogger(__name__)

class ContentReviewerAgent(Agent):
    """Reviews chapter content for consistency and clarity."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("ContentReviewerAgent", llm_client)
        self.llm_client = llm_client

    def execute(self, chapter_path: str, project_knowledge_base: "ProjectKnowledgeBase | None" = None) -> Dict[str, Any]:
        """Reviews a chapter for consistency, clarity, and plot holes."""
        from pathlib import Path

        chapter_content = read_markdown_file(chapter_path)
        if not chapter_content:
            print(f"ERROR: Chapter file is empty or not found: {chapter_path}")
            return {}
        console.print(f"🔍 [cyan]Reviewing Chapter {chapter_path.split('_')[-1].split('.')[0]}...[/cyan]")

        # Use passed PKB; fall back to loading from disk
        pkb = project_knowledge_base
        if pkb is None:
            project_data_path = Path(chapter_path).parent / "project_data.json"
            if project_data_path.exists():
                try:
                    pkb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
                except Exception as e:
                    self.logger.warning(f"Could not load project data: {e}")

        language = pkb.language if pkb else "English"
        genre = pkb.genre if pkb else "Unknown"
        tone = pkb.tone if pkb else "Informative"
        target_audience = pkb.target_audience if pkb else "General"

        prompt = f"""
        You are a meticulous content reviewer. Review the following chapter for:

        Language: {language}
        Genre: {genre}
        Tone: {tone}
        Target Audience: {target_audience}

        1. **Internal Consistency:** Are character actions, dialogue, and motivations consistent with their established personalities and the overall plot?
        2. **Clarity:** Are there any confusing passages, ambiguous descriptions, or unclear plot points?
        3. **Plot Holes:** Are there any logical inconsistencies or unresolved questions within the chapter's narrative?
        4. **Redundancy:** Are there any sentences that repeat too much or don't contribute to the overall narrative?
        5. **Flow and Transitions:** Does the chapter flow smoothly from one scene or idea to the next?
        6. **Engagement:** Does the chapter maintain reader interest for the target audience? Are there sections that drag?
        7. **Tone Consistency:** Does the writing maintain the expected {tone} tone throughout?

        Provide specific examples of any issues found. Output your review in Markdown format with clear headings for each section. If no issues are found in a category, state "No issues found."

        Chapter Content:
        ---
        {chapter_content}
        ---
        """
        try:
            review_results = self.llm_client.generate_content(prompt, max_tokens=4000)
            return {"review": review_results}
        except Exception as e:
            self.logger.exception(f"Error reviewing chapter {chapter_path}: {e}")
            print(f"ERROR: Failed to review chapter {chapter_path}. See log for details.")
            return {}