# Project Anchor

## Active Anchor

A2.30 — Coverage Enforcement in Release Gate

### Goal

Introduce explicit coverage-threshold policy in enterprise release gates.

### Architecture Position

Planned modules:

`src/layers/pro/reasoning/enterprise/`
`tests/unit/layers/pro/`

Planned files:
- `src/layers/pro/reasoning/enterprise/release_gate_model.py`
- `src/layers/pro/reasoning/enterprise/release_gate_aggregator.py`
- `src/layers/pro/reasoning/enterprise/release_gate_decision.py`

### Patch Plan

#### Patch 1 — Coverage threshold policy contract
- Add `minimum_coverage_ratio` policy field and enforce it in release-gate decision path.

#### Patch 2 — Coverage diagnostics source hardening
- Normalize coverage inputs from diagnostics and ensure deterministic fallback behavior.

#### Patch 3 — Coverage quality-gate tests
- Add deterministic contract tests for missing/below/meeting coverage threshold.

#### Patch 4 — CI/report alignment for coverage policy
- Extend release-gate CI/report wiring with coverage field propagation.

#### Patch 5 — Docs and roadmap sync
- Finalize anchor docs/checklist/status and capture rollout guidance.

### Progress

- [x] Patch 1 — Coverage threshold policy contract
- [x] Patch 2 — Coverage diagnostics source hardening
- [ ] Patch 3 — Coverage quality-gate tests
- [ ] Patch 4 — CI/report alignment for coverage policy
- [ ] Patch 5 — Docs and roadmap sync

### Out of Scope

Do NOT modify during A2.30:
- search endpoint behavior and contracts
- OCR pipeline
- UI scope
- unrelated reasoning modules outside release-gate path

### Definition of Done

A2.30 is complete when:
- coverage threshold policy is explicit and normalized
- missing/below coverage is fail-safe in release-gate decisions
- coverage enforcement is covered by deterministic tests
- CI release-gate path is aligned with new policy

## Next Anchor

TBD — Post-A2.30 planning

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.29 — Service Contract Boundary Cleanup (Search)

Completed via patches:
- Patch 1 — Introduce service-neutral search contracts
- Patch 2 — API/service mapping hardening
- Patch 3 — Search endpoint contract quality gate
- Patch 4 — Cleanup and migration safety
- Patch 5 — Docs + CI policy alignment
