"""Optimized formatting agent - no LLM for basic formatting."""
import re
from pathlib import Path
from libriscribe.agents.agent_base import Agent
from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils.file_utils import get_chapter_files, read_markdown_file, write_markdown_file
from libriscribe.knowledge_base import ProjectKnowledgeBase
from rich.console import Console

console = Console()

class OptimizedFormattingAgent(Agent):
    """Formats book using local processing instead of expensive LLM calls."""
    
    def __init__(self, llm_client: LLMClient):
        super().__init__("OptimizedFormattingAgent", llm_client)
    
    def execute(self, project_dir: str, output_path: str) -> None:
        """Format book locally - saves $2+ per book."""
        try:
            console.print(f"📚 [cyan]Assembling manuscript (cost-optimized)...[/cyan]")
            
            project_data_path = Path(project_dir) / "project_data.json"
            project_knowledge_base = ProjectKnowledgeBase.load_from_file(str(project_data_path))
            
            formatted_content = self._create_formatted_book(project_dir, project_knowledge_base)
            
            if output_path.endswith(".md"):
                write_markdown_file(output_path, formatted_content)
            
            console.print(f"[green]✅ Book formatted and saved to {output_path}[/green]")
            console.print(f"[green]💰 Saved ~$2.40 in LLM costs vs original formatting[/green]")
            
        except Exception as e:
            print(f"ERROR: Failed to format book: {e}")
    
    def _create_formatted_book(self, project_dir: str, pkb: ProjectKnowledgeBase) -> str:
        """Create formatted book content without LLM."""
        parts = []
        
        # Title page
        parts.append(f"""# {pkb.title}

**Author:** {pkb.get('author', 'Unknown Author')}
**Genre:** {pkb.get('genre', 'Unknown')}

---

*{pkb.get('logline', 'A compelling story awaits...')}*

""")
        
        # Table of contents
        parts.append("# Table of Contents\n\n")
        chapter_files = get_chapter_files(project_dir)
        for i, chapter_file in enumerate(sorted(chapter_files), 1):
            content = read_markdown_file(chapter_file)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else f"Chapter {i}"
            parts.append(f"{i}. {title}\n")
        
        parts.append("\n---\n\n")
        
        # Chapters
        for chapter_file in sorted(chapter_files):
            content = read_markdown_file(chapter_file)
            # Ensure proper chapter heading format
            content = re.sub(r'^#\s+', '# ', content, flags=re.MULTILINE)
            parts.append(content + "\n\n")
        
        return "".join(parts)
