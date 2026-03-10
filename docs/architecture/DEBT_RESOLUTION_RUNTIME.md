# Debt Resolution Runtime (A2.47)

## Purpose

`A2.47` closes the post-topology debt track with strict runtime parity and
no net-new intelligence capability.

This anchor resolves:

- oversized orchestration concentration in `AnswerService`
- memory consistency strategy ambiguity for SQLite + Qdrant integration
- runtime entrypoint ambiguity around `run_utf8.py`

## Debt closure outcomes

Resolved debt items:

- `TD-A2.45-001`
- `TD-A2.45-003`
- `TD-A2.45-004`

Tracked residual item (still active):

- `TD-A2.45-002`

## Runtime seams and contracts

Answer orchestration seam:

- `_run_assistant_execution_orchestration_seam`

Memory consistency strategy contract:

- `_build_memory_consistency_strategy_contract`
- `memory_consistency_strategy`

Entrypoint decision:

- `run_utf8.py` retained as compatibility wrapper only
- canonical entrypoint remains `src.api.main:app`

## CI and quality gates

A2.47 closure is guarded by:

- `tests/unit/docs/test_debt_resolution_runtime_quality_gate.py`
- `tests/unit/core/test_runtime_entrypoint_compat_runner.py`

## Feature flags

Debt closure preserves default-safe assistant behavior:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`
