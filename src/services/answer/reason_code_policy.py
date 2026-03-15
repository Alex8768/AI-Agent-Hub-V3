"""Reason-code closure seam for answer runtime diagnostics/warnings."""

from __future__ import annotations


def apply_reason_code_closure(*, resp: object) -> object:
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    warnings = [str(x) for x in list(getattr(resp, "warnings", None) or []) if str(x)]
    warning_set = set(warnings)

    runtime_mode = dict(diagnostics.get("runtime_mode") or {})
    act_runtime = dict(diagnostics.get("act_runtime") or {})
    failure_policy = dict(diagnostics.get("failure_policy") or {})

    for reason in list(runtime_mode.get("reason_codes") or []):
        if str(reason):
            warning_set.add(str(reason))
    for reason in list(act_runtime.get("reason_codes") or []):
        if str(reason):
            warning_set.add(str(reason))

    failure_reason = str(failure_policy.get("reason_code", "") or "")
    if failure_reason:
        warning_set.add(failure_reason)

    setattr(resp, "warnings", sorted(warning_set))
    return resp
