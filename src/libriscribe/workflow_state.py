from dataclasses import dataclass
from pathlib import Path

from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils.file_utils import get_existing_chapter_numbers, is_nonempty_file
from libriscribe.utils.project_status import get_interrupted_stage, load_project_status


@dataclass(frozen=True)
class ProjectProgress:
    concept_complete: bool
    outline_complete: bool
    characters_required: bool
    characters_complete: bool
    worldbuilding_required: bool
    worldbuilding_complete: bool
    chapter_numbers_complete: list[int]
    missing_chapters: list[int]
    manuscript_exists: bool
    next_step: str
    interrupted_stage: str | None
    stage_statuses: dict[str, str]


def has_concept_data(project_knowledge_base: ProjectKnowledgeBase) -> bool:
    return bool(project_knowledge_base.logline.strip()) and (
        project_knowledge_base.logline != "No logline available"
    )


def has_outline_data(
    project_dir: Path | None, project_knowledge_base: ProjectKnowledgeBase
) -> bool:
    if project_knowledge_base.outline.strip() or project_knowledge_base.chapters:
        return True
    if not project_dir:
        return False
    return is_nonempty_file(project_dir / "outline.md")


def has_character_data(
    project_dir: Path | None, project_knowledge_base: ProjectKnowledgeBase
) -> bool:
    if project_knowledge_base.characters:
        return True
    if not project_dir:
        return False
    return is_nonempty_file(project_dir / "characters.json")


def has_worldbuilding_data(
    project_dir: Path | None, project_knowledge_base: ProjectKnowledgeBase
) -> bool:
    worldbuilding = project_knowledge_base.worldbuilding
    if worldbuilding and any(
        isinstance(value, str) and value.strip()
        for value in worldbuilding.model_dump().values()
    ):
        return True
    if not project_dir:
        return False
    return is_nonempty_file(project_dir / "world.json")


def get_expected_chapter_numbers(
    project_knowledge_base: ProjectKnowledgeBase,
) -> list[int]:
    num_chapters = project_knowledge_base.get("num_chapters", 1)
    if isinstance(num_chapters, tuple):
        num_chapters = num_chapters[1]
    if not isinstance(num_chapters, int) or num_chapters < 1:
        return []
    return list(range(1, num_chapters + 1))


def inspect_project_progress(
    project_dir: Path | None, project_knowledge_base: ProjectKnowledgeBase
) -> ProjectProgress:
    interrupted_stage = None
    stage_statuses: dict[str, str] = {}
    if project_dir:
        payload = load_project_status(project_dir)
        stages = payload.get("stages", {})
        if isinstance(stages, dict):
            stage_statuses = {
                stage_name: str(stage_payload.get("status", "pending"))
                for stage_name, stage_payload in stages.items()
                if isinstance(stage_payload, dict)
            }
        interrupted_stage = get_interrupted_stage(project_dir)

    outline_complete = has_outline_data(project_dir, project_knowledge_base) or (
        stage_statuses.get("outline") == "complete"
    )
    concept_complete = (
        has_concept_data(project_knowledge_base)
        or outline_complete
        or stage_statuses.get("concept") == "complete"
    )

    characters_required = project_knowledge_base.get("num_characters", 0) > 0
    characters_complete = (
        (not characters_required)
        or has_character_data(project_dir, project_knowledge_base)
        or stage_statuses.get("characters") in {"complete", "skipped"}
    )

    worldbuilding_required = bool(
        project_knowledge_base.get("worldbuilding_needed", False)
    )
    worldbuilding_complete = (
        (not worldbuilding_required)
        or has_worldbuilding_data(project_dir, project_knowledge_base)
        or stage_statuses.get("worldbuilding") in {"complete", "skipped"}
    )

    expected_chapters = get_expected_chapter_numbers(project_knowledge_base)
    existing_chapters = get_existing_chapter_numbers(project_dir) if project_dir else []
    missing_chapters = [
        chapter_number
        for chapter_number in expected_chapters
        if chapter_number not in existing_chapters
    ]

    manuscript_exists = False
    if project_dir:
        manuscript_exists = (
            any(
                is_nonempty_file(project_dir / filename)
                for filename in (
                    "manuscript.md",
                    "manuscript.pdf",
                    "manuscript_original.md",
                    "manuscript_original.pdf",
                )
            )
            or stage_statuses.get("formatting") == "complete"
        )

    if not concept_complete:
        next_step = "concept"
    elif not outline_complete:
        next_step = "outline"
    elif not characters_complete:
        next_step = "characters"
    elif not worldbuilding_complete:
        next_step = "worldbuilding"
    elif missing_chapters:
        next_step = "chapters"
    elif not manuscript_exists:
        next_step = "formatting"
    else:
        next_step = "complete"

    return ProjectProgress(
        concept_complete=concept_complete,
        outline_complete=outline_complete,
        characters_required=characters_required,
        characters_complete=characters_complete,
        worldbuilding_required=worldbuilding_required,
        worldbuilding_complete=worldbuilding_complete,
        chapter_numbers_complete=existing_chapters,
        missing_chapters=missing_chapters,
        manuscript_exists=manuscript_exists,
        next_step=next_step,
        interrupted_stage=interrupted_stage,
        stage_statuses=stage_statuses,
    )
