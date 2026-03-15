# Project Anchor

## Active Anchor

A2.95 - Structured Claim Graph and Evidence Binding Baseline

### Goal

Add deterministic structured claim graph diagnostics with evidence binding metadata so
reasoning-process checks are machine-readable and compact for trust evaluation.

### Why Now

A2.94 introduced evidence-alignment process signals. The next step is structure:
diagnostics should represent claims and evidence bindings as explicit graph-like artifacts.

### Architecture Position

Target A2.95 boundaries:

- **Claim graph seam extension**
  - add deterministic claim extraction and evidence binding metadata in trust diagnostics seam,
  - keep checks pure/testable with no provider dependencies.

- **Runtime diagnostics explainability**
  - surface structured claim graph and evidence bindings in diagnostics,
  - preserve existing `/answer` response contract shape.

- **Caution policy extension**
  - emit claim-graph mismatch reason-codes for unsupported high-certainty claims,
  - keep neutral supported claims unchanged.

- **Guardrails and quality**
  - one patch = one reason,
  - focused + docs + full parity checks remain green.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory claim-structure touchpoints in trust guard and diagnostics merge path,
- lock scope to structured diagnostics only (no answer-text verbosity changes),
- define deterministic claim-graph reason-codes.

Patch 1 artifacts:
- boundaries mapped:
  - trust guard output contract extension (`claim_graph`, `evidence_bindings`),
  - non-breaking response/diagnostics merge path,
- scope lock affirmed:
  - no provider/model routing changes,
  - no EvolutionAgent loop work,
  - no endpoint shape breakage.

#### Patch 2 — Claim graph seam extension
- add deterministic claim graph and evidence-binding builders in truthfulness diagnostics seam.

Patch 2 artifacts:
- seam updates in:
  - `src/services/answer/diagnostics/truthfulness_guard.py`
- baseline checks:
  - claims are extracted into stable nodes,
  - evidence bindings include overlap metrics and bound status.
- seam coverage:
  - `tests/unit/services/answer/test_truthfulness_guard.py`

#### Patch 3 — Runtime wiring + explainability
- wire structured claim diagnostics fields into response diagnostics flow.

Patch 3 artifacts:
- runtime wiring in:
  - `src/services/answer/response_assembly.py`
- diagnostics additions:
  - `diagnostics.truthfulness_guard.claim_graph`
  - `diagnostics.truthfulness_guard.evidence_bindings`
- reason-code closure continuity preserved (`truthfulness_guard_claim_graph_mismatch_detected`).

#### Patch 4 — Continuity tests
- expand continuity tests for claim graph and evidence-binding field stability.

Patch 4 artifacts:
- coverage expansion:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/services/answer/test_reason_code_policy.py`
- scenarios:
  - mismatch warn path exposes claim/evidence binding mismatch,
  - aligned path preserves ok status and bound claims.

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.95.

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
  - result: `151 passed`
- full-suite parity check green:
  - `uv run pytest`
  - result: `614 passed, 3 skipped`
- frontend parity check green:
  - `frontend: npm run build`
  - result: success
- mandatory docs synchronized for A2.95 closure:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [ ] Patch 2 — claim graph seam extension
- [ ] Patch 3 — runtime wiring + explainability
- [ ] Patch 4 — continuity tests
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.88.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.95:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.95 is complete when:

- deterministic claim-graph trust seam extension exists and is unit-tested,
- runtime diagnostics expose structured claim/evidence binding fields without contract regression,
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

TBD - Post-A2.95 planning

## Anchor Closed

A2.94 complete - evidence-to-claim alignment signals baseline closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
