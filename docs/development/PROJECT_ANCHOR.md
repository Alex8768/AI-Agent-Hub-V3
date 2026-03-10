# Project Anchor

## Active Anchor

A2.41 — Dynamic Tool Selection (MCP-aware)

### Goal

Introduce policy-sandboxed dynamic tool selection for planner steps with
MCP-aware routing and strict execution safeguards.

### Architecture Position

Planned modules:

- MCP-aware tool selection contract baseline
- tool selection adapter + deterministic fallback
- tool selection policy guardrails
- runtime wiring + diagnostics parity
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — Tool Selection Contract Baseline
- Patch 2 — MCP-aware Selector Adapter + Fallback
- Patch 3 — Tool Selection Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Tool Selection Contract Baseline
- [x] Patch 2 — MCP-aware Selector Adapter + Fallback
- [ ] Patch 3 — Tool Selection Policy Guardrails
- [ ] Patch 4 — Runtime Wiring + Diagnostics Parity
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.41 completion criteria:
- selected tools remain policy-guarded with deterministic safe fallback.
- MCP-aware selection stays explicit and diagnosable in runtime snapshots.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.42 — Learning from Feedback (Approve/Cancel/Edit)

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.40 — Intent-based Planning Engine (LLM Planner)

Completed via patches:
- Patch 1 — LLM Planner Contract Baseline
- Patch 2 — Planner Adapter + Deterministic Fallback
- Patch 3 — Planner Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure
