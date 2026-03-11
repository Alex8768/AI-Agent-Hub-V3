# Project Anchor

## Active Anchor

TBD - Post-A2.81 planning

### Goal

Continue extraction-only convergence of answer/reasoning facades after A2.80 closure,
reducing residual high-density helper concentration while preserving runtime parity.

### Why Now

A2.80 closed with extraction and guardrail recalibration to `1781`/`262` baselines.
Residual hotspots remain in answer/reasoning facades, requiring another bounded
inventory-first extraction cycle.

### Architecture Position

Target A2.81 boundaries:

- **Answer convergence phase 25**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning convergence phase 25**
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
  - `src/services/answer/answer_service.py`: `1781` lines
  - `src/layers/pro/reasoning/engine.py`: `262` lines
- hotspot inventory captured for extraction planning:
  - answer clusters: `_apply_diagnostics`, `handle_contract`,
    `_run_answer_primary_pipeline`, `_rank_proactive_bundle`
  - reasoning clusters: `synthesize`, `_synthesize_fallback`,
    `_build_reasoning_trace_diagnostics`
- import budget inventory captured:
  - answer local imports: `15` (budget `<= 15`)
  - reasoning local imports: `14` (budget `<= 14`)
- scope lock affirmed:
  - extraction-only changes,
  - parity-safe wiring updates only,
  - no net-new features or endpoint contract changes.
- focused inventory guardrail checks green:
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - result: `16 passed`
- docs quality gates green:
  - `tests/unit/docs`
  - result: `41 passed`

#### Patch 2 - Answer extraction phase-25
- extract next bounded clusters from `answer_service.py` (policy/runtime-guard/helper seams),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- proactive ranking seam extracted into:
  - `src/services/answer/response/proactive_ranking.py`
  - `rank_proactive_bundle`
- `src/services/answer/answer_service.py` now retains thin compatibility wrapper:
  - `_rank_proactive_bundle` delegates to extracted seam via dynamic import
- facade reduction achieved:
  - `src/services/answer/answer_service.py`: `1781 -> 1737` lines
- focused parity/guardrail checks green:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/services/answer/test_answer_soft_failure_observability.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_anticipatory_quality_gate.py`
  - result: `77 passed`

#### Patch 3 - Reasoning extraction phase-25
- extract next bounded clusters from `reasoning/engine.py` (runtime fallback / diagnostics helper seams),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- synthesize runtime dependency composition seam extracted into:
  - `src/layers/pro/reasoning/synthesis/runtime_dependencies.py`
  - `synthesize_with_engine_runtime_dependencies`
- `src/layers/pro/reasoning/engine.py` now retains thin compatibility wrapper:
  - `synthesize` delegates to extracted seam via dynamic import
  - runtime parity preserved by forwarding policy/logger runtime callables from `engine` module
- facade reduction achieved:
  - `src/layers/pro/reasoning/engine.py`: `262 -> 241` lines
- focused parity/guardrail checks green:
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_fallback.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_timeout.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_coordination_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_runtime_integration.py`
  - `tests/unit/layers/pro/test_reasoning_enterprise_productization_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_anticipatory_quality_gate.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - result: `40 passed`

#### Patch 4 - Guardrail threshold recalibration and import-budget expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for seam wiring + import-budget drift prevention,
- keep failure messages actionable for CI.

Patch 4 artifacts:
- no-growth thresholds recalibrated in
  `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`:
  - `answer_service_max_lines: 1781 -> 1737`
  - `reasoning_engine_max_lines: 262 -> 241`
- facade import-budget no-growth gates preserved at reduced baselines:
  - `answer_local_import_budget`: `15`
  - `reasoning_local_import_budget`: `14`
- focused guardrail + parity checks green:
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_fallback.py`
  - `tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_timeout.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_coordination_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_multi_agent_runtime_integration.py`
  - `tests/unit/layers/pro/test_reasoning_enterprise_productization_quality_gate.py`
  - `tests/unit/layers/pro/test_reasoning_anticipatory_quality_gate.py`
  - result: `40 passed`

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.81 with docs sync.

Patch 5 artifacts:
- full-suite checks green:
  - `uv run pytest`
  - result: `576 passed, 3 skipped`
- focused closure checks retained green from A2.81 patch flow:
  - answer/reasoning focused parity + guardrails (`81 passed`)
  - docs quality gates (`41 passed`)
- closure baselines preserved:
  - `src/services/answer/answer_service.py`: `1737` lines
  - `src/layers/pro/reasoning/engine.py`: `241` lines
  - import budgets: answer `15`, reasoning `14`
- mandatory docs sync completed across:
  - `docs/development/PROJECT_ANCHOR.md`
  - `docs/development/PROJECT_CHECKLIST.md`
  - `docs/development/STATUS.md`
  - `docs/architecture/PLATFORM_FEATURES.md`

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-25
- [x] Patch 3 - Reasoning extraction phase-25
- [x] Patch 4 - Guardrail threshold recalibration and import-budget expansion
- [x] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.81
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.81:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.81 is complete when:

- answer and reasoning convergence phase-25 extraction is completed with parity
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

TBD - Post-A2.82 planning

## Anchor Closed

A2.81 complete - Facade Convergence Phase 25 closed with extraction + guardrails + parity.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
