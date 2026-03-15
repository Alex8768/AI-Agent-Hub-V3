from __future__ import annotations

from src.services.answer.reason_code_policy import apply_reason_code_closure


class _Resp:
    def __init__(self) -> None:
        self.warnings = ["baseline_warning"]
        self.diagnostics = {
            "runtime_mode": {"reason_codes": ["runtime_mode_act_disabled_fallback_answer"]},
            "act_runtime": {"reason_codes": ["act_read_only_tool_not_allowlisted"]},
            "failure_policy": {"reason_code": "answer_runtime_controlled_fallback"},
        }


def test_reason_code_policy_merges_runtime_reason_codes_into_warnings() -> None:
    resp = apply_reason_code_closure(resp=_Resp())
    warnings = set(getattr(resp, "warnings", []) or [])
    assert "baseline_warning" in warnings
    assert "runtime_mode_act_disabled_fallback_answer" in warnings
    assert "act_read_only_tool_not_allowlisted" in warnings
    assert "answer_runtime_controlled_fallback" in warnings
