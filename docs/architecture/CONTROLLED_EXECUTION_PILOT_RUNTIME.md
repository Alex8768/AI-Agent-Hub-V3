# Controlled Execution Pilot Runtime (A2.39)

## Purpose

`A2.39` closes the controlled execution pilot runtime for assistant draft actions
with strict safe-mode constraints and deterministic diagnostics in `/api/v1/answer`.

This milestone provides:

- execution pilot contract baseline diagnostics;
- allowlist and transition policy guardrails;
- receipt + rollback contract enforcement before approval execution;
- controlled pilot runtime wiring for allowlisted low-risk actions;
- docs + CI quality-gate closure for the runtime surface.

Pilot runtime stays safe-mode scoped: no external side effects are performed.

## Contracts

Execution pilot contract version: `v1`
Execution receipt contract version: `v1`

Diagnostics contracts exposed:

- `assistant_execution_pilot`
- `assistant_execution_receipt`
- `execution_transition_policy`
- `execution_pilot_contract_version`

## Policy and allowlist guards

Transition policy contract enforces:

- `max_approved_action_ids` capped at 1;
- `allowlisted_action_types` for pilot execution;
- `allowlisted_action_pattern` (`prepare_*_draft`);
- non-allowlisted action filtering before approval transition.

Guard reasons include:

- `non_allowlisted_action_types_blocked`
- `approval_limit_applied`
- `unknown_action_ids_blocked`

## Receipt and rollback enforcement

Before approval can move into pilot runtime, rollback contract must be valid.

Rollback diagnostics include:

- `rollback_contract_status`
- `rollback_missing_action_ids`
- `rollback_status` in `assistant_execution_receipt`

If rollback contract is missing, approval is blocked with:

- `rollback_contract_missing_for_approved_actions`

## Controlled pilot runtime wiring

When approval passes all guards, pilot runtime can mark allowlisted actions as
executed in diagnostics:

- gateway state: `executed_in_pilot`;
- pilot state: `executed`;
- receipt reason: `pilot_runtime_execution_recorded`.

Safe-mode guarantee remains explicit: no external side effects.

## Feature flags

Runtime remains governed by assistant feature flags:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for pilot contracts/policy/rollback/runtime states;
- README reference to this runtime doc;
- roadmap CI entry for A2.39 runtime docs quality gate.
