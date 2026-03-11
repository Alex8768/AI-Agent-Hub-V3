# Project Anchor

## Active Anchor

A2.59 - Monolith Burn-Down Phase 3 (Answer/Reasoning)

### Goal

Continue controlled monolith burn-down for answer/reasoning entrypoints with extraction-only
changes, reducing high-risk helper concentration while preserving endpoint/runtime parity.

### Why Now

A2.58 closed with phase-2 extraction and no-growth line-budget gates.
Residual risk remains in still-large orchestration files that need further bounded extraction
to keep future changes maintainable and policy-safe.

### Architecture Position

Target A2.59 boundaries:

- **Answer burn-down phase 3**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning burn-down phase 3**
  - continue extracting bounded helper clusters from `src/layers/pro/reasoning/engine.py`,
  - keep `ReasoningEngine` as compatibility facade.

- **Guardrails and quality**
  - enforce no-growth rule from `docs/architecture/refactoring-guardrails.md`,
  - keep deterministic focused + full-suite green checks.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory remaining high-density helper clusters and line-budget hotspots in answer/reasoning facades,
- lock scope to extraction-only changes with strict parity constraints.

#### Patch 2 - Answer extraction phase-3
- extract next bounded clusters from `answer_service.py` (execution/diagnostics/post-orchestration helpers),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- runtime diagnostics wiring extraction:
  - `_wire_planner_runtime_diagnostics`
  - `_wire_tool_selection_runtime_diagnostics`
  - `_wire_feedback_runtime_diagnostics`
  - `_wire_feedback_adaptation_runtime_diagnostics`
  - `_wire_assistant_recovery_runtime_diagnostics`
  - `_wire_runtime_diagnostics`
  - moved to `src/services/answer/diagnostics/runtime_wiring.py`

#### Patch 3 - Reasoning extraction phase-3
- extract next bounded clusters from `reasoning/engine.py` (optimization/enterprise/meta-cognition helpers),
- preserve reasoning diagnostics contract behavior.

#### Patch 4 - Guardrail threshold recalibration and coverage expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for extraction-path coverage and guardrail drift prevention,
- keep failure messages actionable for CI.

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.59 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-3
- [ ] Patch 3 - Reasoning extraction phase-3
- [ ] Patch 4 - Guardrail threshold recalibration and coverage expansion
- [ ] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.59
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.59:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.59 is complete when:

- answer and reasoning burn-down phase-3 extraction is completed with parity
- no-growth thresholds are updated to latest baselines and enforced in CI
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

TBD - Post-A2.59 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
