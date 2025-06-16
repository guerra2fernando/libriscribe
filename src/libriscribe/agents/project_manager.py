# src/libriscribe/agents/project_manager.py

import logging
from typing import Optional
from pathlib import Path

from libriscribe.agents.concept_generator import ConceptGeneratorAgent
from libriscribe.agents.outliner import OutlinerAgent
from libriscribe.agents.character_generator import CharacterGeneratorAgent
from libriscribe.agents.worldbuilding import WorldbuildingAgent
from libriscribe.agents.chapter_writer import ChapterWriterAgent
from libriscribe.agents.editor import EditorAgent
from libriscribe.agents.researcher import ResearcherAgent
from libriscribe.agents.formatting import FormattingAgent
from libriscribe.agents.content_reviewer import ContentReviewerAgent
from libriscribe.agents.style_editor import StyleEditorAgent
from libriscribe.agents.plagiarism_checker import PlagiarismCheckerAgent
from libriscribe.agents.fact_checker import FactCheckerAgent

from libriscribe.settings import Settings
from libriscribe.utils.file_utils import write_markdown_file, read_markdown_file
from libriscribe.utils import prompts_context as prompts
from libriscribe.knowledge_base import ProjectKnowledgeBase, Worldbuilding
from libriscribe.utils.llm_client import LLMClient
# For PDF generation
from fpdf import FPDF
import typer  # Import typer
from rich.console import Console
console = Console()

logger = logging.getLogger(__name__)

class ProjectManagerAgent:
    """Manages the book creation process."""

    def __init__(self, llm_client: LLMClient = None):
        self.settings = Settings()
        self.project_knowledge_base: Optional[ProjectKnowledgeBase] = None  # Use ProjectKnowledgeBase
        self.project_dir: Optional[Path] = None
        self.llm_client: Optional[LLMClient] = llm_client  # Add LLMClient instance
        self.agents = {} # Will be initialized after llm
        self.logger = logging.getLogger(self.__class__.__name__) # ADD THIS

    def initialize_llm_client(self, llm_provider: str):
        """Initializes the LLMClient and agents."""
        self.llm_client = LLMClient(llm_provider)
        self.agents = {
            "content_reviewer": ContentReviewerAgent(self.llm_client),  # Pass client
            "concept_generator": ConceptGeneratorAgent(self.llm_client),
            "outliner": OutlinerAgent(self.llm_client),
            "character_generator": CharacterGeneratorAgent(self.llm_client),
            "worldbuilding": WorldbuildingAgent(self.llm_client),
            "chapter_writer": ChapterWriterAgent(self.llm_client),
            "editor": EditorAgent(self.llm_client),
            "researcher": ResearcherAgent(self.llm_client),
            "formatting": FormattingAgent(self.llm_client),
            "style_editor": StyleEditorAgent(self.llm_client),
            "plagiarism_checker": PlagiarismCheckerAgent(self.llm_client),
            "fact_checker": FactCheckerAgent(self.llm_client),
        }

    def initialize_project_with_data(self, project_data: ProjectKnowledgeBase):
        """Initializes a project using the ProjectKnowledgeBase object."""
        self.project_dir = Path(self.settings.projects_dir) / project_data.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.project_knowledge_base = project_data
        self.project_knowledge_base.project_dir = self.project_dir
        
        # Ensure worldbuilding is None if not needed
        if not self.project_knowledge_base.worldbuilding_needed:
            self.project_knowledge_base.worldbuilding = None
            
        self.save_project_data()
        self.logger.info(f"🚀 Initialized project: {project_data.project_name}")
        console.print(f"✨ Project [green]'{project_data.project_name}'[/green] initialized successfully!")    
    def save_project_data(self):
        """Saves project data using the ProjectKnowledgeBase object."""
        if self.project_knowledge_base and self.project_dir:
            try:
                # Debug logs before save
                logger.info("Saving project data...")
                
                # Clean up worldbuilding fields before saving
                if hasattr(self.project_knowledge_base, 'clean_worldbuilding_for_category'):
                    # If you added the helper function to the class
                    self.project_knowledge_base.clean_worldbuilding_for_category()
                else:
                    # Direct cleanup
                    if not self.project_knowledge_base.worldbuilding_needed:
                        self.project_knowledge_base.worldbuilding = None
                    elif self.project_knowledge_base.worldbuilding:
                        # Get relevant fields based on category
                        category = self.project_knowledge_base.category.lower()
                        if category == "fiction":
                            fields_to_keep = [
                                "geography", "culture_and_society", "history", "rules_and_laws",
                                "technology_level", "magic_system", "key_locations",
                                "important_organizations", "flora_and_fauna", "languages",
                                "religions_and_beliefs", "economy", "conflicts"
                            ]
                        elif category == "non-fiction":
                            fields_to_keep = [
                                "setting_context", "key_figures", "major_events", "underlying_causes",
                                "consequences", "relevant_data", "different_perspectives", 
                                "key_concepts"
                            ]
                        elif category == "business":
                            fields_to_keep = [
                                "industry_overview", "target_audience", "market_analysis",
                                "business_model", "marketing_and_sales_strategy", "operations",
                                "financial_projections", "management_team",
                                "legal_and_regulatory_environment", "risks_and_challenges",
                                "opportunities_for_growth"
                            ]
                        elif category == "research paper":
                            fields_to_keep = [
                                "introduction", "literature_review", "methodology", "results",
                                "discussion", "conclusion", "references", "appendices"
                            ]
                        else:
                            fields_to_keep = []
                        
                        # Create clean worldbuilding
                        if fields_to_keep:
                            clean_worldbuilding = Worldbuilding()
                            for field in fields_to_keep:
                                if hasattr(self.project_knowledge_base.worldbuilding, field):
                                    value = getattr(self.project_knowledge_base.worldbuilding, field)
                                    if value and isinstance(value, str) and value.strip():
                                        setattr(clean_worldbuilding, field, value)
                            
                            # Replace with clean version
                            self.project_knowledge_base.worldbuilding = clean_worldbuilding
                
                file_path = str(self.project_dir / "project_data.json")
                self.project_knowledge_base.save_to_file(file_path)
                
                # Verify save
                if Path(file_path).exists():
                    # Read back and verify
                    loaded_data = ProjectKnowledgeBase.load_from_file(file_path)
                else:
                    logger.error(f"File not created: {file_path}")
            except Exception as e:
                logger.exception(f"Error saving project data: {e}")
                print(f"ERROR: Failed to save project data. See log.")
        else:
            logger.warning("Attempted to save project data before initialization.")
            
        
    def load_project_data(self, project_name: str):
        """Loads project data."""
        self.project_dir = Path(self.settings.projects_dir) / project_name
        project_data_path = self.project_dir / "project_data.json"
        if project_data_path.exists():
            data = ProjectKnowledgeBase.load_from_file(str(project_data_path)) 
            if data:
                self.                self.project_knowledge_base = data
                #CRITICAL: Set project_dir in project_knowledge_base
                self.project_knowledge_base.project_dir = self.project_dir
            else:
                raise ValueError("Failed to load or validate project data.")

        else:
            raise FileNotFoundError(f"Project data not found for project: {project_name}")

    def run_agent(self, agent_name: str, *args, **kwargs):
        """Runs a specific agent, passing project_data."""
        if agent_name not in self.agents:
            print(f"ERROR: Agent '{agent_name}' not found.")
            return

        agent = self.agents[agent_name]
        # Pass project_knowledge_base to agents that need it
        if agent_name in ["concept_generator", "outliner", "character_generator", "worldbuilding", "chapter_writer", "editor", "style_editor"]: 
            if self.project_knowledge_base:
                try:
                    agent.execute(project_knowledge_base=self.project_knowledge_base, *args, **kwargs)  # Pass project_knowledge_base
                except Exception as e:
                    logger.exception(f"Error running agent {agent_name}: {e}")
                    print(f"ERROR: Agent {agent_name} failed. See log for details.")
            else:
                print(f"ERROR: Project data not initialized before running {agent_name}.")
        else:  # Other agents
            try:
                agent.execute(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error running agent {agent_name}: {e}")
                print(f"ERROR: Agent {agent_name} failed. See log for details.")


    # --- Command Handlers (using ProjectKnowledgeBase) ---

    def generate_concept(self):
        """Generates a detailed book concept."""
        if self.project_knowledge_base is None:
            print("ERROR: No project initialized.")
            return
        self.run_agent("concept_generator") # type: ignore
        self.save_project_data() # Save after update


    def generate_outline(self):
        """Generates a book outline."""
        self.run_agent("outliner") # type: ignore
        self.save_project_data() # Save after update



    def generate_characters(self):
        """Generates character profiles."""
        self.run_agent("character_generator") # type: ignore
        self.save_project_data()# save after update

    def generate_worldbuilding(self):
        """Generates worldbuilding details."""
        self.run_agent("worldbuilding") # type: ignore
        self.save_project_data()# save after update

    def write_chapter(self, chapter_number: int):
        """Writes a specific chapter."""
        self.run_agent("chapter_writer",  chapter_number=chapter_number, output_path=str(self.project_dir / f"chapter_{chapter_number}.md"))
        self.save_project_data()


    def write_and_review_chapter(self, chapter_number: int):
        """Writes, reviews, and potentially edits a chapter (centralized review logic)."""
        self.write_chapter(chapter_number)  # Write the chapter
        self.review_content(chapter_number)  # Review for content issues

        if self.project_knowledge_base and self.project_knowledge_base.review_preference == "AI":
            # AI review - automatically edit without confirmation
            self.edit_chapter(chapter_number)  # AI editing
            self.edit_style(chapter_number)  # AI style editing
        elif self.project_knowledge_base and self.project_knowledge_base.review_preference == "Human":
            chapter_path = str(self.project_dir / f"chapter_{chapter_number}.md") # type: ignore
            console.print(f"\n📄 Chapter {chapter_number} ready for review!")
            if typer.confirm("Do you want to review and edit this chapter now?"):
                typer.edit(filename=chapter_path)
                print("\nChanges saved.")
            # Even for human review, we might want style editing
            if typer.confirm("Do you want AI to refine the writing style?"):
                self.edit_style(chapter_number)


    def edit_chapter(self, chapter_number: int):
        """Refines an existing chapter (Editor Agent)."""
        self.run_agent("editor", chapter_number=chapter_number)
        self.save_project_data()


    def format_book(self, output_path: str):
        """Formats the entire book into a single Markdown or PDF file.
        Robustly handles both original and revised chapters based on the project outline.
        """
        if not self.project_dir:
            print("ERROR: Project directory not initialized.")
            return

        if not self.project_knowledge_base:
            print("ERROR: Project knowledge base not loaded.")
            return

        try:
            # Get total expected chapters from knowledge base
            total_chapters = self.project_knowledge_base.num_chapters
            if isinstance(total_chapters, tuple):
                total_chapters = total_chapters[1]  # Get max if it's a range
            
            console.print(f"[bold]Formatting book with {total_chapters} chapters...[/bold]")
            
            # --- Original Version ---
            original_content = ""
            missing_chapters = []
            
            # Iterate through expected chapters
            for chapter_num in range(1, total_chapters + 1):
                chapter_path = self.project_dir / f"chapter_{chapter_num}.md"
                if chapter_path.exists():
                    chapter_content = read_markdown_file(str(chapter_path))
                    original_content += chapter_content + "\n\n"
                    console.print(f"[green]✓ Added original Chapter {chapter_num}[/green]")
                else:
                    missing_chapters.append(chapter_num)
                    console.print(f"[yellow]! Original Chapter {chapter_num} not found[/yellow]")
            
            if missing_chapters:
                console.print(f"[yellow]Warning: Missing original chapters: {missing_chapters}[/yellow]")
                if not original_content:
                    console.print("[red]ERROR: No original chapters found to format.[/red]")
                    return
            
            # Format with LLM to ensure proper structure and flow
            console.print(f"{self.agents['formatting'].name} is: Formatting Original Chapters...")
            prompt = prompts.FORMATTING_PROMPT.format(chapters=original_content)
            formatted_original = self.llm_client.generate_content(prompt, max_tokens=4000)
            
            # Add title page
            title_page = self.create_title_page(self.project_knowledge_base)
            formatted_original = title_page + formatted_original
            
            # Determine output path for original version
            original_output_path = output_path.replace(".md", "_original.md").replace(".pdf", "_original.pdf")
            
            # Save as Markdown or PDF (original version)
            if original_output_path.endswith(".md"):
                write_markdown_file(original_output_path, formatted_original)
                console.print(f"[green]📚 Original version formatted and saved![/green]")
            elif original_output_path.endswith(".pdf"):
                self.markdown_to_pdf(formatted_original, original_output_path)
                console.print(f"[green]📚 Original version formatted and saved![/green]")
            else:
                console.print(f"[red]ERROR: Unsupported output format: {original_output_path}. Must be .md or .pdf[/red]")
                return

            # --- Revised Version ---
            revised_content = ""
            missing_revised_chapters = []
            has_revised_chapters = False
            
            # Check if we have any revised chapters
            for chapter_num in range(1, total_chapters + 1):
                if (self.project_dir / f"chapter_{chapter_num}_revised.md").exists():
                    has_revised_chapters = True
                    break
            
            if not has_revised_chapters:
                console.print("[yellow]No revised chapters found. Skipping revised version formatting.[/yellow]")
                return
                
            # Process revised chapters
            for chapter_num in range(1, total_chapters + 1):
                revised_path = self.project_dir / f"chapter_{chapter_num}_revised.md"
                original_path = self.project_dir / f"chapter_{chapter_num}.md"
                
                if revised_path.exists():
                    chapter_content = read_markdown_file(str(revised_path))
                    revised_content += chapter_content + "\n\n"
                    console.print(f"[green]✓ Added revised Chapter {chapter_num}[/green]")
                elif original_path.exists():
                    # Fall back to original if revised doesn't exist
                    chapter_content = read_markdown_file(str(original_path))
                    revised_content += chapter_content + "\n\n"
                    console.print(f"[blue]→ Using original content for Chapter {chapter_num} (no revision found)[/blue]")
                    missing_revised_chapters.append(chapter_num)
                else:
                    missing_revised_chapters.append(chapter_num)
                    console.print(f"[yellow]! Chapter {chapter_num} not found (neither original nor revised)[/yellow]")
            
            if missing_revised_chapters:
                console.print(f"[yellow]Info: {len(missing_revised_chapters)} chapters don't have revised versions[/yellow]")
            
            # Format with LLM
            console.print(f"{self.agents['formatting'].name} is: Formatting Revised Chapters...")
            prompt_revised = prompts.FORMATTING_PROMPT.format(chapters=revised_content)
            formatted_revised = self.llm_client.generate_content(prompt_revised, max_tokens=4000)
            formatted_revised = title_page + formatted_revised
            
            # Save as Markdown or PDF (revised)
            if output_path.endswith(".md"):
                write_markdown_file(output_path, formatted_revised)
                console.print(f"[green]Revised version formatted and saved to: {output_path}[/green]")
            elif output_path.endswith(".pdf"):
                self.markdown_to_pdf(formatted_revised, output_path)
                console.print(f"[green]Revised version formatted and saved to: {output_path}[/green]")
            else:
                console.print(f"[red]ERROR: Unsupported output format: {output_path}. Must be .md or .pdf[/red]")
                
        except Exception as e:
            self.logger.exception(f"Error formatting book: {e}")
            console.print(f"[red]ERROR: Failed to format the book: {str(e)}[/red]")

    def research(self, query: str):
        """Performs web research."""
        self.run_agent("researcher", query, str(self.project_dir / "research_results.md"))# type: ignore

    def edit_style(self, chapter_number: int):
        """Refines writing style."""
        self.run_agent("style_editor", chapter_number=chapter_number)
        self.save_project_data()

    def check_plagiarism(self, chapter_number: int):
        """Checks for plagiarism."""
        chapter_path = str(self.project_dir / f"chapter_{chapter_number}.md")# type: ignore
        results = self.agents["plagiarism_checker"].execute(chapter_path)  # type: ignore
        print(f"Plagiarism check results for chapter {chapter_number}: {results}")

    def check_facts(self, chapter_number: int):
        """Checks factual claims."""
        chapter_path = str(self.project_dir / f"chapter_{chapter_number}.md")# type: ignore
        results = self.agents["fact_checker"].execute(chapter_path)  # type: ignore
        print(f"Fact-check results for chapter {chapter_number}: {results}")

    def review_content(self, chapter_number: int):
        """Reviews chapter content."""
        chapter_path = str(self.project_dir / f"chapter_{chapter_number}.md")# type: ignore
        results = self.agents["content_reviewer"].execute(chapter_path) # type: ignore
        print(f"Content review results for chapter {chapter_number}:\n{results.get('review', 'No review available.')}")

    def does_chapter_exist(self, chapter_number: int) -> bool:
        """Checks if a chapter file exists."""
        chapter_path = self.project_dir / f"chapter_{chapter_number}.md" # type: ignore
        return chapter_path.exists()

    def checkpoint(self):
        """Saves the current project state silently."""
        try:
            self.save_project_data()  # This should not output anything to console
        except Exception as e:
            logger.error(f"Checkpoint failed: {e}")
            
    def create_title_page(self, project_knowledge_base:ProjectKnowledgeBase) -> str: # now accepts ProjectKnowledgeBase
        """Creates a Markdown title page."""
        title = project_knowledge_base.title
        author = project_knowledge_base.get('author', 'Unknown Author')  # Assuming you might add author later
        genre = project_knowledge_base.genre
        language = project_knowledge_base.language
        title_page = f"# {title}\n\n"
        # Check language for different title page formats
        if language == "English":
            title_page += f"## By {author}\n\n"
            title_page += f"**Genre:** {genre}\n\n"
        elif language == "Brazilian Portuguese":
            title_page += f"## Por {author}\n\n"
            title_page += f"**Gênero:** {genre}\n\n"
        # Add other language variations as needed
        else:
            # Default to English if language not specifically handled
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