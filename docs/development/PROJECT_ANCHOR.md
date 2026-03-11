# Project Anchor

## Active Anchor

A2.58 - Thin Facade Completion (Answer/Reasoning) (Closed)

### Goal

Complete phase-2 thin-facade decomposition for `answer_service` and `reasoning/engine`
so orchestration entrypoints remain thin and bounded modules own policy/diagnostics logic.

### Why Now

A2.57 established governance and first extraction seams.
Residual risk remains concentrated in large facade/orchestrator files where policy and
diagnostics logic still coexist with flow wiring.

### Architecture Position

Target A2.58 boundaries:

- **Answer thin-facade completion**
  - continue extracting heavy clusters from `src/services/answer/answer_service.py`,
  - keep behavior/API/diagnostics parity unchanged.

- **Reasoning thin-engine completion**
  - continue extracting bounded helpers from `src/layers/pro/reasoning/engine.py`,
  - keep `ReasoningEngine` as compatibility facade.

- **Guardrails and quality**
  - enforce no-growth rule from `docs/architecture/refactoring-guardrails.md`,
  - keep deterministic focused + full-suite green checks.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory remaining heavy clusters and line-budget hotspots in answer/reasoning facades,
- lock scope to extraction-only changes with strict parity constraints.

#### Patch 2 - Answer extraction phase-2
- extract next bounded clusters from `answer_service.py` (diagnostics/response/execution flow helpers),
- reduce facade branching and preserve endpoint/debug contract behavior.

Patch 2 artifacts:
- language helper extraction:
  - `_detect_response_language`, `_normalize_language_tag`, `_answer_language`
  - moved to `src/services/answer/response/language.py`
- runtime context helper extraction:
  - `_build_answer_service_runtime_context`
  - moved to `src/services/answer/context/runtime_context.py`
- reasoning adapter helper extraction:
  - `_build_reasoning_runtime_adapter`
  - moved to `src/services/answer/reasoning/runtime_adapter.py`
- memory consistency diagnostics helper extraction:
  - `_build_memory_consistency_bundle`, `_build_memory_consistency_strategy_contract`
  - moved to `src/services/answer/diagnostics/memory_consistency.py`

#### Patch 3 - Reasoning extraction phase-2
- extract next bounded clusters from `reasoning/engine.py` (evaluation/self-check/synthesis helpers),
- preserve reasoning diagnostics contract behavior.

Patch 3 artifacts:
- runtime evaluation diagnostics helper extraction:
  - `_reasoning_quality_diagnostics`
  - `_build_reasoning_trace_diagnostics`
  - `_build_reasoning_benchmark_diagnostics`
  - moved to `src/layers/pro/reasoning/evaluation/runtime_diagnostics.py`
- `ReasoningEngine` static methods retain compatibility wrappers delegating to extracted helpers.

#### Patch 4 - Decomposition guardrail quality-gate expansion
- expand deterministic checks for thin-facade budgets and no-growth constraints,
- keep failure messages actionable for CI.

Patch 4 artifacts:
- deterministic no-growth line-budget gate added for monolith targets:
  - `src/services/answer/answer_service.py`
  - `src/layers/pro/reasoning/engine.py`
- gate location:
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`

#### Patch 5 - Guardrails + parity + closure
- run focused and full-suite checks and close A2.58 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer extraction phase-2
- [x] Patch 3 - Reasoning extraction phase-2
- [x] Patch 4 - Decomposition guardrail quality-gate expansion
- [x] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.58
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.58:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.58 is complete when:

- answer and reasoning thin-facade extraction phase-2 is completed with parity
- no-growth and size-budget guardrails are reinforced with deterministic checks
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

TBD - Post-A2.58 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
