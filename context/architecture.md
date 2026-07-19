# Architecture Context

## Stack

| Layer | Technology | Role |
|---|---|---|
| Orchestration | LangGraph | Supervisor graph, agent routing, human-review interrupt |
| LLM | LangChain + NVIDIA AI Endpoints | Structured outputs for specialized agents |
| API | FastAPI | Trigger runs, review queue, approvals, history |
| Database | Supabase PostgreSQL | System of record + LangGraph checkpoints (hosted, managed) |
| ORM | SQLAlchemy Async | Async session management, declarative models |
| Storage | Supabase Storage | Resume, tailored resume, cover letter — documents stored as files, URLs in DB |
| Auth | Supabase Auth | Future — single-user scope currently |
| Realtime | Supabase Realtime | Future — live status updates |
| Cache/Queue | Redis + Celery | Queue and cache |
| Automation | Playwright | ATS automation |
| Vector Store | FAISS | Semantic matching |

## Multi-Agent Architecture

Planner Agent (Supervisor)

- Resume Agent
- Job Agent
- Company Agent
- Match Agent
- ATS Agent
- Resume Tailoring Agent
- Cover Letter Agent
- Human Review Agent
- Apply Agent
- Tracking Agent

Resume Agent, Job Agent and Company Agent may execute in parallel.

## Agent Responsibilities

- Planner: orchestration, routing, retries, parallel execution.
- Resume Agent: parse resume into CandidateProfile.
- Job Agent: parse JD into JobProfile.
- Company Agent: collect company context.
- Match Agent: compute semantic/job fit score.
- ATS Agent: ATS keyword analysis and optimization report.
- Resume Tailoring Agent: generate tailored resume.
- Cover Letter Agent: generate cover letter.
- Human Review Agent: mandatory approval checkpoint.
- Apply Agent: dispatches to Playwright integrations only after approval.
- Tracking Agent: persists application lifecycle.

## Shared State

ApplicationState contains:
- resume_profile
- job_profile
- company_profile
- match_result
- ats_report
- tailored_resume
- cover_letter
- approval_status
- submission_status

## Storage Model

Documents are never stored as text blobs in the database.

```
Supabase Storage Buckets
├── resumes/            — original resume uploads
│   └── {run_id}/resume.pdf
├── tailored-resumes/   — LLM-generated tailored resume per run
│   └── {run_id}/tailored_resume.pdf
└── cover-letters/      — LLM-generated cover letter per run
    └── {run_id}/cover_letter.pdf

Supabase PostgreSQL (via SQLAlchemy)
└── application_records
    ├── resume_storage_url      TEXT  — public URL from Supabase Storage
    ├── tailored_resume_url     TEXT  — public URL from Supabase Storage
    └── cover_letter_url        TEXT  — public URL from Supabase Storage
```

This makes documents accessible from any machine, separates storage concerns from relational concerns, and keeps the DB rows small.

## Persistence Architecture

### LangGraph Checkpoints

LangGraph's `AsyncPostgresSaver` is configured to use the Supabase PostgreSQL connection string. This means:
- Interrupted runs survive server restarts
- The review queue (pending human approval) is durable across deployments
- No separate local Postgres is required

### Session/File Storage

Files are stored in Supabase Storage, not on the local filesystem. `StorageService` uploads and returns a public URL. Graph agents never interact with storage directly — they receive URLs as part of state.

## Existing Invariants

1. Human review cannot be bypassed.
2. API never invokes Playwright directly.
3. Redis is never the source of truth.
4. Apply Agent delegates ATS-specific work to automation modules.
5. **Graph nodes never access Supabase directly** — all DB and storage operations go through `repositories/` and `services/`.
6. Agents remain pure functions of `ApplicationState` — no Supabase client calls inside graph nodes.
