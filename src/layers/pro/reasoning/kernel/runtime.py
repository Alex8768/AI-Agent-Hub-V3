from __future__ import annotations


def build_reasoning_kernel(
    *,
    retriever: object,
    llm: object | None = None,
    llm_timeout_s: float | None = None,
):
    """Build minimal reasoning-kernel runtime adapter.

    This seam formalizes kernel ownership: planner/executor/control stay behind
    ReasoningEngine while callers depend on one stable construction boundary.
    """
    from src.layers.pro.reasoning.engine import ReasoningEngine

    if llm_timeout_s is None:
        return ReasoningEngine(retriever=retriever, llm=llm)
    return ReasoningEngine(retriever=retriever, llm=llm, llm_timeout_s=float(llm_timeout_s))
