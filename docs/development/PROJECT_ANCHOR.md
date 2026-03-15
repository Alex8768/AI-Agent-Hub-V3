# Project Anchor

## Active Anchor

A2.83 Step 0.5 - Facade Stabilization Before Act/Evolve

### Goal

Stabilize `AnswerService` as a strict facade before enabling Act/Evolve runtime tracks,
so new capabilities do not increase coupling or reintroduce unstable `/answer` failures.

### Why Now

Current user-facing issues are runtime-behavioral (intermittent `500`, over-guarded tool
path in assistant mode, oversized response payload), not monolith-size issues.
Without a clean facade boundary, Act/Evolve additions will compound instability.

### Architecture Position

Target A2.83 Step 0.5 boundaries:

- **Facade-first answer runtime**
  - keep `src/services/answer/answer_service.py` as thin orchestration entry,
  - separate mode routing / failure policy / response presentation seams.

- **No-regression path to Act/Evolve**
  - prepare read-only Act route (`list_files`, `read_file`) without mixing execution policy
    into answer synthesis core,
  - preserve existing contract compatibility while adding deterministic reason-codes.

- **Guardrails and quality**
  - maintain one-patch-one-reason execution,
  - keep docs + runtime quality gates green after each patch.

### Patch Plan

#### Patch 1 — Inventory + scope lock (Step 0.5)
- inventory current `AnswerService` responsibilities by runtime concern:
  mode routing, synthesis path, tool path, failure handling, response shaping,
- lock scope to facade stabilization seams only (no net-new intelligence behavior),
- define patch contract for Step 0.5 patches 2-5.

Patch 1 artifacts:
- facade boundary inventory captured:
  - synthesis orchestration path,
  - tool selection/execution entry path,
  - soft-failure policy path,
  - response presentation path (compact vs diagnostics-heavy),
- scope lock affirmed:
  - seam-first changes only,
  - no global refactor,
  - no opportunistic feature drift outside Step 0.5 goals.

#### Patch 2 — Mode router seam
- introduce explicit answer/act mode router seam while preserving endpoint contract.

Patch 2 artifacts:
- mode router seam extracted to:
  - `src/services/answer/mode_router.py`
  - `resolve_answer_runtime_mode`
  - `apply_runtime_mode_diagnostics`
- `AnswerService.handle_contract` now resolves runtime mode explicitly before orchestration
  and records selected/requested mode diagnostics after merge flow.
- deterministic fallback behavior introduced for unsupported/disabled modes:
  - `runtime_mode_unsupported_fallback_answer`
  - `runtime_mode_act_disabled_fallback_answer`
- focused checks green:
  - `tests/unit/services/answer/test_answer_mode_router.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/docs`
  - result: `59 passed`

#### Patch 3 — Failure policy seam
- enforce controlled fallback for user-path errors (`/answer`) with deterministic reason-codes.

Patch 3 artifacts:
- pending

#### Patch 4 — Response presenter seam
- split compact response shape from full diagnostics payload for UI clarity and runtime efficiency.

Patch 4 artifacts:
- pending

#### Patch 5 — Guardrails + parity + closure
- run focused checks for mode router, failure policy and compact/full response seams,
- sync mandatory docs and close Step 0.5.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — mode router seam
- [ ] Patch 3 — failure policy seam
- [ ] Patch 4 — response presenter seam
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep `AnswerService` facade-thin; no new heavy business logic in facade.
- Preserve endpoint parity and deterministic reason-codes.
- No global refactor in Step 0.5.
- One patch = one reason.

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

TBD - Post-A2.83 planning

## Anchor Closed

A2.82 complete - Facade Convergence Phase 26 closed with answer facade stabilization, guardrails, and parity.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
