# Glossary

- **Stage / Step**: numbered workflow phase (`0` to `6`).
- **Current stage**: active stage anchor for branch, or `none` when the workflow has been explicitly closed after finalizer confirmation.
- **Completed steps**: stages explicitly advanced from.
- **Incompleted stages**: started stages skipped/forced past before completion.
- **Next recommended step**: next logical action given current state, or `none` when the workflow is explicitly closed.
- **Status note**: plain-language explanation of active state and next action.
- **Framework agent**: numbered stage role in core workflow.
- **Standalone role agent**: on-demand specialist outside stage sequence.
- **Spec**: persistent markdown branch state.
- **Steering**: repo-specific guidance layer.
- **Profile**: language/project-type rule layer.
- **Bypass / Force**: explicit override of normal progression with traceability preserved.
- **Closed workflow**: branch state reached only after explicit user confirmation in `6-finalizer`, represented by `Current stage = none`.
- **Traceability**: mapping requirement lifecycle across stages.
