# Required Checks Matrix (A2.31)

## Purpose

This document defines the canonical required-checks policy flow used by the
enterprise release-gate path.

The goal is to keep required checks deterministic and convergent across:

- policy contracts in code;
- CI workflow check naming;
- release-gate report artifacts.

## Source Contracts

Primary contracts:

- `src/layers/pro/reasoning/enterprise/required_checks_policy.py`
- `src/layers/pro/reasoning/enterprise/required_checks_normalizer.py`
- `src/layers/pro/reasoning/enterprise/required_checks_matrix.py`

Core functions:

- `build_enterprise_required_checks_policy(...)`
- `normalize_enterprise_required_checks_by_profile(...)`
- `consolidate_enterprise_required_checks_matrix(...)`

## Deterministic Assembly Rules

1. Normalize workflow check inputs into canonical check names.
2. Merge policy checks with normalized workflow checks per profile.
3. Build a matrix with stable ordering (`sorted`, deduplicated lists).
4. Derive release-gate `required_checks` and `blocking_checks` from matrix
   profile entries.

This produces one source of truth for required checks in CI policy evaluation.

## CI Wiring

`/.github/workflows/ci-pro.yml` (`release-gate` job) uses this sequence:

1. Seed policy contract.
2. Normalize workflow checks by profile.
3. Consolidate matrix from policy + workflow inputs.
4. Build release-gate policy from the matrix profile.
5. Export `required_checks_matrix` into `release-gate-report.json`.

## Quality Gates

Deterministic quality tests:

- `tests/unit/layers/pro/test_reasoning_enterprise_required_checks_matrix.py`
- `tests/unit/layers/pro/test_reasoning_enterprise_required_checks_normalizer.py`
- `tests/unit/layers/pro/test_reasoning_enterprise_required_checks_consolidation_quality_gate.py`

These tests validate shape, normalization, merge rules, and deterministic output.
