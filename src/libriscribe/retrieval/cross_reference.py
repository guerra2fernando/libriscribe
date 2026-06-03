# src/libriscribe/retrieval/cross_reference.py

import json
from pathlib import Path
from typing import Any, Dict, List
from libriscribe.retrieval.models import RetrievalChunk, CrossReferenceEntry


class CrossReferenceIndex:
    """Builds and queries the local entity relationship (cross-reference) JSON index."""

    def __init__(self):
        self.entities: Dict[str, CrossReferenceEntry] = {}

    def build(self, chunks: List[RetrievalChunk], entity_definitions: Dict[str, str]) -> None:
        """Builds cross-references by scanning chunk texts for defined entities.

        entity_definitions maps entity_name -> entity_type (e.g., {"Mira Thorn": "character"}).
        """
        self.entities = {}

        # Initialize entries
        for name, etype in entity_definitions.items():
            self.entities[name] = CrossReferenceEntry(
                entity_name=name,
                entity_type=etype,
                referenced_in_chunks=[],
                referenced_in_chapters=[],
                related_entities=[],
            )

        # Scan chunks
        for chunk in chunks:
            chunk_text = chunk.text
            found_entities_in_chunk = []

            # Check which entities are present in this chunk
            for name, entry in self.entities.items():
                # Avoid trivial matches
                if len(name) < 2:
                    continue

                # Case-insensitive word boundary check
                import re
                pattern = r"\b" + re.escape(name) + r"\b"
                if re.search(pattern, chunk_text, re.IGNORECASE):
                    found_entities_in_chunk.append(name)
                    # Add reference
                    if chunk.chunk_id not in entry.referenced_in_chunks:
                        entry.referenced_in_chunks.append(chunk.chunk_id)
                    if chunk.chapter_number is not None and chunk.chapter_number not in entry.referenced_in_chapters:
                        entry.referenced_in_chapters.append(chunk.chapter_number)

            # Link related entities (entities that co-occur in the same chunk)
            for name in found_entities_in_chunk:
                entry = self.entities[name]
                for other_name in found_entities_in_chunk:
                    if name != other_name:
                        if other_name not in entry.related_entities:
                            entry.related_entities.append(other_name)

        # Sort references for clean presentation
        for entry in self.entities.values():
            entry.referenced_in_chapters.sort()
            entry.related_entities.sort()

    def lookup(self, entity_name: str) -> CrossReferenceEntry | None:
        """Looks up an entity by name."""
        # Simple case-insensitive match
        for name, entry in self.entities.items():
            if name.lower() == entity_name.lower():
                return entry
        return None

    def save_to_file(self, file_path: Path) -> None:
        """Saves the cross-reference index to a JSON file."""
        data = {
            "entities": {
                name: entry.model_dump(mode="json")
                for name, entry in self.entities.items()
            }
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self, file_path: Path) -> None:
        """Loads the cross-reference index from a JSON file."""
        if not file_path.exists():
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.entities = {}
        for name, item_data in data.get("entities", {}).items():
            self.entities[name] = CrossReferenceEntry.model_validate(item_data)
