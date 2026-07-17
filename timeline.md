Phase 0 — Project setup

Init repo, Python project structure matching code-standards.md (graph/, api/, automation/, db/, worker/, tests/)
Docker Compose skeleton: app, postgres, redis (no logic yet — just services booting and reachable)
Set up pydantic/pydantic-settings for config, .env.example (real .env stays out of git per protected files)
Create progress-tracker.md with the phases below as open units, so every step from here has somewhere to log status and open questions

Phase 1 — Data foundation

Define Postgres schema: resumes, job_listings, applications tables (SQLAlchemy models + Alembic migration)
Wire up LangGraph's Postgres checkpointer against the same DB — verify a trivial single-node graph can checkpoint and resume
Verify end to end: app boots, migrations run, a dummy row round-trips through the DB

Phase 2 — Resume & JD parsing (core LLM reasoning)

resume_parser_node: resume text/file in → structured resume_profile out (pydantic model, not a dict)
jd_parser_node: JD text in → structured jd_parsed (requirements, ATS keywords) out
Write eval cases for both, reusing scoring patterns from ragEval — a handful of hand-labeled resumes/JDs with expected fields
Verify: parsing nodes tested in isolation, no graph wiring yet

Phase 3 — Matching

match_scorer_node: embeddings (pgvector or Chroma — decide and close the open question in progress-tracker.md) + LLM judgment → match_score
Router function: threshold check → skip_node vs tailor_node
Verify: known good-fit and bad-fit pairs score correctly against your eval set

Phase 4 — Tailoring

tailor_node: generates tailored resume + cover letter from resume_profile + jd_parsed
Add feedback handling so a rejected review loop re-runs tailoring with the user's notes incorporated
Verify: tailored output hits ATS keyword coverage targets from project-overview.md's success criteria

Phase 5 — Human review loop

human_review_node as a LangGraph interrupt() — confirm the graph actually pauses and the checkpoint persists across a process restart
Minimal FastAPI routes: list pending reviews, approve, reject-with-feedback
Verify end to end: run a listing through parsing → tailoring → interrupt → approve via API → graph resumes correctly. This is the first fully wired slice of the graph — treat it as a milestone.

Phase 6 — First ATS automation target (Greenhouse)

automation/greenhouse.py: Playwright script for one real Greenhouse-hosted form — fill + upload + submit
apply_node: dispatches to the platform module by job_listing.platform, only reachable from an approved state
tracker_node: writes final status to applications
Verify: one full run, real listing, real approval, real submission, confirmed in Postgres

Phase 7 — Second ATS target (Lever) + job search

automation/lever.py — repeat the pattern from Greenhouse
job_search_node: pulls candidate listings from configured sources instead of manual JD input
Verify: both platforms pass the >90% success-rate bar from project-overview.md on a small test batch

Phase 8 — API surface + history

FastAPI routes for triggering runs and viewing application history
Verify: full user flow from project-overview.md (upload resume → set criteria → review → approve → track) works through the API alone, no manual DB inspection needed

Phase 9 — Async + caching

Introduce Redis: JD dedupe cache, Celery/arq worker for background run execution (close that other open question)
Move long-running graph execution off the request thread into the worker
Verify: triggering a run returns immediately, status updates show up via polling/the history route

Phase 10 — Hardening & deploy

Error handling / retry policy for flaky Playwright submissions (failed status path)
Docker Compose full stack test locally
AWS deploy: RDS, ElastiCache, ECS/Fargate
Final pass against project-overview.md's success criteria as an acceptance checklist