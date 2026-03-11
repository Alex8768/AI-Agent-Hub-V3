# Project Anchor

## Active Anchor

A2.56 — Operational Guardrails for Soft-Failure KPIs (Closed)

### Goal

Introduce deterministic operational guardrails for answer-path soft-failure/fallback health
signals so degradation risk is observable, trendable, and alertable without API regressions.

The intent of this anchor is observability-policy and operations focused:
- define KPI contracts for healthy answer-path requests,
- establish fallback/soft-failure rate visibility and thresholds,
- preserve runtime/API parity while improving operational triage signals.

### Why Now

A2.55 is closed and documentation state is synchronized.

The main residual risk is operational blind spots: soft-failure and fallback paths are visible
per request, but policy-level KPI/threshold guardrails for sustained degradation are not yet explicit.

A2.56 focuses on operational policy closure for ongoing answer-path reliability.

### Architecture Position

Target A2.56 boundaries:

- **KPI Contract Surface**
  - define healthy-path KPI (`soft_failures_count == 0`)
  - define fallback-rate denominator/numerator contract
  - define deterministic threshold policy wording for alertability

- **Operational Diagnostics Policy**
  - codify soft-failure/fallback visibility expectations
  - classify warning vs critical operational states
  - keep scoped to answer-path diagnostics surface

- **Quality Gates**
  - preserve docs and full-suite green status
  - ensure policy assertions are deterministic and CI-triable

### Patch Plan

#### Patch 1 — Inventory + scope lock
- Build explicit inventory of current soft-failure/fallback diagnostics surfaces and gaps.
- Classify operational guardrail targets:
  - KPI definition,
  - threshold/alert policy wording,
  - diagnostics exposure and reporting scope.
- Define no-regression constraints and allowed edit scope.

#### Patch 2 — KPI policy contract introduction
- Introduce explicit KPI wording/contracts in docs for healthy-path and fallback-rate policy.
- Keep scope operational-policy first (no product behavior changes).

KPI policy contract baseline for A2.56:
- `healthy_request_kpi`: request is healthy when `soft_failures_count == 0`.
- `fallback_rate_kpi`: `requests_with_fallback / total_answer_requests` over a fixed window.
- `soft_failure_rate_kpi`: `requests_with_soft_failures / total_answer_requests` over a fixed window.
- Threshold policy classes:
  - `healthy`: fallback/soft-failure rates below warning thresholds,
  - `warning`: any rate above warning threshold,
  - `critical`: any rate above critical threshold.
- Alertability policy:
  - thresholds must be explicitly documented with denominator/window,
  - all KPI terms must map to diagnostics fields used by answer-path runtime.

#### Patch 3 — Diagnostics surface mapping and reporting contract
- Document which diagnostics fields/panels/reports represent KPI components.
- Ensure deterministic mapping from runtime diagnostics to operational policy terms.

Diagnostics-to-KPI mapping contract (A2.56):
- `requests_with_soft_failures` source:
  - `planning_reason_codes` contains any entry matching `*_soft_failure*`
    or `*_assignment_failed`.
- `requests_with_fallback` source:
  - `response_mode == "assistant_fallback"` OR
  - `planning_reason_codes` contains any entry with `fallback`.
- `healthy_request_kpi` source:
  - request is healthy when neither soft-failure nor fallback predicates are true.
- `soft_failures_count` reporting contract:
  - computed as `len(filtered_soft_failure_codes)` from `planning_reason_codes`
    for each request.
- `fallback_count` reporting contract:
  - computed as `1` when fallback predicate is true, otherwise `0`.
- Panel/report mapping:
  - source-of-truth diagnostics surface is answer debug diagnostics payload;
    operational dashboards/alerts must derive KPI numerators from this payload
    without introducing alternate definitions.

#### Patch 4 — Guardrail test/policy enforcement hardening
- Add/expand deterministic tests or quality gates for operational policy wording/contracts.
- Ensure failure messages are actionable for CI triage.

#### Patch 5 — Guardrails + parity + closure
- Run focused + full checks and finalize closure sync.
- Close A2.56 with docs and quality-gate parity preserved.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — KPI policy contract introduction
- [x] Patch 3 — diagnostics surface mapping and reporting contract
- [x] Patch 4 — guardrail test/policy enforcement hardening
- [x] Patch 5 — guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.56
- Preserve answer/debug runtime/API parity
- Keep operational policy changes deterministic and scoped
- No opportunistic refactors beyond operational guardrails scope
- One patch = one reason

### Out of Scope

Do NOT modify during A2.56:

- planner/kernel topology
- unrelated product feature logic
- endpoint contract shape
- non-doc production code
- unrelated UI or infra features

### Definition of Done

A2.56 is complete when:

- operational KPI/threshold policy is explicitly documented
- diagnostics-to-policy mapping is stable and deterministic
- focused and full quality checks remain green
- no answer/debug parity regressions are introduced

## Next Anchor

TBD — Post-A2.56 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
