# Project Anchor

## Active Anchor

A2.42 — Learning from Feedback (Approve/Cancel/Edit)

### Goal

Introduce a deterministic feedback-learning baseline that captures
approve/cancel/edit signals and improves plan/action relevance diagnostics.

### Architecture Position

Planned modules:

- feedback-learning contract baseline
- feedback capture adapter + deterministic normalization
- feedback policy guardrails
- runtime wiring + diagnostics parity
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — Feedback Contract Baseline
- Patch 2 — Feedback Capture Adapter + Deterministic Normalization
- Patch 3 — Feedback Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Feedback Contract Baseline
- [ ] Patch 2 — Feedback Capture Adapter + Deterministic Normalization
- [ ] Patch 3 — Feedback Policy Guardrails
- [ ] Patch 4 — Runtime Wiring + Diagnostics Parity
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.42 completion criteria:
- feedback capture remains deterministic, explainable, and policy-guarded.
- approve/cancel/edit signals are reflected in planning diagnostics contracts.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.43 — TBD (post-feedback planning)

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.41 — Dynamic Tool Selection (MCP-aware)

Completed via patches:
- Patch 1 — Tool Selection Contract Baseline
- Patch 2 — MCP-aware Selector Adapter + Fallback
- Patch 3 — Tool Selection Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure
