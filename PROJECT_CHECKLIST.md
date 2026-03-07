# Project Checklist

## Completed

- [x] Base Layer stabilization
- [x] Hybrid Retrieval pipeline
- [x] Reasoning Engine initial implementation
- [x] A2.3 Evidence Contract
- [x] A2.4 Self-check Diagnostics Rollout
- [x] A2.5 Verify Node Hardening
- [x] CI tracing compatibility fix
- [x] A2.6 AnswerService Decomposition
- [x] A2.7 OpenAIAdapter Decomposition

## Current Work — A2.8 Config Architecture Cleanup

- [x] Patch 0 — extract LLM config builders with parity
- [ ] Patch 1 — extract vector store config builders
- [ ] Patch 2 — extract feature-flag normalization boundary
- [ ] Patch 3 — external contract parity snapshots

## Next

- [ ] A2.9 IngestService Slimming

## Later

- [ ] A2.9 IngestService Slimming

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
