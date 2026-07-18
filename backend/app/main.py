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

from app.api.routes import health, application, review

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

    # ── Startup / shutdown events ─────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup():
        logger.info("Recon API starting up...")
        logger.info("Docs available at http://localhost:8000/docs")

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Recon API shutting down")

    return app


# ── App singleton — used by uvicorn ──────────────────────────────────────────
app = create_app()
