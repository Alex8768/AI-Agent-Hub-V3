# Assistant Runtime (A2.34)

## Purpose

This document defines the assistant runtime contracts introduced in A2.34 and
the default-safe rollout posture.

## Contracts

- Assistant contract version: `v1`
- Response modes:
  - `strict_rag`
  - `assistant_fallback`
  - `draft_orchestration`
- Draft action contract:
  - `action_id`
  - `action_type`
  - `status=draft`
  - `requires_confirmation=true`
  - `preview`
  - `rollback_plan`

## Feature Flags (default OFF)

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

## Runtime Behavior

- Language-native assistant fallback is used only when assistant mode is enabled
  and retrieval evidence is empty.
- Proactive suggestions are ranked deterministically by priority and rank.
- Draft actions are review-before-execute only; no side effects are performed
  until explicit confirmation.

## Diagnostics Surface

`/api/v1/answer` diagnostics include:

- `assistant_contract_version`
- `response_mode`
- `response_language`
- `assistant_mode_enabled`
- `assistant_proactive_enabled`
- `assistant_actions_enabled`
- `anticipatory.proactive_suggestions`
- `anticipatory.draft_actions`

## Quality Gates

- Runtime tests:
  - `tests/unit/services/answer/test_answer_service_debug_snapshot.py`
  - `tests/unit/api/test_answer_endpoint_debug_snapshot.py`
- Documentation gate:
  - `tests/unit/docs/test_assistant_runtime_quality_gate.py`
- CI wiring:
  - `.github/workflows/ci-pro.yml` release-gate contract tests
