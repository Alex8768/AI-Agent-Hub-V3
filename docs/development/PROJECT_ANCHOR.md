# Project Anchor

## Active Anchor

A2.90 - UI Reliability and Product UX Baseline

### Goal

Stabilize frontend UX for everyday users: restore predictable rendering, add first-class
theme support (light/dark/system), introduce auto locale baseline, and keep runtime
transparency features understandable instead of noisy.

### Why Now

Core runtime hardening (A2.84-A2.89) is complete, but user-visible quality is now the
bottleneck. Current chat styling is still technical/raw and not product-grade for broad
audience usage, so UI reliability and ergonomics must be upgraded next.

### Architecture Position

Target A2.90 boundaries:

- **UI runtime reliability**
  - remove brittle/hardcoded palette hotspots that cause inconsistent visuals,
  - keep chat/layout behavior deterministic under panel collapse/resize.

- **Theme system baseline**
  - support `light`, `dark`, and `system` modes with persisted preference,
  - use graphite-toned dark palette (not near-black) and readable light palette.

- **Locale baseline**
  - auto-detect UI language from browser/system preference (initially `en`/`ru`),
  - keep copy centralized via a minimal translation seam.

- **UX continuity**
  - preserve existing diagnostics/runtime transparency while simplifying wording and noise density.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory current UX liabilities in chat/layout/theme/locale touchpoints,
- lock scope to reliability + UX baseline only (no Evolution loop work in A2.90),
- define deterministic acceptance checks for theme/locale/runtime-info continuity.

Patch 1 artifacts:
- frontend boundaries mapped:
  - chat surface copy and controls,
  - palette/token usage and hardcoded color hotspots,
  - app-level preference persistence points,
  - runtime diagnostics display zones,
- scope lock affirmed:
  - no backend contract changes,
  - no MCP/tooling behavior changes,
  - no unrelated architecture refactor.

#### Patch 2 — Theme + locale preference seam
- add app-level UI preference seam with persisted `theme_mode` and resolved locale.

Patch 2 artifacts:
- new preference seam in frontend:
  - theme mode resolver (`light`/`dark`/`system`),
  - locale resolver (`en`/`ru`, system-first),
  - localStorage persistence helpers.
- seam wiring in:
  - `frontend/src/App.tsx`
  - `frontend/src/index.css`
  - `frontend/src/lib/uiPreferences.ts`
- focused frontend check green:
  - `frontend: npm run build`
  - result: success

#### Patch 3 — Chat/layout UX refresh
- apply product-style visual cleanup to chat and shell surfaces.

Patch 3 artifacts:
- refresh for:
  - `frontend/src/components/ChatPanel.css`
  - `frontend/src/App.css`
- outcomes:
  - improved readability/spacing hierarchy,
  - less harsh borders and better visual affordances,
  - stable behavior under side-panel collapse/expand.
- focused frontend check green:
  - `frontend: npm run build`
  - result: success

#### Patch 4 — Runtime transparency UX simplification
- keep diagnostics transparency while reducing cognitive overload.

Patch 4 artifacts:
- simplify labels and badge wording in:
  - `frontend/src/components/ChatPanel.tsx`
  - related style tokens/classes.
- preserve existing action controls:
  - write approve/cancel flow remains explicit and deterministic.
- focused frontend check green:
  - `frontend: npm run build`
  - result: success

#### Patch 5 — Guardrails + parity + closure
- run frontend lint/build + backend regression parity checks, sync mandatory docs, close A2.90.

Patch 5 artifacts:
- focused closure checks green:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - `tests/unit/services/answer/test_answer_response_presenter.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `127 passed`
- full-suite parity check green:
  - `uv run pytest`
  - result: `602 passed, 3 skipped`
- frontend closure build check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.90 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — theme + locale preference seam
- [x] Patch 3 — chat/layout UX refresh
- [x] Patch 4 — runtime transparency UX simplification
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.90:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.90 is complete when:

- UI renders reliably with no blank/unstyled main surfaces in standard flows,
- theme modes (`light`/`dark`/`system`) are functional and persisted,
- locale auto-selection baseline is in place for core UI copy,
- runtime transparency remains available without overwhelming default UX,
- focused and full quality checks remain green,
- mandatory docs are synchronized.

## A2.87 Snapshot (Closed)

A2.87 closure markers retained for continuity:

- durable state seam for write-confirm pending/idempotency records,
- restart-resilient runtime wiring to memory-store state,
- continuity coverage for pending restore after cache reset,
- full-suite parity: `594 passed, 3 skipped`.

## A2.56 Operational Guardrails Snapshot (Closed)

A2.56 policy markers are retained for deterministic docs quality gates:

- `healthy_request_kpi`
- `fallback_rate_kpi`
- `soft_failure_rate_kpi`
- `requests_with_soft_failures`
- `requests_with_fallback`
- `response_mode == "assistant_fallback"`
- `planning_reason_codes`
- `soft_failures_count`
- `fallback_count`
- `warning`
- `critical`

## Next Anchor

TBD - Post-A2.90 planning

## Anchor Closed

A2.89 complete - confirm-flow quota and rate guardrails closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
