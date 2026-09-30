from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from libriscribe.knowledge_base import Chapter, ProjectKnowledgeBase, Scene
from libriscribe.narrative.models import NarrativeFact, NarrativeGraph
from libriscribe.service import LibriScribeService, ServiceError
from libriscribe.settings import Settings


TOOLS = {
    "create_project",
    "list_projects",
    "get_project_status",
    "get_chapter",
    "replace_chapter_text",
    "search_project",
    "check_narrative",
    "generate_outline",
    "write_chapter",
    "edit_chapter",
    "format_book",
}


def make_project(root: Path, name: str = "Novel") -> tuple[Path, ProjectKnowledgeBase]:
    path = root / name
    path.mkdir(parents=True)
    kb = ProjectKnowledgeBase(
        project_name=name,
        title="A Local Book",
        genre="Fantasy",
        num_chapters=5,
        num_chapters_str="5",
        chapters={1: Chapter(chapter_number=1, title="The Door", scenes=[Scene(scene_number=1, characters=["Mira"], goal="Talk")])},
    )
    kb.project_dir = path
    kb.save_to_file(str(path / "project_data.json"))
    return path, kb


def service_for(root: Path) -> LibriScribeService:
    return LibriScribeService(Settings(_env_file=None, projects_dir=str(root)))


def test_read_tools_and_project_metadata_are_bounded_and_side_effect_free(tmp_path: Path):
    path, kb = make_project(tmp_path)
    chapter = path / "chapter_1.md"
    chapter.write_text("A long chapter text", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    service = service_for(tmp_path)

    assert service.list_projects() == {
        "projects": [{"project": "Novel", "title": "A Local Book", "genre": "Fantasy", "category": "Unknown Category"}],
        "count": 1,
    }
    status = service.get_project_status("Novel")
    assert status["project"] == "Novel"
    assert status["missing_chapters"] == [2, 3, 4, 5]
    page = service.get_chapter("Novel", 1, max_chars=5)
    assert (page["text"], page["has_more"], page["total_chars"]) == ("A lon", True, 19)
    assert service.get_chapter("Novel", 1, start_char=5)["text"] == "g chapter text"
    with pytest.raises(ServiceError, match="does not exist"):
        service.get_chapter("Novel", 1, version="revised")
    after = {p.name: p.read_bytes() for p in path.iterdir()}
    assert before == after


def test_create_project_defaults_duplicate_refusal_and_no_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    service = service_for(tmp_path)
    from libriscribe.agents.project_manager import ProjectManagerAgent

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda *args, **kwargs: pytest.fail("creation initialized a provider"))
    result = service.create_project("New Book", "A New Book")
    assert result["status"] == "complete"
    assert "No LLM was called" in result["summary"]
    created = ProjectKnowledgeBase.load_from_file(str(tmp_path / "New Book" / "project_data.json"))
    assert created is not None
    assert (created.title, created.category, created.genre, created.num_chapters) == ("A New Book", "Fiction", "Unknown Genre", 1)
    assert service.get_project_status("New Book")["operation_state"] == "complete"
    with pytest.raises(ServiceError) as error:
        service.create_project("New Book", "Duplicate")
    assert error.value.code == "project_exists"


def test_create_project_rejects_traversal_and_invalid_fields(tmp_path: Path):
    service = service_for(tmp_path)
    for name in ("../escape", "nested/name", "C:\\escape"):
        with pytest.raises(ServiceError) as error:
            service.create_project(name, "Title")
        assert error.value.code == "invalid_project"
    with pytest.raises(ServiceError) as error:
        service.create_project("Book", "Title", chapter_count=0)
    assert error.value.code == "invalid_argument"
    assert not (tmp_path.parent / "escape").exists()


def test_failed_project_creation_leaves_no_complete_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    service = service_for(tmp_path)
    monkeypatch.setattr(ProjectKnowledgeBase, "save_to_file", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("simulated write failure")))
    with pytest.raises(ServiceError) as error:
        service.create_project("Incomplete", "Incomplete")
    assert error.value.code == "write_failed"
    assert not (tmp_path / "Incomplete").exists()
    assert not list(tmp_path.glob(".libriscribe-create-*"))


def test_manual_chapter_revision_uses_token_and_preserves_stale_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    chapter = path / "chapter_1.md"
    chapter.write_text("Original chapter", encoding="utf-8")
    service = service_for(tmp_path)
    before = service.get_chapter("Novel", 1)
    from libriscribe.agents.project_manager import ProjectManagerAgent
    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda *args, **kwargs: pytest.fail("manual edit initialized a provider"))

    result = service.replace_chapter_text("Novel", 1, "original", "Human revision", before["revision_token"])
    assert result["status"] == "complete"
    after = service.get_chapter("Novel", 1)
    assert after["text"] == "Human revision"
    assert after["revision_token"] == result["revision_token"]
    with pytest.raises(ServiceError) as error:
        service.replace_chapter_text("Novel", 1, "original", "Stale edit", before["revision_token"])
    assert error.value.code == "stale_revision"
    assert chapter.read_text(encoding="utf-8") == "Human revision"
    with pytest.raises(ServiceError) as error:
        service.replace_chapter_text("Novel", 2, "revised", "Create not allowed", "0" * 64)
    assert error.value.code == "artifact_not_found"


def test_legacy_status_file_remains_readable(tmp_path: Path):
    path, _ = make_project(tmp_path)
    (path / ".libriscribe_status.json").write_text(json.dumps({"version": 1, "updated_at": "2020-01-01T00:00:00+00:00", "stages": {}}), encoding="utf-8")
    status = service_for(tmp_path).get_project_status("Novel")
    assert status["status_updated_at"] == "2020-01-01T00:00:00+00:00"
    assert status["operation_state"] == "unknown"


def test_manual_chapter_revision_failed_replace_keeps_previous_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    artifact = path / "chapter_1.md"
    artifact.write_text("Keep this", encoding="utf-8")
    service = service_for(tmp_path)
    token = service.get_chapter("Novel", 1)["revision_token"]
    import libriscribe.service as service_module
    real_replace = service_module.os.replace

    def failing_replace(source, destination):
        if Path(destination) == artifact:
            raise OSError("simulated replacement failure")
        return real_replace(source, destination)

    monkeypatch.setattr(service_module.os, "replace", failing_replace)
    with pytest.raises(ServiceError) as error:
        service.replace_chapter_text("Novel", 1, "original", "New content", token)
    assert error.value.code == "write_failed"
    assert artifact.read_text(encoding="utf-8") == "Keep this"


def test_generation_provider_failure_preserves_existing_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    artifact = path / "outline.md"
    artifact.write_text("Last good outline", encoding="utf-8")
    from libriscribe.agents.project_manager import ProjectManagerAgent

    class FailedProvider:
        last_failure_type = "provider_unavailable"

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda self, *args, **kwargs: setattr(self, "llm_client", FailedProvider()))
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", lambda self, output_path=None: Path(output_path).write_text("Partial replacement", encoding="utf-8"))
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).generate_outline("Novel", overwrite=True)
    assert error.value.code == "provider_failure"
    assert artifact.read_text(encoding="utf-8") == "Last good outline"
    assert not list(path.glob(".libriscribe-stage-*"))
    status = service_for(tmp_path).get_project_status("Novel")
    assert status["operation_state"] == "failed"
    assert status["operation"]["name"] == "generate_outline"
    assert status["recovery_guidance"].startswith("Inspect")


def test_project_write_lock_excludes_a_separate_process(tmp_path: Path):
    from libriscribe.utils.project_status import project_write_lock

    script = """
import sys
from pathlib import Path
from libriscribe.utils.project_status import project_write_lock, ProjectWriteBusy
try:
    with project_write_lock(Path(sys.argv[1])):
        print('acquired')
except ProjectWriteBusy:
    print('busy')
"""
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[1] / "src")
    environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
    with project_write_lock(tmp_path):
        result = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "busy"


@pytest.mark.parametrize("project", ["", ".", "..", "../Novel", "x/y", "x\\y", "C:\\secrets"])
def test_rejects_invalid_project_identifiers(tmp_path: Path, project: str):
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).get_project_status(project)
    assert error.value.code == "invalid_project"


def test_missing_project_has_stable_error(tmp_path: Path):
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).get_project_status("Missing")
    assert error.value.code == "project_not_found"


def test_rejects_symlink_escape_and_does_not_enumerate_it(tmp_path: Path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    make_project(outside, "Secret")
    link = tmp_path / "escape"
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside / "Secret")],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                pytest.skip("Directory junction creation is unavailable on this host")
        else:
            link.symlink_to(outside / "Secret", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available on this host")
    service = service_for(tmp_path)
    assert service.list_projects()["projects"] == []
    with pytest.raises(ServiceError) as error:
        service.get_project_status("escape")
    assert error.value.code == "project_not_found"


def test_rejects_project_entry_link_that_resolves_outside_project(tmp_path: Path):
    path, _ = make_project(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-linked-outside"
    outside.mkdir()
    (outside / "chapter_1.md").write_text("must not be read", encoding="utf-8")
    link = path / "linked-files"
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                pytest.skip("Directory junction creation is unavailable on this host")
        else:
            link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available on this host")
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).get_project_status("Novel")
    assert error.value.code == "project_escape"


def test_search_reports_disabled_or_missing_index_without_mutating(tmp_path: Path):
    path, kb = make_project(tmp_path)
    service = service_for(tmp_path)
    with pytest.raises(ServiceError) as error:
        service.search_project("Novel", "door")
    assert error.value.code == "capability_disabled"
    kb.retrieval.enabled = True
    kb.save_to_file(str(path / "project_data.json"))
    before = set(path.rglob("*"))
    with pytest.raises(ServiceError) as error:
        service.search_project("Novel", "door")
    assert error.value.code == "index_unavailable"
    assert set(path.rglob("*")) == before


def test_narrative_check_uses_existing_graph_and_returns_structured_violations(tmp_path: Path):
    path, kb = make_project(tmp_path)
    kb.chapters[2] = Chapter(chapter_number=2, title="Aftermath", scenes=[Scene(scene_number=1, characters=["Mira"], goal="Talk")])
    kb.save_to_file(str(path / "project_data.json"))
    graph = NarrativeGraph(
        project_name="Novel",
        facts=[NarrativeFact(fact_id="dead1", entity="Mira", entity_type="character", predicate="is_dead", value="dead", chapter=1, evidence_quote="Mira fell.")],
    )
    graph.save(path / "narrative_graph.json")
    service = service_for(tmp_path)
    result = service.check_narrative("Novel", 2)
    assert result["count"] == 1
    assert result["violations"][0]["evidence"] == "Mira fell."
    (path / "narrative_graph.json").unlink()
    with pytest.raises(ServiceError) as error:
        service.check_narrative("Novel", 1)
    assert error.value.code == "graph_unavailable"


def test_write_overwrite_and_swallowed_failure_detection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    from libriscribe.agents.project_manager import ProjectManagerAgent

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda *args, **kwargs: None)
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", lambda self, output_path=None: Path(output_path or path / "outline.md").write_text("# Outline", encoding="utf-8"))
    service = service_for(tmp_path)
    assert service.generate_outline("Novel")["artifact"]["path"] == "outline.md"
    with pytest.raises(ServiceError) as error:
        service.generate_outline("Novel")
    assert error.value.code == "overwrite_refused"
    assert service.generate_outline("Novel", overwrite=True)["status"] == "complete"

    # ProjectManagerAgent methods normally catch some agent exceptions. The facade
    # must detect the missing artifact instead of returning an empty success.
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", lambda self, output_path=None: None)
    with pytest.raises(ServiceError) as error:
        service.generate_outline("Novel", overwrite=True)
    assert error.value.code == "operation_failed"


def test_provider_initialization_failure_and_mcp_error_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    from libriscribe.agents.project_manager import ProjectManagerAgent
    from libriscribe import mcp_server

    def unavailable(*args, **kwargs):
        raise RuntimeError("provider error contains no useful public detail")

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", unavailable)
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).generate_outline("Novel")
    assert error.value.code == "provider_failure"
    response = mcp_server._invoke(lambda: service_for(tmp_path).get_project_status("../escape"))
    assert response == {
        "ok": False,
        "error": {"code": "invalid_project", "message": "Project must be a simple project identifier."},
    }
    assert mcp_server.get_chapter("Novel", 0)["error"]["code"] == "invalid_argument"
    assert mcp_server.list_projects(0)["error"]["code"] == "invalid_argument"
    assert mcp_server.format_book("Novel", "doc")["error"]["code"] == "invalid_argument"

    class FailedProvider:
        last_failure_type = "provider_not_configured"

    def failed_call(self, output_path=None):
        Path(output_path or path / "outline.md").write_text("# Partial", encoding="utf-8")

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda self, *args, **kwargs: setattr(self, "llm_client", FailedProvider()))
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", failed_call)
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).generate_outline("Novel", overwrite=True)
    assert error.value.code == "provider_failure"


def test_write_chapter_range_edit_missing_and_format_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    from libriscribe.agents.project_manager import ProjectManagerAgent

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda *args, **kwargs: None)
    monkeypatch.setattr(ProjectManagerAgent, "write_chapter", lambda self, n, output_path=None: Path(output_path or path / f"chapter_{n}.md").write_text("# Generated", encoding="utf-8"))
    monkeypatch.setattr(ProjectManagerAgent, "edit_chapter", lambda self, n, output_path=None: Path(output_path or path / f"chapter_{n}_revised.md").write_text("# Revised", encoding="utf-8"))
    def format_mock(self, output):
        output_path = Path(output)
        original_path = output_path.parent / f"manuscript_original{output_path.suffix}"
        if output_path.suffix == ".pdf":
            output_path.write_bytes(b"%PDF-1.4\n% mock\n%%EOF\n")
            original_path.write_bytes(b"%PDF-1.4\n% original mock\n%%EOF\n")
        else:
            output_path.write_text("# Manuscript", encoding="utf-8")
            original_path.write_text("# Original", encoding="utf-8")

    monkeypatch.setattr(ProjectManagerAgent, "format_book", format_mock)
    service = service_for(tmp_path)
    assert service.write_chapter("Novel", 1)["artifact"]["path"] == "chapter_1.md"
    with pytest.raises(ServiceError) as error:
        service.write_chapter("Novel", 6)
    assert error.value.code == "invalid_argument"
    with pytest.raises(ServiceError) as error:
        service.edit_chapter("Novel", 2)
    assert error.value.code == "artifact_not_found"
    assert service.edit_chapter("Novel", 1)["artifact"]["path"] == "chapter_1_revised.md"
    formatted = service.format_book("Novel", "md")
    assert {x["path"] for x in formatted["artifacts"]} == {"manuscript.md", "manuscript_original.md"}
    with pytest.raises(ServiceError) as error:
        service.format_book("Novel", "md")
    assert error.value.code == "overwrite_refused"
    pdf_result = service.format_book("Novel", "pdf")
    assert {x["path"] for x in pdf_result["artifacts"]} == {"manuscript.pdf", "manuscript_original.pdf"}


def test_plugin_json_and_mcp_contract_has_exactly_eleven_tools():
    from libriscribe import mcp_server

    registered = mcp_server.mcp._tool_manager.list_tools()
    assert {tool.name for tool in registered} == TOOLS
    schemas = {tool.name: tool.parameters for tool in registered}
    assert "overwrite" in schemas["generate_outline"]["properties"]
    assert "chapter_number" in schemas["write_chapter"]["properties"]
    assert "version" in schemas["get_chapter"]["properties"]
    assert "original, revised" in schemas["get_chapter"]["properties"]["version"]["description"]
    assert "keyword" in schemas["search_project"]["properties"]["mode"]["description"]
    assert "sentence-transformers" in by_name_description(registered, "search_project")
    assert schemas["format_book"]["properties"]["format"]["type"] == "string"
    assert "md or pdf" in schemas["format_book"]["properties"]["format"]["description"]
    expected_properties = {
        "create_project": {"project", "title", "description", "category", "genre", "language", "chapter_count", "llm_provider", "model"},
        "list_projects": {"limit"},
        "get_project_status": {"project"},
        "get_chapter": {"project", "chapter_number", "version", "start_char", "max_chars"},
        "replace_chapter_text": {"project", "chapter_number", "version", "text", "expected_revision_token"},
        "search_project": {"project", "query", "top_k", "mode"},
        "check_narrative": {"project", "chapter_number"},
        "generate_outline": {"project", "overwrite"},
        "write_chapter": {"project", "chapter_number", "overwrite"},
        "edit_chapter": {"project", "chapter_number", "overwrite"},
        "format_book": {"project", "format", "overwrite"},
    }
    assert {name: set(schema["properties"]) for name, schema in schemas.items()} == expected_properties
    by_name = {tool.name: tool for tool in registered}
    for name in {"list_projects", "get_project_status", "get_chapter", "search_project", "check_narrative"}:
        assert by_name[name].annotations.readOnlyHint is True
        assert by_name[name].annotations.openWorldHint is False
    for name in {"create_project", "replace_chapter_text", "generate_outline", "write_chapter", "edit_chapter", "format_book"}:
        assert by_name[name].annotations.readOnlyHint is False
        assert by_name[name].annotations.destructiveHint is True
        assert by_name[name].annotations.openWorldHint is (name in {"generate_outline", "write_chapter", "edit_chapter", "format_book"})

    root = Path(__file__).resolve().parents[1]
    for relative in (
        "plugins/claude-libriscribe/.claude-plugin/plugin.json",
        "plugins/claude-libriscribe/.mcp.json",
        "plugins/codex-libriscribe/.codex-plugin/plugin.json",
        "plugins/codex-libriscribe/.mcp.json",
        ".agents/plugins/marketplace.json",
    ):
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        assert isinstance(payload, dict)


def by_name_description(registered, name: str) -> str:
    return next(tool.description for tool in registered if tool.name == name)


def test_local_index_rebuild_modes_and_keyword_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _kb = make_project(tmp_path)
    service = service_for(tmp_path)
    built = service.rebuild_project_index("Novel", mode="keyword", hybrid_keyword_weight=0.25)
    assert built["mode"] == "keyword"
    loaded_config = ProjectKnowledgeBase.load_from_file(str(path / "project_data.json"))
    assert loaded_config is not None
    assert loaded_config.retrieval.hybrid_keyword_weight == 0.25
    index_file = path / ".libriscribe_retrieval" / "keyword_index.json"
    original_index = index_file.read_bytes()
    assert service.search_project("Novel", "Local Book")["mode"] == "keyword"

    from libriscribe.retrieval.semantic_index import SemanticIndex

    def unavailable(self):
        raise RuntimeError("fixture has no local model")

    monkeypatch.setattr(SemanticIndex, "_load_model", unavailable)
    with pytest.raises(ServiceError) as error:
        service.rebuild_project_index("Novel", mode="hybrid")
    assert error.value.code == "semantic_unavailable"
    assert index_file.read_bytes() == original_index
    with pytest.raises(ServiceError) as error:
        service.search_project("Novel", "anything", mode="remote")
    assert error.value.code == "unsupported_mode"
    with pytest.raises(ServiceError) as error:
        service.rebuild_project_index("Novel", mode="keyword", hybrid_keyword_weight=1.5)
    assert error.value.code == "invalid_argument"


def test_cli_search_rejects_unsupported_mode():
    from typer.testing import CliRunner
    from libriscribe.main import app

    result = CliRunner().invoke(
        app,
        ["retrieval", "search", "--project", "Novel", "--query", "door", "--mode", "vector"],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output


def test_stdio_initialize_list_tools_and_call_tools(tmp_path: Path):
    make_project(tmp_path)

    async def exchange() -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        environment = os.environ.copy()
        environment["PROJECTS_DIR"] = str(tmp_path)
        source_root = str(Path(__file__).resolve().parents[1] / "src")
        environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "libriscribe.mcp_server"],
            env=environment,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {tool.name for tool in tools.tools} == TOOLS
                result = await session.call_tool("list_projects", {"limit": 10})
                assert not result.isError
                assert result.structuredContent["ok"] is True
                assert result.structuredContent["result"]["projects"][0]["project"] == "Novel"
                created = await session.call_tool("create_project", {"project": "Stdio Book", "title": "Created Over MCP"})
                assert not created.isError
                assert created.structuredContent["ok"] is True
                assert created.structuredContent["result"]["project"] == "Stdio Book"

    asyncio.run(exchange())
