# Feedback Adaptation Runtime (A2.43)

## Purpose

`A2.43` introduces feedback-to-planning adaptation diagnostics that transform
approve/cancel/edit signals into deterministic intent-relevance adjustments
while preserving policy-guarded safe behavior.

This milestone provides:

- adaptation diagnostics contract baseline;
- signal-to-plan deterministic adaptation ranking;
- adaptation policy guardrails with forced fallback on violations;
- runtime wiring for diagnostics parity across runtime branches;
- docs + CI quality-gate closure.

Execution remains safe-mode scoped and confirmation-first.

## Contracts

Adaptation contract version: `v1`
Feedback contract version: `v1`
Plan contract version: `v1`

Primary diagnostics contracts:

- `adaptation_contract_version`
- `assistant_feedback_adaptation`
- `adaptation_policy`
- `assistant_feedback_learning`
- `assistant_plan`

## Signal-to-plan deterministic adapter

Adapter runtime derives intent relevance from normalized `latest_signal`:

- `approve` boosts the current plan intent;
- `cancel` boosts `general_query` and can suppress the current intent;
- `edit` boosts current intent and `prepare_meeting`.

Adaptation payload remains diagnostics-only and deterministic.

## Adaptation policy guardrails

Policy contract (`adaptation_policy`) enforces:

- `allowed_latest_signals` allowlist;
- `allowed_intents` allowlist;
- `max_boosted_intents`;
- `max_suppressed_intents`;
- `forbid_boost_suppress_overlap`;
- `fallback_on_policy_violation`.

Policy outcomes include:

- `feedback_adaptation_policy_forced_fallback`
- `feedback_adaptation_latest_signal_not_allowlisted`
- `feedback_adaptation_boosted_intents_exceed_max`
- `feedback_adaptation_suppressed_intents_exceed_max`

## Runtime wiring + diagnostics parity

Runtime wiring guarantees parity in proactive and non-proactive branches.

Parity markers:

- `feedback_adaptation_runtime_wired`
- `feedback_adaptation_runtime_backfilled`
- `feedback_adaptation_runtime_unknown_intent_removed`
- `feedback_adaptation_runtime_overlap_removed`

Wiring synchronizes adaptation diagnostics with normalized feedback and plan
intent while preserving policy limits.

## Feature flags

Adaptation behavior remains behind existing assistant controls:

- `feature_reasoning_api=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for contracts/guardrails/parity;
- README reference to this runtime doc;
- roadmap CI entry for A2.43 feedback adaptation runtime docs quality gate.
