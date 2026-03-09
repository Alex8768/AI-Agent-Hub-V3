# Project Anchor

## Active Anchor

A2.32 — Docs Topology Cleanup (root -> docs/architecture + docs/development)

### Goal

Move root-level operational docs into structured docs topology while preserving
workflow-safe compatibility.

### Architecture Position

Planned modules:

- `docs/architecture/*`
- `docs/development/*`

Planned files:
- `PROJECT_ANCHOR.md` (compatibility stub candidate)
- `STATUS.md` (compatibility stub candidate)
- `PROJECT_CHECKLIST.md` (compatibility stub candidate)
- `PLATFORM_FEATURES.md` (compatibility stub candidate)
- `docs/architecture/*` and `docs/development/*` target locations
- `docs/development/DOCS_TOPOLOGY_POLICY.md`
- `docs/development/PROJECT_ANCHOR.md`
- `docs/development/STATUS.md`
- `docs/development/PROJECT_CHECKLIST.md`
- `docs/architecture/PLATFORM_FEATURES.md`

### Patch Plan

#### Patch plan
- Patch 1 — Introduce docs topology map and compatibility policy
- Patch 2 — Move roadmap docs with root stubs
- Patch 3 — Update references and workflow docs to new paths
- Patch 4 — Add docs topology quality gate
- Patch 5 — Final docs policy alignment closure

### Progress

- [x] Patch 1 — Introduce docs topology map and compatibility policy
- [x] Patch 2 — Move roadmap docs with root stubs
- [ ] Patch 3 — Update references and workflow docs to new paths
- [ ] Patch 4 — Add docs topology quality gate
- [ ] Patch 5 — Final docs policy alignment closure

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.32 is complete when:
- root roadmap docs are moved under structured docs folders
- root compatibility stubs keep existing workflows stable
- references are aligned and protected by deterministic checks

## Next Anchor

A2.33 — API Docs & Feature-Flag Alignment

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.31 — CI Workflow Consolidation & Required Checks Matrix

Completed via patches:
- Patch 1 — Required checks matrix contract + deterministic assembly test
- Patch 2 — Normalize required checks inputs from CI workflow sources
- Patch 3 — Consolidation rules deterministic quality tests
- Patch 4 — Wire consolidated matrix into CI workflow
- Patch 5 — Docs and policy alignment closure
