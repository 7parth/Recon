# Progress Tracker

## Current Phase

Session 4 — Resume from Issue 03 fix + tackle next open items

## Current Goal

1. Fix Supabase DB credentials (Issue 03) — reset password, update `.env`, re-run Alembic migrations, smoke-test full end-to-end with real Postgres persistence.
2. Build out AutomationLogs live-stream backend (SSE log endpoint).
3. Build full History page (dedicated view replacing the redirect stub).
4. Implement Workday, Ashby, SmartRecruiters Playwright automation (Phase 15).

---

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

### Automation Layer
- **`app/automation/greenhouse.py`** — full Playwright form fill + resume upload via `BrowserSession`
- **`app/automation/lever.py`** — full Playwright form fill + resume upload via `BrowserSession`
- **`app/automation/workday.py`** — stub (Sprint 4)
- **`app/automation/ashby.py`** — stub (Sprint 4)
- **`app/automation/smartrecruiters.py`** — stub (Sprint 4)
- **`app/automation/dispatcher.py`** — empty file (needs implementation)

### FastAPI Layer ✅ Smoke-tested
- **`app/api/schemas/application.py`** — `RunRequest`, `ApproveRequest`, `RunStarted`, `ReviewPayload`, `RunStatus`, `ResumeParseResponse`
- **`app/api/routes/health.py`** — `GET /health`
- **`app/api/routes/application.py`** — `POST /resume/parse`, `POST /runs/start` (BackgroundTasks + `thread_id`), `GET /runs/{id}/status`
- **`app/api/routes/review.py`** — `GET /runs/{id}/review` (`graph.aget_state()`), `POST /runs/{id}/approve` (`graph.ainvoke()` resume)
- **`app/api/routes/jobs.py`** — `GET /jobs/search` (DDG proxy)
- **`app/api/routes/history.py`** — `GET /history`, `GET /history/{thread_id}`
- **`app/main.py`** — lifespan factory, CORS, `/api/v1` prefix, startup/shutdown hooks, graceful MemorySaver fallback
- **Smoke test passed** — `uvicorn` started cleanly; `POST /api/v1/resume/parse` returned `200 OK` with 5,418 chars extracted from a real PDF

### Database & Storage Layer ✅
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

### Utility Stubs (empty files — to be implemented)
- **`app/utils/logger.py`** — empty (structured JSON logging for automation events)
- **`app/vectorstore/faiss.py`** — empty (FAISS vector store)
- **`app/vectorstore/indexing.py`** — empty (indexing pipeline)
- **`app/workers/celery_app.py`** — empty (Celery app config)
- **`app/workers/application_tasks.py`** — empty (Celery tasks)
- **`app/workers/indexing_tasks.py`** — empty (Celery indexing tasks)
- **`app/automation/dispatcher.py`** — empty (ATS platform dispatch logic)

### Docs
- **`context/project-overview.md`** — Technical Architecture section: stack table, pipeline diagram, state table, key decisions, repo layout

### Issues Resolved
- **Issue 01** — Missing `duckduckgo-search` dep; moved hardcoded LLM model to `NVIDIA_MODEL` env var
- **Issue 02** — Supabase integration complete — async SQLAlchemy, Supabase Storage, AsyncPostgresSaver all wired
- **Issue 04** — Graceful MemorySaver fallback implemented; connection timeout reduced; server starts cleanly even with bad DB creds

### Frontend — All Pages Implemented ✅
- **`Dashboard.tsx`** — Stats cards + quick-action panel; live data from `useDashboardData`
- **`ReviewQueuePage.tsx`** — Live queue fetched from `GET /api/v1/history`; links to ReviewDetail
- **`ReviewDetail.tsx`** — Full human review UI; approve/reject with feedback; `POST /runs/{id}/approve`
- **`JobSearchPage.tsx`** — Search live listings via DDG `GET /jobs/search`; Copy URL flow
- **`ResumesPage.tsx`** — Card grid of all app runs with original + tailored resume download links
- **`ProfilePage.tsx`** — Candidate identity form (name, email, phone, LinkedIn, portfolio); localStorage
- **`ApplicationsPage.tsx`** — Full table: search, status filter, sort by date/score, inline Review link, document download
- **`ActivityPage.tsx`** — Chronological event timeline from `useDashboardData`; animated status nodes
- **`KeywordsPage.tsx`** — Skills & keyword tag cloud; add/remove/save with localStorage
- **`SettingsPage.tsx`** — Match threshold slider, auto-apply toggle, NVIDIA model dropdown, embedding model input; localStorage
- **`IntegrationsPage.tsx`** — API key reference cards (NVIDIA + Supabase); `.env.example` code block; copy-env-var buttons
- **`SavedJobsPage.tsx`** — Bookmarked listings from localStorage; remove + copy-URL-for-run actions
- **`AutomationLogsPage.tsx`** — Terminal-style Playwright log viewer; per-level filter; demo data (needs live backend)
- **`ATSPlatformsPage.tsx`** — Platform cards (Greenhouse ✅, Lever ✅, Workday 🟡, Ashby 🟡, SmartRecruiters 🟡, LinkedIn/Indeed 📋)
- **Sidebar** — Review Queue badge live from `useDashboardData`; footer user name/email from `recon_profile` localStorage
- **`Stubs.tsx`** — Only `History` remains as a redirect stub → `/applications`

---

## In Progress

- **Issue 03** — Supabase DB password reset still required. MemorySaver fallback active; all non-DB routes functional.
- **`app/automation/dispatcher.py`** — Empty stub; ATS platform dispatch logic unimplemented.
- **History page** — `history` route is a redirect to `/applications`. Full dedicated page deferred.
- **AutomationLogs live stream** — Page uses demo data; backend SSE log endpoint not yet implemented.

---

## Next Up (Prioritized)

| # | Item | Depends On |
|---|------|------------|
| 1 | **Issue 03** — Reset Supabase DB password → update `.env` → re-run Alembic migrations → smoke-test with real Postgres | User action (Supabase dashboard) |
| 2 | **Phase 15: AutomationLogs live stream** — Backend SSE `GET /runs/{id}/logs` endpoint + frontend polling/EventSource | — |
| 3 | **Phase 16: History page** — Replace redirect stub with dedicated filtered timeline view | — |
| 4 | **Phase 17: Workday, Ashby, SmartRecruiters Playwright automation** | Sprint 4 |
| 5 | **Phase 18: Auth & Settings sync** — Persist settings/profile to Supabase user record instead of localStorage | Issue 03 fixed |
| 6 | **`app/automation/dispatcher.py`** — Wire ATS platform detection → correct automation module | Phase 17 progress |
| 7 | **`app/utils/logger.py`** — Structured JSON logging for Playwright automation events | Phase 15 |
| 8 | **Vectorstore + Celery** — FAISS indexing, async task queue (post-MVP) | — |

---

## Open Questions

- **Supabase DB password**: Reset pending (Issue 03). User must reset in Supabase dashboard → update `DATABASE_URL` + `CHECKPOINT_DATABASE_URL` in `backend/.env`.
- **AutomationLogs storage**: Should logs be stored in DB (durable, replayable) or a process-local buffer (simpler)? DB preferred.
- **History page scope**: Mirror of Applications table (same data, different UX) vs. true event log (all state transitions per run)?

---

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

---

## Git

- `main` — active development branch (all work committed here)
  - `00a2cf4` — tool layer + parsing agents
  - `f332d97` — remaining agents (tailoring, review, apply, tracking)
  - `2348fbd` — browser.py, search.py, automation stubs
  - `fcbc574` — FastAPI layer + project-overview update
  - `1811d9d` — fix: issue 01 (duckduckgo-search dep fix, NVIDIA_MODEL env var)
  - `d02b280` — fix: graceful DB fallback + faster connection timeout
  - `ba4c972` — feat: phase 10 — JobSearch, Resumes, Profile pages
  - `62a03ee` — feat: phases 11-14 — all remaining frontend pages + dynamic sidebar
  - `a6980c4` — docs: update progress tracker — issue 03, phases 13-14, git branch correction ← HEAD
- `dev` — stale branch (ahead of initial scaffold; superseded by main)

---

## Session Notes

**Session 1:** Entire backend graph + API layer implemented.
Server smoke-tested live: uvicorn started, `/resume/parse` hit with real PDF → 200 OK, 5,418 chars extracted.
Issue 01 resolved: fixed missing `duckduckgo-search` dep; NVIDIA_MODEL env var.
Issue 02 resolved: Supabase integration complete — async SQLAlchemy, Supabase Storage, AsyncPostgresSaver wired.
Issue 03 active: DB password placeholder (`SecretPass123!`) causing PgBouncer circuit breaker. Graceful MemorySaver fallback in place.

**Session 2:** Full frontend implemented: Dashboard, ReviewQueue, ReviewDetail, JobSearch, Resumes, Profile.

**Session 3:** All remaining stub pages — Applications, Activity, Keywords, Settings, Integrations, SavedJobs, AutomationLogs, ATSPlatforms. Zero TypeScript errors. Sidebar wired — review badge live from API, footer from localStorage profile.

**Session 4 (current):** Full project-state audit. Identified 7 empty utility/worker stub files. Confirmed all 15 frontend pages implemented. Confirmed Greenhouse + Lever automation complete. Prioritized next steps: Issue 03 DB fix → AutomationLogs SSE → History page → Workday/Ashby/SmartRecruiters automation → Auth sync.
