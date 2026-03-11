# Project Anchor

## Active Anchor

A2.71 - Facade Convergence Phase 15 (Answer/Reasoning)

### Goal

Continue extraction-only convergence of answer/reasoning facades after A2.70 closure,
reducing residual high-density helper concentration while preserving runtime parity.

### Why Now

A2.70 closed with extraction and guardrail recalibration to `2345`/`454` baselines.
Residual hotspots remain in answer/reasoning monolith facades, requiring another bounded
inventory-first extraction cycle.

### Architecture Position

Target A2.71 boundaries:

- **Answer convergence phase 15**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning convergence phase 15**
  - continue extracting bounded helper clusters from `src/layers/pro/reasoning/engine.py`,
  - keep `ReasoningEngine` as compatibility facade.

- **Guardrails and quality**
  - enforce no-growth rule from `docs/architecture/refactoring-guardrails.md`,
  - keep deterministic focused + full-suite green checks.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory remaining high-density helper clusters and line-budget hotspots in answer/reasoning facades,
- lock scope to extraction-only changes with strict parity constraints.

Patch 1 artifacts:
- no-growth baseline inventory captured:
  - `src/services/answer/answer_service.py`: `2345` lines
  - `src/layers/pro/reasoning/engine.py`: `454` lines
- hotspot inventory captured for extraction planning:
  - answer clusters: `_apply_diagnostics`, `_run_assistant_execution_orchestration_seam`,
    `_load_durable_records`, `_persist_durable_records`, `_build_idempotency_record_snapshot`
  - reasoning clusters: `_execute_planner_steps_mvp`, `synthesize`, `_synthesize_fallback`
- scope lock affirmed:
  - extraction-only changes,
  - parity-safe wiring updates only,
  - no net-new features or endpoint contract changes.

#### Patch 2 - Answer extraction phase-15
- extract next bounded clusters from `answer_service.py` (policy/runtime-guard/helper seams),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- durable-record helper seam extracted into
  `src/services/answer/execution/durable_keys.py`:
  - `build_idempotency_record_snapshot`
  - `load_durable_records`
  - `persist_durable_records`
- `src/services/answer/answer_service.py` now retains thin compatibility wrappers:
  - `_build_idempotency_record_snapshot`
  - `_load_durable_records`
  - `_persist_durable_records`
- facade reduction achieved without import-budget growth:
  - `src/services/answer/answer_service.py`: `2345 -> 2298` lines
  - local import statement count remained within current no-growth budget (`15`)
- focused parity/guardrail checks green:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/services/answer/test_answer_soft_failure_observability.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - result: `74 passed`

#### Patch 3 - Reasoning extraction phase-15
- extract next bounded clusters from `reasoning/engine.py` (runtime fallback / diagnostics helper seams),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- reasoning fallback-planner execution seam extracted into
  `src/layers/pro/reasoning/evaluation/runtime_productization.py`:
  - `execute_fallback_planner_steps_mvp`
- `src/layers/pro/reasoning/engine.py` now delegates `_execute_planner_steps_mvp`
  through extracted runtime-productization seam while preserving compatibility method.
- monolith reduction achieved with parity-safe wiring:
  - `src/layers/pro/reasoning/engine.py`: `454 -> 406` lines
- focused parity/guardrail checks green:
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_fallback.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_timeout.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_coordination_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_runtime_integration.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - result: `33 passed`

#### Patch 4 - Guardrail threshold recalibration and import-budget expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for seam wiring + import-budget drift prevention,
- keep failure messages actionable for CI.

Patch 4 artifacts:
- no-growth threshold recalibration applied in
  `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`:
  - `answer_service_max_lines`: `2345 -> 2298`
  - `reasoning_engine_max_lines`: `454 -> 406`
- facade import-budget guard verified against current extraction baselines:
  - answer local imports: `15` (budget `<= 15`)
  - reasoning local imports: `16` (budget `<= 17`)
- deterministic guardrail suite remained green after recalibration:
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - result: `16 passed`

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.71 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-15
- [x] Patch 3 - Reasoning extraction phase-15
- [x] Patch 4 - Guardrail threshold recalibration and import-budget expansion
- [ ] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.71
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.71:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.71 is complete when:

- answer and reasoning convergence phase-15 extraction is completed with parity
- no-growth thresholds and import-budget constraints are updated to latest baselines and enforced in CI
- target facades are further reduced and orchestration-focused
- focused and full quality checks remain green
- no answer/debug parity regressions are introduced

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

TBD - Post-A2.71 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
