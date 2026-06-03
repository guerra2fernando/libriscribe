import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.agents.project_manager import ProjectManagerAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase


class ProjectManagerTests(unittest.TestCase):
    def test_initialize_project_with_data_creates_project_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"PROJECTS_DIR": tmpdir}, clear=False):
                manager = ProjectManagerAgent()
                kb = ProjectKnowledgeBase(
                    project_name="project-init-demo",
                    title="Demo",
                    description="Demo description",
                    category="Fiction",
                    genre="Fantasy",
                    logline="A saved logline",
                    fallback_chain=["claude"],
                    agent_fallback_chains={"editor": ["openai/gpt-4o"]},
                )

                manager.initialize_project_with_data(kb)

                project_file = Path(tmpdir) / "project-init-demo" / "project_data.json"
                self.assertTrue(project_file.exists())

                loaded = ProjectKnowledgeBase.load_from_file(str(project_file))
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded.fallback_chain, ["claude"])
                self.assertEqual(
                    loaded.agent_fallback_chains,
                    {"editor": ["openai/gpt-4o"]},
                )

                status_file = (
                    Path(tmpdir) / "project-init-demo" / ".libriscribe_status.json"
                )
                self.assertTrue(status_file.exists())
                status_payload = json.loads(status_file.read_text(encoding="utf-8"))
                self.assertEqual(
                    status_payload["stages"]["concept"]["status"], "complete"
                )
                self.assertEqual(
                    status_payload["stages"]["outline"]["status"], "pending"
                )


if __name__ == "__main__":
    unittest.main()
