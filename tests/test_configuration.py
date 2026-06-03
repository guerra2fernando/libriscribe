import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.configuration import build_project_knowledge_base, load_expert_config


class ExpertConfigurationTests(unittest.TestCase):
    def test_load_expert_config_normalizes_fallback_settings(self):
        config_text = """
version: 1
project:
  project_name: fallback-demo
  title: Demo
  category: Fiction
  genre: Fantasy
  description: Demo description
  num_chapters: "4"
  llm_provider: openai
  model: gpt-4o-mini
  fallback_chain: claude, openrouter/anthropic/claude-3-haiku
  agent_fallback_chains:
    outliner: google_ai_studio, mistral/mistral-large-latest
workflow:
  chapter_writing: auto
""".strip()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "expert.yaml"
            path.write_text(config_text, encoding="utf-8")

            config = load_expert_config(str(path))

        self.assertEqual(
            config.project.fallback_chain,
            ["claude", "openrouter/anthropic/claude-3-haiku"],
        )
        self.assertEqual(
            config.project.agent_fallback_chains["outliner"],
            ["google_ai_studio", "mistral/mistral-large-latest"],
        )

    def test_build_project_knowledge_base_keeps_fallback_fields(self):
        config_text = """
{
  "version": 1,
  "project": {
    "project_name": "kb-demo",
    "title": "Demo",
    "category": "Fiction",
    "genre": "Fantasy",
    "description": "Demo description",
    "num_chapters": "3",
    "llm_provider": "openai",
    "model": "gpt-4o-mini",
    "fallback_chain": ["claude", "openrouter/anthropic/claude-3-haiku"],
    "agent_fallback_chains": {
      "editor": ["openai/gpt-4o"]
    }
  }
}
""".strip()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "expert.json"
            path.write_text(config_text, encoding="utf-8")
            config = load_expert_config(str(path))

        knowledge_base = build_project_knowledge_base(config)
        self.assertEqual(
            knowledge_base.fallback_chain,
            ["claude", "openrouter/anthropic/claude-3-haiku"],
        )
        self.assertEqual(
            knowledge_base.agent_fallback_chains,
            {"editor": ["openai/gpt-4o"]},
        )


if __name__ == "__main__":
    unittest.main()
