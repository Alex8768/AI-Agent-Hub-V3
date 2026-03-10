# Confirmation Handshake Runtime (A2.36)

## Purpose

`A2.36` formalizes a deterministic confirmation-to-execution handshake runtime for
assistant draft actions in `/api/v1/answer` diagnostics.

This milestone provides:

- handshake contracts and transition states;
- deterministic approval/cancellation transitions with token checks;
- transition policy guards for decision/action constraints;
- deterministic execution receipt stub diagnostics.

No real side effects are executed in this milestone.

## Contracts

Handshake contract version: `v1`
Execution receipt contract version: `v1`

Diagnostics contracts exposed:

- `assistant_execution_handshake`
- `execution_transition_policy`
- `assistant_execution_receipt`
- `execution_handshake_contract_version`
- `execution_receipt_contract_version`

## Handshake lifecycle

Supported handshake states:

- `idle`
- `pending_confirmation`
- `approved`
- `executed`
- `cancelled`

Transition inputs are read from request filters:

- `handshake_decision` (`approve` or `cancel`)
- `handshake_confirmation_token`
- `handshake_action_ids`

Token mismatch keeps handshake in `pending_confirmation` with policy reason codes.

## Transition policy guards

The transition policy contract is deterministic:

- mode: `confirmation_guarded`
- required token validation
- `allowed_decisions`: `approve`, `cancel`
- partial approvals allowed
- max approved action ids: `3`

Policy diagnostics include:

- requested/available action counts;
- unknown action ids filtered by policy;
- applied policy reason codes.

## Execution receipt stub

Execution receipt is diagnostics-only in A2.36:

- deterministic `receipt_id` generated for `approved`/`cancelled`;
- status values: `idle`, `awaiting_confirmation`, `recorded`;
- `executed_action_ids` remains empty in this milestone;
- receipt tracks approved/blocked ids for review and audit preparation.

## Feature flags

Runtime remains governed by existing assistant feature flags:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

All defaults stay OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- contract and transition markers in this architecture document;
- README reference to this document;
- roadmap CI entry for A2.36 handshake docs quality gate.
