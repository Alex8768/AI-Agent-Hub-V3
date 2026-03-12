from __future__ import annotations

from src.layers.pro.reasoning.execution_plane.request_boundary import (
    normalize_execution_request,
)
from src.layers.pro.reasoning.contracts import (
    APPROVAL_SESSION_CONTRACT_VERSION,
    AnswerRequest,
    DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    EXECUTION_PILOT_CONTRACT_VERSION,
    EXECUTION_RECEIPT_CONTRACT_VERSION,
    HANDSHAKE_CONTRACT_VERSION,
    IDEMPOTENCY_RECORD_CONTRACT_VERSION,
)
from src.services.answer.execution.durable_keys import (
    apply_durable_confirmation_token_guards as _apply_durable_confirmation_token_guards_impl,
    apply_execution_idempotency_guard as _apply_execution_idempotency_guard_impl,
    apply_handshake_transition as _apply_handshake_transition_impl,
    apply_handshake_transition_policy as _apply_handshake_transition_policy_impl,
    apply_rollback_contract_guard as _apply_rollback_contract_guard_impl,
    build_approval_session_bundle as _build_approval_session_bundle_impl,
    build_durable_approval_session_record as _build_durable_approval_session_record_impl,
    build_execution_handshake_bundle as _build_execution_handshake_bundle_impl,
    build_execution_pilot_bundle as _build_execution_pilot_bundle_impl,
    build_execution_receipt_stub as _build_execution_receipt_stub_impl,
    build_idempotency_record_snapshot as _build_idempotency_record_snapshot_impl,
    build_safe_mode_execution_gateway as _build_safe_mode_execution_gateway_impl,
    run_execution_pilot_runtime as _run_execution_pilot_runtime_impl,
)

EXECUTION_IDEMPOTENCY_CONTRACT_VERSION = "v1"
EXECUTION_GATEWAY_CONTRACT_VERSION = "v1"
EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES: tuple[str, ...] = (
    "prepare_summary_draft",
    "collect_context_draft",
    "prepare_workflow_draft",
)
EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN = "prepare_*_draft"
EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS = 1
_EXECUTION_IDEMPOTENCY_SEEN: dict[str, str] = {}


def build_execution_handshake_bundle(
    *,
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_execution_handshake_bundle_impl(
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions_bundle,
        assistant_mode_enabled=assistant_mode_enabled,
        actions_enabled=actions_enabled,
        handshake_contract_version=HANDSHAKE_CONTRACT_VERSION,
    )


def extract_handshake_transition_input(req: AnswerRequest) -> dict[str, object]:
    filters = dict(getattr(req, "filters", {}) or {})
    return normalize_execution_request(filters=filters)


def apply_handshake_transition(
    *,
    handshake_bundle: dict[str, object],
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> dict[str, object]:
    return _apply_handshake_transition_impl(
        handshake_bundle=handshake_bundle,
        transition_input=transition_input,
        draft_actions_bundle=draft_actions_bundle,
    )


def apply_execution_idempotency_guard(
    *,
    transition_input: dict[str, object],
    workspace_id: str,
    plan_id: str,
    prior_record: dict[str, object] | None = None,
    persist: bool = True,
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_execution_idempotency_guard_impl(
        transition_input=transition_input,
        workspace_id=workspace_id,
        plan_id=plan_id,
        prior_record=prior_record,
        persist=persist,
        execution_idempotency_contract_version=EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
        seen_store=_EXECUTION_IDEMPOTENCY_SEEN,
    )


def build_transition_policy_contract() -> dict[str, object]:
    from src.services.answer.reasoning.llm_planner_policy import (
        build_transition_policy_contract as _build_transition_policy_contract_impl,
    )

    return _build_transition_policy_contract_impl(
        max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        allowlisted_action_pattern=EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN,
    )


def is_allowlisted_pilot_action_type(action_type: str, allowlisted_action_types: set[str]) -> bool:
    normalized = str(action_type or "").strip()
    if not normalized:
        return False
    if normalized in allowlisted_action_types:
        return True
    return normalized.startswith("prepare_") and normalized.endswith("_draft")


def apply_handshake_transition_policy(
    *,
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_handshake_transition_policy_impl(
        transition_input=transition_input,
        draft_actions_bundle=draft_actions_bundle,
        policy_contract=policy_contract,
        is_allowlisted_action_type_fn=is_allowlisted_pilot_action_type,
    )


def apply_durable_confirmation_token_guards(
    *,
    transition_input: dict[str, object],
    durable_approval_record: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    return _apply_durable_confirmation_token_guards_impl(
        transition_input=transition_input,
        durable_approval_record=durable_approval_record,
    )


def apply_rollback_contract_guard(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_rollback_contract_guard_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
    )


def run_execution_pilot_runtime(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    actions_enabled: bool,
) -> tuple[list[str], list[str]]:
    return _run_execution_pilot_runtime_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
        actions_enabled=actions_enabled,
        execution_pilot_allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        execution_pilot_max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        is_allowlisted_action_type_fn=is_allowlisted_pilot_action_type,
    )


def build_execution_receipt_stub(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
    executed_action_ids: list[str] | None = None,
) -> dict[str, object]:
    return _build_execution_receipt_stub_impl(
        handshake_bundle=handshake_bundle,
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions_bundle,
        workspace_id=workspace_id,
        request_id=request_id,
        executed_action_ids=executed_action_ids,
        execution_receipt_contract_version=EXECUTION_RECEIPT_CONTRACT_VERSION,
    )


def build_safe_mode_execution_gateway(
    *,
    handshake_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_safe_mode_execution_gateway_impl(
        handshake_bundle=handshake_bundle,
        receipt_bundle=receipt_bundle,
        actions_enabled=actions_enabled,
        execution_gateway_contract_version=EXECUTION_GATEWAY_CONTRACT_VERSION,
    )


def build_execution_pilot_bundle(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_execution_pilot_bundle_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
        receipt_bundle=receipt_bundle,
        actions_enabled=actions_enabled,
        execution_pilot_contract_version=EXECUTION_PILOT_CONTRACT_VERSION,
        execution_pilot_allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        execution_pilot_max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        is_allowlisted_action_type_fn=is_allowlisted_pilot_action_type,
    )


def build_approval_session_bundle(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
) -> dict[str, object]:
    return _build_approval_session_bundle_impl(
        handshake_bundle=handshake_bundle,
        plan_bundle=plan_bundle,
        workspace_id=workspace_id,
        request_id=request_id,
        approval_session_contract_version=APPROVAL_SESSION_CONTRACT_VERSION,
    )


def build_durable_approval_session_record(
    *,
    approval_session_bundle: dict[str, object],
    session_id: str,
    confirmation_token: str,
    transition_input: dict[str, object],
    previous_record: dict[str, object] | None = None,
) -> dict[str, object]:
    return _build_durable_approval_session_record_impl(
        approval_session_bundle=approval_session_bundle,
        session_id=session_id,
        confirmation_token=confirmation_token,
        transition_input=transition_input,
        previous_record=previous_record,
        durable_approval_session_contract_version=DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    )


def build_idempotency_record_snapshot(
    *,
    execution_idempotency_bundle: dict[str, object],
    workspace_id: str,
    plan_id: str,
    transition_input: dict[str, object],
) -> dict[str, object]:
    return _build_idempotency_record_snapshot_impl(
        execution_idempotency_bundle=execution_idempotency_bundle,
        workspace_id=workspace_id,
        plan_id=plan_id,
        transition_input=transition_input,
        idempotency_record_contract_version=IDEMPOTENCY_RECORD_CONTRACT_VERSION,
    )
