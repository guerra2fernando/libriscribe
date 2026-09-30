"""Local stdio MCP server for LibriScribe."""
from __future__ import annotations

import builtins
import logging
import sys
from typing import Annotated, Any, Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from libriscribe.service import LibriScribeService, ServiceError

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("libriscribe.mcp")
service = LibriScribeService()
mcp = FastMCP("libriscribe")


def _invoke(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Keep Python/Rich CLI output off stdout, which belongs to JSON-RPC."""
    try:
        return {"ok": True, "result": call()}
    except ServiceError as exc:
        return {"ok": False, "error": {"code": exc.code, "message": exc.message}}
    except Exception:
        logger.exception("Unexpected MCP tool failure")
        return {"ok": False, "error": {"code": "internal_error", "message": "The request failed unexpectedly. Check the local LibriScribe log."}}


def _redirect_diagnostics():
    """Keep library prints/Rich output on stderr without redirecting protocol stdout."""
    from rich.console import Console

    original_stdout = sys.stdout
    original_print = builtins.print

    if not getattr(builtins.print, "_libriscribe_stderr", False):
        def stderr_print(*args: Any, **kwargs: Any) -> None:
            output = kwargs.get("file")
            if output is None or output is original_stdout:
                kwargs["file"] = sys.stderr
            original_print(*args, **kwargs)

        setattr(stderr_print, "_libriscribe_stderr", True)
        builtins.print = stderr_print
    # ProjectManagerAgent imports its workflow agents up front. Keep this list
    # explicit so the hot tool path does not scan unrelated runtime modules.
    console_modules = (
        "libriscribe.agents.project_manager",
        "libriscribe.agents.character_generator",
        "libriscribe.agents.chapter_writer",
        "libriscribe.agents.concept_generator",
        "libriscribe.agents.formatting_optimized",
        "libriscribe.agents.worldbuilding",
        "libriscribe.agents.style_editor",
        "libriscribe.agents.formatting",
        "libriscribe.agents.researcher",
        "libriscribe.agents.fact_checker",
        "libriscribe.agents.plagiarism_checker",
        "libriscribe.agents.outliner",
        "libriscribe.agents.editor_enhanced",
        "libriscribe.agents.editor",
        "libriscribe.agents.content_reviewer",
    )
    for module_name in console_modules:
        module = sys.modules.get(module_name)
        console = getattr(module, "console", None) if module else None
        if isinstance(console, Console) and console.file is original_stdout:
            console.file = sys.stderr


READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITE_LLM = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)
FORMAT_LLM = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)
WRITE_LOCAL = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)


@mcp.tool(name="list_projects", description="List LibriScribe projects under the configured projects directory. Returns only project identifiers and basic metadata; limit is 1–100.", annotations=READ, structured_output=True)
def list_projects(limit: Annotated[int, Field(description="Maximum projects to return; 1 to 100.")] = 50) -> dict[str, Any]:
    return _invoke(lambda: service.list_projects(limit))


@mcp.tool(name="create_project", description="Create an empty local project with structured metadata. Does not call an LLM or accept filesystem paths. Refuses an existing project identifier.", annotations=WRITE_LOCAL, structured_output=True)
def create_project(project: Annotated[str, Field(description="Unique project identifier; 1–100 letters, numbers, spaces, dots, underscores, or hyphens.")], title: Annotated[str, Field(description="Book or project title.", max_length=300)], description: Annotated[str, Field(description="Short project description.", max_length=5000)] = "", category: Annotated[str, Field(description="Existing project category, such as Fiction, Non-fiction, Business, or Research Paper.", max_length=100)] = "Fiction", genre: Annotated[str, Field(description="Genre.", max_length=200)] = "Unknown Genre", language: Annotated[str, Field(description="Writing language.", max_length=100)] = "English", chapter_count: Annotated[int, Field(description="Planned chapter count from 1 to 500.", ge=1, le=500)] = 1, llm_provider: Annotated[str, Field(description="Provider identifier used by later generation tools; no provider call occurs during creation.", max_length=100)] = "openai", model: Annotated[str, Field(description="Optional provider model identifier.", max_length=200)] = "") -> dict[str, Any]:
    return _invoke(lambda: service.create_project(project, title, description, category, genre, language, chapter_count, llm_provider, model))


@mcp.tool(name="get_project_status", description="Read workflow progress and the most recent operation, including whether it completed, failed, or may have been interrupted and the next safe explicit action.", annotations=READ, structured_output=True)
def get_project_status(project: str) -> dict[str, Any]:
    return _invoke(lambda: service.get_project_status(project))


@mcp.tool(name="get_chapter", description="Read an original or revised chapter and its SHA-256 revision_token. Text is bounded; use start_char and max_chars (up to 20,000) to page through it. Pass the token to replace_chapter_text to guard against stale edits.", annotations=READ, structured_output=True)
def get_chapter(project: str, chapter_number: Annotated[int, Field(description="Positive chapter number.")], version: Annotated[str, Field(description="One of: original, revised.")] = "original", start_char: Annotated[int, Field(description="Nonnegative character offset for pagination.")] = 0, max_chars: Annotated[int, Field(description="Page size from 1 to 20,000 characters.")] = 20_000) -> dict[str, Any]:
    return _invoke(lambda: service.get_chapter(project, chapter_number, version, start_char, max_chars))


@mcp.tool(name="replace_chapter_text", description="Save user-supplied text as a manual revision of an existing original or revised chapter. Makes no LLM call. Requires the current revision_token from get_chapter; refuses stale tokens and never creates a missing version.", annotations=WRITE_LOCAL, structured_output=True)
def replace_chapter_text(project: str, chapter_number: Annotated[int, Field(description="Positive chapter number.", ge=1)], version: Annotated[str, Field(description="Existing chapter version to replace: original or revised.")] , text: Annotated[str, Field(description="Complete nonempty replacement text, up to 100,000 characters.", min_length=1, max_length=100_000)], expected_revision_token: Annotated[str, Field(description="SHA-256 revision_token returned by get_chapter.", min_length=64, max_length=64)]) -> dict[str, Any]:
    return _invoke(lambda: service.replace_chapter_text(project, chapter_number, version, text, expected_revision_token))


@mcp.tool(name="search_project", description="Search an existing local keyword index. Does not rebuild it. Fails clearly when retrieval is disabled or its index is unavailable.", annotations=READ, structured_output=True)
def search_project(project: str, query: Annotated[str, Field(description="Nonempty query, up to 2,000 characters.")], top_k: Annotated[int, Field(description="Number of matches from 1 to 20.")] = 6, mode: Annotated[str, Field(description="Currently supported mode: keyword.")] = "keyword") -> dict[str, Any]:
    return _invoke(lambda: service.search_project(project, query, top_k, mode))


@mcp.tool(name="check_narrative", description="Check a chapter's scene outline against the existing narrative graph and return structured continuity violations. This check makes no LLM call.", annotations=READ, structured_output=True)
def check_narrative(project: str, chapter_number: Annotated[int, Field(description="Positive chapter number.")]) -> dict[str, Any]:
    return _invoke(lambda: service.check_narrative(project, chapter_number))


@mcp.tool(name="generate_outline", description="Generate an outline for an existing project. May contact the project's configured LLM provider. Refuses to replace outline.md unless overwrite=true.", annotations=WRITE_LLM, structured_output=True)
def generate_outline(project: str, overwrite: bool = False) -> dict[str, Any]:
    return _invoke(lambda: service.generate_outline(project, overwrite))


@mcp.tool(name="write_chapter", description="Generate one chapter for an existing project. May contact the project's configured LLM provider. Refuses to replace an existing chapter unless overwrite=true.", annotations=WRITE_LLM, structured_output=True)
def write_chapter(project: str, chapter_number: Annotated[int, Field(description="Positive chapter number.")], overwrite: bool = False) -> dict[str, Any]:
    return _invoke(lambda: service.write_chapter(project, chapter_number, overwrite))


@mcp.tool(name="edit_chapter", description="Edit an existing original chapter into a revised chapter. May contact the project's configured LLM provider. Refuses to replace a revised chapter unless overwrite=true.", annotations=WRITE_LLM, structured_output=True)
def edit_chapter(project: str, chapter_number: Annotated[int, Field(description="Positive chapter number.")], overwrite: bool = False) -> dict[str, Any]:
    return _invoke(lambda: service.edit_chapter(project, chapter_number, overwrite))


@mcp.tool(name="format_book", description="Format a book to a fixed manuscript filename inside its project (md or pdf). PDF formatting may call the configured LLM provider. Refuses existing output files unless overwrite=true.", annotations=FORMAT_LLM, structured_output=True)
def format_book(project: str, format: Annotated[str, Field(description="Output format: md or pdf.")], overwrite: bool = False) -> dict[str, Any]:
    return _invoke(lambda: service.format_book(project, format, overwrite))


def main() -> None:
    """Run the MCP protocol over stdin/stdout."""
    _redirect_diagnostics()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
