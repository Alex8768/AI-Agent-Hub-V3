# PROJECT STATUS

## Current Phase
Phase 0 -> Base stabilization

## Last Completed Anchor
A0.5 Unified logging and request context

## Current Active Anchor
A0.6 Feature flags for risky Pro capabilities

## Next Anchor
A1.1 Graph schema and indexes

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
