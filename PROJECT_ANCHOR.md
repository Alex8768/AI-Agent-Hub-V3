# Project Anchor

## Active Anchor

A2.13 — Reasoning Observability

### Goal

Introduce full observability for reasoning execution.

This includes timeline events, step latency, planner decisions,
verify outcomes and quality evaluation visibility.

### Architecture Position

Planned module:
- `src/layers/pro/reasoning/observability/`

Planned files:
- `timeline_model.py`
- `timeline_collector.py`
- `trace_enricher.py`

### Patch Plan

#### Patch 1 — Timeline model
- Introduce `ReasoningTimelineEvent` and `ReasoningTimeline` structures.

#### Patch 2 — Timeline collector
- Collect timeline events during reasoning execution.

#### Patch 3 — Trace enrichment
- Add timeline information to `ReasoningTrace`.

#### Patch 4 — Diagnostics exposure
- Expose `diagnostics.reasoning_timeline`.

#### Patch 5 — Timeline tests
- Add tests validating timeline generation and structure.

### Progress

- [x] Patch 1 — timeline model
- [x] Patch 2 — timeline collector
- [ ] Patch 3 — trace enrichment
- [ ] Patch 4 — diagnostics.reasoning_timeline exposure
- [ ] Patch 5 — timeline tests

### Out of Scope

Do NOT modify during A2.13:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- major reasoning graph redesign

### Definition of Done

A2.13 is complete when:
- reasoning timeline events are recorded
- timeline is attached to reasoning trace
- diagnostics.reasoning_timeline is exposed
- timeline behaviour is covered by tests

## Next Anchor

A2.14 — (to be defined)

### Discipline

Work order is strict:
- A2.13 -> A2.14
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.12 — Reasoning Trace + Replay

Completed via patches:
- Patch 1 — trace model contract extracted with deterministic normalization
- Patch 2 — trace collector added (plan/steps/verify/quality assembly)
- Patch 3 — diagnostics.reasoning_trace exposed and contract-tested
- Patch 4 — deterministic trace serializer/deserializer added
- Patch 5 — replay utility added for deterministic trace reproduction

## A2.14 — Reasoning Control Layer

### Goal

Introduce a runtime control layer for reasoning execution.

This layer governs planner execution, step retries,
loop protection and execution limits.

### Architecture Position

New module:

src/layers/pro/reasoning/control/

Planned files:

- execution_policy.py
- step_controller.py
- loop_guard.py

### Patch Plan

Patch 1 — Execution policy  
Patch 2 — Step controller  
Patch 3 — Loop guard  
Patch 4 — Policy integration  
Patch 5 — Control tests

### Definition of Done

A2.14 is complete when:

- execution policy is enforced
- planner obeys control layer
- infinite loops are prevented
- retry behaviour is bounded
- tests validate reasoning control behaviour
