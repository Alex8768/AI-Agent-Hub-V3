# Feedback Learning Runtime (A2.42)

## Purpose

`A2.42` introduces approve/cancel/edit feedback learning diagnostics
while preserving deterministic normalization and policy-guarded safety.

This milestone provides:

- feedback-learning diagnostics contract baseline;
- feedback capture adapter with deterministic signal normalization;
- feedback policy guardrails with forced fallback on violations;
- runtime wiring for diagnostics parity across runtime branches;
- docs + CI quality-gate closure.

Execution remains safe-mode scoped and confirmation-first.

## Contracts

Feedback contract version: `v1`
Plan contract version: `v1`

Primary diagnostics contracts:

- `feedback_contract_version`
- `assistant_feedback_learning`
- `feedback_policy`
- `assistant_plan`

## Feedback capture adapter + deterministic normalization

Feedback runtime normalizes signals into an allowlisted set:

- `approve`
- `cancel`
- `edit`

Normalization behavior:

- preserve first-seen order for normalized signals;
- deduplicate repeated entries;
- ignore unknown signals from mixed request inputs;
- derive `latest_signal` from normalized data when needed.

## Feedback policy guardrails

Policy contract (`feedback_policy`) enforces:

- `allowed_signals` allowlist;
- `max_signals_per_request`;
- `require_latest_in_signals`;
- `fallback_on_policy_violation`.

Policy outcomes include:

- `feedback_policy_forced_fallback`
- `feedback_signals_exceed_max`
- `feedback_latest_signal_mismatch`

## Runtime wiring + diagnostics parity

Runtime wiring guarantees parity in proactive and non-proactive branches.

Parity markers:

- `feedback_runtime_wired`
- `feedback_runtime_unknown_signals_removed`

Wiring keeps `assistant_feedback_learning` and `feedback_policy` diagnostics
consistent after runtime composition.

## Feature flags

Feedback runtime behavior remains behind existing assistant controls:

- `feature_reasoning_api=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for contracts/guardrails/parity;
- README reference to this runtime doc;
- roadmap CI entry for A2.42 feedback learning runtime docs quality gate.
