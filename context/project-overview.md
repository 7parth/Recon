# Recon - Job Application Agent

## Overview

The Job Application Agent is an autonomous, human-supervised system that finds job listings matching a candidate's profile, tailors a resume and cover letter for each one, and submits the application via browser automation — pausing for human approval before anything is actually sent. It's built for individual job seekers (starting with the builder's own internship/new-grad search) who want to apply to more roles without sacrificing the quality of each application, and it solves the core tension of job hunting at scale: broad reach usually means generic, low-effort applications, while tailored applications don't scale past a handful a day.

## Goals

1. Cut the time to produce a tailored resume + cover letter for a single job listing from ~20-30 minutes of manual editing to under 2 minutes of review time.
2. Reach a 3-5x increase in weekly applications submitted without lowering per-application tailoring quality (measured by ATS keyword coverage and match score).
3. Maintain a 100% human-approval checkpoint before submission — zero applications go out without explicit sign-off.
4. Successfully automate form-fill and submission on at least two major ATS platforms (e.g. Greenhouse, Lever) with a measurable success rate (>90% successful submits on supported platforms).

## Core User Flow

1. User uploads/updates their base resume; the agent parses it into a structured profile (skills, experience, education).
2. User defines search criteria (roles, locations, keywords) or supplies a specific job URL/JD directly.
3. Agent finds and parses matching job listings, scoring each against the resume profile.
4. For listings above the match threshold, the agent drafts a tailored resume and cover letter, optimized for ATS keywords from the JD.
5. Agent pauses and surfaces the tailored documents to the user for review.
6. User approves, edits, or rejects (with feedback, triggering a re-tailor).
7. On approval, the agent fills out the application form via browser automation and submits it.
8. Agent logs the outcome (applied / failed / skipped) and moves to the next listing.
9. User can view application history and status at any point.

## Features

### Resume & Job Matching

- Resume parsing into a structured, reusable candidate profile
- Job description parsing into structured requirements and ATS keywords
- Semantic match scoring (embeddings + LLM judgment) between profile and JD
- Configurable match-score threshold to auto-skip weak-fit listings

### Tailoring

- LLM-generated tailored resume bullets and summary per listing
- LLM-drafted cover letter per listing
- ATS keyword optimization pass on generated documents

### Human-in-the-Loop Review

- Mandatory approval checkpoint before any submission
- Reject-with-feedback loop that re-runs tailoring with the user's notes
- Persisted review queue (survives restarts via LangGraph checkpoints stored in Supabase PostgreSQL)

### Application Automation

- Browser automation (Playwright) for form-fill and submission
- Initial support for standardized ATS platforms (Greenhouse, Lever)
- Resume/cover letter file upload handling per platform

### Tracking & History

- Per-application status tracking (skipped / pending review / applied / failed)
- Searchable history of past applications and the documents used for each
- Basic run triggering and status API (FastAPI)

## Scope

### In Scope

- Single-user, self-hosted operation (not a multi-tenant SaaS)
- Resume/JD parsing, matching, and tailoring via LLM
- Human approval checkpoint before submission
- Browser automation for Greenhouse- and Lever-hosted application forms
- Application history and status tracking in Supabase PostgreSQL + Storage

### Out of Scope

- Automated applying on LinkedIn, Indeed, or other platforms whose ToS restrict bot-driven applications
- Multi-user/account support, billing, or SaaS-style onboarding
- Interview scheduling, follow-up email automation, or offer negotiation
- Fully unsupervised submission (no bypass of the human-review checkpoint)
- Resume design/formatting overhaul — the agent edits content, not visual template

## Success Criteria

1. A user can upload a resume and, from a single job URL, receive a tailored resume + cover letter ready for review in under 2 minutes.
2. The human-review checkpoint correctly blocks submission until explicit approval is recorded, verified across at least 20 test runs with no bypass.
3. The agent successfully completes end-to-end submission (form-filled and confirmed) on both Greenhouse and Lever test listings with a >90% success rate.
4. Application history persisted in Supabase PostgreSQL accurately reflects real-world status (applied/failed/skipped) for 100% of processed listings.
5. Match scoring correctly skips clearly mismatched listings (validated against a hand-labeled test set) with acceptable precision/recall.

## Technical Architecture

### Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph `StateGraph` with checkpoint-based persistence |
| LLM | NVIDIA AI Endpoints — `meta/llama-4-scout-17b-16e-instruct` (temp 0.2 extraction / 0.7 creative) |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2`, local inference, no API cost |
| Resume parsing | `pypdf` (PDF), `python-docx` (DOCX) |
| JD fetching | `httpx` + `BeautifulSoup` — semantic landmark extraction |
| Web search | `duckduckgo-search` — no API key required |
| Browser automation | `playwright` (Chromium, sync API) |
| API | FastAPI (async) |
| Database | Supabase PostgreSQL (hosted) |
| ORM | SQLAlchemy Async |
| Storage | Supabase Storage (resumes, tailored resumes, cover letters) |
| Package manager | `uv` |

### Agent Pipeline

```
START
  │
  ▼
planner ──(error)──────────────────────────────────────────────► END
  │
  ├──► resume_agent ──┐   (parallel fan-out — run concurrently)
  ├──► job_agent ─────┤
  └──► company_agent ─┘
                      │  (fan-in)
                      ▼
                 match_agent  ── (score < 0.65) ──────────────► END
                      │
                 ats_agent
                      │
              tailoring_agent ◄──────────── (rejected, re-tailor loop)
                      │                              ▲
              cover_letter_agent                     │
                      │                              │
                human_review ── (rejected + feedback)┘
                [INTERRUPT]
                      │
                  (approved)
                      │
                apply_agent
                      │
               tracking_agent
                      │
                     END
```

### State (`ApplicationState` TypedDict)

All agents share a single typed state object. Each agent reads specific fields and returns a partial dict that LangGraph merges in:

| Field | Type | Written by |
|---|---|---|
| `resume_raw` | `str` | API (upload) |
| `job_url` | `str` | API (input) |
| `resume_profile` | `CandidateProfile` | `resume_agent` |
| `job_profile` | `JobProfile` | `job_agent` |
| `company_profile` | `CompanyProfile` | `company_agent` |
| `match_result` | `MatchResult` | `match_agent` |
| `ats_report` | `ATSReport` | `ats_agent` |
| `tailored_resume` | `TailoredResume` | `tailoring_agent` |
| `cover_letter` | `CoverLetter` | `cover_letter_agent` |
| `approval_status` | `"approved" \| "rejected" \| "pending"` | API (resume) |
| `rejection_feedback` | `str` | API (on reject) |
| `submission_status` | `"applied" \| "failed" \| "skipped"` | `apply_agent` |
| `error` | `str` | any agent (non-fatal) |

### Key Design Decisions

- **Fixed routing, not dynamic planner**: The graph topology is statically compiled. The planner node validates inputs; routing logic lives in `router.py` as pure functions. Simpler to debug and test than a dynamic LLM-driven supervisor.
- **Two-stage match scoring**: Embeddings cosine similarity as a cheap pre-filter (early exit below 0.325), then LLM detailed scoring for borderline/good matches. Final score = 70% LLM + 30% embeddings.
- **`interrupt_before=[HUMAN_REVIEW]`**: LangGraph pauses the graph before `human_review_agent` runs on every pass. The FastAPI layer surfaces the draft documents, waits for the user decision, then resumes the graph via `graph.invoke()` with the checkpoint's `thread_id`.
- **Conditional prompt selection in tailoring/cover letter**: The same node handles both first-run and re-tailor (after rejection) by branching on `state["rejection_feedback"]`. No extra graph nodes needed.
- **ATS dispatcher**: `apply_agent` detects the ATS platform from the URL and delegates to a per-platform automation module. Adding a new ATS = implement one `submit()` function, add one dict entry.

### Repository Layout

```
backend/
  app/
    graph/
      agents/       — 11 agent nodes (planner → tracking)
      prompts/      — prompt templates (separated from agent logic)
      tools/        — resume_parser, jd_parser, embeddings, llm, browser, search
      state.py      — ApplicationState TypedDict + 7 Pydantic models
      constants.py  — node name constants, routing literals
      builder.py    — StateGraph construction + graph singleton
      router.py     — conditional edge functions
    automation/     — per-ATS Playwright submit() functions
    api/            — FastAPI routes and schemas
    db/             — SQLAlchemy models, Supabase client, repositories
    storage/        — Supabase Storage wrappers (resume, document upload)
    services/       — business logic layer
    workers/        — Celery background tasks (future)
    vectorstore/    — FAISS embedding index (future)
```

