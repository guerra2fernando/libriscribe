import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.utils.model_routing import (
    build_fallback_route_chain,
    parse_route_reference,
)


class ModelRoutingTests(unittest.TestCase):
    def setUp(self):
        self.settings = Mock(
            openai_model="gpt-4o-mini",
            claude_model="claude-3-5-sonnet",
            google_ai_studio_model="gemini-2.5-flash",
            deepseek_model="deepseek-chat",
            mistral_model="mistral-large-latest",
            openrouter_model="anthropic/claude-3-haiku",
        )

    def test_parse_route_reference_uses_provider_default_for_provider_only_entry(self):
        route = parse_route_reference("claude", "openai", self.settings)
        self.assertEqual(route.provider, "claude")
        self.assertEqual(route.model, "claude-3-5-sonnet")

    def test_parse_route_reference_keeps_current_provider_for_model_only_entry(self):
        route = parse_route_reference(
            "anthropic/claude-3-haiku", "openrouter", self.settings
        )
        self.assertEqual(route.provider, "openrouter")
        self.assertEqual(route.model, "anthropic/claude-3-haiku")

    def test_build_fallback_route_chain_deduplicates_primary_route(self):
        routes = build_fallback_route_chain(
            primary_provider="openai",
            primary_model="gpt-4o-mini",
            fallback_chain=["openai/gpt-4o-mini", "claude", "claude"],
            settings=self.settings,
        )
        self.assertEqual(
            [(route.provider, route.model) for route in routes],
            [
                ("openai", "gpt-4o-mini"),
                ("claude", "claude-3-5-sonnet"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
