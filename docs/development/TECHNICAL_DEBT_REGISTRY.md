# Technical Debt Registry

## Purpose

Track architectural/runtime debt explicitly with deterministic ownership,
decision status, and target closure anchors.

Required fields per entry:

- `debt_id`
- `area`
- `description`
- `risk_level`
- `decision_status`
- `owner`
- `target_anchor`
- `notes`

## Active Items

### debt_id: `TD-A2.45-001`

- area: `services/answer`
- description: `AnswerService remains large and includes many orchestration concerns.`
- risk_level: `medium`
- decision_status: `resolved_in_a2_47`
- owner: `architecture-track`
- target_anchor: `A2.47`
- notes: `Resolved via `_run_assistant_execution_orchestration_seam` extraction with runtime parity preserved.`

### debt_id: `TD-A2.45-002`

- area: `reasoning/planner`
- description: `Planner wiring still depends on concrete runtime provider composition paths.`
- risk_level: `medium`
- decision_status: `active_targeted_for_a2_48`
- owner: `architecture-track`
- target_anchor: `A2.48`
- notes: `A2.45 added guarded adapter seam; A2.48 is dedicated to planner composition decoupling closure.`

### debt_id: `TD-A2.45-003`

- area: `memory/sqlite-qdrant`
- description: `Cross-store consistency is best-effort and not transactionally unified.`
- risk_level: `high`
- decision_status: `resolved_in_a2_47`
- owner: `architecture-track`
- target_anchor: `A2.47`
- notes: `Resolved by explicit `memory_consistency_strategy` contract; outbox/compensation remains deferred by policy.`

### debt_id: `TD-A2.45-004`

- area: `legacy-runner`
- description: `Temporary or legacy runner path (`run_utf8.py`) can cause entrypoint ambiguity.`
- risk_level: `low`
- decision_status: `resolved_in_a2_47`
- owner: `architecture-track`
- target_anchor: `A2.47`
- notes: `Resolved by keeping `run_utf8.py` as compatibility wrapper and locking canonical entrypoint to `src.api.main:app`.`
