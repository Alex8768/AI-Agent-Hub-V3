# Project Anchor

## Active Anchor

A2.92 - Trust Calibration and Explainability Baseline

### Goal

Add deterministic trust calibration for answer confidence and explainability signals so
low-evidence certainty is explicitly down-scored and surfaced with contract-safe diagnostics.

### Why Now

A2.91 introduced baseline trust warnings. The next step is to make trust signals actionable:
confidence should be calibrated when guard risk is detected and diagnostics should explain
why confidence changed.

### Architecture Position

Target A2.92 boundaries:

- **Trust calibration seam**
  - add deterministic confidence-cap policy tied to trust guard risk,
  - keep calibration pure/testable with no provider dependencies.

- **Runtime diagnostics explainability**
  - surface pre/post confidence and cap application state in diagnostics,
  - preserve existing `/answer` response contract shape.

- **Caution policy extension**
  - cap confidence on low-evidence certainty and source-deference risk paths,
  - keep neutral evidence-backed responses unchanged.

- **Guardrails and quality**
  - one patch = one reason,
  - focused + docs + full parity checks remain green.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory confidence-touchpoint seams in answer response assembly and diagnostics,
- lock scope to trust calibration + explainability only,
- define deterministic reason-codes for confidence-cap outcomes.

Patch 1 artifacts:
- boundaries mapped:
  - calibration seam input/output contract (`status`, `reason_codes`, confidence before/after),
  - non-breaking response/diagnostics merge path,
- scope lock affirmed:
  - no provider/model routing changes,
  - no EvolutionAgent loop work,
  - no endpoint shape breakage.

#### Patch 2 — Confidence calibration seam
- add deterministic confidence-calibration helper aligned with truthfulness guard results.

Patch 2 artifacts:
- calibration helper in:
  - `src/services/answer/diagnostics/truthfulness_guard.py`
- baseline checks:
  - warn status caps confidence at deterministic ceiling,
  - ok status leaves confidence unchanged.
- seam coverage:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
- focused seam check green:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - result: `6 passed`

#### Patch 3 — Runtime wiring + explainability
- wire confidence calibration into answer response assembly.

Patch 3 artifacts:
- runtime wiring in:
  - `src/services/answer/response_assembly.py`
  - `src/services/answer/response/runtime_parity_helpers.py`
- diagnostics additions:
  - `diagnostics.truthfulness_guard.confidence_before`
  - `diagnostics.truthfulness_guard.confidence_after`
  - `diagnostics.truthfulness_guard.confidence_cap_applied`
- reason-code closure continuity preserved (`truthfulness_guard_confidence_capped`).
- focused wiring checks green:
  - `tests/unit/services/answer/test_response_assembly_truthfulness.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - `tests/unit/services/answer/test_answer_soft_failure_observability.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py::test_decomposition_no_growth_gate_answer_and_reasoning_monolith_line_budgets`
  - result: `68 passed`

#### Patch 4 — Continuity tests
- expand continuity tests for calibration behavior and debug snapshot stability.

Patch 4 artifacts:
- coverage expansion:
  - `tests/unit/services/answer/test_response_assembly_truthfulness.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
- scenarios:
  - warn path caps confidence and emits reason-code,
  - ok path keeps confidence unchanged.
- focused continuity checks green:
  - `tests/unit/services/answer/test_response_assembly_truthfulness.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - result: `50 passed`

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.92.

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
  - result: `608 passed, 3 skipped`
- frontend parity check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.92 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — confidence calibration seam
- [x] Patch 3 — runtime wiring + explainability
- [x] Patch 4 — continuity tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.92:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.92 is complete when:

- deterministic confidence calibration seam exists and is unit-tested,
- runtime diagnostics expose confidence calibration explainability fields without contract regression,
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

TBD - Post-A2.92 planning

## Anchor Closed

A2.91 complete - truthfulness and consistency guard baseline closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
