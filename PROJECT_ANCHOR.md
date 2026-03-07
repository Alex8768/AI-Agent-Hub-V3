# Project Anchor

## Active Anchor

A2.9 — IngestService Slimming

### Goal

Reduce `IngestService` orchestration complexity while preserving ingest behavior and external contracts.

A2.9 must split ingest responsibilities into smaller units without behaviour drift.

### Patch Plan

#### Patch 0 — Extract metadata preparation boundary
- Isolate metadata shaping/defaulting from ingest orchestration
- Preserve existing metadata fields and defaults

#### Patch 1 — Extract chunking boundary
- Isolate text chunking setup/invocation from ingest orchestration
- Preserve chunk count/content behavior

#### Patch 2 — Extract vector persistence boundary
- Isolate vector upsert/persist boundary from ingest orchestration
- Preserve best-effort/error semantics

#### Patch 3 — External contract parity tests
- Freeze ingest service behavior contracts and snapshots
- Prove no regressions from decomposition

### Progress

- [ ] Patch 0 — extract metadata preparation boundary
- [ ] Patch 1 — extract chunking boundary
- [ ] Patch 2 — extract vector persistence boundary
- [ ] Patch 3 — external contract parity tests

### Out of Scope

Do NOT modify during A2.9:
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need
- AnswerService decomposition beyond closed A2.6
- OpenAIAdapter decomposition beyond closed A2.7
- config architecture cleanup beyond closed A2.8

### Definition of Done

A2.9 is complete when:
- ingest responsibilities are split into focused units
- ingest behavior and contracts remain unchanged
- behavior parity is validated by tests
