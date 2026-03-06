# PROJECT ANCHOR

## Project
AI Agent Hub v3.1-dev

## Mission
Создать стабильную платформу AI Agent Hub с архитектурой Base -> Pro -> Reasoning.

## Current Development Goal
Стабилизировать Base слой перед развитием Pro, чтобы Pro MVP строился на прочном фундаменте, а не на скрытых проблемах.

## Current Stage
Phase 0 -> Base stabilization

## Approved Roadmap

1. Phase 0 -> Stabilize Base
2. Phase 1 -> Graph RAG MVP
3. Phase 2 -> Reasoning MVP
4. Phase 3 -> MCP Tools
5. Phase 4 -> API expansion
6. Phase 5 -> Multi-Agent (только после стабилизации single-agent ядра)
7. Phase 6 -> Canvas / Visualization
8. Phase 7 -> Personalization / Memory

## Critical Path

1. Lifespan + API dependencies
2. FAISS thread safety
3. JSON metadata instead of pickle
4. OpenAIAdapter cleanup
5. Graph schema and graph retrieval
6. Hybrid retrieval
7. Planner + reasoning flow
8. Evidence contract + self-check verification

## What is approved and should NOT be re-discussed from scratch

- Pro нельзя развивать поверх нестабильного Base.
- Сначала укрепляем фундамент, потом усложняем Pro.
- Multi-agent, canvas и глубокую персонализацию не начинаем до стабилизации single-agent ядра.
- Новый код Pro не должен напрямую тащить глобальный settings.
- Новые рискованные Pro возможности включаются только через feature flags.
- Один патч = одна причина.
- Один завершённый якорь = отдельное понятное обновление статуса.

## Non-negotiable rules

- Один патч = одна причина
- Compile -> pytest -> commit
- Не смешивать несколько архитектурных изменений в одном коммите
- Не переписывать roadmap с нуля без серьёзной причины
- Не тащить FastAPI app.state в core слой
- Не превращать core/providers.py в скрытый service locator
- Не делать create_task без управляемого жизненного цикла там, где нужна надёжность
- Не лезть в сложные расширения раньше времени

## Current Focus

Phase 0 -> Base stabilization

Current active anchor:
A0.5 Unified logging and request context

Next anchor:
A0.6 Feature flags for risky Pro capabilities

## What is explicitly postponed

- Multi-agent orchestration
- Canvas / visualization
- Deep personalization
- Full DI refactor of all legacy Base services
- Big-bang rewrite of Base

## How to resume work in a new chat

1. Read PROJECT_ANCHOR.md
2. Read STATUS.md
3. Read PROJECT_CHECKLIST.md
4. Read WORKFLOW.md
5. Only then analyze code and propose changes.

Do NOT redesign roadmap from scratch.
Do NOT skip the current anchor.
Do NOT mix multiple anchor goals in one patch.
