# Project Anchor

## Active Anchor

A2.67 - Facade Convergence Phase 11 (Answer/Reasoning)

### Goal

Continue extraction-only convergence of answer/reasoning facades to reduce remaining
residual helper concentration and keep moving toward facade/orchestrator target budgets.

### Why Now

A2.66 closed with additional policy/runtime seam extraction and refreshed no-growth gates.
Residual high-density helper clusters remain in `answer_service.py` and `reasoning/engine.py`,
so another bounded convergence phase is required.

### Architecture Position

Target A2.67 boundaries:

- **Answer convergence phase 11**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning convergence phase 11**
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
  - `src/services/answer/answer_service.py`: `2972` lines
  - `src/layers/pro/reasoning/engine.py`: `535` lines
- hotspot inventory captured for extraction planning:
  - answer clusters: `_apply_diagnostics`, `_run_assistant_execution_orchestration_seam`,
    `_apply_execution_idempotency_guard`, `_build_tool_selection_bundle`, `_build_feedback_learning_bundle`
  - reasoning clusters: `synthesize`, `_synthesize_fallback`
- scope lock affirmed:
  - extraction-only changes,
  - parity-safe wiring updates only,
  - no net-new features or endpoint contract changes.

#### Patch 2 - Answer extraction phase-11
- extract next bounded clusters from `answer_service.py` (policy/runtime-guard/helper seams),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- feedback/tool-selection bundle seam extraction into existing planner-policy module:
  - moved `_build_feedback_learning_bundle` implementation to
    `src/services/answer/reasoning/llm_planner_policy.py` as `build_feedback_learning_bundle`
  - moved `_build_tool_selection_bundle` implementation to
    `src/services/answer/reasoning/llm_planner_policy.py` as `build_tool_selection_bundle`
- compatibility wrappers retained in `src/services/answer/answer_service.py` for monkeypatch/runtime API parity
- monolith reduction after extraction:
  - `src/services/answer/answer_service.py`: `2972 -> 2832` lines
- answer local import budget preserved:
  - `src.services.answer*` imports: `15`

#### Patch 3 - Reasoning extraction phase-11
- extract next bounded clusters from `reasoning/engine.py` (runtime fallback / diagnostics helper seams),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- graph runtime diagnostics seam extraction into existing evaluation diagnostics module:
  - moved graph-path diagnostics assembly from `ReasoningEngine.synthesize` to
    `src/layers/pro/reasoning/evaluation/runtime_diagnostics.py` as
    `apply_graph_runtime_diagnostics`
  - `src/layers/pro/reasoning/engine.py` now delegates graph runtime diagnostics/warning enrichment
    to extracted evaluation seam with compatibility callables
- compatibility parity preserved:
  - patched call path keeps `build_reasoning_execution_policy` and
    `_reasoning_quality_diagnostics` injectable/monkeypatchable via engine-level callables
- monolith reduction after extraction:
  - `src/layers/pro/reasoning/engine.py`: `535 -> 481` lines

#### Patch 4 - Guardrail threshold recalibration and import-budget expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for seam wiring + import-budget drift prevention,
- keep failure messages actionable for CI.

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.67 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-11
- [x] Patch 3 - Reasoning extraction phase-11
- [ ] Patch 4 - Guardrail threshold recalibration and import-budget expansion
- [ ] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.67
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.67:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.67 is complete when:

- answer and reasoning convergence phase-11 extraction is completed with parity
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

TBD - Post-A2.67 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
