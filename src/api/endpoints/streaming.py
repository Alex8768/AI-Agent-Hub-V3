"""
Streaming endpoints (SSE proper format, bytes output).
If internal publisher is unavailable, falls back to keepalive-only stream.

Test mode: add ?once=1 to return initial event(s) and close stream (useful for TestClient/CI).
"""

from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, HTTPException, Request, status, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.config import settings

router = APIRouter(tags=["Streaming"])


def _format_sse(event: str, data: dict | None = None) -> bytes:
    payload = ""
    if event:
        payload += f"event: {event}\n"
    if data is not None:
        payload += f"data: {json.dumps(data, ensure_ascii=False)}\n"
    payload += "\n"
    return payload.encode("utf-8")


@router.get("/api/v1/stream/{session_id}")
async def stream_events(
    session_id: str,
    request: Request,
    once: int = Query(default=0, ge=0, le=1),
):
    if not settings.streaming_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is disabled",
        )

    SSEPublisher = None
    try:
        from src.layers.base.streaming.publishers.sse_publisher import SSEPublisher as _SSEPublisher  # type: ignore
        SSEPublisher = _SSEPublisher
    except Exception as e:
        logger.warning(f"Streaming publisher unavailable, using keepalive-only stream: {e}")

    async def fallback_generator():
        # immediate flush (comment line)
        yield b": ping\n\n"

        yield _format_sse(
            event="connected",
            data={"session_id": session_id, "message": "Connected (keepalive-only)"},
        )

        if once:
            return

        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(1.0)
            yield _format_sse(event="keepalive", data=None)

    async def publisher_generator():
        publisher = SSEPublisher()
        queue = await publisher.subscribe(session_id)

        try:
            yield _format_sse(
                event="connected",
                data={"session_id": session_id, "message": "Connected to event stream"},
            )

            if once:
                return

            while True:
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)

                    if isinstance(event, dict):
                        yield _format_sse(
                            event=event.get("event", "message"),
                            data=event.get("data"),
                        )
                    else:
                        yield _format_sse(event="message", data={"value": str(event)})

                except asyncio.TimeoutError:
                    yield _format_sse(event="keepalive", data=None)

        finally:
            await publisher.unsubscribe(session_id, queue)

    try:
        generator = publisher_generator() if SSEPublisher else fallback_generator()
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Streaming backend unavailable: {str(e)}",
        )
