# src/libriscribe/agents/content_reviewer.py
import logging
from typing import Any, Dict

from rich.console import Console

from libriscribe.agents.agent_base import Agent
from libriscribe.utils.file_utils import read_markdown_file
from libriscribe.utils.llm_client import LLMClient

console = Console()
logger = logging.getLogger(__name__)


class ContentReviewerAgent(Agent):
    """Reviews chapter content for consistency and clarity."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("ContentReviewerAgent", llm_client)
        self.llm_client = llm_client

    def execute(self, chapter_path: str) -> Dict[str, Any]:
        """Reviews a chapter for consistency, clarity, and plot holes.

        Args:
            chapter_path: Path to the chapter file.

        Returns:
            A dictionary containing review findings (e.g., inconsistencies, suggestions).
            Returns an empty dictionary if the file doesn't exist or is empty.
        """
        chapter_content = read_markdown_file(chapter_path)
        if not chapter_content:
            print(f"ERROR: Chapter file is empty or not found: {chapter_path}")
            return {}
        console.print(
            f"🔍 [cyan]Reviewing Chapter {chapter_path.split('_')[-1].split('.')[0]}...[/cyan]"
        )

        # Get the project_knowledge_base from the ProjectManagerAgent
        # We need to get the language from the project knowledge base
        # Since we're passed only the chapter_path, we need to infer the project

        # Extract project directory from chapter path to find project data
        from pathlib import Path

        from libriscribe.knowledge_base import ProjectKnowledgeBase

        chapter_file = Path(chapter_path)
        project_dir = chapter_file.parent
        project_data_path = project_dir / "project_data.json"

        # Default language in case we can't load the project data
        language = "English"

        # Try to load the project knowledge base to get the language
        if project_data_path.exists():
            try:
                project_kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
                if project_kb and hasattr(project_kb, "language"):
                    language = project_kb.language
            except Exception as e:
                self.logger.warning(f"Could not load project data for language detection: {e}")
                # Continue with default language

        prompt = """
        You are a meticulous content reviewer. Review the following chapter for:

        Language: {language}

        1.  **Internal Consistency:** Are character actions, dialogue, and motivations consistent with their established personalities and the overall plot?
        2.  **Clarity:** Are there any confusing passages, ambiguous descriptions, or unclear plot points?
        3.  **Plot Holes:** Are there any logical inconsistencies or unresolved questions within the chapter's narrative?
        4. **Redundancy**: Are there any sentences that repeat too much, or don't contribute to the overall?
        5. **Flow and Transitions:** Does the chapter flow smoothly from one scene or idea to the next? Are transitions between scenes clear?
        6. **Engagement:** Does the chapter maintain reader interest? Are there any sections that drag or feel slow?

        Provide specific examples of any issues found, referencing line numbers or sections where possible.  Output your review in Markdown format,
        with clear headings for each section (Consistency, Clarity, Plot Holes, etc.).  If no issues are found in a category,
        state "No issues found."

        Chapter Content:
        ---
        {chapter_content}
        ---
        """
        try:
            review_results = self.llm_client.generate_content(prompt, max_tokens=1500)
            return {"review": review_results}
        except Exception as e:
            self.logger.exception(f"Error reviewing chapter {chapter_path}: {e}")
            print(f"ERROR: Failed to review chapter {chapter_path}. See log for details.")
            return {}
