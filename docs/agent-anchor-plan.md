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
- [ ] A4: memory-lite integration (session context first, expandable).
- [ ] A5: reflection-lite + quality gate (bounded retries).
- [ ] A6: action/disclaimer policy contract hardening.
- [ ] A7: acceptance matrix + canary feature flag rollout.

## Active Patch
- Anchor: A3
- Patch: A3.1
- Scope:
  - add container split (`dialog` and `action/advice`),
  - route by `QueryType` in `AnswerService`,
  - keep execution pipeline behavior unchanged.
- Status: done

## Patch Reporting Template
- Anchor/Patch:
- What changed:
- Validation:
- Risks:
- Next patch request:

