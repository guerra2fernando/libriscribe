"""Tests for multi-session brainstorm storage + migration (B18)."""
import json
import tempfile
import unittest
from pathlib import Path

import libriscribe.api.routers.chat as chat


class ChatSessionStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._orig = chat.get_projects_dir
        chat.get_projects_dir = lambda: self.tmp
        (self.tmp / "demo").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        chat.get_projects_dir = self._orig

    def test_seeds_default_general_session(self):
        sessions = chat._list_sessions("demo")
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "General")

    def test_migrates_legacy_history(self):
        # A legacy single-thread history exists.
        (self.tmp / "demo" / "chat_history.json").write_text(
            json.dumps([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]),
            encoding="utf-8",
        )
        sessions = chat._list_sessions("demo")
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "General")
        self.assertEqual(len(sessions[0]["messages"]), 2)

    def test_create_and_resolve_and_append(self):
        s = chat._new_session("Villain arc", focus={"type": "character", "name": "Mordecai"})
        chat._save_session("demo", s)
        chat._append_message("demo", s, "user", "what's his weakness?")
        loaded = chat._load_session("demo", s["id"])
        self.assertEqual(loaded["title"], "Villain arc")
        self.assertEqual(loaded["focus"]["name"], "Mordecai")
        self.assertEqual(loaded["messages"][0]["content"], "what's his weakness?")

    def test_resolve_specific_vs_default(self):
        default = chat._list_sessions("demo")[0]
        other = chat._new_session("Plot")
        other["created_at"] = "2099-01-01T00:00:00+00:00"  # explicitly newer than the seeded default
        chat._save_session("demo", other)
        self.assertEqual(chat._resolve_session("demo", other["id"])["id"], other["id"])
        # Unknown id falls back to the default (oldest) session.
        self.assertEqual(chat._resolve_session("demo", "nope1234")["id"], default["id"])

    def test_meta_strips_messages_and_counts(self):
        s = chat._new_session("X")
        chat._append_message("demo", s, "user", "a")
        meta = chat._session_meta(s)
        self.assertNotIn("messages", meta)
        self.assertEqual(meta["message_count"], 1)


class RollingMemoryTests(unittest.TestCase):
    class _FakeClient:
        def __init__(self):
            self.calls = 0
        def generate_content(self, prompt, **kw):
            self.calls += 1
            return "MEMORY: prior + new folded together"

    def setUp(self):
        from libriscribe.knowledge_base import ProjectKnowledgeBase
        self.tmp = Path(tempfile.mkdtemp())
        self._orig = chat.get_projects_dir
        chat.get_projects_dir = lambda: self.tmp
        (self.tmp / "demo").mkdir(parents=True, exist_ok=True)
        self.kb = ProjectKnowledgeBase(project_name="demo", title="Demo", genre="Fantasy")

    def tearDown(self):
        chat.get_projects_dir = self._orig

    def test_window_start_drops_old_and_build_from_start(self):
        history = [{"role": "user", "content": "word " * 150} for _ in range(20)]
        start = chat._window_start_index(history, 3000)
        self.assertGreater(start, 0)
        self.assertLess(start, len(history))
        convo = chat._build_conversation(history, start)
        self.assertTrue(convo.strip().endswith("Assistant:"))

    def test_summarizes_when_batch_reached(self):
        s = chat._new_session("Plot")
        s["messages"] = [{"role": "user" if i % 2 == 0 else "assistant", "content": "word " * 150} for i in range(20)]
        chat._save_session("demo", s)
        client = self._FakeClient()
        orig = chat._RECENT_WINDOW_TOKENS
        try:
            summary, start = chat._manage_session_memory("demo", self.kb, s, client)
        finally:
            chat._RECENT_WINDOW_TOKENS = orig
        self.assertTrue(summary)                       # a running summary was produced
        self.assertGreaterEqual(client.calls, 1)
        self.assertEqual(s["summarized_upto"], start)
        # persisted
        self.assertEqual(chat._load_session("demo", s["id"])["summary"], summary)

    def test_no_summary_for_short_session(self):
        s = chat._new_session("Plot")
        s["messages"] = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
        chat._save_session("demo", s)
        client = self._FakeClient()
        summary, start = chat._manage_session_memory("demo", self.kb, s, client)
        self.assertEqual(summary, "")
        self.assertEqual(client.calls, 0)              # nothing old enough to summarize
        self.assertEqual(start, 0)

    def test_new_session_has_memory_fields(self):
        s = chat._new_session("X")
        self.assertEqual(s["summary"], "")
        self.assertEqual(s["summarized_upto"], 0)


class BrainstormPrefsTests(unittest.TestCase):
    """Per-session prefs foundation + verbosity (B23) + collaborator preamble / intent lens (B26)."""
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._orig = chat.get_projects_dir
        chat.get_projects_dir = lambda: self.tmp
        (self.tmp / "demo").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        chat.get_projects_dir = self._orig

    def test_new_session_has_default_prefs(self):
        self.assertEqual(chat._new_session("X")["prefs"], {"verbosity": "medium"})

    def test_load_backfills_prefs_for_legacy_session(self):
        s = chat._new_session("L")
        del s["prefs"]                       # simulate a session saved before prefs existed
        chat._save_session("demo", s)
        self.assertEqual(chat._load_session("demo", s["id"])["prefs"], {"verbosity": "medium"})

    def test_session_meta_includes_prefs(self):
        self.assertEqual(chat._session_meta(chat._new_session("X"))["prefs"], {"verbosity": "medium"})

    def test_verbosity_levels_map_to_token_caps(self):
        self.assertEqual(chat._verbosity({"verbosity": "low"})["max_tokens"], 512)
        self.assertEqual(chat._verbosity({"verbosity": "high"})["max_tokens"], 4000)
        self.assertEqual(chat._verbosity(None)["max_tokens"], 1200)            # default medium
        self.assertEqual(chat._verbosity({"verbosity": "bogus"})["max_tokens"], 1200)  # unknown -> medium

    def test_max_tokens_override_supersedes_tier_cap(self):
        # An explicit numeric override wins over the verbosity tier's cap...
        self.assertEqual(chat._verbosity({"verbosity": "low", "max_tokens": 8000})["max_tokens"], 8000)
        # ...but keeps the tier's directive.
        self.assertEqual(
            chat._verbosity({"verbosity": "low", "max_tokens": 8000})["directive"],
            chat._VERBOSITY["low"]["directive"],
        )
        # Blank / zero / garbage overrides fall back to the tier cap.
        self.assertEqual(chat._verbosity({"verbosity": "high", "max_tokens": 0})["max_tokens"], 4000)
        self.assertEqual(chat._verbosity({"verbosity": "high", "max_tokens": None})["max_tokens"], 4000)
        self.assertEqual(chat._verbosity({"verbosity": "high", "max_tokens": "x"})["max_tokens"], 4000)
        # Overrides are clamped to a sane ceiling.
        self.assertEqual(chat._verbosity({"max_tokens": 999999})["max_tokens"], 32000)

    def test_prompts_carry_collaborator_and_verbosity_directive(self):
        from types import SimpleNamespace
        kb = SimpleNamespace(title="Book", genre="Sci-Fi")
        low = chat._VERBOSITY["low"]["directive"]
        gen = chat._system_prompt(kb, "(lore)", low)
        self.assertIn("sharp creative collaborator", gen)
        self.assertIn("ULTRA-CONCISE", gen)

    def test_focus_prompt_carries_intent_lens(self):
        from types import SimpleNamespace
        kb = SimpleNamespace(title="Book", genre="Sci-Fi")
        foc = chat._focus_system_prompt(kb, "character", "Maren", "(rec)", "(lore)", chat._VERBOSITY["high"]["directive"])
        self.assertIn("sharp creative collaborator", foc)
        self.assertIn("MOTIVATION", foc)     # character intent lens
        # a different type gets a different lens
        arc = chat._focus_system_prompt(kb, "arc", "Fall of X", "(rec)", "(lore)", chat._VERBOSITY["low"]["directive"])
        self.assertIn("STAKES", arc)
        self.assertNotIn("MOTIVATION", arc)


if __name__ == "__main__":
    unittest.main()
