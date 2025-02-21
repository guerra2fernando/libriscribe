# src/libriscribe/main.py
import typer
from libriscribe.agents.project_manager import ProjectManagerAgent
from typing import List, Dict, Any
from libriscribe.utils.llm_client import LLMClient
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import logging
#MODIFIED
from libriscribe.knowledge_base import ProjectKnowledgeBase, Chapter  # Import the new class
from libriscribe.settings import Settings
from rich.progress import track  # Import track
try:
    from pick import pick
except ImportError:
    console.print("[red]The 'pick' package is required for this application.[/red]")
    console.print("[yellow]Please install it with: pip install pick[/yellow]")
    import sys
    sys.exit(1)
# Configure logging (same as before)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Remove timestamp and level info from user-visible logs
    handlers=[
        logging.FileHandler("libriscribe.log"),  # Send detailed logs to file instead
        logging.StreamHandler()  # Simplified logs to console
    ]
)

console = Console()
app = typer.Typer()
#project_manager = ProjectManagerAgent()  # Initialize ProjectManager
project_manager = ProjectManagerAgent(llm_client=None)
logger = logging.getLogger(__name__)

def select_llm(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    """Lets the user select an LLM provider."""
    available_llms = []
    settings = Settings()

    if settings.openai_api_key:
        available_llms.append("openai")
    if settings.claude_api_key:
        available_llms.append("claude")
    if settings.google_ai_studio_api_key:
        available_llms.append("google_ai_studio")
    if settings.deepseek_api_key:
        available_llms.append("deepseek")
    if settings.mistral_api_key:
        available_llms.append("mistral")

    if not available_llms:
        console.print("[red]❌ No LLM API keys found in .env file. Please add at least one.[/red]")
        raise typer.Exit(code=1)

    llm_choice = select_from_list("🤖 Select your preferred AI model:", available_llms)
    
    # Convert display name back to API identifier
    if "OpenAI" in llm_choice:
        llm_choice = "openai"
    elif "Claude" in llm_choice:
        llm_choice = "claude"
    elif "Google Gemini" in llm_choice:
        llm_choice = "google_ai_studio"
    elif "DeepSeek" in llm_choice:
        llm_choice = "deepseek"
    elif "Mistral" in llm_choice:
        llm_choice = "mistral"
        
    project_knowledge_base.set("llm_provider", llm_choice)
    return llm_choice

def introduction():
    """Prints a welcome message (same as before)."""
    console.print(
        Panel(
            "[bold blue]📚✨ Welcome to Libriscribe! ✨📚[/bold blue]\n\n"
            "Libriscribe is an AI-powered open-source book creation system made by Fernando Guerra",
            title="[bold blue]Libriscribe[/bold blue]",
            border_style="blue",
        )
    )

def select_from_list(prompt: str, options: List[str], allow_custom: bool = False) -> str:
    """Presents options with arrow key navigation and returns selection."""
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.style import Style
    from rich.text import Text
    from pick import pick  # Make sure to install this: pip install pick
    
    console = Console()
    console.print(f"[bold]{prompt}[/bold]")
    
    # Add emojis to common option types if they don't already have them
    option_with_emojis = []
    for option in options:
        if "Fiction" in option and "📖" not in option:
            option = f"📖 {option}"
        elif "Non-Fiction" in option and "📚" not in option:
            option = f"📚 {option}"
        elif "Business" in option and "💼" not in option:
            option = f"💼 {option}"
        elif "Research" in option and "🔬" not in option:
            option = f"🔬 {option}"
        elif "Fantasy" in option and "🧙" not in option:
            option = f"🧙 {option}"
        elif "Science Fiction" in option and "🚀" not in option:
            option = f"🚀 {option}"
        elif "Romance" in option and "❤️" not in option:
            option = f"❤️ {option}"
        elif "Thriller" in option and "🔪" not in option:
            option = f"🔪 {option}"
        elif "Mystery" in option and "🔍" not in option:
            option = f"🔍 {option}"
        elif "Horror" in option and "👻" not in option:
            option = f"👻 {option}"
        option_with_emojis.append(option)
    
    if allow_custom:
        option_with_emojis.append("✏️ Custom (enter your own)")
    
    # Use pick to create arrow navigation
    selected_option, index = pick(option_with_emojis, prompt, indicator="→")
    
    # Handle custom option
    if allow_custom and index == len(options):
        console.print("Enter your custom value:")
        custom_value = input("> ")
        return custom_value
    
    # Return the original option without emoji if needed
    original_option = options[index]
    return original_option


def save_project_data():
    """Saves project data (using new method)."""
    project_manager.save_project_data() # Now it's the same


def generate_questions_with_llm(category: str, genre: str) -> Dict[str, Any]:
    """Generates genre-specific questions (same as before, but using LLMClient)."""
    prompt = f"""
    Generate a list of 5-7 KEY questions ... (rest of the prompt)
    """
    llm_client = project_manager.llm_client
    if llm_client is None:
        console.print("[red] LLM is not selected[/red]")
        return {}

    try:
        response = llm_client.generate_content(prompt, max_tokens=500)
        questions = json.loads(response)
        return questions
    except (Exception, json.JSONDecodeError) as e:
        logger.error(f"Error generating questions: {e}")
        print(f"Error generating questions: {e}")
        return {}


# --- Helper functions for Simple Mode ---

def get_project_name_and_title():
    project_name = typer.prompt("📁 Enter a project name (this will be the directory name)")
    title = typer.prompt("📕 What is the title of your book?")
    return project_name, title

def get_category_and_genre(project_knowledge_base: ProjectKnowledgeBase):
    category = select_from_list(
        "📚 What category best describes your book?",
        ["Fiction", "Non-Fiction", "Business", "Research Paper"],
        allow_custom=True,
    )
    project_knowledge_base.set("category", category)

    if category == "Fiction":
        genre_options = ["Fantasy", "Science Fiction", "Romance", "Thriller", "Mystery", "Historical Fiction", "Horror", "Young Adult", "Contemporary"]
    elif category == "Non-Fiction":
        genre_options = ["Biography", "History", "Science", "Self-Help", "Travel", "True Crime", "Cookbook"]
    elif category == "Business":
        genre_options = ["Marketing", "Management", "Finance", "Entrepreneurship", "Leadership", "Sales", "Productivity"]
    elif category == "Research Paper":
        genre = typer.prompt("🔍 Enter the field of study for your research paper")
        project_knowledge_base.set("genre", genre)
        return
    else:
        genre_options = []  # Should not happen, but for safety

    if genre_options:
        genre = select_from_list(f"🏷️ What genre/subject best fits your {category} book?", genre_options, allow_custom=True)
        project_knowledge_base.set("genre", genre)



def get_book_length(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    book_length = select_from_list(
        "📏 How long would you like your book to be?",
        ["Short Story (1-3 chapters)", "Novella (5-8 chapters)", "Novel (15+ chapters)", "Full Book (Non-Fiction)"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

def get_fiction_details(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    if project_knowledge_base.category == "Fiction":
        num_characters = typer.prompt("👥 How many main characters will your story have?", type=int)
        project_knowledge_base.set("num_characters", num_characters)
        worldbuilding_needed = typer.confirm("🌍 Does your story require extensive worldbuilding?")
        project_knowledge_base.set("worldbuilding_needed", worldbuilding_needed)

def get_review_preference(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    review_preference = select_from_list("🔍 How would you like your chapters to be reviewed?", ["Human (you'll review it)", "AI (automatic review)"])
    project_knowledge_base.set("review_preference", review_preference)

def get_description(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    description = typer.prompt("📝 Provide a brief description of your book's concept or plot")
    project_knowledge_base.set("description", description)

def generate_and_review_concept(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    project_manager.generate_concept()
    project_manager.checkpoint() # Checkpoint
    console.print(f"\n[bold cyan]✨ Refined Concept:[/bold cyan]")
    console.print(f"  [bold]Title:[/bold] {project_knowledge_base.title}")
    console.print(f"  [bold]Logline:[/bold] {project_knowledge_base.logline}")
    console.print(f"  [bold]Description:[/bold]\n{project_knowledge_base.description}")
    return typer.confirm("Do you want to proceed with generating an outline based on this concept?")

def generate_and_edit_outline(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    project_manager.generate_outline()
    project_manager.checkpoint()  # Checkpoint after outline
    console.print(f"\n[bold green]📝 Outline generated![/bold green]")

    if typer.confirm("Do you want to review and edit the outline now?"):
        typer.edit(filename=str(project_manager.project_dir / "outline.md"))
        print("\nChanges saved.")


def generate_characters_if_needed(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
     if project_knowledge_base.get("num_characters", 0) > 0:  # Use get with default
        if typer.confirm("Do you want to generate character profiles?"):
            console.print("\n[bold cyan]👥 Generating character profiles...[/bold cyan]")
            project_manager.generate_characters()
            project_manager.checkpoint() # Checkpoint
            console.print(f"\n[bold green]✅ Character profiles generated![/bold green]")

def generate_worldbuilding_if_needed(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    if project_knowledge_base.get("worldbuilding_needed", False):  # Use get with default
        if typer.confirm("Do you want to generate worldbuilding details?"):
            console.print("\n[bold cyan]🏔️ Creating worldbuilding details...[/bold cyan]")
            project_manager.generate_worldbuilding()
            project_manager.checkpoint() # Checkpoint
            console.print(f"\n[bold green]✅ Worldbuilding details generated![/bold green]")

def write_and_review_chapters(project_knowledge_base: ProjectKnowledgeBase):
    """Write and review chapters with better progress tracking and error handling."""
    num_chapters = project_knowledge_base.get("num_chapters", 1)
    if isinstance(num_chapters, tuple):
        num_chapters = num_chapters[1]

    console.print(f"\n[bold]Starting chapter writing process. Total chapters: {num_chapters}[/bold]")

    for i in range(1, num_chapters + 1):
        chapter = project_knowledge_base.get_chapter(i)
        if chapter is None:
            console.print(f"[yellow]WARNING: Chapter {i} not found in outline. Creating basic structure...[/yellow]")
            chapter = Chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                summary="To be written"
            )
            project_knowledge_base.add_chapter(chapter)  # Add to knowledge base!

        console.print(f"\n[bold cyan]Writing Chapter {i}: {chapter.title}[/bold cyan]")

        if project_manager.does_chapter_exist(i):
            if not typer.confirm(f"Chapter {i} already exists. Overwrite?"):
                console.print(f"[yellow]Skipping chapter {i}...[/yellow]")
                continue

        try:
            project_manager.write_and_review_chapter(i)
            project_manager.checkpoint()
            console.print(f"[bold green]✅ Chapter {i} completed successfully[/bold green]")
        except Exception as e:
            console.print(f"[red]ERROR writing chapter {i}: {str(e)}[/red]")
            logger.exception(f"Error writing chapter {i}")
            if not typer.confirm("Continue with next chapter?"):
                break

        if i < num_chapters:
            if not typer.confirm("\nContinue to next chapter?"):
                break

    console.print("\n[bold green]Chapter writing process completed![/bold green]")




def format_book(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    if typer.confirm("Do you want to format the book now?"):
        output_format = select_from_list("Choose output format:", ["Markdown (.md)", "PDF (.pdf)"])
        if output_format == "Markdown (.md)":
            output_path = str(project_manager.project_dir / "manuscript.md")
        else:
            output_path = str(project_manager.project_dir / "manuscript.pdf")
        project_manager.format_book(output_path)
        console.print(f"\n[bold green]📘 Book formatted and saved![/bold green]")


# --- Simple Mode (Refactored) ---
def simple_mode():
    print("\n[bold cyan]✨ Starting Simple Mode...[/bold cyan]\n")

    project_name, title = get_project_name_and_title()
    project_knowledge_base = ProjectKnowledgeBase(project_name=project_name, title=title)

    llm_choice = select_llm(project_knowledge_base)
    project_manager.initialize_llm_client(llm_choice)

    get_category_and_genre(project_knowledge_base)
    get_book_length(project_knowledge_base)
    get_fiction_details(project_knowledge_base)
    get_review_preference(project_knowledge_base)
    get_description(project_knowledge_base)

    project_manager.initialize_project_with_data(project_knowledge_base)

    if generate_and_review_concept(project_knowledge_base):
        generate_and_edit_outline(project_knowledge_base)
        generate_characters_if_needed(project_knowledge_base)
        generate_worldbuilding_if_needed(project_knowledge_base)

        project_manager.checkpoint() 
        # Ensure chapters are written
        num_chapters = project_knowledge_base.get("num_chapters", 1)
        if isinstance(num_chapters, tuple):
            num_chapters = num_chapters[1]

        print(f"\nPreparing to write {num_chapters} chapters...")
        for chapter_num in range(1, num_chapters + 1):
            if not typer.confirm(f"\n📝 Ready to write Chapter {chapter_num}?"):
                break
            project_manager.write_and_review_chapter(chapter_num)
            project_manager.checkpoint()

        # Only format after chapters are written
        if typer.confirm("\nDo you want to format the book now?"):
            format_book(project_knowledge_base)
    else:
        print("Exiting.")
        return

    console.print("\n[bold green]🎉 Book creation process complete![/bold green]")

# --- Helper Functions for Advanced Mode ---

def get_advanced_fiction_details(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
     num_characters_str = typer.prompt(
            "👥 How many main characters do you envision? (e.g., 3, 2-4, 5+)", default="2-3"
        )
     project_knowledge_base.set("num_characters_str",num_characters_str)
     project_knowledge_base.set("num_characters", num_characters_str)

     worldbuilding_needed = typer.confirm("🌍 Does your story need extensive worldbuilding?")
     project_knowledge_base.set("worldbuilding_needed", worldbuilding_needed)

     tone = select_from_list("🎭 What overall tone would you like for your book?", 
                      ["Serious", "Funny", "Romantic", "Informative", "Persuasive"])
     project_knowledge_base.set("tone", tone)

     target_audience = select_from_list("👥 Who is your target audience?", 
                              ["Children", "Teens", "Young Adult", "Adults"])
     project_knowledge_base.set("target_audience", target_audience)

     book_length = select_from_list(
         "📏 How long will your book be?",
         ["Short Story ", "Novella", "Novel ", "Full Book"],
         allow_custom=False,
     )
     project_knowledge_base.set("book_length",book_length)

     num_chapters_str = typer.prompt(
        "📑 Approximately how many chapters do you want? (e.g., 10, 8-12, 20+)",
        default="8-12",)
     project_knowledge_base.set("num_chapters_str", num_chapters_str)
     project_knowledge_base.set("num_chapters", num_chapters_str)
     inspired_by = typer.prompt("✨ Are there any authors, books, or series that inspire you? (Optional)")
     project_knowledge_base.set("inspired_by",inspired_by)

def get_advanced_nonfiction_details(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    project_knowledge_base.set("num_characters", 0)
    project_knowledge_base.set("num_chapters",0)
    project_knowledge_base.set("worldbuilding_needed",False)

    tone = select_from_list("🎭 What tone would you like for your non-fiction book?", 
                    ["Serious", "Funny", "Romantic", "Informative", "Persuasive"])
    project_knowledge_base.set("tone", tone)

    target_audience = select_from_list(
        "👥 Who is your target audience?",
        ["Children", "Teens", "Young Adult", "Adults", "Professional/Expert"],
    )
    project_knowledge_base.set("target_audience", target_audience)

    book_length = select_from_list(
        "Select the desired book length:",
        ["Article", "Essay", "Full Book"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

    author_experience = typer.prompt("🧠 What is your experience or expertise in this subject?")
    project_knowledge_base.set("author_experience",author_experience)

def get_advanced_business_details(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    project_knowledge_base.set("num_characters",0)
    project_knowledge_base.set("num_chapters",0)
    project_knowledge_base.set("worldbuilding_needed",False)

    tone = select_from_list("Select Tone", ["Informative", "Motivational", "Instructive"])
    project_knowledge_base.set("tone", tone)

    target_audience = select_from_list(
        "👥 Select Target Audience",
        [
            "Entrepreneurs",
            "Managers",
            "Employees",
            "Students",
            "General Business Readers",
        ],
    )
    project_knowledge_base.set("target_audience", target_audience)

    book_length = select_from_list(
        "📏 Select the desired book length:",
        ["Pamphlet", "Guidebook", "Full Book"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

    key_takeaways = typer.prompt("What are the key takeaways you want readers to gain?")
    project_knowledge_base.set("key_takeaways",key_takeaways)

    case_studies = typer.confirm("Will you include case studies?")
    project_knowledge_base.set("case_studies", case_studies)

    actionable_advice = typer.confirm("Will you provide actionable advice/exercises?")
    project_knowledge_base.set("actionable_advice",actionable_advice)

    if project_knowledge_base.get("genre") == "Marketing":
        marketing_focus = select_from_list(
            "✨ What is the primary focus of your marketing book?",
            [
                "SEO",
                "Performance Marketing",
                "Data Analytics",
                "Offline Marketing",
                "Content Marketing",
                "Social Media Marketing",
                "Branding",
            ],
            allow_custom=True,
        )
        project_knowledge_base.set("marketing_focus",marketing_focus)

    elif project_knowledge_base.get("genre") == "Sales":
        sales_focus = select_from_list(
            "✨  What is the primary focus of your sales book?",
            [
                "Sales Techniques",
                "Pitching",
                "Negotiation",
                "Building Relationships",
                "Sales Management",
            ],
            allow_custom=True,
        )
        project_knowledge_base.set("sales_focus", sales_focus)

def get_advanced_research_details(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    project_knowledge_base.set("num_characters",0)
    project_knowledge_base.set("num_chapters",0)
    project_knowledge_base.set("worldbuilding_needed",False)
    project_knowledge_base.set("tone","Formal and Objective")

    target_audience = select_from_list(
        "👥 Select Target Audience",
        ["Academic Community", "Researchers", "Students", "General Public (if applicable)"],
    )
    project_knowledge_base.set("target_audience", target_audience)

    project_knowledge_base.set("book_length","Academic Article")

    research_question = typer.prompt("What is your primary research question?")
    project_knowledge_base.set("research_question",research_question)

    hypothesis = typer.prompt("What is your hypothesis (if applicable)?")
    project_knowledge_base.set("hypothesis", hypothesis)

    methodology = select_from_list(
        "🔍  Select your research methodology:",
        ["Quantitative", "Qualitative", "Mixed Methods"],
        allow_custom=True,
    )
    project_knowledge_base.set("methodology", methodology)

def get_dynamic_questions(project_knowledge_base: ProjectKnowledgeBase): #MODIFIED
    print("\nNow, let's dive into some genre-specific questions...")
    dynamic_questions = generate_questions_with_llm(project_knowledge_base.get("category"), project_knowledge_base.get("genre"))

    for q_id, question in dynamic_questions.items():
        answer = typer.prompt(question)
        project_knowledge_base.dynamic_questions[q_id] = answer
        save_project_data()

# --- Advanced Mode (Refactored) ---

def advanced_mode():
    console.print("\n[bold cyan]✨ Starting Advanced Mode...[/bold cyan]\n")

    project_name, title = get_project_name_and_title()
    project_knowledge_base = ProjectKnowledgeBase(project_name=project_name, title=title) #MODIFIED
    #LLM selection
    llm_choice = select_llm(project_knowledge_base) #MODIFIED
    project_manager.initialize_llm_client(llm_choice)

    get_category_and_genre(project_knowledge_base) #MODIFIED

    if project_knowledge_base.get("category") == "Fiction":
        get_advanced_fiction_details(project_knowledge_base) #MODIFIED
    elif project_knowledge_base.get("category") == "Non-Fiction":
        get_advanced_nonfiction_details(project_knowledge_base) #MODIFIED
    elif project_knowledge_base.get("category") == "Business":
        get_advanced_business_details(project_knowledge_base) #MODIFIED
    elif project_knowledge_base.get("category") == "Research Paper":
        get_advanced_research_details(project_knowledge_base) #MODIFIED

    get_review_preference(project_knowledge_base) #MODIFIED
    get_description(project_knowledge_base) #MODIFIED

    project_manager.initialize_project_with_data(project_knowledge_base)  # Initialize #MODIFIED

    get_dynamic_questions(project_knowledge_base) #MODIFIED

    if generate_and_review_concept(project_knowledge_base): #MODIFIED
        generate_and_edit_outline(project_knowledge_base) #MODIFIED
        generate_characters_if_needed(project_knowledge_base) #MODIFIED
        generate_worldbuilding_if_needed(project_knowledge_base) #MODIFIED
        write_and_review_chapters(project_knowledge_base)
        format_book(project_knowledge_base)
    else:
        print("Exiting.")
        return

    print("\nBook creation process complete (Advanced Mode).")


@app.command()
def start():
    """Starts the interactive book creation process."""
    introduction()
    mode = select_from_list("✨ Choose your creation mode:", ["Simple (guided process)", "Advanced (more options)"])
    if mode == "Simple":
        simple_mode()
    elif mode == "Advanced":
        advanced_mode()


# Removed the create command

@app.command()
def outline():
    """Generates a book outline."""
    project_manager.generate_outline()

@app.command()
def characters():
    """Generates character profiles."""
    project_manager.generate_characters()

@app.command()
def worldbuilding():
    """Generates worldbuilding details."""
    project_manager.generate_worldbuilding()

@app.command()
def write(chapter_number: int = typer.Option(..., prompt="Chapter number")):
    """Writes a specific chapter, with review process."""
    logger.info(f"📝 Agent {project_manager.agents['chapter_writer'].name} writing chapter {chapter_number}...") # type: ignore
    project_manager.write_and_review_chapter(chapter_number)
    logger.info(f"✅ Chapter {chapter_number} complete.")



@app.command()
def edit(chapter_number: int = typer.Option(..., prompt="Chapter number to edit")):
    """Edits and refines a specific chapter"""
    project_manager.edit_chapter(chapter_number)


@app.command()
def format():
    """Formats the entire book into a single Markdown or PDF file."""
    output_format = select_from_list("Choose output format:", ["Markdown (.md)", "PDF (.pdf)"])
    if output_format == "Markdown (.md)":
        output_path = str(project_manager.project_dir / "manuscript.md")
    else:
        output_path = str(project_manager.project_dir / "manuscript.pdf")
    project_manager.format_book(output_path)  # Pass output_path here
    print(f"\nBook formatted and saved to: {output_path}")

@app.command()
def research(query: str = typer.Option(..., prompt="Research query")):
    """Performs web research on a given query."""
    project_manager.research(query)

@app.command()
def resume(project_name: str = typer.Option(..., prompt="Project name to resume")):
    """Resumes a project from the last checkpoint."""
    try:
        project_manager.load_project_data(project_name)
        print(f"Project '{project_name}' loaded. Resuming...")

        # Determine where to resume from.  This logic is simplified for now
        # and assumes you'll mostly resume chapter writing. A more robust
        # solution would inspect more files.

        if not project_manager.project_knowledge_base: #MODIFIED
            print("ERROR resuming project")
            return

        if project_manager.project_dir and (project_manager.project_dir / "outline.md").exists():
            # Find the last written chapter
            last_chapter = 0
            num_chapters = project_manager.project_knowledge_base.get("num_chapters",1) #MODIFIED
            if isinstance(num_chapters, tuple):
                num_chapters = num_chapters[1]

            for i in range(1, num_chapters + 1):  # Iterate in order
                if (project_manager.project_dir / f"chapter_{i}.md").exists():
                    last_chapter = i
                else:
                    break  # Stop at the first missing chapter

            print(f"Last written chapter: {last_chapter}")

            # Check the project data and files to determine next steps
            for i in range(last_chapter + 1, num_chapters + 1):
                 project_manager.write_and_review_chapter(i)
            if typer.confirm("Do you want to format now the book?"):
                format()

        elif project_manager.project_knowledge_base:  # Project data exists, but no outline #MODIFIED
            # Resume from outline generation (this is a simplification)
            print("Resuming from outline generation...")
            project_manager.generate_outline()
            # ... (rest of the logic, similar to simple/advanced mode)

        else:
            print("No checkpoint found to resume from.")


    except FileNotFoundError:
        print(f"Project '{project_name}' not found.")
    except ValueError as e:
        print(f"Error loading project data: {e}")



if __name__ == "__main__":
    app()