# Project Anchor

## Active Anchor

A2.4 — Self-check Diagnostics Rollout

### Goal

Introduce deterministic reasoning diagnostics without changing answer behaviour first.

A2.4 must be delivered in a controlled rollout:
1. prove planner runtime path behaves correctly
2. introduce diagnostics-only self_check
3. add warning-only policy
4. tune thresholds
5. stabilize the external contract

### Patch Plan

#### Patch 0 — Preflight planner runtime parity
- Prove planner/runtime path actually executes
- Validate invoke / ainvoke compatibility
- Ensure fallback does not silently mask planner runtime issues
- Explicit test coverage for:
  - compile + ainvoke path
  - compile + invoke path
  - runtime without ainvoke/invoke -> controlled fallback with diagnostics

#### Patch 1 — Diagnostics-only self_check
- Introduce diagnostics.self_check
- Deterministic and stable structure
- Pre-freeze schema with status: "not_evaluated" to prevent API drift
- No influence on final answer
- No routing changes
- No blocking behaviour

#### Patch 2 — Warning-only policy
- Convert failed self-check conditions into warning-level diagnostics
- Final answer must still be returned
- No hard blocking
- No hidden behaviour changes

#### Patch 3 — Threshold tuning
- Introduce explicit thresholds
- Example dimensions: minimal_coverage_score, missing_minimal_count
- Add boundary tests
- Preserve predictable planner/fallback behaviour

#### Patch 4 — External contract stabilization
- Update API/service snapshot tests
- Ensure diagnostics.self_check is externally stable
- Freeze outward-facing contract for this phase

### Out of Scope

Do NOT modify during A2.4:
- AnswerService decomposition
- OpenAIAdapter decomposition
- config.py architecture cleanup
- IngestService slimming
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need

### Definition of Done

A2.4 is complete when:
- planner runtime parity is explicitly validated
- diagnostics.self_check is stable
- warning-only policy is covered by tests
- threshold behaviour is covered by boundary tests
- external API/service contract is stabilized
