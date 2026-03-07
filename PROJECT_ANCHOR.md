# Project Anchor

## Active Anchor

A2.6 — AnswerService Decomposition

### Goal

Reduce `AnswerService` orchestration complexity while preserving external contracts.

A2.6 must split responsibilities into smaller testable units without behaviour drift.

### Patch Plan

#### Patch 0 — Extract diagnostics builder
- Isolate diagnostics assembly from endpoint orchestration
- Keep output schema identical
- Preserve current warnings and metadata fields

#### Patch 1 — Extract memory I/O boundary
- Isolate load/save session memory behavior
- Keep best-effort semantics unchanged

#### Patch 2 — Extract LLM wiring boundary
- Isolate provider/model resolution and adapter creation
- Preserve current fallback behavior

#### Patch 3 — External contract parity tests
- Freeze API/service snapshots for unchanged output shape
- Prove no regressions from decomposition

### Out of Scope

Do NOT modify during A2.6:
- OpenAIAdapter decomposition
- config.py architecture cleanup
- IngestService slimming
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need

### Definition of Done

A2.6 is complete when:
- AnswerService responsibilities are split into focused units
- API/service external contracts remain unchanged
- behavior parity is validated by tests
