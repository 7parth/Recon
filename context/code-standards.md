# Code Standards

## General

- Keep modules small and single-purpose — one node, one route, one platform integration per file
- Fix root causes, do not layer workarounds — if a node's output shape is wrong, fix the node, don't patch it downstream
- Do not mix unrelated concerns in one function or route
- Prefer explicit, readable code over clever abstractions — this codebase will be read in an interview setting

## Python

- Type hints are required throughout the project — no untyped function signatures
- Avoid `dict`/`Any` for structured data — use `TypedDict`, `pydantic` models, or dataclasses with explicit fields
- Validate unknown external input (JD text, scraped listings, form field data) at system boundaries before trusting it — never pass raw scraped/LLM output straight into a DB write or a form fill
- Prefer `pydantic` models for anything crossing a boundary (API request/response, LLM structured output, DB rows)

## LangGraph

- Each node is a pure function of `ApplicationState` in, `ApplicationState` (or a partial update) out — no hidden globals or side effects outside what's returned
- Conditional routing logic lives in dedicated router functions, not inlined inside a node
- The `human_review_node` interrupt is never bypassed or stubbed out, including in test/dev graphs — use a mock approval source instead of removing the node
- Prompts used by a node live in the same module as that node, not in a shared prompt-dump file

## Prompts & LLM Output

- All LLM calls that need structured output request it explicitly (function calling / structured output mode) — never parse free text with regex when a structured mode is available
- Prompts are version-controlled like code; a prompt change that alters tailoring behavior is a reviewable diff, not a live edit
- Never hardcode a specific model name deep in node logic — model selection is configured once and injected

## API Routes (FastAPI)

- Validate and parse request input (via pydantic) before any logic runs
- Every route that touches an application's state confirms it against the current LangGraph checkpoint before acting — no route mutates application state directly
- Return consistent, predictable response shapes across routes (status, data, error fields)
- Routes never call Playwright or LLM logic directly — they trigger or read from the graph, nothing else

## Data and Storage

- **Structured metadata** (status, scores, timestamps, relationships, file URLs) belongs in **Supabase PostgreSQL** via SQLAlchemy
- **Documents** (resume.pdf, tailored_resume.pdf, cover_letter.pdf, Playwright screenshots) belong in **Supabase Storage** — the database stores the returned public URL, not the file content
- Redis holds only cache and queue data — nothing that would be a problem to lose
- Playwright session/storage-state files are kept outside the main repo/data directories, treated as credentials
- Never store large text blobs in DB rows — if content exceeds ~4 KB, put it in Supabase Storage and store the URL

## Supabase Access Rules

- **Graph nodes must never access Supabase directly** — no `supabase.storage.from_()` or `AsyncSession` calls inside agent functions
- All database access goes through `app/db/repositories/` — one repository class per entity
- All file storage access goes through `app/services/storage_service.py`
- The Supabase client and SQLAlchemy session are injected via FastAPI dependencies (`app/dependencies.py`), never imported directly in routes or agents

## File Organization

- `graph/` — LangGraph nodes, state schema, routing functions, prompts
- `api/` — FastAPI routes, request/response models
- `automation/` — Playwright modules, one per ATS platform
- `db/` — SQLAlchemy models, async engine, Supabase client, repositories, migrations
- `storage/` — Supabase Storage wrappers: `storage.py`, `resume_storage.py`, `document_storage.py`
- `services/` — business logic: `storage_service.py`, `checkpoint_service.py`, etc.
- `workers/` — Celery/arq task definitions for async run execution
- `tests/` — mirrors the above structure; one test module per node/route/platform