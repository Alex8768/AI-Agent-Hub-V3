# Assistant Conversational Recovery Runtime (A2.44)

## Purpose

`A2.44` hardens assistant-mode conversational behavior for low-evidence requests.
The goal is to avoid generic "I do not know" style responses for conversational
queries while keeping strict safety for source-grounded flows.

This milestone provides:

- conversational recovery baseline and runtime hook;
- language-native recovery behavior (`ru`/`en`);
- recovery policy guardrails with forced fallback on violations;
- runtime wiring for deterministic diagnostics parity;
- docs + CI quality-gate closure.

Execution remains safe-mode scoped and policy-guarded.

## Contracts

Assistant contract version: `v1`
Plan contract version: `v1`

Primary diagnostics contracts:

- `assistant_contract_version`
- `response_mode`
- `response_language`
- `assistant_recovery_policy`
- `assistant_chat_recovery_applied`
- `assistant_plan`
- `planning_reason_codes`

## Recovery scope and intent gating

Recovery is designed for low-evidence assistant conversations and is constrained
to conversational intents:

- `general_chat`
- `general_query`

The runtime keeps source-grounded/factual paths under existing evidence policy.

## Recovery policy guardrails

Policy contract (`assistant_recovery_policy`) enforces:

- `allow_low_evidence_only`;
- `allowed_intents`;
- `block_greeting_queries`;
- `allowed_languages`;
- `require_assistant_mode`;
- `fallback_on_policy_violation`.

Policy outcomes include:

- `assistant_chat_recovery_policy_forced_fallback`
- `assistant_chat_recovery_assistant_mode_disabled`
- `assistant_chat_recovery_requires_low_evidence`
- `assistant_chat_recovery_intent_not_allowlisted`
- `assistant_chat_recovery_greeting_blocked`
- `assistant_chat_recovery_language_not_allowlisted`

## Runtime wiring + diagnostics parity

Runtime wiring keeps recovery diagnostics deterministic in proactive and
non-proactive branches.

Parity markers:

- `assistant_chat_recovery_runtime_wired`
- `assistant_chat_recovery_runtime_unknown_violation_removed`
- `assistant_chat_recovery_runtime_applied_flag_reset`
- `assistant_chat_recovery_applied`

Wiring normalizes policy payloads (`allowed_intents`, `allowed_languages`,
`target_language`, `violations`, `applied_reason_codes`) and preserves
reason-code parity through `planning_reason_codes`.

## Feature flags

Conversational recovery remains under existing assistant controls:

- `feature_reasoning_api=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for contracts/guardrails/parity;
- README reference to this runtime doc;
- roadmap CI entry for A2.44 conversational recovery runtime docs quality gate.
