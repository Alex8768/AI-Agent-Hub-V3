from __future__ import annotations

from src.layers.pro.reasoning.enterprise.coverage_contract import (
    normalize_optional_coverage_ratio,
    resolve_coverage_ratio_from_diagnostics,
)


def test_normalize_optional_coverage_ratio_handles_ratio_and_percent_inputs():
    assert normalize_optional_coverage_ratio(0.85) == 0.85
    assert normalize_optional_coverage_ratio(85) == 0.85
    assert normalize_optional_coverage_ratio("92") == 0.92
    assert normalize_optional_coverage_ratio(-1) == 0.0
    assert normalize_optional_coverage_ratio(150) == 1.0
    assert normalize_optional_coverage_ratio("bad") is None
    assert normalize_optional_coverage_ratio(None) is None


def test_resolve_coverage_ratio_from_diagnostics_prefers_known_fields_order():
    assert resolve_coverage_ratio_from_diagnostics({"coverage": {"line_rate": 0.81}}) == 0.81
    assert resolve_coverage_ratio_from_diagnostics({"coverage": {"coverage_ratio": 82}}) == 0.82
    assert resolve_coverage_ratio_from_diagnostics({"coverage": {"line_coverage_ratio": 0.83}}) == 0.83
    assert resolve_coverage_ratio_from_diagnostics({"coverage": {"coverage_percent": 84}}) == 0.84
    assert resolve_coverage_ratio_from_diagnostics({"coverage": {"unexpected": True}}) is None
