# src/libriscribe/agents/outliner.py

import logging
import re
from pathlib import Path
from typing import Optional

from libriscribe.utils.llm_client import LLMClient
from libriscribe.utils import prompts_context as prompts
from libriscribe.agents.agent_base import Agent
from libriscribe.utils.file_utils import write_markdown_file, write_json_file
from libriscribe.knowledge_base import ProjectKnowledgeBase, Chapter, Scene
from rich.console import Console

console = Console()

_ADVANCED_FIELDS: list[tuple[str, str]] = [
    ("inspired_by", "Inspired by"),
    ("author_experience", "Author experience"),
    ("key_takeaways", "Key takeaways"),
    ("case_studies", "Includes case studies"),
    ("actionable_advice", "Includes actionable advice"),
    ("marketing_focus", "Marketing focus"),
    ("sales_focus", "Sales focus"),
    ("research_question", "Research question"),
    ("hypothesis", "Hypothesis"),
    ("methodology", "Methodology"),
]
logger = logging.getLogger(__name__)


class OutlinerAgent(Agent):
    """Generates book outlines."""

    def __init__(self, llm_client: LLMClient):
        super().__init__("OutlinerAgent", llm_client)

    def execute(self, project_knowledge_base: ProjectKnowledgeBase, output_path: Optional[str] = None) -> None:
        """Generates a chapter outline and then iterates to generate scene outlines."""
        try:
            # --- Step 1: Determine max chapters based on book length FIRST ---
            max_chapters = self._get_max_chapters(project_knowledge_base)

            # Enhance the prompt with explicit chapter count instruction
            if project_knowledge_base.book_length == "Short Story":
                initial_prompt = prompts.OUTLINE_PROMPT.format(**project_knowledge_base.model_dump())
                initial_prompt += f"\n\nIMPORTANT: This is a SHORT STORY. Generate EXACTLY {max_chapters} chapters. Do not exceed this limit."
            elif project_knowledge_base.book_length == "Novella":
                initial_prompt = prompts.OUTLINE_PROMPT.format(**project_knowledge_base.model_dump())
                initial_prompt += f"\n\nIMPORTANT: This is a NOVELLA. Generate EXACTLY {max_chapters} chapters. Do not exceed this limit."
            else:
                initial_prompt = prompts.OUTLINE_PROMPT.format(**project_knowledge_base.model_dump())
                initial_prompt += f"\n\nIMPORTANT: Generate at most {max_chapters} chapters."

            # Task 10: Append user's chapter count preference to prompt (only when explicitly set)
            num_ch_str = project_knowledge_base.get("num_chapters_str", "")
            if num_ch_str and str(num_ch_str) not in ("0", ""):
                initial_prompt += f"\nAuthor's preferred chapter count: {num_ch_str}."

            # Task 3: Append advanced-mode author notes to prompt
            notes = []
            for field, label in _ADVANCED_FIELDS:
                val = project_knowledge_base.get(field)
                if val is not None and val is not False and str(val).strip():
                    notes.append(f"  - {label}: {val}")
            if notes:
                initial_prompt += "\n\nAuthor notes (incorporate into structure):\n" + "\n".join(notes)

            console.print("📝 [cyan]Creating chapter outline...[/cyan]")
            initial_outline = self.llm_client.generate_content(initial_prompt, max_tokens=3000, temperature=0.5)
            if not initial_outline:
                logger.error("Initial outline generation failed.")
                return

            # Process outline with max_chapters limit already included in prompt
            self.process_outline(project_knowledge_base, initial_outline, max_chapters)
            # Task 11: Enforce chapter limit (trim any excess chapters the LLM may have generated)
            self._enforce_chapter_limit(project_knowledge_base, max_chapters)

            # Save the overall outline first
            if output_path is None:
                project_dir = project_knowledge_base.project_dir
                if project_dir is None:
                    logger.error("project_dir is not set on knowledge base; cannot save outline.")
                    return
                output_path = str(Path(project_dir) / "outline.md")

            project_knowledge_base.outline = initial_outline
            write_markdown_file(output_path, project_knowledge_base.outline)

            # --- Step 2: Generate scene outlines for each chapter ---
            console.print("🎬 [cyan]Creating scene/sections breakdowns for each chapter...[/cyan]")

            for chapter_num, chapter in project_knowledge_base.chapters.items():
                if chapter_num <= max_chapters:
                    console.print(f"📋 Working on Chapter {chapter_num}: {chapter.title}")

                    self.generate_scene_outline(project_knowledge_base, chapter)

                    if chapter.scenes:
                        console.print(f"  [green]✅ Created {len(chapter.scenes)} scenes for Chapter {chapter_num}[/green]")
                    else:
                        console.print(f"  [yellow]⚠ No scenes were generated for Chapter {chapter_num}[/yellow]")

            # Save the updated project data with scenes
            if hasattr(project_knowledge_base, "project_dir") and project_knowledge_base.project_dir:
                scenes_path = str(Path(project_knowledge_base.project_dir) / "scenes.json")

                scenes_data: dict[str, list[dict]] = {}
                for chapter_num, chapter in project_knowledge_base.chapters.items():
                    scenes_data[str(chapter_num)] = [scene.model_dump() for scene in chapter.scenes]

                write_json_file(scenes_path, scenes_data)
                console.print(f"Scene outlines saved to: {scenes_path}")

            self.logger.info("Outline and scenes generated and saved to knowledge base and %s", output_path)

        except Exception:
            self.logger.exception("Error generating outline")
            console.print("[red]ERROR:[/red] Failed to generate outline. See log for details.")

    def _get_max_chapters(self, project_knowledge_base: ProjectKnowledgeBase) -> int:
        """Determine the maximum number of chapters based on book length and user preference."""
        pkb = project_knowledge_base
        if pkb.book_length == "Short Story":
            length_max = 2
        elif pkb.book_length == "Novella":
            length_max = 8
        else:
            length_max = 20

        # Only honor num_chapters when the user explicitly set it (num_chapters_str is the explicit signal).
        # The PKB default num_chapters=1 must not be treated as a user preference.
        num_ch_str = pkb.get("num_chapters_str", "")
        if not num_ch_str or str(num_ch_str) in ("0", ""):
            return length_max

        num_ch = pkb.num_chapters
        if isinstance(num_ch, tuple) and len(num_ch) == 2:
            user_max = max(num_ch)
        elif isinstance(num_ch, int) and num_ch > 0:
            user_max = num_ch
        else:
            user_max = None

        if user_max is not None:
            return min(user_max, length_max)
        return length_max

    def _enforce_chapter_limit(self, project_knowledge_base: ProjectKnowledgeBase, max_chapters: int) -> None:
        """Limit the number of chapters in the knowledge base to max_chapters."""
        current_chapters = len(project_knowledge_base.chapters)
        if current_chapters > max_chapters:
            logger.info("Limiting chapters from %d to %d", current_chapters, max_chapters)
            console.print(f"[yellow]Trimming outline to {max_chapters} chapters for {project_knowledge_base.book_length}[/yellow]")

            chapters_to_keep = {
                i: project_knowledge_base.chapters[i]
                for i in range(1, max_chapters + 1)
                if i in project_knowledge_base.chapters
            }
            project_knowledge_base.chapters = chapters_to_keep
            project_knowledge_base.num_chapters = max_chapters

    def generate_scene_outline(self, project_knowledge_base: ProjectKnowledgeBase, chapter: Chapter) -> bool:
        """Generates the scene outline for a single chapter."""
        try:
            dq = project_knowledge_base.dynamic_questions
            dq_note = ""
            if dq:
                dq_lines = "\n".join(f"  - {q}: {a}" for q, a in dq.items())
                dq_note = f"\n\nGenre-specific author details:\n{dq_lines}"
            scene_prompt = f"""
            Create a detailed outline for the scenes in Chapter {chapter.chapter_number}: {chapter.title}
            of a {project_knowledge_base.genre} book titled "{project_knowledge_base.title}"
            which is categorized as {project_knowledge_base.category}.
            The book should be written in {project_knowledge_base.language}.

            Book Description: {project_knowledge_base.description}{dq_note}

            Chapter Summary: {chapter.summary}

            The outline should include a breakdown of 3-6 scenes for this chapter, with EACH scene having:
            * Scene Number: (e.g., Scene 1, Scene 2, etc.)
            * Summary: (A short description of what happens in the scene, 1-2 sentences)
            * Characters: (A list of the characters involved, separated by commas)
            * Setting: (Where the scene takes place)
            * Goal: (The purpose of the scene)
            * Emotional Beat: (The primary emotion conveyed in the scene)

            IMPORTANT: Format the scene outline using Markdown bullet points, as shown below:

            Scene 1:
                * Summary: [Scene summary here]
                * Characters: [Character 1, Character 2, ...]
                * Setting: [Scene setting]
                * Goal: [Scene goal]
                * Emotional Beat: [Scene emotional beat]

            Scene 2:
                * Summary: [Scene summary here]
                * Characters: [Character 1, Character 2, ...]
                * Setting: [Scene setting]
                * Goal: [Scene goal]
                * Emotional Beat: [Scene emotional beat]

            [Repeat for each scene, maintaining the exact same bullet point format]

            Be sure to include all main characters relevant to this chapter and create a natural flow between scenes.
            """

            # Task 3: Append advanced-mode author notes to scene prompt
            notes = []
            for field, label in _ADVANCED_FIELDS:
                val = project_knowledge_base.get(field)
                if val is not None and val is not False and str(val).strip():
                    notes.append(f"  - {label}: {val}")
            if notes:
                scene_prompt += "\n\nAuthor notes (maintain consistency with these):\n" + "\n".join(notes)

            console.print(f"  Generating Scene Outline for Chapter {chapter.chapter_number}...")
            scene_outline_md = self.llm_client.generate_content(scene_prompt, max_tokens=2000, temperature=0.5)
            if not scene_outline_md:
                logger.error("Scene outline generation failed for Chapter %d.", chapter.chapter_number)
                return False

            chapter.scenes = []

            scene_sections = self._split_into_scene_sections(scene_outline_md)

            for scene_number, scene_section in enumerate(scene_sections, 1):
                scene_data = self._extract_scene_data(scene_section, scene_number)

                if scene_data:
                    scene = Scene(**scene_data)
                    chapter.scenes.append(scene)
                    logger.debug("Added Scene %d to Chapter %d", scene_number, chapter.chapter_number)
                else:
                    logger.warning("Failed to extract data for Scene %d in Chapter %d", scene_number, chapter.chapter_number)

            chapter.scenes.sort(key=lambda s: s.scene_number)

            return True

        except Exception:
            logger.exception("Error generating scene outline for chapter %d", chapter.chapter_number)
            return False

    def _split_into_scene_sections(self, scene_outline_md: str) -> list[str]:
        """Split the scene outline into sections for each scene."""
        scene_outline_md = scene_outline_md.replace("\r\n", "\n").replace("\r", "\n")
        lines = scene_outline_md.split("\n")

        scene_sections: list[str] = []
        current_section: list[str] = []
        is_in_scene = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "Scene" in line and (":" in line or line.strip().startswith("Scene")):
                if is_in_scene and current_section:
                    scene_sections.append("\n".join(current_section))
                    current_section = []

                is_in_scene = True
                current_section.append(line)
            elif is_in_scene:
                current_section.append(line)

        if current_section:
            scene_sections.append("\n".join(current_section))

        return scene_sections

    def _extract_scene_data(self, scene_section: str, default_scene_number: int) -> dict | None:
        """Extract scene data from a scene section."""
        scene_data: dict = {
            "scene_number": default_scene_number,
            "summary": "",
            "characters": [],
            "setting": "",
            "goal": "",
            "emotional_beat": "",
        }

        lines = scene_section.split("\n")

        header_line = lines[0] if lines else ""
        if "Scene" in header_line and ":" in header_line:
            try:
                number_part = header_line.split("Scene", 1)[1].split(":", 1)[0].strip()
                if number_part.isdigit():
                    scene_data["scene_number"] = int(number_part)
            except (IndexError, ValueError):
                pass

        for line in lines:
            line = line.strip()

            if not line or line.startswith("Scene"):
                continue

            for field, marker in [
                ("summary", "Summary:"),
                ("characters", "Characters:"),
                ("setting", "Setting:"),
                ("goal", "Goal:"),
                ("emotional_beat", "Emotional Beat:"),
            ]:
                if marker.lower() in line.lower():
                    content = (
                        line.split(marker, 1)[1].strip()
                        if marker in line
                        else line.split(marker.lower(), 1)[1].strip()
                    )

                    content = content.lstrip("*-[]").strip()

                    if field == "characters":
                        scene_data["characters"] = [name.strip() for name in content.split(",") if name.strip()]
                    else:
                        scene_data[field] = content

        if not scene_data["summary"]:
            for line in lines:
                if line and not any(
                    marker in line.lower()
                    for marker in ["scene", "summary:", "characters:", "setting:", "goal:", "emotional beat:"]
                ):
                    if scene_data["summary"]:
                        scene_data["summary"] += " " + line.strip()
                    else:
                        scene_data["summary"] = line.strip()

        return scene_data if scene_data["summary"] else None

    def process_outline(self, project_knowledge_base: ProjectKnowledgeBase, outline_markdown: str, max_chapters: int) -> None:
        """Parses the Markdown outline and populates the knowledge base."""
        lines = outline_markdown.split("\n")
        current_chapter: Optional[Chapter] = None
        chapter_count = 0
        current_section: Optional[str] = None
        current_content: list[str] = []

        logger.info("Processing outline...")

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                continue

            if "Chapter" in line and (line.startswith("Chapter") or "##" in line or "**" in line):
                if chapter_count >= max_chapters:
                    break

                if current_chapter and current_content:
                    if current_section == "summary":
                        current_chapter.summary = "\n".join(current_content).strip()
                    current_content = []

                try:
                    chapter_parts = line.replace("##", "").replace("**", "").replace("Chapter", "").strip()

                    if ":" in chapter_parts:
                        chapter_num_str, chapter_title = chapter_parts.split(":", 1)
                    elif "-" in chapter_parts:
                        chapter_num_str, chapter_title = chapter_parts.split("-", 1)
                    else:
                        match = re.match(r"(\d+)\s*(.*)", chapter_parts)
                        if match:
                            chapter_num_str, chapter_title = match.groups()
                        else:
                            chapter_num_str = str(chapter_count + 1)
                            chapter_title = f"Chapter {chapter_num_str}"

                    chapter_number = int("".join(filter(str.isdigit, chapter_num_str)))
                    chapter_title = chapter_title.strip()

                    logger.info("Found Chapter %d: %s", chapter_number, chapter_title)

                    current_chapter = Chapter(
                        chapter_number=chapter_number,
                        title=chapter_title,
                        summary="",
                    )
                    project_knowledge_base.add_chapter(current_chapter)
                    chapter_count += 1
                    current_section = None
                    current_content = []

                except Exception:
                    logger.error("Error processing chapter line '%s'", line, exc_info=True)
                    continue

            elif "Book Summary" in line and chapter_count == 0:
                pass  # Book summary is stored in outline field; user description is preserved

            elif current_chapter and ("Summary" in line or line.startswith("Summary")):
                current_section = "summary"
                current_content = []
                continue

            elif current_chapter and ("Key Events" in line or "Plot Points" in line):
                if current_content:
                    current_chapter.summary = "\n".join(current_content).strip()
                current_section = "plot_points"
                current_content = []
                continue

            elif current_chapter and current_section:
                cleaned_line = line.replace("*", "").replace("[", "").replace("]", "").strip()
                if cleaned_line:
                    current_content.append(cleaned_line)
                    if current_section == "summary":
                        current_chapter.summary = "\n".join(current_content).strip()

            elif "Chapter List" in line or "chapters" in line.lower():
                try:
                    next_line = lines[i + 1] if i + 1 < len(lines) else ""
                    if next_line:
                        digits = re.findall(r"\d+", next_line)
                        if digits:
                            total_chapters = int(digits[0])
                            logger.info("Found total chapters: %d", total_chapters)
                            if 0 < total_chapters <= max_chapters:
                                project_knowledge_base.num_chapters = total_chapters
                except Exception:
                    logger.error("Error extracting chapter count", exc_info=True)

        if current_chapter and current_content:
            if current_section == "summary":
                current_chapter.summary = "\n".join(current_content).strip()

        if chapter_count == 0:
            logger.warning("No chapters found in outline")
            default_chapter = Chapter(
                chapter_number=1,
                title="Chapter 1",
                summary="Opening chapter.",
            )
            default_scene = Scene(
                scene_number=1,
                summary="Opening scene.",
                characters=[],
                setting="",
                goal="",
                emotional_beat="",
            )
            default_chapter.scenes.append(default_scene)
            project_knowledge_base.add_chapter(default_chapter)
            project_knowledge_base.num_chapters = 1
            logger.info("Created default chapter with scene")
        else:
            project_knowledge_base.num_chapters = chapter_count
            logger.info("Successfully processed %d chapters", chapter_count)

        if isinstance(project_knowledge_base.num_chapters, int) and project_knowledge_base.num_chapters <= 1:
            try:
                full_text = outline_markdown.lower()
                if "chapter list" in full_text:
                    chapter_count_patterns = [
                        r"(\d+)\s+chapters",
                        r"total\s+chapters:\s*(\d+)",
                        r"chapter\s+list\s*[\(:]?\s*(\d+)",
                    ]

                    for pattern in chapter_count_patterns:
                        match_obj = re.search(pattern, full_text)
                        if match_obj:
                            estimated_chapters = int(match_obj.group(1))
                            if 1 <= estimated_chapters <= max_chapters:
                                project_knowledge_base.num_chapters = estimated_chapters
                                logger.info("Extracted estimated chapter count: %d", estimated_chapters)
                                break
            except Exception:
                logger.error("Error extracting chapter count from text", exc_info=True)
