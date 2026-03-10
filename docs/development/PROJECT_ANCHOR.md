# Project Anchor

## Active Anchor

A2.43 — TBD (post-feedback planning)

### Goal

Define the next implementation anchor after feedback-learning stabilization.

### Architecture Position

Planned modules:

- TBD (post-feedback planning)

### Patch Plan

#### Patch plan
- Patch plan is intentionally deferred until A2.43 scope is approved.

### Progress

- [ ] Patch 1 — TBD

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.43 completion criteria:
- scope, contracts, and patch plan are explicitly documented and approved.
- selected implementation path preserves deterministic safety constraints.
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
