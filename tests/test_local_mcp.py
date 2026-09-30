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
    "list_projects",
    "get_project_status",
    "get_chapter",
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
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", lambda self: (path / "outline.md").write_text("# Outline", encoding="utf-8"))
    service = service_for(tmp_path)
    assert service.generate_outline("Novel")["artifact"]["path"] == "outline.md"
    with pytest.raises(ServiceError) as error:
        service.generate_outline("Novel")
    assert error.value.code == "overwrite_refused"
    assert service.generate_outline("Novel", overwrite=True)["status"] == "complete"

    # ProjectManagerAgent methods normally catch some agent exceptions. The facade
    # must detect the missing artifact instead of returning an empty success.
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", lambda self: None)
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

    def failed_call(self):
        (path / "outline.md").write_text("# Partial", encoding="utf-8")

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda self, *args, **kwargs: setattr(self, "llm_client", FailedProvider()))
    monkeypatch.setattr(ProjectManagerAgent, "generate_outline", failed_call)
    with pytest.raises(ServiceError) as error:
        service_for(tmp_path).generate_outline("Novel", overwrite=True)
    assert error.value.code == "provider_failure"


def test_write_chapter_range_edit_missing_and_format_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path, _ = make_project(tmp_path)
    from libriscribe.agents.project_manager import ProjectManagerAgent

    monkeypatch.setattr(ProjectManagerAgent, "initialize_llm_client", lambda *args, **kwargs: None)
    monkeypatch.setattr(ProjectManagerAgent, "write_chapter", lambda self, n: (path / f"chapter_{n}.md").write_text("# Generated", encoding="utf-8"))
    monkeypatch.setattr(ProjectManagerAgent, "edit_chapter", lambda self, n: (path / f"chapter_{n}_revised.md").write_text("# Revised", encoding="utf-8"))
    def format_mock(self, output):
        output_path = Path(output)
        original_path = path / f"manuscript_original{output_path.suffix}"
        if output_path.suffix == ".pdf":
            output_path.write_bytes(b"%PDF-mock")
            original_path.write_bytes(b"%PDF-original-mock")
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


def test_plugin_json_and_mcp_contract_has_exactly_nine_tools():
    from libriscribe import mcp_server

    registered = mcp_server.mcp._tool_manager.list_tools()
    assert {tool.name for tool in registered} == TOOLS
    schemas = {tool.name: tool.parameters for tool in registered}
    assert "overwrite" in schemas["generate_outline"]["properties"]
    assert "chapter_number" in schemas["write_chapter"]["properties"]
    assert "version" in schemas["get_chapter"]["properties"]
    assert "original, revised" in schemas["get_chapter"]["properties"]["version"]["description"]
    assert "keyword" in schemas["search_project"]["properties"]["mode"]["description"]
    assert schemas["format_book"]["properties"]["format"]["type"] == "string"
    assert "md or pdf" in schemas["format_book"]["properties"]["format"]["description"]
    expected_properties = {
        "list_projects": {"limit"},
        "get_project_status": {"project"},
        "get_chapter": {"project", "chapter_number", "version", "start_char", "max_chars"},
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
    for name in {"generate_outline", "write_chapter", "edit_chapter", "format_book"}:
        assert by_name[name].annotations.readOnlyHint is False
        assert by_name[name].annotations.destructiveHint is True
        assert by_name[name].annotations.openWorldHint is True

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

    asyncio.run(exchange())
