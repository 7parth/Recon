# Recon

**Autonomous, human-supervised job application pipeline.**

Recon is an AI agent that reads your resume, finds jobs, scores fit, tailors your resume and cover letter, and submits applications — all with a mandatory human review gate before anything is sent.

---

## How It Works

```
User → FastAPI → Planner (Supervisor)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Resume Agent   Job Agent   Company Agent
        │             │             │
        └─────────────┴─────────────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
         Match Agent      ATS Agent
              │               │
              └───────┬───────┘
                      ▼
             Tailoring Agent → Cover Letter Agent
                      │
                      ▼
            ⛔ Human Review (interrupt)
                      │
              Approve / Reject+Feedback
                      │
              ┌───────┴───────┐
              │               │
           Reject         Approve
              │               │
        Tailoring Agent   Apply Agent
         (re-tailor)          │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
               Greenhouse  Lever     Workday
               Ashby  SmartRecruiters  LinkedIn Easy Apply
                              │
                        Tracking Agent → Dashboard
```

Agents run in a **LangGraph** `StateGraph`. The graph pauses at `human_review` via `interrupt_before`, stores the suspended state in **Supabase Postgres** via `AsyncPostgresSaver`, and resumes when the user approves via the review API.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | NVIDIA AI Endpoints (`meta/llama-4-scout-17b-16e-instruct`) |
| Agent Orchestration | LangGraph (`StateGraph` + `interrupt_before`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector Store | pgvector on Supabase Postgres |
| Backend API | FastAPI + Uvicorn |
| Background Workers | Celery + Redis |
| Database | Supabase PostgreSQL (SQLAlchemy async + asyncpg) |
| File Storage | Supabase Storage |
| Browser Automation | Playwright (headless + headed for LinkedIn auth) |
| Frontend | React 19 + TypeScript + Vite |
| Migrations | Alembic |

---

## Supported ATS Platforms

| Platform | Status |
|---|---|
| Greenhouse | ✅ |
| Lever | ✅ |
| Workday | ✅ |
| Ashby | ✅ |
| SmartRecruiters | ✅ |
| LinkedIn Easy Apply | ✅ |

---

## Project Structure

```
Recon/
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI routers + Pydantic schemas
│   │   │   └── routes/        # health, application, review, jobs, history, logs, user, linkedin
│   │   ├── automation/        # Playwright ATS modules (greenhouse, lever, workday, ashby, smartrecruiters, linkedin)
│   │   ├── db/                # SQLAlchemy models + async repositories + Supabase client
│   │   ├── graph/             # LangGraph: state, builder, router, agents (11 nodes), tools
│   │   ├── services/          # checkpoint_service, storage_service
│   │   ├── storage/           # Supabase Storage helpers
│   │   ├── utils/             # AutomationLogger (in-memory SSE + DB persistence)
│   │   ├── vectorstore/       # pgvector upsert/search + indexing helpers
│   │   ├── workers/           # Celery app factory + pipeline/indexing tasks
│   │   └── tests/             # pytest-asyncio unit + integration tests
│   ├── migrations/            # Alembic migration history
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   └── .env.example
└── frontend/
    └── src/
        ├── pages/             # Dashboard, ReviewQueue, Applications, JobSearch, Resumes, etc.
        ├── components/        # Sidebar, shared UI
        ├── hooks/             # useDashboardData, API hooks
        └── lib/               # API client
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Supabase project (free tier works)
- NVIDIA API key ([build.nvidia.com](https://build.nvidia.com))
- Redis (optional — only needed for Celery workers)

### 1. Clone

```bash
git clone https://github.com/7parth/Recon.git
cd Recon
```

### 2. Backend

```bash
cd backend

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY, Supabase credentials, DATABASE_URL

# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`

### 4. Celery Workers (optional)

Celery workers offload the graph pipeline and resume indexing to background queues. Redis is required.

```bash
# Start Redis (or use Docker: docker run -p 6379:6379 redis)

cd backend

# Pipeline worker
uv run celery -A app.workers.celery_app worker -Q pipeline -c 2 --loglevel=info

# Indexing worker
uv run celery -A app.workers.celery_app worker -Q indexing -c 4 --loglevel=info
```

Enable Celery dispatch per-request with `?use_celery=true`:
```
POST /api/v1/runs/start?use_celery=true
```

### 5. Docker Compose

```bash
cd backend
docker compose up
```

Starts the API server + Celery pipeline worker + Celery indexing worker. Redis is included. Requires a populated `.env` file.

### 6. LinkedIn Easy Apply (one-time setup)

```bash
cd backend
uv run python -m app.automation.linkedin_login
```

This opens a headed browser. Log in to LinkedIn. The session is saved to `.linkedin_session.json` (git-ignored) and reused for all subsequent headless automation runs.

You can also re-authenticate from the **Integrations** page in the frontend UI.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/resume/parse` | Parse a resume file |
| `POST` | `/api/v1/runs/start` | Start an application pipeline run |
| `GET` | `/api/v1/runs/{id}/status` | Poll run status |
| `GET` | `/api/v1/runs/{id}/review` | Fetch the human review payload |
| `POST` | `/api/v1/runs/{id}/approve` | Approve or reject with feedback |
| `GET` | `/api/v1/runs/{id}/logs` | Snapshot automation logs |
| `GET` | `/api/v1/runs/{id}/logs/stream` | SSE live log stream |
| `GET` | `/api/v1/jobs/search` | Search jobs via DuckDuckGo |
| `GET` | `/api/v1/history` | All application runs |
| `GET` | `/api/v1/history/{thread_id}` | Single run history |
| `GET/PUT` | `/api/v1/user/profile` | Candidate profile |
| `GET/PUT` | `/api/v1/user/settings` | User preferences |
| `GET` | `/api/v1/linkedin/auth/status` | LinkedIn session validity |
| `POST` | `/api/v1/linkedin/auth/init` | Start LinkedIn headed login |

Full interactive docs: `http://localhost:8000/docs`

---

## Environment Variables

```env
# LLM
NVIDIA_API_KEY=
NVIDIA_MODEL=meta/llama-4-scout-17b-16e-instruct

# Supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=resumes
SUPABASE_CHECKPOINT_BUCKET=checkpoints

# Database
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# App
ENVIRONMENT=development
LOG_LEVEL=INFO

# Celery / Redis (optional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# LinkedIn (optional — set by login script automatically)
LINKEDIN_SESSION_PATH=.linkedin_session.json
```

---

## Architecture Notes

- **Human review is mandatory** — `interrupt_before=[HUMAN_REVIEW]` is hardcoded in the graph builder. The apply agent never runs without an explicit approval signal.
- **Two-stage match scoring** — embeddings cosine similarity (floor filter) → LLM detailed analysis, blended 70/30. Respects `match_score_threshold` from user settings.
- **Resilient checkpointing** — `AsyncPostgresSaver` persists interrupted graph state to Supabase Postgres. Interrupted runs survive server restarts. Falls back to `MemorySaver` if Postgres is unavailable.
- **Opt-in Celery** — `?use_celery=true` enables queue-based dispatch. Default path uses FastAPI `BackgroundTasks` — no Redis needed for development.
- **LinkedIn session persistence** — session stored in `.linkedin_session.json` (excluded from VCS). Validity checked live before each run via a Playwright page probe.
- **pgvector** — all resume embeddings stored in `resume_embeddings` table (384-dim vectors, IVFFlat cosine index). Indexed automatically after every pipeline run.

---

## Running Tests

```bash
cd backend
uv run pytest app/tests/ -v
```

Test coverage includes:
- End-to-end pipeline (graph execution, interrupt, approval resumption)
- LinkedIn automation (URL detection, dispatcher routing, session auth helpers)
- User profile and settings API
- pgvector embedding store (upsert, search, score clipping)
- Celery task mocking (pipeline task, indexing task, retry logic)

---

## License

MIT
