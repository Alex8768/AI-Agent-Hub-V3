# Project Anchor

## Active Anchor

A2.61 - Facade Convergence Phase 5 (Answer/Reasoning)

### Goal

Continue extraction-only convergence of answer/reasoning facades to reduce remaining
runtime-helper concentration and approach orchestrator/facade budget targets with parity.

### Why Now

A2.60 closed with additional policy/runtime seam extraction and stronger import-budget gates.
Residual complexity remains concentrated in large facade files that still exceed target budget
ranges, requiring one more bounded burn-down phase.

### Architecture Position

Target A2.61 boundaries:

- **Answer convergence phase 5**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning convergence phase 5**
  - continue extracting bounded helper clusters from `src/layers/pro/reasoning/engine.py`,
  - keep `ReasoningEngine` as compatibility facade.

- **Guardrails and quality**
  - enforce no-growth rule from `docs/architecture/refactoring-guardrails.md`,
  - keep deterministic focused + full-suite green checks.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory remaining high-density helper clusters and line-budget hotspots in answer/reasoning facades,
- lock scope to extraction-only changes with strict parity constraints.

#### Patch 2 - Answer extraction phase-5
- extract next bounded clusters from `answer_service.py` (policy/adapter/runtime-fallback helper seams),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- feedback policy seam extraction into existing planner-policy module:
  - `_build_feedback_policy_contract`
  - `_apply_feedback_policy_guards`
  - `_build_feedback_adaptation_policy_contract`
  - `_apply_feedback_adaptation_policy_guards`
  - moved to `src/services/answer/reasoning/llm_planner_policy.py`

#### Patch 3 - Reasoning extraction phase-5
- extract next bounded clusters from `reasoning/engine.py` (runtime fallback / planning helper seams),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- runtime dry-run fallback seam extraction:
  - `_build_dry_run_answer`
  - `_build_dry_run_answer_from_parts`
  - moved to `src/layers/pro/reasoning/evaluation/runtime_productization.py`

#### Patch 4 - Guardrail threshold recalibration and import-budget expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for seam wiring + import-budget drift prevention,
- keep failure messages actionable for CI.

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.61 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-5
- [x] Patch 3 - Reasoning extraction phase-5
- [ ] Patch 4 - Guardrail threshold recalibration and import-budget expansion
- [ ] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.61
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.61:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.61 is complete when:

- answer and reasoning convergence phase-5 extraction is completed with parity
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

TBD - Post-A2.61 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
