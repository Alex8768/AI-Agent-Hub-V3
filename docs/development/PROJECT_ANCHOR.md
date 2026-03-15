# Project Anchor

## Active Anchor

A2.84 - Act Read-Only Runtime + UX Transparency

### Goal

Deliver the first user-visible Act runtime path with read-only workspace tools and
explicit UI-visible block reasons, while preserving controlled `/answer` behavior.

### Why Now

A2.83 established the facade seams (mode routing, failure policy, response presenter),
so the next highest-impact step is enabling practical read-only actions and making
policy/runtime decisions transparent to users.

### Architecture Position

Target A2.84 boundaries:

- **Act read-only runtime enablement**
  - allow only `list_files` and `read_file` execution path in Act mode,
  - block side-effecting tools with deterministic policy reason-codes.

- **No-uncontrolled-failure answer path**
  - preserve non-500 controlled fallback guarantees on user path,
  - keep mode/policy diagnostics explicit and machine-consumable.

- **UX transparency contract**
  - surface runtime mode and policy block reasons in UI instead of opaque errors,
  - keep default response contract backward compatible.

- **Guardrails and quality**
  - maintain one patch = one reason discipline,
  - keep focused + docs + full-suite closure checks green.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory all current Act/Tool runtime touchpoints and UI diagnostics touchpoints:
  answer mode routing, policy blocks, tool execution filters, response diagnostics mapping,
- lock scope to read-only Act enablement + diagnostics transparency only,
- define deterministic reason-code contract for mode/policy decisions.

Patch 1 artifacts:
- runtime boundary inventory captured:
  - Act-mode routing seam usage path,
  - tool-allowlist/policy enforcement path,
  - controlled fallback and reason-code emission path,
  - UI diagnostics consumption path for mode/block visibility,
- scope lock affirmed:
  - read-only tools only (`list_files`, `read_file`),
  - no write/side-effect execution in A2.84,
  - no endpoint shape breakage,
  - no global refactor,
  - no opportunistic feature drift.

#### Patch 2 — Act read-only execution seam
- wire deterministic read-only tool execution path for Act mode with explicit allowlist.

Patch 2 artifacts:
- act runtime seam extracted to:
  - `src/services/answer/act_read_only.py`
  - `apply_act_read_only_runtime`
- `AnswerService.handle_contract` now invokes read-only Act seam after runtime mode
  resolution and before response presentation.
- deterministic read-only policy enforced for Act mode:
  - allowlist: `list_files`, `read_file`
  - blocked reason-code: `act_read_only_tool_not_allowlisted`
  - execution reason-code: `act_read_only_tool_executed`
- workspace MCP runtime wiring kept explicit on app bootstrap:
  - `src/api/mcp_workspace_runtime.py`
  - `src/api/bootstrap.py`
- focused checks green:
  - `tests/unit/services/answer/test_act_read_only_runtime.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `106 passed`

#### Patch 3 — Failure-policy and reason-code closure
- guarantee controlled fallback + reason-codes for policy/runtime blocks across `/answer`.

Patch 3 artifacts:
- reason-code closure seam extracted to:
  - `src/services/answer/reason_code_policy.py`
  - `apply_reason_code_closure`
- `AnswerService.handle_contract` now applies reason-code closure after
  mode/act diagnostics, ensuring deterministic policy/runtime reason-codes are
  promoted to top-level `warnings`.
- closure includes reason-code propagation from:
  - `diagnostics.runtime_mode.reason_codes`
  - `diagnostics.act_runtime.reason_codes`
  - `diagnostics.failure_policy.reason_code`
- focused checks green:
  - `tests/unit/services/answer/test_reason_code_policy.py`
  - `tests/unit/services/answer/test_answer_orchestration_quality_gate.py`
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
  - `tests/unit/docs`
  - result: `107 passed`

#### Patch 4 — UI mode/block transparency
- surface `runtime_mode` and policy block reasons in UI (meta/chat surfaces).

Patch 4 artifacts:
- chat runtime transparency added in:
  - `frontend/src/components/ChatPanel.tsx`
  - `frontend/src/components/ChatPanel.css`
- per-answer runtime badges now render:
  - selected/requested mode visibility
  - Act runtime status
  - surfaced reason-codes for policy/runtime block context
- meta diagnostics panel expanded with runtime sections:
  - `frontend/src/components/MetaPanel.tsx`
  - new Runtime Mode and Act Runtime blocks
- frontend compile verification green:
  - `npm run build`
  - result: `vite build` success

#### Patch 5 — Guardrails + parity + closure
- run focused + full-suite checks, sync mandatory docs, close A2.84.

Patch 5 artifacts:
- pending

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — Act read-only execution seam
- [x] Patch 3 — failure-policy and reason-code closure
- [x] Patch 4 — UI mode/block transparency
- [ ] Patch 5 — guardrails + closure

### Non-Negotiable Rules

- Keep Act execution strictly read-only in A2.84.
- Preserve `/answer` contract compatibility and controlled fallback behavior.
- Keep diagnostics deterministic with explicit reason-codes.
- One patch = one reason.

### Out of Scope

Do NOT modify during A2.84:

- write-path tool execution / side-effectful actions,
- policy profile matrix expansion (`prod_strict`/`dev_guided`/`dev_full`),
- EvolutionAgent loop implementation,
- unrelated product or architecture refactors.

### Definition of Done

A2.84 is complete when:

- Act read-only execution works through explicit allowlist,
- blocked actions return stable reason-codes with no uncontrolled 500 on user path,
- UI surfaces runtime mode + block reason instead of opaque failure,
- focused and full quality checks remain green,
- mandatory docs are synchronized.

## A2.83 Step 0.5 Snapshot (Closed)

A2.83 closure markers retained for continuity:

- mode router seam (`runtime_mode_*` reason-code fallback behavior),
- controlled runtime fallback seam (`answer_runtime_controlled_fallback`),
- response presenter seam (`diagnostics.presentation` compact/full),
- full-suite parity: `581 passed, 3 skipped`.

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

TBD - Post-A2.84 planning

## Anchor Closed

A2.83 Step 0.5 complete - Facade stabilization before Act/Evolve with mode/failure/presenter seams.

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first,
- execution seam second,
- failure/policy closure third,
- UI transparency fourth,
- guardrails and closure last.
