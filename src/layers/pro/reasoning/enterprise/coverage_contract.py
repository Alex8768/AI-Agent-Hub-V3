from __future__ import annotations


def normalize_optional_coverage_ratio(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        return None
    if parsed > 1.0:
        parsed = parsed / 100.0
    if parsed < 0.0:
        return 0.0
    if parsed > 1.0:
        return 1.0
    return float(parsed)


def resolve_coverage_ratio_from_diagnostics(diagnostics: dict[str, object] | None) -> float | None:
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    coverage = dict(diag.get("coverage") or {})
    raw = coverage.get(
        "line_rate",
        coverage.get("coverage_ratio", coverage.get("line_coverage_ratio", coverage.get("coverage_percent"))),
    )
    return normalize_optional_coverage_ratio(raw)
