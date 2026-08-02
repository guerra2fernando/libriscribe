# src/libriscribe/agents/chapter_writer.py
"""ChapterWriterAgent: writes chapters scene-by-scene with narrative constraint injection and quality loop."""

import json
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console

from libriscribe.agents.agent_base import Agent
from libriscribe.knowledge_base import Chapter, ProjectKnowledgeBase, Scene
from libriscribe.narrative.graph_builder import NarrativeGraphBuilder
from libriscribe.narrative.invariant_checker import InvariantChecker
from libriscribe.narrative.models import NarrativeGraph
from libriscribe.utils import prompts_context as prompts
from libriscribe.utils.file_utils import write_markdown_file
from libriscribe.utils.llm_client import LLMClient

console = Console()
logger = logging.getLogger(__name__)

# Option B: rewrite when scene quality falls below this threshold
_QUALITY_REWRITE_THRESHOLD = 0.65

# Option A: inject style hints from axes scoring below this threshold
_STYLE_HINT_THRESHOLD = 0.70

_REWRITE_PROMPT = """\
You are a literary editor performing a targeted rewrite of a single scene.

PROBLEMS TO FIX (preserve everything else exactly):
{problems}

STRICT CONSTRAINTS:
- Keep all character names, locations, events, and plot facts identical.
- Keep all physical descriptions and injuries (e.g. a character missing a hand stays missing a hand).
- Do NOT add new characters, locations, or events.
- Do NOT change the scene's emotional beat or narrative outcome.
- Fix ONLY the flagged prose problems listed above.
- Return the complete rewritten scene — no preamble, no commentary.

ORIGINAL SCENE:
---
{scene_content}
---
"""


class ChapterWriterAgent(Agent):
    """Writes chapters scene-by-scene with narrative invariant injection and quality loop."""

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__("ChapterWriterAgent", llm_client)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def execute(
        self,
        project_knowledge_base: ProjectKnowledgeBase,
        chapter_number: int,
        output_path: Optional[str] = None,
    ) -> None:
        """Write a chapter scene by scene."""
        try:
            chapter = self._get_or_create_chapter(project_knowledge_base, chapter_number)
            console.print(f"\n[cyan]Writing Chapter {chapter_number}: {chapter.title}[/cyan]")

            project_dir = (
                Path(project_knowledge_base.project_dir)
                if project_knowledge_base.project_dir
                else None
            )

            # Load narrative graph for InvariantChecker
            narrative_graph = self._load_narrative_graph(project_dir, project_knowledge_base.project_name)
            checker = InvariantChecker(narrative_graph)

            # Option A: build style hints from prior chapter quality report
            style_block = self._build_style_hints(chapter_number, project_dir)

            if not chapter.scenes:
                chapter.scenes.append(self._default_scene())

            ordered_scenes = sorted(chapter.scenes, key=lambda s: s.scene_number)
            scene_contents: list[str] = []

            for scene in ordered_scenes:
                console.print(f"  Scene {scene.scene_number}/{len(ordered_scenes)}...")

                scene_content = self._write_scene(
                    scene=scene,
                    chapter=chapter,
                    chapter_number=chapter_number,
                    project_knowledge_base=project_knowledge_base,
                    ordered_scenes=ordered_scenes,
                    checker=checker,
                    style_block=style_block,
                )
                scene_contents.append(scene_content)

            chapter_content = f"## Chapter {chapter_number}: {chapter.title}\n\n"
            chapter_content += "\n\n".join(scene_contents)

            if output_path is None:
                _dir: Path = project_dir if project_dir is not None else Path(".")
                output_path = str(_dir / f"chapter_{chapter_number}.md")
            write_markdown_file(output_path, chapter_content)

            console.print(f"[green]Chapter {chapter_number} done ({len(ordered_scenes)} scenes).[/green]")

            # Update narrative graph after chapter is fully written
            if project_dir and self.llm_client:
                try:
                    builder = NarrativeGraphBuilder(self.llm_client, project_dir, project_knowledge_base)
                    new_facts = builder.extract_from_chapter(chapter_number)
                    self.logger.info(
                        "Extracted %d new narrative facts from chapter %d.", len(new_facts), chapter_number
                    )
                except Exception:
                    self.logger.exception(
                        "Narrative graph update failed for chapter %d; existing graph preserved.", chapter_number
                    )

        except Exception as e:
            self.logger.exception("Error writing chapter %d: %s", chapter_number, e)
            console.print(f"[red]ERROR: Failed to write chapter {chapter_number}. See log for details.[/red]")

    # ------------------------------------------------------------------
    # Option A: Preventive style injection from prior chapter quality report
    # ------------------------------------------------------------------

    def _build_style_hints(self, chapter_number: int, project_dir: Optional[Path]) -> str:
        """Return a STYLE CONSTRAINTS block from quality_chapter_{N-1}.json, or empty string."""
        if chapter_number <= 1 or project_dir is None:
            return ""

        prior_quality_path = project_dir / f"quality_chapter_{chapter_number - 1}.json"
        if not prior_quality_path.exists():
            return ""

        try:
            data = json.loads(prior_quality_path.read_text(encoding="utf-8"))
            axes = data.get("axes", [])
        except Exception:
            self.logger.exception("Could not read prior quality report %s.", prior_quality_path)
            return ""

        hints: list[str] = []
        for axis in axes:
            score = axis.get("score", 1.0)
            if score >= _STYLE_HINT_THRESHOLD:
                continue
            name = axis.get("name", "")
            recommendation = axis.get("recommendation", "").strip()
            excerpts = axis.get("flagged_excerpts", [])
            if recommendation:
                hints.append(f"- [{name}] {recommendation}")
            for excerpt in excerpts[:2]:
                hints.append(f'  Avoid phrases like: "{excerpt}"')

        if not hints:
            return ""

        block = "STYLE CONSTRAINTS (patterns to avoid from prior chapter quality analysis):\n"
        block += "\n".join(hints)
        return block

    # ------------------------------------------------------------------
    # Scene writing with Option B: reactive rewrite loop
    # ------------------------------------------------------------------

    def _write_scene(
        self,
        scene: Scene,
        chapter: Chapter,
        chapter_number: int,
        project_knowledge_base: ProjectKnowledgeBase,
        ordered_scenes: list,
        checker: InvariantChecker,
        style_block: str,
    ) -> str:
        """Build prompt, generate scene, optionally rewrite if quality is below threshold."""
        violations = checker.check_scene(scene, chapter_number, project_knowledge_base)
        for v in violations:
            if v.severity == "hard":
                console.print(
                    f"[yellow]INVARIANT WARNING[/yellow] ch{chapter_number} scene {scene.scene_number}: {v.description}"
                )

        constraint_block = checker.format_violations_for_prompt(violations)
        scene_title = self._scene_title(scene)

        scene_prompt = prompts.SCENE_PROMPT.format(
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            book_title=project_knowledge_base.title,
            genre=project_knowledge_base.genre,
            category=project_knowledge_base.category,
            language=project_knowledge_base.language,
            tone=project_knowledge_base.tone,
            target_audience=project_knowledge_base.target_audience,
            chapter_summary=chapter.summary,
            scene_number=scene.scene_number,
            scene_summary=scene.summary,
            characters=", ".join(scene.characters) if scene.characters else "None specified",
            setting=scene.setting or "None specified",
            goal=scene.goal or "None specified",
            emotional_beat=scene.emotional_beat or "None specified",
            total_scenes=len(ordered_scenes),
        )

        # Prepend constraint blocks (invariants first, then style hints)
        dq = project_knowledge_base.dynamic_questions
        dq_block = ""
        if dq:
            dq_lines = "\n".join(f"  - {q}: {a}" for q, a in dq.items())
            dq_block = "GENRE-SPECIFIC AUTHOR DETAILS:\n" + dq_lines
        prefix_parts = [p for p in [constraint_block, style_block, dq_block] if p]
        if prefix_parts:
            scene_prompt = "\n\n".join(prefix_parts) + "\n\n" + scene_prompt

        scene_prompt += f"\n\nIMPORTANT: Begin the scene with the title: **{scene_title}**"

        scene_content = self.llm_client.generate_content(scene_prompt, max_tokens=2000)
        if not scene_content:
            self.logger.warning("Empty scene content for ch%d scene %d.", chapter_number, scene.scene_number)
            scene_content = f"[Scene {scene.scene_number} content unavailable]"
        elif not scene_content.startswith(f"**{scene_title}**") and not scene_content.startswith(f"# {scene_title}"):
            scene_content = f"**{scene_title}**\n\n{scene_content}"

        # Option B: reactive quality check and rewrite
        scene_content = self._maybe_rewrite_scene(
            scene_content=scene_content,
            chapter_number=chapter_number,
            scene_number=scene.scene_number,
        )

        return scene_content

    def _maybe_rewrite_scene(
        self, scene_content: str, chapter_number: int, scene_number: int
    ) -> str:
        """Score the scene; if below threshold, attempt one targeted rewrite. Never raises."""
        label = f"ch{chapter_number}_scene{scene_number}"
        try:
            from libriscribe.agents.content_quality import ContentQualityAgent

            qa = ContentQualityAgent(self.llm_client)
            report = qa.score_prose(scene_content, scene_label=label)
        except Exception:
            self.logger.exception("Quality scoring failed for %s; keeping original.", label)
            return scene_content

        if report is None or report.overall_score >= _QUALITY_REWRITE_THRESHOLD:
            if report:
                self.logger.debug(
                    "Scene %s quality OK (%.3f >= %.2f).", label, report.overall_score, _QUALITY_REWRITE_THRESHOLD
                )
            return scene_content

        self.logger.info(
            "Scene %s quality %.3f < %.2f — attempting rewrite.", label, report.overall_score, _QUALITY_REWRITE_THRESHOLD
        )
        console.print(
            f"  [yellow]Quality {report.overall_score:.2f} < {_QUALITY_REWRITE_THRESHOLD} — rewriting scene {scene_number}...[/yellow]"
        )

        # Build concise problem list from lowest-scoring axes
        low_axes = sorted(report.axes, key=lambda a: a.score)[:3]
        problem_lines: list[str] = []
        for axis in low_axes:
            if axis.score >= _QUALITY_REWRITE_THRESHOLD:
                break
            problem_lines.append(f"- {axis.name} (score {axis.score:.2f}): {axis.recommendation}")
            for excerpt in axis.flagged_excerpts[:2]:
                problem_lines.append(f'  Example to rewrite: "{excerpt}"')

        if not problem_lines:
            return scene_content

        rewrite_prompt = _REWRITE_PROMPT.format(
            problems="\n".join(problem_lines),
            scene_content=scene_content,
        )

        try:
            rewritten = self.llm_client.generate_content(rewrite_prompt, max_tokens=2000)
        except Exception:
            self.logger.exception("Rewrite LLM call failed for %s; keeping original.", label)
            return scene_content

        if not rewritten or len(rewritten.strip()) < len(scene_content) // 2:
            self.logger.warning("Rewrite output too short for %s; keeping original.", label)
            return scene_content

        self.logger.info("Rewrite complete for %s.", label)
        return rewritten

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_narrative_graph(
        self, project_dir: Optional[Path], project_name: str
    ) -> NarrativeGraph:
        if project_dir is None:
            return NarrativeGraph.empty(project_name)
        graph_path = project_dir / "narrative_graph.json"
        if not graph_path.exists():
            return NarrativeGraph.empty(project_name)
        try:
            return NarrativeGraph.load(graph_path)
        except Exception:
            self.logger.exception("Could not load narrative graph; using empty graph.")
            return NarrativeGraph.empty(project_name)

    def _get_or_create_chapter(
        self, pkb: ProjectKnowledgeBase, chapter_number: int
    ) -> Chapter:
        chapter = pkb.get_chapter(chapter_number)
        if chapter:
            return chapter
        console.print(f"[red]Chapter {chapter_number} not found in knowledge base.[/red]")
        chapter = Chapter(
            chapter_number=chapter_number,
            title=f"Chapter {chapter_number}",
            summary="A new chapter in the unfolding story.",
        )
        chapter.scenes.append(self._default_scene())
        pkb.add_chapter(chapter)
        console.print(f"[yellow]Created default chapter {chapter_number}.[/yellow]")
        return chapter

    @staticmethod
    def _default_scene() -> Scene:
        return Scene(
            scene_number=1,
            summary="The story continues with new developments.",
            characters=[],
            setting="Unknown",
            goal="Advance the plot",
            emotional_beat="Tension",
        )

    @staticmethod
    def _scene_title(scene: Scene) -> str:
        summary = scene.summary
        return (
            f"Scene {scene.scene_number}: {summary[:30]}..."
            if len(summary) > 30
            else f"Scene {scene.scene_number}: {summary}"
        )
