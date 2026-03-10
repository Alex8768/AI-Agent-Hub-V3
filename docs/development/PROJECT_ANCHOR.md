# Project Anchor

## Active Anchor

A2.47 — Debt Resolution Track (Runtime Clarity + Reliability)

### Goal

Resolve post-A2.46 technical debt with strict runtime parity and zero capability expansion.

This anchor closes explicitly tracked debt around:

- `AnswerService` orchestration overpacking
- cross-store memory consistency strategy
- runtime entrypoint ambiguity (`run_utf8.py`)
- dependency gate coverage continuity

The objective is to reduce operational and architectural risk while preserving behavior.

### Why Now

A2.46 stabilized topology and dependency directions.

The next risk concentration is unresolved debt with known owners and accepted deferrals:

- `TD-A2.45-001`
- `TD-A2.45-003`
- `TD-A2.45-004`

Closing these items improves maintainability and production safety without adding new
intelligence surfaces.

### Architecture Position

Primary debt closure zones:

- `services/answer` (orchestration decomposition seams)
- `layers/pro` + memory integration boundaries (consistency strategy contract)
- runtime entrypoint docs/policy (`src.api.main:app` vs legacy runner)
- platform quality gates and debt registry alignment

A2.47 preserves the A2.46 topology and dependency constraints.

### Patch Plan

#### Patch plan
- Patch 1 — debt closure inventory + scope lock
- Patch 2 — AnswerService orchestration extraction seam
- Patch 3 — memory consistency strategy contract (outbox/compensation decision)
- Patch 4 — runtime entrypoint cleanup decision (`run_utf8.py`)
- Patch 5 — debt registry/docs/CI closure for A2.47

### Progress

- [x] Patch 1 — debt closure inventory + scope lock
- [x] Patch 2 — AnswerService orchestration extraction seam
- [x] Patch 3 — memory consistency strategy contract (outbox/compensation decision)
- [ ] Patch 4 — runtime entrypoint cleanup decision (`run_utf8.py`)
- [ ] Patch 5 — debt registry/docs/CI closure for A2.47

### Patch 1 Outputs

Debt inventory mapped to A2.47:

- `TD-A2.45-001`: `AnswerService` remains oversized and couples many orchestration concerns.
- `TD-A2.45-003`: memory writes are cross-store best-effort and need explicit strategy.
- `TD-A2.45-004`: `run_utf8.py` legacy path needs keep/remove decision.

Scope lock:

- preserve runtime behavior and diagnostics contracts unless patch explicitly states otherwise
- no net-new model/provider/intelligence capabilities
- keep dependency gates from A2.46 active while debt is extracted

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

A2.47 completion criteria:
- targeted debt items (`TD-A2.45-001/003/004`) have explicit closure outcomes;
- `AnswerService` orchestration boundaries are clearer with preserved runtime parity;
- memory consistency strategy is documented/contracted and test-covered;
- runtime entrypoint ambiguity is resolved and documented;
- docs/checklist/status/features and CI quality gates reflect actual closure state.

## Next Anchor

A2.48 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.46 — Kernel / Extensions / Execution Plane Hardening

Completed via patches:
- Patch 1 — architecture zoning inventory + scope lock
- Patch 2 — kernel boundary formalization
- Patch 3 — governance subcore extraction
- Patch 4 — execution request boundary + execution plane isolation
- Patch 5 — dependency quality gates + docs closure
