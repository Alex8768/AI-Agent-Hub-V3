from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest


class RuntimeRetrieverAdapter:
    """Compatibility wrapper for extracted retrieval runtime adapter."""

    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        import importlib

        impl_cls = getattr(
            importlib.import_module("src.services.answer.retrieval.adapter"),
            "RetrieverAdapter",
        )
        self._impl = impl_cls(engine=engine, hybrid=hybrid, workspace_id=workspace_id)

    @property
    def last_stats(self) -> dict[str, object]:
        return dict(getattr(self._impl, "last_stats", {}) or {})

    @property
    def last_top_evidence(self) -> list[str]:
        return list(getattr(self._impl, "last_top_evidence", []) or [])

    async def retrieve(self, request: AnswerRequest):
        return await self._impl.retrieve(request=request)
