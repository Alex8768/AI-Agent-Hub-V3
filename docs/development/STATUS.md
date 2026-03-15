# Project Status

## Current Phase

A2.85 in progress

## Last Completed Anchor

A2.84 - Act Read-Only Runtime + UX Transparency

A2.84 closed with:
- Act read-only runtime seam with deterministic allowlist (`list_files`, `read_file`)
- reason-code closure seam promoting policy/runtime reason-codes into top-level warnings
- chat/meta UI visibility for runtime mode, Act status and block reason-codes
- focused and full-suite checks green at closure (`584 passed, 3 skipped`)

Legacy closure markers retained for A2.56 docs quality-gate compatibility:
- Anchor Closed — A2.56 complete (operational guardrails policy closure)
- Post-A2.56 Maintenance — M1 complete (quality-gate closed-status compatibility)

## Current Active Anchor

A2.85 - Managed Action Profiles + Compact Diagnostics UX

Current focus:
- introduce deterministic runtime policy profiles by environment/context
- deliver compact diagnostics default with expanded opt-in path
- preserve A2.84 mode/reason transparency while adding diagnostics ergonomics
- continue one-patch-one-reason execution discipline

Execution discipline:
- no net-new intelligence features
- preserve runtime parity
- one patch = one reason
- inventory first, extraction second

## Next Anchor

A2.85 - Patch 5 (guardrails + parity + closure)

## CI Status

CI pipelines are green.

Answer-path decomposition must preserve:
- answer endpoint behavior
- debug snapshot behavior
- diagnostics parity
- contract stability
