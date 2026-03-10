# Project Anchor

## Active Anchor

A2.40 — Intent-based Planning Engine (LLM Planner)

### Goal

Introduce an LLM-driven intent planning layer while preserving deterministic
planning guards and safe-mode execution boundaries.

### Architecture Position

Planned modules:

- planner contract baseline for LLM intent planning
- llm planner adapter wiring with deterministic fallback
- planning policy invariants and safety guards
- diagnostics parity for planner decisions
- docs + CI quality-gate closure

### Patch Plan

#### Patch plan
- Patch 1 — LLM Planner Contract Baseline
- Patch 2 — Planner Adapter + Deterministic Fallback
- Patch 3 — Planner Policy Guardrails
- Patch 4 — Runtime Wiring + Diagnostics Parity
- Patch 5 — Docs/CI Closure

### Progress

- [x] Patch 1 — LLM Planner Contract Baseline
- [ ] Patch 2 — Planner Adapter + Deterministic Fallback
- [ ] Patch 3 — Planner Policy Guardrails
- [ ] Patch 4 — Runtime Wiring + Diagnostics Parity
- [ ] Patch 5 — Docs/CI Closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.40 completion criteria:
- LLM planner decisions remain policy-guarded and deterministic where required.
- fallback path preserves current safe-mode behavior when planner is unavailable.
- full unit suite and quality-gate coverage remain green.

## Next Anchor

A2.41 — Dynamic Tool Selection (MCP-aware)

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.39 — Controlled Execution Pilot (Strict Safe Mode+)

Completed via patches:
- Patch 1 — Execution Pilot Contract Baseline
- Patch 2 — Allowlist + Policy Gate
- Patch 3 — Receipt + Rollback Contract Enforcement
- Patch 4 — Pilot Runtime Wiring
- Patch 5 — Docs/CI Closure
