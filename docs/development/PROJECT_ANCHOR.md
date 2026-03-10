# Project Anchor

## Active Anchor

A2.34 — Digital COO Runtime (Assistant + Draft Actions)

### Goal

Evolve reasoning runtime into a user-facing assistant that can produce
reviewable draft actions, proactive suggestions, and language-native responses.

### Architecture Position

Planned modules:

- `src/core/*`
- `src/layers/pro/reasoning/*`
- `src/services/answer/*`
- `docs/development/*`
- `docs/architecture/*`

Planned files:
- assistant contracts/flags/diagnostics surfaces
- answer runtime orchestration and quality gates

### Patch Plan

#### Patch plan
- Patch 1 — Assistant mode contracts, flags, and diagnostics baseline
- Patch 2 — Language-native assistant fallback behavior
- Patch 3 — Proactive suggestion ranking MVP
- Patch 4 — Draft action runtime (review-before-execute)
- Patch 5 — Docs/CI closure for assistant runtime

### Progress

- [x] Patch 1 — Assistant mode contracts, flags, and diagnostics baseline
- [x] Patch 2 — Language-native assistant fallback behavior
- [ ] Patch 3 — Proactive suggestion ranking MVP
- [ ] Patch 4 — Draft action runtime (review-before-execute)
- [ ] Patch 5 — Docs/CI closure for assistant runtime

### Out of Scope

Do NOT modify during planning:
- existing stable contracts without explicit patch scope
- unrelated subsystems outside next selected anchor

### Definition of Done

A2.34 is complete when:
- assistant-mode contracts and feature flags are stable and default-off
- language-native fallback behavior is deterministic and test-covered
- proactive suggestions and draft actions are reviewable before execution
- docs and CI quality gates protect assistant runtime behavior

## Next Anchor

A2.35 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.33 — API Docs & Feature-Flag Alignment

Completed via patches:
- Patch 1 — Audit API docs vs runtime contracts
- Patch 2 — Update API docs for request/response parity
- Patch 3 — Align feature-flag docs with default behavior
- Patch 4 — Add deterministic API docs quality gate
- Patch 5 — Docs closure and roadmap sync
