# Approval Execution Gateway Runtime (A2.37)

## Purpose

`A2.37` closes the approval-session and idempotent execution gateway baseline for
assistant draft actions in `/api/v1/answer` diagnostics.

This milestone provides:

- approval session lifecycle diagnostics contract;
- dedicated confirm/cancel API contract surface;
- idempotency key and replay/conflict guard diagnostics;
- safe-mode execution gateway diagnostics with no side effects.

No real execution is performed in this milestone.

## Contracts

Approval session contract version: `v1`
Execution idempotency contract version: `v1`
Execution gateway contract version: `v1`

Diagnostics contracts exposed:

- `assistant_approval_session`
- `execution_idempotency`
- `assistant_execution_gateway`
- `approval_session_contract_version`
- `execution_gateway_contract_version`

## Confirm/Cancel contract surface

Dedicated endpoint:

- `POST /api/v1/answer/confirm`

Request contract fields:

- `decision` (`approve` or `cancel`)
- `confirmation_token`
- `action_ids`
- `idempotency_key`

Mapped transition filters:

- `handshake_decision`
- `handshake_confirmation_token`
- `handshake_action_ids`
- `handshake_idempotency_key`

## Idempotency and replay guard

Idempotency diagnostics (`execution_idempotency`) include:

- `status`: `fresh`, `replayed`, `conflict`, `missing_key`, `not_applicable`, `dry_run`;
- operation fingerprint for deterministic replay matching;
- guard action and reason codes.

Conflict mode blocks transition execution intent and keeps runtime in safe-mode flow.

## Safe-mode execution gateway

Gateway diagnostics (`assistant_execution_gateway`) are deterministic:

- mode: `safe_mode`
- side effects: always disabled
- `executed_action_ids`: always empty in `A2.37`

Gateway state surface:

- `awaiting_confirmation`
- `ready_for_execution`
- `cancelled`
- `disabled`
- `idle`

When handshake is `approved`, gateway reports `ready_for_execution` and mirrors
approved ids only into `dry_run_action_ids`.

## Feature flags

Runtime remains governed by assistant feature flags:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for approval/idempotency/gateway contracts;
- README reference to this runtime doc;
- roadmap CI entry for A2.37 runtime docs quality gate.
