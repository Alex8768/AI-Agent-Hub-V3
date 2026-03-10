# Project Anchor

## Active Anchor

A2.38 — TBD

### Goal

Establish durable approval/idempotency contract baselines for restart-safe COO
confirmation flow, while preserving safe-mode and side-effect-free runtime.

### Architecture Position

Planned modules:

- durable approval session persistence-ready contracts
- durable idempotency record persistence-ready contracts
- diagnostics surface for durable contract snapshots (no persistence yet)

Planned files:
- `src/layers/pro/reasoning/contracts.py`
- `src/services/answer/answer_service.py`
- `tests/unit/layers/pro/test_reasoning_contracts.py`
- `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
- `tests/unit/api/test_answer_endpoint_debug_snapshot.py`

### Patch Plan

#### Patch plan
- Patch 1 — Durable Contracts Baseline
- Patch 2 — Persistence Wiring for Approval/Idempotency Records
- Patch 3 — Token TTL + One-Time Consumption Guards
- Patch 4 — Restart Recovery + Deterministic Replay Outcomes
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Durable Contracts Baseline
- [x] Patch 2 — Persistence Wiring for Approval/Idempotency Records
- [ ] Patch 3 — TBD
- [ ] Patch 4 — TBD
- [ ] Patch 5 — TBD

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.38 is complete when:
- approval/idempotency records are persistence-ready and deterministic
- runtime loads/saves approval/idempotency state via durable wiring
- token ttl + one-time semantics are guard-enforced with diagnostics
- replay outcomes are restart-safe and deterministic
- docs and release-gate contracts cover A2.38 runtime

## Next Anchor

A2.39 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.37 — Approval Session & Idempotent Execution Gateway (Safe Mode)

Completed via patches:
- Patch 1 — Approval Session Contract Baseline
- Patch 2 — Confirm/Cancel API Contract Surface
- Patch 3 — Idempotency Key + Replay Guard
- Patch 4 — Safe-Mode Execution Gateway
- Patch 5 — Docs/CI Closure
