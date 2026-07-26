# Progress Tracker

## Current Phase

Blocked — Supabase DB password reset required (Issue 03)

## Current Goal

Fix Supabase DB credentials (Issue 03), run Alembic migrations against live DB, smoke-test full end-to-end pipeline with real Postgres persistence.

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

### Issues Resolved
- **Issue 01** — Missing `duckduckgo-search` dep; moved hardcoded LLM model to `NVIDIA_MODEL` env var

### Supabase Integration ✅ (Issue 02)
- **`app/config.py`** — Supabase env vars
- **`app/db/database.py`** — async SQLAlchemy engine via Supabase PostgreSQL connection string
- **`app/db/supabase.py`** — Supabase async client singleton
- **`app/db/models/`** — ORM models (`ApplicationRecord`, `Company`, `Job`, `Resume`, `Review`) with storage URL fields
- **`app/db/repositories/`** — async repository pattern
- **`app/storage/`** — `storage.py`, `resume_storage.py`, `document_storage.py`
- **`app/services/storage_service.py`** — upload documents, return public URLs
- **`app/services/checkpoint_service.py`** — AsyncPostgresSaver wired to Supabase Postgres
- **`backend/.env.example`** — Supabase env vars added
- **Alembic migrations** — initial schema created

### Supabase API Integration ✅ (Issue 02 - API Layer)
- **`app/main.py`** — Use FastAPI `lifespan` to initialize AsyncPostgresSaver globally
- **`app/graph/builder.py`** — Replaced global graph singleton with dynamic lifespan compilation
- **`app/api/routes/application.py`** — Removed in-memory `_runs` dict. Implemented `ApplicationRepository` with async sessions. Rewrote background tasks using `ainvoke`.
- **`/resume/parse`** — Integrated `StorageService` to upload raw resumes to Supabase Storage and return public URL.
- **`app/api/routes/review.py`** — Removed `_runs`. Human review endpoints now fetch checkpoint state directly via `app.state.graph.aget_state()` and update the DB accordingly.
- **End-to-end graph smoke test** — invoked full graph with real resume + JD URL, successfully hit `pending_review` breakpoint, stored documents in Supabase buckets.

- **Automation implementation** — full Playwright flows for Greenhouse + Lever (Sprint 3)
  - Updated `CandidateProfile` to extract `first_name`, `last_name`, `email`, `phone`, `linkedin_url`, `leetcode_url`.
  - Updated `greenhouse.py` and `lever.py` to use `BrowserSession` context manager.
  - Implemented form fills via `safe_fill` and resume upload via `upload_file`.
  - Added screenshot capture on automation error.

### Phase 7 & 8 API Integration ✅
- **`app/api/schemas/jobs.py`** — Added `JobSearchResponse` and `JobSearchResult`
- **`app/api/schemas/history.py`** — Added `ApplicationRecordResponse` and `HistoryListResponse`
- **`app/api/routes/jobs.py`** — Added `GET /jobs/search` to proxy DDG web search (Phase 7)
- **`app/api/routes/history.py`** — Added `GET /history` and `GET /history/{thread_id}` for persistence tracking (Phase 8)
- **`app/main.py`** — Registered new routers

### Phase 10: Frontend Subpages ✅
- **`JobSearchPage.tsx`** — Search live listings via DDG, `GET /jobs/search`, Copy URL flow
- **`ResumesPage.tsx`** — Card grid of all app runs with original + tailored resume download links
- **`ProfilePage.tsx`** — Candidate identity form (name, email, phone, LinkedIn, portfolio); localStorage

### Phase 11 & 12: Remaining Frontend Pages ✅
All "under construction" stubs replaced with full pages. `Stubs.tsx` now only holds `History` (redirect).

- **`ApplicationsPage.tsx`** — Full applications table: search, status filter, sort by date/score, inline Review link, document download links
- **`ActivityPage.tsx`** — Chronological event timeline derived from `useDashboardData` history; animated status nodes
- **`KeywordsPage.tsx`** — Skills & keyword tag cloud; add/remove/save with localStorage; used by ATS audit agent
- **`SettingsPage.tsx`** — Preferences page: match threshold slider, auto-apply toggle, NVIDIA model dropdown, embedding model input; localStorage
- **`IntegrationsPage.tsx`** — API key reference cards (NVIDIA + Supabase); `.env.example` code block; copy-env-var buttons
- **`SavedJobsPage.tsx`** — Bookmarked listings from localStorage; remove + copy-URL-for-run actions
- **`AutomationLogsPage.tsx`** — Terminal-style Playwright log viewer; per-level filter (INFO/DEBUG/WARN/ERROR/SUCCESS); animated replay playback
- **`ATSPlatformsPage.tsx`** — Platform cards (Greenhouse ✅, Lever ✅, Workday 🟡, Ashby 🟡, SmartRecruiters 🟡, LinkedIn/Indeed 📋) with implementation status

### Phase 13 & 14: Sidebar Wiring ✅
- **`Sidebar.tsx`** — Review Queue badge now driven live from `useDashboardData` (`stats.in_review`); hides when count is 0
- **`Sidebar.tsx`** — Footer user name / initials / email pulled from `recon_profile` localStorage (set via ProfilePage)

### Issues Resolved
- **Issue 03** — Supabase PgBouncer circuit breaker triggered by wrong DB password (`SecretPass123!` placeholder). **Graceful fallback implemented**: `app.main` lifespan catches the connection timeout and falls back to `MemorySaver` — server starts cleanly and all non-DB routes work. **Action required**: reset DB password in Supabase dashboard, update `DATABASE_URL` + `CHECKPOINT_DATABASE_URL` in `backend/.env`.

## In Progress

- **Issue 03** — Reset Supabase DB password → update `.env` → re-run Alembic migrations → re-smoke-test.
- **History page** — Currently a redirect to `/applications`. Full dedicated view deferred.
- **AutomationLogs live stream** — Page uses demo data; needs real log endpoint from backend.

## Next Up

- **Issue 03 (BLOCKED)** — Fix DB password → re-run migrations → smoke-test full pipeline with Postgres.
- **Phase 15: Automation Layer** — Full Playwright flows for Workday, Ashby, SmartRecruiters (Sprint 3/4).
- **Phase 16: Auth & Settings sync** — Persist settings/profile to Supabase user record instead of localStorage.
- **Phase 17: AutomationLogs live stream** — Backend log endpoint + SSE or polling for real Playwright traces.

## Open Questions

- ~~Dynamic planner vs fixed routing?~~ **Resolved**: fixed routing (statically compiled graph, pure-function routers in `router.py`)
- ~~Parallel execution strategy?~~ **Resolved**: LangGraph native fan-out via `route_after_planner` returning a list
- **Supabase project**: Does user have a Supabase project created? If not, create one at [supabase.com](https://supabase.com) and capture `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and the direct Postgres connection string.

## Architecture Decisions

- Supervisor (Planner Agent) controls execution via fixed routing, not dynamic LLM dispatch.
- Specialized agents own one responsibility each.
- Human review remains mandatory before Apply Agent (`interrupt_before=[HUMAN_REVIEW]`).
- Two-stage match scoring: embeddings floor check → LLM detailed, 70/30 blended score.
- API schema ≠ graph state models — deliberate separation for independent evolution.
- LLM: NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2 extraction / 0.7 creative).
- **Database: Supabase PostgreSQL** — managed, hosted Postgres. SQLAlchemy async talks to it via direct connection string. No local Postgres required.
- **Storage: Supabase Storage** — resume.pdf, tailored_resume.pdf, cover_letter.pdf stored in buckets. DB models store URLs, not blobs.
- **LangGraph checkpointer: AsyncPostgresSaver** — pointed at Supabase Postgres. Interrupted workflows survive server restarts.
- **Graph nodes never access Supabase directly** — all DB/storage access goes through repositories and services.

## Git

- `main` — active development branch (all work committed here)
  - `00a2cf4` — tool layer + parsing agents
  - `f332d97` — remaining agents (tailoring, review, apply, tracking)
  - `2348fbd` — browser.py, search.py, automation stubs
  - `fcbc574` — FastAPI layer + project-overview update
  - `1811d9d` — fix: issue 01 (duckduckgo-search dep fix, NVIDIA_MODEL env var)
  - `d02b280` — fix: graceful DB fallback + faster connection timeout
  - `ba4c972` — feat: phase 10 — JobSearch, Resumes, Profile pages
  - `62a03ee` — feat: phases 11-14 — all remaining frontend pages + dynamic sidebar ← HEAD
- `dev` — stale branch (ahead of initial scaffold; superseded by main)

## Session Notes

Entire backend graph + API layer implemented in session 1.
Server smoke-tested live: uvicorn started, `/resume/parse` hit with real PDF → 200 OK, 5,418 chars extracted.
**Issue 01 Resolved:** Fixed missing `duckduckgo-search` dependency. Moved hardcoded LLM model to `NVIDIA_MODEL` env var.
**Issue 02 Resolved:** Supabase integration complete — async SQLAlchemy, Supabase Storage, AsyncPostgresSaver all wired.
**Issue 03 Active:** DB password placeholder (`SecretPass123!`) causing PgBouncer circuit breaker. Graceful MemorySaver fallback in place — server runs, all non-DB routes functional. Fix: reset password in Supabase dashboard.
**Session 2:** Full frontend implemented: Dashboard, ReviewQueue, ReviewDetail, JobSearch, Resumes, Profile.
**Session 3:** All remaining stub pages — Applications, Activity, Keywords, Settings, Integrations, SavedJobs, AutomationLogs, ATSPlatforms. Zero TypeScript errors.
**Session 3 (cont):** Sidebar wired — review badge live from API, footer from localStorage profile.
