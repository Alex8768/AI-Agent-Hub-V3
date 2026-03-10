# AI Agent Hub — Pro v3.1 (Milestone: pro-v3.1.0-dev.0)

## Стратегия

Base (stable, production-safe)
↓
Pro (feature-flagged extensions)
↓
Enterprise-ready orchestration layer

Все Pro-возможности отключены по умолчанию.
Base поведение не меняется при выключенных флагах.

---

## Feature Flags

| Flag | Назначение | Статус |
|------|------------|--------|
| feature_qdrant | Pro vector store (Qdrant) | ✅ MVP (default OFF) |
| feature_acl | Role-based workspace ACL | ✅ MVP (default OFF) |
| feature_memory | Durable DB-backed memory | ✅ MVP (default OFF) |
| feature_memory_embeddings | Semantic memory embedding index | ✅ MVP (default OFF) |
| feature_graphrag | Graph layer (nodes/edges) | ✅ MVP (default OFF) |
| feature_reasoning | Reasoning synthesis layer | ✅ MVP (default OFF) |
| feature_reasoning_api | `/api/v1/answer` and `/api/v1/tools*` API surface | ✅ MVP (default OFF) |
| feature_hybrid_search_api | `/api/v1/search-hybrid` API surface | ✅ MVP (default OFF) |
| feature_reasoning_llm_enabled | Real LLM calls in reasoning pipeline | ✅ MVP (default OFF) |
| feature_reasoning_llm_dry_run | Deterministic dry-run reasoning LLM mode | ✅ MVP (default OFF) |
| feature_assistant_mode | Assistant-native fallback/runtime mode | ✅ MVP (default OFF) |
| feature_assistant_proactive | Proactive suggestion ranking runtime | ✅ MVP (default OFF) |
| feature_assistant_actions | Review-before-execute draft actions | ✅ MVP (default OFF) |

Alias compatibility:
- `feature_graph_rag` is deprecated alias for `feature_graphrag` and should not be used as canonical config.

---

## Providers Facade

Единая точка расширения:

- get_vector_store()
- get_authorizer()
- get_memory_store()
- get_graph_store()

Позволяет:
- переключать реализацию без изменения API
- изолировать Base от Pro
- безопасно расширять архитектуру

---

## Pro Components (MVP)

### 1️⃣ Qdrant Adapter
- Async client
- Hosted CI integration
- Feature-flag routing

### 2️⃣ ACL Authorizer
- Workspace-level authorization
- Feature-flag gated
- Enforcement в dependencies_impl.py

### 3️⃣ Memory Store
- DB-backed SQLite implementation
- Feature-flag routing
- Tested with temp DB

### 4️⃣ GraphRAG
- GraphNode / GraphEdge models
- DB-backed GraphStore
- BFS neighbors expansion
- Search by name/id

---

## CI

- Base CI (CPU hosted)
- Pro CI (Qdrant service container)
- Integration tests gated by env flag
- Required-checks matrix consolidation for release-gate policy (A2.31)
- API docs deterministic quality gate in release-gate contracts (A2.33)
- Assistant runtime docs quality gate in release-gate contracts (A2.34)
- Intent-to-plan orchestrator docs quality gate in release-gate contracts (A2.35)
- Confirmation handshake runtime docs quality gate in release-gate contracts (A2.36)
- Approval execution gateway runtime docs quality gate in release-gate contracts (A2.37)
- Durable approval recovery runtime docs quality gate in release-gate contracts (A2.38)
- Controlled execution pilot runtime docs quality gate in release-gate contracts (A2.39)

---

## Architectural Guarantees

- Base is not modified by Pro flags
- All Pro logic behind providers facade
- All Pro features covered by unit tests
- Milestone tagged (pro-v3.1.0-dev.0)

---

## Next Steps (v3.1.x)

- Graph extraction pipeline (LLM-based entity extraction)
- Vector → Graph hybrid retrieval
- Memory embedding + semantic recall
- ACL roles + policy model
- Observability for Pro components
- Performance benchmarking

---

## Definition of Done for Pro Layer

- Feature flags ON/OFF safe
- CI green
- Tests covering:
  - vector
  - acl
  - memory
  - graph
- Tagged milestone
- No Base regression

