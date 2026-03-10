# Project Anchor

## Active Anchor

A2.49 — Conversational Reliability Track (Human-Friendly Safe UX)

### Goal

Make assistant responses consistently human-friendly and conversationally reliable
while preserving existing safety, policy, and runtime contracts.

This anchor targets:

- response-style reliability under low evidence and fallback paths
- deterministic friendliness guardrails without policy drift
- diagnostics visibility for conversational quality decisions
- CI/documentation enforcement for conversational boundary drift

### Why Now

A2.48 closed planner-coupling debt and restored strict composition independence.
The next operational risk is user-facing interaction quality: answers can stay safe
but still feel too abrupt or non-human in constrained contexts.

This anchor keeps behavior safe while normalizing a friendlier, reliable interaction tone.

No net-new intelligence capability is introduced.

### Architecture Position

Primary closure zones:

- `services/answer` response-shaping seams and diagnostics handoff
- `layers/pro/reasoning` fallback/recovery conversational boundaries
- assistant runtime policy adapters (guarded, deterministic)
- docs + quality gates for conversational reliability contracts

A2.49 preserves A2.46 topology constraints, A2.47 debt decisions, and A2.48 planner decoupling outcomes.

### Patch Plan

#### Patch plan
- Patch 1 — conversational reliability inventory + scope lock
- Patch 2 — response-style boundary seam extraction
- Patch 3 — low-evidence friendliness normalization
- Patch 4 — conversational diagnostics/runtime parity guardrails
- Patch 5 — docs/CI closure for A2.49

### Progress

- [x] Patch 1 — conversational reliability inventory + scope lock
- [x] Patch 2 — response-style boundary seam extraction
- [x] Patch 3 — low-evidence friendliness normalization
- [x] Patch 4 — conversational diagnostics/runtime parity guardrails
- [x] Patch 5 — docs/CI closure for A2.49

### Patch 1 Outputs

Conversational reliability inventory mapped to A2.49:

- low-evidence answer tone remains safe but can be too rigid in user-facing dialogue
- fallback responses need clearer friendly-presence baseline across contexts

Scope lock:

- preserve existing safety behavior, outputs, and diagnostics contracts
- no net-new model/provider/intelligence capabilities
- no quality-threshold policy changes for verify/self-check/release gates
- keep topology/dependency/debt gates from A2.46-A2.48 active

### Out of Scope

Do NOT modify during A2.49:
- new model/provider integrations
- net-new intelligence capabilities
- OCR redesign
- major retrieval redesign
- UI feature expansion beyond topology/documentation scope
- new MCP ecosystem features
- new enterprise rollout capabilities beyond topology support

### Definition of Done

A2.49 completion criteria:
- assistant response style stays human-friendly under constrained evidence paths;
- friendliness normalization remains policy-safe and deterministic;
- conversational diagnostics/runtime parity is preserved and test-covered;
- docs/checklist/status/features and CI quality gates reflect closure state.

## Next Anchor

A2.50 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.49 — Conversational Reliability Track (Human-Friendly Safe UX)

Completed via patches:
- Patch 1 — conversational reliability inventory + scope lock
- Patch 2 — response-style boundary seam extraction
- Patch 3 — low-evidence friendliness normalization
- Patch 4 — conversational diagnostics/runtime parity guardrails
- Patch 5 — docs/CI closure for A2.49
