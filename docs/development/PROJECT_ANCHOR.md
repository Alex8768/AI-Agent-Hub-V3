# Project Anchor

## Active Anchor

A2.88 - Write Confirm TTL Cleanup + Observability Metrics

### Goal

Add deterministic TTL cleanup lifecycle and runtime observability metrics for write-confirm
state so long-running environments stay stable and easier to diagnose.

### Why Now

A2.87 made write confirm-flow durable; the next bottleneck is lifecycle hygiene
(expired-state cleanup) and transparent operational metrics for runtime decisions.

### Architecture Position

Target A2.88 boundaries:

- **TTL cleanup lifecycle**
  - evict expired pending confirmations and idempotency records deterministically,
  - keep cleanup safe under best-effort storage availability.

- **Runtime observability metrics**
  - expose cleanup and state-size counters to `act_runtime` diagnostics,
  - keep reason-code behavior stable and machine-consumable.

- **Continuity and guardrails**
  - preserve existing endpoint shape and write-confirm contract semantics,
  - maintain one-patch-one-reason execution discipline.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory lifecycle/observability touchpoints:
  pending/idempotency expiry semantics, cleanup trigger points,
  diagnostics surfaces, and runtime contract dependencies,
- lock scope to cleanup + observability only (no new tool/action surface),
- define deterministic cleanup metric contract for diagnostics.

Patch 1 artifacts:
- runtime boundary inventory captured:
  - write-confirm pending expiry path,
  - idempotency expiry/index lifecycle path,
  - cleanup trigger integration path in act runtime,
  - diagnostics metric emission path,
- scope lock affirmed:
  - no ungated write execution path in A2.88,
  - no endpoint shape breakage,
  - no global refactor,
  - no opportunistic feature drift.

#### Patch 2 — TTL lifecycle state-store seam
- add deterministic cleanup lifecycle and expiry-aware store behavior.

Patch 2 artifacts:
- state-store seam extended with lifecycle and TTL behavior:
  - `src/services/answer/act_write_state_store.py`
- seam additions:
  - idempotency TTL metadata (`created_at`, `expires_at`)
  - idempotency index registry for cleanup traversal
  - expiry-aware load path for idempotency replay records
  - explicit cleanup API: `cleanup_expired_write_state`
- seam observability metrics contract introduced:
  - `pending_expired`
  - `idempotency_expired`
  - `idempotency_index_size`
- seam coverage expanded:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - expiry and cleanup metric scenarios
- focused checks green:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - `tests/unit/services/answer/test_answer_response_presenter.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `121 passed`

#### Patch 3 — Runtime cleanup + observability wiring
- invoke cleanup lifecycle in act runtime and expose deterministic store metrics.

Patch 3 artifacts:
- Act runtime now invokes cleanup lifecycle before write-confirm policy evaluation:
  - `src/services/answer/act_read_only.py`
  - `act_write_state_store.cleanup_expired_write_state(...)`
- cleanup metrics wired into write-confirm diagnostics payload:
  - `act_runtime.store_stats.pending_expired`
  - `act_runtime.store_stats.idempotency_expired`
  - `act_runtime.store_stats.idempotency_index_size`
- observability behavior remains contract-safe:
  - no endpoint shape breakage
  - existing reason-code pathways preserved
- focused checks green:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - `tests/unit/services/answer/test_answer_response_presenter.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `121 passed`

#### Patch 4 — Continuity tests for cleanup and metrics
- expand unit coverage for expiry and diagnostics metric continuity.

Patch 4 artifacts:
- pending

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.88.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — TTL lifecycle state-store seam
- [x] Patch 3 — runtime cleanup + observability wiring
- [ ] Patch 4 — continuity tests for cleanup and metrics
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.88:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.88 is complete when:

- pending/idempotency cleanup lifecycle is deterministic and tested,
- runtime diagnostics expose actionable cleanup/state metrics,
- write-confirm behavior remains contract-safe with no endpoint shape regression,
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

TBD - Post-A2.88 planning

## Anchor Closed

A2.87 complete - durable approval state persistence hardening closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
