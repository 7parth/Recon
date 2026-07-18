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
- **`app/graph/tools/embeddings.py`** — `get_embeddings` (sentence-transformers, lazy singleton via `lru_cache`), `compute_similarity` (pure-Python cosine), `score_resume_jd` helper
- **`app/graph/agents/planner.py`** — Planner Agent (supervisor entry node): validates inputs, seeds `approval_status`, clears stale errors; no LLM call
- **`app/graph/router.py`** — all conditional edge functions: `route_after_planner` (parallel fan-out), `route_after_match` (threshold gate), `route_after_review` (approve/reject/re-tailor), `route_after_apply`
- **`app/graph/builder.py`** — full `StateGraph` assembled: 11 nodes registered, parallel parsing fan-out, match gate, `interrupt_before=[HUMAN_REVIEW]`, rejection re-tailor loop, `graph` singleton exported
- **`app/graph/tools/resume_parser.py`** — `parse_pdf` (pypdf + `io.BytesIO`), `parse_docx` (python-docx), `parse_resume` dispatcher
- **`app/graph/tools/jd_parser.py`** — `fetch_jd` (httpx + BeautifulSoup, semantic landmark selection, noise removal), `normalize_jd` for raw-text input
- **`app/graph/tools/embeddings.py`** *(implemented)* — `get_embeddings`, `compute_similarity`, `score_resume_jd`

- **`app/graph/prompts/resume.py`** — system + user prompt templates for resume extraction
- **`app/graph/agents/resume_agent.py`** — `resume_agent_node`: `with_structured_output(CandidateProfile)`, SystemMessage + HumanMessage pattern
- **`app/graph/prompts/job.py`** — prompt targeting `required_skills`, `responsibilities`, `experience_required`
- **`app/graph/agents/job_agent.py`** — `job_agent_node`: URL-vs-raw-text detection, fetch via `jd_parser`, `with_structured_output(JobProfile)`
- **`app/graph/prompts/company.py`** — prompt targeting `name`, `industry`, `size`, `culture_notes`
- **`app/graph/agents/company_agent.py`** — `company_agent_node`: same JD fetch as job_agent (independent — parallel nodes cannot share state mid-flight)

- **`app/graph/prompts/match.py`** — two-profile prompt (candidate + job as readable text), concrete example instructions for specificity
- **`app/graph/agents/match_agent.py`** — `match_agent_node`: two-stage scoring (embeddings pre-filter → LLM detailed), score blending (70% LLM + 30% embeddings), early-exit on obvious mismatch
- **`app/graph/prompts/ats.py`** — keyword ratio + section score + gap recommendations prompt
- **`app/graph/agents/ats_agent.py`** — `ats_agent_node`: audits *original* resume against `job_profile.required_skills`, bulleted skill list formatting, keyword_match clamping

- **`app/graph/prompts/tailoring.py`** — two variants: first-run (ATS gaps + strengths) and re-tailor (user feedback as top priority)
- **`app/graph/agents/tailoring_agent.py`** — `tailoring_agent_node`: conditional prompt selection on `rejection_feedback`, clears feedback after re-tailor
- **`app/graph/prompts/cover_letter.py`** — two variants with tone-matching rules (startup vs enterprise), 250–350 word constraint
- **`app/graph/agents/cover_letter_agent.py`** — `cover_letter_agent_node`: `llm.bind(temperature=0.7)` for creative prose, graceful fallback on missing `company_profile`

- **`app/graph/agents/human_review_agent.py`** — validation passthrough post-interrupt; no LLM; documents the full 9-step interrupt/resume lifecycle
- **`app/graph/agents/apply_agent.py`** — ATS dispatcher pattern (`_detect_platform` + lazy-imported submit functions), `"skipped"` status for unsupported platforms, non-fatal failure
- **`app/graph/agents/tracking_agent.py`** — terminal node; structured grep-able outcome log, UTC timestamp for DB stamping

## In Progress

- FastAPI entrypoint (`app/main.py`)
- API routes (`app/api/routes/`)

## Next Up

- **Database models & migrations** — `app/db/`
- **Automation stubs** — `app/automation/greenhouse.py`, `lever.py`, `workday.py`, `ashby.py`
- **End-to-end smoke test** — run graph with mock state, verify all nodes fire

## Open Questions

- Dynamic planner vs fixed routing?
- Parallel execution strategy for independent agents (Resume + Job + Company can run concurrently).

## Architecture Decisions

- Supervisor (Planner Agent) controls execution.
- Specialized agents own one responsibility each.
- Human review remains mandatory before Apply Agent.
- Backend scaffolded under `backend/app/` matching Feature 01 spec exactly.
- LLM: NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`, temp=0.2, top_p=0.7).

## Git

- `main` — stable, scaffolded baseline (2 commits)
- `dev`  — active development branch; PR open at github.com/7parth/Recon/pull/new/dev

## Session Notes

Refactored design from sequential workflow to multi-agent architecture without changing product goals.
Backend scaffold (empty files only, no code) created from Feature 01 spec; all dependencies installed.
`state.py` fixed: `CompanyProfile` was missing; all Pydantic models reordered before `ApplicationState`; `from __future__ import annotations` added.
`constants.py` fully defined with node names, routing literals, and match threshold.
LLM client wired in `tools/llm.py`; tool stubs documented in `resume_parser.py`, `jd_parser.py`, `embeddings.py`.
Tool layer fully implemented: `resume_parser`, `jd_parser`, `embeddings`.
Agents implemented: `planner`, `resume_agent`, `job_agent`, `company_agent`, `match_agent`, `ats_agent`.
All work pushed to `dev` branch — commit `00a2cf4`.
