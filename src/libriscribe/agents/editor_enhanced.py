"""Enhanced editor agent with external prompt support."""
import logging
from typing import Dict, Any
from libriscribe.agents.agent_base import Agent
from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils.prompt_integration import ExternalPromptMixin
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import extract_json_from_markdown
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class EnhancedEditorAgent(Agent, ExternalPromptMixin):
    """Editor agent with external prompt template support."""
    
    def __init__(self, llm_client: LLMClient):
        Agent.__init__(self, "EnhancedEditorAgent", llm_client)
        ExternalPromptMixin.__init__(self)
    
    def execute(self, chapter_number: int, **kwargs) -> Dict[str, Any]:
        """Execute chapter editing with external prompts."""
        try:
            # Get chapter content and review data (simplified for demo)
            prompt_data = {
                "genre": kwargs.get("genre", "fiction"),
                "book_title": kwargs.get("book_title", "Untitled"),
                "language": kwargs.get("language", "English"),
                "chapter_number": chapter_number,
                "chapter_title": f"Chapter {chapter_number}",
                "chapter_content": kwargs.get("chapter_content", "Sample content..."),
                "review_feedback": kwargs.get("review_feedback", "No specific feedback.")
            }
            
            console.print(f"✏️ [cyan]Editing Chapter {chapter_number} with external prompts...[/cyan]")
            
            # Use external prompt with fallback to hardcoded
            edited_content = self.generate_with_external_prompt(
                prompt_name="editor",
                fallback_prompt=prompts.EDITOR_PROMPT,
                prompt_data=prompt_data,
                default_max_tokens=8000
            )
            
            console.print(f"✅ [green]Chapter {chapter_number} edited successfully[/green]")
            return {"edited_content": edited_content}
            
        except Exception as e:
            logger.exception(f"Error editing chapter {chapter_number}: {e}")
            return {"error": str(e)}
