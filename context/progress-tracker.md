# Progress Tracker

## Current Phase

Implementation

## Current Goal

Database layer — SQLAlchemy async models + Alembic migrations for application history persistence

## Completed

- Defined specialized agent architecture
- Added shared ApplicationState
- Preserved mandatory human review invariant
- **Feature 01: Backend directory & file scaffold** — full `backend/app/` tree created
- `requirements.txt` generated and all 132 packages installed via `uv add`

### Graph Core
- **`app/graph/constants.py`** — node name constants, routing literals, `MATCH_SCORE_THRESHOLD`
- **`app/graph/state.py`** — `ApplicationState` TypedDict + 7 Pydantic models; `CompanyProfile` added
- **`app/graph/router.py`** — `route_after_planner` (fan-out), `route_after_match`, `route_after_review`, `route_after_apply`
- **`app/graph/builder.py`** — full `StateGraph`: 11 nodes, parallel fan-out, `interrupt_before=[HUMAN_REVIEW]`, re-tailor loop, `graph` singleton

### Tool Layer
- **`app/graph/tools/llm.py`** — NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2)
- **`app/graph/tools/resume_parser.py`** — `parse_pdf` (pypdf + `io.BytesIO`), `parse_docx` (python-docx), `parse_resume` dispatcher
- **`app/graph/tools/jd_parser.py`** — `fetch_jd` (httpx + BeautifulSoup), `normalize_jd`
- **`app/graph/tools/embeddings.py`** — `get_embeddings` (sentence-transformers, `lru_cache` singleton), `compute_similarity`, `score_resume_jd`
- **`app/graph/tools/browser.py`** — `BrowserSession` context manager (Playwright), `safe_fill`, `safe_click`, `upload_file`, `get_page_text`
- **`app/graph/tools/search.py`** — `search_web` (DuckDuckGo), `SearchResult` dataclass, `search_company`, `search_jobs`, `fetch_first_result`

### Agents (all 11)
- **`planner.py`** — input validation, seeds `approval_status`, no LLM
- **`resume_agent.py`** — `with_structured_output(CandidateProfile)`, SystemMessage + HumanMessage
- **`job_agent.py`** — URL-vs-raw-text detection, `with_structured_output(JobProfile)`
- **`company_agent.py`** — independent JD fetch (parallel node isolation)
- **`match_agent.py`** — two-stage scoring (embeddings pre-filter → LLM), 70/30 blend
- **`ats_agent.py`** — keyword coverage audit, feeds tailoring agent
- **`tailoring_agent.py`** — conditional prompt (first-run vs re-tailor on `rejection_feedback`)
- **`cover_letter_agent.py`** — `llm.bind(temperature=0.7)`, tone-matched to company culture
- **`human_review_agent.py`** — validation passthrough post-interrupt, no LLM
- **`apply_agent.py`** — ATS dispatcher (`_detect_platform`), `"skipped"` for unsupported platforms
- **`tracking_agent.py`** — terminal node, structured outcome log, UTC timestamp

### Automation Stubs
- **`app/automation/`** — `greenhouse.py`, `lever.py`, `workday.py`, `ashby.py`, `smartrecruiters.py` — correct `submit()` signature; full Playwright flows deferred to Sprint 3

### FastAPI Layer ✅ Smoke-tested
- **`app/api/schemas/application.py`** — `RunRequest`, `ApproveRequest`, `RunStarted`, `ReviewPayload`, `RunStatus`, `ResumeParseResponse`
- **`app/api/routes/health.py`** — `GET /health`
- **`app/api/routes/application.py`** — `POST /resume/parse`, `POST /runs/start` (BackgroundTasks + `thread_id`), `GET /runs/{id}/status`
- **`app/api/routes/review.py`** — `GET /runs/{id}/review` (`graph.get_state()`), `POST /runs/{id}/approve` (`graph.invoke()` resume)
- **`app/main.py`** — app factory, CORS, `/api/v1` prefix, startup/shutdown hooks
- **Smoke test passed** — `uvicorn` started cleanly; `POST /api/v1/resume/parse` returned `200 OK` with 5,418 chars extracted from a real PDF

### Docs
- **`context/project-overview.md`** — Technical Architecture section: stack table, pipeline diagram, state table, key decisions, repo layout

## In Progress

- Database layer (`app/db/`)

## Next Up

- **`app/db/database.py`** — SQLAlchemy async engine + session factory
- **`app/db/models/application.py`** — `ApplicationRecord` ORM model
- **Alembic migrations** — `alembic init`, initial migration
- **End-to-end graph smoke test** — invoke full graph with real resume + JD URL
- **Automation implementation** — full Playwright flows for Greenhouse + Lever (Sprint 3)

## Open Questions

- ~~Dynamic planner vs fixed routing?~~ **Resolved**: fixed routing (statically compiled graph, pure-function routers in `router.py`)
- ~~Parallel execution strategy?~~ **Resolved**: LangGraph native fan-out via `route_after_planner` returning a list

## Architecture Decisions

- Supervisor (Planner Agent) controls execution via fixed routing, not dynamic LLM dispatch.
- Specialized agents own one responsibility each.
- Human review remains mandatory before Apply Agent (`interrupt_before=[HUMAN_REVIEW]`).
- Two-stage match scoring: embeddings floor check → LLM detailed, 70/30 blended score.
- API schema ≠ graph state models — deliberate separation for independent evolution.
- LLM: NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2 extraction / 0.7 creative).

## Git

- `main` — stable baseline (2 commits: scaffold + gitignore)
- `dev`  — active development (5 commits: agents, tools, browser/search, FastAPI, fixes)
  - `00a2cf4` — tool layer + parsing agents
  - `f332d97` — remaining agents (tailoring, review, apply, tracking)
  - `2348fbd` — browser.py, search.py, automation stubs
  - `fcbc574` — FastAPI layer + project-overview update
  - `HEAD`    — fix: issue 01 (duckduckgo-search dep fix, NVIDIA_MODEL env var)

## Session Notes

Entire backend graph + API layer implemented in one session.
Server smoke-tested live: uvicorn started, `/resume/parse` hit with real PDF → 200 OK, 5,418 chars extracted.
**Issue 01 Resolved:** Fixed missing `duckduckgo-search` dependency. Moved hardcoded LLM model to `NVIDIA_MODEL` env var to address deprecation warning gracefully.
All work on `dev` branch — ready for DB layer then PR to `main`.
