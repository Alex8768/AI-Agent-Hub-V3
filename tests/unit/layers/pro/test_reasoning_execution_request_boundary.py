from __future__ import annotations


def test_normalize_execution_request_filters_invalid_decision():
    from src.layers.pro.reasoning.execution_plane.request_boundary import normalize_execution_request

    out = normalize_execution_request(
        filters={
            "handshake_decision": "unknown",
            "handshake_confirmation_token": "token-1",
            "handshake_action_ids": ["a1", "", "a2"],
            "handshake_idempotency_key": "idem-1",
        }
    )
    assert out == {
        "decision": "",
        "confirmation_token": "token-1",
        "requested_action_ids": ["a1", "a2"],
        "idempotency_key": "idem-1",
    }


def test_build_execution_request_boundary_bundle_marks_ready():
    from src.layers.pro.reasoning.execution_plane.request_boundary import (
        build_execution_request_boundary_bundle,
    )

    out = build_execution_request_boundary_bundle(
        execution_request={
            "decision": "approve",
            "confirmation_token": "token-1",
            "requested_action_ids": ["a1"],
            "idempotency_key": "idem-1",
        },
        transition_policy={"mode": "confirmation_guarded"},
    )
    assert out.get("contract_version") == "v1"
    assert out.get("mode") == "execution_request_boundary"
    assert out.get("status") == "ready"
    assert out.get("transition_policy_mode") == "confirmation_guarded"
    assert out.get("requested_action_ids_count") == 1
    assert out.get("has_confirmation_token") is True
    assert out.get("idempotency_key_present") is True
    reasons = list(out.get("reason_codes") or [])
    assert "execution_request_boundary_runtime_wired" in reasons
    assert "execution_request_decision:approve" in reasons
