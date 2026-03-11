# Project Anchor

## Active Anchor

A2.54 — Diagnostics Contract Guardrails (Closed)

### Goal

Strengthen deterministic diagnostics contract guardrails for answer-path runtime so
regressions in diagnostics shape/reason-codes/counters are caught early without changing API behavior.

The intent of this anchor is quality-gate and contract safety focused:
- preserve runtime/API parity,
- enforce diagnostics snapshot contract stability,
- enforce exception-policy contract coverage via deterministic tests.

### Why Now

A2.53 closed exception-policy hardening and removed scoped silent handlers in answer-path runtime.

Now the main residual risk is silent drift of diagnostics schema/fields/reason-code policies
without immediate failure signals.

A2.54 focuses on guardrail depth so future refactors keep diagnostics contracts stable.

### Architecture Position

Target A2.54 boundaries:

- **Diagnostics Contract Snapshot Surface**
  - answer/debug diagnostics top-level key set invariants
  - soft-failure reason-code presence invariants in failure paths
  - deterministic counter/flag invariants for fallback paths

- **Exception Policy Guardrails**
  - scoped no-silent-swallow policy remains enforced
  - critical-stage exception behavior remains explicit

- **Quality Gates**
  - stronger diagnostics snapshot and contract assertions
  - parity gate to ensure no user-facing behavior regression

### Patch Plan

#### Patch 1 — Inventory + scope lock
- Build explicit inventory of diagnostics contract surfaces already relied upon by tests/docs.
- Classify current guardrails into:
  - shape (snapshot keys),
  - policy (reason-codes/flags),
  - parity (answer/debug behavior).
- Define no-regression constraints and forbidden drift scope.

#### Patch 2 — Diagnostics snapshot contract expansion
- Add/expand stable snapshot assertions for diagnostics schema in answer-path tests.
- Preserve runtime outputs and avoid business-logic changes.

#### Patch 3 — Soft-failure policy guardrail coverage expansion
- Add targeted tests asserting reason-code/counter visibility for fallback paths.
- Keep all changes test/guardrail-centric.

#### Patch 4 — Exception policy enforcement hardening
- Strengthen AST/static guardrails for scoped modules and policy constraints.
- Ensure deterministic failure messages for CI triage.

#### Patch 5 — Guardrails + parity + closure
- Run full diagnostics/parity guardrail suite and finalize closure checks.
- Run parity-focused tests and full suite.
- Close docs/checklist/status/features sync for A2.54.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — diagnostics snapshot contract expansion
- [x] Patch 3 — soft-failure policy guardrail coverage expansion
- [x] Patch 4 — exception policy enforcement hardening
- [x] Patch 5 — guardrails + parity + closure

### Non-Negotiable Rules

- No net-new intelligence features during A2.54
- Preserve answer/debug output parity
- No diagnostics contract drift without explicit guardrail updates
- No weakening of exception-policy scope gates
- One patch = one reason

### Out of Scope

Do NOT modify during A2.54:

- planner/kernel topology
- new tool safety capabilities
- new multi-agent capabilities
- OCR redesign
- MCP ecosystem expansion
- UI feature expansion unrelated to answer-path structure
- product/marketing README work

### Definition of Done

A2.54 is complete when:

- diagnostics contract surfaces are covered by deterministic guardrails
- soft-failure policy visibility is test-covered
- answer/debug output parity is preserved
- quality gates enforce scoped exception policy and diagnostics schema stability

## Next Anchor

TBD — Post-A2.54 planning

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
