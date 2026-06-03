import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.utils.llm_client import LLMClient


class ScriptedLLMClient(LLMClient):
    def __init__(self, scripts, fallback_chain=None):
        self.settings = SimpleNamespace(
            openai_model="gpt-4o-mini",
            claude_model="claude-3-5-sonnet",
            google_ai_studio_model="gemini-2.5-flash",
            deepseek_model="deepseek-chat",
            mistral_model="mistral-large-latest",
            openrouter_model="anthropic/claude-3-haiku",
            fallback_chain="",
        )
        self.llm_provider = "openai"
        self._client_cache = {}
        self.client = None
        self.default_model = "gpt-4o-mini"
        self.model = "gpt-4o-mini"
        self.cost_tracker = Mock()
        self.request_fallback_chain = fallback_chain
        self.scripts = {key: list(value) for key, value in scripts.items()}
        self.calls = []

    def _generate_once(self, route, prompt, max_tokens, temperature):
        self.calls.append((route.provider, route.model, prompt))
        key = (route.provider, route.model)
        result = self.scripts[key].pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class LLMFallbackTests(unittest.TestCase):
    def test_timeout_falls_back_to_next_route(self):
        client = ScriptedLLMClient(
            {
                ("openai", "gpt-4o-mini"): [
                    requests.Timeout("timed out"),
                    requests.Timeout("timed out again"),
                ],
                ("claude", "claude-3-5-sonnet"): ["fallback success"],
            },
            fallback_chain=["claude"],
        )

        response = client.generate_content("hello")

        self.assertEqual(response, "fallback success")
        self.assertEqual(
            [provider for provider, _, _ in client.calls],
            ["openai", "openai", "claude"],
        )

    def test_invalid_json_after_repair_falls_back(self):
        client = ScriptedLLMClient(
            {
                ("openai", "gpt-4o-mini"): [
                    "not valid json",
                    "still not valid json",
                ],
                (
                    "google_ai_studio",
                    "gemini-2.5-flash",
                ): ['```json\n{"ok": true}\n```'],
            },
            fallback_chain=["google_ai_studio"],
        )

        response = client.generate_content_with_json_repair("return json")

        self.assertEqual(response, '```json\n{"ok": true}\n```')
        self.assertEqual(
            [provider for provider, _, _ in client.calls],
            ["openai", "openai", "google_ai_studio"],
        )


if __name__ == "__main__":
    unittest.main()
