# AI Workflow Rules

## Approach

Build this project incrementally using a spec-driven workflow. Context files (`architecture.md`, `progress-tracker.md`, and this file) define what to build, how to build it, and the current state of progress. Always implement against these specs — do not infer or invent graph behavior, state shape, or platform support from scratch. Each LangGraph node, API route, or automation target should trace back to something written in `project-overview.md` or `architecture.md` before it's coded.

## Scoping Rules

- Work on one feature unit at a time (one graph node, one API route, one ATS platform integration)
- Prefer small, verifiable increments over large speculative changes
- Do not combine unrelated system boundaries in a single implementation step (e.g. don't touch the tailoring node and the Playwright apply node in the same change)

## When to Split Work

Split an implementation step if it combines:

- LangGraph node logic and the human-review interrupt/checkpointing plumbing
- Resume/JD parsing changes and match-scoring changes
- Browser automation for more than one ATS platform at a time
- FastAPI route changes and background worker (Celery/arq) changes
- Behavior not clearly defined in the context files

If a change cannot be verified end to end quickly, the scope is too broad — split it.

## Handling Missing Requirements

- Do not invent product behavior not defined in the context files — this includes never relaxing or bypassing the human-review checkpoint before submission
- If a requirement is ambiguous, resolve it in the relevant context file before implementing
- If a requirement is missing, add it as an open question in `progress-tracker.md` before continuing

## Protected Files

Do not modify the following unless explicitly instructed:

- `.env` / any secrets or credential files (ATS login sessions, API keys)
- Playwright storage-state / session files used for authenticated ATS sessions
- LangGraph checkpointer schema/migrations once in use
- Any third-party library internals

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- Graph structure, node boundaries, or state schema (`architecture.md`)
- Storage model decisions (Postgres tables, Redis key patterns)
- Code conventions or standards
- Feature scope, including any change to which ATS platforms are supported

## Before Moving to the Next Unit

1. The current unit works end to end within its defined scope
2. No invariant defined in `architecture.md` was violated — in particular, no submission path bypasses human review
3. `progress-tracker.md` reflects the completed work
4. Relevant tests pass (`pytest`) and the app starts cleanly (`docker compose up`)

## Multi-Agent Rules

- Add one agent at a time.
- Each agent owns a single responsibility.
- Agents communicate only through ApplicationState.
- Planner Agent performs routing; worker agents never invoke each other directly.
- Human Review Agent must remain before Apply Agent.

## Supabase Rules

- Never access Supabase (client, storage, or DB session) directly from graph nodes.
- All database access must go through `app/db/repositories/` — agents are pure functions of state.
- All file storage access must go through `app/services/storage_service.py`.
- Agents receive storage URLs as part of `ApplicationState`; they never perform uploads.
- This keeps agents fully testable without a live Supabase connection.
