# Project Anchor

## Active Anchor

A2.43 — Feedback-to-Planning Adaptation (MVP)

### Goal

Use captured approve/cancel/edit feedback to deterministically adapt
plan/action relevance diagnostics while preserving safe-mode constraints.

### Architecture Position

Planned modules:

- adaptation diagnostics contract baseline
- signal-to-plan deterministic adapter
- adaptation policy guardrails
- runtime wiring + diagnostics parity
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — Adaptation Contract Baseline
- Patch 2 — Signal-to-Plan Adapter + Deterministic Ranking
- Patch 3 — Adaptation Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Adaptation Contract Baseline
- [x] Patch 2 — Signal-to-Plan Adapter + Deterministic Ranking
- [x] Patch 3 — Adaptation Policy Guardrails
- [ ] Patch 4 — Runtime Wiring + Diagnostics Parity
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.43 completion criteria:
- feedback signals influence planning diagnostics deterministically.
- adaptation remains policy-guarded and review-safe by default.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.44 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.42 — Learning from Feedback (Approve/Cancel/Edit)

Completed via patches:
- Patch 1 — Feedback Contract Baseline
- Patch 2 — Feedback Capture Adapter + Deterministic Normalization
- Patch 3 — Feedback Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure
