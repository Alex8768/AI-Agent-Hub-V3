# PROJECT STATUS

## Current Phase
Phase 0 -> Base stabilization

## Last Completed Anchor
A1.3 Entity extraction jobs

## Current Active Anchor
A1.4 Graph retriever

## Next Anchor
A1.5 Hybrid retrieval

## Current Goal
Подготовить устойчивую и понятную базу для развития Pro слоя без архитектурного хаоса.

## What is being protected right now
- Чистая граница между API и core
- Управляемая инициализация зависимостей
- Предсказуемый маршрут развития Pro

## Notes
Project architecture:
Base -> Pro -> Reasoning

Workflow:
autopatch -> compile -> pytest -> commit

Important:
не смешивать несколько якорей в одном патче.
