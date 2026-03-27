# Changelog

All notable changes to book-producer are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- dual package preparation for npm and GitHub Packages
- CI and publish workflows
- managed tool entrypoints for Claude, Copilot, Cursor, and Antigravity
- orchestration commands for chapter and research packets

### Changed

- documentation now clarifies that `.book-framework/` is installed in user repositories
- documentation now clarifies that `.spec/<book-slug>/` stores book specs and workflow memory
- stage-file creation is now documented as lazy after initialization

## [0.1.0] — 2026-03-26

### Initial Release

This is the first public release of book-producer. The implementation is complete and tested, but several enhancements are planned for v0.2.0.

#### Added

- **Chat-first workflow**: Core 6-stage book creation framework (init, plan, design, chapters, review, finalize)
- **CLI**: One-time install command + optional status, list, use commands for terminal users
- **Directory model**: Split spec memory (`.spec/<slug>/`) from book content (`<slug>/` at repo root)
- **Branch mapping**: Automatic tracking of books per branch; auto-resolution of book context in multi-book repos
- **State persistence**: `state.json` and markdown stage files ensure work survives across chat sessions
- **Chapter management**: Sliding-window context (last 4–5 chapters in full + JSON summaries of older ones) for managing large books
- **Status command**: `book-producer status [slug]` for terminal visibility into workflow progress
- **Force-policy gates**: Explicit user confirmation required before destructive operations (cleanup)
- **Orchestration modes**: Sequential (default, faster in chat) or Parallel (faster compute but needs explicit sync points)
- **Template system**: Auto-generated stage files from configurable templates
- **Asset library**: Installed framework docs, agent instructions, and templates in `.book-framework/`
- **Test coverage**: 86 tests covering core workflows, error cases, install flows, orchestration modes, and state robustness

#### Known Limitations

- **No concurrent write safety**: If two processes write `state.json` simultaneously, corruption is possible. Mitigation: do not run two `book-producer init` in parallel on the same repo. Atomic writes planned for v0.2.0.
- **No API stability guarantee**: Public functions exported from CLI but no formalized API contract yet. v0.1.0 only.

#### Breaking Changes

None — this is the initial release.

---

## [Unreleased]

### Planned for v0.2.0

Fixed in `0.1.0` (previously planned):
- ✅ JSON error handling with descriptive recovery messages (`state.json`, `.branch-mapping.json`)
- ✅ Chapter order validation (gaps, duplicates, title format warnings) in the assembler
- ✅ Asset integrity integration tests verify all templates and agent files on install
- ✅ `bookContentDir` field added to `state.json` template and type definition

Still planned for v0.2.0:
- Atomic file writing for `state.json` to prevent corruption from concurrent writes
- `BookContext` struct to reduce parameter passing in functions
- Shared `constants.ts` for `SPEC_ROOT` and other shared values
- `--json` flag on `status` command for machine-readable output
- JSDoc on all exported functions
- `vitest.config.ts` for explicit test configuration
- Public assets (`public/book-producer-logo.svg`, workflow diagrams)
- Release automation scripts for GitHub releases

---

## Glossary

- **stage**: One of six workflow phases (init, plan, design, chapters, review, finalize)
- **spec memory**: Workflow files stored in `.spec/<slug>/` — not user-editable book content
- **book content**: User-created chapters and manuscript stored in `<slug>/` at repo root
- **slug**: Normalized book identifier (lowercase, hyphenated), derived from book name
- **branch mapping**: Registry tracking which books have been worked on per git branch
- **orchestration mode**: `sequential` (default, chat-friendly) or `parallel` (compute-friendly)
- **force-policy**: System requiring explicit user confirmation before destructive operations
