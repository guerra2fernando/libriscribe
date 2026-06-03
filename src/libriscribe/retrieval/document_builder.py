from __future__ import annotations

# src/libriscribe/retrieval/document_builder.py

import hashlib
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libriscribe.knowledge_base import ProjectKnowledgeBase

from libriscribe.retrieval.models import RetrievalDocument
from libriscribe.retrieval.metadata import extract_characters, extract_locations, extract_tags_and_themes


def compute_sha256(text: str) -> str:
    """Computes the SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentBuilder:
    """Assembles searchable RetrievalDocument instances from a ProjectKnowledgeBase and markdown files."""

    def __init__(self, kb: ProjectKnowledgeBase, project_dir: Path):
        self.kb = kb
        self.project_dir = project_dir
        # Cache entities for metadata enrichment
        self.all_character_names = list(kb.characters.keys())
        self.all_locations = []
        if kb.worldbuilding and hasattr(kb.worldbuilding, "key_locations"):
            locs_text = kb.worldbuilding.key_locations or ""
            # Simple line or comma splits
            self.all_locations = [
                l.strip()
                for l in locs_text.replace("\n", ",").split(",")
                if l.strip()
            ]

    def build_all(self) -> list[RetrievalDocument]:
        """Assembles all configured source documents."""
        documents = []

        # 1. Project Metadata
        metadata_doc = self._build_project_metadata()
        if metadata_doc:
            documents.append(metadata_doc)

        # 2. Outline
        outline_doc = self._build_outline()
        if outline_doc:
            documents.append(outline_doc)

        # 3. Characters
        documents.extend(self._build_characters())

        # 4. Worldbuilding
        documents.extend(self._build_worldbuilding())

        # 5. Chapter & Scene Summaries
        documents.extend(self._build_chapters_and_scenes())

        # 6. Chapter markdown texts
        documents.extend(self._build_chapter_prose_files())

        return documents

    def _create_doc(
        self,
        doc_id: str,
        source_type: str,
        title: str,
        text: str,
        *,
        source_path: str | None = None,
        chapter_number: int | None = None,
        scene_number: int | None = None,
        entity_name: str | None = None,
        tags: list[str] | None = None,
    ) -> RetrievalDocument:
        """Helper to construct a RetrievalDocument with auto-enriched entities/tags."""
        tags = tags or []
        doc_hash = compute_sha256(text)
        updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Extract matches
        chars = extract_characters(text, self.all_character_names)
        locs = extract_locations(text, self.all_locations)
        themes = extract_tags_and_themes(text)

        return RetrievalDocument(
            document_id=doc_id,
            project_name=self.kb.project_name,
            source_type=source_type,
            title=title,
            text=text,
            source_path=source_path,
            chapter_number=chapter_number,
            scene_number=scene_number,
            entity_name=entity_name,
            tags=tags,
            characters=chars,
            locations=locs,
            themes=themes,
            updated_at=updated_at,
            hash=doc_hash,
        )

    def _build_project_metadata(self) -> RetrievalDocument | None:
        lines = [
            f"Title: {self.kb.title}",
            f"Genre: {self.kb.genre}",
            f"Category: {self.kb.category}",
            f"Description: {self.kb.description}",
            f"Logline: {self.kb.logline}",
            f"Tone: {self.kb.tone}",
            f"Target Audience: {self.kb.target_audience}",
        ]
        text = "\n".join(lines)
        if not text.strip():
            return None
        return self._create_doc(
            "project_metadata",
            "project_metadata",
            "Project Metadata",
            text,
            tags=["metadata", "config"],
        )

    def _build_outline(self) -> RetrievalDocument | None:
        if not self.kb.outline or not self.kb.outline.strip():
            return None
        return self._create_doc(
            "project_outline",
            "outline",
            "Project Outline",
            self.kb.outline,
            tags=["outline", "plot"],
        )

    def _build_characters(self) -> list[RetrievalDocument]:
        docs = []
        for name, char in self.kb.characters.items():
            lines = [
                f"Name: {char.name}",
                f"Role: {char.role}",
                f"Age: {char.age}",
                f"Physical Description: {char.physical_description}",
                f"Personality Traits: {char.personality_traits}",
                f"Background: {char.background}",
                f"Motivations: {char.motivations}",
                f"Internal Conflicts: {char.internal_conflicts}",
                f"External Conflicts: {char.external_conflicts}",
                f"Character Arc: {char.character_arc}",
            ]
            if char.relationships:
                lines.append("Relationships:")
                for rel_char, rel_desc in char.relationships.items():
                    lines.append(f"  - {rel_char}: {rel_desc}")

            text = "\n".join(lines)
            docs.append(
                self._create_doc(
                    f"char_{name.replace(' ', '_').lower()}",
                    "character_profile",
                    f"Character Profile - {char.name}",
                    text,
                    entity_name=char.name,
                    tags=["character", "profile"],
                )
            )
        return docs

    def _build_worldbuilding(self) -> list[RetrievalDocument]:
        docs = []
        wb = self.kb.worldbuilding
        if not wb:
            return docs

        # Iterate over all non-empty worldbuilding fields
        for field, value in wb.model_dump().items():
            if value and isinstance(value, str) and value.strip():
                docs.append(
                    self._create_doc(
                        f"world_{field}",
                        "worldbuilding",
                        f"Worldbuilding - {field.replace('_', ' ').title()}",
                        value,
                        tags=["worldbuilding", field],
                    )
                )
        return docs

    def _build_chapters_and_scenes(self) -> list[RetrievalDocument]:
        docs = []
        for ch_num, chapter in self.kb.chapters.items():
            if chapter.summary and chapter.summary.strip():
                docs.append(
                    self._create_doc(
                        f"chapter_{ch_num}_summary",
                        "chapter_summary",
                        f"Chapter {ch_num} Summary - {chapter.title}",
                        chapter.summary,
                        chapter_number=ch_num,
                        tags=["chapter", "summary"],
                    )
                )

            for scene in chapter.scenes:
                if scene.summary and scene.summary.strip():
                    lines = [
                        f"Scene Number: {scene.scene_number}",
                        f"Setting: {scene.setting}",
                        f"Goal: {scene.goal}",
                        f"Emotional Beat: {scene.emotional_beat}",
                        f"Characters involved: {', '.join(scene.characters)}",
                        f"Summary: {scene.summary}",
                    ]
                    text = "\n".join(lines)
                    docs.append(
                        self._create_doc(
                            f"chapter_{ch_num}_scene_{scene.scene_number}_summary",
                            "scene_summary",
                            f"Chapter {ch_num} Scene {scene.scene_number} Summary",
                            text,
                            chapter_number=ch_num,
                            scene_number=scene.scene_number,
                            tags=["scene", "summary"],
                        )
                    )
        return docs

    def _build_chapter_prose_files(self) -> list[RetrievalDocument]:
        docs = []
        # Find any chapter_{n}.md or chapter_{n}_revised.md files in the project_dir
        if not self.project_dir.exists():
            return docs

        # Find markdown files
        for path in self.project_dir.glob("chapter_*.md"):
            # Exclude formatted manuscripts or other docs
            filename = path.name
            if filename.startswith("chapter_") and not filename.endswith("_original.md"):
                # Parse chapter number
                parts = filename.split("_")
                try:
                    ch_num = int(parts[1].split(".")[0])
                except (ValueError, IndexError):
                    continue

                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    continue

                if text.strip():
                    source_type = "chapter_text"
                    title = f"Chapter {ch_num} Full Text"
                    is_revised = "revised" in filename
                    tags = ["chapter", "prose"]
                    if is_revised:
                        tags.append("revised")
                        title += " (Revised)"

                    docs.append(
                        self._create_doc(
                            f"prose_{filename.replace('.', '_')}",
                            source_type,
                            title,
                            text,
                            source_path=str(path),
                            chapter_number=ch_num,
                            tags=tags,
                        )
                    )
        return docs
