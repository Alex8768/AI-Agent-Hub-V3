"""Reasoning runtime adapter builder extracted from answer service."""

from __future__ import annotations


def build_reasoning_runtime_adapter(
    *,
    reasoning_factory: object,
    retriever: object,
    llm: object | None,
) -> object | None:
    if not callable(reasoning_factory):
        return None
    adapter = reasoning_factory(retriever=retriever, llm=llm)
    if adapter is None:
        return None
    if not hasattr(adapter, "synthesize"):
        return None
    return adapter
