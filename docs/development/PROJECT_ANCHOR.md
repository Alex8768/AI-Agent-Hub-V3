# Project Anchor

## Active Anchor

A2.76 - Facade Convergence Phase 20 (Answer/Reasoning)

### Goal

Continue extraction-only convergence of answer/reasoning facades after A2.75 closure,
reducing residual high-density helper concentration while preserving runtime parity.

### Why Now

A2.75 closed with extraction and guardrail recalibration to `2051`/`310` baselines.
Residual hotspots remain in answer/reasoning facades, requiring another bounded
inventory-first extraction cycle.

### Architecture Position

Target A2.76 boundaries:

- **Answer convergence phase 20**
  - continue extracting bounded helper clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning convergence phase 20**
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
  - `src/services/answer/answer_service.py`: `2051` lines
  - `src/layers/pro/reasoning/engine.py`: `310` lines
- hotspot inventory captured for extraction planning:
  - answer clusters: `_apply_diagnostics`, `retrieve`,
    `_bridge_plan_to_draft_actions`, `_build_conversational_runtime_parity_bundle`, `handle_contract`
  - reasoning clusters: `synthesize`, `_synthesize_fallback`, `_build_fallback_answer_text`
- import budget inventory captured:
  - answer local imports: `15` (budget `<= 15`)
  - reasoning local imports: `14` (budget `<= 17`)
- scope lock affirmed:
  - extraction-only changes,
  - parity-safe wiring updates only,
  - no net-new features or endpoint contract changes.

#### Patch 2 - Answer extraction phase-20
- extract next bounded clusters from `answer_service.py` (policy/runtime-guard/helper seams),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- pending.

#### Patch 3 - Reasoning extraction phase-20
- extract next bounded clusters from `reasoning/engine.py` (runtime fallback / diagnostics helper seams),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- pending.

#### Patch 4 - Guardrail threshold recalibration and import-budget expansion
- recalibrate no-growth thresholds to new post-extraction baselines,
- expand deterministic checks for seam wiring + import-budget drift prevention,
- keep failure messages actionable for CI.

Patch 4 artifacts:
- pending.

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.76 with docs sync.

Patch 5 artifacts:
- pending.

### Progress

- [x] Patch 1 — inventory + scope lock
- [ ] Patch 2 - Answer extraction phase-20
- [ ] Patch 3 - Reasoning extraction phase-20
- [ ] Patch 4 - Guardrail threshold recalibration and import-budget expansion
- [ ] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.76
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.76:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.76 is complete when:

- answer and reasoning convergence phase-20 extraction is completed with parity
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

TBD - Post-A2.76 planning

## Anchor Closed

A2.75 complete - Facade Convergence Phase 19 closed with extraction + guardrails + parity.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
