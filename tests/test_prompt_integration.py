from pathlib import Path
from unittest.mock import Mock

from libriscribe.agents.editor import EditorAgent
from libriscribe.knowledge_base import ProjectKnowledgeBase
from libriscribe.utils.prompt_loader import PromptLoader


def test_packaged_prompt_is_available_without_project_checkout(tmp_path: Path) -> None:
    loader = PromptLoader(tmp_path / "missing-prompts")

    template = loader.get_template("editor")

    assert "Expert editor" in template
    assert "editor" in loader.list_prompts()


def test_project_prompt_override_takes_precedence(tmp_path: Path) -> None:
    templates_dir = tmp_path / "prompts" / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "editor.yml").write_text(
        "template: |\n  Custom editor for {genre}.\nsettings:\n  max_tokens: 123\n",
        encoding="utf-8",
    )

    loader = PromptLoader(tmp_path / "prompts")

    assert loader.get_template("editor").strip() == "Custom editor for {genre}."
    assert loader.get_settings("editor")["max_tokens"] == 123


def test_production_editor_uses_project_prompt_override(tmp_path: Path) -> None:
    templates_dir = tmp_path / "prompts" / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "editor.yml").write_text(
        "template: |\n  CUSTOM EDITOR {chapter_content}\nsettings:\n  max_tokens: 321\n  temperature: 0.2\n",
        encoding="utf-8",
    )
    chapter_path = tmp_path / "chapter_1.md"
    chapter_path.write_text("# Chapter 1\n\nDraft.", encoding="utf-8")

    llm = Mock()
    llm.generate_content.side_effect = ["Review feedback", "# Chapter 1\n\nRevised."]
    agent = EditorAgent(llm)
    agent.prompt_loader = PromptLoader(tmp_path / "prompts")
    pkb = ProjectKnowledgeBase(
        project_name="prompt-demo",
        title="Prompt Demo",
        genre="Fantasy",
        project_dir=tmp_path,
    )

    agent.execute(pkb, 1)

    editor_call = llm.generate_content.call_args_list[1]
    assert "CUSTOM EDITOR" in editor_call.args[0]
    assert editor_call.kwargs["max_tokens"] == 321
    assert editor_call.kwargs["temperature"] == 0.2
