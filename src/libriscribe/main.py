# src/libriscribe/main.py
import json
import logging
import os
import sys
import warnings
from importlib.metadata import version as package_version
from typing import cast

import typer
from pydantic import PydanticDeprecationWarning
from rich.console import Console
from rich.panel import Panel

from libriscribe.agents.project_manager import ProjectManagerAgent
from libriscribe.configuration import (
    ApprovalMode,
    ErrorMode,
    ExpertConfig,
    OutputFormat,
    StageMode,
    build_project_knowledge_base,
    load_expert_config,
    load_recent_expert_config,
    save_recent_expert_config,
)
from libriscribe.knowledge_base import (  # Import the new class
    Chapter,
    ProjectKnowledgeBase,
)
from libriscribe.settings import Settings
from libriscribe.utils.editor import open_file_in_editor
from libriscribe.utils.model_routing import parse_fallback_chain_string
from libriscribe.workflow_state import ProjectProgress, inspect_project_progress

warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)

# Configure logging (same as before)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler("libriscribe.log", encoding="utf-8"),  # Add encoding
        logging.StreamHandler(),  # Simplified logs to console
    ],
)
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(logging.Formatter("%(message)s"))
        stream = handler.stream
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(errors="replace")

console = Console()
app = typer.Typer()
# project_manager = ProjectManagerAgent()  # Initialize ProjectManager
project_manager = ProjectManagerAgent(llm_client=None)
logger = logging.getLogger(__name__)

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "claude": "Claude",
    "google_ai_studio": "Google AI Studio",
    "deepseek": "DeepSeek",
    "mistral": "Mistral",
    "openrouter": "OpenRouter",
}

AGENT_MODEL_OPTIONS = [
    ("concept_generator", "Concept Generator"),
    ("outliner", "Outliner"),
    ("character_generator", "Character Generator"),
    ("worldbuilding", "Worldbuilding"),
    ("chapter_writer", "Chapter Writer"),
    ("content_reviewer", "Content Reviewer"),
    ("editor", "Editor"),
    ("style_editor", "Style Editor"),
    ("researcher", "Researcher"),
    ("formatting", "Formatting"),
]


def get_default_model_for_provider(
    provider: str, settings: Settings | None = None
) -> str:
    settings = settings or Settings()
    return {
        "openai": settings.openai_model,
        "claude": settings.claude_model,
        "google_ai_studio": settings.google_ai_studio_model,
        "deepseek": settings.deepseek_model,
        "mistral": settings.mistral_model,
        "openrouter": settings.openrouter_model,
    }.get(provider, "")


def get_available_llm_providers(settings: Settings | None = None) -> list[str]:
    settings = settings or Settings()
    available_llms: list[str] = []

    if settings.openrouter_api_key:
        available_llms.append("openrouter")
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

    return available_llms


def _prompt_text(text: str, default: str | None = None) -> str:
    if default is None:
        return cast(str, typer.prompt(text))
    return cast(str, typer.prompt(text, default=default))


def _prompt_int(text: str, default: int | None = None) -> int:
    if default is None:
        return cast(int, typer.prompt(text, type=int))
    return cast(int, typer.prompt(text, type=int, default=default))


def select_llm(project_knowledge_base: ProjectKnowledgeBase) -> str:
    """Lets the user select an LLM provider and applies the provider default model."""
    settings = Settings()
    available_llms = get_available_llm_providers(settings)

    if not available_llms:
        console.print(
            "[red]❌ No LLM API keys found in .env file. Please add at least one.[/red]"
        )
        raise typer.Exit(code=1)

    provider_options = [
        f"{PROVIDER_LABELS.get(provider, provider)} (default: {get_default_model_for_provider(provider, settings)})"
        for provider in available_llms
    ]
    option_to_provider: dict[str, str] = dict(zip(provider_options, available_llms))

    console.print("")
    selected_option = select_from_list(
        "🤖 Select your preferred AI provider:", provider_options
    )
    llm_choice = option_to_provider[selected_option]

    project_knowledge_base.set("llm_provider", llm_choice)
    project_knowledge_base.set(
        "model", get_default_model_for_provider(llm_choice, settings)
    )
    return llm_choice


def configure_advanced_model(project_knowledge_base: ProjectKnowledgeBase) -> str:
    """Lets advanced users keep the .env default model or enter a custom one."""
    provider = project_knowledge_base.llm_provider
    if not provider:
        return ""

    default_model = get_default_model_for_provider(provider)
    console.print("")
    choice = select_from_list(
        f"🧠 Which {PROVIDER_LABELS.get(provider, provider)} model would you like to use?",
        [f"Use default from .env ({default_model})", "Enter custom model ID"],
    )

    if choice == "Enter custom model ID":
        custom_model = _prompt_text("Enter the model ID")
        project_knowledge_base.set("model", custom_model)
        return custom_model

    project_knowledge_base.set("model", default_model)
    return default_model


def _prompt_fallback_chain_input(prompt_text: str) -> list[str]:
    console.print(
        "[dim]Examples: claude | openrouter/anthropic/claude-3-haiku | gpt-4o[/dim]"
    )
    raw_value = _prompt_text(prompt_text, default="").strip()
    return parse_fallback_chain_string(raw_value)


def configure_advanced_fallbacks(project_knowledge_base: ProjectKnowledgeBase) -> None:
    provider = project_knowledge_base.llm_provider
    if not provider:
        return

    console.print("")
    if not typer.confirm(
        "🛟 Do you want to configure fallback models for recoverable failures?",
        default=False,
    ):
        project_knowledge_base.set("fallback_chain", [])
        project_knowledge_base.set("agent_fallback_chains", {})
        return

    console.print(
        "[dim]Fallbacks are used for timeouts, rate limits, provider 5xx errors, empty responses, and unrecoverable JSON output.[/dim]"
    )
    console.print(
        f"[dim]Current provider: {provider}. Leave blank to keep no project-wide fallback chain.[/dim]"
    )
    console.print("")
    project_knowledge_base.set(
        "fallback_chain",
        _prompt_fallback_chain_input("Project fallback chain (comma-separated)"),
    )

    agent_fallback_chains: dict[str, list[str]] = {}
    console.print("")
    if typer.confirm(
        "Would you like to configure per-agent fallback chains too?", default=False
    ):
        remaining_agents = [label for _, label in AGENT_MODEL_OPTIONS]
        label_to_agent = {
            label: agent_name for agent_name, label in AGENT_MODEL_OPTIONS
        }

        while remaining_agents:
            choice = select_from_list(
                "Select an agent to configure a fallback chain for:",
                [*remaining_agents, "Done"],
            )
            if choice == "Done":
                break

            agent_name = label_to_agent[choice]
            console.print("")
            chain = _prompt_fallback_chain_input(
                f"Fallback chain for {choice} (comma-separated)"
            )
            if chain:
                agent_fallback_chains[agent_name] = chain
            remaining_agents = [label for label in remaining_agents if label != choice]
            console.print("")
            if not remaining_agents or not typer.confirm(
                "Configure another per-agent fallback chain?", default=False
            ):
                break

    project_knowledge_base.set("agent_fallback_chains", agent_fallback_chains)


def introduction():
    """Prints a welcome message."""

    console.print("")
    console.print("")
    console.print("")
    console.print(
        Panel(
            "Welcome to [bold]Libriscribe[/bold]! ✨\n\n"
            "An AI-powered, open-source book creation system crafted by Fernando Guerra.\n\n"
            "🚀  Ready to write your next masterpiece?\n\n"
            "⭐ If you find Libriscribe helpful, please consider supporting the project by giving it a star on GitHub:\n[link]https://github.com/guerra2fernando/libriscribe[/link]\n"
            "Your support helps keep this project going!",
            title="[bold blue]Libriscribe[/bold blue]",
            border_style="blue",
            padding=(1, 2),  # Add some padding for better visual appearance
        )
    )
    # Print emojis separately to avoid formatting issues (Optional in this case)
    console.print("")
    console.print("")
    # Print emojis separately to avoid formatting issues
    console.print("Let's create something amazing! \n")


def select_from_list(
    prompt: str, options: list[str], allow_custom: bool = False
) -> str:
    """Presents options and returns selection with improved formatting."""
    console.print(f"[bold]{prompt}[/bold]")

    # Display options with numbers
    for i, option in enumerate(options):
        console.print(f"[cyan]{i + 1}.[/cyan] {option}")

    if allow_custom:
        console.print(f"[cyan]{len(options) + 1}.[/cyan]Custom (enter your own)")

    # Get user selection with error handling
    while True:
        try:
            choice = _prompt_text("Enter your choice")
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(options):
                return options[choice_idx]  # Return original option without emoji
            elif allow_custom and choice_idx == len(options):
                custom_value = _prompt_text("Enter your custom value")
                return custom_value
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")


def save_project_data():
    """Saves project data (using new method)."""
    project_manager.save_project_data()  # Now it's the same


def generate_questions_with_llm(category: str, genre: str) -> dict[str, str]:
    """Generates genre-specific questions with improved error handling."""
    prompt = f"""
    Generate a list of 5-7 KEY questions that would help develop a {category} {genre} book.
    Format your response as a JSON object where keys are question IDs and values are the questions.

    For example:
    {{
        "q1": "What is the central conflict of your story?",
        "q2": "Who is the main antagonist?",
        "q3": "What is the world's primary magic system?"
    }}

    Return ONLY valid JSON, nothing else.
    """

    llm_client = project_manager.llm_client
    if llm_client is None:
        console.print("[red]LLM is not selected[/red]")
        return {}

    try:
        response = llm_client.generate_content(prompt, max_tokens=500)

        # Clean the response - find JSON content
        response = response.strip()
        # Look for JSON between curly braces if there's other text
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response

        try:
            questions = json.loads(json_str)
            if isinstance(questions, dict):
                return {str(key): str(value) for key, value in questions.items()}
            raise json.JSONDecodeError("Expected object", json_str, 0)
        except json.JSONDecodeError:
            # If it fails, create a minimal set of questions as fallback
            console.print(
                "[yellow]Could not parse LLM response. Using default questions.[/yellow]"
            )
            return {
                "q1": f"What key themes do you want to explore in your {genre} story?",
                "q2": "Who is your favorite character and why?",
                "q3": "What makes your story unique compared to similar works?",
            }
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        console.print(
            "[yellow]Error generating custom questions. Using defaults.[/yellow]"
        )
        return {
            "q1": f"What key themes do you want to explore in your {genre} story?",
            "q2": "Who is your favorite character and why?",
            "q3": "What makes your story unique compared to similar works?",
        }


# --- Helper functions for Simple Mode ---


def get_project_name_and_title() -> tuple[str, str]:
    console.print("")
    project_name = _prompt_text(
        "📁 Enter a project name (this will be the directory name)"
    )
    console.print("")
    title = _prompt_text("📕 What is the title of your book?")
    return project_name, title


def get_category_and_genre(project_knowledge_base: ProjectKnowledgeBase):
    console.print("")
    category = select_from_list(
        "📚 What category best describes your book?",
        ["Fiction", "Non-Fiction", "Business", "Research Paper"],
        allow_custom=True,
    )
    project_knowledge_base.set("category", category)

    if category == "Fiction":
        genre_options = [
            "Fantasy",
            "Science Fiction",
            "Romance",
            "Thriller",
            "Mystery",
            "Historical Fiction",
            "Horror",
            "Young Adult",
            "Contemporary",
        ]
    elif category == "Non-Fiction":
        genre_options = [
            "Biography",
            "History",
            "Science",
            "Self-Help",
            "Travel",
            "True Crime",
            "Cookbook",
        ]
    elif category == "Business":
        genre_options = [
            "Marketing",
            "Management",
            "Finance",
            "Entrepreneurship",
            "Leadership",
            "Sales",
            "Productivity",
        ]
    elif category == "Research Paper":
        genre = _prompt_text("🔍 Enter the field of study for your research paper")
        project_knowledge_base.set("genre", genre)
        return
    else:
        genre_options = []  # Should not happen, but for safety

    if genre_options:
        console.print("")
        genre = select_from_list(
            f"🏷️ What genre/subject best fits your {category} book?",
            genre_options,
            allow_custom=True,
        )
        project_knowledge_base.set("genre", genre)


def get_book_length(project_knowledge_base: ProjectKnowledgeBase):
    console.print("")
    book_length = select_from_list(
        "📏 How long would you like your book to be?",
        [
            "Short Story (1-3 chapters)",
            "Novella (5-8 chapters)",
            "Novel (15+ chapters)",
            "Full Book (Non-Fiction)",
        ],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)


def get_fiction_details(project_knowledge_base: ProjectKnowledgeBase):
    if project_knowledge_base.category == "Fiction":
        console.print("")
        num_characters = _prompt_int(
            "👥 How many main characters will your story have?"
        )
        project_knowledge_base.set("num_characters", num_characters)
        console.print("")
        worldbuilding_needed = typer.confirm(
            "🌍 Does your story require extensive worldbuilding?"
        )
        project_knowledge_base.set("worldbuilding_needed", worldbuilding_needed)


def get_review_preference(project_knowledge_base: ProjectKnowledgeBase):
    console.print("")
    review_preference = select_from_list(
        "🔍 How would you like your chapters to be reviewed?",
        ["Human (you'll review it)", "AI (automatic review)"],
    )
    if review_preference.startswith("Human"):
        project_knowledge_base.set("review_preference", "Human")
    else:
        project_knowledge_base.set("review_preference", "AI")


def get_description(project_knowledge_base: ProjectKnowledgeBase):
    console.print("")
    description = _prompt_text(
        "📝 Provide a brief description of your book's concept or plot"
    )
    project_knowledge_base.set("description", description)


def generate_and_review_concept(
    project_knowledge_base: ProjectKnowledgeBase,
    approval_mode: ApprovalMode = ApprovalMode.PROMPT,
):
    project_manager.generate_concept()
    project_manager.checkpoint()  # Checkpoint
    console.print("")
    console.print("\n[cyan]✨ Refined Concept:[/cyan]")
    console.print(f"  [bold]Title:[/bold] {project_knowledge_base.title}")
    console.print(f"  [bold]Logline:[/bold] {project_knowledge_base.logline}")
    console.print(f"  [bold]Description:[/bold]\n{project_knowledge_base.description}")
    if approval_mode == ApprovalMode.PROMPT:
        return typer.confirm(
            "Do you want to proceed with generating an outline based on this concept?"
        )
    return True


def generate_and_edit_outline(
    project_knowledge_base: ProjectKnowledgeBase,
    review_mode: ApprovalMode = ApprovalMode.PROMPT,
):
    project_manager.generate_outline()
    project_manager.checkpoint()  # Checkpoint after outline
    console.print("")
    console.print("\n[green]📝 Outline generated![/green]")

    if not project_manager.project_dir:
        return

    if review_mode == ApprovalMode.PROMPT and typer.confirm(
        "Do you want to review and edit the outline now?"
    ):
        open_file_in_editor(str(project_manager.project_dir / "outline.md"))
        print("\nOpened outline for editing.")


def generate_characters_if_needed(
    project_knowledge_base: ProjectKnowledgeBase, mode: StageMode = StageMode.PROMPT
):
    num_characters = project_knowledge_base.num_characters
    if isinstance(num_characters, tuple):
        num_characters = num_characters[1]

    if num_characters > 0 and mode != StageMode.SKIP:
        console.print("")
        if mode == StageMode.AUTO or typer.confirm(
            "Do you want to generate character profiles?"
        ):
            console.print("\n[cyan]👥 Generating character profiles...[/cyan]")
            project_manager.generate_characters()
            project_manager.checkpoint()  # Checkpoint
            console.print("")
            console.print("\n[green]✅ Character profiles generated![/green]")


def generate_worldbuilding_if_needed(
    project_knowledge_base: ProjectKnowledgeBase, mode: StageMode = StageMode.PROMPT
):
    if project_knowledge_base.worldbuilding_needed and mode != StageMode.SKIP:
        console.print("")
        if mode == StageMode.AUTO or typer.confirm(
            "Do you want to generate worldbuilding details?"
        ):
            console.print("\n[cyan]🏔️ Creating worldbuilding details...[/cyan]")
            project_manager.generate_worldbuilding()
            project_manager.checkpoint()  # Checkpoint
            console.print("")
            console.print("\n[green]✅ Worldbuilding details generated![/green]")


def confirm_full_book_run(
    project_knowledge_base: ProjectKnowledgeBase,
    num_chapters: int,
    error_mode: ErrorMode,
) -> bool:
    provider = project_knowledge_base.llm_provider or "unknown"
    model = project_knowledge_base.model or get_default_model_for_provider(provider)
    review_preference = project_knowledge_base.review_preference

    console.print("")
    console.print("[bold yellow]⚠️ Full-book automatic writing[/bold yellow]")
    console.print(
        f"Provider: [cyan]{provider}[/cyan] | Model: [cyan]{model}[/cyan] | Review: [cyan]{review_preference}[/cyan]"
    )
    console.print(
        f"This will write {num_chapters} chapters without pausing between chapters."
    )
    console.print(
        "[yellow]Warning:[/yellow] this may consume a large number of tokens / credits, especially for longer books."
    )
    console.print(
        f"If a chapter fails, LibriScribe will [bold]{error_mode.value}[/bold]."
    )
    return typer.confirm("Continue with full-book automatic writing?")


def configure_chapter_writing_flow(
    project_knowledge_base: ProjectKnowledgeBase, advanced: bool = False
):
    """Configures whether chapter writing pauses between chapters and how errors are handled."""
    review_preference = project_knowledge_base.review_preference
    project_knowledge_base.set("chapter_writing_mode", "prompt")
    project_knowledge_base.set("chapter_error_mode", "stop")

    if review_preference != "AI":
        console.print("")
        console.print(
            "[yellow]Manual chapter review is enabled, so LibriScribe will keep prompting as you move through chapters.[/yellow]"
        )
        return

    console.print("")
    chapter_mode = select_from_list(
        "📝 How should chapter writing proceed?",
        ["Pause before each chapter", "Write the whole book automatically"],
    )

    if chapter_mode == "Write the whole book automatically":
        project_knowledge_base.set("chapter_writing_mode", "auto")
        if advanced:
            console.print("")
            error_mode = select_from_list(
                "🚨 If a chapter fails, what should LibriScribe do?",
                ["Stop on the first error", "Continue to the next chapter"],
            )
            project_knowledge_base.set(
                "chapter_error_mode",
                "continue" if error_mode == "Continue to the next chapter" else "stop",
            )


def write_and_review_chapters(
    project_knowledge_base: ProjectKnowledgeBase,
    progression_mode: StageMode = StageMode.PROMPT,
    error_mode: ErrorMode = ErrorMode.STOP,
):
    """Write and review chapters with configurable progression and error handling."""
    num_chapters = project_knowledge_base.num_chapters
    if isinstance(num_chapters, tuple):
        num_chapters = num_chapters[1]

    existing_chapters = [
        chapter_number
        for chapter_number in range(1, num_chapters + 1)
        if project_manager.does_chapter_exist(chapter_number)
    ]
    missing_chapters = [
        chapter_number
        for chapter_number in range(1, num_chapters + 1)
        if chapter_number not in existing_chapters
    ]

    console.print(
        f"\n[bold]Starting chapter writing process. Total chapters: {num_chapters}[/bold]"
    )
    if existing_chapters:
        console.print(
            f"[blue]Found existing chapters that will be preserved and skipped: {existing_chapters}[/blue]"
        )
    if not missing_chapters:
        console.print(
            "[green]All chapters already exist. Nothing to resume here.[/green]"
        )
        return

    auto_progression = progression_mode == StageMode.AUTO

    if auto_progression:
        if not confirm_full_book_run(
            project_knowledge_base, len(missing_chapters), error_mode
        ):
            return

    for i in range(1, num_chapters + 1):
        chapter = project_knowledge_base.get_chapter(i)
        if chapter is None:
            console.print(
                f"[yellow]WARNING: Chapter {i} not found in outline. Creating basic structure...[/yellow]"
            )
            chapter = Chapter(
                chapter_number=i, title=f"Chapter {i}", summary="To be written"
            )
            project_knowledge_base.add_chapter(chapter)

        if project_manager.does_chapter_exist(i):
            console.print(
                f"[blue]Skipping existing Chapter {i}: {chapter.title or f'Chapter {i}'}[/blue]"
            )
            continue

        if not auto_progression and not typer.confirm(
            f"\n📝 Ready to write Chapter {i}: {chapter.title}?"
        ):
            break

        console.print(f"\n[cyan]Writing Chapter {i}: {chapter.title}[/cyan]")

        try:
            project_manager.write_and_review_chapter(i)
            project_manager.checkpoint()
            console.print("")
            console.print(f"[green]✅ Chapter {i} completed successfully[/green]")
        except Exception as e:
            console.print(f"[red]ERROR writing chapter {i}: {str(e)}[/red]")
            logger.exception(f"Error writing chapter {i}")
            if error_mode == ErrorMode.CONTINUE:
                console.print("[yellow]Continuing to the next chapter...[/yellow]")
                continue
            break

    console.print("\n[green]Chapter writing process completed![/green]")


def format_book(
    project_knowledge_base: ProjectKnowledgeBase,
    mode: StageMode = StageMode.PROMPT,
    output_format: OutputFormat = OutputFormat.MARKDOWN,
):
    console.print("")
    if mode == StageMode.SKIP:
        return

    should_format = mode == StageMode.AUTO or typer.confirm(
        "Do you want to format the book now?"
    )
    if should_format:
        if not project_manager.project_dir:
            console.print("[red]ERROR: Project directory not initialized.[/red]")
            return

        if mode == StageMode.PROMPT:
            selected_output = select_from_list(
                "Choose output format:", ["Markdown (.md)", "PDF (.pdf)"]
            )
            output_format = (
                OutputFormat.MARKDOWN
                if selected_output == "Markdown (.md)"
                else OutputFormat.PDF
            )

        if output_format == OutputFormat.MARKDOWN:
            output_path = str(project_manager.project_dir / "manuscript.md")
        else:
            output_path = str(project_manager.project_dir / "manuscript.pdf")
        project_manager.format_book(output_path)
        console.print("")
        console.print("\n[green]📘 Book formatted and saved![/green]")


# --- Simple Mode (Refactored) ---
def simple_mode():
    console.print("\n[cyan]✨ Starting Simple Mode...[/cyan]\n")

    project_name, title = get_project_name_and_title()
    project_knowledge_base = ProjectKnowledgeBase(
        project_name=project_name, title=title
    )

    # Add language selection right after project name and title
    select_language(project_knowledge_base)

    llm_choice = select_llm(project_knowledge_base)
    project_manager.initialize_llm_client(llm_choice, project_knowledge_base.model)

    get_category_and_genre(project_knowledge_base)
    get_book_length(project_knowledge_base)
    get_fiction_details(project_knowledge_base)
    get_review_preference(project_knowledge_base)
    configure_chapter_writing_flow(project_knowledge_base)
    get_description(project_knowledge_base)

    project_manager.initialize_project_with_data(project_knowledge_base)

    if generate_and_review_concept(project_knowledge_base):
        generate_and_edit_outline(project_knowledge_base)
        generate_characters_if_needed(project_knowledge_base)
        generate_worldbuilding_if_needed(project_knowledge_base)

        project_manager.checkpoint()

        write_and_review_chapters(
            project_knowledge_base,
            progression_mode=StageMode.AUTO
            if project_knowledge_base.chapter_writing_mode == "auto"
            else StageMode.PROMPT,
            error_mode=ErrorMode.STOP,
        )

        # Only format after chapters are written
        if typer.confirm("\nDo you want to format the book now?"):
            format_book(project_knowledge_base)
    else:
        print("Exiting.")
        return

    console.print("\n[green]🎉 Book creation process complete![/green]")


# --- Helper Functions for Advanced Mode ---


def get_advanced_fiction_details(project_knowledge_base: ProjectKnowledgeBase):
    """Gets detailed information for fiction projects with proper type conversion."""
    console.print("")
    num_characters_str = _prompt_text(
        "👥 How many main characters do you envision? (e.g., 3, 2-4, 5+)",
        default="2-3",
    )
    project_knowledge_base.set("num_characters_str", num_characters_str)

    # Convert to appropriate type
    if "-" in num_characters_str:
        try:
            min_val, max_val = map(int, num_characters_str.split("-"))
            project_knowledge_base.set("num_characters", (min_val, max_val))
        except ValueError:
            # Fallback if conversion fails
            project_knowledge_base.set("num_characters", (2, 3))
    elif "+" in num_characters_str:
        try:
            base_val = int(num_characters_str.replace("+", ""))
            project_knowledge_base.set("num_characters", base_val)
        except ValueError:
            project_knowledge_base.set("num_characters", 3)
    else:
        try:
            project_knowledge_base.set("num_characters", int(num_characters_str))
        except ValueError:
            # Fallback if conversion fails
            project_knowledge_base.set("num_characters", 3)

    console.print("")
    worldbuilding_needed = typer.confirm(
        "🌍 Does your story need extensive worldbuilding?"
    )
    project_knowledge_base.set("worldbuilding_needed", worldbuilding_needed)

    console.print("")
    tone = select_from_list(
        "🎭 What overall tone would you like for your book?",
        ["Serious", "Funny", "Romantic", "Informative", "Persuasive"],
    )

    project_knowledge_base.set("tone", tone)

    console.print("")
    target_audience = select_from_list(
        "👥 Who is your target audience?",
        ["Children", "Teens", "Young Adult", "Adults"],
    )
    project_knowledge_base.set("target_audience", target_audience)

    console.print("")
    book_length = select_from_list(
        "📏 How long will your book be?",
        ["Short Story", "Novella", "Novel", "Full Book"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

    console.print("")
    num_chapters_str = _prompt_text(
        "📑 Approximately how many chapters do you want? (e.g., 10, 8-12, 20+)",
        default="8-12",
    )
    project_knowledge_base.set("num_chapters_str", num_chapters_str)

    # Convert to appropriate type
    if "-" in num_chapters_str:
        try:
            min_val, max_val = map(int, num_chapters_str.split("-"))
            project_knowledge_base.set("num_chapters", (min_val, max_val))
        except ValueError:
            # Fallback if conversion fails
            project_knowledge_base.set("num_chapters", (8, 12))
    elif "+" in num_chapters_str:
        try:
            base_val = int(num_chapters_str.replace("+", ""))
            project_knowledge_base.set("num_chapters", base_val)
        except ValueError:
            project_knowledge_base.set("num_chapters", 12)
    else:
        try:
            project_knowledge_base.set("num_chapters", int(num_chapters_str))
        except ValueError:
            # Fallback if conversion fails
            project_knowledge_base.set("num_chapters", 10)

    inspired_by = _prompt_text(
        "✨ Are there any authors, books, or series that inspire you? (Optional)"
    )
    project_knowledge_base.set("inspired_by", inspired_by)


def get_advanced_nonfiction_details(project_knowledge_base: ProjectKnowledgeBase):
    project_knowledge_base.set("num_characters", 0)
    project_knowledge_base.set("num_chapters", 0)
    project_knowledge_base.set("worldbuilding_needed", False)

    console.print("")
    tone = select_from_list(
        "🎭 What tone would you like for your non-fiction book?",
        ["Serious", "Funny", "Romantic", "Informative", "Persuasive"],
    )
    project_knowledge_base.set("tone", tone)

    console.print("")
    target_audience = select_from_list(
        "👥 Who is your target audience?",
        ["Children", "Teens", "Young Adult", "Adults", "Professional/Expert"],
    )
    project_knowledge_base.set("target_audience", target_audience)

    console.print("")
    book_length = select_from_list(
        "Select the desired book length:",
        ["Article", "Essay", "Full Book"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

    console.print("")
    author_experience = _prompt_text(
        "🧠 What is your experience or expertise in this subject?"
    )
    project_knowledge_base.set("author_experience", author_experience)


def get_advanced_business_details(project_knowledge_base: ProjectKnowledgeBase):
    project_knowledge_base.set("num_characters", 0)
    project_knowledge_base.set("num_chapters", 0)
    project_knowledge_base.set("worldbuilding_needed", False)

    console.print("")
    tone = select_from_list(
        "Select Tone", ["Informative", "Motivational", "Instructive"]
    )
    project_knowledge_base.set("tone", tone)

    console.print("")
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

    console.print("")
    book_length = select_from_list(
        "📏 Select the desired book length:",
        ["Pamphlet", "Guidebook", "Full Book"],
        allow_custom=False,
    )
    project_knowledge_base.set("book_length", book_length)

    console.print("")
    key_takeaways = _prompt_text("What are the key takeaways you want readers to gain?")
    project_knowledge_base.set("key_takeaways", key_takeaways)

    console.print("")
    case_studies = typer.confirm("Will you include case studies?")
    project_knowledge_base.set("case_studies", case_studies)

    console.print("")
    actionable_advice = typer.confirm("Will you provide actionable advice/exercises?")
    project_knowledge_base.set("actionable_advice", actionable_advice)

    if project_knowledge_base.get("genre") == "Marketing":
        console.print("")
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
        project_knowledge_base.set("marketing_focus", marketing_focus)

    elif project_knowledge_base.get("genre") == "Sales":
        console.print("")
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


def get_advanced_research_details(project_knowledge_base: ProjectKnowledgeBase):
    project_knowledge_base.set("num_characters", 0)
    project_knowledge_base.set("num_chapters", 0)
    project_knowledge_base.set("worldbuilding_needed", False)
    project_knowledge_base.set("tone", "Formal and Objective")

    console.print("")
    target_audience = select_from_list(
        "👥 Select Target Audience",
        [
            "Academic Community",
            "Researchers",
            "Students",
            "General Public (if applicable)",
        ],
    )
    console.print("")
    project_knowledge_base.set("target_audience", target_audience)

    console.print("")
    project_knowledge_base.set("book_length", "Academic Article")

    console.print("")
    research_question = _prompt_text("What is your primary research question?")
    project_knowledge_base.set("research_question", research_question)

    console.print("")
    hypothesis = _prompt_text("What is your hypothesis (if applicable)?")
    project_knowledge_base.set("hypothesis", hypothesis)

    console.print("")
    methodology = select_from_list(
        "🔍  Select your research methodology:",
        ["Quantitative", "Qualitative", "Mixed Methods"],
        allow_custom=True,
    )
    project_knowledge_base.set("methodology", methodology)


def get_dynamic_questions(project_knowledge_base: ProjectKnowledgeBase):
    print("\nNow, let's dive into some genre-specific questions...")
    dynamic_questions = generate_questions_with_llm(
        project_knowledge_base.category, project_knowledge_base.genre
    )

    for q_id, question in dynamic_questions.items():
        answer = _prompt_text(question)
        project_knowledge_base.dynamic_questions[q_id] = answer
        save_project_data()


# --- Advanced Mode (Refactored) ---


def advanced_mode():
    console.print("\n[cyan]✨ Starting Advanced Mode...[/cyan]\n")

    project_name, title = get_project_name_and_title()
    project_knowledge_base = ProjectKnowledgeBase(
        project_name=project_name, title=title
    )

    # Add language selection right after project name and title
    select_language(project_knowledge_base)

    # LLM selection
    llm_choice = select_llm(project_knowledge_base)
    configure_advanced_model(project_knowledge_base)
    configure_advanced_fallbacks(project_knowledge_base)
    project_manager.initialize_llm_client(llm_choice, project_knowledge_base.model)

    get_category_and_genre(project_knowledge_base)

    if project_knowledge_base.category == "Fiction":
        get_advanced_fiction_details(project_knowledge_base)
    elif project_knowledge_base.category == "Non-Fiction":
        get_advanced_nonfiction_details(project_knowledge_base)
    elif project_knowledge_base.category == "Business":
        get_advanced_business_details(project_knowledge_base)
    elif project_knowledge_base.category == "Research Paper":
        get_advanced_research_details(project_knowledge_base)

    get_review_preference(project_knowledge_base)
    configure_chapter_writing_flow(project_knowledge_base, advanced=True)
    get_description(project_knowledge_base)

    project_manager.initialize_project_with_data(project_knowledge_base)  # Initialize

    get_dynamic_questions(project_knowledge_base)

    if generate_and_review_concept(project_knowledge_base):
        generate_and_edit_outline(project_knowledge_base)
        generate_characters_if_needed(project_knowledge_base)
        generate_worldbuilding_if_needed(project_knowledge_base)
        write_and_review_chapters(
            project_knowledge_base,
            progression_mode=StageMode.AUTO
            if project_knowledge_base.chapter_writing_mode == "auto"
            else StageMode.PROMPT,
            error_mode=ErrorMode.CONTINUE
            if project_knowledge_base.chapter_error_mode == "continue"
            else ErrorMode.STOP,
        )
        format_book(project_knowledge_base)
    else:
        print("Exiting.")
        return

    print("\nBook creation process complete (Advanced Mode).")


def select_language(project_knowledge_base: ProjectKnowledgeBase) -> str:
    """Lets the user select a language for their book."""
    console.print("")
    language_options = [
        "English",
        "Spanish",
        "Brazilian Portuguese",
        "French",
        "German",
        "Chinese (Simplified)",
        "Japanese",
        "Russian",
        "Arabic",
        "Hindi",
    ]
    language = select_from_list(
        "🌐 Select the language for your book:", language_options, allow_custom=True
    )
    project_knowledge_base.set("language", language)
    return language


def resolve_expert_config(config_path: str | None = None) -> tuple[ExpertConfig, str]:
    """Loads expert configuration from a file or from the most recent saved expert settings."""
    if config_path:
        config = load_expert_config(config_path)
        return config, f"{config_path}"

    recent_config = load_recent_expert_config()
    if recent_config:
        console.print("")
        source = select_from_list(
            "⚙️ How would you like to start Expert mode?",
            ["Use most recent expert settings", "Load a configuration file"],
        )
        if "most recent" in source:
            return recent_config, "most recent expert settings"

    console.print("")
    entered_path = str(
        typer.prompt(
            "📄 Enter the path to your expert config file (.json, .yml, .yaml)"
        )
    )
    config = load_expert_config(entered_path)
    return config, entered_path


def expert_mode(config_path: str | None = None) -> None:
    console.print("\n[cyan]✨ Starting Expert Mode...[/cyan]\n")

    try:
        config, source = resolve_expert_config(config_path)
        save_recent_expert_config(config)
        project_knowledge_base = build_project_knowledge_base(config)

        project_manager.initialize_llm_client(
            project_knowledge_base.llm_provider,
            project_knowledge_base.model,
        )
        project_manager.initialize_project_with_data(project_knowledge_base)

        console.print(f"[green]Loaded expert configuration from {source}[/green]")

        if generate_and_review_concept(
            project_knowledge_base, config.workflow.concept_approval
        ):
            generate_and_edit_outline(
                project_knowledge_base, config.workflow.outline_review
            )
            generate_characters_if_needed(
                project_knowledge_base, config.workflow.character_generation
            )
            generate_worldbuilding_if_needed(
                project_knowledge_base, config.workflow.worldbuilding_generation
            )

            if config.workflow.chapter_writing != StageMode.SKIP:
                write_and_review_chapters(
                    project_knowledge_base,
                    progression_mode=config.workflow.chapter_writing,
                    error_mode=config.workflow.chapter_error_mode,
                )

            format_book(
                project_knowledge_base,
                mode=config.workflow.formatting,
                output_format=config.workflow.output_format,
            )
        else:
            print("Exiting.")
            return

        console.print("\n[green]🎉 Book creation process complete![/green]")
    except Exception as e:
        console.print(f"[red]Expert mode failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def start(
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to an expert configuration file (.json, .yml, .yaml).",
    ),
):
    """Starts the interactive book creation process."""
    introduction()

    if config:
        expert_mode(config)
        return

    mode_options = [
        "Simple Guided Setup",
        "Advanced Guided Setup",
        "Expert: Configuration File",
    ]
    mode = select_from_list("✨ Choose your creation mode:", mode_options)

    if "Simple" in mode:
        simple_mode()
    elif "Advanced" in mode:
        advanced_mode()
    elif "Expert" in mode:
        expert_mode()


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
    chapter_writer_agent = project_manager.agents.get("chapter_writer")
    chapter_writer_name = (
        chapter_writer_agent.name
        if chapter_writer_agent is not None
        else "ChapterWriterAgent"
    )
    logger.info(f"📝 Agent {chapter_writer_name} writing chapter {chapter_number}...")
    project_manager.write_and_review_chapter(chapter_number)
    logger.info(f"✅ Chapter {chapter_number} complete.")


@app.command()
def edit(chapter_number: int = typer.Option(..., prompt="Chapter number to edit")):
    """Edits and refines a specific chapter"""
    project_manager.edit_chapter(chapter_number)


@app.command()
def format():
    """Formats the entire book into a single Markdown or PDF file."""
    output_format = select_from_list(
        "Choose output format:", ["Markdown (.md)", "PDF (.pdf)"]
    )
    if not project_manager.project_dir:
        print("ERROR: Project directory not initialized.")
        return

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


def _print_resume_summary(project_name: str, progress: ProjectProgress) -> None:
    console.print("")
    console.print(f"[bold]Resume summary for {project_name}[/bold]")
    console.print(
        f"Concept: {'done' if progress.concept_complete else 'pending'} | Outline: {'done' if progress.outline_complete else 'pending'}"
    )
    console.print(
        f"Characters: {'done' if progress.characters_complete else 'pending'} | Worldbuilding: {'done' if progress.worldbuilding_complete else 'pending'}"
    )
    console.print(
        f"Completed chapters: {progress.chapter_numbers_complete or 'none'} | Missing chapters: {progress.missing_chapters or 'none'}"
    )
    console.print(
        f"Manuscript: {'present' if progress.manuscript_exists else 'not generated yet'}"
    )
    if progress.interrupted_stage:
        console.print(
            f"[yellow]Last recorded interrupted/failed stage:[/yellow] {progress.interrupted_stage}"
        )
    if progress.stage_statuses:
        console.print(f"Recorded stage status file: {progress.stage_statuses}")
    console.print(f"Next recommended step: [cyan]{progress.next_step}[/cyan]")


@app.command()
def resume(project_name: str = typer.Option(..., prompt="Project name to resume")):
    """Resumes a project from the next incomplete step without overwriting completed work."""
    try:
        project_manager.load_project_data(project_name)
        if not project_manager.project_knowledge_base:
            print("ERROR resuming project")
            return

        project_knowledge_base = project_manager.project_knowledge_base
        project_manager.initialize_llm_client(
            project_knowledge_base.llm_provider,
            project_knowledge_base.model,
        )

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        _print_resume_summary(project_name, progress)

        if progress.next_step == "complete":
            console.print(
                "[green]This project already looks complete. No resume work needed.[/green]"
            )
            return

        if not typer.confirm(
            "Resume from the next incomplete step and keep existing files intact?"
        ):
            console.print("[yellow]Resume cancelled.[/yellow]")
            return

        if not progress.concept_complete:
            console.print("[cyan]Resuming concept generation...[/cyan]")
            if not generate_and_review_concept(project_knowledge_base):
                console.print("[yellow]Resume stopped after concept review.[/yellow]")
                return

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        if not progress.outline_complete:
            console.print("[cyan]Resuming outline generation...[/cyan]")
            generate_and_edit_outline(project_knowledge_base)

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        if progress.characters_required and not progress.characters_complete:
            console.print("[cyan]Generating missing character profiles...[/cyan]")
            generate_characters_if_needed(project_knowledge_base, mode=StageMode.AUTO)

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        if progress.worldbuilding_required and not progress.worldbuilding_complete:
            console.print("[cyan]Generating missing worldbuilding details...[/cyan]")
            generate_worldbuilding_if_needed(
                project_knowledge_base, mode=StageMode.AUTO
            )

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        if progress.missing_chapters:
            console.print(
                f"[cyan]Writing only missing chapters: {progress.missing_chapters}[/cyan]"
            )
            write_and_review_chapters(
                project_knowledge_base,
                progression_mode=StageMode.AUTO
                if project_knowledge_base.chapter_writing_mode == "auto"
                else StageMode.PROMPT,
                error_mode=ErrorMode.CONTINUE
                if project_knowledge_base.chapter_error_mode == "continue"
                else ErrorMode.STOP,
            )

        progress = inspect_project_progress(
            project_manager.project_dir, project_knowledge_base
        )
        if progress.next_step == "formatting":
            console.print(
                "[cyan]All core content is present. Formatting is the next step.[/cyan]"
            )
            format_book(project_knowledge_base)

        console.print("[green]Resume flow complete.[/green]")

    except FileNotFoundError:
        print(f"Project '{project_name}' not found.")
    except ValueError as e:
        print(f"Error loading project data: {e}")


# --- Retrieval CLI Commands ---
retrieval_app = typer.Typer(help="Manage local search and retrieval index.")


def _load_retrieval_project(project_name: str) -> None:
    project_manager.load_project_data(project_name)
    if not project_manager.project_knowledge_base:
        console.print(f"[red]Error:[/red] Project '{project_name}' not found.")
        raise typer.Exit(code=1)

    ret_config = getattr(project_manager.project_knowledge_base, "retrieval", None)
    if not ret_config:
        from libriscribe.retrieval.models import RetrievalConfig
        project_manager.project_knowledge_base.retrieval = RetrievalConfig(enabled=True, mode="keyword")
        project_manager.save_project_data()
    elif not ret_config.enabled:
        ret_config.enabled = True
        if ret_config.mode == "disabled":
            ret_config.mode = "keyword"
        project_manager.save_project_data()


@retrieval_app.command()
def rebuild(project: str = typer.Option(..., "--project", "-p", help="Project name")):
    """Forces a clean, complete rebuild of all local retrieval files and indexes."""
    _load_retrieval_project(project)
    console.print(f"[cyan]Rebuilding retrieval index for project '{project}'...[/cyan]")
    project_manager.rebuild_retrieval_index()
    console.print("[green]Rebuild complete![/green]")


@retrieval_app.command()
def refresh(project: str = typer.Option(..., "--project", "-p", help="Project name")):
    """Refreshes the index incrementally if changes are detected in sources."""
    _load_retrieval_project(project)
    console.print(f"[cyan]Refreshing retrieval index for project '{project}'...[/cyan]")
    project_manager.refresh_retrieval_index()
    console.print("[green]Refresh check complete![/green]")


@retrieval_app.command()
def search(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    mode: str = typer.Option("keyword", "--mode", "-m", help="Search mode (keyword)"),
    top_k: int = typer.Option(6, "--top-k", "-k", help="Number of results to return"),
):
    """Queries the local retrieval index."""
    _load_retrieval_project(project)
    project_manager.initialize_retrieval()

    console.print(f"[cyan]Searching in '{project}' for:[/cyan] [bold]'{query}'[/bold] [cyan](mode: {mode}, top_k: {top_k})...[/cyan]")
    results = project_manager.search_service.search(query, mode=mode, top_k=top_k)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    console.print(f"\n[green]Found {len(results)} results:[/green]")
    for i, res in enumerate(results, 1):
        console.print(f"\n[bold]{i}. {res.title}[/bold] (Score: {res.score:.4f}, Type: {res.source_type})")
        snippet = res.text[:200] + "..." if len(res.text) > 200 else res.text
        console.print(f"   [dim]{snippet}[/dim]")


@retrieval_app.command()
def xref(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    entity: str = typer.Option(..., "--entity", "-e", help="Entity name"),
):
    """Looks up co-occurrences and cross-references of an entity."""
    _load_retrieval_project(project)
    project_manager.initialize_retrieval()

    console.print(f"[cyan]Looking up cross-references for entity:[/cyan] [bold]'{entity}'[/bold]...")
    entry = project_manager.search_service.search_cross_references(entity)

    if not entry:
        console.print(f"[yellow]No cross-references found for entity '{entity}'.[/yellow]")
        return

    console.print(f"\n[green]Cross-Reference Entry for '{entry.entity_name}' ({entry.entity_type}):[/green]")
    console.print(f"  [bold]Chapters referenced in:[/bold] {sorted(list(set(entry.referenced_in_chapters)))}")
    console.print(f"  [bold]Related/co-occurring entities:[/bold] {', '.join(entry.related_entities) or 'None'}")
    console.print(f"  [bold]Referenced in chunks:[/bold] {len(entry.referenced_in_chunks)} chunk(s)")


app.add_typer(retrieval_app, name="retrieval")


if __name__ == "__main__":
    # Display environment info for debugging
    if "--debug" in sys.argv:
        console.print("[yellow]Debug Info:[/yellow]")
        console.print(f"Python: {sys.version}")
        console.print(f"Terminal: {os.environ.get('TERM', 'Unknown')}")
        console.print(f"Rich version: {package_version('rich')}")
        # Then continue with normal app execution
    app()
