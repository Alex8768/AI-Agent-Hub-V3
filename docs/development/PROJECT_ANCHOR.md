# Project Anchor

## Active Anchor

A2.35 — Intent-to-Plan Orchestrator (COO MVP)

### Goal

Add a deterministic intent-to-plan baseline for assistant runtime: extract normalized
intent from free-form request, expose stable planning diagnostics, and keep all
execution in review-only mode (no side effects).

### Architecture Position

Planned modules:

- intent contract baseline under reasoning contracts
- answer diagnostics bridge for intent/planning metadata
- deterministic planner skeleton for next patches

Planned files:
- `src/layers/pro/reasoning/contracts.py`
- `src/services/answer/answer_service.py`
- `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
- `tests/unit/api/test_answer_endpoint_debug_snapshot.py`

### Patch Plan

#### Patch plan
- Patch 1 — Intent Contract Baseline
- Patch 2 — Deterministic Plan Builder MVP
- Patch 3 — Plan -> Draft Actions Bridge
- Patch 4 — Policy Guards for Planning
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Intent Contract Baseline
- [x] Patch 2 — Deterministic Plan Builder MVP
- [x] Patch 3 — Plan -> Draft Actions Bridge
- [ ] Patch 4 — Policy Guards for Planning
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.35 is complete when:
- intent contract and planning diagnostics are stable and deterministic
- plan generation is deterministic and review-only by default
- policy guards prevent unsafe or side-effectful execution paths
- plan-to-draft-action bridge is covered by focused tests
- docs and release-gate quality checks are aligned

## Next Anchor

A2.36 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.34 — Digital COO Runtime (Assistant + Draft Actions)

Completed via patches:
- Patch 1 — Assistant mode contracts, flags, and diagnostics baseline
- Patch 2 — Language-native assistant fallback behavior
- Patch 3 — Proactive suggestion ranking MVP
- Patch 4 — Draft action runtime (review-before-execute)
- Patch 5 — Docs/CI closure for assistant runtime
