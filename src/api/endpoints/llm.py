"""
LLM endpoints.
Thin layer over base LLM provider contract.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.config import settings
from src.api.schemas import LLMRequest, LLMResponse

router = APIRouter(tags=["LLM"])


@router.post("/api/v1/llm/generate", response_model=LLMResponse)
async def generate_completion(request: LLMRequest):
    """Generate text completion using LLM."""
    try:
        from src.layers.base.llm.providers import get_llm_provider

        provider = await get_llm_provider(
            provider_type=request.provider or settings.llm_provider
        )

        # Build core Message list (system + user)
        from src.core.types import Message, MessageRole

        messages = []
        if request.system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=request.system_prompt))
        messages.append(Message(role=MessageRole.USER, content=request.prompt))

        # Config overrides
        cfg = {}
        if request.temperature is not None:
            cfg["temperature"] = request.temperature
        if request.max_tokens is not None:
            cfg["max_tokens"] = request.max_tokens
        if request.model:
            cfg["model"] = request.model

        completion = await provider.complete(messages=messages, config=cfg or None)

        return LLMResponse(
            content=completion.content,
            model=completion.model,
            provider=completion.provider,
            tokens_used=completion.tokens_used or 0,
            finish_reason=completion.finish_reason,
            metadata=completion.metadata or {}
        )

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/api/v1/llm/generate-stream")
async def generate_completion_stream(request: LLMRequest):
    """Generate streaming text completion (JSON-SSE)."""
    try:
        import json
        from src.layers.base.llm.providers import get_llm_provider
        from src.core.types import Message, MessageRole

        provider = await get_llm_provider(
            provider_type=request.provider or settings.llm_provider
        )

        async def event_generator():
            # Build core Message list (system + user)
            messages = []
            if request.system_prompt:
                messages.append(Message(role=MessageRole.SYSTEM, content=request.system_prompt))
            messages.append(Message(role=MessageRole.USER, content=request.prompt))

            cfg = {}
            if request.temperature is not None:
                cfg["temperature"] = request.temperature
            if request.max_tokens is not None:
                cfg["max_tokens"] = request.max_tokens
            if request.model:
                cfg["model"] = request.model

            buffer = ""
            min_flush = 40  # characters

            async for chunk in provider.complete_stream(messages=messages, config=cfg or None):
                text = chunk.content or ""
                if not text:
                    continue

                buffer += text

                if len(buffer) >= min_flush or buffer.endswith((".", "!", "?", "\n")):
                    payload = json.dumps({"delta": buffer}, ensure_ascii=False)
                    yield f"event: token\ndata: {payload}\n\n"
                    buffer = ""

            # Final flush
            if buffer:
                payload = json.dumps({"delta": buffer}, ensure_ascii=False)
                yield f"event: token\ndata: {payload}\n\n"

            yield "event: done\ndata: {}\n\n"

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
        logger.error(f"LLM stream generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream generation failed: {str(e)}"
        )
