from __future__ import annotations


def build_planner_runtime_parity_fallback_bundle(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    planner_path_used = bool(diag.get("planner_path_used", False))
    action = str(diag.get("agent_current_action", "") or "").strip()
    step_idx = int(diag.get("agent_current_step", 0) or 0)
    trace = dict(diag.get("reasoning_trace") or {})
    plan_rows = list(trace.get("plan") or [])
    step_count = int(len(plan_rows))
    max_step_index = max(step_count - 1, 0)
    reason_codes: list[str] = ["planner_runtime_parity_evaluated"]
    status = "pass"
    if action:
        reason_codes.append("planner_runtime_action_present")
    else:
        status = "warn"
        reason_codes.append("planner_runtime_action_missing")
    if step_idx < 0 or (step_count > 0 and step_idx > max_step_index):
        status = "warn"
        reason_codes.append("planner_runtime_step_out_of_bounds")
    else:
        reason_codes.append("planner_runtime_step_in_bounds")
    reason_codes.append(
        "planner_runtime_graph_path" if planner_path_used else "planner_runtime_fallback_path"
    )
    return {
        "contract_version": "v1",
        "mode": "planner_runtime_parity_guarded",
        "status": status,
        "inputs": {
            "planner_path_used": planner_path_used,
            "planner_step_count": step_count,
            "observed_action": action,
            "observed_step": step_idx,
        },
        "thresholds": {
            "action_required": True,
            "step_index_min": 0,
            "step_index_max": int(max_step_index),
        },
        "reason_codes": sorted(set(reason_codes)),
    }


def build_conversational_runtime_parity_bundle(
    *,
    diagnostics: dict[str, object],
    query: str,
    answer: str,
    normalize_language_tag_fn: object,
    answer_language_fn: object,
    is_unknown_style_answer_fn: object,
) -> dict[str, object]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.response.conversational_runtime_parity"),
        "build_conversational_runtime_parity_bundle",
    )
    return impl(
        diagnostics=diagnostics,
        query=query,
        answer=answer,
        normalize_language_tag_fn=normalize_language_tag_fn,
        answer_language_fn=answer_language_fn,
        is_unknown_style_answer_fn=is_unknown_style_answer_fn,
    )


def build_truthfulness_guard_bundle(
    *,
    query: str,
    answer: str,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.diagnostics.truthfulness_guard"),
        "build_truthfulness_guard_bundle",
    )
    return impl(query=query, answer=answer, diagnostics=diagnostics)


def calibrate_confidence_with_truthfulness_guard(
    *,
    confidence: float | int | None,
    truthfulness_guard_bundle: dict[str, object] | None,
) -> tuple[float, dict[str, object]]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.diagnostics.truthfulness_guard"),
        "calibrate_confidence_with_truthfulness_guard",
    )
    return impl(confidence=confidence, truthfulness_guard_bundle=truthfulness_guard_bundle)
