# Changelog

## 0.5.1 — 2026-09-30

### Added

- PyPI package metadata, MIT license, and a GitHub Actions Trusted Publishing workflow.
- Optional provider extras so local keyword retrieval and MCP utilities do not install every provider SDK.
- Actionable installation messages when a selected provider SDK is missing.

### Compatibility

- Install `libriscribe[openai]` for OpenAI, OpenRouter, or Bedrock Mantle; use `anthropic`, `google`, or `bedrock` for those providers.
- Use `all-providers` to include all provider SDKs, and `semantic` only when on-device embeddings are wanted.
- The base install can use DeepSeek and Mistral through its existing HTTP implementation, subject to provider API credentials and charges.

## 0.5.0 — 2026-09-30

### Added

- Optional local semantic and hybrid project search using sentence-transformers. Keyword search remains the default and does not require the embedding extra or model files.
- CLI search modes and hybrid keyword weighting; the existing `search_project` MCP tool now accepts keyword, semantic, and hybrid ranking.
- Project-confined retrieval indexes with traversal and symlink escape checks.
- Deterministic retrieval metrics (Recall@k, Precision@k, and MRR) and writing diagnostics that run without provider calls.
- Documentation for local model preparation, index lifecycle, known limitations, and local Claude Code/Codex integrations.

### Improved

- Manuscript replacement exports stage and validate the full artifact set, restoring existing artifacts if publishing the replacement set fails.
- CLI rejects unsupported search modes at argument parsing.

### Compatibility and limitations

- Keyword retrieval remains the default. Semantic support is installed separately with `pip install -e ".[semantic]"`.
- Model files are not included in the package. Users explicitly prepare a local model before semantic indexing; inference makes no embedding-provider API calls.
- Writing benchmark values are transparent lexical diagnostics, not an automated substitute for human review.
