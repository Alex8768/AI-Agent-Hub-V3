# Project Anchor

## Active Anchor

A2.39 — Controlled Execution Pilot (Strict Safe Mode+)

### Goal

Introduce a strictly controlled execution pilot surface on top of safe-mode runtime:
formalize pilot contracts, enforce allowlist/policy gates, and keep execution auditable
with mandatory receipt and rollback contracts.

### Architecture Position

Planned modules:

- execution pilot contract baseline (diagnostics-first)
- allowlist and execution policy gates
- receipt/rollback enforcement contract
- controlled runtime wiring for allowlisted low-risk actions
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — Execution Pilot Contract Baseline
- Patch 2 — Allowlist + Policy Gate
- Patch 3 — Receipt + Rollback Contract Enforcement
- Patch 4 — Pilot Runtime Wiring
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Execution Pilot Contract Baseline
- [ ] Patch 2 — Allowlist + Policy Gate
- [ ] Patch 3 — Receipt + Rollback Contract Enforcement
- [ ] Patch 4 — Pilot Runtime Wiring
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.39 completion criteria:
- allowlisted low-risk action execution only (strict policy gate).
- approval/idempotency/receipt/rollback diagnostics stay deterministic and explicit.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.40 — Intent-based Planning Engine (LLM Planner)

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.38 — Durable Approval Recovery Runtime (Safe Mode)

Completed via patches:
- Patch 1 — Durable Contracts Baseline
- Patch 2 — Persistence Wiring for Approval/Idempotency Records
- Patch 3 — Token TTL + One-Time Consumption Guards
- Patch 4 — Restart Recovery + Deterministic Replay Outcomes
- Patch 5 — Docs/CI Closure
