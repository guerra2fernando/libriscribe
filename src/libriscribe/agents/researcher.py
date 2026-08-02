# src/libriscribe/agents/researcher.py
import logging
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from rich.console import Console

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import write_markdown_file
from libriscribe.utils.llm_client import LLMClient

console = Console()
logger = logging.getLogger(__name__)

_GOOGLE_SEARCH_TIMEOUT = 10


class ResearcherAgent(Agent):
    """Conducts web research."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("ResearcherAgent", llm_client)

    def execute(self, query: str, output_path: str) -> None:
        """Performs web research and saves the results to a Markdown file."""

        try:
            output_file = Path(output_path)
            project_dir = output_file.parent
            project_data_path = project_dir / "project_data.json"

            language = "English"

            if project_data_path.exists():
                try:
                    project_kb = ProjectKnowledgeBase.load_from_file(str(project_data_path))
                    if project_kb and hasattr(project_kb, "language"):
                        language = project_kb.language
                except Exception as e:
                    self.logger.warning("Could not load project data for language detection: %s", e)

            console.print(f"🔎 [cyan]Researching: {query}...[/cyan]")
            prompt = prompts.RESEARCH_PROMPT.format(query=query, language=language)
            llm_summary = self.llm_client.generate_content(prompt, max_tokens=1000)

            search_results = self.scrape_google_search(query)
            parts: list[str] = []
            for result in search_results:
                parts.append(f"### [{result['title']}]({result['url']})\n\n{result['snippet']}\n\n")
            scraped_content = "".join(parts)

            final_report = (
                f"# Research Report: {query}\n\n"
                f"## AI-Generated Summary\n\n{llm_summary}\n\n"
                f"## Web Search Results\n\n{scraped_content}"
            )
            write_markdown_file(output_path, final_report)

        except Exception:
            self.logger.exception("Error during research for query '%s'", query)
            console.print(f"[red]ERROR:[/red] Failed to perform research for '{query}'. See log.")

    def scrape_google_search(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        """Scrapes Google Search results for a given query.

        Note: relies on Google's internal CSS class names which may change without notice.
        Returns an empty list when scraping fails or classes have changed.
        """
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            url = "https://www.google.com/search"
            response = requests.get(
                url,
                headers=headers,
                params={"q": query, "num": num_results},
                timeout=_GOOGLE_SEARCH_TIMEOUT,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results: list[dict[str, Any]] = []

            for g in soup.find_all("div", class_="tF2Cxc"):
                if not isinstance(g, Tag):
                    continue
                try:
                    anchor = g.find("a")
                    if not isinstance(anchor, Tag):
                        continue
                    link = anchor.get("href", "")
                    h3 = g.find("h3")
                    title = h3.get_text() if isinstance(h3, Tag) else ""
                    snippet_div = g.find("div", class_="VwiC3b")
                    snippet = snippet_div.get_text() if isinstance(snippet_div, Tag) else ""
                    results.append({"title": title, "url": link, "snippet": snippet})
                except Exception:
                    self.logger.warning("Error parsing a search result", exc_info=True)
                    continue

            return results
        except requests.exceptions.RequestException as e:
            self.logger.error("Error during Google Search scraping: %s", e)
            console.print(f"[red]ERROR:[/red] Could not perform web search: {e}")
            return []
        except Exception:
            self.logger.exception("An unexpected error occurred during google scraping")
            return []
