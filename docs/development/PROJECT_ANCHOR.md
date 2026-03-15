# Project Anchor

## Active Anchor

A2.93 - Logic Consistency Signals Baseline

### Goal

Add deterministic logic-consistency signaling so answers with internal contradiction patterns
are surfaced as trust warnings with compact, user-readable explanation signals.

### Why Now

A2.92 calibrated confidence under trust risk; the next trust gap is internal coherence.
The runtime should explicitly flag probable answer contradictions and explain why trust is reduced.

### Architecture Position

Target A2.93 boundaries:

- **Logic consistency seam extension**
  - add deterministic contradiction-pattern checks in trust diagnostics seam,
  - keep checks pure/testable with no provider dependencies.

- **Runtime diagnostics explainability**
  - surface compact trust summary and logic consistency status in diagnostics,
  - preserve existing `/answer` response contract shape.

- **Caution policy extension**
  - emit contradiction reason-codes for internally inconsistent answer phrasing,
  - keep neutral internally consistent answers unchanged.

- **Guardrails and quality**
  - one patch = one reason,
  - focused + docs + full parity checks remain green.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory logic-consistency touchpoints in trust guard and diagnostics merge path,
- lock scope to contradiction signaling + compact explanation only,
- define deterministic contradiction reason-codes.

Patch 1 artifacts:
- boundaries mapped:
  - trust guard output contract extension (`logic_consistency`, compact trust summary),
  - non-breaking response/diagnostics merge path,
- scope lock affirmed:
  - no provider/model routing changes,
  - no EvolutionAgent loop work,
  - no endpoint shape breakage.

#### Patch 2 — Logic consistency seam extension
- add contradiction-pattern checks and compact trust summary in truthfulness diagnostics seam.

Patch 2 artifacts:
- seam updates in:
  - `src/services/answer/diagnostics/truthfulness_guard.py`
- baseline checks:
  - contradictory phrase pairs trigger warn status,
  - compact trust summary explains triggered trust signals.
- seam coverage:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
- focused seam check green:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - result: `8 passed`

#### Patch 3 — Runtime wiring + explainability
- wire logic-consistency explainability fields into response diagnostics flow.

Patch 3 artifacts:
- runtime wiring in:
  - `src/services/answer/response_assembly.py`
- diagnostics additions:
  - `diagnostics.truthfulness_guard.logic_consistency`
  - `diagnostics.truthfulness_guard.trust_summary`
- reason-code closure continuity preserved (`truthfulness_guard_internal_contradiction_detected`).
- focused wiring checks green:
  - `tests/unit/services/answer/test_response_assembly_truthfulness.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - `tests/unit/services/answer/test_answer_soft_failure_observability.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py::test_decomposition_no_growth_gate_answer_and_reasoning_monolith_line_budgets`
  - result: `71 passed`

#### Patch 4 — Continuity tests
- expand continuity tests for logic-consistency and explainability field stability.

Patch 4 artifacts:
- coverage expansion:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
- scenarios:
  - contradiction warn path exposes trust summary and reason-code,
  - consistent path preserves ok status.

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.93.

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
  - result: `147 passed`
- full-suite parity check green:
  - `uv run pytest`
  - result: `610 passed, 3 skipped`
- frontend parity check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.93 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — logic consistency seam extension
- [x] Patch 3 — runtime wiring + explainability
- [ ] Patch 4 — continuity tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.93:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.93 is complete when:

- deterministic logic-consistency trust seam extension exists and is unit-tested,
- runtime diagnostics expose logic-consistency explainability fields without contract regression,
- reason-code/warnings closure remains deterministic,
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

TBD - Post-A2.93 planning

## Anchor Closed

A2.92 complete - trust calibration and explainability baseline closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
