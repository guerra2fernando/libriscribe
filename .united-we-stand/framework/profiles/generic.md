# Generic Profile

Applies to all repositories regardless of language.

## Coding and Design Expectations

- Prefer clarity over cleverness.
- Keep modules cohesive and functions focused.
- Use descriptive naming; avoid vague or single-letter identifiers in non-trivial contexts.
- Reduce avoidable complexity with guard clauses and small helpers.
- Extract duplicated logic into reusable units.
- Avoid magic constants when named constants/enums improve readability.

## Documentation Expectations

- Keep implementation rationale explicit.
- Document meaningful tradeoffs, risks, and open questions.
- Add comments only when they explain intent/boundary decisions.

## Reliability and Security Expectations

- Validate external inputs and boundary conditions.
- Handle errors intentionally; do not swallow errors.
- Add structured logging for important failures and branch-critical operations.
- Minimize dependencies and justify new packages.

## Testing Expectations

- Add tests proportionate to risk and change impact.
- Favor Arrange-Act-Assert structure.
- Mock external I/O boundaries where appropriate.
- Include negative and edge-case coverage for critical paths.

## Review Expectations

- Verify conformance, quality, security, testing, and documentation impact.
- Flag missing ownership checks and over-exposed data shapes for API/data changes.