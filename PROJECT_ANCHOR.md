# Project Anchor

## Active Anchor

A2.31 — CI Workflow Consolidation & Required Checks Matrix

### Goal

Consolidate required-check logic behind a deterministic matrix contract used as a
single source for CI policy convergence.

### Architecture Position

Planned modules:

- `src/layers/pro/reasoning/enterprise/required_checks_matrix.py`
- `src/layers/pro/reasoning/enterprise/required_checks_normalizer.py`

Planned files:
- `src/layers/pro/reasoning/enterprise/required_checks_matrix.py`
- `tests/unit/layers/pro/test_reasoning_enterprise_required_checks_matrix.py`
- `src/layers/pro/reasoning/enterprise/required_checks_normalizer.py`
- `tests/unit/layers/pro/test_reasoning_enterprise_required_checks_normalizer.py`

### Patch Plan

#### Patch plan
- Patch 1 — Required checks matrix contract + deterministic assembly test
- Patch 2 — Normalize required checks inputs from CI workflow sources
- Patch 3 — Consolidation rules deterministic quality tests
- Patch 4 — Wire consolidated matrix into CI workflow
- Patch 5 — Docs and policy alignment closure

### Progress

- [x] Patch 1 — Required checks matrix contract + deterministic assembly test
- [x] Patch 2 — Normalize required checks inputs from CI workflow sources
- [ ] Patch 3 — Consolidation rules deterministic quality tests
- [ ] Patch 4 — Wire consolidated matrix into CI workflow
- [ ] Patch 5 — Docs and policy alignment closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.31 is complete when:
- required-checks matrix is the deterministic source of truth
- CI workflows consume consolidated policy without drift
- quality gates validate policy assembly and consolidation behavior

## Next Anchor

A2.32 — Docs Topology Cleanup (root -> docs/architecture + docs/development)

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.30 — Coverage Enforcement in Release Gate

Completed via patches:
- Patch 1 — Coverage threshold policy contract
- Patch 2 — Coverage diagnostics source hardening
- Patch 3 — Coverage quality-gate tests
- Patch 4 — CI/report alignment for coverage policy
- Patch 5 — Docs and roadmap sync
