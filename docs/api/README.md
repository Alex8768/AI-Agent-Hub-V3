# API Documentation

## Base URL

`http://localhost:8000/api/v1`

## OpenAPI

- `http://localhost:8000/api/v1/docs` (Swagger UI, debug mode)
- `http://localhost:8000/api/v1/redoc` (ReDoc, debug mode)
- `http://localhost:8000/api/v1/openapi.json` (debug mode)

## Authentication Runtime Notes

- In debug mode (`settings.debug=True`), API dependencies allow anonymous access.
- In non-debug mode, JWT is required for dependencies that use `get_current_user`.
- Workspace-aware endpoints resolve `workspace_id` from:
  - query parameter `workspace_id`, or
  - header `X-Workspace-Id`, or
  - fallback `"default"`.

## Endpoint Contracts (Runtime Parity)

### Health

- `GET /health` -> `HealthResponse`
- `GET /api/v1/health` -> `HealthResponse` (alias)
- `GET /api/v1/health/deep` -> deep diagnostics payload

### LLM

- `POST /api/v1/llm/generate`
  - request: `LLMRequest`
  - response: `LLMResponse`
- `POST /api/v1/llm/generate-stream`
  - request: `LLMRequest`
  - response: SSE stream (`event: token`, `event: done`)

### Documents

- `POST /api/v1/documents/upload`
  - multipart form (`file`) + optional query params:
    - `chunk_size` (100..10000)
    - `chunk_overlap` (0..1000)
  - response: `DocumentOut`
- `GET /api/v1/documents`
  - query params: `skip`, `limit`, optional `status`
  - response: `list[DocumentOut]`
- `GET /api/v1/documents/{document_id}`
  - response: `DocumentDetailOut`
- `DELETE /api/v1/documents/{document_id}`
  - response: deletion status payload

### Search

- `POST /api/v1/search`
  - request: `SearchRequest`
  - response: `list[SearchResult]`
- `POST /api/v1/search-hybrid`
  - request: `SearchRequest`
  - response: `HybridSearchResponse`

### Reasoning

- `POST /api/v1/answer`
  - request: `AnswerRequest`
  - response: `AnswerResponse`

### Tools

- `GET /api/v1/tools` -> MCP discovery payload
- `GET /api/v1/tools/{tool_name}` -> tool schema
- `POST /api/v1/tools/{tool_name}/invoke` -> runtime execution payload

### Export

- `POST /api/v1/export`
  - request: `ExportRequest`
  - response: `ExportResult`
- `GET /api/v1/export/{export_id}/download`
  - response: file download

### Streaming

- `GET /api/v1/stream/{session_id}`
  - query param: `once` (`0|1`)
  - response: SSE stream

### Diagnostics

- `GET /api/v1/trace-test` -> tracing smoke payload

## Feature-Flag Defaults and API Gating

Runtime defaults in `src/core/config.py` are conservative: advanced Pro/API
surfaces are disabled unless explicitly enabled.

Default values:

- `feature_reasoning_api=false`
- `feature_reasoning=false`
- `feature_graphrag=false`
- `feature_hybrid_search_api=false`
- `feature_reasoning_llm_enabled=false`
- `feature_reasoning_llm_dry_run=false`
- `streaming_enabled=false`
- `rate_limit_enabled=false`

Endpoint gating behavior:

- `POST /api/v1/answer` requires:
  - `feature_reasoning_api=true`
  - `feature_reasoning=true`
  - `feature_graphrag=true`
- `POST /api/v1/search-hybrid` requires:
  - `feature_hybrid_search_api=true`
  - `feature_graphrag=true`
- `/api/v1/tools*` endpoints require:
  - `feature_reasoning_api=true`
- `GET /api/v1/stream/{session_id}` requires:
  - `streaming_enabled=true`

When a feature-gated endpoint is disabled, handlers return `404 Not Found`.
When streaming is disabled, streaming handler returns `400 Bad Request`.

## Schema Sources

- API transport schemas: `src/api/schemas.py`
- Reasoning request/response contracts: `src/layers/pro/reasoning/contracts.py`

## A2.33 Audit Reference

- `docs/api/A2.33_PATCH1_API_RUNTIME_AUDIT.md`

## API Docs Quality Gate

- Deterministic docs parity gate: `tests/unit/docs/test_api_docs_quality_gate.py`
- CI wiring: `.github/workflows/ci-pro.yml` (`release-gate` contract tests)
- Gate enforces:
  - runtime endpoint marker coverage for documented API surface
  - feature-flag defaults and endpoint-gating notes
  - roadmap feature-flag default-off markers parity
