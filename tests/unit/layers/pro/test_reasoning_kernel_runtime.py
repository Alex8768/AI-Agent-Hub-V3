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


def test_normalize_reasoning_query_input_supports_request_and_string():
    from src.layers.pro.reasoning.contracts import AnswerRequest
    from src.layers.pro.reasoning.kernel import normalize_reasoning_query_input

    assert normalize_reasoning_query_input("  q  ") == "q"
    assert normalize_reasoning_query_input(AnswerRequest(query="  q  ")) == "q"


def test_build_reasoning_response_style_runtime_exposes_callables():
    from src.layers.pro.reasoning.kernel import build_reasoning_response_style_runtime

    out = build_reasoning_response_style_runtime()
    assert set(out.keys()) == {
        "build_fallback_answer",
        "build_chat_recovery_answer",
        "is_simple_greeting_query",
        "is_unknown_style_answer",
        "is_generic_assistant_fallback_answer",
        "normalize_low_evidence_friendliness",
    }
    assert callable(out["build_fallback_answer"])
    assert callable(out["build_chat_recovery_answer"])
    assert callable(out["is_simple_greeting_query"])
    assert callable(out["is_unknown_style_answer"])
    assert callable(out["is_generic_assistant_fallback_answer"])
    assert callable(out["normalize_low_evidence_friendliness"])
