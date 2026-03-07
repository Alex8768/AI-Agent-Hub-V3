# Project Checklist

## Completed

- [x] Base Layer stabilization
- [x] Hybrid Retrieval pipeline
- [x] Reasoning Engine initial implementation
- [x] A2.3 Evidence Contract
- [x] CI tracing compatibility fix

## Current Work — A2.4 Self-check Diagnostics Rollout

- [ ] Patch 0 — runtime parity tests (compile+ainvoke, compile+invoke, no-invoke fallback)
- [ ] Patch 1 — diagnostics.self_check schema with status "not_evaluated"
- [ ] Patch 2 — warning-only policy
- [ ] Patch 3 — threshold tuning
- [ ] Patch 4 — external contract stabilization

## Next

- [ ] A2.5 Verify Node Hardening

## Later

- [ ] A2.6 AnswerService Decomposition
- [ ] A2.7 OpenAIAdapter Decomposition
- [ ] A2.8 Config Architecture Cleanup
- [ ] A2.9 IngestService Slimming

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
