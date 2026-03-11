# A2.57 Reasoning Decomposition Move Map

## Purpose

This move map defines the first decomposition steps for `src/layers/pro/reasoning/engine.py`
with strict behavior parity and thin-facade direction.

## Scope

- extraction-only for `engine.py`,
- no change to public `ReasoningEngine` behavior/contracts,
- no planner/response behavior changes in this patch.

## Target Structure

- `src/layers/pro/reasoning/engine.py` (thin facade trajectory)
- `src/layers/pro/reasoning/planner/`
- `src/layers/pro/reasoning/synthesis/`
- `src/layers/pro/reasoning/evaluation/`
- `src/layers/pro/reasoning/self_check/`
- `src/layers/pro/reasoning/diagnostics/`
- `src/layers/pro/reasoning/fallback/`

## Patch 4 Implemented Extraction

Diagnostics/evaluation runtime-contract helpers moved from `engine.py` into:

- `src/layers/pro/reasoning/diagnostics/runtime_contracts.py`

Extracted helpers:

- `_evidence_summary` -> `evidence_summary`
- `_evidence_contract_status` -> `evidence_contract_status`
- `_evidence_contract_gate_reason` -> `evidence_contract_gate_reason`
- `_self_check_diagnostics` -> `self_check_diagnostics`
- `_verify_diagnostics_preflight` -> `verify_diagnostics_preflight`
- `_build_planner_runtime_parity_diagnostics` -> `build_planner_runtime_parity_diagnostics`

`ReasoningEngine` keeps static methods as compatibility wrappers that delegate to extracted
helpers, preserving call sites and test contracts.

## Next Extractions (Patch 5+)

- move quality-retry/evaluation helpers into `evaluation/`,
- move self-check decision flow into `self_check/`,
- move synthesis/fallback branching into dedicated `synthesis/` and `fallback/`.
