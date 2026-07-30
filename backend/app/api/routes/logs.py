"""
api/routes/logs.py — Automation log streaming endpoints.

Endpoints:
  GET /runs/{thread_id}/logs          — fetch buffered logs as JSON array
  GET /runs/{thread_id}/logs/stream   — SSE stream for live log tailing

How SSE streaming works:
  1. Frontend opens an EventSource to /runs/{thread_id}/logs/stream.
  2. Server sends all buffered historical logs immediately (replay).
  3. Server then blocks, waiting for new log entries emitted by the
     automation layer (via utils.logger.subscribe()).
  4. Each new LogEntry is sent as a "data: <json>\n\n" SSE event.
  5. When the client disconnects (or the run completes), the endpoint
     unsubscribes and closes.

Log persistence:
  Logs are held in an in-memory buffer (utils.logger._LOG_BUFFER) for the
  lifetime of the server process. On restart, historical logs are lost unless
  we add DB persistence (Phase 15 enhancement — out of scope here).
"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.utils.logger import get_logs_async, subscribe, unsubscribe

logger = logging.getLogger(__name__)
router = APIRouter(tags=["logs"])

_HEARTBEAT_INTERVAL = 15  # seconds — keeps the connection alive through proxies


# ── JSON snapshot ─────────────────────────────────────────────────────────────

@router.get("/runs/{thread_id}/logs")
async def get_run_logs(thread_id: str):
    """
    Return all buffered log entries for a run as a JSON array.

    Useful for initial page load or when SSE is not available.
    Returns an empty list if no logs have been emitted yet.
    """
    entries = await get_logs_async(thread_id)
    return {"thread_id": thread_id, "entries": entries, "count": len(entries)}


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/runs/{thread_id}/logs/stream")
async def stream_run_logs(thread_id: str, request: Request):
    """
    Server-Sent Events stream for live automation log tailing.

    Connect with EventSource:
        const es = new EventSource('/api/v1/runs/<thread_id>/logs/stream');
        es.onmessage = (e) => { const entry = JSON.parse(e.data); ... };

    The stream:
      - Immediately replays all buffered historical log entries (type: "history").
      - Then streams new entries as they are emitted (type: "log").
      - Sends a heartbeat comment every 15 s to prevent proxy timeouts.
      - Sends a {"type": "done"} event when the run is finished (no more logs expected).
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        q = subscribe(thread_id)
        try:
            # 1. Replay buffered history (memory or DB)
            historical = await get_logs_async(thread_id)
            for entry in historical:
                payload = json.dumps({"type": "history", **entry})
                yield f"data: {payload}\n\n"

            # 2. Stream new live entries
            while True:
                if await request.is_disconnected():
                    break

                try:
                    entry = await asyncio.wait_for(q.get(), timeout=_HEARTBEAT_INTERVAL)
                    payload = json.dumps({"type": "log", **entry})
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    # Send a heartbeat comment to keep the connection alive
                    yield ": heartbeat\n\n"

        finally:
            unsubscribe(thread_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
