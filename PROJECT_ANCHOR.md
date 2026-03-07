# Project Anchor

## Active Anchor

A2.10 — Reasoning Quality Loop

### Goal

Introduce a deterministic reasoning quality evaluation layer after verify.

The goal is to measure reasoning quality and optionally trigger limited
self-correction without redesigning the reasoning graph.

### Architecture Position

Retrieval
↓
Evidence Contract
↓
Reasoning
↓
Verify
↓
Reasoning Quality Evaluation
↓
Final Answer

### Patch Plan

#### Patch 0 — Claim extraction
- Extract structured claims from reasoning output
- Claims become units for verification

#### Patch 1 — Evidence coverage scoring
- Map claims to evidence
- Calculate deterministic coverage score

#### Patch 2 — Reasoning confidence model
- Combine coverage, unsupported claims and missing claims
- Produce deterministic confidence score

#### Patch 3 — Retry policy
- If confidence is below threshold allow single retry
- Retry must be strictly bounded and must not create loops

#### Patch 4 — Diagnostics exposure
- Add `diagnostics.reasoning_quality`
- Include coverage and confidence
- Freeze external contract parity tests

### Progress

- [x] Patch 0 — claim extraction
- [x] Patch 1 — evidence coverage scoring
- [x] Patch 2 — reasoning confidence model
- [ ] Patch 3 — retry policy
- [ ] Patch 4 — diagnostics exposure and parity tests

### Out of Scope

Do NOT modify during A2.10:
- Retrieval redesign
- Adapter refactors
- Config architecture
- Ingest pipeline
- Major reasoning graph changes

### Definition of Done

A2.10 is complete when:
- claim extraction implemented
- coverage scoring implemented
- reasoning confidence available
- retry policy limited and predictable
- `diagnostics.reasoning_quality` stable

### Last Completed Anchor

A2.9 — IngestService Slimming

Completed via patches:
- Patch 0 — metadata preparation boundary extracted with parity
- Patch 1 — chunking boundary extracted with parity
- Patch 2 — vector persistence boundary extracted with rollback/error parity
- Patch 3 — external contract parity tests frozen
