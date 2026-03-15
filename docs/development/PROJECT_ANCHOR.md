# Project Anchor

## Active Anchor

A2.85 - Managed Action Profiles + Compact Diagnostics UX

### Goal

Introduce runtime policy profiles and compact diagnostics delivery so action behavior is
controllable by environment and the UI can switch between concise and expanded views.

### Why Now

A2.84 unlocked read-only Act and visible block reasons. The next bottleneck is profile
control (`prod_strict`/`dev_guided`/`dev_full`) and response payload ergonomics for the UI.

### Architecture Position

Target A2.85 boundaries:

- **Managed runtime policy profiles**
  - normalize policy profile selection by environment/runtime context,
  - keep deterministic reason-codes when profile blocks actions.

- **Compact diagnostics delivery**
  - keep core answer payload stable while enabling concise default diagnostics output,
  - preserve ability to request expanded diagnostics deterministically.

- **UI diagnostics ergonomics**
  - expose compact/expanded diagnostics toggle in UI,
  - preserve runtime mode and reason-code visibility from A2.84.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory profile-sensitive runtime touchpoints:
  action allowlist/deny rules, mode routing, fallback and warning propagation,
  compact diagnostics shaping and UI consumption paths,
- lock scope to managed profiles + compact diagnostics UX only,
- define deterministic contract for profile and diagnostics-view reason-codes.

Patch 1 artifacts:
- runtime boundary inventory captured:
  - profile selection and policy decision path,
  - diagnostics compact/full presenter path,
  - UI diagnostics toggle/render path,
  - controlled fallback + warning propagation path,
- scope lock affirmed:
  - no expansion of side-effecting execution in A2.85,
  - no endpoint shape breakage,
  - no global refactor,
  - no opportunistic feature drift.

#### Patch 2 — Policy profile seam
- introduce deterministic runtime profile resolver (`prod_strict`/`dev_guided`/`dev_full`)
  and wire policy diagnostics reason-codes.

Patch 2 artifacts:
- policy profile seam extracted to:
  - `src/services/answer/policy_profiles.py`
  - `resolve_runtime_policy_profile`
- Act runtime now resolves and surfaces profile diagnostics in:
  - `src/services/answer/act_read_only.py`
  - `diagnostics.runtime_policy_profile`
- deterministic profile gating enforced:
  - `prod_strict` blocks Act read-only execution with `act_blocked_by_policy_profile`
  - `dev_guided`/`dev_full` keep read-only Act path enabled
  - debug-only request override reason-codes:
    - `runtime_policy_profile_override_applied`
    - `runtime_policy_profile_override_blocked_in_non_debug`
- focused checks green:
  - `tests/unit/services/answer/test_policy_profiles.py`
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `110 passed`

#### Patch 3 — Compact diagnostics contract seam
- enforce compact diagnostics default with deterministic expanded diagnostics opt-in.

Patch 3 artifacts:
- pending

#### Patch 4 — UI compact/expanded diagnostics toggle
- add UI control for diagnostics verbosity while preserving mode/reason visibility.

Patch 4 artifacts:
- pending

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.85.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — policy profile seam
- [ ] Patch 3 — compact diagnostics contract seam
- [ ] Patch 4 — UI compact/expanded diagnostics toggle
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep Act side-effect execution disabled in A2.85.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.85:

- write-path tool execution / side-effectful actions,
- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.85 is complete when:

- profile-driven policy behavior is deterministic and observable,
- compact diagnostics default + expanded opt-in contract is stable,
- UI can toggle diagnostics verbosity without losing reason-code transparency,
- focused and full quality checks remain green,
- mandatory docs are synchronized.

## A2.84 Snapshot (Closed)

A2.84 closure markers retained for continuity:

- Act read-only seam (`list_files`, `read_file` allowlist),
- reason-code closure seam into top-level warnings,
- UI runtime mode + block reason visibility,
- full-suite parity: `584 passed, 3 skipped`.

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

TBD - Post-A2.85 planning

## Anchor Closed

A2.84 complete - Act read-only runtime and UI transparency closure.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
