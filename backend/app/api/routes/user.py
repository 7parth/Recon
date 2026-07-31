"""api/routes/user.py — Endpoints for user profile and pipeline settings."""

from fastapi import APIRouter, Depends
from app.api.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.db.database import get_async_session
from app.db.repositories.user_repository import UserRepository

router = APIRouter(prefix="/user", tags=["user"])


# ── Profile Endpoints ─────────────────────────────────────────────────────────

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile():
    """Fetch current user profile from database."""
    async with get_async_session() as session:
        repo = UserRepository(session)
        record = await repo.get_profile(user_id="default_user")
        return UserProfileResponse.model_validate(record)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(body: UserProfileUpdate):
    """Update current user profile in database."""
    async with get_async_session() as session:
        repo = UserRepository(session)
        record = await repo.update_profile(body, user_id="default_user")
        return UserProfileResponse.model_validate(record)


# ── Settings Endpoints ────────────────────────────────────────────────────────

@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings():
    """Fetch user pipeline preferences from database."""
    async with get_async_session() as session:
        repo = UserRepository(session)
        record = await repo.get_settings(user_id="default_user")
        return UserSettingsResponse.model_validate(record)


@router.put("/settings", response_model=UserSettingsResponse)
async def update_user_settings(body: UserSettingsUpdate):
    """Update user pipeline preferences in database."""
    async with get_async_session() as session:
        repo = UserRepository(session)
        record = await repo.update_settings(body, user_id="default_user")
        return UserSettingsResponse.model_validate(record)
