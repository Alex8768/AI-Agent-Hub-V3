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
| feature_qdrant | Pro vector store (Qdrant) | ✅ MVP |
| feature_acl | Role-based workspace ACL | ✅ MVP |
| feature_memory | Durable DB-backed memory | ✅ MVP |
| feature_graphrag | Graph layer (nodes/edges) | ✅ MVP |

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

