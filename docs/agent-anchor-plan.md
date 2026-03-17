# Agent Anchor Plan (Single Execution Line)

## Mandatory Rule
- Before starting any anchor or patch, read this file first.
- Work strictly in sequence: no skipping anchors.
- After each patch:
  1) provide a short done summary,
  2) ask user permission for the next patch,
  3) create a commit.
- Push only after all anchors are complete and user confirms runtime quality.

## Current Objective
Build a thinking assistant layer (not scripted behavior) with two contours:
- DIALOG contour: natural, fast, low-friction conversation.
- ACTION contour: full safety pipeline, confirmations, and constraints.

## Execution Protocol
- Keep architecture modular; avoid monolith files.
- Soft limits:
  - file size <= 300 lines (hard exception <= 450 with justification),
  - function size <= 60 lines.
- Every patch must update this checklist status.

## Anchors
- [x] A0: governance baseline + single-line execution document.
- [x] A1: query router/classifier (`dialog`, `advice`, `action`) + diagnostics.
- [x] A2: unified LLM core for generation-first behavior.
- [x] A3: containers split (`dialog` vs `action/advice`) wired in answer service.
- [x] A4: memory-lite integration (session context first, expandable).
- [x] A5: reflection-lite + quality gate (bounded retries).
- [x] A6: action/disclaimer policy contract hardening.
- [ ] A7: acceptance matrix + canary feature flag rollout.

## Active Patch
- Anchor: A6
- Patch: A6.1
- Scope:
  - enforce query-type tool policy route contract (`dialog/advice/action`),
  - block tool execution in `dialog`,
  - require idempotency gate for `action`,
  - add advisory disclaimer contract for `advice`.
- Status: done

## Patch Reporting Template
- Anchor/Patch:
- What changed:
- Validation:
- Risks:
- Next patch request:

