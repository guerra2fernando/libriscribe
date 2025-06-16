# src/libriscribe/agents/formatting.py
import logging
from pathlib import Path

from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils import prompts_context as prompts
from libriscribe.agents.agent_base import Agent
from libriscribe.utils.file_utils import get_chapter_files, read_markdown_file, write_markdown_file
# For PDF creation
from fpdf import FPDF

from libriscribe.knowledge_base import ProjectKnowledgeBase
from rich.console import Console
console = Console()
logger = logging.getLogger(__name__)

class FormattingAgent(Agent):
    """Formats the book into a single Markdown or PDF file."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("FormattingAgent", llm_client)

    def execute(self, project_dir: str, output_path: str) -> None:
        """Formats the book and saves to output path, handles both Markdown and PDF"""

        try:
            chapter_files = get_chapter_files(project_dir)
            if not chapter_files:
                print("ERROR: No chapter files found to format.")
                return

            all_chapters_content = ""
            for chapter_file in chapter_files:
                all_chapters_content += read_markdown_file(chapter_file) + "\n\n"


            # Get project data (for title page)
            project_data_path = Path(project_dir) / "project_data.json"
            project_knowledge_base = ProjectKnowledgeBase.load_from_file(str(project_data_path)) 
            if not project_knowledge_base:
              print(f"ERROR: Could not load project data from {project_data_path}")
              return


            # Format with LLM
            console.print(f"📚 [cyan]Assembling final manuscript...[/cyan]")
            prompt = prompts.FORMATTING_PROMPT.format(chapters=all_chapters_content,  language=project_knowledge_base.language)
            formatted_markdown = self.llm_client.generate_content(prompt, max_tokens=120000) # May need large token limit

            # Add title page (before LLM formatting, for simplicity)
            title_page = self.create_title_page(project_knowledge_base) 
            formatted_markdown = title_page + formatted_markdown


            # Save as Markdown
            if output_path.endswith(".md"):
                write_markdown_file(output_path, formatted_markdown)

            # Save as PDF.
            elif output_path.endswith(".pdf"):
              self.markdown_to_pdf(formatted_markdown, output_path)
            else:
                print(f"ERROR: Unsupported output format: {output_path}.  Must be .md or .pdf")
                return

        except Exception as e:
            self.logger.exception(f"Error formatting book: {e}")
            print(f"ERROR: Failed to format the book. See log.")

    def create_title_page(self, project_knowledge_base:ProjectKnowledgeBase) -> str: # now accepts ProjectKnowledgeBase
        """Creates a Markdown title page."""
        title = project_knowledge_base.title
        author = project_knowledge_base.get('author', 'Unknown Author')  # Assuming you might add author later
        genre = project_knowledge_base.genre

        title_page = f"# {title}\n\n"
        title_page += f"## By {author}\n\n"
        title_page += f"**Genre:** {genre}\n\n"
        return title_page

    def markdown_to_pdf(self, markdown_text:str, output_path:str):
      """Converts the formatted markdown to PDF"""
      pdf = FPDF()
      pdf.add_page()
      pdf.set_font("Arial", size=12)

      # Basic Markdown parsing and PDF generation
      lines = markdown_text.split("\n")
      for line in lines:
          if line.startswith("# "):  # Chapter heading
              pdf.set_font("Arial", 'B', 16)  # Bold, larger font
              pdf.cell(0, 10, line[2:], ln=True)  # Remove '#' and add to PDF
              pdf.set_font("Arial", size=12)  # Reset font
          elif line.startswith("## "): # Subheading
              pdf.set_font("Arial", 'B', 14)
              pdf.cell(0, 10, line[3:], ln=True)
              pdf.set_font("Arial", size=12)  # Reset font
          else: # Regular text
            pdf.multi_cell(0, 10, line)
      pdf.output(output_path)