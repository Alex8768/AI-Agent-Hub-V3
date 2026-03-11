# Project Anchor

## Active Anchor

A2.55 — Documentation Consistency Cleanup

### Goal

Eliminate stale cross-document contradictions so planning/status artifacts remain a reliable
source of truth for active and completed work without changing runtime behavior.

The intent of this anchor is docs-consistency and operational clarity focused:
- align capability status across features/checklist/status/anchor docs,
- remove stale roadmap statements that conflict with completed anchors,
- preserve existing docs topology and runtime/API behavior.

### Why Now

A2.54 is closed and guardrails are green.

The main residual risk is documentation drift: stale capability states and roadmap text can
mislead anchor selection, progress tracking, and execution order.

A2.55 focuses on consistency closure before new technical anchors begin.

### Architecture Position

Target A2.55 boundaries:

- **Capability Status Consistency**
  - align completed capabilities with completed anchors
  - remove stale "planned/current" wording for already closed work
  - preserve intentional deferred items only

- **Roadmap Text Consistency**
  - remove outdated "current anchor" statements
  - keep roadmap ideas as future-facing only
  - ensure no contradiction with checklist/status

- **Quality Gates**
  - keep docs topology and docs quality gates green
  - preserve deterministic CI outcomes

### Patch Plan

#### Patch 1 — Inventory + scope lock
- Build explicit inventory of docs contradictions and stale states.
- Classify inconsistencies by type:
  - capability status drift,
  - roadmap/state wording drift,
  - anchor/checklist synchronization drift.
- Define no-regression constraints and allowed edit scope.

#### Patch 2 — Capability map consistency corrections
- Update capability/status statements in `PLATFORM_FEATURES.md` to match closed anchors.
- Keep changes wording-only (no scope expansion).

#### Patch 3 — Checklist/status/anchor synchronization
- Align `PROJECT_CHECKLIST.md`, `STATUS.md`, and `PROJECT_ANCHOR.md` on active/next state.
- Remove stale "current work" carry-over blocks when no longer active.

#### Patch 4 — Roadmap wording normalization
- Normalize roadmap clauses that conflict with completed milestones.
- Keep future-looking roadmap ideas intact and non-contradictory.

#### Patch 5 — Guardrails + parity + closure
- Run docs-focused and full-suite checks for closure.
- Finalize docs-sync and close A2.55.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — capability map consistency corrections
- [x] Patch 3 — checklist/status/anchor synchronization
- [ ] Patch 4 — roadmap wording normalization
- [ ] Patch 5 — guardrails + parity + closure

### Non-Negotiable Rules

- No net-new runtime features during A2.55
- Preserve docs topology policy
- Preserve runtime/API behavior (docs-only anchor)
- No opportunistic refactors beyond docs consistency scope
- One patch = one reason

### Out of Scope

Do NOT modify during A2.55:

- planner/kernel topology
- service runtime logic
- endpoint contracts
- non-doc production code
- unrelated UI or infra features

### Definition of Done

A2.55 is complete when:

- stale docs contradictions identified and resolved
- active/next anchor state is consistent across docs
- roadmap wording no longer conflicts with completed milestones
- docs and full-suite quality checks remain green

## Next Anchor

TBD — Post-A2.55 planning

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
