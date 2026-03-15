# Project Anchor

## Active Anchor

A2.87 - Durable Approval State Persistence Hardening

### Goal

Harden write-confirm runtime by persisting approval/idempotency state in durable memory
store so confirmation flow survives process restarts and remains deterministic.

### Why Now

A2.86 introduced controlled write execution and UI approvals, but pending/idempotency
state still relied on process memory fallback paths that can be lost on restart.

### Architecture Position

Target A2.87 boundaries:

- **Durable state persistence seam**
  - isolate write-confirm pending/idempotency state access behind a dedicated store seam,
  - persist and reload state via memory store with safe in-process fallback.

- **Confirm-flow restart resilience**
  - preserve pending confirmations and idempotency replay after process restart,
  - keep token validation semantics deterministic.

- **Diagnostics continuity**
  - preserve existing runtime reason-code transparency contract,
  - expose deterministic durable-state load/save behavior through tests.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory write-confirm state touchpoints:
  pending confirmation record lifecycle, idempotency replay record lifecycle,
  memory-store integration points, and fallback behavior boundaries,
- lock scope to durable-state hardening only (no net-new write tool expansion),
- define deterministic persistence contract for load/save/replay semantics.

Patch 1 artifacts:
- runtime boundary inventory captured:
  - write-confirm pending record read/write path,
  - idempotency replay record read/write path,
  - memory-store best-effort integration and fallback path,
  - runtime diagnostics contract continuity path,
- scope lock affirmed:
  - no ungated write execution path in A2.87,
  - no endpoint shape breakage,
  - no global refactor,
  - no opportunistic feature drift.

#### Patch 2 — Durable write state store seam
- extract and wire durable pending/idempotency state store seam for write-confirm runtime.

Patch 2 artifacts:
- durable state store seam extracted to:
  - `src/services/answer/act_write_state_store.py`
- seam responsibilities:
  - scope/key normalization for pending/idempotency write-confirm records
  - memory-store read/write with JSON normalization
  - safe in-process fallback cache for unavailable memory-store operations
  - test reset helper for deterministic runtime tests
- seam coverage added:
  - `tests/unit/services/answer/test_act_write_state_store.py`
- focused checks green (seam + runtime regressions):
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - result: `73 passed`

#### Patch 3 — Restart-resilient confirm-flow runtime wiring
- adapt write-confirm runtime to load/save/consume durable state store records.

Patch 3 artifacts:
- pending

#### Patch 4 — Runtime diagnostics continuity + tests
- validate durable storage behavior and preserve diagnostic contract surfaces.

Patch 4 artifacts:
- pending

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.87.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — durable write state store seam
- [ ] Patch 3 — restart-resilient confirm-flow runtime wiring
- [ ] Patch 4 — runtime diagnostics continuity + tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.87.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.87:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.87 is complete when:

- pending/idempotency write-confirm state is persisted and reloadable from durable store,
- runtime behavior is restart-resilient without contract regressions,
- diagnostics and reason-code behavior remain stable,
- focused and full quality checks remain green,
- mandatory docs are synchronized.

## A2.86 Snapshot (Closed)

A2.86 closure markers retained for continuity:

- profile-aware write policy contract (`blocked` / `confirm_required` / `direct_allowed`),
- Act write confirm-flow runtime with token validation and idempotency replay,
- UI approve/cancel controls for pending write actions,
- full-suite parity: `591 passed, 3 skipped`.

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

TBD - Post-A2.87 planning

## Anchor Closed

A2.86 complete - controlled write actions via confirm-flow closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
