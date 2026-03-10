# Planner Decoupling Runtime (A2.48)

## Purpose

`A2.48` closes remaining planner-coupling debt while preserving strict runtime parity.
The anchor keeps behavior stable and limits changes to composition boundaries,
query normalization, diagnostics parity, and closure governance.

## Debt closure outcome

Closed debt item:

- `TD-A2.45-002`

Closure status in registry:

- `decision_status: resolved_in_a2_48`
- `target_anchor: A2.48`

## Runtime seams introduced or normalized

Planner composition boundary:

- `build_reasoning_planner_runtime`

Prompt/planner input boundary:

- `normalize_reasoning_query_input`

Deterministic diagnostics parity boundary:

- `planner_runtime_parity`

## Architecture position

Planner/runtime composition must stay behind kernel seams so callers do not depend on
concrete planner module paths.

Required separation:

- planner callsites consume kernel seam contracts;
- prompt/planner query input is normalized through one boundary contract;
- diagnostics shape remains deterministic across planner and fallback paths.

## Runtime parity and non-negotiables

`A2.48` is closure work only, with no behavior expansion:

- no net-new model/provider capability;
- no planner threshold policy changes;
- no intelligence scope expansion;
- planner outputs and diagnostics contracts remain backward-compatible.

## Quality gates

Deterministic guardrails for this closure:

- `tests/unit/layers/pro/test_reasoning_kernel_runtime.py`
- `tests/unit/layers/pro/test_reasoning_planner.py`
- `tests/unit/layers/pro/test_reasoning_prompt_builder.py`
- `tests/unit/layers/pro/test_reasoning_engine_planner_runtime_parity.py`
- `tests/unit/docs/test_planner_decoupling_runtime_quality_gate.py`

## Feature-flag baseline

Runtime closure preserves default-safe behavior with:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

