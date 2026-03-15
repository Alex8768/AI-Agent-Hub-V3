# Project Anchor

## Active Anchor

A2.91 - Truthfulness and Consistency Guard Baseline

### Goal

Introduce a deterministic truthfulness/consistency guard seam that evaluates answer claims
against runtime evidence signals and flags probable overconfidence, source deference,
or contradiction-risk with explicit reason-codes.

### Why Now

Runtime safety and UX baselines are in place through A2.90; the next bottleneck is trust:
answers should be logically cautious when evidence is weak and should not blindly defer
to potentially wrong sources.

### Architecture Position

Target A2.91 boundaries:

- **Truthfulness guard seam**
  - build deterministic heuristics for claim/evidence consistency checks,
  - keep seam pure and testable with no network dependencies.

- **Runtime diagnostics integration**
  - surface guard status and reason-codes in diagnostics,
  - preserve existing `/answer` response contract shape.

- **Caution policy baseline**
  - trigger explicit warning signals for low-evidence high-certainty outputs,
  - detect direct source-deference language patterns.

- **Guardrails and quality**
  - one patch = one reason,
  - focused + docs + full parity checks remain green.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory trust-related runtime touchpoints:
  evidence counters, confidence fields, warning/reason-code merge paths, response assembly seams,
- lock scope to deterministic truthfulness guard baseline only,
- define initial reason-code taxonomy and diagnostics shape.

Patch 1 artifacts:
- boundaries mapped:
  - guard seam input contract (`query`, `answer`, diagnostics evidence signals),
  - guard seam output contract (`status`, `reason_codes`),
  - non-breaking diagnostics merge path,
- scope lock affirmed:
  - no provider/model routing changes,
  - no EvolutionAgent loop work,
  - no endpoint shape breakage.

#### Patch 2 — Truthfulness guard seam
- add extracted seam for deterministic claim/evidence risk evaluation.

Patch 2 artifacts:
- new seam:
  - `src/services/answer/diagnostics/truthfulness_guard.py`
- baseline checks:
  - low evidence + strong certainty phrase,
  - direct source-deference phrase detection.
- seam coverage:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
- focused seam check green:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - result: `4 passed`

#### Patch 3 — Runtime wiring
- wire guard seam into answer response diagnostics flow.

Patch 3 artifacts:
- runtime wiring in:
  - `src/services/answer/response_assembly.py` (or equivalent response seam)
- diagnostics additions:
  - `diagnostics.truthfulness_guard.status`
  - `diagnostics.truthfulness_guard.reason_codes`
- reason-code closure continuity preserved.

#### Patch 4 — Continuity tests
- expand tests for diagnostics continuity and warning propagation.

Patch 4 artifacts:
- coverage expansion:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
- scenarios:
  - no evidence + certainty claim emits guard warning,
  - neutral answer remains guard-pass.

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.91.

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
  - result: green
- frontend parity check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.91 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — truthfulness guard seam
- [ ] Patch 3 — runtime wiring
- [ ] Patch 4 — continuity tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.91:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.91 is complete when:

- deterministic truthfulness guard seam exists and is unit-tested,
- runtime diagnostics expose guard status and reason-codes without contract regression,
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

TBD - Post-A2.91 planning

## Anchor Closed

A2.90 complete - ui reliability and product ux baseline closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
