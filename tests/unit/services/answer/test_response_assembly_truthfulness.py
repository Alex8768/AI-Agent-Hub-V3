from __future__ import annotations

import pytest

from src.services.answer.response_assembly import run_answer_response_assembly


class _Resp:
    def __init__(self, answer: str, diagnostics: dict[str, object]) -> None:
        self.answer = answer
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
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert dict(diag.get("truthfulness_guard") or {}).get("status") == "warn"
    assert "truthfulness_guard_low_evidence_high_certainty_claim" in list(diag.get("planning_reason_codes") or [])


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
    )
    diag = dict(getattr(out, "diagnostics", None) or {})
    assert dict(diag.get("truthfulness_guard") or {}).get("status") == "ok"
    assert "truthfulness_guard_evaluated" not in list(diag.get("planning_reason_codes") or [])
