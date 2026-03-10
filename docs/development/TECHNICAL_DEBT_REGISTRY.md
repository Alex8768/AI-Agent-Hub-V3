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
- decision_status: `accepted_for_incremental_extraction`
- owner: `architecture-track`
- target_anchor: `A2.46`
- notes: `Keep behavior stable; continue seam-based extraction only.`

### debt_id: `TD-A2.45-002`

- area: `reasoning/planner`
- description: `Planner wiring still depends on concrete runtime provider composition paths.`
- risk_level: `medium`
- decision_status: `mitigated_with_guardrail`
- owner: `architecture-track`
- target_anchor: `A2.46`
- notes: `A2.45 added guarded adapter seam; deeper decoupling deferred.`

### debt_id: `TD-A2.45-003`

- area: `memory/sqlite-qdrant`
- description: `Cross-store consistency is best-effort and not transactionally unified.`
- risk_level: `high`
- decision_status: `visibility_added_pending_strategy`
- owner: `architecture-track`
- target_anchor: `A2.46`
- notes: `A2.45 introduced memory consistency diagnostics; outbox/compensation strategy is pending.`

### debt_id: `TD-A2.45-004`

- area: `legacy-runner`
- description: `Temporary or legacy runner path (`run_utf8.py`) can cause entrypoint ambiguity.`
- risk_level: `low`
- decision_status: `pending_cleanup_decision`
- owner: `architecture-track`
- target_anchor: `A2.46`
- notes: `Main runtime entrypoint is `src.api.main:app`; remove/retain decision deferred.`
