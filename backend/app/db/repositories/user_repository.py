"""UserRepository — DB queries for UserProfileRecord and UserSettingsRecord.

Async CRUD operations for profile & preferences persistence in Supabase PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import UserProfileRecord, UserSettingsRecord
from app.api.schemas.user import UserProfileUpdate, UserSettingsUpdate


class UserRepository:
    """Async repository for user profile and user settings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Profile ──────────────────────────────────────────────────────────────

    async def get_profile(self, user_id: str = "default_user") -> UserProfileRecord:
        """Fetch or create default UserProfileRecord."""
        stmt = select(UserProfileRecord).where(UserProfileRecord.user_id == user_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            record = UserProfileRecord(
                user_id=user_id,
                first_name="",
                last_name="",
                email="",
                phone="",
                linkedin_url="",
                portfolio_url="",
            )
            self._session.add(record)
            await self._session.flush()
        return record

    async def update_profile(
        self, data: UserProfileUpdate, user_id: str = "default_user"
    ) -> UserProfileRecord:
        """Upsert/update UserProfileRecord fields."""
        profile = await self.get_profile(user_id=user_id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if value is not None:
                setattr(profile, key, value)

        await self._session.flush()
        return profile

    # ── Settings ─────────────────────────────────────────────────────────────

    async def get_settings(self, user_id: str = "default_user") -> UserSettingsRecord:
        """Fetch or create default UserSettingsRecord."""
        stmt = select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            record = UserSettingsRecord(
                user_id=user_id,
                match_threshold=70,
                nvidia_model="meta/llama-4-maverick-17b-128e-instruct",   # matches config.py default
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                auto_apply=False,
                enable_notifications=True,
            )
            self._session.add(record)
            await self._session.flush()
        return record

    async def update_settings(
        self, data: UserSettingsUpdate, user_id: str = "default_user"
    ) -> UserSettingsRecord:
        """Upsert/update UserSettingsRecord fields."""
        settings = await self.get_settings(user_id=user_id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(settings, key, value)

        await self._session.flush()
        return settings
