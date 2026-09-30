---
sidebar_position: 5
---

# Local retrieval and quality

LibriScribe keeps retrieval data inside each selected project. The default index uses local BM25 when installed and a pure-Python TF-IDF fallback otherwise. Keyword search needs no embedding library, credentials, model download, or network connection.

## Optional semantic and hybrid search

Install the optional embedding dependency only when you want semantic ranking:

```bash
pip install -e ".[semantic]"
```

Sentence-transformers computes embeddings on the current device. Model inference consumes local CPU/GPU time and disk space but makes no provider API calls and has no per-request provider charge. Models are not downloaded implicitly by LibriScribe: local-only loading is enabled by default. Use a model already in the local Hugging Face cache, or pass a local model directory.

Configure the index mode and build its local files:

```bash
libriscribe retrieval rebuild --project MyBook --mode hybrid
libriscribe retrieval rebuild --project MyBook --mode semantic --embedding-model C:\models\my-embedder
libriscribe retrieval rebuild --project MyBook --mode hybrid --keyword-weight 0.65
```

Search without changing the existing keyword default:

```bash
libriscribe retrieval search --project MyBook --query "the hidden passage" --mode hybrid
```

The `search_project` MCP tool accepts `keyword`, `semantic`, and `hybrid` modes too. It reads an existing index and never rebuilds it. CLI `refresh` rebuilds when source documents change; rebuild explicitly after changing the model or retrieval mode. Rebuilding in keyword mode removes the stale semantic index. The default index directory is `.libriscribe_retrieval` under the project. Configured index paths that traverse out of the project or resolve through an escaping symlink are rejected.

The project retrieval configuration stores `mode`, `embedding_model`, `embedding_local_files_only` (true by default), and `hybrid_keyword_weight` (0.5 by default). The CLI rebuild options update and save mode, model, and hybrid weight in `project_data.json`.

Semantic and hybrid searches fail with a structured error when the optional package, local model, or matching semantic index is unavailable. Keyword search continues to work independently. This feature supports sentence-transformers only; index files are local JSON and there is no remote vector database or embedding provider.

## Reproducible quality diagnostics

Run the checked-in fixture benchmark from the repository root:

```bash
python -m libriscribe.benchmarks
python -m libriscribe.benchmarks --k 5
```

Retrieval reports Recall@k, Precision@k, and mean reciprocal rank using a deterministic pure-Python TF-IDF baseline. Writing diagnostics report word and sentence counts, mean sentence length, type-token ratio, and repeated-sentence rate. They are reproducible lexical measurements, not a substitute for human judgment, and need no provider calls. The fixture lives at `tests/fixtures/quality_benchmark.json` and can be replaced with `--fixture path/to/fixture.json`.

## Export behavior and plugin checks

The shared service stages Markdown and PDF export files inside the project, validates them before publication, and restores the previous set if publishing a replacement set fails. PDFs require a valid generated PDF artifact; Markdown assembly is local. PDF formatting may use the configured LLM provider and incur its normal cost.

The local Claude Code and Codex plugin manifests are JSON-validated in the test suite. To smoke-test host workflows, install the Python package in the MCP host's environment, then follow the [local integration guide](local-integrations.md). Host CLI checks can only run on systems where those CLIs are installed. The repository does not submit plugins to a public marketplace.
