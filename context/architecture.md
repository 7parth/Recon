# Architecture Context

## Stack

| Layer | Technology | Role |
|---|---|---|
| Orchestration | LangGraph | Supervisor graph, agent routing, human-review interrupt |
| LLM | LangChain + Groq | Structured outputs for specialized agents |
| API | FastAPI | Trigger runs, review queue, approvals, history |
| Database | PostgreSQL | System of record + LangGraph checkpoints |
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

## Existing Invariants

1. Human review cannot be bypassed.
2. API never invokes Playwright directly.
3. Redis is never the source of truth.
4. Apply Agent delegates ATS-specific work to automation modules.
