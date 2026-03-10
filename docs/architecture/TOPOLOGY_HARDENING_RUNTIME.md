# Topology Hardening Runtime (A2.46)

## Purpose

`A2.46` formalizes strict architectural zoning to prevent reasoning-core overpacking
while preserving runtime parity for the existing assistant and reasoning surfaces.

This anchor locks capability ownership into canonical homes:

- `kernel/`
- `governance/`
- `extensions/`
- `execution_plane/`
- `knowledge_plane/`
- `platform_ops/`
- `interface/`

## Contracts and seams

Reasoning kernel seam:

- `build_reasoning_kernel`

Governance subcore seam:

- `build_governance_subcore_bundle`

Execution request boundary seam:

- `normalize_execution_request`
- `build_execution_request_boundary_bundle`

Diagnostics contract introduced in A2.46 patch 4:

- `execution_request_boundary`

## Dependency directions

Allowed directions:

- `interface -> execution_plane -> kernel`
- `execution_plane -> governance`
- `extensions -> kernel`
- `platform_ops -> governance`
- `knowledge_plane -> kernel`

Forbidden directions:

- `kernel -> execution_plane`
- `kernel -> interface`
- `governance -> interface`
- `extensions -> execution side-effects`

## Dependency quality gates

Topology dependency drift is blocked by:

- `tests/unit/layers/pro/test_reasoning_topology_dependency_quality_gate.py`

Runtime/docs closure is validated by:

- `tests/unit/docs/test_topology_hardening_runtime_quality_gate.py`

## Non-negotiable rules

- Kernel stays minimal.
- Reasoning never acts directly.
- One capability = one architectural home.
- No net-new intelligence features during topology hardening.
- Runtime parity is preserved during extraction.

## Feature flags

Topology hardening keeps default-safe assistant behavior unchanged:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`
