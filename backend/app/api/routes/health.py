"""
api/routes/health.py — Health check endpoint.

Always the first route to implement — it verifies the server is up
and (optionally) that dependencies are reachable.
Used by Docker health checks, load balancers, and smoke tests.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns 200 OK when the server is running."""
    return HealthResponse(status="ok")
