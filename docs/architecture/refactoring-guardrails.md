# Refactoring Guardrails

## Purpose

This document defines non-negotiable architecture guardrails for decomposition work.
The goal is to stop monolith growth and enforce role-bounded modules.

## No-Growth Rule

- New feature logic must not be added to existing monolith files.
- Monolith files may only receive:
  - extraction changes,
  - thin-facade changes,
  - parity-safe wiring updates.
- Every patch must reduce or hold monolith complexity; no growth is allowed.

## Responsibility Separation Rules

- Facade calls policy/orchestrators and must not contain policy decisions.
- Policy decides and must not format response payloads.
- Assembler builds response payloads and must not make product decisions.
- Diagnostics describe outcomes and must not control business flow.
- Provider-specific logic must not live in application facades.
- Feature-flag matrices must move into dedicated gate/policy modules once branching grows.

## Size Budgets

### File-level budgets

- Facade/entrypoint: target <= 180 lines, warning > 250, red > 350.
- Orchestrator: target <= 220 lines, warning > 300, red > 400.
- Policy/Mapper/Builder/Formatter: target <= 150 lines, warning > 220, red > 300.
- Models/constants/enums may exceed these budgets when justified by bounded context.

### Function-level budgets

- Function target <= 30 lines, warning > 45, red > 70.
- Keep nesting depth <= 2.
- Avoid try/except-heavy control flow.
- Avoid large boolean control matrices in one function.

## Dependency Budgets

- Orchestrator modules should keep local logic imports within 7-9.
- Orchestrator modules should keep explicit infrastructure dependencies to at most 1.
- If one orchestrator knows retrieval, reasoning, execution, diagnostics, response formatting,
  tracing, and security simultaneously, it must be split.

## Extraction Checklist

- Public API parity preserved.
- Runtime behavior parity preserved.
- Diagnostics/debug payload parity preserved.
- No new business logic added to monolith file.
- Responsibility boundaries are explicit in new modules.
- Import direction remains acyclic and layer-safe.

## PR Acceptance Rules

PRs are accepted only when:

- behavior and public contracts stay stable,
- tests are green,
- extracted modules have clear single responsibility,
- monolith file size/complexity is reduced or held,
- no generic helper dump module is introduced.

PRs are rejected when:

- file split is mechanical (part1/part2/helpers dump),
- cyclic imports appear,
- facade still owns all decisions,
- policy formats response payloads,
- diagnostics starts controlling pipeline flow.
