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
- [x] A2.8 Config Architecture Cleanup
- [x] A2.9 IngestService Slimming

## Current Work — A2.10 Reasoning Quality Loop

- [x] Patch 0 — claim extraction
- [x] Patch 1 — evidence coverage scoring
- [x] Patch 2 — reasoning confidence model
- [ ] Patch 3 — retry policy (single bounded retry)
- [ ] Patch 4 — diagnostics.reasoning_quality exposure + parity tests

## Next

- [ ] A2.11 (to be defined)

## Later

- [ ] A2.11 (to be defined)

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
