# LLM Planner Runtime (A2.40)

## Purpose

`A2.40` introduces an intent-based planning runtime that can use an LLM planner
adapter while preserving deterministic planning safety and fallback behavior.

This milestone provides:

- LLM planner diagnostics contract baseline;
- planner adapter wiring with deterministic fallback;
- planner policy guardrails with forced fallback on violations;
- runtime diagnostics parity across proactive and non-proactive paths;
- docs + CI quality-gate closure.

Execution remains safe-mode scoped and confirmation-first.

## Contracts

LLM planner contract version: `v1`
Plan contract version: `v1`

Diagnostics contracts exposed:

- `llm_planner_contract_version`
- `assistant_llm_planner`
- `llm_planner_policy`
- `assistant_plan`

## Planner adapter and fallback

Planner runtime supports three outcomes:

- `source=llm`, `status=ready` when adapter returns a valid allowlisted intent;
- `source=fallback`, `status=fallback` when adapter is unavailable/invalid;
- `source=heuristic`, `status=disabled` when LLM planner is disabled.

Fallback preserves deterministic plan construction and existing safe behavior.

## Planner policy guardrails

Policy contract (`llm_planner_policy`) enforces:

- `allowed_intents` allowlist;
- `require_plan_id_prefix_match`;
- `fallback_on_policy_violation`.

Key guard outcomes:

- `llm_planner_policy_forced_fallback`
- `llm_planner_intent_not_allowlisted`
- `llm_plan_id_intent_mismatch`

## Runtime diagnostics parity

Runtime wiring keeps planner diagnostics synchronized in all runtime branches.

Parity markers:

- `llm_planner_runtime_wired`
- `llm_planner_runtime_plan_id_synced`

`assistant_llm_planner.plan_id` is aligned with `assistant_plan.plan_id`.

## Feature flags

Planner runtime remains governed by existing flags:

- `feature_reasoning_llm_enabled=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for planner contracts/guardrails/parity;
- README reference to this runtime doc;
- roadmap CI entry for A2.40 planner runtime docs quality gate.
