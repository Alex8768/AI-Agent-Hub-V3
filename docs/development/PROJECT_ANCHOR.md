# Project Anchor

## Active Anchor

A2.44 — Assistant Conversational Recovery (Low-Evidence UX)

### Goal

Prevent assistant-mode generic "I don't know"/template outputs for low-evidence
conversational queries while preserving strict safety for source-grounded flows.

### Architecture Position

Planned modules:

- conversational recovery contract baseline
- low-evidence non-greeting recovery adapter
- recovery policy guardrails
- runtime wiring + diagnostics parity
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — Conversational Recovery Baseline + Runtime Hook
- Patch 2 — Language-Native Recovery Adapter Hardening
- Patch 3 — Recovery Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — Conversational Recovery Baseline + Runtime Hook
- [x] Patch 2 — Language-Native Recovery Adapter Hardening
- [x] Patch 3 — Recovery Policy Guardrails
- [ ] Patch 4 — Runtime Wiring + Diagnostics Parity
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.44 completion criteria:
- low-evidence conversational queries avoid generic "I don't know" output.
- source-grounded/factual safety gates remain intact and deterministic.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.45 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.43 — Feedback-to-Planning Adaptation (MVP)

Completed via patches:
- Patch 1 — Adaptation Contract Baseline
- Patch 2 — Signal-to-Plan Adapter + Deterministic Ranking
- Patch 3 — Adaptation Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure
