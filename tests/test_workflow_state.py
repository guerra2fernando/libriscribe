import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.workflow_state import inspect_project_progress


class WorkflowStateTests(unittest.TestCase):
    def test_inspect_project_progress_detects_missing_stages_and_skips_empty_files(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "outline.md").write_text("# Outline", encoding="utf-8")
            (project_dir / "characters.json").write_text("[]", encoding="utf-8")
            (project_dir / "chapter_1.md").write_text(
                "Chapter 1 content", encoding="utf-8"
            )
            (project_dir / "chapter_2.md").write_text("   ", encoding="utf-8")

            kb = ProjectKnowledgeBase(
                project_name="resume-demo",
                title="Resume Demo",
                description="A project",
                category="Fiction",
                genre="Fantasy",
                logline="A generated logline",
                num_characters=2,
                worldbuilding_needed=True,
                num_chapters=3,
            )

            progress = inspect_project_progress(project_dir, kb)

        self.assertTrue(progress.concept_complete)
        self.assertTrue(progress.outline_complete)
        self.assertTrue(progress.characters_complete)
        self.assertFalse(progress.worldbuilding_complete)
        self.assertEqual(progress.chapter_numbers_complete, [1])
        self.assertEqual(progress.missing_chapters, [2, 3])
        self.assertEqual(progress.next_step, "worldbuilding")

    def test_inspect_project_progress_reports_complete_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "outline.md").write_text("# Outline", encoding="utf-8")
            (project_dir / "chapter_1.md").write_text("Chapter 1", encoding="utf-8")
            (project_dir / "chapter_2.md").write_text("Chapter 2", encoding="utf-8")
            (project_dir / "manuscript.md").write_text(
                "Full manuscript", encoding="utf-8"
            )

            kb = ProjectKnowledgeBase(
                project_name="done-demo",
                title="Done Demo",
                description="A project",
                category="Fiction",
                genre="Fantasy",
                num_characters=0,
                worldbuilding_needed=False,
                num_chapters=2,
                chapters={},
            )

            progress = inspect_project_progress(project_dir, kb)

        self.assertEqual(progress.next_step, "complete")
        self.assertEqual(progress.chapter_numbers_complete, [1, 2])
        self.assertTrue(progress.manuscript_exists)

    def test_inspect_project_progress_reads_interrupted_stage_from_status_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / ".libriscribe_status.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "stages": {
                            "outline": {"status": "complete"},
                            "chapters": {"status": "in_progress"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            kb = ProjectKnowledgeBase(
                project_name="status-demo",
                title="Status Demo",
                description="A project",
                category="Fiction",
                genre="Fantasy",
                logline="A generated logline",
                num_characters=0,
                worldbuilding_needed=False,
                num_chapters=2,
            )

            progress = inspect_project_progress(project_dir, kb)

        self.assertEqual(progress.interrupted_stage, "chapters")
        self.assertEqual(progress.stage_statuses["chapters"], "in_progress")
        self.assertEqual(progress.next_step, "chapters")


if __name__ == "__main__":
    unittest.main()
