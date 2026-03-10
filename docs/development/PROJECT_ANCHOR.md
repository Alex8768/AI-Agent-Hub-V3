# Project Anchor

## Active Anchor

A2.51 — Answer Orchestration Decomposition

### Goal

Decompose the current answer path into explicit orchestration layers so that `AnswerService`
becomes a thin facade rather than a concentration point for interface shaping,
runtime orchestration, diagnostics formatting, and response assembly.

The intent of this anchor is structural:
- keep runtime behavior stable,
- preserve current answer/debug contracts,
- make ownership inside the answer path explicit and testable.

### Why Now

The platform has already completed:

- kernel / extensions / execution-plane topology hardening
- planner / composition residual decoupling
- governance and execution boundary formalization

The next highest-complexity concentration point is the answer path.

A2.51 addresses that by separating:
- request normalization / facade concerns
- orchestration flow
- response shaping / diagnostics exposure

### Architecture Position

Target answer-path topology:

- **Answer Facade**
  - accepts request DTO
  - performs minimal validation / normalization
  - delegates to orchestrator
  - returns normalized response DTO

- **Answer Orchestrator**
  - coordinates knowledge / reasoning / execution-plane flow
  - does not own API formatting concerns
  - produces normalized answer outcome

- **Answer Response Assembly**
  - confidence shaping
  - warnings shaping
  - diagnostics/debug snapshot shaping
  - response DTO mapping

Planned files/modules (conceptual):
- `src/services/answer/answer_service.py` (thin facade target)
- `src/services/answer/orchestrator.py`
- `src/services/answer/response_assembly.py`

Exact filenames may vary if existing structure suggests a cleaner fit.

### Patch Plan

#### Patch 1 — Answer path inventory + scope lock
- Create an inventory of current answer-path responsibilities.
- Assign each current responsibility to target home:
  - facade
  - orchestrator
  - response assembly
- Define allowed / forbidden dependencies for the answer path.

#### Patch 2 — Orchestrator seam extraction
- Extract runtime orchestration flow into an explicit orchestrator component.
- Ensure the facade no longer owns flow coordination details.

#### Patch 3 — Response assembly extraction
- Extract confidence / warnings / diagnostics shaping into response-assembly logic.
- Keep API/debug output parity stable.

#### Patch 4 — Interface contract cleanup
- Ensure endpoint/service boundary depends only on stable request/response contracts.
- Remove accidental runtime-detail leakage into API-facing layer.

#### Patch 5 — Dependency / parity / quality gates
- Add deterministic guardrails for answer-path layering.
- Add parity tests to ensure no behavioral drift in answer/debug outputs.
- Close docs/checklist/status for A2.51.

### Progress

- [x] Patch 1 — answer path inventory + scope lock
- [x] Patch 2 — orchestrator seam extraction
- [x] Patch 3 — response assembly extraction
- [x] Patch 4 — interface contract cleanup
- [x] Patch 5 — dependency / parity / quality gates

### Non-Negotiable Rules

- No net-new intelligence features during A2.51
- Preserve answer/debug output parity
- Keep `AnswerService` thin
- Orchestrator coordinates but does not format API/debug output
- Response assembly shapes output but does not own runtime flow
- One patch = one reason

### Out of Scope

Do NOT modify during A2.51:

- planner/kernel topology
- new tool safety capabilities
- new multi-agent capabilities
- OCR redesign
- MCP ecosystem expansion
- UI feature expansion unrelated to answer-path structure
- product/marketing README work

### Definition of Done

A2.51 is complete when:

- answer-path responsibilities are explicitly zoned
- `AnswerService` is reduced to thin facade responsibilities
- orchestration flow is isolated in explicit orchestrator logic
- response shaping / diagnostics shaping are isolated from runtime flow
- endpoint-facing layer depends only on stable contracts
- dependency and parity tests protect the decomposition from regression

## Next Anchor

TBD — Post-A2.51 planning

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
