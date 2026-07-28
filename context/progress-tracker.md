# Progress Tracker

## Current Phase

Session 5 — Phase 17: Workday, Ashby, SmartRecruiters automation + apply_agent refactor

## Current Goal

1. Implement full Playwright automation for Workday, Ashby, and SmartRecruiters.
2. Refactor `apply_agent.py` to use the shared `dispatcher.dispatch()` (remove duplication).
3. ATSPlatformsPage — update platform status badges to reflect new implementations.
4. Issue 03 — blocked on user Supabase dashboard action (no change needed from code side).

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
- **`app/automation/workday.py`** ✅ — `data-automation-id` selectors, multi-step wizard navigation, resume upload + fallback, cover letter, confirmation detection
- **`app/automation/ashby.py`** ✅ — Apply button click, standard HTML5 form fill, label-proximity cover letter fallback, confirmation
- **`app/automation/smartrecruiters.py`** ✅ — Apply Now click, personal info, styled-button upload fallback, cover letter, URL+element confirmation
- **`app/automation/dispatcher.py`** ✅ — URL-pattern platform detection + dispatch to correct module + AutomationLogger integration
- **`app/graph/agents/apply_agent.py`** ✅ — Refactored: uses `dispatcher.dispatch()`, threads `thread_id` for SSE logging, removed duplicate detection logic

### FastAPI Layer ✅ Smoke-tested
- **`app/api/schemas/application.py`** — `RunRequest`, `ApproveRequest`, `RunStarted`, `ReviewPayload`, `RunStatus`, `ResumeParseResponse`
- **`app/api/routes/health.py`** — `GET /health`
- **`app/api/routes/application.py`** — `POST /resume/parse`, `POST /runs/start` (BackgroundTasks + `thread_id`), `GET /runs/{id}/status`
- **`app/api/routes/review.py`** — `GET /runs/{id}/review` (`graph.aget_state()`), `POST /runs/{id}/approve` (`graph.ainvoke()` resume)
- **`app/api/routes/jobs.py`** — `GET /jobs/search` (DDG proxy)
- **`app/api/routes/history.py`** — `GET /history`, `GET /history/{thread_id}`
- **`app/api/routes/logs.py`** ✅ — `GET /runs/{id}/logs` (snapshot), `GET /runs/{id}/logs/stream` (SSE)
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

### Utility Layer (filled in Session 4)
- **`app/utils/logger.py`** ✅ — `AutomationLogger` with in-memory buffer + SSE pub/sub queues; `get_logs()`, `subscribe()`, `unsubscribe()`
- **`app/automation/dispatcher.py`** ✅ — URL-pattern ATS detection (`detect_platform`) + `dispatch()` with AutomationLogger

### Utility Stubs (still empty — post-MVP)
- **`app/vectorstore/faiss.py`** — FAISS vector store
- **`app/vectorstore/indexing.py`** — indexing pipeline
- **`app/workers/celery_app.py`** — Celery app config
- **`app/workers/application_tasks.py`** — Celery tasks
- **`app/workers/indexing_tasks.py`** — Celery indexing tasks

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
- **`AutomationLogsPage.tsx`** ✅ — SSE live stream via `EventSource`; run selector dropdown; LIVE indicator + animated pulse dot; replay animation; per-level filter
- **`ATSPlatformsPage.tsx`** ✅ — Platform cards: Greenhouse ✅, Lever ✅, Workday ✅, Ashby ✅, SmartRecruiters ✅, LinkedIn/Indeed 📋 — 5/5 automation completed
- **`HistoryPage.tsx`** ✅ — Full dedicated page: expandable per-run state-transition timeline, document links, automation logs nav; replaces Stubs.tsx redirect
- **Sidebar** — Review Queue badge live from `useDashboardData`; footer user name/email from `recon_profile` localStorage
- **`Stubs.tsx`** — Fully superseded; no routes point to it

---

## In Progress

- **Issue 03** — Supabase DB password reset still required. MemorySaver fallback active; all non-DB routes functional.

---

## Next Up (Prioritized)

| # | Item | Depends On |
|---|------|------------|
| 1 | **Issue 03** — Reset Supabase DB password → update `.env` → re-run Alembic migrations → smoke-test with real Postgres | User action (Supabase dashboard) |
| 2 | **Phase 18: Auth & Settings sync** — Persist settings/profile to Supabase user record instead of localStorage | Issue 03 fixed |
| 3 | **Log durability** — Persist `AutomationLogger` entries to DB so logs survive server restart | Issue 03 fixed |
| 4 | **LinkedIn Easy Apply** — OAuth integration + LinkedIn-specific automation | Sprint 5 |
| 5 | **Vectorstore + Celery** — FAISS indexing, async task queue (post-MVP) | — |

---

## Open Questions

- **Supabase DB password**: Reset pending (Issue 03). User must reset in Supabase dashboard → update `DATABASE_URL` + `CHECKPOINT_DATABASE_URL` in `backend/.env`.
- **AutomationLogs storage**: Chosen **process-local in-memory buffer** (simpler, zero deps). Logs survive within a single server process but are lost on restart. DB persistence deferred to post-MVP (Phase 18).
- ~~History page scope~~ **Resolved**: Implemented as expandable per-run state-transition timeline (distinct from ApplicationsPage table).

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
  - `a6980c4` — docs: update progress tracker — issue 03, phases 13-14, git branch correction
  - `29917e1` — feat: phases 15-16 — SSE automation logs, full history page, dispatcher + logger stubs filled
  - `ece0233` — feat: phase 17 — Workday, Ashby, SmartRecruiters Playwright automation + apply_agent refactor ← HEAD
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

**Session 5:** Phase 17 complete — 5/5 ATS platforms now fully automated. Implemented:
- `app/automation/workday.py` — multi-step wizard + `data-automation-id` selectors + confirmation detection
- `app/automation/ashby.py` — Apply button + label-proximity cover letter + confirmation
- `app/automation/smartrecruiters.py` — Apply Now + styled-button upload fallback + URL/element confirmation
- `app/graph/agents/apply_agent.py` — refactored: delegates to `dispatcher.dispatch()`, threads `thread_id` for SSE
- `ATSPlatformsPage.tsx` — Workday/Ashby/SmartRecruiters promoted to implemented (green cards)
- Zero TS errors · uv import check passed · git commit `ece0233` · pushed main + dev
