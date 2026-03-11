# A2.57 Answer Decomposition Move Map

## Purpose

This move map defines how `src/services/answer/answer_service.py` responsibilities are
extracted into bounded modules under `src/services/answer/` without behavior changes.

## Scope

- extraction-only and thin-facade-only for monolith targets,
- no runtime/API contract changes,
- no net-new feature behavior.

## Target Package Skeleton

- `src/services/answer/facade.py`
- `src/services/answer/models.py`
- `src/services/answer/types.py`
- `src/services/answer/constants.py`
- `src/services/answer/context/`
- `src/services/answer/retrieval/`
- `src/services/answer/reasoning/`
- `src/services/answer/execution/`
- `src/services/answer/diagnostics/`
- `src/services/answer/response/`
- `src/services/answer/observability/`

## Responsibility Clusters and Planned Moves

### Context cluster

From `answer_service.py`:
- request/session/workspace/memory context assembly helpers,
- runtime context builders for per-request orchestration metadata.

To:
- `context/request_context_builder.py`
- `context/session_context_resolver.py`
- `context/memory_context_resolver.py`
- `context/workspace_context_resolver.py`
- `context/user_context_resolver.py`

### Retrieval cluster

From `answer_service.py` and existing retrieval-related orchestration decisions:
- retrieval enable/skip decisions,
- retrieval fallback path wiring,
- retrieval result normalization to answer-internal DTO structures.

To:
- `retrieval/retrieval_orchestrator.py`
- `retrieval/retrieval_policy.py`
- `retrieval/retrieval_filters.py`
- `retrieval/retrieval_result_mapper.py`
- `retrieval/retrieval_fallbacks.py`

### Reasoning cluster

From `answer_service.py` reasoning gates and policy helpers:
- reasoning enable/disable and mode gates,
- policy/fallback decision helpers,
- result mapping into normalized internal structures.

To:
- `reasoning/reasoning_orchestrator.py`
- `reasoning/reasoning_policy.py`
- `reasoning/reasoning_gate.py`
- `reasoning/reasoning_result_mapper.py`
- `reasoning/reasoning_fallbacks.py`

### Execution cluster

From `answer_service.py` handshake/idempotency/pilot logic:
- approval handshake transitions,
- idempotency guards and durable-execution checks,
- dangerous action gating and tool result normalization.

To:
- `execution/tool_execution_orchestrator.py`
- `execution/approval_handshake.py`
- `execution/idempotency_guard.py`
- `execution/execution_policy.py`
- `execution/tool_result_normalizer.py`
- `execution/dangerous_action_gate.py`

### Diagnostics cluster

From `answer_service.py` diagnostics and confidence assembly:
- diagnostics merge and enrichment,
- confidence/debug payload assembly,
- retrieval/reasoning/execution diagnostics stitching.

To:
- `diagnostics/diagnostics_orchestrator.py`
- `diagnostics/diagnostics_merge.py`
- `diagnostics/confidence_builder.py`
- `diagnostics/trace_enrichment.py`
- `diagnostics/execution_diagnostics.py`
- `diagnostics/retrieval_reasoning_diagnostics.py`

### Response cluster

From `answer_service.py` response assembly and formatting helpers:
- final payload assembly,
- fallback response composition,
- citation enrichment and post-processing normalization.

To:
- `response/response_assembler.py`
- `response/citation_enricher.py`
- `response/response_post_processor.py`
- `response/answer_formatter.py`
- `response/fallback_response_builder.py`

### Observability cluster

From `answer_service.py` observability/logging helpers:
- structured logging events,
- metrics/tracing helper seams for answer flow.

To:
- `observability/event_logger.py`
- `observability/metrics_recorder.py`
- `observability/tracing_helpers.py`
- `observability/structured_logging.py`

## Thin Facade End State

`facade.py` should keep:
- public service class entrypoint,
- public answer method,
- short orchestration pipeline wiring only.

`facade.py` must not keep:
- deep policy decisions,
- payload formatting logic,
- diagnostics merge/business details,
- provider-specific branching.

## Patch 3 Progress (Implemented)

- `answer_service._clip_text` moved to `context/session_text.py::clip_text`.
- `answer_service._durable_approval_record_key` moved to
  `execution/durable_keys.py::durable_approval_record_key`.
- `answer_service._durable_idempotency_record_key` moved to
  `execution/durable_keys.py::durable_idempotency_record_key`.
- `answer_service._append_planning_reason_codes` moved to
  `diagnostics/reason_codes.py::append_planning_reason_codes`.
- `answer_service.log_observability` moved to
  `observability/event_logger.py::log_observability`.
