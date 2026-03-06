# PROJECT CHECKLIST

## Phase 0 — Base stabilization

### A0.1 Lifespan + API dependencies
Status: TODO
Goal:
Создать правильную инициализацию storages при запуске FastAPI.

Done when:
- storages создаются в bootstrap/lifespan
- API получает их через deps.py
- core не зависит от FastAPI

---

### A0.2 FAISS thread safety
Status: TODO
Goal:
Сделать работу FAISS безопасной для многопоточности.

Done when:
- операции add/search/save идут через executor
- есть lock
- нет гонок

---

### A0.3 JSON metadata instead of pickle
Status: TODO
Goal:
Сделать хранение метаданных безопасным и читаемым.

Done when:
- pickle удалён
- JSON metadata используется
- есть version + fingerprint

---

### A0.4 OpenAIAdapter cleanup
Status: TODO
Goal:
Убрать устаревший хардкод и сделать адаптер стабильным.

Done when:
- убран legacy fallback
- system/user context корректен
- код не зависит от устаревших моделей

---

## Phase 1 — Graph RAG

### A1.1 Graph schema
Status: TODO

### A1.2 Entity extraction jobs
Status: TODO

### A1.3 Graph retriever
Status: TODO

### A1.4 Hybrid retrieval
Status: TODO

---

## Phase 2 — Reasoning

### A2.1 Session memory
Status: TODO

### A2.2 Planner
Status: TODO

### A2.3 Evidence contract
Status: TODO

### A2.4 Self-check
Status: TODO
