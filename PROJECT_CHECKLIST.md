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
- [x] A2.10 Reasoning Quality Loop
- [x] A2.11 Multi-step Reasoning Planner
- [x] A2.11.5 Planner evaluation tests (quality gate)

## Current Work — A2.12 Reasoning Trace + Replay

- [ ] Trace model
- [ ] Trace collector
- [ ] diagnostics.reasoning_trace exposure
- [ ] Trace serialization
- [ ] Replay utility

## Next

- [ ] A2.13 (to be defined)

## Later

- [ ] A2.13 (to be defined)

## A2.12 Reasoning Trace + Replay (active anchor)

- [ ] Trace model
- [ ] Trace collector
- [ ] diagnostics.reasoning_trace exposure
- [ ] Trace serialization
- [ ] Replay utility

## Working Rules

- One patch = one reason
- Work only inside the active anchor
- No opportunistic refactors outside the current patch
- Validate locally before commit
- Commit only files relevant to the active task
