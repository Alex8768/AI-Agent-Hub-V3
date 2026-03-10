# Project Anchor

## Active Anchor

A2.48 — Planner Decoupling Track (Kernel Composition Independence)

### Goal

Close remaining planner-coupling debt by separating planner composition paths from
concrete provider/runtime assembly, while preserving strict runtime parity.

This anchor targets:

- planner runtime dependency decoupling
- prompt/planner boundary normalization
- deterministic planner diagnostics parity
- CI/documentation enforcement for planner boundary drift

### Why Now

A2.47 closed the major runtime/debt items and left one tracked architectural item:

- `TD-A2.45-002`

Planner behavior is guarded, but runtime composition is still more coupled than desired.
Decoupling this path is the next low-risk/high-value stabilization step.

### Architecture Position

Primary closure zones:

- `layers/pro/reasoning/kernel` planner-facing contracts
- `core/providers_parts` runtime composition seams
- `services/answer` planner adapter wiring (no behavior expansion)
- planner boundary quality-gate tests and docs

A2.48 preserves A2.46 topology constraints and A2.47 runtime decisions.

### Patch Plan

#### Patch plan
- Patch 1 — planner decoupling inventory + scope lock
- Patch 2 — planner composition seam extraction
- Patch 3 — prompt/planner boundary normalization
- Patch 4 — planner diagnostics/runtime parity guardrails
- Patch 5 — debt registry/docs/CI closure for A2.48

### Progress

- [x] Patch 1 — planner decoupling inventory + scope lock
- [x] Patch 2 — planner composition seam extraction
- [x] Patch 3 — prompt/planner boundary normalization
- [ ] Patch 4 — planner diagnostics/runtime parity guardrails
- [ ] Patch 5 — debt registry/docs/CI closure for A2.48

### Patch 1 Outputs

Debt inventory mapped to A2.48:

- `TD-A2.45-002`: planner wiring still depends on concrete runtime/provider composition paths.

Scope lock:

- preserve planner behavior, outputs, and diagnostics contracts
- no net-new model/provider/intelligence capabilities
- no planner quality-threshold policy changes
- keep topology/dependency gates from A2.46 and debt gates from A2.47 active

### Out of Scope

Do NOT modify during planning:
- new model/provider integrations
- net-new intelligence capabilities
- OCR redesign
- major retrieval redesign
- UI feature expansion beyond topology/documentation scope
- new MCP ecosystem features
- new enterprise rollout capabilities beyond topology support

### Definition of Done

A2.48 completion criteria:
- `TD-A2.45-002` has explicit closure outcome in debt registry;
- planner composition path is decoupled from concrete provider assembly seams;
- prompt/planner boundaries are normalized without behavior drift;
- planner diagnostics/runtime parity is preserved and test-covered;
- docs/checklist/status/features and CI quality gates reflect closure state.

## Next Anchor

A2.49 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.47 — Debt Resolution Track (Runtime Clarity + Reliability)

Completed via patches:
- Patch 1 — debt closure inventory + scope lock
- Patch 2 — AnswerService orchestration extraction seam
- Patch 3 — memory consistency strategy contract (outbox/compensation decision)
- Patch 4 — runtime entrypoint cleanup decision (`run_utf8.py`)
- Patch 5 — debt registry/docs/CI closure for A2.47
