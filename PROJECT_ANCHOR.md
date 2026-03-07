# Project Anchor

## Active Anchor

A2.14 — Reasoning Control Layer

### Goal

Introduce a runtime control layer for reasoning execution.

This layer governs planner execution, step retries,
loop protection and execution limits.

### Architecture Position

New module:

`src/layers/pro/reasoning/control/`

Planned files:
- `execution_policy.py`
- `step_controller.py`
- `loop_guard.py`

### Patch Plan

#### Patch 1 — Execution policy
- Introduce `ReasoningExecutionPolicy` model and normalization rules.

#### Patch 2 — Step controller
- Add step controller for planner-driven execution boundaries.

#### Patch 3 — Loop guard
- Add deterministic loop guard for runaway reasoning.

#### Patch 4 — Policy integration
- Integrate control policy with planner/executor/quality loop.

#### Patch 5 — Control tests
- Add tests validating control layer behavior.

### Progress

- [x] Patch 1 — execution policy
- [x] Patch 2 — step controller
- [ ] Patch 3 — loop guard
- [ ] Patch 4 — policy integration
- [ ] Patch 5 — control tests

### Out of Scope

Do NOT modify during A2.14:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- major reasoning graph redesign

### Definition of Done

A2.14 is complete when:
- execution policy is enforced
- planner obeys control layer
- infinite loops are prevented
- retry behaviour is bounded
- tests validate reasoning control behaviour

## Next Anchor

A2.15 — (to be defined)

### Discipline

Work order is strict:
- A2.14 -> A2.15
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.13 — Reasoning Observability

Completed via patches:
- Patch 1 — timeline model contract added with deterministic event normalization
- Patch 2 — timeline collector boundaries added with latency aggregation
- Patch 3 — trace contract enriched with timeline payload
- Patch 4 — diagnostics.reasoning_timeline exposed with stable shape
- Patch 5 — timeline quality-gate tests added (ordering, duration, trace integration)
