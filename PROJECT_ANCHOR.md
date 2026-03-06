# PROJECT ANCHOR

## Project
AI Agent Hub v3.1-dev

## Mission
Создать стабильную платформу AI Agent Hub с архитектурой Base → Pro → Reasoning.

## Current Development Goal
Стабилизировать Base слой перед развитием Pro.

## Current Stage
Phase 0 — Base stabilization.

## Approved Roadmap

1. Phase 0 — Stabilize Base
2. Phase 1 — Graph RAG MVP
3. Phase 2 — Reasoning MVP
4. Phase 3 — MCP Tools
5. Phase 4 — API expansion
6. Phase 5 — Multi-Agent (после стабилизации)
7. Phase 6 — Canvas / Visualization
8. Phase 7 — Personalization / Memory

## Critical Path

1. Lifespan + API dependencies
2. FAISS thread safety
3. JSON metadata instead of pickle
4. OpenAIAdapter cleanup
5. Graph schema
6. Hybrid retrieval
7. Planner + reasoning
8. Self-check verification

## Non-negotiable rules

- Один патч = одна причина
- Compile -> pytest -> commit
- Не смешивать архитектурные изменения
- Новые Pro функции только под feature flags
- Новый код не должен напрямую импортировать глобальный settings

## Current Focus

Phase 0 — Base stabilization

First anchor:
Lifespan + API dependencies

## How to resume work in a new chat

1. Read PROJECT_ANCHOR.md
2. Read STATUS.md
3. Read PROJECT_CHECKLIST.md
4. Only then analyze code.

Do NOT redesign roadmap from scratch.
