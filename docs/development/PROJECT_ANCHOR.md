# Project Anchor

## Active Anchor

A2.45 — Architecture Hardening Track (COO Runtime Reliability)

### Goal

Reduce architectural risk accumulated during fast feature delivery by
introducing deterministic hardening around service boundaries, planner coupling,
and memory consistency diagnostics while preserving current behavior.

### Architecture Position

Planned modules:

- AnswerService boundary extraction scaffold (orchestrator-first shape)
- planner runtime abstraction seam (provider-agnostic boundary)
- memory consistency diagnostics contract (sqlite index parity visibility)
- technical debt ledger + cleanup policy for legacy/temporary runners
- docs/CI closure for hardening policy

### Patch Plan

#### Patch plan
- Patch 1 — Anchor Formalization + Scope Lock
- Patch 2 — AnswerService Boundary Hardening Baseline
- Patch 3 — Planner Coupling Guardrail (Abstraction Seam)
- Patch 4 — Memory Consistency Diagnostics Guardrails
- Patch 5 — Docs/CI Closure + Technical-Debt Registry

### Progress

- [x] Patch 1 — Anchor Formalization + Scope Lock
- [x] Patch 2 — AnswerService Boundary Hardening Baseline
- [x] Patch 3 — Planner Coupling Guardrail (Abstraction Seam)
- [x] Patch 4 — Memory Consistency Diagnostics Guardrails
- [ ] Patch 5 — Docs/CI Closure + Technical-Debt Registry

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.45 completion criteria:
- core runtime contracts and behavior remain backward-compatible;
- hardening diagnostics are deterministic and visible in debug snapshots;
- memory consistency risks are surfaced through explicit policy diagnostics;
- technical-debt items are cataloged with explicit decision status;
- full unit suite and release-gate docs checks remain green.

## Next Anchor

A2.46 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.44 — Assistant Conversational Recovery (Low-Evidence UX)

Completed via patches:
- Patch 1 — Conversational Recovery Baseline + Runtime Hook
- Patch 2 — Language-Native Recovery Adapter Hardening
- Patch 3 — Recovery Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure
