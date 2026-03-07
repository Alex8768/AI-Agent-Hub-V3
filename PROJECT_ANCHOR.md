# Project Anchor

## Active Anchor

A2.8 — Config Architecture Cleanup

### Goal

Simplify config structure and ownership boundaries while preserving runtime defaults and compatibility.

A2.8 must split config responsibilities into smaller units without behaviour drift.

### Patch Plan

#### Patch 0 — Extract LLM config builders
- Isolate LLM provider requirements validation from `get_llm_config()`
- Isolate LLM provider config map assembly
- Preserve fail-fast and fallback behavior

#### Patch 1 — Extract vector store config builders
- Isolate vector provider config assembly from `get_vector_store_config()`
- Keep defaults and fallback behavior unchanged

#### Patch 2 — Extract feature-flag normalization boundary
- Isolate deprecated alias normalization/consistency logic
- Preserve validation semantics

#### Patch 3 — External contract parity tests
- Freeze config-level behavior contracts for core getters
- Prove no regressions from decomposition

### Progress

- [x] Patch 0 — LLM config builders extracted with parity
- [ ] Patch 1 — extract vector store config builders
- [ ] Patch 2 — extract feature-flag normalization boundary
- [ ] Patch 3 — external contract parity tests

### Out of Scope

Do NOT modify during A2.8:
- IngestService slimming
- retrieval pipeline redesign
- reasoning graph redesign beyond active-patch need
- AnswerService decomposition beyond closed A2.6
- OpenAIAdapter decomposition beyond closed A2.7

### Definition of Done

A2.8 is complete when:
- config responsibilities are split into focused units
- runtime defaults and compatibility remain unchanged
- behavior parity is validated by tests
