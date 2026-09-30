"""External prompt template loader for LibriScribe."""
import os
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


class PromptLoader:
    """Loads and manages external prompt templates."""

    def __init__(self, prompts_dir: str | os.PathLike[str] | None = None):
        configured_dir = prompts_dir or os.getenv("LIBRISCRIBE_PROMPTS_DIR") or "prompts"
        self.prompts_dir = Path(configured_dir)
        self.templates_dir = self.prompts_dir / "templates"
        self.configs_dir = self.prompts_dir / "configs"
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _packaged_template(prompt_name: str) -> resources.abc.Traversable:
        return resources.files("libriscribe.prompt_templates").joinpath(
            f"{prompt_name}.yml"
        )

    def load_prompt(self, prompt_name: str) -> dict[str, Any]:
        """Load prompt template from YAML file."""
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        template_path = self.templates_dir / f"{prompt_name}.yml"
        if template_path.exists():
            prompt_text = template_path.read_text(encoding="utf-8")
        else:
            packaged_template = self._packaged_template(prompt_name)
            if not packaged_template.is_file():
                raise FileNotFoundError(f"Prompt template not found: {template_path}")
            prompt_text = packaged_template.read_text(encoding="utf-8")

        prompt_data = yaml.safe_load(prompt_text)

        self._cache[prompt_name] = prompt_data
        return prompt_data

    def get_template(self, prompt_name: str) -> str:
        """Get the template string for a prompt."""
        prompt_data = self.load_prompt(prompt_name)
        return prompt_data["template"]

    def get_settings(self, prompt_name: str) -> dict[str, Any]:
        """Get the settings for a prompt."""
        prompt_data = self.load_prompt(prompt_name)
        return prompt_data.get("settings", {})

    def list_prompts(self) -> list[str]:
        """List all available prompt templates."""
        names = {f.stem for f in self.templates_dir.glob("*.yml")}
        packaged_templates = resources.files("libriscribe.prompt_templates")
        names.update(
            path.name.removesuffix(".yml")
            for path in packaged_templates.iterdir()
            if path.name.endswith(".yml")
        )
        return sorted(names)
