# Profile Selection

Always apply profiles in this order:

1. `generic.md`
2. one primary language profile
3. one primary project-type profile

If stack is mixed, read all relevant profiles and let steering docs break ties.

## Role Application

- `4-implementer` must apply selected profiles when coding/testing.
- `5-code-reviewer` must evaluate code against selected profiles.
- Other framework roles should use profiles when writing technical guidance that depends on language/runtime behavior.

## Examples

- JS frontend app -> `javascript-typescript.md` + `web-app.md`
- Python API -> `python.md` + `api-service.md`
- Go CLI -> `go.md` + `cli-tool.md`
