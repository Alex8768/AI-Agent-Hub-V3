# Project Status

## Current Phase

A2.91 in progress

## Last Completed Anchor

A2.90 - UI Reliability and Product UX Baseline

A2.90 closed with:
- persisted theme preferences (`light`/`dark`/`system`) and system-first locale baseline (`en`/`ru`)
- product UX refresh for chat and layout surfaces with improved readability and visual hierarchy
- runtime transparency simplified for end users while preserving technical reason-code visibility
- frontend lint/build and backend focused/full regression checks green (`602 passed, 3 skipped`)

Legacy closure markers retained for A2.56 docs quality-gate compatibility:
- Anchor Closed — A2.56 complete (operational guardrails policy closure)
- Post-A2.56 Maintenance — M1 complete (quality-gate closed-status compatibility)

## Current Active Anchor

A2.91 - Truthfulness and Consistency Guard Baseline

Current focus:
- add deterministic trust guardrails for answer consistency/evidence alignment
- preserve runtime contract and reason-code determinism while adding trust diagnostics
- continue one-patch-one-reason execution discipline

Execution discipline:
- no net-new intelligence features
- preserve runtime parity
- one patch = one reason
- inventory first, extraction second

## Next Anchor

TBD - Post-A2.91 planning

## CI Status

CI pipelines are green.

Answer-path decomposition must preserve:
- answer endpoint behavior
- debug snapshot behavior
- diagnostics parity
- contract stability
