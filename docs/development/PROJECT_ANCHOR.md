# Project Anchor

## Active Anchor

A2.86 - Controlled Write Actions via Confirm Flow

### Goal

Enable managed write-capable actions through explicit confirmation flow and profile-aware
policy gating without reintroducing uncontrolled side effects.

### Why Now

A2.85 completed profile diagnostics and diagnostics UX controls; the next bottleneck is
safe write execution enablement under deterministic confirmation and policy contracts.

### Architecture Position

Target A2.86 boundaries:

- **Write action governance**
  - allow write-capable tool path only behind confirmation gate,
  - enforce profile-aware policy behavior with deterministic reason-codes.

- **Confirmation flow hardening**
  - require explicit tokenized approval before side-effectful execution,
  - preserve idempotency and replay protection.

- **UI approval ergonomics**
  - surface pending write approvals with explicit approve/cancel controls,
  - preserve runtime/profile/reason transparency from A2.85.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory write-action runtime touchpoints:
  tool policy profile checks, confirmation token lifecycle, idempotency replay path,
  execution receipt diagnostics, and UI approval interaction path,
- lock scope to controlled write actions via confirm-flow only,
- define deterministic reason-code contract for policy, approval, and execution states.

Patch 1 artifacts:
- runtime boundary inventory captured:
  - write policy profile decision path,
  - confirmation handshake and token validation path,
  - execution gateway/idempotency replay path,
  - UI approval action path and status rendering,
- scope lock affirmed:
  - no ungated write execution path in A2.86,
  - no endpoint shape breakage,
  - no global refactor,
  - no opportunistic feature drift.

#### Patch 2 — Profile-aware write policy seam
- enforce write-action policy matrix (`prod_strict`/`dev_guided`/`dev_full`) and
  deterministic policy reason-codes.

Patch 2 artifacts:
- policy profile seam extended with explicit write policy contract:
  - `src/services/answer/policy_profiles.py`
  - `act_write_policy`: `blocked` / `confirm_required` / `direct_allowed`
- profile-to-write-policy matrix now deterministic:
  - `prod_strict` -> `blocked`
  - `dev_guided` -> `confirm_required`
  - `dev_full` -> `direct_allowed`
- unit coverage expanded for profile write policy expectations:
  - `tests/unit/services/answer/test_policy_profiles.py`
- focused checks green:
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `107 passed`

#### Patch 3 — Confirm-flow write execution seam
- route write-capable tool execution through approval handshake with deterministic
  token/idempotency/replay behavior.

Patch 3 artifacts:
- pending

#### Patch 4 — UI approval controls for write actions
- add pending-approval controls (approve/cancel) and execution status surfaces in UI.

Patch 4 artifacts:
- pending

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.86.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — profile-aware write policy seam
- [ ] Patch 3 — confirm-flow write execution seam
- [ ] Patch 4 — UI approval controls for write actions
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep ungated write execution disabled in A2.86.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.86:

- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.86 is complete when:

- write actions execute only through deterministic confirmation path,
- profile matrix behavior is deterministic and observable in diagnostics,
- UI surfaces approval intent/status and supports approve/cancel flow,
- focused and full quality checks remain green,
- mandatory docs are synchronized.

## A2.85 Snapshot (Closed)

A2.85 closure markers retained for continuity:

- runtime policy profile seam (`prod_strict` / `dev_guided` / `dev_full`),
- diagnostics presentation contract normalization (`requested_mode`/`resolved_mode`),
- UI compact/expanded diagnostics toggle,
- full-suite parity: `589 passed, 3 skipped`.

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

TBD - Post-A2.86 planning

## Anchor Closed

A2.85 complete - managed policy profiles and compact diagnostics UX closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
