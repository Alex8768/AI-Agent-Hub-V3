# Project Anchor

## Active Anchor

A2.52 — AnswerService Facade Slimming

### Goal

Complete the next decomposition stage after A2.51 so that `AnswerService.handle_contract()`
is a short, explicit facade pipeline and no longer owns large post-orchestration flow blocks.

The intent of this anchor is structural and safety-focused:
- preserve runtime/API parity,
- make post-orchestration ownership explicit,
- keep diagnostics and fallback behavior deterministic and testable.

### Why Now

A2.51 closed the primary facade/orchestrator/response-assembly seams, and post-A2.51
maintenance hardened soft-failure observability and guardrails.

The next concentration point is the remaining size/complexity in `AnswerService`,
especially post-orchestration wiring and diagnostics merge steps.

A2.52 focuses on finishing facade slimming without behavior changes.

### Architecture Position

Target A2.52 boundaries:

- **Answer Facade (`AnswerService`)**
  - request contract normalization
  - orchestration + assembly invocation
  - short post-processing pipeline via extracted helpers

- **Post-Orchestration Flow Module (new seam)**
  - anticipatory/handshake/approval/idempotency wiring
  - no endpoint contract shaping

- **Diagnostics Merge Module (new seam)**
  - deterministic diagnostics wiring/merge/fallback reason-code propagation
  - no runtime flow coordination

### Patch Plan

#### Patch 1 — Inventory + scope lock
- Build explicit inventory of remaining `AnswerService` responsibilities after A2.51.
- Define extraction targets for:
  - post-orchestration flow,
  - diagnostics merge/wiring,
  - fallback/recovery helpers.
- Define allowed/forbidden dependency directions for new seams.

#### Patch 2 — Post-orchestration seam extraction
- Extract anticipatory/handshake/approval/idempotency wiring block from facade.
- Keep output parity and existing reason-code behavior.

#### Patch 3 — Diagnostics merge seam extraction
- Extract diagnostics wiring/merge logic into dedicated helper/module.
- Keep deterministic diagnostics key-set parity.

#### Patch 4 — Facade pipeline cleanup
- Reduce `handle_contract()` to short readable pipeline (5-8 explicit steps).
- Keep orchestrator and response assembly responsibilities unchanged.

#### Patch 5 — Guardrails + parity + closure
- Add/extend quality gates for new seams and exception policy.
- Run parity-focused tests and full suite.
- Close docs/checklist/status/features sync for A2.52.

### Progress

- [x] Patch 1 — inventory + scope lock
- [x] Patch 2 — post-orchestration seam extraction
- [x] Patch 3 — diagnostics merge seam extraction
- [x] Patch 4 — facade pipeline cleanup
- [x] Patch 5 — guardrails + parity + closure

### Non-Negotiable Rules

- No net-new intelligence features during A2.52
- Preserve answer/debug output parity
- Keep `AnswerService` thin
- Orchestrator coordinates but does not format API/debug output
- Response assembly shapes output but does not own runtime flow
- One patch = one reason

### Out of Scope

Do NOT modify during A2.52:

- planner/kernel topology
- new tool safety capabilities
- new multi-agent capabilities
- OCR redesign
- MCP ecosystem expansion
- UI feature expansion unrelated to answer-path structure
- product/marketing README work

### Definition of Done

A2.52 is complete when:

- remaining `AnswerService` responsibilities are explicitly zoned
- post-orchestration and diagnostics merge seams are extracted
- `handle_contract()` is a short facade pipeline
- answer/debug output parity is preserved
- dependency and parity quality gates cover the new seams

Closure status:
- A2.52 closed; all patch milestones completed.

## Next Anchor

TBD — Post-A2.52 planning

### Discipline

Work order is strict:

- inventory first
- extraction second
- guardrails immediately after each seam move
- preserve runtime parity
- no opportunistic feature work
