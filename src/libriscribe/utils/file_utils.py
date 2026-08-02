# src/libriscribe/utils/file_utils.py

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Generic type for Pydantic models
T = TypeVar("T", bound=BaseModel)


def read_json_file(
    file_path: str, model: Optional[Type[T]] = None
) -> Union[dict[str, Any], T, None]:
    """Reads a JSON file, optionally validating it against a Pydantic model."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if model:
                try:
                    return model.model_validate(data)
                except ValidationError as e:
                    logger.error("JSON validation error in %s: %s", file_path, e)
                    return None
            return data
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        return None
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in %s", file_path)
        return None
    except Exception:
        logger.exception("Error reading JSON file %s", file_path)
        return None


def write_json_file(
    file_path: str, data: Union[dict[str, Any], BaseModel]
) -> None:
    """Writes data (dict or Pydantic model) to a JSON file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(data, BaseModel):
                json.dump(data.model_dump(), f, indent=4)
            else:
                json.dump(data, f, indent=4)
        logger.info("Data written to %s", file_path)
    except Exception:
        logger.exception("Error writing to JSON file %s", file_path)


def read_markdown_file(file_path: str) -> str:
    """Reads a Markdown file and returns its content as a string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        return ""
    except Exception:
        logger.exception("Error reading Markdown file %s", file_path)
        return ""


def write_markdown_file(file_path: str, content: str) -> None:
    """Writes a string to a Markdown file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    except Exception:
        logger.exception("Error writing to Markdown file %s", file_path)


def is_nonempty_file(file_path: Union[str, Path]) -> bool:
    """Returns True when the file exists and contains non-whitespace content."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return False

    try:
        return bool(path.read_text(encoding="utf-8").strip())
    except UnicodeDecodeError:
        return path.stat().st_size > 0
    except Exception:
        logger.exception("Error checking file content for %s", path)
        return False


def _extract_chapter_number(filename: str) -> Optional[int]:
    match = re.match(r"chapter_(\d+)(?:_revised)?\.md$", filename)
    if not match:
        return None
    return int(match.group(1))


def get_existing_chapter_numbers(project_dir: Union[str, Path]) -> list[int]:
    """Gets sorted chapter numbers for non-empty original chapter files."""
    project_path = Path(project_dir)
    chapter_numbers = []

    if not project_path.exists():
        return chapter_numbers

    for path in project_path.iterdir():
        chapter_number = _extract_chapter_number(path.name)
        if chapter_number is None or path.name.endswith("_revised.md"):
            continue
        if is_nonempty_file(path):
            chapter_numbers.append(chapter_number)

    return sorted(set(chapter_numbers))


def get_chapter_files(project_dir: str) -> list[str]:
    """Gets a sorted list of original chapter files in the project directory."""
    project_path = Path(project_dir)
    chapter_files = []

    if not project_path.exists():
        return chapter_files

    for path in project_path.iterdir():
        chapter_number = _extract_chapter_number(path.name)
        if chapter_number is None or path.name.endswith("_revised.md"):
            continue
        if is_nonempty_file(path):
            chapter_files.append((chapter_number, str(path)))

    chapter_files.sort(key=lambda item: item[0])
    return [path for _, path in chapter_files]


def extract_json_from_markdown(markdown_text: str) -> Optional[dict[str, Any]]:
    """Extracts JSON from within Markdown code blocks, handling potential errors."""
    try:
        start = markdown_text.find("```json")
        if start == -1:
            return None

        start += len("```json")
        end = markdown_text.find("```", start)
        if end == -1:
            return None

        json_str = markdown_text[start:end].strip()
        return json.loads(json_str)

    except json.JSONDecodeError:
        return None
    except Exception:
        logger.exception("Error extracting JSON from Markdown")
        return None
