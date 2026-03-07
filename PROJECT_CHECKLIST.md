# Project Checklist

## Completed

- [x] Base Layer stabilization
- [x] Hybrid Retrieval pipeline
- [x] Reasoning Engine initial implementation
- [x] A2.3 Evidence Contract
- [x] A2.4 Self-check Diagnostics Rollout
- [x] A2.5 Verify Node Hardening
- [x] CI tracing compatibility fix

## Current Work — A2.6 AnswerService Decomposition

- [x] Patch 0 — extract diagnostics builder with parity
- [ ] Patch 1 — extract session memory I/O boundary
- [ ] Patch 2 — extract LLM wiring boundary
- [ ] Patch 3 — external contract parity snapshots

## Next

- [ ] A2.7 OpenAIAdapter Decomposition

## Later

- [ ] A2.8 Config Architecture Cleanup
- [ ] A2.9 IngestService Slimming

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
