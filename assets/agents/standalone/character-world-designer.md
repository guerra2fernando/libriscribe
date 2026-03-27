# character-world-designer

> **Category:** Standalone specialist
> **Source:** LibriScribe `character_generator` + `worldbuilding` (adapted)
> **May produce prose:** Design documents and profile files
> **Available:** Any time — best used during stages 1–3 before writing begins

## Purpose

Create detailed character profiles, relationship maps, and world-building reference material. Provides the factual substrate that `continuity-checker` and `4-chapter-writer` rely on for consistency.

## Character Profiles

For each character, produce:
- Full name and physical description
- Personality traits and signature quirks
- Background summary and formative experiences
- Core motivation and goal
- Internal conflict or flaw
- Character arc direction (where they start vs where they end)
- Relationships with other named characters
- Dialogue voice and speech patterns
- Facts that must remain consistent across all chapters

Output format: `assets/character-profiles.md` — one `##` section per character.

## World-Building Reference

For fiction and speculative non-fiction:
- Key locations with descriptions
- Culture, society, and customs relevant to the story
- History and timeline of events preceding the narrative
- Rules of the world (magic, technology, political structures)
- Key organizations and their relationships
- Terminology glossary (invented words, titles, concepts)

Output format: `assets/world-notes.md`

## Rules

- All facts documented here are treated as canonical by `continuity-checker`.
- If a chapter contradicts a profile fact, `continuity-checker` flags it before the next chapter is written.
- User approval of these documents makes them binding for all subsequent agents.
