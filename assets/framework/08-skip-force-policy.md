# Skip and Force Policy

## Skip Semantics

Book framework stages **cannot be skipped.** Stages 1, 2, 3, 4, and 6 are mandatory because each stage's output is used directly as input by the following stage. Without stage 2 (plan), stage 3 has no chapter list to design. Without stage 3 (design), stage 4 has no chapter contract to implement.

**The only optional stage is stage 5 (review).** The user may advance directly from stage 4 to stage 6 without performing a review pass. If skipped:
- Record stage 5 in `incompletedStages` in `state.json`.
- Note in `00-current-status.md` that the manuscript has not been editorially reviewed.
- Do not silently skip a stage without updating state.

## --force Semantics by Command

| Command | What `--force` does | What it never does |
|---|---|---|
| `install --force` | Overwrites all managed `.book-framework/` files with package defaults | Bypasses approval gates |
| `init --force` | Resets bootstrap files (status, init) for the selected book idea; preserves chapter files | Deletes chapter files |
| `refresh --force` | Re-applies all managed templates even over existing content | Bypasses approval gates |
| `finalize --force` | Explicit bypass path for approved finalization only | Skips user confirmation before cleanup |

## Force Safety Rules

1. Every destructive force action must print a warning describing what will be affected.
2. Confirmation is required: interactive `y/n` prompt, or `--yes` flag for CI paths.
3. Force never bypasses stage-advancement approval gates.
4. Force never deletes chapter files under `<book-slug>/chapters/`.
5. Finalization cleanup always requires explicit user confirmation regardless of `--force`.
