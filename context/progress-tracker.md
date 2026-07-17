# Progress Tracker

## Current Phase

Implementation

## Current Goal

Implement backend agents and API layer following the scaffolded structure

## Completed

- Defined specialized agent architecture
- Added shared ApplicationState
- Preserved mandatory human review invariant
- **Feature 01: Backend directory & file scaffold** — full `backend/app/` tree created (graph, agents, prompts, tools, automation, api, db, services, vectorstore, workers, utils, tests)
- `requirements.txt` generated and all 132 packages installed via `uv add`
- **`app/graph/constants.py`** — all node name constants and routing literals defined (`PLANNER`, `RESUME_AGENT`, …, `TRACKING_AGENT`, `APPROVED`, `REJECTED`, `MATCH_SCORE_THRESHOLD`)
- **`app/graph/state.py`** — `ApplicationState` TypedDict complete with all 7 Pydantic models (`CandidateProfile`, `JobProfile`, `CompanyProfile`, `MatchResult`, `ATSReport`, `TailoredResume`, `CoverLetter`); fixed forward-reference ordering and added missing `CompanyProfile`
- **`app/graph/tools/llm.py`** — LLM client initialised (NVIDIA AI Endpoints, `meta/llama-4-scout-17b-16e-instruct`)
- **`app/graph/tools/resume_parser.py`** — stub documented (`parse_pdf`, `parse_docx` via pypdf / python-docx)
- **`app/graph/tools/jd_parser.py`** — stub documented (`fetch_jd` via httpx + BeautifulSoup)
- **`app/graph/tools/embeddings.py`** — stub documented (`get_embeddings`, `compute_similarity` via sentence-transformers)
- **`app/graph/agents/planner.py`** — Planner Agent (supervisor entry node): validates inputs, seeds `approval_status`, clears stale errors; no LLM call
- **`app/graph/router.py`** — all conditional edge functions: `route_after_planner` (parallel fan-out), `route_after_match` (threshold gate), `route_after_review` (approve/reject/re-tailor), `route_after_apply`
- **`app/graph/builder.py`** — full `StateGraph` assembled: 11 nodes registered, parallel parsing fan-out, match gate, `interrupt_before=[HUMAN_REVIEW]`, rejection re-tailor loop, `graph` singleton exported

## In Progress

- Resume Agent (`app/graph/agents/resume_agent.py`)
- Job Agent (`app/graph/agents/job_agent.py`)
- Company Agent (`app/graph/agents/company_agent.py`)

## Next Up

- **Tools (implement stubs)**
  - `resume_parser.py` — `parse_pdf` / `parse_docx`
  - `jd_parser.py` — `fetch_jd`
  - `embeddings.py` — `get_embeddings` / `compute_similarity`
  - `browser.py` / `search.py` — Playwright & web-search helpers
- **Remaining Agents**
  - Match Agent (`app/graph/agents/match_agent.py`)
  - ATS Agent (`app/graph/agents/ats_agent.py`)
  - Tailoring Agent (`app/graph/agents/tailoring_agent.py`)
  - Cover Letter Agent (`app/graph/agents/cover_letter_agent.py`)
  - Human Review Agent (`app/graph/agents/human_review_agent.py`)
  - Apply Agent (`app/graph/agents/apply_agent.py`)
  - Tracking Agent (`app/graph/agents/tracking_agent.py`)
- **FastAPI entrypoint & routes** — `app/main.py`, `app/api/routes/`
- **Database models & migrations** — `app/db/`

## Open Questions

- Dynamic planner vs fixed routing?
- Parallel execution strategy for independent agents (Resume + Job + Company can run concurrently).

## Architecture Decisions

- Supervisor (Planner Agent) controls execution.
- Specialized agents own one responsibility each.
- Human review remains mandatory before Apply Agent.
- Backend scaffolded under `backend/app/` matching Feature 01 spec exactly.
- LLM: NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2, top_p=0.7).

## Session Notes

Refactored design from sequential workflow to multi-agent architecture without changing product goals.
Backend scaffold (empty files only, no code) created from Feature 01 spec; all dependencies installed.
`state.py` fixed: `CompanyProfile` was missing; all Pydantic models reordered before `ApplicationState`; `from __future__ import annotations` added.
`constants.py` fully defined with node names, routing literals, and match threshold.
LLM client wired in `tools/llm.py`; tool stubs documented in `resume_parser.py`, `jd_parser.py`, `embeddings.py`.
