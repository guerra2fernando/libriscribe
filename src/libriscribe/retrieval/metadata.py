# src/libriscribe/retrieval/metadata.py

import re


def clean_text_for_matching(text: str) -> str:
    """Cleans text to make keyword matching robust."""
    return re.sub(r"\s+", " ", text).strip()


def extract_characters(text: str, character_names: list[str]) -> list[str]:
    """Finds all character names that appear in the given text.

    Performs case-sensitive exact word-boundary matching.
    """
    if not text or not character_names:
        return []

    found = []
    # Avoid compiling regex for empty or super short names to avoid issues
    for name in character_names:
        if not name or len(name) < 2:
            continue
        # Use word boundaries
        pattern = r"\b" + re.escape(name) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(name)
    return found


def extract_locations(text: str, locations: list[str]) -> list[str]:
    """Finds all locations that appear in the given text."""
    if not text or not locations:
        return []

    found = []
    for loc in locations:
        if not loc or len(loc) < 2:
            continue
        pattern = r"\b" + re.escape(loc) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(loc)
    return found


def extract_tags_and_themes(text: str) -> list[str]:
    """Heuristically extracts potential theme/tag keywords from a chunk of text."""
    # We can start with a simple placeholder or a small vocabulary of common themes
    themes = ["conflict", "secrets", "alliance", "betrayal", "magic", "journey", "lore"]
    found = []
    text_lower = text.lower()
    for theme in themes:
        if theme in text_lower:
            found.append(theme)
    return found
