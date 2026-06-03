# src/libriscribe/agents/plagiarism_checker.py 

import logging
from typing import Any, Dict, List

from libriscribe.agents.agent_base import Agent
from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils.file_utils import read_markdown_file, extract_json_from_markdown
from rich.console import Console
console = Console()
logger = logging.getLogger(__name__)

class PlagiarismCheckerAgent(Agent):
    """Checks a chapter for potential plagiarism."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("PlagiarismCheckerAgent", llm_client)
        self.llm_client = llm_client

    def execute(self, chapter_path: str) -> List[Dict[str, Any]]:
        """Checks a chapter for potential plagiarism, handling Markdown-wrapped JSON."""

        chapter_content = read_markdown_file(chapter_path)
        if not chapter_content:
            print(f"ERROR: Chapter file is empty or not found: {chapter_path}")
            return []

        # --- Split into chunks
        chunks = self.split_into_chunks(chapter_content, chunk_size=500) # Smaller chunk size

        plagiarism_results = []
        for chunk in chunks:
            check_result = self.check_plagiarism(chunk)
            if check_result:  # Only add if potential plagiarism is found
                plagiarism_results.extend(check_result)

        return plagiarism_results

    def check_plagiarism(self, text_chunk: str) -> List[Dict[str, Any]]:
        """Checks a text chunk, using extract_json_from_markdown."""
        console.print(f"🔎 [cyan]Checking originality of Chapter {chapter_path.split('_')[-1].split('.')[0]}...[/cyan]")

        prompt = f"""
       You are a plagiarism detection expert. Analyze the following text for potential plagiarism.
       The text is written in {project_knowledge_base.language}.
       
       Do NOT compare it to the entire internet. Instead, focus on identifying common phrases, sentence structures,
       or ideas that might indicate a lack of originality.  If you find something that raises concerns,
       return it as a JSON array. Each item should have this format: {{"text": "...", "similarity_score": 0.8, "source": "Possible source or explanation"}}.
       If the text appears original, return an empty JSON array [].

       Text:
       ---
       {text_chunk}
       ---
       """
        try:
            response_json_str = self.llm_client.generate_content(prompt, max_tokens=500)
            results = extract_json_from_markdown(response_json_str)
            if results is None:
                return []  # Return empty list on parsing failure
            if not isinstance(results, list):
                 logger.warning("Plagiarism check result is not a List")
                 return []

            return results

        except Exception as e:
            self.logger.exception(f"Error during plagiarism check: {e}")
            print(f"ERROR: Failed to check for plagiarism. See log.")
            return []

    def split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Splits the text into smaller chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks