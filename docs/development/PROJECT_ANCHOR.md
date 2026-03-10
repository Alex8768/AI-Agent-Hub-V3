# Project Anchor

## Active Anchor

A2.36 — Confirmation-to-Execution Handshake (MVP)

### Goal

Introduce explicit confirmation-to-execution handshake contracts and diagnostics
for draft actions, while preserving strict no-side-effects behavior in runtime.

### Architecture Position

Planned modules:

- handshake contract baseline under reasoning contracts
- answer diagnostics handshake state wiring
- policy-first transition skeleton for future approval/execute phases

Planned files:
- `src/layers/pro/reasoning/contracts.py`
- `src/services/answer/answer_service.py`
- `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
- `tests/unit/api/test_answer_endpoint_debug_snapshot.py`

### Patch Plan

#### Patch plan
- Patch 1 — Handshake Contract Baseline
- Patch 2 — Confirmation Transition Model (Approved/Cancelled)
- Patch 3 — Execution Receipt Stub Integration
- Patch 4 — Transition Policy Guards
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Handshake Contract Baseline
- [x] Patch 2 — Confirmation Transition Model (Approved/Cancelled)
- [x] Patch 3 — Execution Receipt Stub Integration
- [ ] Patch 4 — Transition Policy Guards
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.36 is complete when:
- handshake contracts and diagnostics are explicit and deterministic
- confirmation transitions are modeled and policy-guarded
- execution receipt baseline is wired without side effects
- release-gate docs/tests cover new handshake contracts

## Next Anchor

A2.37 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.35 — Intent-to-Plan Orchestrator (COO MVP)

Completed via patches:
- Patch 1 — Intent Contract Baseline
- Patch 2 — Deterministic Plan Builder MVP
- Patch 3 — Plan -> Draft Actions Bridge
- Patch 4 — Policy Guards for Planning
- Patch 5 — Docs/CI Closure
