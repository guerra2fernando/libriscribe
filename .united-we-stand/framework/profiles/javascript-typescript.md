# JavaScript / TypeScript Profile

## Coding Guidance

- Follow Airbnb JS/TS style guidance unless repo conventions override specific rules.
- Prefer `const` by default; use `let` only when reassignment is required; avoid `var`.
- Use descriptive `verb + object` function naming.
- Avoid vague names like `handle`, `process`, `run`, `doThing` for core logic.
- Avoid single-letter identifiers for non-trivial values (`i`, `e`, `a`, `b`); prefer intent-revealing names.
- Prefer strict equality (`===`, `!==`) except intentional nullish checks.
- Avoid deep nesting; use guard clauses and helpers.
- Prefer spread/object spread over legacy patterns where equivalent.
- Use `Number.isNaN()` rather than global `isNaN()`.
- Avoid absolute imports unless repo conventions explicitly require alias-based imports.
- Avoid self-imports and clean unused variables/assignments.

## Documentation Guidance

- Use JSDoc/TSDoc on exported and non-trivial functions/methods.
- For complex blocks, add short intent-focused comments.

## Quality and Security Checks

- Avoid introducing vulnerable, deprecated, or unmaintained packages.
- Keep dependencies minimal and justify new ones.
- Treat ESLint, parser-based AST analysis, and similar static-analysis tooling as mandatory quality inputs when the repository provides them.
- Run package audit commands when dependency graph changes:
  - `npm audit`
  - `pnpm audit`
  - `yarn audit`
- In npm-based repos, prefer running `npm audit` at implementation close when feasible.
- Ensure user-controlled values do not flow into unsafe sinks without validation.
- Ensure authn/authz ownership checks for resource-level operations.

## Testing and Validation

- Run lint, parser/static-analysis checks, tests, and build using repo commands when available.
- Add/adjust tests for changed behavior and high-risk paths.
- Prefer Arrange-Act-Assert layout in tests.
- Verify changed runtime paths behave as expected in local/dev environment.
- At implementation close, verify changes against plan and design notes; record intentional deviations.

## Reviewer Focus

Reviewers should additionally check:

- complexity hotspots and duplication
- stale or dead code
- unsafe data exposure in API responses
- dependency risk introduced by new packages
- lint/parser/static-analysis findings for the changed scope and whether they were addressed or intentionally deferred
