# 04-implementation

## What changed
Built the `book-framework` npm package from scratch: CLI binary, command modules, lib utilities, framework asset docs, agent markdown files, stage templates, and tests. Then refactored the workflow semantics so stage 3 is the final book design handoff, stage 4 materializes `book/chapters/` with one file per designed chapter, stage 5 is the quality/editorial review pass, and stage 6 concatenates chapter files without rewriting them. Original LibriScribe Python source files were deleted after all content was extracted into framework agent docs.

## Why it changed
Per `03-design.md`: replace the Python LibriScribe runtime with a Claude-first, multi-agent book creation framework distributed as an npm package, installable in any repository. The later refactor aligned the workflow to the real content pipeline: initialize idea → plan work → design final book contents → implement the book → editorial/quality review → final assembly.

## Implementation log

### Phase 1 — Package scaffold
- [x] `book-framework/package.json`
- [x] `book-framework/tsconfig.json`
- [x] `book-framework/.eslintrc.json`
- [x] `book-framework/bin/book-framework.js`

### Phase 2 — CLI entry + command router
- [x] `book-framework/src/cli.ts`

### Phase 3 — Lib modules
- [x] `book-framework/src/lib/types.ts`
- [x] `book-framework/src/lib/state-manager.ts`
- [x] `book-framework/src/lib/book-idea-manager.ts`
- [x] `book-framework/src/lib/template-engine.ts`
- [x] `book-framework/src/lib/force-policy.ts`
- [x] `book-framework/src/lib/orchestration.ts`
- [x] `book-framework/src/lib/chapter-assembler.ts`

### Phase 4 — CLI commands
- [x] `book-framework/src/commands/install.ts`
- [x] `book-framework/src/commands/init.ts`
- [x] `book-framework/src/commands/list.ts`
- [x] `book-framework/src/commands/use.ts`
- [x] `book-framework/src/commands/doctor.ts`
- [x] `book-framework/src/commands/refresh.ts`

### Phase 5 — Framework asset docs
- [x] `book-framework/assets/AGENTS.md`
- [x] `book-framework/assets/framework/01-core-rules.md`
- [x] `book-framework/assets/framework/02-state-model.md`
- [x] `book-framework/assets/framework/03-stage-lifecycle.md`
- [x] `book-framework/assets/framework/04-command-routing.md`
- [x] `book-framework/assets/framework/08-skip-force-policy.md`
- [x] `book-framework/assets/framework/09-orchestration-policy.md`

### Phase 6 — Agent markdown files
- [x] `book-framework/assets/agents/1-book-init.md`
- [x] `book-framework/assets/agents/2-book-planner.md`
- [x] `book-framework/assets/agents/3-book-designer.md`
- [x] `book-framework/assets/agents/4-chapter-writer.md`
- [x] `book-framework/assets/agents/5-book-reviewer.md`
- [x] `book-framework/assets/agents/6-publish-assembler.md`
- [x] `book-framework/assets/agents/standalone/book-project-manager.md`
- [x] `book-framework/assets/agents/standalone/concept-architect.md`
- [x] `book-framework/assets/agents/standalone/book-outliner.md`
- [x] `book-framework/assets/agents/standalone/developmental-editor.md`
- [x] `book-framework/assets/agents/standalone/line-editor.md`
- [x] `book-framework/assets/agents/standalone/character-world-designer.md`
- [x] `book-framework/assets/agents/standalone/research-fact-integrity.md`
- [x] `book-framework/assets/agents/standalone/chapter-arc-architect.md`
- [x] `book-framework/assets/agents/standalone/continuity-checker.md`
- [x] `book-framework/assets/agents/standalone/book-blurb-writer.md`
- [x] `book-framework/assets/agents/standalone/sensitivity-reader.md`

### Phase 7 — Stage templates
- [x] `book-framework/assets/templates/state.json.template`
- [x] `book-framework/assets/templates/00-current-status.md.template`
- [x] `book-framework/assets/templates/01-init.md.template`
- [x] `book-framework/assets/templates/02-plan.md.template`
- [x] `book-framework/assets/templates/03-design.md.template`
- [x] `book-framework/assets/templates/04-implementation.md.template`
- [x] `book-framework/assets/templates/05-review.md.template`
- [x] `book-framework/assets/templates/06-finalization.md.template`
- [x] `book-framework/assets/templates/chapter.md.template`
- [x] `book-framework/assets/templates/chapter-memory.json.template`

### Phase 8 — Tests
- [x] `book-framework/tests/objective-init.test.ts`
- [x] `book-framework/tests/objective-matching.test.ts`
- [x] `book-framework/tests/stage-transitions.test.ts`
- [x] `book-framework/tests/orchestration.test.ts`
- [x] `book-framework/tests/chapter-assembler.test.ts`
- [x] `book-framework/tests/force-policy.test.ts`

### Phase 9 — Implementation cleanup
- [x] Deleted: `src/`
- [x] Deleted: `prompts/`
- [x] Deleted: `requirements.txt`
- [x] Deleted: `setup.py`
- [x] Deleted: `__init__.py` (root)
- [x] Deleted: `CONTRIBUTING.md`
- [x] Deleted: `docs/`

## Cleanup log
Deleted after all agent content extracted and rewritten into `book-framework/assets/agents/`:
- `src/libriscribe/` — Python agents, utilities, settings adapted into markdown agent docs
- `prompts/templates/` — YAML prompt templates rewritten as agent instruction sections
- Root Python packaging files and Docusaurus docs site no longer applicable

## Files touched
See Implementation log above.

## Validation and tests executed
- `npm install` at repo root — dependencies installed successfully after flattening the package to the repository root
- `npm run build` — first run failed on strict optional typing in 3 command files; fixed by conditionally spreading `autoYes` only when defined; second run passed
- `npm test` — full test suite via vitest passed (`9` files, `86` tests)
- Post-refactor rebuild/test after workflow changes (`book/chapters` layout, stage 3/4/5/6 contract changes, no-rewrite finalizer) — passed

## Lint / static-analysis
- TypeScript strict mode enabled in `tsconfig.json`
- ESLint configured at repo root; `npm run lint` passes after flat-config migration and typed test-project coverage fix

## Remaining gaps / follow-ups
- Amazon metadata artifacts (`book-blurb-writer` output integration into `06-finalization`) deferred to v2
- Public package name/scope issue resolved: package renamed to `book-producer` before first publish
- Compatibility aliases with `united-we-stand` commands not implemented (open question from init)
- `sensitivity-reader` agent instruction is a first-pass draft; professional editorial review recommended before use in production

## Amendment - multi-tool release and orchestration refresh

### What changed
- Added dual release preparation for npm (`book-producer`) and GitHub Packages (`@<owner>/book-producer`)
- Replaced the stale docs deploy workflow with package CI and publish workflows
- Installed managed tool entrypoint sections/files for Claude, Copilot, Cursor, and Antigravity that point back to `.book-framework/`
- Added `book-producer orchestrate chapters` and `book-producer orchestrate research` commands to emit tool-specific work packets
- Installed `.book-framework/CHAT-WORKFLOW.md` and `.book-framework/tooling/`
- Hardened branch detection for unborn branches by preferring `git symbolic-ref --short HEAD`
- Updated docs to explain that `.book-framework/` is installed in user repos, `.spec/<slug>/` stores specs, and later stage files are created lazily

### Validation rerun
- `npm run build`
- `npm test` (`12` files, `101` tests)
- `npm run lint`
- `npm run prepare:publish:npm`
- `BOOK_PRODUCER_GITHUB_SCOPE=@mrudinal npm run prepare:publish:github`
- `npm pack ./.release/npm`
- `npm pack ./.release/github`
- Fresh target repo smoke test: `install`, `init`, `orchestrate`, and `doctor` all passed

## Amendment - gitignore cleanup

### What changed
- Reorganized the root `.gitignore` into grouped sections for dependencies, build outputs, environment files, temp/log files, and editor/OS noise
- Added common temp/runtime artifacts such as `*.log`, `*.tmp`, `tmp/`, `temp/`, npm/yarn/pnpm debug logs, and `.tmp-review-summary.txt`
- Added npm cache entries plus `package-lock.json` to the ignore list per the requested housekeeping pass

### Notes
- `package-lock.json` is already a tracked file in this repository, so adding it to `.gitignore` affects new/untracked cases only and does not automatically remove the existing tracked file from git history or index
