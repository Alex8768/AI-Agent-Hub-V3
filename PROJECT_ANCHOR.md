# Project Anchor

## Active Anchor

A2.29 — Service Contract Boundary Cleanup (Search)

### Goal

Remove service-to-API schema coupling in search flow by introducing service-neutral
contracts and explicit API/service mapping boundaries.

### Architecture Position

Planned modules:

`src/services/search/`
`src/api/endpoints/`

Planned files:
- `src/services/search/contracts.py`
- `src/services/search/search_service.py`
- `src/api/endpoints/search.py`
- `src/api/endpoints/search_hybrid.py`

### Patch Plan

#### Patch 1 — Introduce service-neutral search contracts
- Add service-level request/response DTOs and switch `SearchService` to those contracts.

#### Patch 2 — API/service mapping hardening
- Add explicit endpoint mapping and preserve stable API response models.

#### Patch 3 — Search endpoint contract quality gate
- Add deterministic tests for boundary and contract parity.

#### Patch 4 — Cleanup and migration safety
- Remove leftover boundary leaks and keep compatibility across retrieval paths.

#### Patch 5 — Docs + CI policy alignment
- Align architecture docs/checklists and ensure CI coverage for the boundary rules.

### Progress

- [x] Patch 1 — Introduce service-neutral search contracts
- [x] Patch 2 — API/service mapping hardening
- [x] Patch 3 — Search endpoint contract quality gate
- [ ] Patch 4 — Cleanup and migration safety
- [ ] Patch 5 — Docs + CI policy alignment

### Out of Scope

Do NOT modify during A2.29:
- Retrieval algorithm behavior
- OCR pipeline
- Config architecture
- major reasoning graph redesign
- UI feature scope

### Definition of Done

A2.29 is complete when:
- `SearchService` no longer imports `src.api.schemas`
- API schemas remain stable for `/api/v1/search` and `/api/v1/search-hybrid`
- service-neutral contracts own search service boundary
- boundary quality gates are present and green

## Next Anchor

TBD — Post-A2.29 planning

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.28 — Interface Foundation (MVP)

Completed via patches:
- Patch 1 — UI shell + API contracts baseline
- Patch 2 — Documents + search journey wiring
- Patch 3 — Answer + diagnostics journey wiring
- Patch 4 — Session/workspace UX hardening
- Patch 5 — UI quality gate
