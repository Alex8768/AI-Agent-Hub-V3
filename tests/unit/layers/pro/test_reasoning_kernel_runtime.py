from __future__ import annotations


class _FakeRetriever:
    async def retrieve(self, request):
        _ = request
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


def test_build_reasoning_kernel_returns_reasoning_engine():
    from src.layers.pro.reasoning.kernel import build_reasoning_kernel

    out = build_reasoning_kernel(retriever=_FakeRetriever(), llm=None, llm_timeout_s=None)
    assert out is not None
    assert out.__class__.__name__ == "ReasoningEngine"
    assert out.__class__.__module__ == "src.layers.pro.reasoning.engine"


def test_build_reasoning_planner_runtime_exposes_callables():
    from src.layers.pro.reasoning.kernel import build_reasoning_planner_runtime

    out = build_reasoning_planner_runtime()
    assert set(out.keys()) == {"create_plan", "execute_steps", "build_prompt"}
    assert callable(out["create_plan"])
    assert callable(out["execute_steps"])
    assert callable(out["build_prompt"])
