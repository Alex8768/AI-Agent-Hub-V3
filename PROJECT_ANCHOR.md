# Project Anchor

## Active Anchor

A2.11.5 — Planner evaluation tests (quality gate)

### Goal

Introduce deterministic evaluation tests for the multi-step planner before enabling
A2.12 Reasoning Trace + Replay.

These tests validate that planner behavior remains stable and predictable.

### Architecture Position

Planned test module:
- `tests/unit/layers/pro/test_reasoning_planner_evaluation.py`

### Patch Plan

#### Patch 1 — Multi-step reasoning correctness
- Verify planner-driven multi-step execution is correct.

#### Patch 2 — State propagation
- Verify reasoning state is propagated across steps.

#### Patch 3 — Verify-per-step behavior
- Verify each step runs verify with stable contract.

#### Patch 4 — max_steps safety guard
- Verify step limit is enforced deterministically.

#### Patch 5 — Deterministic planner behavior
- Verify planner output and execution are stable across runs.

### Progress

- [ ] Patch 1 — multi-step reasoning correctness
- [ ] Patch 2 — state propagation
- [ ] Patch 3 — verify-per-step behavior
- [ ] Patch 4 — max_steps safety guard
- [ ] Patch 5 — deterministic planner behavior

### Out of Scope

Do NOT modify during A2.11.5:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- A2.12 implementation before A2.11.5 is closed

### Definition of Done

A2.11.5 is complete when:
- planner evaluation tests exist
- tests validate multi-step execution
- tests validate state propagation
- tests validate `max_steps` guard
- planner passes evaluation suite consistently

## Next Defined Anchor

A2.12 — Reasoning Trace + Replay

### Goal

Make reasoning deterministic and reproducible through trace recording and replay.

### Architecture Position

Planned module:
- `src/layers/pro/reasoning/trace/`

Planned files:
- `trace_model.py`
- `trace_collector.py`
- `trace_serializer.py`
- `replay.py`

### Patch Plan (predefined, not active)

#### Patch 1 — Trace model
- Introduce `ReasoningTrace` structure.

#### Patch 2 — Trace collector
- Collect plan steps, verify results, quality data.

#### Patch 3 — Diagnostics exposure
- Expose `diagnostics.reasoning_trace`.

#### Patch 4 — Serialization
- Save trace for debugging and post-analysis.

#### Patch 5 — Replay utility
- Replay reasoning pipeline from stored trace.

### Definition of Done

A2.12 is complete when:
- reasoning trace is recorded
- trace serialization is implemented
- replay reproduces the reasoning pipeline
- tests validate replay behavior

### Discipline

Work order is strict:
- A2.11 (complete) -> A2.11.5 quality gate -> A2.12
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.11 — Multi-step Reasoning Planner

Completed via patches:
- Patch 1 — plan model contract extracted with deterministic normalization helper
- Patch 2 — deterministic MVP planner added (query -> one/two steps)
- Patch 3 — step executor boundary added with verify-per-step contract
- Patch 4 — planner + step executor integrated into `ReasoningEngine` fallback flow
- Patch 5 — max_steps safety guard enforced in step execution
