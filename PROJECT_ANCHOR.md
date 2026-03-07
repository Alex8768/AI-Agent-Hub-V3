# Project Anchor

## Active Anchor

A2.5 — Verify Node Hardening

### Goal

Add a deterministic verify step to reasoning flow without broad refactors.

A2.5 must strengthen claim/evidence validation and expose predictable verify diagnostics.

### Patch Plan

#### Patch 0 — Verify contract preflight
- Define minimal verify diagnostics schema
- Keep behaviour additive and warning-only at start
- Validate planner/fallback parity for verify diagnostics

### Out of Scope

Do NOT modify during A2.5:
- AnswerService decomposition
- OpenAIAdapter decomposition
- config.py architecture cleanup
- IngestService slimming
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need

### Definition of Done

A2.5 is complete when:
- verify diagnostics are deterministic and externally stable
- verify policy behaviour is covered by tests
- planner/fallback verify parity is validated
