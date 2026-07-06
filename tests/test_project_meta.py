"""PUT /projects/{name}/meta — edit a story's primary details.

Confirms the endpoint writes provided fields, ignores omitted ones, coerces the target
chapter count like project creation does, leaves the project id (folder name) fixed, and
404s on a missing project."""
import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from libriscribe.api.app import create_app


class ProjectMetaTests(unittest.TestCase):
    def setUp(self):
        self._prev_dir = os.environ.get("LIBRISCRIBE_PROJECTS_DIR")
        os.environ["LIBRISCRIBE_PROJECTS_DIR"] = tempfile.mkdtemp()
        from libriscribe.services import project_service
        from libriscribe.knowledge_base import ProjectKnowledgeBase
        self.project_service = project_service
        pdir = project_service.get_projects_dir() / "demo"
        pdir.mkdir(parents=True, exist_ok=True)
        kb = ProjectKnowledgeBase(
            project_name="demo", title="Old Title", genre="Sci-Fi",
            category="Fiction", language="English", num_chapters=5,
        )
        project_service.save_kb("demo", kb)
        self.client = TestClient(create_app())

    def tearDown(self):
        if self._prev_dir is None:
            os.environ.pop("LIBRISCRIBE_PROJECTS_DIR", None)
        else:
            os.environ["LIBRISCRIBE_PROJECTS_DIR"] = self._prev_dir

    def test_updates_provided_fields_and_persists(self):
        resp = self.client.put("/api/projects/demo/meta", json={
            "title": "New Title",
            "genre": "Fantasy",
            "description": "A grand tale.",
            "num_chapters": "10-14",
            "target_word_count": 90000,
            "logline": "One line.",
            "tone": "Dark",
            "target_audience": "Adult",
            "book_length": "Novel",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["title"], "New Title")
        self.assertEqual(body["genre"], "Fantasy")
        self.assertEqual(body["target_word_count"], 90000)
        self.assertEqual(body["num_chapters"], [10, 14])  # range coerced to tuple->JSON list

        # Persisted to disk.
        kb = self.project_service.load_kb("demo")
        self.assertEqual(kb.title, "New Title")
        self.assertEqual(kb.target_word_count, 90000)
        self.assertEqual(kb.num_chapters, (10, 14))

    def test_omitted_fields_are_left_untouched(self):
        resp = self.client.put("/api/projects/demo/meta", json={"title": "Only Title"})
        self.assertEqual(resp.status_code, 200)
        kb = self.project_service.load_kb("demo")
        self.assertEqual(kb.title, "Only Title")
        self.assertEqual(kb.genre, "Sci-Fi")       # unchanged
        self.assertEqual(kb.num_chapters, 5)        # unchanged

    def test_project_id_is_not_editable(self):
        # `project_name` is not a field on the model; sending it is silently ignored.
        self.client.put("/api/projects/demo/meta", json={"title": "T", "project_name": "hacked"})
        self.assertIsNone(self.project_service.load_kb("hacked"))
        self.assertIsNotNone(self.project_service.load_kb("demo"))

    def test_missing_project_returns_404(self):
        resp = self.client.put("/api/projects/nope/meta", json={"title": "x"})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
