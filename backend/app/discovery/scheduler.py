"""
discovery/scheduler.py — APScheduler integration for automated daily discovery.

Public interface
----------------
``init_scheduler(app)``
    Called during FastAPI lifespan startup.  Creates an ``AsyncIOScheduler``,
    registers a daily cron job pointing at ``trigger_scheduled_discovery``,
    starts the scheduler, stores it on ``app.state.scheduler``, and returns it
    so the lifespan context manager can call ``scheduler.shutdown()`` on exit.

``trigger_scheduled_discovery(app)``
    Called by APScheduler at the configured UTC hour.  Checks whether the
    default user has ``auto_discover = True``; if not, it is a no-op.  If a
    discovery session is already running, logs a WARNING and skips creating a
    new session.  Otherwise creates a new session record and launches
    ``run_discovery_session`` via ``asyncio.create_task``.

Requirements: 7.1, 7.2, 7.3, 7.4
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.config import get_settings
from app.db.database import get_async_session
from app.db.repositories.discovery_repo import DiscoveryRepository
from app.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

USER_ID = "default_user"


# ── Public API ────────────────────────────────────────────────────────────────


def init_scheduler(app: FastAPI) -> AsyncIOScheduler:
    """Create, configure, and start the APScheduler scheduler.

    Registers a daily cron job that fires at
    ``settings.discovery_schedule_utc_hour`` UTC to trigger automated
    discovery (Requirement 7.1, 7.3).

    The scheduler is stored on ``app.state.scheduler`` so other parts of the
    application can inspect it, and returned so the lifespan context manager
    can shut it down gracefully on exit.

    Parameters
    ----------
    app:
        The running FastAPI application instance.  Injected into the scheduled
        job so ``trigger_scheduled_discovery`` can access ``app.state.graph``.

    Returns
    -------
    AsyncIOScheduler
        The started scheduler instance.
    """
    settings = get_settings()
    utc_hour = settings.discovery_schedule_utc_hour

    scheduler = AsyncIOScheduler()

    # APScheduler 3.x: pass the FastAPI app instance as a positional argument
    # to the job function so trigger_scheduled_discovery can access app.state.
    scheduler.add_job(
        trigger_scheduled_discovery,
        CronTrigger(hour=utc_hour, timezone="UTC"),
        args=[app],
        id="daily_discovery",
        replace_existing=True,
        max_instances=1,  # prevent overlapping runs at the scheduler level
    )

    scheduler.start()

    app.state.scheduler = scheduler

    logger.info(
        "init_scheduler: daily discovery job registered at UTC hour=%d",
        utc_hour,
    )

    return scheduler


# ── Scheduled job ─────────────────────────────────────────────────────────────


async def trigger_scheduled_discovery(app: FastAPI) -> None:
    """APScheduler job: conditionally launch a new discovery session.

    Steps
    -----
    1. Load ``UserSettingsRecord.auto_discover`` for the default user.
       If ``False``, return immediately (R7.1 — opt-in).
    2. Check for a running ``DiscoverySessionRecord`` via
       ``DiscoveryRepository.get_active_session``.  If one exists, log a
       WARNING with the ``user_id`` and ``session_id`` and return (R7.2).
    3. Create a new session record and launch ``run_discovery_session`` as an
       ``asyncio.create_task`` so this function returns promptly (R7.4).

    Parameters
    ----------
    app:
        The running FastAPI application instance, injected by APScheduler.
        Used to access ``app.state.graph``.
    """
    # Local import avoids circular dependency at module load time.
    from app.discovery.orchestrator import run_discovery_session

    # ── Step 1: Check auto_discover flag ──────────────────────────────────
    try:
        async with get_async_session() as session:
            user_repo = UserRepository(session)
            user_settings = await user_repo.get_settings(USER_ID)
            auto_discover: bool = getattr(user_settings, "auto_discover", False)
    except Exception as exc:
        logger.error(
            "trigger_scheduled_discovery: failed to read user settings for "
            "user_id=%s: %s",
            USER_ID,
            exc,
        )
        return

    if not auto_discover:
        logger.debug(
            "trigger_scheduled_discovery: auto_discover=False for user_id=%s, skipping",
            USER_ID,
        )
        return

    # ── Step 2: Check for an already-running session ──────────────────────
    try:
        async with get_async_session() as session:
            discovery_repo = DiscoveryRepository(session)
            active_session = await discovery_repo.get_active_session(USER_ID)
    except Exception as exc:
        logger.error(
            "trigger_scheduled_discovery: failed to query active session for "
            "user_id=%s: %s",
            USER_ID,
            exc,
        )
        return

    if active_session is not None:
        logger.warning(
            "trigger_scheduled_discovery: skipping scheduled run — a session is "
            "already running. user_id=%s session_id=%s",
            USER_ID,
            active_session.id,
        )
        return  # R7.2

    # ── Step 3: Create a new session and launch the orchestrator ──────────
    try:
        async with get_async_session() as session:
            discovery_repo = DiscoveryRepository(session)
            new_session = await discovery_repo.create_session(USER_ID)
            session_id = new_session.id
            await session.commit()
    except Exception as exc:
        logger.error(
            "trigger_scheduled_discovery: failed to create discovery session for "
            "user_id=%s: %s",
            USER_ID,
            exc,
        )
        return

    logger.info(
        "trigger_scheduled_discovery: launching discovery session_id=%s for "
        "user_id=%s",
        session_id,
        USER_ID,
    )

    # Fire-and-forget: run_discovery_session manages its own error handling and
    # writes the terminal session_status to the DB on completion or failure.
    asyncio.create_task(
        run_discovery_session(session_id, app.state.graph),
        name=f"discovery-{session_id}",
    )
