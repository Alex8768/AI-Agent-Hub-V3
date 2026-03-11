# Platform Features Catalog

## Purpose

This document is the single source of truth for:

- what the platform should be able to do;
- which capabilities are already implemented;
- which capabilities are planned next;
- how future anchors should be derived.

Use this file before creating or updating `docs/development/PROJECT_ANCHOR.md`,
`docs/development/STATUS.md`, and `docs/development/PROJECT_CHECKLIST.md`.

---

## Product Direction

AI-Agent-Hub-V3 is a modular AI platform for production-grade agent systems with:

- retrieval and ingestion;
- memory and context continuity;
- graph-aware reasoning;
- tool orchestration;
- execution control, traceability, and governance.

---

## Capability Map

### 1) Retrieval Layer

- [x] Vector search (FAISS)
- [x] Hybrid retrieval
- [x] Qdrant path
- [x] Search service-neutral contracts boundary (A2.29 patch 1)
- [x] Hybrid search API mapping hardening with response model sanitation (A2.29 patch 2)
- [x] Search endpoint deterministic quality gate coverage (A2.29 patch 3)
- [x] Search API mapping adapters with migration-safe normalization (A2.29 patch 4)
- [x] Search docs + CI policy alignment (A2.29 patch 5)
- [ ] Retrieval eval benchmark suite
- [ ] Adaptive retrieval policy optimizer

### 2) Ingestion Layer

- [x] Text/document ingest pipeline
- [x] Chunking and embeddings
- [x] OCR for scanned PDFs/images (A2.21 complete)
- [ ] Structured layout extraction (tables/forms)
- [ ] Multilingual ingest quality checks

### 3) Memory Layer

- [x] Workspace memory baseline
- [x] Semantic memory integration
- [ ] Long-horizon memory policies
- [ ] Memory conflict resolution

### 4) Reasoning Layer

- [x] Multi-step planner
- [x] Step executor
- [x] Quality loop
- [x] Trace + replay
- [x] Timeline observability
- [x] Execution control (policy, loop guard, retries)
- [x] Trust/Governance execution receipts
- [x] Multi-agent coordination
- [x] Adaptive optimization diagnostics
- [x] Enterprise productization diagnostics

### 5) Tooling Layer

- [x] Tool integration boundaries
- [x] Tool permission model (capability-based)
- [x] Sandbox execution modes
- [x] Side-effect risk classification
- [x] MCP connector expansion (A2.25 complete: registry/discovery/safety/runtime with quality gates)

### 6) Platform/Operations

- [x] Feature flags
- [x] CI workflows
- [x] Ruleset-protected main branch flow
- [x] Stable required checks policy (A2.26 complete)
- [x] Release quality gates and benchmark reports (A2.26 complete)
- [x] Search boundary CI quality gate (A2.29 patch 5)
- [x] Release-gate coverage threshold policy contract (A2.30 patch 1)
- [x] Shared coverage diagnostics normalization contract (A2.30 patch 2)
- [x] Release-gate coverage quality-gate tests (A2.30 patch 3)
- [x] Release-gate CI/report coverage policy alignment (A2.30 patch 4)
- [x] Coverage enforcement docs/roadmap closure (A2.30 patch 5)
- [x] Required checks matrix source-of-truth contract introduced (A2.31 patch 1)
- [x] Required checks workflow input normalization (A2.31 patch 2)
- [x] Required checks consolidation deterministic gates (A2.31 patch 3)
- [x] CI wiring for consolidated required checks matrix (A2.31 patch 4)
- [x] Required checks docs/policy closure (A2.31 patch 5)
- [x] Docs topology map and compatibility policy (A2.32 patch 1)
- [x] Docs migration to target topology with root stubs (A2.32 patch 2)
- [x] Docs references/workflow path alignment (A2.32 patch 3)
- [x] Docs topology quality gate (A2.32 patch 4)
- [x] Docs topology closure and policy sync (A2.32 patch 5)
- [x] API docs/runtime contract parity alignment (A2.33 patch 1)
- [x] API docs request/response closure (A2.33 patch 2)
- [x] Feature-flag docs/default behavior alignment (A2.33 patch 3)
- [x] API docs deterministic quality gate (A2.33 patch 4)
- [x] API docs and roadmap closure (A2.33 patch 5)
- [x] Operational KPI policy contract baseline for answer-path soft-failure/fallback health (A2.56 patch 2)
- [x] Operational diagnostics-to-KPI mapping contract for answer debug/reporting surfaces (A2.56 patch 3)
- [x] Operational KPI policy quality-gate enforcement for deterministic docs markers (A2.56 patch 4)
- [x] Assistant mode contracts + flags + diagnostics baseline (A2.34 patch 1)
- [x] Language-native assistant fallback behavior (A2.34 patch 2)
- [x] Proactive suggestion ranking MVP (A2.34 patch 3)
- [x] Draft action runtime (review-before-execute) (A2.34 patch 4)
- [x] Assistant runtime docs/CI closure (A2.34 patch 5)
- [x] Intent contract baseline with planning diagnostics (A2.35 patch 1)
- [x] Deterministic review-only plan builder baseline (A2.35 patch 2)
- [x] Plan-to-draft-actions deterministic diagnostics bridge (A2.35 patch 3)
- [x] Planning policy guards for review-only safety (A2.35 patch 4)
- [x] Intent-to-plan orchestrator docs/CI closure (A2.35 patch 5)
- [x] Confirmation-to-execution handshake diagnostics baseline (A2.36 patch 1)
- [x] Confirmation transition model (approved/cancelled) diagnostics (A2.36 patch 2)
- [x] Execution receipt stub diagnostics integration (A2.36 patch 3)
- [x] Handshake transition policy guards diagnostics (A2.36 patch 4)
- [x] Confirmation handshake runtime docs/CI closure (A2.36 patch 5)
- [x] Approval session diagnostics baseline (A2.37 patch 1)
- [x] Dedicated confirm/cancel API contract surface (A2.37 patch 2)
- [x] Idempotency key and replay-guard diagnostics (A2.37 patch 3)
- [x] Safe-mode execution gateway diagnostics (A2.37 patch 4)
- [x] Approval execution gateway docs/CI closure (A2.37 patch 5)
- [x] Durable approval/idempotency contract baseline diagnostics (A2.38 patch 1)
- [x] Durable approval/idempotency persistence wiring (A2.38 patch 2)
- [x] Token ttl and one-time confirmation guards (A2.38 patch 3)
- [x] Restart recovery deterministic replay outcomes (A2.38 patch 4)
- [x] Durable approval recovery docs/CI closure (A2.38 patch 5)
- [x] Controlled execution pilot contract baseline diagnostics (A2.39 patch 1)
- [x] Controlled execution allowlist and transition policy gate (A2.39 patch 2)
- [x] Execution receipt rollback contract enforcement for approvals (A2.39 patch 3)
- [x] Controlled execution pilot runtime wiring (allowlisted safe-mode actions) (A2.39 patch 4)
- [x] Controlled execution pilot docs/CI closure (A2.39 patch 5)
- [x] LLM planner diagnostics contract baseline (A2.40 patch 1)
- [x] Planner adapter wiring with deterministic fallback behavior (A2.40 patch 2)
- [x] LLM planner policy guardrails with forced fallback on violations (A2.40 patch 3)
- [x] LLM planner runtime wiring and diagnostics parity (A2.40 patch 4)
- [x] LLM planner runtime docs/CI closure (A2.40 patch 5)
- [x] MCP-aware tool selection diagnostics contract baseline (A2.41 patch 1)
- [x] MCP-aware selector adapter with deterministic fallback diagnostics (A2.41 patch 2)
- [x] Tool selection policy guardrails with forced fallback diagnostics (A2.41 patch 3)
- [x] Tool selection runtime wiring and diagnostics parity (A2.41 patch 4)
- [x] Dynamic tool selection docs/CI closure (A2.41 patch 5)
- [x] Feedback-learning diagnostics contract baseline (A2.42 patch 1)
- [x] Feedback capture adapter with deterministic signal normalization (A2.42 patch 2)
- [x] Feedback policy guardrails with forced fallback diagnostics (A2.42 patch 3)
- [x] Feedback runtime wiring and diagnostics parity (A2.42 patch 4)
- [x] Feedback learning runtime docs/CI closure (A2.42 patch 5)
- [x] Feedback-to-planning adaptation diagnostics contract baseline (A2.43 patch 1)
- [x] Feedback signal-to-plan deterministic adaptation ranking (A2.43 patch 2)
- [x] Feedback adaptation policy guardrails with forced fallback diagnostics (A2.43 patch 3)
- [x] Feedback adaptation runtime wiring and diagnostics parity (A2.43 patch 4)
- [x] Feedback adaptation runtime docs/CI closure (A2.43 patch 5)
- [x] Assistant low-evidence conversational recovery runtime hook (A2.44 patch 1)
- [x] Assistant language-native conversational recovery hardening (A2.44 patch 2)
- [x] Assistant conversational recovery policy guardrails with forced fallback diagnostics (A2.44 patch 3)
- [x] Assistant conversational recovery runtime wiring and diagnostics parity (A2.44 patch 4)
- [x] Assistant conversational recovery runtime docs/CI closure (A2.44 patch 5)
- [x] Architecture hardening track formalization and scope lock (A2.45 patch 1)
- [x] AnswerService boundary hardening baseline runtime-context seam (A2.45 patch 2)
- [x] Planner coupling guardrail via reasoning adapter abstraction seam (A2.45 patch 3)
- [x] Memory consistency diagnostics guardrails in answer runtime snapshots (A2.45 patch 4)
- [x] Architecture hardening runtime docs/CI closure + technical debt registry (A2.45 patch 5)
- [x] Topology zoning inventory and dependency-direction scope lock (A2.46 patch 1)
- [x] Kernel runtime boundary formalization via dedicated kernel seam (A2.46 patch 2)
- [x] Governance subcore extraction via explicit runtime governance bundle (A2.46 patch 3)
- [x] Execution request boundary formalization with execution-plane seam and diagnostics (A2.46 patch 4)
- [x] Topology dependency quality gates + docs/CI closure (A2.46 patch 5)
- [x] Debt-closure inventory and scope lock for runtime clarity/reliability (A2.47 patch 1)
- [x] AnswerService orchestration extraction seam with runtime parity preserved (A2.47 patch 2)
- [x] Memory consistency strategy contract for best-effort dual-store with deferred outbox/compensation (A2.47 patch 3)
- [x] Runtime entrypoint cleanup decision via `run_utf8.py` compatibility wrapper to `src.api.main:app` (A2.47 patch 4)
- [x] Debt registry/docs/CI closure with dedicated runtime quality gate (A2.47 patch 5)
- [x] Planner decoupling inventory and scope lock for kernel composition independence (A2.48 patch 1)
- [x] Planner composition seam extraction via kernel runtime adapter wiring (A2.48 patch 2)
- [x] Prompt/planner boundary normalization via shared query-input contract (A2.48 patch 3)
- [x] Planner diagnostics/runtime parity guardrails via dedicated parity contract (A2.48 patch 4)
- [x] Planner decoupling debt registry/docs/CI closure with runtime quality gate (A2.48 patch 5)
- [x] Conversational reliability inventory and scope lock for human-friendly safe UX (A2.49 patch 1)
- [x] Response-style boundary seam extraction via kernel runtime adapter wiring (A2.49 patch 2)
- [x] Low-evidence friendliness normalization via deterministic response-style contract (A2.49 patch 3)
- [x] Conversational diagnostics/runtime parity guardrails via dedicated parity contract (A2.49 patch 4)
- [x] Conversational reliability docs/CI closure with runtime quality gate (A2.49 patch 5)
- [x] Composition boundary contract baseline for planner residual decoupling (A2.50 patch 1)
- [x] Composition resolver/adapter extraction with planner consuming only normalized resolution (A2.50 patch 2)
- [x] Dependency/parity/fallback guardrails for planner-composition boundary closure (A2.50 patch 3)
- [x] Answer-path inventory and scope lock for facade/orchestrator/response-assembly decomposition (A2.51 patch 1)
- [x] Orchestrator seam extraction with `AnswerService` delegating core flow coordination (A2.51 patch 2)
- [x] Response assembly extraction for recovery/friendliness/parity shaping (A2.51 patch 3)
- [x] Endpoint-facing interface contract cleanup with stable answer-service request envelope (A2.51 patch 4)
- [x] Answer-path dependency/parity quality gates with CI release-gate wiring (A2.51 patch 5)
- [x] Post-A2.51 answer-path soft-failure observability hardening + guardrail tests (M1/M2)
- [x] Post-A2.51 answer-path guardrail coverage for durable-hydration soft-failure path (M3)
- [x] Post-A2.51 answer-path guardrail coverage for post-orchestration soft-failure path (M4)
- [x] Post-A2.51 guardrail maintenance closure sync across project docs (M5)
- [x] A2.52 AnswerService facade slimming inventory + scope lock (patch 1)
- [x] A2.52 AnswerService post-orchestration seam extraction via dedicated flow module (patch 2)
- [x] A2.52 AnswerService diagnostics merge seam extraction via dedicated flow module (patch 3)
- [x] A2.52 AnswerService facade pipeline cleanup via helper-driven primary pipeline/dependency builders (patch 4)
- [x] A2.52 Answer-path guardrails/parity closure (seam import + facade pipeline + soft-failure policy gates) (patch 5)
- [x] A2.53 Answer-path exception-policy inventory/scope-lock for remaining silent handlers (patch 1)
- [x] A2.53 Orchestrator silent-except removal with fallback-failure observability reason-codes (patch 2)
- [x] A2.53 AnswerService phase-1 diagnostics soft-failure hardening (evidence/retriever/apply diagnostics reason-codes) (patch 3)
- [x] A2.53 AnswerService phase-2 silent-except hardening for observability/session-memory/retriever-adapter best-effort paths (patch 4)
- [x] A2.53 exception-policy quality gate scope expansion + parity/full-suite closure sync (patch 5)
- [x] A2.54 diagnostics-contract guardrails inventory/scope-lock (snapshot/policy/parity constraints) (patch 1)
- [x] A2.54 diagnostics snapshot guardrail expansion for cross-mode keyset stability (patch 2)
- [x] A2.54 soft-failure policy guardrail expansion for diagnostics reason-code/flag visibility (patch 3)
- [x] A2.54 exception-policy enforcement hardening with scoped AST handler-contract gate (patch 4)
- [x] A2.54 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.55 documentation consistency cleanup inventory/scope-lock (patch 1)
- [x] A2.55 capability-map consistency correction for OCR completion status (patch 2)
- [x] A2.55 checklist/status/anchor synchronization with stale carry-over cleanup (patch 3)
- [x] A2.55 roadmap wording normalization for completed OCR/MCP milestones (patch 4)
- [x] A2.55 guardrails/parity closure with docs-focused + full-suite green (patch 5)
- [x] A2.56 operational guardrails inventory/scope-lock for soft-failure KPI policy (patch 1)
- [x] A2.56 KPI policy contract introduction (healthy path + fallback/soft-failure rate definitions) (patch 2)
- [x] A2.56 diagnostics surface mapping and reporting contract for KPI numerators/counters (patch 3)
- [x] A2.56 operational KPI policy quality-gate enforcement (patch 4)
- [x] A2.56 guardrails/parity closure with docs-focused + full-suite green (patch 5)
- [x] Post-A2.56 guardrail compatibility maintenance for closed-status quality-gate handling (M1)
- [x] A2.57 decomposition regime inventory + scope lock with no-growth governance baseline (patch 1)
- [x] A2.57 answer-service move-map contract and package scaffolding baseline (patch 2)
- [x] A2.57 answer heavy-cluster extraction phase-1 (context/execution/diagnostics/observability helpers) (patch 3)
- [x] A2.57 reasoning-engine move-map and diagnostics/evaluation runtime-contract extraction baseline (patch 4)
- [x] A2.57 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.58 thin-facade completion inventory/scope-lock for answer/reasoning phase-2 extraction (patch 1)
- [x] A2.58 answer phase-2 helper extraction for language/runtime-context/reasoning-adapter/memory-consistency seams (patch 2)
- [x] A2.58 reasoning phase-2 helper extraction for runtime evaluation diagnostics seams (patch 3)
- [x] A2.58 decomposition no-growth line-budget quality-gate expansion for answer/reasoning monolith targets (patch 4)
- [x] A2.58 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.59 monolith burn-down phase-3 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.59 answer phase-3 runtime diagnostics wiring extraction for planner/tool-selection/feedback/recovery seams (patch 2)
- [x] A2.59 reasoning phase-3 runtime productization diagnostics extraction for optimization/enterprise/meta-cognition seams (patch 3)
- [x] A2.59 no-growth threshold recalibration + extraction-path seam coverage expansion for answer/reasoning facades (patch 4)
- [x] A2.59 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.60 facade convergence phase-4 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.60 answer phase-4 llm-planner policy seam extraction for guarded planner policy/fallback helpers (patch 2)
- [x] A2.60 reasoning phase-4 multi-agent runtime helper seam extraction for coordination/enrichment helpers (patch 3)
- [x] A2.60 no-growth threshold recalibration + seam/import-budget coverage expansion for answer/reasoning facades (patch 4)
- [x] A2.60 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.61 facade convergence phase-5 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.61 answer phase-5 feedback-policy seam extraction for feedback/adaptation guard contracts (patch 2)
- [x] A2.61 reasoning phase-5 dry-run fallback seam extraction for runtime fallback answer builders (patch 3)
- [x] A2.61 no-growth threshold recalibration + seam/import-budget coverage refresh for answer/reasoning facades (patch 4)
- [x] A2.61 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.62 facade convergence phase-6 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.62 answer phase-6 tool-selection policy seam extraction into planner-policy module (patch 2)
- [x] A2.62 reasoning phase-6 runtime warning-flags seam extraction into diagnostics runtime contracts (patch 3)
- [x] A2.62 no-growth threshold recalibration + runtime diagnostics seam wiring gate expansion for answer/reasoning facades (patch 4)
- [x] A2.62 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.63 facade convergence phase-7 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.63 answer phase-7 transition-policy contract seam extraction into planner-policy module (patch 2)
- [x] A2.63 reasoning phase-7 loop-guard bounded-plan seam extraction into control loop-guard module (patch 3)
- [x] A2.63 no-growth threshold recalibration + loop-guard seam wiring gate expansion for answer/reasoning facades (patch 4)
- [x] A2.63 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.64 facade convergence phase-8 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.64 answer phase-8 assistant-recovery policy seam extraction into planner-policy module (patch 2)
- [x] A2.64 reasoning phase-8 per-step diagnostics mapping seam extraction into evaluation runtime diagnostics module (patch 3)
- [x] A2.64 no-growth threshold recalibration + runtime diagnostics seam wiring gate expansion for answer/reasoning facades (patch 4)
- [x] A2.64 guardrails/parity closure with focused + full-suite green (patch 5)
- [x] A2.65 facade convergence phase-9 inventory + scope lock for answer/reasoning extraction-only governance (patch 1)
- [x] A2.65 answer phase-9 plan-policy guard seam extraction into planner-policy module (patch 2)
- [x] A2.65 reasoning phase-9 fallback planner observations seam extraction into evaluation runtime diagnostics module (patch 3)
- [x] A2.65 no-growth threshold recalibration + baseline refresh for answer/reasoning facades (patch 4)

### 7) Interface Layer

- [x] First-party web interface (workspace/session UX) (A2.28 patch 4: context controls + local persistence + loading hardening)
- [x] Answer/debug diagnostics panel (A2.28 patch 3)
- [x] Document/search/answer end-user flows (A2.28 patches 2-4)
- [x] UI deterministic quality gate + CI interface smoke wiring (A2.28 patch 5)

---

## Planned Anchor Ideas (Draft)

- `A2.15` Trust & Governance Layer (verifiable execution receipts)
- `A2.16` Multi-Agent Coordination Fabric
- `A2.17` Tool Safety Sandbox
- `A2.18` Evaluation & Benchmark Hub
- `A2.19` Adaptive Optimization Layer
- `A2.20` Enterprise Productization Pack
- `A2.21` OCR Ingestion Layer
- `A2.22` Dynamic Composition Engine (MVP)
- `A2.23` Meta-Cognition Engine (Lite)
- `A2.24` Anticipatory Engine (Safe Mode)
- `A2.25` MCP Ecosystem Expansion
- `A2.26` Release Gates & CI Policy Hardening
- `A2.27` Architecture & Readiness Audit
- `A2.28` Interface Foundation (MVP)
- `A2.29` Service Contract Boundary Cleanup (Search)
- `A2.30` Coverage Enforcement in Release Gate
- `A2.31` CI Workflow Consolidation & Required Checks Matrix
- `A2.32` Docs Topology Cleanup (root -> docs/architecture + docs/development)
- `A2.33` API Docs & Feature-Flag Alignment
- `A2.34` Digital COO Runtime (Assistant + Draft Actions)
- `A2.35` Intent-to-Plan Orchestrator (COO MVP)
- `A2.36` Confirmation-to-Execution Handshake (MVP)
- `A2.37` Approval Session & Idempotent Execution Gateway (Safe Mode)
- `A2.38` Durable Approval Recovery Runtime (Safe Mode)
- `A2.39` Controlled Execution Pilot (Strict Safe Mode+)
- `A2.40` Intent-based Planning Engine (LLM Planner)
- `A2.41` Dynamic Tool Selection (MCP-aware)
- `A2.42` Learning from Feedback (Approve/Cancel/Edit)

Roadmap order:

- `A2.15 -> A2.16 -> A2.17 -> A2.18 -> A2.19 -> A2.20 -> A2.21 -> A2.22 -> A2.23 -> A2.24 -> A2.25 -> A2.26 -> A2.27 -> A2.28 -> A2.29 -> A2.30 -> A2.31 -> A2.32 -> A2.33 -> A2.34 -> A2.35 -> A2.36 -> A2.37 -> A2.38 -> A2.39`
- OCR milestone is complete (`A2.21`); future composition work must still follow staged MVP-first rollout.
- Composition should start as rule-based MVP before advanced autonomy.
- Meta-cognition should consume existing diagnostics first (no graph redesign in first pass).
- Anticipatory mode should start as safe post-response suggestions (lightweight).
- MCP expansion milestone is complete (`A2.25`); future MCP work requires a new anchor with explicit quality gates.

---

## Feature Spec Template

Copy this section when defining a new major feature:

### Feature: <name>

- **Problem:** <what pain it solves>
- **Value:** <why this matters for users/business>
- **Scope (in):** <included>
- **Scope (out):** <excluded>
- **Contracts:** <data/API/model contracts to add>
- **Observability:** <metrics, diagnostics, traces>
- **Security/Policy:** <controls/guardrails>
- **Tests:** <unit/integration/quality gate>
- **Rollout:** <flag/gradual rollout strategy>

---

## Working Rule

Every new anchor should reference at least one item from this catalog and clearly mark:

- implemented capabilities;
- net-new capabilities;
- deferred capabilities.
