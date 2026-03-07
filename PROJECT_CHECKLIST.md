# Project Checklist

## Completed

- [x] Base Layer stabilization
- [x] Hybrid Retrieval pipeline
- [x] Reasoning Engine initial implementation
- [x] A2.3 Evidence Contract
- [x] A2.4 Self-check Diagnostics Rollout
- [x] CI tracing compatibility fix

## Current Work — A2.5 Verify Node Hardening

- [ ] Patch 0 — verify diagnostics schema preflight
- [ ] Patch 1 — verify node warning-only policy
- [ ] Patch 2 — verify threshold tuning and boundary tests
- [ ] Patch 3 — external contract stabilization for diagnostics.verify

## Next

- [ ] A2.6 AnswerService Decomposition

## Later

- [ ] A2.7 OpenAIAdapter Decomposition
- [ ] A2.8 Config Architecture Cleanup
- [ ] A2.9 IngestService Slimming

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
