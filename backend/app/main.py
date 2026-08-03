"""
main.py — FastAPI application entrypoint.

Creates the FastAPI app, registers all routers, and configures middleware.

Run locally:
  cd backend
  uvicorn app.main:app --reload --port 8000

API docs auto-generated at:
  http://localhost:8000/docs      (Swagger UI)
  http://localhost:8000/redoc     (ReDoc)
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, application, review, jobs, history, logs, user, linkedin

# ── Logging configuration ─────────────────────────────────────────────────────
# Configure once at startup — all modules use logging.getLogger(__name__)
# which flows up to this root configuration.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Application factory pattern.

    Why a factory function instead of a module-level app object?
      - Easier to test: tests call create_app() with different configs.
      - Avoids circular imports: routers import from app, not from main.
      - Standard FastAPI pattern for production apps.
    """
    # ── Lifespan (Startup / Shutdown) ─────────────────────────────────────────
    from contextlib import asynccontextmanager
    from app.services.checkpoint_service import get_checkpointer
    from app.graph.builder import build_graph

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        logger.info("Recon API starting up...")
        logger.info("Docs available at http://localhost:8000/docs")
        
        # Initialize LangGraph Checkpoint Service (Supabase Postgres)
        # Fall back to MemorySaver if Postgres is unavailable or authentication fails
        try:
            async with get_checkpointer() as checkpointer:
                app_instance.state.checkpointer = checkpointer
                app_instance.state.graph = build_graph(checkpointer=checkpointer)
                yield
        except Exception as e:
            logger.warning(
                f"Failed to initialize Postgres checkpointer ({e}). "
                "Falling back to MemorySaver (in-memory state persistence)."
            )
            from langgraph.checkpoint.memory import MemorySaver

            memory_cp = MemorySaver()
            app_instance.state.checkpointer = memory_cp
            app_instance.state.graph = build_graph(checkpointer=memory_cp)
            yield

        logger.info("Recon API shutting down")

    app = FastAPI(
        title="Recon — Job Application Agent API",
        description=(
            "Autonomous, human-supervised job application pipeline. "
            "Parses resumes, matches jobs, tailors applications, and submits "
            "after mandatory human review."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Allow the frontend (any localhost port during dev) to call the API.
    # In production, replace allow_origins with your actual frontend domain.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register routers ──────────────────────────────────────────────────────
    # Each router is a group of related endpoints.
    # The prefix scopes all routes in that router under a path prefix.
    app.include_router(health.router)                        # GET /health
    app.include_router(application.router, prefix="/api/v1") # POST /api/v1/runs/start, etc.
    app.include_router(review.router,      prefix="/api/v1") # GET  /api/v1/runs/{id}/review, etc.
    app.include_router(jobs.router,        prefix="/api/v1") # GET  /api/v1/jobs/search
    app.include_router(history.router,     prefix="/api/v1") # GET  /api/v1/history
    app.include_router(logs.router,        prefix="/api/v1") # GET  /api/v1/runs/{id}/logs[/stream]
    app.include_router(user.router,        prefix="/api/v1") # GET/PUT /api/v1/user/profile & /settings
    app.include_router(linkedin.router,    prefix="/api/v1") # GET /api/v1/linkedin/auth/status, POST /api/v1/linkedin/auth/init

    return app


# ── App singleton — used by uvicorn ──────────────────────────────────────────
app = create_app()
