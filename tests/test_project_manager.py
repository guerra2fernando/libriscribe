import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.agents.project_manager import ProjectManagerAgent
from libriscribe.agents.formatting_optimized import OptimizedFormattingAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.workflow_state import inspect_project_progress


class _FakeLLM:
    default_model = "test-model"
    settings = type("Settings", (), {"fallback_chain": ""})()

    def set_model(self, model: str) -> None:
        self.default_model = model

    def set_fallback_chain(self, _fallback_chain: object) -> None:
        return None


class _FakePipelineAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    def execute(self, project_knowledge_base=None, chapter_number=None, **_kwargs):
        assert project_knowledge_base is not None
        assert project_knowledge_base.project_dir is not None

        if self.name == "OutlinerAgent":
            project_knowledge_base.outline = "# Outline\n\nA complete outline."
            (project_knowledge_base.project_dir / "outline.md").write_text(
                project_knowledge_base.outline, encoding="utf-8"
            )
        elif self.name == "ChapterWriterAgent":
            (project_knowledge_base.project_dir / f"chapter_{chapter_number}.md").write_text(
                f"# Chapter {chapter_number}\n\nDraft text.", encoding="utf-8"
            )
        elif self.name == "EditorAgent":
            (project_knowledge_base.project_dir / f"chapter_{chapter_number}_revised.md").write_text(
                f"# Chapter {chapter_number}\n\nRevised text.", encoding="utf-8"
            )


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

    def test_mocked_pipeline_reaches_complete_and_resume_is_noop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"PROJECTS_DIR": tmpdir}, clear=False):
                manager = ProjectManagerAgent()
                kb = ProjectKnowledgeBase(
                    project_name="pipeline-demo",
                    title="Pipeline Demo",
                    description="A pipeline test",
                    category="Fiction",
                    genre="Fantasy",
                    logline="A complete logline",
                    num_chapters=1,
                )
                manager.initialize_project_with_data(kb)
                manager.llm_client = _FakeLLM()
                manager.agents["outliner"] = _FakePipelineAgent("OutlinerAgent")
                manager.agents["chapter_writer"] = _FakePipelineAgent("ChapterWriterAgent")
                manager.agents["editor"] = _FakePipelineAgent("EditorAgent")
                manager.agents["formatting"] = OptimizedFormattingAgent(manager.llm_client)

                manager.generate_outline()
                manager.write_chapter(1)
                manager.edit_chapter(1)
                manuscript_path = Path(tmpdir) / "pipeline-demo" / "manuscript.md"
                manager.format_book(str(manuscript_path))

                progress = inspect_project_progress(manager.project_dir, kb)
                self.assertEqual(progress.next_step, "complete")
                self.assertTrue(manuscript_path.exists())

                import libriscribe.main as main

                with patch.object(main, "project_manager", manager):
                    with patch.object(manager, "initialize_llm_client") as initialize_llm:
                        main.resume("pipeline-demo")
                        initialize_llm.assert_called_once()


if __name__ == "__main__":
    unittest.main()
