# Project Anchor

## Active Anchor

A2.33 — API Docs & Feature-Flag Alignment

### Goal

Align API documentation with actual feature-flag behavior and contract defaults.

### Architecture Position

Planned modules:

- `docs/architecture/*`
- `docs/development/*`

Planned files:
- `docs/api/*`
- feature-flag docs references in developer docs

### Patch Plan

#### Patch plan
- Patch 1 — Audit API docs vs runtime contracts
- Patch 2 — Update API docs for request/response parity
- Patch 3 — Align feature-flag docs with default behavior
- Patch 4 — Add deterministic API docs quality gate
- Patch 5 — Docs closure and roadmap sync

### Progress

- [ ] Patch 1 — Audit API docs vs runtime contracts
- [ ] Patch 2 — Update API docs for request/response parity
- [ ] Patch 3 — Align feature-flag docs with default behavior
- [ ] Patch 4 — Add deterministic API docs quality gate
- [ ] Patch 5 — Docs closure and roadmap sync

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.33 is complete when:
- API docs match delivery contracts
- feature-flag docs match runtime defaults
- docs quality gate protects against contract drift

## Next Anchor

A2.34 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.32 — Docs Topology Cleanup (root -> docs/architecture + docs/development)

Completed via patches:
- Patch 1 — Docs topology map and compatibility policy
- Patch 2 — Roadmap docs moved to canonical topology with root stubs
- Patch 3 — References/workflow aligned to canonical docs paths
- Patch 4 — Deterministic docs topology quality gate and CI wiring
- Patch 5 — Final docs policy sync and root compatibility stubs removal
