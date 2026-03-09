from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _FakeRetriever:
    def __init__(self):
        self.calls = []

    async def retrieve(self, request):
        self.calls.append(request)

        return {
            "results": [{"chunk_id": "chunk:1"}, {"chunk_id": "chunk:2"}],
            "graph": {
                "nodes": [{"id": "node:1"}, {"id": "node:2"}],
                "edges": [{"id": "edge:1"}],
            },
            "evidence": [
                {"type": "chunk", "id": "chunk:1", "source_refs": ["doc:A#1"], "confidence": 0.9},
                # malformed evidence should be ignored
                {"bad": "shape"},
            ],
        }


class _EmptyRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [],
        }


@pytest.mark.asyncio
async def test_reasoning_engine_synthesize_stub_orchestration():
    retriever = _FakeRetriever()
    eng = ReasoningEngine(retriever=retriever)

    req = AnswerRequest(query="Hello", k=2, graph_depth=1)
    resp = await eng.synthesize(req)

    # retriever called exactly once with the same request
    assert retriever.calls == [req]

    # deterministic stub
    assert resp.answer == "(reasoning layer stub)"
    assert resp.confidence == 0.9

    # best-effort ids collected
    assert resp.used_chunks == ["chunk:1", "chunk:2"]
    assert resp.used_nodes == ["node:1", "node:2"]
    assert resp.used_edges == ["edge:1"]

    # provenance validated (malformed skipped)
    assert len(resp.provenance) == 1
    p = resp.provenance[0]
    assert p.type == "chunk"
    assert p.id == "chunk:1"
    assert p.source_refs == ["doc:A#1"]
    assert p.confidence == 0.9

    # context preview packed from provenance source_refs (MVP)
    assert resp.context_preview == "doc:A#1"


@pytest.mark.asyncio
async def test_reasoning_engine_uses_session_memory_when_retrieval_context_empty():
    eng = ReasoningEngine(retriever=_EmptyRetriever())
    req = AnswerRequest(query="follow up", session_memory_last_answer="previous answer from session")

    resp = await eng.synthesize(req)

    assert resp.answer == "(reasoning layer stub)"
    assert resp.context_preview == "previous answer from session"


@pytest.mark.asyncio
async def test_reasoning_engine_fallback_executes_planner_steps(monkeypatch):
    calls: dict[str, object] = {}

    def _fake_create_reasoning_plan(*, query: str):
        calls["query"] = query
        return {
            "steps": [
                {"description": "step one"},
                {"description": "step two"},
            ]
        }

    async def _fake_execute_plan_steps(*, plan, run_reasoning_step, run_verify_step, max_steps=None):
        calls["plan_steps"] = int(len(plan.get("steps") or []))
        calls["max_steps"] = max_steps
        _ = run_reasoning_step
        _ = run_verify_step
        return [
            {
                "step_index": 0,
                "step_description": "step one",
                "reasoning_output": "step one",
                "verify_status": "pass",
                "verify_reasons": [],
            },
            {
                "step_index": 1,
                "step_description": "step two",
                "reasoning_output": "step two",
                "verify_status": "pass",
                "verify_reasons": [],
            },
        ]

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.create_reasoning_plan",
        _fake_create_reasoning_plan,
    )
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.execute_plan_steps",
        _fake_execute_plan_steps,
    )

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    resp = await eng.synthesize(AnswerRequest(query="multi step query"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert calls.get("query") == "multi step query"
    assert calls.get("plan_steps") == 2
    assert calls.get("max_steps") == 3
    assert diag.get("agent_current_action") == "ANSWER"
    assert diag.get("agent_current_step") == 1
    bench = dict(diag.get("reasoning_benchmark") or {})
    assert bench.get("suite_name") == "reasoning_runtime_fallback"
    summary = dict(bench.get("summary") or {})
    assert summary.get("total_cases") == 2
    assert summary.get("passed_cases") == 2
    optimization = dict(diag.get("reasoning_optimization") or {})
    assert set(optimization.keys()) == {"signal", "proposals", "decision"}
    assert isinstance(optimization.get("signal"), dict)
    assert isinstance(optimization.get("proposals"), list)
    assert isinstance(optimization.get("decision"), dict)
    trace = dict(diag.get("reasoning_trace") or {})
    assert trace.get("query") == "multi step query"
    assert trace.get("plan") == ["step one", "step two"]
    assert trace.get("steps") == ["step one", "step two"]


@pytest.mark.asyncio
async def test_reasoning_engine_fallback_applies_loop_guard_to_repeated_steps(monkeypatch):
    calls: dict[str, object] = {}

    def _fake_create_reasoning_plan(*, query: str):
        _ = query
        return {
            "steps": [
                {"description": "repeat"},
                {"description": " repeat "},
                {"description": "REPEAT"},
            ]
        }

    async def _fake_execute_plan_steps(*, plan, run_reasoning_step, run_verify_step, max_steps=None):
        _ = run_reasoning_step
        _ = run_verify_step
        calls["plan_steps"] = list(plan.get("steps") or [])
        calls["max_steps"] = max_steps
        return []

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.create_reasoning_plan",
        _fake_create_reasoning_plan,
    )
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.execute_plan_steps",
        _fake_execute_plan_steps,
    )

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    await eng.synthesize(AnswerRequest(query="loop"))

    assert calls.get("max_steps") == 3
    assert calls.get("plan_steps") == [
        {"description": "repeat"},
        {"description": "repeat"},
    ]


@pytest.mark.asyncio
async def test_reasoning_engine_quality_retry_uses_execution_policy_max_retries(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_build_reasoning_execution_policy(*, max_steps=None, max_latency_ms=None, max_retries=None):
        _ = max_steps
        _ = max_latency_ms
        _ = max_retries
        return {"max_steps": 3, "max_latency_ms": 15000, "max_retries": 2}

    def _fake_decide_reasoning_quality_retry(*, confidence_score, attempt, threshold=0.6, max_retries=1):
        _ = confidence_score
        _ = attempt
        _ = threshold
        captured["max_retries"] = max_retries
        return {
            "attempt": 0,
            "max_retries": int(max_retries),
            "confidence_score": 0.0,
            "threshold": 0.6,
            "confidence_below_threshold": True,
            "retry_budget_available": True,
            "should_retry": True,
            "next_attempt": 1,
            "loop_guard_triggered": False,
            "reason": "retry_allowed_low_confidence",
        }

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.build_reasoning_execution_policy",
        _fake_build_reasoning_execution_policy,
    )
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.decide_reasoning_quality_retry",
        _fake_decide_reasoning_quality_retry,
    )

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    resp = await eng.synthesize(AnswerRequest(query="q"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    rq = dict(diag.get("reasoning_quality") or {})
    retry = dict(rq.get("retry") or {})

    assert captured.get("max_retries") == 2
    assert retry.get("max_retries") == 2
    assert diag.get("reasoning_execution_policy") == {
        "max_steps": 3,
        "max_latency_ms": 15000,
        "max_retries": 2,
    }
