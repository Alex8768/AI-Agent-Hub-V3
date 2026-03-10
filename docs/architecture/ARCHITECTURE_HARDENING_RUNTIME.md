# Architecture Hardening Runtime (A2.45)

## Purpose

`A2.45` introduces architecture hardening primitives for the COO runtime without
changing user-facing behavior. The anchor focuses on deterministic boundaries,
planner coupling risk reduction, and memory consistency visibility.

This milestone provides:

- AnswerService runtime-context boundary seam;
- planner coupling guardrail via a reasoning adapter abstraction seam;
- memory consistency diagnostics contract in answer debug snapshots;
- technical-debt registry for legacy/temporary runtime artifacts;
- docs + CI quality-gate closure.

## Contracts

Assistant contract version: `v1`
Memory consistency contract version: `v1`

Primary diagnostics contracts:

- `assistant_contract_version`
- `planning_reason_codes`
- `memory_consistency`
- `memory_consistency.contract_version`
- `memory_consistency.mode`
- `memory_consistency.status`
- `memory_consistency.inputs`
- `memory_consistency.reason_codes`

## AnswerService boundary hardening

Runtime context is normalized through an explicit seam:

- `_build_answer_service_runtime_context`

This keeps feature-flag resolution deterministic and local to orchestrator
bootstrap, reducing implicit coupling in request handling flow.

## Planner coupling guardrail

Reasoning engine binding now passes through a guarded abstraction seam:

- `_build_reasoning_runtime_adapter`

Guardrail behavior:

- validates runtime factory callability;
- requires adapter `synthesize` capability;
- forces safe fallback (`None`) when adapter contract is invalid.

## Memory consistency diagnostics guardrails

Debug snapshots now include an explicit memory consistency bundle:

- `_build_memory_consistency_bundle`
- `memory_consistency`
- `memory_consistency_guard_evaluated`
- `memory_consistency_store_unavailable`
- `memory_consistency_session_hit`
- `memory_consistency_durable_approval_loaded`
- `memory_consistency_durable_idempotency_loaded`

These signals are diagnostics-only and deterministic.

## Technical debt registry linkage

Architecture hardening requires explicit debt tracking:

- `docs/development/TECHNICAL_DEBT_REGISTRY.md`

Registry includes debt IDs, ownership, risk, decision status, and planned
resolution anchor.

## Feature flags

Hardening behavior remains under existing assistant/runtime controls:

- `feature_reasoning_api=false`
- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for seams/guardrails/contracts;
- technical-debt registry markers and required fields;
- README and roadmap references for A2.45 hardening docs quality gate.
