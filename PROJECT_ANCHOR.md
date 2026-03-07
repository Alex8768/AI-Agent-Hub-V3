# Project Anchor

## Active Anchor

A2.11 — Multi-step Reasoning Planner

### Goal

Enable the reasoning engine to execute multiple reasoning steps instead of a single step.

Current pipeline:
- query -> retrieval -> reasoning -> verify -> quality -> answer

Target pipeline:
- query -> planner -> step reasoning -> verify -> step reasoning -> verify -> quality -> answer

Reasoning becomes a planned process, while keeping execution deterministic and bounded.

### Architecture Position

New module:
- `src/layers/pro/reasoning/planner/`

Planned files:
- `plan_model.py`
- `planner.py`
- `step_executor.py`

### Patch Plan

#### Patch 1 — Plan model
- Introduce structured plan representation.
- Minimal contract:
  - `PlanStep` with `description`.
  - `ReasoningPlan` with `steps: list[PlanStep]`.

#### Patch 2 — Planner
- Convert query to reasoning plan.
- MVP planner can produce one or two steps without heavy heuristics.

#### Patch 3 — Step executor
- Execute each reasoning step and run verify per step.

#### Patch 4 — Engine integration
- Execute plan steps sequentially inside `ReasoningEngine`.

#### Patch 5 — Safety limits
- Introduce `max_steps` guard to prevent infinite loops.

### Progress

- [ ] Patch 1 — plan model
- [ ] Patch 2 — planner
- [ ] Patch 3 — step executor
- [ ] Patch 4 — engine integration
- [ ] Patch 5 — safety limits (`max_steps`)

### Out of Scope

Do NOT modify during A2.11:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- A2.12 implementation before A2.11 is closed

### Definition of Done

A2.11 is complete when:
- planner generates a reasoning plan
- step executor runs reasoning steps
- verify works per step
- `max_steps` guard is implemented
- tests cover multi-step reasoning scenarios

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
- A2.11 -> STOP -> A2.12
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.10 — Reasoning Quality Loop

Completed via patches:
- Patch 0 — claim extraction boundary extracted with parity
- Patch 1 — evidence coverage scoring boundary extracted with parity
- Patch 2 — reasoning confidence model boundary extracted with parity
- Patch 3 — single bounded retry policy boundary extracted with loop guard
- Patch 4 — diagnostics.reasoning_quality exposure with contract parity tests frozen
