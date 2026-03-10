# Project Anchor

## Active Anchor

A2.46 — Kernel / Extensions / Execution Plane Hardening

### Goal

Formalize strict architectural zoning and prevent reasoning-core overpacking.

This anchor introduces a canonical topology with three primary rings:

- Reasoning Kernel
- Governance Subcore / Reasoning Extensions
- Execution / Coordination Plane

Runtime parity must be preserved while ownership boundaries become explicit and enforceable.

### Why Now

Capability coverage is already broad across reasoning, governance, coordination,
tool safety, evaluation, OCR, MCP, and release policy.

The primary risk is center-of-gravity overpacking in reasoning core paths.
A2.46 addresses this by defining canonical architectural homes and dependency rules.

### Architecture Position

Planned modules:

- `kernel/`
- `governance/`
- `extensions/`
- `execution_plane/`
- `knowledge_plane/`
- `platform_ops/`
- `interface/`

Target conceptual mapping:

- Reasoning Kernel: planner, step executor, execution control, policy application, minimal contracts
- Governance Subcore: receipts, trace, replay, timeline
- Reasoning Extensions: meta-cognition, anticipatory, optimization, benchmark enrichments
- Execution / Coordination Plane: handoff, arbitration, tool safety, execution request handling

### Patch Plan

#### Patch plan
- Patch 1 — architecture zoning inventory + scope lock
- Patch 2 — kernel boundary formalization
- Patch 3 — governance subcore extraction
- Patch 4 — execution request boundary + execution plane isolation
- Patch 5 — dependency quality gates + docs closure

### Progress

- [x] Patch 1 — architecture zoning inventory + scope lock
- [x] Patch 2 — kernel boundary formalization
- [x] Patch 3 — governance subcore extraction
- [x] Patch 4 — execution request boundary + execution plane isolation
- [ ] Patch 5 — dependency quality gates + docs closure

### Patch 1 Outputs

Inventory by target home:

- `kernel/`: `src/layers/pro/reasoning/planner.py`, `step_executor.py`, `execution_policy.py`, `step_controller.py`, `contracts.py`
- `governance/`: `execution_receipt_*`, `trace_*`, `timeline_*`, replay serializers
- `extensions/`: `meta_cognition/*`, `anticipatory/*`, optimization and benchmark helpers
- `execution_plane/`: `multi_agent_*`, tool safety stack, execution handoff/orchestration bridges
- `knowledge_plane/`: retriever/memory integrations and knowledge shaping boundaries
- `platform_ops/`: release-gate policy/matrix/decision stack + CI alignment docs
- `interface/`: API endpoint adapters + UI-facing diagnostics contracts

Current cross-layer leaks to address in A2.46:

- reasoning-path orchestration ownership concentrated in `AnswerService`
- direct runtime coupling between planning and acting surfaces
- governance signals mixed into extension-heavy diagnostics paths

Allowed dependency directions:

- `interface -> execution_plane -> kernel`
- `execution_plane -> governance`
- `extensions -> kernel`
- `platform_ops -> governance`
- `knowledge_plane -> kernel`

Forbidden dependency directions:

- `kernel -> execution_plane`
- `kernel -> interface`
- `governance -> interface`
- `extensions -> execution side-effects`

### Out of Scope

Do NOT modify during planning:
- new model/provider integrations
- net-new intelligence capabilities
- OCR redesign
- major retrieval redesign
- UI feature expansion beyond topology/documentation scope
- new MCP ecosystem features
- new enterprise rollout capabilities beyond topology support

### Definition of Done

A2.46 completion criteria:
- every major subsystem has a canonical architectural home;
- kernel boundary is minimal and explicit;
- governance is represented as a distinct trusted subcore;
- reasoning-to-execution boundary is explicit and normalized;
- forbidden dependency directions are enforced by tests/gates;
- docs and topology reflect actual platform structure.

## Next Anchor

A2.47 — TBD

### Discipline

Work order is strict:
- A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25
- OCR is explicitly deferred to A2.21
- MCP expansion is deferred until post-A2.21 stabilization and later-anchor gates
- Do not mix implementation across these anchors.

### Last Completed Anchor

A2.45 — Architecture Hardening Track (COO Runtime Reliability)

Completed via patches:
- Patch 1 — Anchor Formalization + Scope Lock
- Patch 2 — AnswerService Boundary Hardening Baseline
- Patch 3 — Planner Coupling Guardrail (Abstraction Seam)
- Patch 4 — Memory Consistency Diagnostics Guardrails
- Patch 5 — Docs/CI Closure + Technical-Debt Registry
