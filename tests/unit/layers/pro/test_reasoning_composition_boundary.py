from __future__ import annotations


def test_build_composition_request_normalizes_fields():
    from src.layers.pro.reasoning.planner.composition_boundary import build_composition_request

    out = build_composition_request(
        query="  q  ",
        composition_mode=1,
        composition_registry=None,
    )
    assert out == {
        "query": "q",
        "composition_mode": True,
        "composition_registry": None,
    }


def test_build_composition_resolution_normalizes_contract_shape():
    from src.layers.pro.reasoning.planner.composition_boundary import build_composition_resolution

    out = build_composition_resolution(
        mode="resolved",
        reason_codes=["x", "x", ""],
        warnings=["warn", "warn"],
        diagnostics={"a": 1},
        step_descriptions=[" step ", ""],
        composition_graph={"graph_id": "g1"},
    )
    assert out["contract_version"] == "v1"
    assert out["mode"] == "resolved"
    assert out["reason_codes"] == ["x"]
    assert out["warnings"] == ["warn"]
    assert out["diagnostics"] == {"a": 1}
    assert out["step_descriptions"] == ["step"]
    assert out["composition_graph"] == {"graph_id": "g1"}
