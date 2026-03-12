from __future__ import annotations

from typing import Any


class LLMGenerateAdapter:
    """Adapt Base LLM provider (complete/messages) to ReasoningEngine contract (generate(prompt)->str)."""

    def __init__(self, provider: object, *, provider_name: str = "", model: str = ""):
        self._p = provider
        self.provider_name = provider_name
        self.model = model

    async def generate(self, prompt: str) -> str:
        from src.core.types import Message, MessageRole

        messages = [Message(role=MessageRole.USER, content=str(prompt or ""))]
        cfg: dict[str, Any] = {}
        if self.model:
            cfg["model"] = self.model

        if hasattr(self._p, "complete"):
            c = await self._p.complete(messages=messages, config=(cfg or None))
            text = getattr(c, "content", None)
            return str(text if text is not None else c)

        raise RuntimeError("LLM provider does not implement complete()")
