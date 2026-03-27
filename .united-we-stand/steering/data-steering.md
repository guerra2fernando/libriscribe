# Data Steering

Use this file when the repo owns schemas, migrations, analytics, or data pipelines.

## Schema and Diagram Expectations

- For SQL database work, capture both conceptual and implementation-level structure.
- Each process that interacts with the database should have:
  - a flowchart
  - a sequence diagram
  - an entity-relationship model (`modelo de entidad relacion`)
  - a relational model (`modelo relacional`)

## SQL File Organization

- Keep SQL commands in correctly named files separated by purpose, such as create, alter/update, seed, policy/RLS, rollback, or backfill work.
- SQL files should have clear file-level comments stating purpose, scope, and execution intent.
- If a `supabase/` directory exists, keep SQL migration files inside `supabase/migrations/`.
- If SQL files already exist outside `supabase/migrations/` in a repo that uses Supabase, move or rewrite them into `supabase/migrations/` unless the user explicitly requests otherwise.
- Use names that make the function obvious, for example timestamped migration files with purpose suffixes such as `create_users_table`, `update_booking_indexes`, or `rls_appointments_policies`.

## Migration Rules

- Separate schema creation, data correction, and security-policy work when that separation improves reviewability.
- Comment non-trivial SQL blocks to explain intent, assumptions, and ordering constraints.
- Prefer idempotent or explicitly guarded operations when the platform/workflow expects rerunnable scripts.

## Data Safety Expectations

- Make ownership, access control, and retention implications explicit for schema changes.
- Document compatibility or rollout concerns when migrations affect live data or existing consumers.
