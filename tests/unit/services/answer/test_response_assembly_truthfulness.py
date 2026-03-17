from __future__ import annotations

import pytest

from src.services.answer.response_assembly import run_answer_response_assembly


class _Resp:
    def __init__(self, answer: str, diagnostics: dict[str, object]) -> None:
        self.answer = answer
        self.confidence = 0.95
        self.diagnostics = diagnostics


class _Req:
    def __init__(self, query: str) -> None:
        self.query = query


@pytest.mark.asyncio
async def test_response_assembly_wires_truthfulness_guard_warn_reason() -> None:
    resp = _Resp(answer="This will definitely always work.", diagnostics={"retrieved_provenance_count": 0})
    req = _Req(query="Will it fail?")

    def _build_truthfulness_guard_bundle(*, query: str, answer: str, diagnostics: dict[str, object]) -> dict[str, object]:
        _ = (query, answer, diagnostics)
        return {
            "contract_version": "v1",
            "mode": "deterministic_heuristic",
            "status": "warn",
            "reason_codes": [
                "truthfulness_guard_evaluated",
                "truthfulness_guard_low_evidence_high_certainty_claim",
            ],
        }

    out = await run_answer_response_assembly(
        resp=resp,
        req=req,
        llm=None,
        assistant_mode_enabled=False,
        assistant_response_language="en",
        build_assistant_recovery_policy_contract=lambda: {"contract_version": "v1"},
        apply_assistant_recovery_policy_guards=lambda **kwargs: (False, {"applied_reason_codes": []}),
        build_assistant_chat_recovery_answer=lambda **kwargs: "",
        normalize_low_evidence_friendliness=lambda **kwargs: kwargs.get("answer", ""),
        build_conversational_runtime_parity_bundle=lambda **kwargs: {"reason_codes": []},
        build_truthfulness_guard_bundle=_build_truthfulness_guard_bundle,
        calibrate_confidence_with_truthfulness_guard=lambda **kwargs: (
            0.55,
            {
                "confidence_before": 0.95,
                "confidence_after": 0.55,
                "confidence_cap_applied": True,
                "reason_codes": ["truthfulness_guard_confidence_capped"],
            },
        ),
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert dict(diag.get("truthfulness_guard") or {}).get("status") == "warn"
    assert float(getattr(out, "confidence", 0.0)) == 0.55
    assert "truthfulness_guard_low_evidence_high_certainty_claim" in list(diag.get("planning_reason_codes") or [])
    assert "truthfulness_guard_confidence_capped" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_response_assembly_keeps_planning_reasons_clean_when_guard_ok() -> None:
    resp = _Resp(answer="Likely, based on current evidence.", diagnostics={"retrieved_provenance_count": 2})
    req = _Req(query="summary")

    out = await run_answer_response_assembly(
        resp=resp,
        req=req,
        llm=None,
        assistant_mode_enabled=False,
        assistant_response_language="en",
        build_assistant_recovery_policy_contract=lambda: {"contract_version": "v1"},
        apply_assistant_recovery_policy_guards=lambda **kwargs: (False, {"applied_reason_codes": []}),
        build_assistant_chat_recovery_answer=lambda **kwargs: "",
        normalize_low_evidence_friendliness=lambda **kwargs: kwargs.get("answer", ""),
        build_conversational_runtime_parity_bundle=lambda **kwargs: {"reason_codes": []},
        build_truthfulness_guard_bundle=lambda **kwargs: {
            "contract_version": "v1",
            "mode": "deterministic_heuristic",
            "status": "ok",
            "reason_codes": ["truthfulness_guard_evaluated"],
        },
        calibrate_confidence_with_truthfulness_guard=lambda **kwargs: (
            0.95,
            {
                "confidence_before": 0.95,
                "confidence_after": 0.95,
                "confidence_cap_applied": False,
                "reason_codes": ["truthfulness_guard_confidence_calibrated"],
            },
        ),
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert dict(diag.get("truthfulness_guard") or {}).get("status") == "ok"
    assert float(getattr(out, "confidence", 0.0)) == 0.95
    assert "truthfulness_guard_evaluated" not in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_response_assembly_l1_contract_replaces_unknown_style() -> None:
    """L1: terminal must not be stub/empty/unknown-style; replaced with useful structure."""
    resp = _Resp(
        answer="Я не знаю.",
        diagnostics={"retrieved_provenance_count": 0, "assistant_plan": {"intent": "general_query"}},
    )
    req = _Req(query="Какой план презентации по географии ты предложишь?")

    out = await run_answer_response_assembly(
        resp=resp,
        req=req,
        llm=None,
        assistant_mode_enabled=True,
        assistant_response_language="ru",
        build_assistant_recovery_policy_contract=lambda: {"contract_version": "v1"},
        apply_assistant_recovery_policy_guards=lambda **kwargs: (False, {"applied_reason_codes": []}),
        build_assistant_chat_recovery_answer=lambda **kwargs: kwargs.get("current_answer", ""),
        normalize_low_evidence_friendliness=lambda **kwargs: str(kwargs.get("answer", "") or ""),
        build_conversational_runtime_parity_bundle=lambda **kwargs: {"reason_codes": []},
        build_truthfulness_guard_bundle=lambda **kwargs: {
            "contract_version": "v1",
            "status": "ok",
            "reason_codes": ["truthfulness_guard_evaluated"],
        },
        calibrate_confidence_with_truthfulness_guard=lambda **kwargs: (
            kwargs.get("confidence", 0.0),
            {"reason_codes": []},
        ),
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert diag.get("risk_tier") == "L1"
    assert "Я не знаю" not in str(getattr(out, "answer", ""))
    assert "assistant_terminal_answer_replaced" in list(diag.get("planning_reason_codes") or [])
    assert len(str(getattr(out, "answer", "") or "").strip()) > 50


@pytest.mark.asyncio
async def test_response_assembly_l2_contract_replaces_empty_terminal() -> None:
    """L2: empty/stub terminal replaced with plan/preview + confirm-required message."""
    resp = _Resp(
        answer="",
        diagnostics={"retrieved_provenance_count": 0, "assistant_plan": {"intent": "general_query"}},
    )
    req = _Req(query="Выполни команду ls в корне")

    out = await run_answer_response_assembly(
        resp=resp,
        req=req,
        llm=None,
        assistant_mode_enabled=True,
        assistant_response_language="ru",
        build_assistant_recovery_policy_contract=lambda: {"contract_version": "v1"},
        apply_assistant_recovery_policy_guards=lambda **kwargs: (False, {"applied_reason_codes": []}),
        build_assistant_chat_recovery_answer=lambda **kwargs: "",
        normalize_low_evidence_friendliness=lambda **kwargs: str(kwargs.get("answer", "") or ""),
        build_conversational_runtime_parity_bundle=lambda **kwargs: {"reason_codes": []},
        build_truthfulness_guard_bundle=lambda **kwargs: {
            "contract_version": "v1",
            "status": "ok",
            "reason_codes": ["truthfulness_guard_evaluated"],
        },
        calibrate_confidence_with_truthfulness_guard=lambda **kwargs: (
            kwargs.get("confidence", 0.0),
            {"reason_codes": []},
        ),
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert diag.get("risk_tier") == "L2"
    assert "assistant_l2_terminal_contract_enforced" in list(diag.get("planning_reason_codes") or [])
    answer = str(getattr(out, "answer", "") or "")
    assert "подтвержд" in answer or "план" in answer
    assert "quality_trace:tier_contract_l2_enforced" in list(diag.get("quality_trace") or [])
