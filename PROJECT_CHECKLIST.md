# PROJECT CHECKLIST

Legend:
- TODO = ещё не начали
- IN_PROGRESS = текущий активный якорь
- DONE = завершено и зафиксировано
- BLOCKED = упёрлись в проблему
- DEFERRED = сознательно отложено

---

## Phase 0 — Base stabilization

### A0.1 Lifespan + API dependencies
Status: IN_PROGRESS

Why this matters:
Нужно один раз правильно создавать ключевые объекты приложения при старте FastAPI и отдавать их через API-зависимости. Это убирает костыли, уменьшает путаницу и создаёт чистую точку сборки для Pro.

Done when:
- storages и registry создаются в bootstrap / lifespan
- API получает их через deps.py
- core не зависит от FastAPI app.state
- новый Pro код не использует core/providers.py как скрытый service locator

---

### A0.2 FAISS thread safety
Status: TODO

Why this matters:
Индекс не должен зависать, конфликтовать сам с собой или блокировать приложение. Сначала делаем retrieval-ядро безопасным, потом строим умные надстройки.

Done when:
- операции add / search / save идут через executor
- есть lock на опасные участки
- нет гонок между параллельными вызовами
- поведение сохранения и загрузки остаётся предсказуемым

---

### A0.3 JSON metadata instead of pickle
Status: TODO

Why this matters:
Метаданные должны храниться в понятном и безопасном формате, который проще читать, проверять и переносить между версиями.

Done when:
- pickle больше не используется для метаданных
- JSON metadata используется вместо него
- есть version
- есть fingerprint / hash для связи метаданных с индексом
- загрузка старых или битых метаданных обрабатывается понятно

---

### A0.4 OpenAIAdapter cleanup
Status: TODO

Why this matters:
Нельзя строить reasoning поверх адаптера, в котором зашит устаревающий хардкод и неочевидные fallback-пути.

Done when:
- убран опасный legacy-хардкод
- fallback-поведение стало понятнее
- system / user context передаётся корректно
- адаптер меньше зависит от устаревших предположений о моделях

---

### A0.5 Unified logging and request context
Status: TODO

Why this matters:
Когда Pro начнёт усложняться, без единого контекста логов быстро начнётся хаос. Нужно заранее упростить трассировку запросов и ошибок.

Done when:
- request_id и workspace_id проходят единообразно
- ключевые операции логируются в одном стиле
- по логам можно понять путь запроса и место падения

---

### A0.6 Feature flags for risky Pro capabilities
Status: TODO

Why this matters:
Новые возможности нужно включать по рубильнику, а не выпускать сразу на весь поток. Это снижает риск случайно сломать стабильный путь.

Done when:
- ключевые Pro возможности можно включать и выключать отдельно
- risky features не активируются случайно
- rollout можно делать поэтапно

---

## Phase 1 — Graph RAG MVP

### A1.1 Graph schema and indexes
Status: TODO

Why this matters:
Чтобы граф не был медленным и бесполезным, нужна нормальная схема хранения и индексы для быстрых переходов по связям.

---

### A1.2 Chunk -> entity linkage contract
Status: TODO

Why this matters:
Нужно жёстко понимать, какой кусок текста породил какие сущности и связи. Иначе graph retrieval будет магией без объяснимости.

---

### A1.3 Entity extraction jobs
Status: TODO

Why this matters:
Извлечение сущностей должно быть управляемой фоновой задачей со статусом, а не потерянным create_task.

---

### A1.4 Graph retriever
Status: TODO

Why this matters:
Система должна уметь расширять найденный контекст через связи между сущностями, а не только искать похожие куски текста.

---

### A1.5 Hybrid retrieval
Status: TODO

Why this matters:
Нужен гибридный путь: векторный поиск даёт стартовые точки, граф расширяет и углубляет контекст.

---

## Phase 2 — Reasoning MVP

### A2.1 Session memory
Status: TODO

Why this matters:
Reasoning должен помнить полезные промежуточные выводы внутри сессии, а не каждый раз начинать почти заново.

---

### A2.2 Planner
Status: TODO

Why this matters:
Сложные задачи нужно разбивать на шаги, а не пытаться решить одним прыжком.

---

### A2.3 Evidence contract
Status: TODO

Why this matters:
Перед self-check нужно договориться, как выглядит доказательство: откуда оно пришло, что подтверждает и насколько надёжно.

---

### A2.4 Self-check
Status: TODO

Why this matters:
Ответ должен перепроверяться перед выдачей, чтобы уменьшить галлюцинации и недоказанные утверждения.

---

### A2.5 Verify node in reasoning graph
Status: TODO

Why this matters:
Проверка должна быть встроенным этапом reasoning, а не декоративной надстройкой сбоку.

---

## Phase 3 — MCP / Tools

### A3.1 Tool registry
Status: TODO

### A3.2 Safe tool servers
Status: TODO

### A3.3 Tool-aware reasoning
Status: TODO

---

## Phase 4 — API expansion

### A4.1 Graph API
Status: TODO

### A4.2 Memory API
Status: TODO

### A4.3 MCP API
Status: TODO

### A4.4 Jobs / status API
Status: TODO

---

## Phase 5 — Delayed expansions

### A5.1 Multi-agent
Status: DEFERRED

### A5.2 Canvas / visualization
Status: DEFERRED

### A5.3 Deep personalization
Status: DEFERRED
