# Project Anchor

## Active Anchor

A2.57 - Application Decomposition Regime (Answer/Reasoning No-Growth) (Closed)

### Goal

Introduce a strict application-level decomposition regime that stops monolith growth and
enforces bounded modules for Answer and Reasoning orchestration paths.

### Why Now

A2.56 is closed and operational guardrails are stabilized.
The main residual architecture risk is centripetal growth of large files in answer/reasoning
orchestration paths without hard no-growth enforcement.

### Architecture Position

Target A2.57 boundaries:

- **Decomposition Regime**
  - enforce facade/orchestrator/policy/mapper/assembler/diagnostics separation,
  - prevent new feature logic from entering monolith files.

- **Answer Path Structure**
  - structure bounded subpackages under `src/services/answer/`,
  - keep facade thin and orchestration-only.

- **Reasoning Engine Structure**
  - structure bounded subpackages under `src/layers/pro/reasoning/`,
  - keep engine file as a thin facade with delegated responsibilities.

- **Governance**
  - enforce size/dependency budgets and no-growth rules via docs + quality gates.

### Patch Plan

#### Patch 1 — Inventory + scope lock
- inventory current responsibility clusters and file-size hotspots,
- lock scope to extraction-only and thin-facade-only changes,
- publish governance baseline in `docs/architecture/refactoring-guardrails.md`.

#### Patch 2 - Answer move-map and package scaffolding
- define exact move map for `src/services/answer/answer_service.py`,
- add target subpackage scaffolding for context/retrieval/reasoning/execution/diagnostics/response/observability,
- keep behavior unchanged.

Patch 2 artifacts:
- Move map document: `docs/architecture/answer-decomposition-move-map-a2.57.md`
- Scaffolding baseline created under `src/services/answer/`:
  - `facade.py`, `models.py`, `types.py`, `constants.py`
  - `context/`, `retrieval/`, `reasoning/`, `execution/`, `diagnostics/`, `response/`, `observability/`

#### Patch 3 - Answer heavy-cluster extraction
- extract diagnostics, response assembly, execution guards, and context resolvers into bounded modules,
- shrink monolith toward orchestration-only facade.

Patch 3 phase-1 extraction completed:
- context helper extracted:
  - `answer_service._clip_text` -> `src/services/answer/context/session_text.py::clip_text`
- execution durable key builders extracted:
  - `answer_service._durable_approval_record_key` -> `src/services/answer/execution/durable_keys.py::durable_approval_record_key`
  - `answer_service._durable_idempotency_record_key` -> `src/services/answer/execution/durable_keys.py::durable_idempotency_record_key`
- diagnostics reason-code merge helper extracted:
  - `answer_service._append_planning_reason_codes` -> `src/services/answer/diagnostics/reason_codes.py::append_planning_reason_codes`
- observability logging helper extracted:
  - `answer_service.log_observability` -> `src/services/answer/observability/event_logger.py::log_observability`

#### Patch 4 - Reasoning engine move-map and first extraction
- define and execute first safe extraction from `src/layers/pro/reasoning/engine.py`,
- prioritize evaluation/self-check/diagnostics clusters with parity preserved.

Patch 4 artifacts:
- Move map document: `docs/architecture/reasoning-decomposition-move-map-a2.57.md`
- First safe extraction delivered:
  - `engine.py` diagnostics/evaluation runtime-contract helpers extracted to
    `src/layers/pro/reasoning/diagnostics/runtime_contracts.py`
  - `ReasoningEngine` keeps compatibility wrappers delegating to extracted helpers

#### Patch 5 - Guardrails + parity + closure
- add/update deterministic guardrails for decomposition constraints,
- run focused and full-suite checks and close A2.57 with docs sync.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 - Answer move-map and package scaffolding
- [x] Patch 3 - Answer heavy-cluster extraction
- [x] Patch 4 - Reasoning engine move-map and first extraction
- [x] Patch 5 - guardrails + parity + closure

### Non-Negotiable Rules

- No net-new user-facing features during A2.57
- Preserve answer/debug runtime/API parity
- No new business logic additions inside monolith files
- Extraction-only and thin-facade-only changes in monolith targets
- Keep decomposition changes deterministic and scoped
- One patch = one reason

### Out of Scope

Do NOT modify during A2.57:

- unrelated product feature logic
- endpoint contract shape
- non-target services outside answer/reasoning decomposition scope
- opportunistic cross-domain cleanups

### Definition of Done

A2.57 is complete when:

- answer and reasoning monolith growth is explicitly frozen by governance rules
- extraction move maps are completed for targeted responsibility clusters
- target facades are thinner and orchestration-focused
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

TBD - Post-A2.57 planning

## Post-A2.56 Maintenance

- [x] M1 — operational quality-gate compatibility fix for closed-status marker handling

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
