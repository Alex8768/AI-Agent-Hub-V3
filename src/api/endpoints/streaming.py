"""
Streaming endpoints (SSE).
NOTE: Kept 1:1 with existing behavior (yields dict events) to avoid behavior change.
"""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.config import settings

router = APIRouter(tags=["Streaming"])


@router.get("/api/v1/stream/{session_id}")
async def stream_events(session_id: str, request: Request):
    """Stream agent events via Server-Sent Events."""
    if not settings.streaming_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is disabled"
        )

    try:
        from src.layers.base.streaming.publishers.sse_publisher import SSEPublisher

        publisher = SSEPublisher()

        async def event_generator():
            queue = await publisher.subscribe(session_id)

            try:
                # Send initial event
                yield {
                    "event": "connected",
                    "data": {
                        "session_id": session_id,
                        "message": "Connected to event stream"
                    }
                }

                # Stream events
                while True:
                    if await request.is_disconnected():
                        break

                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield event
                    except asyncio.TimeoutError:
                        # Send keep-alive
                        yield ": keep-alive\n\n"

            except asyncio.CancelledError:
                pass
            finally:
                await publisher.unsubscribe(session_id, queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream connection failed: {str(e)}"
        )
