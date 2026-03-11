# Project Anchor

## Active Anchor

A2.53 — Answer-Path Exception Policy Hardening

### Goal

Eliminate remaining silent exception swallowing in answer-path runtime code and
standardize soft-failure diagnostics/logging policy without changing answer/debug behavior.

The intent of this anchor is reliability and observability focused:
- preserve runtime/API parity,
- remove silent failure paths (`except ...: pass`) from active answer runtime,
- enforce deterministic soft-failure reason-code propagation and warning logs.

### Why Now

A2.52 closed facade slimming and seam guardrails, but inventory still shows legacy
silent `except ...: pass` blocks in active answer-path modules.

These blocks reduce diagnosability and can hide degradations in production.

A2.53 focuses on exception-policy hardening with strict runtime parity.

### Architecture Position

Target A2.53 boundaries:

- **Answer Runtime Modules (`answer_service`, `orchestrator`)**
  - replace silent `except ...: pass` in active runtime paths
  - keep best-effort semantics where required, but always emit reason codes + warning logs
  - keep critical stages fail-fast with controlled exceptions

- **Soft-Failure Policy Contract**
  - reason-code naming consistency
  - diagnostics key policy consistency (`planning_reason_codes` and counters)
  - deterministic fallback visibility contract

- **Quality Gates**
  - AST/static gate for forbidden silent `except ...: pass` in scoped modules
  - parity gate to ensure no user-facing behavior regression

### Patch Plan

#### Patch 1 — Inventory + scope lock
- Build explicit inventory of remaining silent `except ...: pass` in answer-path runtime.
- Classify each site:
  - best-effort fallback (must log + reason-code),
  - critical stage (must not swallow exception).
- Define reason-code/logging policy and no-regression constraints.

#### Patch 2 — `orchestrator` silent-except removal
- Replace scoped silent handlers with structured warning logs + diagnostics reason-codes.
- Preserve existing runtime contracts and fallback outputs.

#### Patch 3 — `answer_service` silent-except removal (phase 1)
- Replace low-risk, best-effort silent handlers with policy-compliant soft-failure wiring.
- Keep answer/debug parity and avoid opportunistic refactors.

#### Patch 4 — `answer_service` silent-except removal (phase 2)
- Finish remaining scoped sites and normalize reason-code/counter behavior.
- Keep fallback behavior deterministic and observable.

#### Patch 5 — Guardrails + parity + closure
- Extend quality gates to enforce exception policy scope.
- Run parity-focused tests and full suite.
- Close docs/checklist/status/features sync for A2.53.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — `orchestrator` silent-except removal
- [x] Patch 3 — `answer_service` silent-except removal (phase 1)
- [x] Patch 4 — `answer_service` silent-except removal (phase 2)
- [ ] Patch 5 — guardrails + parity + closure

### Non-Negotiable Rules

- No net-new intelligence features during A2.53
- Preserve answer/debug output parity
- No silent `except ...: pass` in scoped active runtime modules after closure
- Critical stages must not swallow exceptions
- One patch = one reason

### Out of Scope

Do NOT modify during A2.53:

- planner/kernel topology
- new tool safety capabilities
- new multi-agent capabilities
- OCR redesign
- MCP ecosystem expansion
- UI feature expansion unrelated to answer-path structure
- product/marketing README work

### Definition of Done

A2.53 is complete when:

- remaining scoped silent exception sites are removed/replaced
- soft-failure policy is deterministic and test-covered
- answer/debug output parity is preserved
- quality gates enforce scoped exception policy

## Next Anchor

TBD — Post-A2.53 planning

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
