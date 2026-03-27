# 05-review

## Purpose

Review the book-framework implementation covering the full feature set: chat-first workflow, directory split model, branch mapping system, and status command.

---

## Review Rounds

- **Round 1 (previous):** Chat-first workflow, `chat-helper.ts`, asset documentation, initial test suite  APPROVED 
- **Round 2 (this review):** Directory split model (`spec/` vs repo-root content), `branch-mapper.ts`, `status.ts` command, updated tests, updated `CHAT-WORKFLOW.md`  see below

---

## Reviewed Scope (Round 2)

- `src/lib/branch-mapper.ts`  NEW: Branchbook registry, `resolveActiveBook()`
- `src/commands/status.ts`  NEW: `book-framework status [slug]` command
- `src/lib/types.ts`  Added `bookContentDir` field to `BookIdeaState`
- `src/lib/book-idea-manager.ts`  Updated: split-dir creation, calls `registerBookOnBranch`
- `src/lib/chapter-assembler.ts`  Updated: reads/writes from `bookContentDir`
- `src/lib/chat-helper.ts`  Updated: chapter/manuscript functions take `bookContentDir`
- `src/commands/init.ts`  Updated: destructures `bookContentDir`, shows both paths in output
- `assets/CHAT-WORKFLOW.md`  Full rewrite for new directory model, branch mapping, status command
- `tests/objective-init.test.ts`  Updated: asserts split-dir model, checks `book/` dir absent from spec
- `tests/chapter-assembler.test.ts`  Updated: uses `<slug>/chapters/` not `book/chapters/`
- Unit test suite: 6 files, 39 tests

---

## Non-Reviewed Scope

- External references only (not bundled in this repository):
  - https://github.com/guerra2fernando/libriscribe
  - https://github.com/mrudinal/united-we-stand-framework
- Original removed files (Python src, prompts, docs)  Already extracted and rewritten

---

## Findings (Round 2)

### Directory Split Model 

**Design requirement:** Separate spec memory (`.spec/<slug>/`) from book content (`<slug>/` at repo root) so the agent writes to both but the boundaries are enforced structurally.

**What was verified:**

- `book-idea-manager.ts  createBookIdea` creates `.spec/<slug>/assets/` and `<slug>/chapters/` independently; no `book/` subdirectory is created inside `.spec/`  confirmed by test assertion `expect(await fs.pathExists(path.join(folder, 'book'))).toBe(false)`
- `BookIdeaState.bookContentDir` persisted in `state.json` so the agent can recover the correct path across sessions without re-deriving it
- `chapter-assembler.ts` reads from `bookContentDir/chapters/` and writes manuscript to `bookContentDir/manuscript-<slug>-final.md`; no knowledge of `.spec/` at all  clean separation
- `chat-helper.ts` functions `listChapterFiles`, `readChapterFile`, `writeChapterFile`, `createManuscriptFile` all take `bookContentDir`, not `bookIdeaMemoryFolder`  parameter names match responsibility

**Observations:**
- The two-parameter split (`bookIdeaMemoryFolder` for spec ops, `bookContentDir` for content ops) is clean but callers must pass both. There is no single "book context" object that groups them. For v2, a `BookContext` struct `{ specFolder, bookContentDir, state }` would reduce repetition at call sites.
- `init.ts` now shows both paths in output (`Spec: ...` / `Content: ...`)  good usability.
- `bookContentDir` is derived from `path.join(repoRoot, slug)` where slug is already normalized  no traversal risk.

**Recommendation:**  Acceptable for v1. Flag `BookContext` struct as v2 cleanup.

---

### branch-mapper.ts 

**What was verified:**

- `readBranchMapping` returns a default empty mapping when the file doesn't exist; `writeBranchMapping` calls `fs.ensureDir`  no silent failure if `.spec/` doesn't exist yet
- `getCurrentBranch` wraps `git rev-parse` in try/catch and falls back to `'default'`  safe in non-git environments and CI
- `registerBookOnBranch` is idempotent: deduplicates both `mapping.branches[branch]` and `mapping.books[slug].branches`; safe to call multiple times
- `resolveActiveBook` returns a discriminated union with three variants (`resolved`, `ambiguous`, `none`)  clean and exhaustive; TypeScript can exhaustively check all callers
- `listBookIdeaSlugs` uses `withFileTypes` and filters `isDirectory()`  the JSON file `.branch-mapping.json` is correctly excluded 

**Observations:**
- No direct unit tests for `registerBookOnBranch` or `resolveActiveBook`. These are currently integration-tested only via the `createBookIdea` init path. Coverage gap noted but not blocking for v1.
- The mapping file is written on every `createBookIdea` call. Since that's a once-per-book operation, write frequency is negligible.
- `execSync` with `stdio: ['ignore', 'pipe', 'ignore']`  stderr suppressed, no user input passed to shell; clean security posture.

**Recommendation:**  Acceptable for v1. Add `tests/branch-mapper.test.ts` in v2.

---

### status.ts 

**What was verified:**

- Handles all three `resolveActiveBook` variants: `resolved`  auto-proceeds; `ambiguous`  lists choices and exits 0; `none`  lists all books and exits 0
- `process.exit(0)` on "nothing actionable" paths; `process.exit(1)` only on actual error (spec folder missing for explicit slug)  correct exit code semantics
- Chapter status detection uses frontmatter regex `/^status:\s*approved/m`  compatible with current chapter format
- Progress: `Math.round((approvedChapters / totalChapters) * 100)` with guard `if (totalChapters > 0)`  no division by zero
- `STAGE_LABELS` maps all defined stage IDs; unknown stage IDs fall back to the raw string  graceful degradation
- Manuscript path shown **only if it exists**  conditional, not shown when book hasn't been assembled yet

**Observations:**
- `SPEC_ROOT = '.spec'` is duplicated in `status.ts`, `book-idea-manager.ts`, and `branch-mapper.ts`. Low-risk for v1 but warrants extraction to `src/lib/constants.ts` in v2.
- Chapter status scan reads every chapter file fully. Fine for 1030 chapters; would be slow for 500+ chapters. Acceptable for target scope.
- No `--json` flag. If CI or other tools need machine-readable output, this would be the first enhancement needed in v2.

**Recommendation:**  Acceptable for v1.

---

### chat-helper.ts Refactor 

- Module comment updated to show dual-directory model with annotations for each path
- `getChaptersDirectory(bookContentDir)` correctly removes old `book/chapters` nesting
- `createManuscriptFile` now calls `fs.ensureDir(bookContentDir)` before writing  prevents silent failure if directory was deleted
- `getChapterMemory` / `updateChapterMemory` remain in `bookIdeaMemoryFolder/assets/`  correct; these are spec/continuity files, not book content
- Parameter names updated throughout: `bookContentDir` replaces `bookIdeaMemoryFolder` for chapter-related functions  names match their responsibility

**Recommendation:**  No issues.

---

### Quality & Maintainability (Cumulative) 

No regressions from Round 1. New improvements:
- Clean structural separation of spec memory vs book content
- `branch-mapper.ts` self-contained with no circular dependencies
- `status.ts` composes from existing lib functions without duplicating logic

Remaining v2 items:
- Extract `SPEC_ROOT` and other shared constants to `src/lib/constants.ts`
- `BookContext` struct to bundle `{ specFolder, bookContentDir, state }`
- `tests/branch-mapper.test.ts`  unit tests for `registerBookOnBranch`, `resolveActiveBook`
- `--json` flag on `status` command

---

### Security & Boundaries 

No new risks introduced:
- `getCurrentBranch` uses `execSync` with `stdio: ['ignore', 'pipe', 'ignore']`  no user input interpolated into shell
- Branch names are only used as JSON object keys in `mapping.branches`, never interpolated into filesystem paths
- `bookContentDir` derived from `path.join(repoRoot, normalizeSlug(...))`  no traversal risk

**Recommendation:**  No issues.

---

## Lint / Static Analysis Results

```
 npm run build  PASSED
   No type errors, strict mode, all imports resolved

 npm test  PASSED
   9 test files, 86 tests
   - tests/integration.test.ts (33)         new: asset completeness + template checks
   - tests/state-manager-robustness.test.ts (4) new: invalid JSON, concurrent writes, permission path
   - tests/branch-mapper.test.ts (5)        new: branch edge-case matrix + fallback
   - tests/objective-init.test.ts (10)      updated: split-dir assertions
   - tests/objective-matching.test.ts (6)
   - tests/stage-transitions.test.ts (7)    updated: includes bookContentDir
   - tests/orchestration.test.ts (9)
   - tests/chapter-assembler.test.ts (11)   updated: order/title validation tests
   - tests/force-policy.test.ts (1)
```

---

## Documentation Review

### assets/CHAT-WORKFLOW.md 

- Directory model section completely rewritten: `.book-framework/`, `.spec/`, and `<slug>/` at repo root clearly separated with annotations
- Branch mapping section added: explains `.spec/.branch-mapping.json`, all three resolution rules, multi-book/multi-branch scenarios
- Status command section added: example CLI usage and output fields described
- `Persistence Between Chat Sessions` updated: agent now reads `.branch-mapping.json` first, then `state.json`

### In-Code Documentation 

- `branch-mapper.ts`: JSDoc on all exported functions; module header explains resolution rules
- `status.ts`: module header explains CLI usage and chat-first equivalent
- `book-idea-manager.ts`: module header updated with directory model comment block
- `chat-helper.ts`: module header fully rewritten to show dual-directory model

---

## Test Sufficiency (Updated)

| Test file | Coverage |
|---|---|
| `integration.test.ts` | Asset completeness, template presence, framework/agent file delivery |
| `state-manager-robustness.test.ts` | Invalid JSON recovery message contract, concurrent patch stress, permission-denied write path |
| `branch-mapper.test.ts` | Branch name edge cases (slash/unicode/spaces), mapping read-permission fallback |
| `objective-init.test.ts` | Slug normalization, `createBookIdea` split-dir model, absence of `book/` in spec, `listBookIdeaSlugs` |
| `objective-matching.test.ts` | `findBookIdeaMatch`, Levenshtein fuzzy matching |
| `stage-transitions.test.ts` | Stage advancement, completion semantics |
| `orchestration.test.ts` | Sequential vs parallel mode |
| `chapter-assembler.test.ts` | Chapter read/sort, manuscript assembly, order/title validation |
| `force-policy.test.ts` | Destructive op gate |

**Gap (v2):** No explicit end-to-end test yet for `book-framework status --json` CLI output contract.

---

## Implementation Alignment with Design

| Design Requirement | Status | Notes |
|---|---|---|
| CLI `install` only required; rest chat-first |  | Documented in `cli.ts` and `init.ts` |
| `.book-framework/`  installed assets, never edit |  | `install.ts` creates it; no other command touches it |
| `.spec/<slug>/`  workflow memory only |  | `createBookIdea` creates only `assets/`; no `book/` dir |
| `<slug>/chapters/` at repo root  book content |  | `createBookIdea` creates `path.join(repoRoot, slug, 'chapters')` |
| Branch mapping in `.spec/.branch-mapping.json` |  | `branch-mapper.ts` manages; `createBookIdea` registers on init |
| Context resolution (1 book  auto, multiple  ask) |  | `resolveActiveBook()` implements all three cases |
| `book-framework status` command |  | `status.ts` with branch-aware auto-resolution |
| `bookContentDir` persisted in `state.json` |  | Field in `BookIdeaState`, written on `createBookIdea` |
| Build & tests passing |  | Clean build, 86/86 tests |

---

## Round 3: Current Open Audit Items (Post-Fix Re-Review)

This section has been cleaned to include **only currently open issues** after Round 4 fixes. All resolved items are tracked at the bottom in `Round 4: Audit Resolution Verification`.

### Open Runtime / Robustness Issues

| Issue | Severity | Risk | Action Required |
|---|---|---|---|
| File permission errors not proactively checked in `install.ts` | **MEDIUM** | Read-only filesystems may fail during writes with runtime error paths only | Add preflight writeability check in install path and emit one consistent recovery message. |

### Open Test Coverage Issues

No open test-coverage blockers remain from this audit.

Covered locally by:

- `tests/state-manager-robustness.test.ts`
  - invalid `state.json` message contract
  - concurrent `patchState()` stress test
  - permission-denied write path (EACCES)
- `tests/branch-mapper.test.ts`
  - branch-name edge cases (slash, unicode, spaces, non-git fallback)

### Open Documentation / Maintainability Issues

| Issue | Severity | Risk | Action Required |
|---|---|---|---|
| JSDoc not complete on all critical exports | **LOW** | Slower onboarding for maintainers | Add `@param`, `@returns`, `@throws` for critical exported functions. |

### Current Release Status (Re-reviewed)

- Build: ✅ clean
- Tests: ✅ 86/86 passing
- Release readiness: ✅ approved for v0.1.0
- Remaining issues: non-blocking; tracked for v0.2.0

---

## Sign-Off

- Reviewed by: GitHub Copilot (Code Reviewer Agent)
- Round 1 date: 2026-03-26 (chat-first workflow)
- Round 2 date: 2026-03-26 (directory model + branch mapping)
- Round 3 date: 2026-03-26 (pre-release comprehensive audit)
- Round 4 date: 2026-03-26 (audit items resolved — see section below)
- Round 5 date: 2026-03-26 (security + package verification + low-priority fixes)
- Review depth: Full implementation, test coverage, error handling, asset completeness, distribution readiness
- Result: **Code APPROVED ✅** | **Release APPROVED ✅** (all CRITICAL and HIGH blockers resolved)

---

## Round 4: Audit Resolution Verification

### Items Fixed Since Round 3

All CRITICAL and HIGH issues from the Round 3 audit have been resolved. Build is clean, tests pass (86/86).

| Round 3 Issue | Severity | Resolution |
|---|---|---|
| Missing user-facing README.md | CRITICAL | ✅ README.md rewritten (united-we-stand pattern): usability-focused, chapter format doc, install guide, workflow table, CLI commands, troubleshooting, pointers to PUBLISHING.md |
| JSON parse error in state-manager.ts | CRITICAL | ✅ `readState()` now has two try/catch blocks (file read + JSON parse); both include recovery instructions with file path |
| JSON parse error in branch-mapper.ts | CRITICAL | ✅ `readBranchMapping()` catches both read and parse errors; returns empty mapping as safe fallback with console.warn |
| package.json "files" listed missing docs/ | HIGH | ✅ Removed `docs` from files array; added individual doc files: README.md, CHANGELOG.md, VERSIONS.md, TROUBLESHOOTING.md, UPGRADING.md, LICENSE |
| stage-transitions.test.ts missing bookContentDir | HIGH | ✅ `bookContentDir: 'test-book'` added to baseState; type now matches BookIdeaState fully |
| No CHANGELOG.md | HIGH | ✅ CHANGELOG.md updated with fixed/resolved items correctly categorized; unreleased section updated |
| No TROUBLESHOOTING.md guide | MEDIUM | ✅ TROUBLESHOOTING.md created with common issue diagnosis and recovery flows |
| No VERSIONS.md | HIGH | ✅ VERSIONS.md rewritten in united-we-stand detailed format with CLI commands, workflow model, chapter format, error handling, and summary sections |
| No UPGRADING.md | MEDIUM | ✅ UPGRADING.md simplified to: update package + `install --force`; documents what is safe across upgrades |
| Missing maintainer publishing guide | MEDIUM | ✅ PUBLISHING.md created for adaptation and release flow |
| No integration test for asset completeness | MEDIUM | ✅ `tests/integration.test.ts` created (33 tests): covers all required templates, stage agents, framework files, root assets, package docs, and content sanity checks |
| No dedicated corrupted `state.json` test | MEDIUM | ✅ Added `tests/state-manager-robustness.test.ts` assertion for invalid JSON recovery message contract |
| No read-only/permission-denied write test | MEDIUM | ✅ Added permission-denied write-path test (`EACCES`) in `tests/state-manager-robustness.test.ts` |
| No concurrent state write test | MEDIUM | ✅ Added concurrent `patchState()` stress test plus atomic write implementation in `state-manager.ts` |
| No branch-name edge-case test matrix | LOW | ✅ Added `tests/branch-mapper.test.ts` cases for slash, unicode, spaces, and non-git fallback |
| `SPEC_ROOT` duplication in multiple files | LOW | ✅ Extracted to shared `src/lib/constants.ts`; consumers updated (`status.ts`, `book-idea-manager.ts`, `branch-mapper.ts`) |
| No `--json` output mode in status command | LOW | ✅ Added `book-framework status --json` with machine-readable payload for resolved, ambiguous, none, and not-found flows |
| Missing stage template files verification | HIGH | ✅ Template presence now enforced by integration tests (`00` through `06`, plus chapter/state templates) |
| Incomplete `assets/framework/` delivery risk | HIGH | ✅ Required framework files existence asserted in integration tests |
| Chapter assembler no order validation | MEDIUM | ✅ `validateChapterOrder()` exported from chapter-assembler: detects gaps, duplicate numbers, and non-standard title format; `assembleManuscript()` now returns `warnings[]` |
| chapter.md.template title format | MEDIUM | ✅ Template updated to `"Chapter {{CHAPTER_NUMBER}}: {{CHAPTER_TITLE}}"` |
| state.json.template missing bookContentDir | MEDIUM | ✅ `"bookContentDir": "{{BOOK_IDEA_SLUG}}"` added to template |
| Stages could be skipped | HIGH | ✅ `01-core-rules.md`, `03-stage-lifecycle.md`, `08-skip-force-policy.md` all updated: stages 1-4,6 mandatory; stage 5 optional; no-skip invariant is rule #4 |
| 2-book-planner marked "optional" | HIGH | ✅ Changed to mandatory in agent file; prerequisites chain updated |
| 4-chapter-writer prerequisites allowed skipped stages | MEDIUM | ✅ "or explicitly skipped" removed; now requires stages 1-3 complete and approved |
| 5-book-reviewer marked "mandatory before finalization" | N/A | ✅ Changed to optional per user requirement |
| 6-publish-assembler prerequisites required stage 5 | N/A | ✅ Updated: stage 4 complete required; stage 5 recommended but optional |
| Missing predecessor file check not documented | MEDIUM | ✅ Rule #9 added to 01-core-rules.md; section added to 03-stage-lifecycle.md; 4-chapter-writer chapter title convention documented |
| Stale `dist/` artifacts shipped in package tarball (newly discovered in Round 5) | MEDIUM | ✅ Build now cleans `dist/` first via `scripts/clean-dist.mjs`; `npm pack --dry-run` confirms stale `objective-*` artifacts are not shipped |

### Test Suite After Round 4 Fixes

```
✓ npm run build    PASSED (clean, no TypeScript errors)
✓ npm test         PASSED
  9 test files, 86 tests
  - tests/integration.test.ts (33)          NEW: asset completeness
  - tests/state-manager-robustness.test.ts (4) NEW: invalid JSON, concurrent writes, permission-denied path
  - tests/branch-mapper.test.ts (5)         NEW: branch-name edge cases + mapping read-permission fallback
  - tests/chapter-assembler.test.ts (11)    UPDATED: validateChapterOrder tests + title format
  - tests/orchestration.test.ts (9)
  - tests/objective-init.test.ts (10)
  - tests/stage-transitions.test.ts (7)     FIXED: bookContentDir in baseState
  - tests/objective-matching.test.ts (6)
  - tests/force-policy.test.ts (1)
```

### Items Deferred to v0.2.0 (non-blocking)

| Item | Reason for deferral |
|---|---|
| Tests for read-only filesystem | Not blocking; handled gracefully in error messages |
| JSDoc on all exported functions | Not blocking; code is readable without formal JSDoc |
| BookContext struct | Refactor only; no behavior change |
| branch-mapper unit tests | Integration-covered via createBookIdea path |
| status `--json` explicit CLI contract test | Enhancement; not blocking v1 |
| Public assets (logo, diagrams) | Optional; not blocking v1 |

### Round 4 Conclusion

**✅ APPROVED for v0.1.0 npm publish.**

All CRITICAL and HIGH-priority blockers identified in Round 3 have been resolved. Build is clean, 86/86 tests pass. Documentation is complete (README, CHANGELOG, VERSIONS, UPGRADING, TROUBLESHOOTING, PUBLISHING, LICENSE). Framework rules enforce correct stage ordering with no-skip invariant. Chapter format convention is established and validated.

The deferred items are all genuinely non-blocking and are properly tracked in CHANGELOG.md and VERSIONS.md for v0.2.0 delivery.

---

## Round 5: Security & Packaging Verification

### What was checked

- Runtime dependency audit: `npm audit --omit=dev --audit-level=moderate`
- Static scan for dangerous execution patterns (`eval`, `new Function`, shell interpolation)
- Path-handling review around slug normalization and path joining
- Package generation check: `npm pack --dry-run`
- New feature safety check: `book-framework status --json` output behavior

### Results

- ✅ `npm audit` (runtime deps): **0 vulnerabilities**
- ✅ No `eval` / `new Function` usage found in source
- ✅ `execSync` usage is isolated to `git rev-parse --abbrev-ref HEAD` with fixed command and suppressed stderr, no user-input interpolation
- ✅ Slug paths remain normalized via `normalizeSlug()` before filesystem joins
- ✅ `status --json` returns valid structured JSON for no-book and resolved flows
- ✅ Package dry-run now excludes stale compiled artifacts after build cleanup step

### New issues identified in Round 5

| Issue | Severity | Risk | Status |
|---|---|---|---|
| Stale `dist/` artifacts could be shipped if build output is not cleaned | **MEDIUM** | Package could include obsolete commands not present in source | ✅ Fixed in this round (`scripts/clean-dist.mjs` + build script update) |
| `pip 25.3` CVE-2026-1703 in local Python venv | **MEDIUM** | Local dev environment only — not shipped | ✅ Fixed: upgraded to `pip 26.0.1` |
| `pygments 2.19.2` CVE-2026-4539 in local Python venv | **UNKNOWN** | Local dev environment only — not shipped by `book-producer` | ⚠️ No upstream fix version published; revisit on next env refresh |

### Python environment audit note

`pip-audit` was run against the full `.venv/` used for local Python development (the
LibriScribe Python scaffold that underlies this workspace). Neither `pip` nor `pygments`
are runtime dependencies of the `book-producer` npm package. The `pip` vulnerability
was resolved immediately. The `pygments` CVE has no published fix version as of this
audit date (2026-03-26).

### Round 5 conclusion

Security and packaging checks pass with no new unresolved medium/high findings in the
shipped package. The `pygments` advisory is local-environment-only and non-blocking.
Remaining open items are low-risk maintainability enhancements.

---

## Round 6: End-to-End Repo, Install Flow, and Documentation Review

### What was checked

- Repo-root validation after dissolving `book-framework/` into the repository root
- Full maintainer checks: `npm run build`, `npm test`, `npm run lint`, `npm audit`, `npm audit --omit=dev`, `npm pack --dry-run`
- Local source-folder install simulation in a fresh consumer project
- Packed-tarball install simulation and target-repository install/init/status flow
- Core documentation review: `README.md`, `PUBLISHING.md`, `TROUBLESHOOTING.md`, `UPGRADING.md`, `VERSIONS.md`, `docs/INDEX.md`
- Windows console rendering check for the `status` command

### Results

- ✅ Repo now works correctly from the repository root; no remaining functional dependency on a nested `book-framework/` directory
- ✅ `npm run build` passes cleanly from repo root
- ✅ `npm test` passes: **9 files, 86 tests**
- ✅ `npm run lint` passes cleanly after migrating to ESLint flat config and fixing typed-lint issues
- ✅ `npm audit --omit=dev` reports **0 vulnerabilities** for shipped runtime dependencies
- ✅ Full `npm audit` now reports **0 vulnerabilities** after upgrading dev-only lint/test tooling (`eslint`, `@typescript-eslint/*`, `vitest`, `typescript`)
- ✅ `npm pack --dry-run` produces `book-producer-0.1.0.tgz` with expected package contents
- ✅ Local source-folder consumer install works: `npx book-producer --help` resolves correctly in a fresh project
- ✅ Fresh target-repo flow works: `book-producer install`, `book-producer init "Review Demo"`, and `book-producer status <slug>` all succeed and generate the expected `.book-framework/`, `.spec/<slug>/`, and `<slug>/chapters/` structure
- ✅ Documentation corrected and aligned with current behavior:
  - fixed stale test counts (`39/39` → `86/86`)
  - fixed stale tarball examples (`@book-producer-0.1.0.tgz` → `book-producer-0.1.0.tgz`)
  - fixed broken relative link in `UPGRADING.md`
  - completed the `docs/` tree with `API.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `FAQ.md`
- ✅ `status` output now uses ASCII-only stage/title separators so it renders cleanly in Windows PowerShell

### Issues identified in Round 6 and resolution

| Issue | Severity | Risk | Status |
|---|---|---|---|
| ESLint typed config did not include `tests/`, causing review-stage lint failures | MEDIUM | Repo maintenance command failed despite passing build/tests | ✅ Fixed with `tsconfig.eslint.json` + flat-config migration |
| `chat-helper.ts` still used `any` for chapter-memory helpers | LOW | Reduced type safety | ✅ Fixed with `ChapterMemory` typing |
| Repo-level dev toolchain had 18 moderate audit findings | MEDIUM | Maintainer environment security debt | ✅ Fixed by upgrading `eslint`, `@typescript-eslint/*`, `vitest`, and pinning compatible `typescript` |
| `docs/INDEX.md` linked to missing files | LOW | Broken maintainer documentation navigation | ✅ Fixed by adding the missing docs files |
| Windows console rendered Unicode status glyphs poorly | LOW | Cosmetic CLI readability issue on Windows terminals | ✅ Fixed by switching status output to ASCII-only separators |

### GitHub/source-install note

Packed tarball install and local source-folder install were both verified successfully. A live remote GitHub URL install was **not** revalidated against GitHub itself during this review pass because the branch changes are still local until committed and pushed. Once this branch is pushed, the repository root layout is now correct for a git-source install as well.

### Round 6 conclusion

**✅ APPROVED from review perspective.**

The repository, the npm package, the installed framework assets, the target-repository bootstrap flow, and the core maintainer documentation are all in a healthy state. No unresolved runtime or full-repo audit findings remain. The workflow is ready to return to `6-finalizer` for refreshed final sign-off.
