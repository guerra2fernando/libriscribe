"""Optimized formatting agent - no LLM for basic formatting."""
import re
from pathlib import Path
from typing import List
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
            console.print(f"📚 [cyan]Assembling manuscript (optimized)...[/cyan]")
            
            # Get project data
            project_data_path = Path(project_dir) / "project_data.json"
            project_knowledge_base = ProjectKnowledgeBase.load_from_file(str(project_data_path))
            
            # Create formatted content
            formatted_content = self._create_formatted_book(project_dir, project_knowledge_base)
            
            # Save
            write_markdown_file(output_path, formatted_content)
            console.print(f"[green]✅ Book formatted and saved to {output_path}[/green]")
            
        except Exception as e:
            print(f"ERROR: Failed to format book: {e}")
    
    def _create_formatted_book(self, project_dir: str, pkb: ProjectKnowledgeBase) -> str:
        """Create formatted book content without LLM."""
        content_parts = []
        
        # Title page
        content_parts.append(self._create_title_page(pkb))
        content_parts.append("\n\n---\n\n")
        
        # Table of contents
        content_parts.append(self._create_table_of_contents(project_dir))
        content_parts.append("\n\n---\n\n")
        
        # Chapters
        chapter_files = get_chapter_files(project_dir)
        for chapter_file in sorted(chapter_files):
            chapter_content = read_markdown_file(chapter_file)
            formatted_chapter = self._format_chapter(chapter_content)
            content_parts.append(formatted_chapter)
            content_parts.append("\n\n")
        
        return "".join(content_parts)
    
    def _create_title_page(self, pkb: ProjectKnowledgeBase) -> str:
        """Create title page."""
        return f"""# {pkb.title}

**Author:** {pkb.get('author', 'Unknown Author')}

**Genre:** {pkb.get('genre', 'Unknown')}

---

*{pkb.get('logline', 'A compelling story awaits...')}*
"""
    
    def _create_table_of_contents(self, project_dir: str) -> str:
        """Create table of contents."""
        toc_lines = ["# Table of Contents\n"]
        
        chapter_files = get_chapter_files(project_dir)
        for i, chapter_file in enumerate(sorted(chapter_files), 1):
            chapter_content = read_markdown_file(chapter_file)
            # Extract chapter title from first heading
            title_match = re.search(r'^#\s+(.+)$', chapter_content, re.MULTILINE)
            title = title_match.group(1) if title_match else f"Chapter {i}"
            toc_lines.append(f"{i}. [{title}](#chapter-{i})")
        
        return "\n".join(toc_lines)
    
    def _format_chapter(self, content: str) -> str:
        """Format chapter content consistently."""
        # Ensure chapter starts with proper heading
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Ensure consistent heading format
            if line.strip().startswith('# '):
                formatted_lines.append(line.strip())
            elif line.strip().startswith('## '):
                formatted_lines.append(line.strip())
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
