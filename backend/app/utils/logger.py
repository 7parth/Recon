"""
utils/logger.py — Structured JSON logger for automation events.

Usage:
    from app.utils.logger import get_automation_logger

    log = get_automation_logger(thread_id="abc-123")
    log.info("BrowserSession started", context="browser.py")
    log.success("Form submitted", context="greenhouse.py")

Each call emits a LogEntry dict, broadcasts to active SSE listeners,
stores in an in-memory buffer, and asynchronously persists to PostgreSQL.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

LogLevel = Literal["INFO", "DEBUG", "WARN", "ERROR", "SUCCESS"]


class LogEntry:
    """Immutable structured log entry for one automation event."""

    __slots__ = ("id", "thread_id", "ts", "level", "message", "context")

    def __init__(
        self,
        thread_id: str,
        level: LogLevel,
        message: str,
        context: Optional[str] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.thread_id = thread_id
        self.ts = datetime.now(timezone.utc).strftime("%H:%M:%S.") + str(
            datetime.now(timezone.utc).microsecond // 1000
        ).zfill(3)
        self.level = level
        self.message = message
        self.context = context

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "ts": self.ts,
            "level": self.level,
            "message": self.message,
            "context": self.context,
        }

    def to_sse(self) -> str:
        """Format as Server-Sent Event data line."""
        return f"data: {json.dumps(self.to_dict())}\n\n"


# ── In-memory log buffer ──────────────────────────────────────────────────────
_LOG_BUFFER: dict[str, list[dict]] = {}
_LOG_LISTENERS: dict[str, list[asyncio.Queue]] = {}  # SSE subscriber queues


async def _persist_log_to_db(entry: LogEntry) -> None:
    """Async background task to save a log entry to Supabase Postgres."""
    try:
        from app.db.database import get_async_session
        from app.db.repositories.log_repo import AutomationLogRepository

        async with get_async_session() as session:
            repo = AutomationLogRepository(session)
            await repo.create(
                thread_id=entry.thread_id,
                level=entry.level,
                message=entry.message,
                context=entry.context,
                ts=entry.ts,
            )
    except Exception as e:
        logging.getLogger(__name__).debug("Failed to persist log to DB: %s", e)


def _store(entry: LogEntry) -> None:
    """Append entry to the in-memory buffer, broadcast to SSE listeners, and save to DB."""
    buf = _LOG_BUFFER.setdefault(entry.thread_id, [])
    buf.append(entry.to_dict())

    # Broadcast to any active SSE listeners for this thread
    for q in _LOG_LISTENERS.get(entry.thread_id, []):
        try:
            q.put_nowait(entry.to_dict())
        except asyncio.QueueFull:
            pass  # drop if consumer is too slow

    # Asynchronously persist to DB if event loop is running
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            loop.create_task(_persist_log_to_db(entry))
    except RuntimeError:
        pass  # No running event loop (e.g. CLI or sync test)


def get_logs(thread_id: str) -> list[dict]:
    """Return all buffered log entries for a thread (synchronous memory lookup)."""
    return _LOG_BUFFER.get(thread_id, [])


async def get_logs_async(thread_id: str) -> list[dict]:
    """Return all log entries for a thread.

    If present in memory buffer, returns memory buffer.
    Otherwise, loads historical logs from Postgres DB into memory buffer.
    """
    if thread_id in _LOG_BUFFER and len(_LOG_BUFFER[thread_id]) > 0:
        return _LOG_BUFFER[thread_id]

    # Cold load from DB
    try:
        from app.db.database import get_async_session
        from app.db.repositories.log_repo import AutomationLogRepository

        async with get_async_session() as session:
            repo = AutomationLogRepository(session)
            records = await repo.get_by_thread_id(thread_id)
            entries = [
                {
                    "id": str(r.id),
                    "thread_id": r.thread_id,
                    "ts": r.ts or r.created_at.strftime("%H:%M:%S.000"),
                    "level": r.level,
                    "message": r.message,
                    "context": r.context,
                }
                for r in records
            ]
            if entries:
                _LOG_BUFFER[thread_id] = entries
            return entries
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to fetch logs from DB: %s", e)
        return _LOG_BUFFER.get(thread_id, [])


def subscribe(thread_id: str) -> asyncio.Queue:
    """Register an SSE listener queue. Returns the queue; caller must call unsubscribe."""
    q: asyncio.Queue = asyncio.Queue(maxsize=500)
    _LOG_LISTENERS.setdefault(thread_id, []).append(q)
    return q


def unsubscribe(thread_id: str, q: asyncio.Queue) -> None:
    """Remove an SSE listener queue when the client disconnects."""
    listeners = _LOG_LISTENERS.get(thread_id, [])
    if q in listeners:
        listeners.remove(q)
    if not listeners:
        _LOG_LISTENERS.pop(thread_id, None)


# ── AutomationLogger ──────────────────────────────────────────────────────────

class AutomationLogger:
    """
    Thin wrapper that emits structured log entries to:
      1. Standard Python ``logging`` module.
      2. In-memory buffer + SSE.
      3. Supabase Postgres database.
    """

    _PY_LEVEL = {
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "SUCCESS": logging.INFO,
    }

    def __init__(self, thread_id: str) -> None:
        self.thread_id = thread_id
        self._py = logging.getLogger(f"automation.{thread_id[:8]}")

    def _emit(self, level: LogLevel, message: str, context: Optional[str]) -> None:
        entry = LogEntry(self.thread_id, level, message, context)
        _store(entry)
        self._py.log(self._PY_LEVEL[level], "[%s] %s | %s", context or "—", message, level)

    def info(self, message: str, *, context: Optional[str] = None) -> None:
        self._emit("INFO", message, context)

    def debug(self, message: str, *, context: Optional[str] = None) -> None:
        self._emit("DEBUG", message, context)

    def warn(self, message: str, *, context: Optional[str] = None) -> None:
        self._emit("WARN", message, context)

    def error(self, message: str, *, context: Optional[str] = None) -> None:
        self._emit("ERROR", message, context)

    def success(self, message: str, *, context: Optional[str] = None) -> None:
        self._emit("SUCCESS", message, context)


def get_automation_logger(thread_id: str) -> AutomationLogger:
    """Factory — returns an AutomationLogger bound to a specific run thread."""
    return AutomationLogger(thread_id)
