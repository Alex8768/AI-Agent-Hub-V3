# Project Anchor

## Active Anchor

A2.89 - Confirm-Flow Quota and Rate Guards

### Goal

Add deterministic quota and decision-rate guardrails for write confirm-flow so runtime
can reject abusive or bursty approval traffic with explicit reason-codes.

### Why Now

A2.88 stabilized TTL cleanup and observability metrics. The next reliability gap is
capacity control: pending confirmation churn, idempotency growth, and rapid approval
retries should be constrained before EvolutionAgent-era workloads increase pressure.

### Architecture Position

Target A2.89 boundaries:

- **Quota controls**
  - enforce pending confirmation quota per session scope,
  - enforce idempotency index capacity per session scope.

- **Decision-rate controls**
  - add deterministic approve/cancel rate window guard,
  - keep behavior durable under cache resets with memory-store fallback.

- **Runtime policy continuity**
  - preserve existing write-confirm contract and endpoint shape,
  - surface guard outcomes via stable `act_runtime.reason_codes`.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory quota/rate insertion points in write-confirm flow:
  pending issuance, approve/cancel decision path, idempotency persistence path,
- lock scope to quota/rate guards and diagnostics continuity only,
- define initial reason-code contract for quota/rate outcomes.

Patch 1 artifacts:
- runtime boundaries mapped:
  - pending confirmation issuance gate,
  - approval decision rate gate,
  - idempotency capacity gate,
  - diagnostics emission path,
- scope lock affirmed:
  - no new tool surface,
  - no endpoint shape breakage,
  - no unrelated runtime refactor.

#### Patch 2 — State-store quota/rate seam
- extend durable state seam with quota/rate evaluation helpers.

Patch 2 artifacts:
- state-store seam additions in:
  - `src/services/answer/act_write_state_store.py`
- new deterministic guard APIs:
  - pending quota evaluation,
  - idempotency quota evaluation,
  - approve/cancel decision rate evaluation with sliding window.
- seam coverage expanded in:
  - `tests/unit/services/answer/test_act_write_state_store.py`
- focused seam check green:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - result: `7 passed`

#### Patch 3 — Runtime guard wiring
- integrate quota/rate guard calls into write-confirm runtime transitions.

Patch 3 artifacts:
- runtime guard wiring in:
  - `src/services/answer/act_read_only.py`
- guard outcomes mapped to explicit reason-codes for blocked flows:
  - pending quota exceeded,
  - idempotency quota exceeded,
  - decision rate limited.
- diagnostics continuity preserved:
  - existing `act_runtime` structure retained,
  - `store_stats` continuity maintained.
- focused runtime check green:
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - result: `6 passed`

#### Patch 4 — Continuity and regression tests
- add runtime and seam tests for guard decisions and reason-code stability.

Patch 4 artifacts:
- coverage expanded in:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
- scenarios:
  - pending quota blocks second issuance in same scope,
  - idempotency quota blocks new replay-key persistence,
  - decision rate guard blocks burst approvals.
- focused regression checks green:
  - `tests/unit/services/answer/test_act_write_state_store.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - result: `16 passed`

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.89.

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
- mandatory docs synchronized for A2.89 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — state-store quota/rate seam
- [x] Patch 3 — runtime guard wiring
- [x] Patch 4 — continuity and regression tests
- [x] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.89:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.89 is complete when:

- pending/idempotency quota and decision-rate guards are deterministic and tested,
- runtime diagnostics expose explicit quota/rate reason-codes for blocked paths,
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

TBD - Post-A2.89 planning

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
