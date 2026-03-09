# Project Anchor

## Active Anchor

A2.28 — Interface Foundation (MVP)

### Goal

Establish a first-party interface foundation with a stable app shell and typed API
contracts for core backend journeys.

### Architecture Position

Planned modules:

`frontend/src/contracts/`
`frontend/src/lib/`
`frontend/src/`

Planned files:
- `frontend/src/contracts/api.ts`
- `frontend/src/lib/apiClient.ts`
- `frontend/src/App.tsx`

### Patch Plan

#### Patch 1 — UI shell + API contracts baseline
- Add frontend app shell scaffold and typed API contract/client foundation.

#### Patch 2 — Documents + search journey wiring
- Add basic document and search screens wired to backend endpoints.

#### Patch 3 — Answer + diagnostics journey wiring
- Add answer workflow UI with diagnostics panel baseline.

#### Patch 4 — Session/workspace UX hardening
- Add state persistence, loading/error states, and navigation hardening.

#### Patch 5 — UI quality gate
- Add deterministic UI contract/smoke checks and release wiring for interface flow.

### Progress

- [x] Patch 1 — UI shell + API contracts baseline
- [x] Patch 2 — Documents + search journey wiring
- [ ] Patch 3 — Answer + diagnostics journey wiring
- [ ] Patch 4 — Session/workspace UX hardening
- [ ] Patch 5 — UI quality gate

### Out of Scope

Do NOT modify during A2.28:
- Retrieval redesign
- OCR pipeline
- Config architecture
- major reasoning graph redesign

### Definition of Done

A2.28 is complete when:
- first-party interface shell is available
- core document/search/answer user journeys are wired
- diagnostics visibility is available in UI
- UI quality gates validate contract and smoke path behavior

## Next Anchor

TBD — Post-A2.28 planning

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.27 — Architecture & Readiness Audit

Completed via patches:
- Patch 1 — architecture/readiness baseline snapshot
- Patch 2 — component dependency and boundary review
- Patch 3 — operational readiness review
- Patch 4 — product readiness review
- Patch 5 — consolidated audit report with A2.28 priority proposal
