# Project Anchor

## Active Anchor

A2.37 — Approval Session & Idempotent Execution Gateway (Safe Mode)

### Goal

Add deterministic approval-session runtime contracts and diagnostics as the first
step to an idempotent execution gateway, while keeping runtime side-effect free.

### Architecture Position

Planned modules:

- approval-session contract baseline for confirmation workflows
- diagnostics wiring for approval session state in answer runtime
- idempotent execution gateway skeleton for next patches

Planned files:
- `src/layers/pro/reasoning/contracts.py`
- `src/services/answer/answer_service.py`
- `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
- `tests/unit/api/test_answer_endpoint_debug_snapshot.py`

### Patch Plan

#### Patch plan
- Patch 1 — Approval Session Contract Baseline
- Patch 2 — Confirm/Cancel API Contract Surface
- Patch 3 — Idempotency Key + Replay Guard
- Patch 4 — Safe-Mode Execution Gateway
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Approval Session Contract Baseline
- [x] Patch 2 — Confirm/Cancel API Contract Surface
- [x] Patch 3 — Idempotency Key + Replay Guard
- [x] Patch 4 — Safe-Mode Execution Gateway
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.37 is complete when:
- approval session contracts are explicit and deterministic
- confirm/cancel flows use dedicated contract surface
- idempotency and replay protection are diagnostics-backed
- execution gateway remains safe-mode and side-effect free
- docs and release-gate contracts cover A2.37 runtime

## Next Anchor

A2.38 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.36 — Confirmation-to-Execution Handshake (MVP)

Completed via patches:
- Patch 1 — Handshake Contract Baseline
- Patch 2 — Confirmation Transition Model (Approved/Cancelled)
- Patch 3 — Execution Receipt Stub Integration
- Patch 4 — Transition Policy Guards
- Patch 5 — Docs/CI Closure
