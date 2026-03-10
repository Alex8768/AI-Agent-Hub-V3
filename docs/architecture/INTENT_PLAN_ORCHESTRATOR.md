# Intent-to-Plan Orchestrator (A2.35)

## Purpose

`A2.35` introduces a deterministic intent-to-plan baseline for assistant runtime in
`/api/v1/answer`. The orchestrator converts free-form user input into:

- normalized intent diagnostics;
- deterministic review-only plan diagnostics;
- policy-guarded plan state;
- draft-action bridge diagnostics.

No side effects are executed in this milestone. All outputs are diagnostics-only
and confirmation-first.

## Contracts

Intent contract version: `v1`
Plan contract version: `v1`

Primary runtime diagnostics contracts:

- `assistant_intent`
- `assistant_plan`
- `planning_policy`
- `planning_reason_codes`
- `plan_id`

## Runtime flow

1. Extract assistant intent via deterministic heuristic contract baseline.
2. Build deterministic plan from `(intent, normalized query)`.
3. Apply policy guards in review-only mode.
4. Bridge plan steps into draft actions when assistant actions are enabled and
   proactive pipeline does not provide actions.
5. Emit diagnostics snapshot for API/UI observability.

## Policy guards

Planning policy is strict review-only:

- allowed action pattern: `prepare_*_draft`
- blocked unsafe markers: `execute`, `delete`, `write`, `send`, `publish`
- plan steps cap: `max_steps=5`
- blocked or truncated plans are explicitly reflected in `planning_policy`

If all steps are blocked, plan status transitions to `guarded`.

## Determinism and safety

- `plan_id` is deterministic and derived from `(intent, normalized query)`.
- Planning outputs are stable for equivalent inputs.
- All generated actions are draft-only and `requires_confirmation=true`.
- Rollback notes are included for draft actions even though side effects are not executed.

## Feature flags

Assistant planning behavior is gated by existing assistant flags:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Default-off behavior remains unchanged for Base and for Pro runtime when flags are off.

## Diagnostics surface

`/api/v1/answer` diagnostics include:

- `intent_contract_version`
- `plan_contract_version`
- `assistant_intent`
- `assistant_plan`
- `planning_policy`
- `planning_reason_codes`
- `plan_id`
- `anticipatory.draft_actions`

## Quality gates

Release-gate docs checks validate:

- architecture doc markers for intent-plan contracts and policy;
- README reference to this architecture doc;
- roadmap CI alignment for A2.35 docs quality gate.
