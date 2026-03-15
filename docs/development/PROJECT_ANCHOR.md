# Project Anchor

## Active Anchor

A2.94 - Evidence-to-Claim Alignment Signals Baseline

### Goal

Add deterministic evidence-to-claim alignment signaling so trust diagnostics reflect a clear
reasoning process (checks and outcomes) without polluting answer text with hedging noise.

### Why Now

A2.93 added internal contradiction checks. The next trust gap is external alignment:
claims should be compared with available evidence signals and surfaced as process diagnostics.

### Architecture Position

Target A2.94 boundaries:

- **Evidence alignment seam extension**
  - add deterministic claim-vs-evidence mismatch heuristics in trust diagnostics seam,
  - keep checks pure/testable with no provider dependencies.

- **Runtime diagnostics explainability**
  - surface compact reasoning-process steps and evidence-alignment status in diagnostics,
  - preserve existing `/answer` response contract shape.

- **Caution policy extension**
  - emit evidence mismatch reason-codes for high-certainty unsupported claims,
  - keep neutral evidence-aligned answers unchanged.

- **Guardrails and quality**
  - one patch = one reason,
  - focused + docs + full parity checks remain green.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory evidence-alignment touchpoints in trust guard and diagnostics merge path,
- lock scope to process-style trust diagnostics only (no answer-text verbosity changes),
- define deterministic evidence mismatch reason-codes.

Patch 1 artifacts:
- boundaries mapped:
  - trust guard output contract extension (`evidence_alignment`, reasoning process steps),
  - non-breaking response/diagnostics merge path,
- scope lock affirmed:
  - no provider/model routing changes,
  - no EvolutionAgent loop work,
  - no endpoint shape breakage.

#### Patch 2 — Evidence alignment seam extension
- add claim-vs-evidence mismatch checks and reasoning-process output in truthfulness diagnostics seam.

Patch 2 artifacts:
- seam updates in:
  - `src/services/answer/diagnostics/truthfulness_guard.py`
- baseline checks:
  - high-certainty claim with low evidence overlap triggers warn status,
  - reasoning process contains explicit check outcomes.
- seam coverage:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
- focused seam check green:
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - result: `8 passed`

#### Patch 3 — Runtime wiring + explainability
- wire evidence-alignment explainability fields into response diagnostics flow.

Patch 3 artifacts:
- runtime wiring in:
  - `src/services/answer/response_assembly.py`
- diagnostics additions:
  - `diagnostics.truthfulness_guard.evidence_alignment`
  - `diagnostics.truthfulness_guard.reasoning_process`
- reason-code closure continuity preserved (`truthfulness_guard_evidence_claim_mismatch_detected`).
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
- expand continuity tests for evidence-alignment and reasoning-process field stability.

Patch 4 artifacts:
- coverage expansion:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
- scenarios:
  - mismatch warn path exposes reasoning process and reason-code,
  - aligned path preserves ok status.
- focused continuity checks green:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_truthfulness_guard.py`
  - `tests/unit/services/answer/test_response_assembly_truthfulness.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - result: `58 passed`

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.94.

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
  - result: `149 passed`
- full-suite parity check green:
  - `uv run pytest`
  - result: `612 passed, 3 skipped`
- frontend parity check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.94 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [ ] Patch 2 — evidence alignment seam extension
- [ ] Patch 3 — runtime wiring + explainability
- [ ] Patch 4 — continuity tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.94:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.94 is complete when:

- deterministic evidence-alignment trust seam extension exists and is unit-tested,
- runtime diagnostics expose evidence-alignment reasoning-process fields without contract regression,
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

TBD - Post-A2.94 planning

## Anchor Closed

A2.93 complete - logic consistency signals baseline closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
