# Project Anchor

## Active Anchor

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

### Patch Plan

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

### Progress

- [x] Patch 1 — trace model
- [x] Patch 2 — trace collector
- [x] Patch 3 — diagnostics.reasoning_trace exposure
- [ ] Patch 4 — serialization
- [ ] Patch 5 — replay utility

### Out of Scope

Do NOT modify during A2.12:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- major reasoning graph redesign

### Definition of Done

A2.12 is complete when:
- reasoning trace is recorded
- trace serialization is implemented
- replay reproduces the reasoning pipeline
- tests validate replay behavior

## Next Anchor

A2.13 — (to be defined)

### Discipline

Work order is strict:
- A2.12 -> A2.13
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.11.5 — Planner evaluation tests (quality gate)

Completed via patches:
- Patch 1 — multi-step reasoning correctness evaluation test added
- Patch 2 — state propagation evaluation test added
- Patch 3 — verify-per-step behavior evaluation test added
- Patch 4 — max_steps safety guard evaluation test added
- Patch 5 — deterministic planner behavior evaluation test added
