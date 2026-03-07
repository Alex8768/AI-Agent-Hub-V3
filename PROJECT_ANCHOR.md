# Project Anchor

## Active Anchor

A2.7 — OpenAIAdapter Decomposition

### Goal

Reduce `OpenAIAdapter` branching complexity while preserving provider behavior and fallback compatibility.

A2.7 must split completion/streaming responsibilities into smaller testable units without behaviour drift.

### Patch Plan

#### Patch 0 — Extract completion builders
- Isolate completion object assembly from `complete()` branching
- Keep chat path and responses-fallback metadata parity
- Preserve existing request/response behavior

#### Patch 1 — Extract request parameter builders
- Isolate config merge and request params construction
- Keep defaults and None-pruning behavior unchanged

#### Patch 2 — Extract streaming boundaries
- Isolate stream iteration and final chunk synthesis
- Preserve chunk ordering and finish_reason behavior

#### Patch 3 — External contract parity tests
- Freeze adapter-level completion/streaming behavior contracts
- Prove no regressions from decomposition

### Progress

- [x] Patch 0 — completion builders extracted with behavior parity
- [x] Patch 1 — request parameter builders extracted with parity
- [x] Patch 2 — streaming boundaries extracted with parity
- [ ] Patch 3 — external contract parity tests

### Out of Scope

Do NOT modify during A2.7:
- config.py architecture cleanup
- IngestService slimming
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need
- AnswerService decomposition beyond closed A2.6

### Definition of Done

A2.7 is complete when:
- OpenAIAdapter responsibilities are split into focused units
- provider behavior and fallback compatibility remain unchanged
- behavior parity is validated by tests
