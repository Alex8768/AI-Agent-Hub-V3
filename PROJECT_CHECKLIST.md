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

## Current Work — A2.7 OpenAIAdapter Decomposition

- [x] Patch 0 — extract completion builders with parity
- [x] Patch 1 — extract request parameter builders
- [x] Patch 2 — extract streaming boundaries
- [x] Patch 3 — external contract parity snapshots

## Next

- [ ] A2.8 Config Architecture Cleanup

## Later

- [ ] A2.9 IngestService Slimming

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
