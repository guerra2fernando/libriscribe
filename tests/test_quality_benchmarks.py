from __future__ import annotations

from pathlib import Path
import os
import subprocess
from types import SimpleNamespace

import pytest

from libriscribe.benchmarks import DEFAULT_FIXTURE, run_benchmarks
from libriscribe.retrieval.keyword_index import KeywordIndex
from libriscribe.retrieval.models import RetrievalChunk, RetrievalConfig
from libriscribe.retrieval.search_service import SearchServiceImpl
from libriscribe.retrieval.semantic_index import SemanticIndex
from libriscribe.retrieval.config import get_retrieval_dir


class FixtureEmbedder:
    def encode(self, texts, normalize_embeddings=True):
        vectors = {"red apple": [1.0, 0.0], "crimson fruit": [0.0, 1.0], "red apple query": [0.0, 1.0]}
        return [vectors[text] for text in texts]


def chunk(chunk_id: str, text: str) -> RetrievalChunk:
    return RetrievalChunk(
        chunk_id=chunk_id, document_id=chunk_id, project_name="Book", text=text,
        source_type="prose", chunk_index=0, hash=chunk_id,
    )


def test_semantic_and_hybrid_ranking_are_deterministic(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    chunks = [chunk("literal", "red apple"), chunk("concept", "crimson fruit")]
    semantic = SemanticIndex("fixture", local_files_only=True)
    monkeypatch.setattr(semantic, "_load_model", lambda: FixtureEmbedder())
    semantic.build(chunks)
    index_path = tmp_path / "vectors.json"
    semantic.save_to_file(index_path)
    restored = SemanticIndex("fixture")
    restored.load_from_file(index_path)
    monkeypatch.setattr(restored, "_load_model", lambda: FixtureEmbedder())

    keyword = KeywordIndex(tmp_path)
    keyword.build(chunks)
    search = object.__new__(SearchServiceImpl)
    search.config = RetrievalConfig(hybrid_keyword_weight=0.2)
    search.index_manager = SimpleNamespace(keyword_index=keyword, semantic_index=restored)
    assert search.search("red apple query", mode="semantic")[0].chunk_id == "concept"
    assert search.search("red apple query", mode="hybrid")[0].chunk_id == "concept"
    assert search.search("red apple query", mode="keyword")[0].chunk_id == "literal"


def test_index_directory_rejects_traversal_and_symlink_escape(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(ValueError):
        get_retrieval_dir(project, RetrievalConfig(projects_subdir="../outside"))
    link = project / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, text=True)
            if result.returncode:
                pytest.skip("Directory symlinks and junctions are unavailable on this host.")
        else:
            pytest.skip("Directory symlinks are unavailable on this host.")
    with pytest.raises(ValueError):
        get_retrieval_dir(project, RetrievalConfig(projects_subdir="linked/index"))


def test_benchmark_fixture_reports_reproducible_metrics():
    first = run_benchmarks(DEFAULT_FIXTURE, 3)
    second = run_benchmarks(DEFAULT_FIXTURE, 3)
    assert first == second
    assert first["retrieval"]["queries"] == 3
    assert first["retrieval"]["mean_reciprocal_rank"] == 1.0
    assert first["writing_diagnostics"]["words"] > 0


def test_benchmark_rejects_invalid_k(tmp_path: Path):
    with pytest.raises(ValueError, match="k must"):
        run_benchmarks(DEFAULT_FIXTURE, 0)


def test_multi_file_export_restores_previous_artifacts_on_promotion_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from libriscribe.service import LibriScribeService
    import libriscribe.service as service_module

    stage = tmp_path / "stage"
    stage.mkdir()
    staged_output = stage / "manuscript.md"
    staged_original = stage / "manuscript_original.md"
    staged_output.write_text("new manuscript", encoding="utf-8")
    staged_original.write_text("new original", encoding="utf-8")
    output = tmp_path / staged_output.name
    original = tmp_path / staged_original.name
    output.write_text("good old manuscript", encoding="utf-8")
    original.write_text("good old original", encoding="utf-8")
    real_replace = service_module.os.replace

    def fail_second_promotion(source, target):
        if Path(source) == staged_original and Path(target) == original:
            raise OSError("simulated disk failure")
        return real_replace(source, target)

    monkeypatch.setattr(service_module.os, "replace", fail_second_promotion)
    with pytest.raises(Exception, match="previous artifacts were restored"):
        LibriScribeService._promote_many(
            [(staged_output, output), (staged_original, original)], stage
        )
    assert output.read_text(encoding="utf-8") == "good old manuscript"
    assert original.read_text(encoding="utf-8") == "good old original"
