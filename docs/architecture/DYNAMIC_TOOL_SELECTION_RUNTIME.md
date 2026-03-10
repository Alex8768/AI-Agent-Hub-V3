# Dynamic Tool Selection Runtime (A2.41)

## Purpose

`A2.41` introduces MCP-aware dynamic tool selection for assistant planning
while preserving deterministic safety and policy-guarded fallback behavior.

This milestone provides:

- tool selection diagnostics contract baseline;
- MCP-aware selector adapter with deterministic fallback;
- policy guardrails for route/step constraints;
- runtime wiring for diagnostics parity across runtime branches;
- docs + CI quality-gate closure.

Execution remains safe-mode scoped and confirmation-first.

## Contracts

Tool selection contract version: `v1`
Plan contract version: `v1`

Primary diagnostics contracts:

- `tool_selection_contract_version`
- `assistant_tool_selection`
- `tool_selection_policy`
- `assistant_plan`

## Selector adapter + fallback

Selector runtime derives candidate tool mappings from MCP registry metadata
(`tool_name`, `description`, `tags`) against plan-step intent tokens.

Adapter outcomes:

- `source=mcp` when at least one step has MCP registry match;
- `source=deterministic` when no MCP matches are available;
- deterministic fallback rows (`tool_name=none`, `route=deterministic_fallback`)
  keep diagnostics complete for every plan step.

## Policy guardrails

Policy contract (`tool_selection_policy`) enforces:

- `allowed_routes` allowlist;
- `require_plan_step_binding`;
- `max_selected_tools`;
- `fallback_on_policy_violation`.

Policy outcomes include:

- `tool_selection_policy_forced_fallback`
- `tool_selection_step_not_in_plan`
- `tool_selection_route_not_allowlisted`

## Runtime wiring + diagnostics parity

Runtime wiring guarantees parity in proactive and non-proactive branches.

Parity markers:

- `tool_selection_runtime_wired`
- `tool_selection_runtime_backfilled`
- `tool_selection_runtime_orphaned_steps_removed`

Wiring keeps one tool-selection row per plan step and removes orphaned rows.

## Feature flags

Tool selection behavior remains behind existing assistant controls:

- `feature_reasoning_api=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for contracts/guardrails/parity;
- README reference to this runtime doc;
- roadmap CI entry for A2.41 dynamic tool selection docs quality gate.
