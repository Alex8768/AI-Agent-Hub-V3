# Project Anchor

## Active Anchor

A2.50 — Planner Residual Decoupling (Composition Boundary Closure)

### Goal

Finalize residual planner/composition decoupling so planner callers and internals
share a strict composition boundary, while preserving runtime parity.

This anchor targets residual debt:

- normalized composition boundary contract (`CompositionRequest -> CompositionResolution`)
- extraction of composition resolution from planner internals to dedicated adapter/resolver
- deterministic dependency/parity/fallback guardrails for planner/composition boundary

### Why Now

`A2.48` decoupled planner callers, but planner internals still own composition
assembly details (registry lookup, graph build/validate, fallback decisioning).

Residual cleanup is required to fully close planner/composition coupling debt.

### Architecture Position

Primary closure zones:

- `layers/pro/reasoning/planner` boundary contract + planner consumption path
- dedicated composition resolver/adapter seam
- dependency and parity guardrails for deterministic fallback behavior

A2.50 preserves A2.46-A2.49 constraints and decisions, with no behavior expansion.

### Patch Plan

#### Patch plan
- Patch 1 — composition boundary contract + scope lock
- Patch 2 — composition resolver/adapter extraction
- Patch 3 — dependency/parity/fallback guardrails

### Progress

- [x] Patch 1 — composition boundary contract + scope lock
- [x] Patch 2 — composition resolver/adapter extraction
- [x] Patch 3 — dependency/parity/fallback guardrails

### Patch 1 Outputs

Residual debt mapped to A2.50:

- planner imports registry/builder/validator directly;
- planner still owns composition fallback decision path.

Scope lock:

- preserve runtime behavior, outputs, and diagnostics contracts
- no net-new model/provider/intelligence capabilities
- no policy-threshold changes
- one patch = one reason; no opportunistic refactors

### Out of Scope

Do NOT modify during A2.50:
- new model/provider integrations
- net-new intelligence capabilities
- OCR redesign
- major retrieval redesign
- UI feature expansion beyond topology/documentation scope
- new MCP ecosystem features
- new enterprise rollout capabilities beyond topology support

### Definition of Done

A2.50 completion criteria:
- planner consumes normalized `CompositionResolution` only;
- composition resolution logic is extracted from planner internals;
- dependency/parity/fallback guardrails are test-backed and deterministic.

## Next Anchor

A2.51 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.50 — Planner Residual Decoupling (Composition Boundary Closure)

Completed via patches:
- Patch 1 — composition boundary contract + scope lock
- Patch 2 — composition resolver/adapter extraction
- Patch 3 — dependency/parity/fallback guardrails
