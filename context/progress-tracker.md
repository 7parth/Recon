# Progress Tracker

## Current Phase

Session 8 — Phase 19 (LinkedIn Easy Apply) completed ✅

## Current Goal

1. **Phase 20: Vectorstore + Celery** — FAISS indexing, candidate embedding search, background task queue (post-MVP)

---

## Completed

- Defined specialized agent architecture
- Added shared ApplicationState
- Preserved mandatory human review invariant
- **Feature 01: Backend directory & file scaffold** — full `backend/app/` tree created
- `requirements.txt` generated and all 132 packages installed via `uv add`

### Graph Core
- **`app/graph/constants.py`** — node name constants, routing literals, `MATCH_SCORE_THRESHOLD`
- **`app/graph/state.py`** — `ApplicationState` TypedDict + 7 Pydantic models; `CompanyProfile` added; `match_score_threshold` added
- **`app/graph/router.py`** — `route_after_planner` (fan-out), `route_after_match` (respects `match_score_threshold`), `route_after_review`, `route_after_apply`
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
- **`app/automation/dispatcher.py`** ✅ — URL-pattern platform detection + dispatch to correct module + AutomationLogger integration; LinkedIn added (6 platforms total)
- **`app/graph/agents/apply_agent.py`** ✅ — Refactored: uses `dispatcher.dispatch()`, threads `thread_id` for SSE logging, removed duplicate detection logic

### LinkedIn Easy Apply (Phase 19) ✅
- **`app/automation/linkedin_auth.py`** ✅ — `get_session_path()` (env var / default), `load_session()` (cookie injection), `save_session()` (storage_state persist), `is_session_valid()` (live feed-page check), `session_file_exists()`
- **`app/automation/linkedin_login.py`** ✅ — One-time CLI interactive login; headed Playwright browser; polls for `/feed` redirect; auto-saves session; `python -m app.automation.linkedin_login`
- **`app/automation/linkedin.py`** ✅ — Full Easy Apply automation: session load + validation → job navigate → Easy Apply modal click → multi-step handling (phone, resume upload, cover letter, Next/Review/Submit) → confirmation detection; best-effort, returns `False` gracefully on unhandled steps
- **`app/api/routes/linkedin.py`** ✅ — `GET /api/v1/linkedin/auth/status` (live Playwright session validity check), `POST /api/v1/linkedin/auth/init` (starts headed login in background thread)
- **`app/config.py`** ✅ — `linkedin_session_path` setting (env: `LINKEDIN_SESSION_PATH`)
- **`.gitignore`** ✅ — `.linkedin_session.json` and `*_error.png` excluded from VCS
- **`app/tests/test_linkedin_automation.py`** ✅ — 22 unit tests (URL detection, dispatcher routing, session path, auth helpers, config); **22/22 passed**

### FastAPI Layer & End-to-End Pipeline Tests ✅
- **`app/api/schemas/application.py`** — `RunRequest`, `ApproveRequest`, `RunStarted`, `ReviewPayload`, `RunStatus`, `ResumeParseResponse`
- **`app/api/routes/health.py`** — `GET /health`
- **`app/api/routes/application.py`** — `POST /resume/parse`, `POST /runs/start` (BackgroundTasks + `thread_id`), `GET /runs/{id}/status`
- **`app/api/routes/review.py`** — `GET /runs/{id}/review` (`graph.aget_state()`), `POST /runs/{id}/approve` (`graph.ainvoke()` resume)
- **`app/api/routes/jobs.py`** — `GET /jobs/search` (DDG proxy)
- **`app/api/routes/history.py`** — `GET /history`, `GET /history/{thread_id}`
- **`app/api/routes/logs.py`** ✅ — `GET /runs/{id}/logs` (snapshot), `GET /runs/{id}/logs/stream` (SSE)
- **`app/tests/test_e2e_pipeline.py`** ✅ — Full end-to-end pipeline test suite verifying graph execution, pause at human review interrupt, approval resumption, state transitions, and tracking. Passed 100%.

### Database & User Persistence Layer (Phase 18) ✅
- **`app/config.py`** — Supabase env vars
- **`app/db/database.py`** — async SQLAlchemy engine via Supabase PostgreSQL connection string + `dispose_engine` helper
- **`app/db/supabase.py`** — Supabase async client singleton
- **`app/db/models/`** — ORM models (`ApplicationRecord`, `CompanyRecord`, `JobRecord`, `ResumeRecord`, `ReviewRecord`, `AutomationLogRecord`, `UserProfileRecord`, `UserSettingsRecord`)
- **`app/db/repositories/`** — async repository pattern (`ApplicationRepository`, `AutomationLogRepository`, `UserRepository`)
- **`app/api/schemas/user.py`** — Pydantic schemas for `UserProfileResponse`, `UserProfileUpdate`, `UserSettingsResponse`, `UserSettingsUpdate`
- **`app/api/routes/user.py`** — FastAPI endpoints `GET/PUT /api/v1/user/profile` and `GET/PUT /api/v1/user/settings`
- **`app/tests/test_user_api.py`** ✅ — Async test suite for profile and settings endpoints. Passed 100%.
- **`app/storage/`** — `storage.py`, `resume_storage.py`, `document_storage.py`
- **`app/services/storage_service.py`** — upload documents, return public URLs
- **`app/services/checkpoint_service.py`** — AsyncPostgresSaver wired to Supabase Postgres
- **Alembic migrations** — initial schema (`ecca31836228`), added `job_title` & `company_name` (`8804cb3c4a4d`), added `automation_logs` (`ce969023baf9`), added `user_profiles` & `user_settings` (`f92a101b4567`)

### Utility Layer ✅
- **`app/utils/logger.py`** ✅ — `AutomationLogger` with in-memory buffer + SSE broadcast + asynchronous Supabase PostgreSQL log persistence + cold-load DB fallback
- **`app/automation/dispatcher.py`** ✅ — URL-pattern ATS detection (`detect_platform`) + `dispatch()` with AutomationLogger

### Frontend — Profile & Settings Backend Sync & Clean Build ✅
- **`ProfilePage.tsx`** ✅ — Candidate identity form (name, email, phone, LinkedIn, portfolio); synced with `GET/PUT /api/v1/user/profile` + `localStorage` fallback
- **`SettingsPage.tsx`** ✅ — Preferences form (match threshold slider, auto-apply toggle, NVIDIA model, embedding model); synced with `GET/PUT /api/v1/user/settings` + `localStorage` fallback
- **`Dashboard.tsx`** — Stats cards + quick-action panel; live data from `useDashboardData`
- **`ReviewQueuePage.tsx`** — Live queue fetched from `GET /api/v1/history`; links to ReviewDetail
- **`ReviewDetail.tsx`** — Full human review UI; approve/reject with feedback; `POST /runs/{id}/approve`
- **`JobSearchPage.tsx`** — Search live listings via DDG `GET /jobs/search`; Copy URL flow
- **`ResumesPage.tsx`** — Card grid of all app runs with original + tailored resume download links
- **`ApplicationsPage.tsx`** — Full table: search, status filter, sort by date/score, inline Review link, document download
- **`ActivityPage.tsx`** — Chronological event timeline from `useDashboardData`; animated status nodes
- **`KeywordsPage.tsx`** — Skills & keyword tag cloud; add/remove/save with localStorage
- **`IntegrationsPage.tsx`** ✅ — API key reference cards (NVIDIA + Supabase) + **LinkedIn Session card**: live `GET /api/v1/linkedin/auth/status` poll, "Connect LinkedIn" button → `POST /api/v1/linkedin/auth/init`, 5s polling while waiting, animated pulse dot, `.env.example` updated
- **`SavedJobsPage.tsx`** — Bookmarked listings from localStorage; remove + copy-URL-for-run actions
- **`AutomationLogsPage.tsx`** — SSE live stream via `EventSource`; run selector dropdown; LIVE indicator + animated pulse dot
- **`ATSPlatformsPage.tsx`** ✅ — Platform cards: Greenhouse ✅, Lever ✅, Workday ✅, Ashby ✅, SmartRecruiters ✅, **LinkedIn Easy Apply ✅** — **6/6 automation completed**
- **`HistoryPage.tsx`** — Full dedicated page: expandable per-run state-transition timeline, document links, automation logs nav
- **Production Build** ✅ — `npm run build` completed cleanly in 155ms with zero TypeScript compilation or bundle errors

### Test Infrastructure
- **`pyproject.toml`** — Added `[tool.pytest.ini_options]` with `pythonpath = ["."]` and `asyncio_mode = "auto"`

---

## In Progress

- Phase 19 completed. System is ready for Phase 20 (Vectorstore + Celery).

---

## Next Up (Prioritized)

| # | Item | Depends On |
|---|------|------------|
| 1 | **Phase 20: Vectorstore + Celery** — FAISS indexing, candidate embedding search, background task queue | — |

---

## Architecture Decisions

- Supervisor (Planner Agent) controls execution via fixed routing, not dynamic LLM dispatch.
- Specialized agents own one responsibility each.
- Human review remains mandatory before Apply Agent (`interrupt_before=[HUMAN_REVIEW]`).
- Two-stage match scoring: embeddings floor check → LLM detailed, 70/30 blended score. Respects `match_score_threshold` set in ApplicationState and UserSettings.
- API schema ≠ graph state models — deliberate separation for independent evolution.
- LLM: NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2 extraction / 0.7 creative).
- **Database: Supabase PostgreSQL** — managed, hosted Postgres. SQLAlchemy async talks to it via direct connection string.
- **User Profile & Preferences Persistence** — stored in `user_profiles` and `user_settings` tables in Supabase Postgres via `UserRepository`. Frontend components sync with API endpoints and fallback to `localStorage` when offline.
- **Storage: Supabase Storage** — resume.pdf, tailored_resume.pdf, cover_letter.pdf stored in buckets.
- **LangGraph checkpointer: AsyncPostgresSaver** — pointed at Supabase Postgres. Interrupted workflows survive server restarts.
- **Automation Logs: In-memory SSE buffer + PostgreSQL persistence (`automation_logs` table)**. Logs stream live in real time and persist across server restarts.
- **Shared frontend data: `DashboardDataContext`** — single `GET /history` fetch per mount, shared across Sidebar, Dashboard, HistoryPage, etc. via React context.
- **LinkedIn Easy Apply: Stored Playwright session** — user logs in once via `python -m app.automation.linkedin_login` (headed browser); session persisted to `.linkedin_session.json` (git-ignored); reused for all subsequent headless automation runs. Session validity checked live before each run via `is_session_valid()`. Re-authentication available via IntegrationsPage UI or CLI.

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
  - `ece0233` — feat: phase 17 — Workday, Ashby, SmartRecruiters Playwright automation + apply_agent refactor
  - `0e2cfa5` — feat: session 6 — context-backed dashboard data, history data contract alignment, log DB persistence
  - `6fc5a87` — feat: phase 18 — user profile & settings DB sync + e2e pipeline smoke test
  - `11a2ecc` — feat: phase 19 — LinkedIn Easy Apply automation + auth API + frontend integration
- `dev` — target branch for release pushes
