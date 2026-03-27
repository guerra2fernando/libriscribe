# Coding Steering

This file defines repo-specific coding conventions that `4-implementer` must
follow for every code change and `5-code-reviewer` must enforce during review.
When this file is more specific than a profile doc, this file wins.

## Formatting and consistency

- Follow Airbnb JS/TS style guidance unless a stricter repo rule in this file overrides it.
- Keep code consistently formatted with configured formatter/linter rules when present.
- Order imports consistently.
- Prefer clarity over cleverness.
- Small, composable functions are mandatory.
- Keep modules cohesive so each file has one main responsibility.
- Use `const` by default; use `let` only when reassignment is required; avoid `var`.
- Avoid deep nesting by using early returns, guard clauses, and small helpers.
- Do not leave oversized functions in place when they can be split into smaller helpers with clearer responsibilities.
- If a function starts mixing responsibilities, repeated condition branches, or long sequential logic, split it before considering the implementation complete.

## Naming conventions

- Use explicit, intent-revealing names instead of abbreviations.
- Function and method names must describe what they do using `verb + object` naming where practical, such as `createAppointmentSlots`, `validateBookingRequest`, or `loadAvailableDays`.
- Avoid vague names such as `doThing`, `handle`, `process`, `run`, `q`, or `fn1` for core logic.
- Do not use single-letter identifiers, including in loops, callbacks, and temporary variables.
- Prefer descriptive iteration and callback names such as `index`, `dayIndex`, `slotIndex`, `hourIndex`, `day`, `hour`, `appointment`, `user`, `request`, `error`, `event`, `response`, or `document`.
- Use `camelCase` for variables and functions.
- Use `PascalCase` for classes and components.
- Use `UPPER_SNAKE_CASE` only for values that are truly constant and shared.

## Commenting and documentation preferences

- Commenting requirements in this section are mandatory for `4-implementer` and must be enforced by `5-code-reviewer`.
- Every function and method must have a short JSDoc-style doc comment immediately above it.
- Keep function and method doc comments to one brief sentence describing behavior.
- Every changed code file must contain at least one intent-focused code comment.
- If a file contains only one small function, that file still must include at least one short comment explaining what the function does.
- Add `//` inline comments before each non-trivial block to explain intent, boundary handling, or reasoning.
- When a block is small but important, still add a short comment if it clarifies why the code exists.
- Do not comment obvious code paths line by line; comment intent, boundaries, and why the block exists.

## Error-handling preferences

- Handle errors intentionally and do not swallow exceptions.
- Prefer predictable control flow and avoid hidden side effects.

## Shared utilities rules

- If logic is needed in more than one place, extract it into a shared function or module.
- Prefer `utils/` for general-purpose helpers.
- Prefer `lib/` for domain-specific shared logic.
- Add at least minimal tests for shared utilities.

## Dependency policy

- Keep dependencies minimal and justify every new package.
- Prefer built-in platform APIs before adding third-party dependencies when they are sufficient.
- Prefer popular, maintained libraries with active releases and a solid security posture when a dependency is necessary.
- Do not add deprecated or unmaintained packages when a maintained alternative exists.
- Do not add packages with known active vulnerabilities.
- Maintain the appropriate lockfile for the package manager in use.
- Before merging a dependency change in npm-based repositories, run `npm audit` and address reported vulnerabilities by updating, replacing, or removing the dependency.

## SonarQube-aligned quality rules

- Follow common SonarQube-style clean code guidance as mandatory review criteria.
- Avoid large functions. If a function grows beyond a small, easy-to-scan unit or starts carrying multiple responsibilities, split it into helpers before calling the work done.
- Use strict equality (`===`, `!==`) instead of loose equality except for intentional safe nullish checks.
- Do not import a module into itself.
- Avoid absolute import paths unless repo conventions explicitly require alias-based imports.
- Use `Number.isNaN()` for `NaN` checks.
- Prefer spread syntax over redundant `.apply()` usage.
- Prefer object spread syntax over `Object.assign()` when it is appropriate and equivalent.
- Keep function and method names compliant with the naming rules in this file.
- Remove unused variables, unused assignments, and dead code.
- Avoid duplicated logic.
- Avoid code shapes that would predictably trigger routine SonarQube-style maintainability findings when a straightforward cleanup is available.
