## Patch 1 — Stabilize shell and unify layout state

### Goal
Stabilize the application shell with a single typed layout state and predictable sidebar behavior, while preparing the top-level shell skeleton for follow-up patches.

### Scope
- frontend/src/App.tsx
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/layoutState.ts
- frontend/src/components/shell/TopBar.tsx
- frontend/src/components/shell/LeftSidebar.tsx
- frontend/src/components/shell/RightSidebar.tsx
- frontend/src/components/shell/MainWorkspace.tsx
- frontend/src/components/shell/GlobalModalHost.tsx
- docs/frontend-refactor-log.md

### Changes
- Introduced typed `ShellLayoutState` with `appMode`, sidebar visibility, sections/tabs, canvas visibility, density, and runtime visibility flags.
- Added localStorage read/write helpers for unified shell state persistence.
- Reworked the root app composition to use shell skeleton wrappers: `TopBar`, `LeftSidebar`, `MainWorkspace`, `RightSidebar`, and `GlobalModalHost`.
- Removed conflicting sidebar collapse logic in `AppLayout` and replaced it with deterministic open/close behavior driven by one state source.
- Added app mode foundation (`chat` / `split` / `canvas`) in shell-level workspace switching without deep canvas/runtime refactor.

### Why
- The previous shell relied on duplicated sidebar control paths that could desynchronize panel behavior.
- A single typed shell state is required before role-based sidebar refactor, runtime stream rendering, and canvas-centric flows.

### Validation
- npm run build
- npm run lint

### Result
- done

---

## Anchor A1 / Patch A1.1 — Query classifier + diagnostics wiring

### Goal
Introduce an explicit query router signal (`dialog|advice|action`) in a dedicated module and expose it in diagnostics without changing the existing orchestration path.

### Scope
- src/services/answer/classifier.py (new)
- src/services/answer/diagnostics/runtime_apply.py
- tests/unit/services/answer/test_classifier.py (new)
- tests/unit/services/answer/test_answer_service_debug_snapshot.py

### Changes
- Added `QueryType` enum and `classify_query_type()` in `src/services/answer/classifier.py`.
- Implemented layered classification strategy:
  - rule-first markers for action/advice/dialog;
  - optional LLM fallback for ambiguous queries;
  - safe fallback behavior if LLM classification fails.
- Wired diagnostics in `runtime_apply`:
  - `query_type`
  - `query_type_reason`
- Added classifier unit tests (rules + LLM fallback path).
- Updated diagnostics snapshot keyset test for new fields.

### Validation
- `uv run pytest tests/unit/services/answer/test_classifier.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_populates_debug_snapshot_fields`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_diagnostics_keyset_stable_when_proactive_flag_changes`

### Result
- done

---

## Anchor A2 / Patch A2.1 — Unified LLM core (generation-first)

### Goal
Introduce a single generation wrapper (`llm_core`) so natural response paths use one bounded LLM entry with retry, quality guard, and emergency fallback hooks.

### Scope
- src/services/answer/llm_core.py (new)
- src/layers/pro/reasoning/response_style.py
- tests/unit/services/answer/test_llm_core.py (new)

### Changes
- Added `LLMCoreMode` and `generate_with_llm_core()` in `src/services/answer/llm_core.py`.
- Implemented unified generation behavior:
  - mode-aware prompting (`dialog|advice|action`),
  - bounded retries,
  - pluggable `quality_guard`,
  - emergency fallback hook,
  - optional disable of default fallback.
- Refactored `build_natural_safe_terminal_response()` to route LLM generation through `llm_core` while preserving existing tier contracts:
  - `L0/L1`: contextual useful answer
  - `L2`: confirmation semantics required
  - `L3`: explicit refusal semantics required
- Added unit tests for `llm_core` core behavior.

### Validation
- `uv run pytest tests/unit/services/answer/test_llm_core.py`
- `uv run pytest tests/unit/layers/pro/test_reasoning_response_style.py`
- `uv run pytest tests/unit/services/answer/test_response_assembly_truthfulness.py`

### Result
- done

---

## Anchor A3 / Patch A3.1 — Container split in AnswerService

### Goal
Split answer execution into dedicated containers (`dialog` vs `action/advice`) and make `AnswerService` responsible for routing, not container internals.

### Scope
- src/services/answer/containers/shared.py (new)
- src/services/answer/containers/dialog.py (new)
- src/services/answer/containers/action.py (new)
- src/services/answer/containers/__init__.py (new)
- src/services/answer/answer_service.py
- tests/unit/services/answer/test_answer_service_containers.py (new)

### Changes
- Added container layer:
  - `run_dialog_container()`
  - `run_action_container()`
  - shared execution helper `run_container_pipeline()`
- Refactored `AnswerService.handle_contract()`:
  - classifies query via `classify_query_type()`,
  - routes `DIALOG` to dialog container,
  - routes `ADVICE/ACTION` to action container.
- Kept existing orchestration/post-processing/diagnostics merge behavior unchanged by reusing the same pipeline callbacks.
- Added routing unit tests for dialog/action container selection.

### Validation
- `uv run pytest tests/unit/services/answer/test_answer_service_containers.py`
- `uv run pytest tests/unit/services/answer/test_classifier.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_populates_debug_snapshot_fields`

### Result
- done

---

## Anchor A4 / Patch A4.1 — Memory-lite (session context first)

### Goal
Add a modular memory-lite layer that reuses existing session memory and exposes a stable session-context payload for routing-time observability.

### Scope
- src/services/answer/context/memory_lite.py (new)
- src/services/answer/answer_service.py
- tests/unit/services/answer/test_memory_lite.py (new)
- tests/unit/services/answer/test_answer_service_debug_snapshot.py

### Changes
- Added `memory_lite` module with:
  - `attach_memory_lite_context()` (builds session-context payload from `session_id` and `session_memory_last_answer`)
  - `apply_memory_lite_runtime_diagnostics()` (writes `diagnostics.memory_lite`)
- Integrated memory-lite into `AnswerService`:
  - builds context right after query classification,
  - applies `memory_lite` diagnostics before final presenter stage.
- Updated debug snapshot keyset to include `memory_lite`.
- Added unit tests for memory-lite payload construction and diagnostics wiring.

### Validation
- `uv run pytest tests/unit/services/answer/test_memory_lite.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_containers.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_populates_debug_snapshot_fields`

### Result
- done

---

## Anchor A5 / Patch A5.1 — Reflection-lite quality gate

### Goal
Add a post-answer reflection step that detects low-quality terminal outcomes (stub/template/low-info/unknown-style) and allows at most one safe rewrite attempt.

### Scope
- src/services/answer/reflection_lite.py (new)
- src/services/answer/answer_service.py
- tests/unit/services/answer/test_reflection_lite.py (new)
- tests/unit/services/answer/test_answer_service_debug_snapshot.py

### Changes
- Added `apply_reflection_lite()`:
  - evaluates answer quality markers (`stub`, `unknown`, `low-information`, `template`),
  - applies one bounded rewrite attempt (`max_retries=1`) via safe terminal builder,
  - writes diagnostics payload `reflection_lite`,
  - appends planning reason code when retry is applied.
- Integrated reflection-lite into `AnswerService` after memory-lite diagnostics and before runtime/presentation stages.
- Updated debug snapshot keyset to include `reflection_lite`.
- Added unit tests for rewrite path and skip path.

### Validation
- `uv run pytest tests/unit/services/answer/test_reflection_lite.py`
- `uv run pytest tests/unit/services/answer/test_memory_lite.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_containers.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_populates_debug_snapshot_fields`

### Result
- done

---

## Anchor A6 / Patch A6.1 — Tool policy + confirm contract

### Goal
Harden tool policy behavior by query type:
- `DIALOG`: no tool execution
- `ADVICE`: explicit advisory disclaimer
- `ACTION`: strict idempotency gate before act-mode execution

### Scope
- src/services/answer/tool_policy_contract.py (new)
- src/services/answer/answer_service.py
- tests/unit/services/answer/test_tool_policy_contract.py (new)
- tests/unit/services/answer/test_answer_service_debug_snapshot.py

### Changes
- Added route-level contract in `apply_tool_policy_route_contract()`:
  - blocks `act` mode for `dialog`,
  - requires `act_idempotency_key` for `action` when `act` mode is requested.
- Added response-level contract in `apply_tool_policy_response_contract()`:
  - prepends advisory disclaimer for `advice` responses.
- Wired both contracts into `AnswerService`:
  - route contract applied immediately after query classification,
  - response contract applied after `act_read_only` runtime.
- Added diagnostics payload `tool_policy_contract` with reason codes.
- Added unit tests for dialog/action/advice contract behavior.

### Validation
- `uv run pytest tests/unit/services/answer/test_tool_policy_contract.py`
- `uv run pytest tests/unit/services/answer/test_reflection_lite.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_containers.py`
- `uv run pytest tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_populates_debug_snapshot_fields`

### Result
- done

### Next patch
- Patch 2: rebuild left/right sidebars by roles (navigation vs operational context) with dedicated section/tab components.

## Patch 2 — Rebuild sidebars by roles

### Goal
Reorganize left and right sidebars by explicit platform roles without touching chat runtime stream, canvas internals, settings architecture, or API contracts.

### Scope
- frontend/src/App.tsx
- frontend/src/components/shell/layoutState.ts
- frontend/src/components/shell/LeftSidebar.tsx
- frontend/src/components/RightPanel.tsx
- frontend/src/components/left-sidebar/ChatsSection.tsx
- frontend/src/components/left-sidebar/ProjectsSection.tsx
- frontend/src/components/left-sidebar/ViewsSection.tsx
- frontend/src/components/left-sidebar/SavedSection.tsx
- frontend/src/components/right-sidebar/FilesTab.tsx
- frontend/src/components/right-sidebar/ToolsTab.tsx
- frontend/src/components/right-sidebar/ContextTab.tsx
- frontend/src/components/right-sidebar/TraceTab.tsx
- frontend/src/components/right-sidebar/ApprovalsTab.tsx
- docs/frontend-refactor-log.md

### Changes
- Left sidebar now has dedicated navigation sections: `Chats`, `Projects`, `Views`, `Saved`.
- Added separate component per left section and wired section switching through unified typed layout state.
- Added mode switcher (`Chat` / `Split` / `Canvas`) in left sidebar `Views` section.
- Right sidebar now exposes 5 operational tabs: `Files`, `Tools`, `Context`, `Trace`, `Approvals`.
- Added separate component per right tab and switched tab state to controlled mode via unified layout state.
- Kept existing files/tools operational logic as-is and wrapped it in role-specific tab components.

### Why
- Shell needed clear role separation: navigation on the left and operational context on the right.
- Decomposed components make future patches predictable and reduce sidebar coupling.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 3: transform chat into execution runtime stream with event-driven rendering and approval cards.

## Patch 3 — Transform chat into runtime stream

### Goal
Upgrade chat UI from plain message feed to execution runtime stream with typed event rendering, reasoning summaries, inline approvals, and result action bar foundation.

### Scope
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/chat-runtime/types.ts
- frontend/src/components/chat-runtime/ResultActionBar.tsx
- frontend/src/App.tsx
- docs/frontend-refactor-log.md

### Changes
- Added typed chat runtime UI model with explicit item and event types.
- Rebuilt chat timeline rendering around event-driven cards:
  - execution events
  - plan card
  - reasoning summary card
  - inline approval card
  - result card
- Added inline approval flow with `approve / deny / review` actions in chat stream.
- Added result action bar with `Copy`, `Retry`, `Continue`, `Open Canvas`, `Show Trace`, `Show Context`, `Export`.
- Connected action bar hooks to shell-level layout actions (`canvas`, `trace`, `context`) via thin callbacks from app shell.

### Why
- Runtime transparency requires showing what the assistant is doing step-by-step, not just final text.
- Typed UI events prepare the frontend for future backend streaming without breaking current API contracts.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 4: integrate canvas as a real workspace surface tied to runtime outputs.

## Patch 4 — Integrate canvas as workspace surface

### Goal
Integrate Canvas into workspace modes (`chat`, `split`, `canvas`) as a first-class surface and wire result/runtime actions to open meaningful canvas views.

### Scope
- frontend/src/App.tsx
- frontend/src/components/shell/layoutState.ts
- frontend/src/components/shell/MainWorkspace.tsx
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/chat-runtime/ResultActionBar.tsx
- frontend/src/components/canvas/canvasState.ts
- frontend/src/components/canvas/CanvasHost.tsx
- frontend/src/components/canvas/views/EmptyCanvasView.tsx
- frontend/src/components/canvas/views/GraphCanvasView.tsx
- frontend/src/components/canvas/views/PlanCanvasView.tsx
- frontend/src/components/canvas/views/DiffCanvasView.tsx
- frontend/src/components/canvas/views/ArtifactCanvasView.tsx
- frontend/src/components/canvas/views/DocumentCanvasView.tsx
- docs/frontend-refactor-log.md

### Changes
- Added typed canvas view model (`CanvasViewType`, `CanvasState`) and integrated it into unified shell layout state.
- Updated `MainWorkspace` to operate as mode router with stable real behavior for `chat`, `split`, and `canvas`.
- Added dedicated canvas host and separate view components for graph, plan, diff, artifact, and document previews.
- Wired ResultActionBar actions to canvas content flows:
  - Open Canvas -> plan view
  - Open Diff -> diff view
  - Open Artifact -> artifact view
  - Show Trace/Show Context -> document previews on canvas
- Reused existing `GraphCanvas` through a dedicated `GraphCanvasView` adapter.

### Why
- Canvas needed explicit state and view semantics to become a real workspace surface.
- Runtime outputs now have direct path into canvas without backend contract changes.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: move settings into proper modal/popover layers and polish UX density/status cues.

## Patch 4.5 — Shell UX cleanup

### Goal
Polish shell composition so collapsed sidebars, top controls, and panel framing feel intentional and product-like while preserving Patch 1-4 architecture.

### Scope
- frontend/src/App.tsx
- frontend/src/components/shell/TopBar.tsx
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/LeftSidebar.tsx
- frontend/src/components/shell/RightSidebar.tsx
- frontend/src/components/shell/MainWorkspace.tsx
- docs/frontend-refactor-log.md

### Changes
- Reworked top controls into a single cohesive top control surface with title/context, mode switch, connection status, quick theme toggle, and settings trigger.
- Replaced broken-looking collapsed sidebars with intentional compact rails (`Nav`/`Ops`) and clear reopen triggers.
- Reduced shell framing noise by removing excessive nested card shells and simplifying panel containers.
- Improved visual hierarchy so center workspace reads as primary surface and sidebars are clearly secondary.
- Kept mode/router, runtime stream, and canvas state architecture intact.

### Why
- The shell still looked like scaffolding with stacked bars and accidental collapsed states.
- Product feel required clearer control surfaces and less decorative container noise.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: settings/modal architecture and final UX polish.

## Patch 5 — Settings IA and modal architecture

### Goal
Move settings from a monolithic dialog into clear interaction surfaces: lightweight quick popover in top bar plus dedicated modals for connection/model, agent behavior, and workspace configuration.

### Scope
- frontend/src/App.tsx
- frontend/src/components/shell/TopBar.tsx
- frontend/src/components/SettingsDialog.tsx
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/chat-runtime/ResultActionBar.tsx
- frontend/src/components/shell/layoutState.ts
- frontend/src/components/settings/settingsTypes.ts
- frontend/src/components/settings/QuickSettingsPopover.tsx
- frontend/src/components/settings/ConnectionModelModal.tsx
- frontend/src/components/settings/AgentBehaviorModal.tsx
- frontend/src/components/settings/WorkspaceSettingsModal.tsx
- docs/frontend-refactor-log.md

### Changes
- Introduced typed settings state `AppSettingsState` with explicit domains:
  - `connection` (provider/model/endpoint)
  - `behavior` (reasoning/search/approval/detail/auto-open flags)
  - `workspace` (root/policy/profile/session preferences)
- Replaced top bar monolithic settings entry with:
  - lightweight `QuickSettingsPopover` (theme, density, runtime visibility toggles)
  - `ConnectionModelModal`
  - `AgentBehaviorModal`
  - `WorkspaceSettingsModal`
- Kept top bar status compact and scoped to key signals only:
  - backend status
  - active provider/model
  - active workspace/session
  - active mode
- Added `showTraceShortcut` into persisted shell layout state and wired it to runtime action bar visibility.
- Updated runtime UI to respect quick toggles:
  - hide/show execution event cards
  - hide/show trace action in result action bar
- Converted old `SettingsDialog` into a deprecated compatibility adapter (legacy mapping wrapper), no longer primary architecture.

### Why
- Settings UX needed correct information architecture: quick operational toggles in a popover and deeper config in dedicated modals.
- A typed domain state enables cleaner ownership boundaries and future backend reintegration without reintroducing a monolithic dialog.

### Validation
- npm run build
- npm run lint

### Result
- done

## Patch 5.1 / 6 — Control vs status consolidation

### Goal
Separate control surfaces from status surfaces: keep top bar focused on active controls, move passive telemetry to a lightweight bottom status strip, and consolidate settings into one canonical hub.

### Scope
- frontend/src/components/shell/TopBar.tsx
- frontend/src/components/shell/BottomStatusBar.tsx
- frontend/src/components/settings/SettingsHub.tsx
- frontend/src/App.tsx
- frontend/src/lib/uiPreferences.ts
- frontend/src/components/ChatPanel.tsx
- docs/frontend-refactor-log.md

### Changes
- Reworked `TopBar` to control-first layout:
  - left panel toggle pinned to left edge
  - centered workspace context (title + meta)
  - mode switch near center
  - single `Settings` entry point
  - compact connection indicator
  - right panel toggle pinned to right edge.
- Added `BottomStatusBar` as read-mostly status strip for:
  - session
  - mode
  - provider/model
  - backend state
  - runtime state
  - workspace short label
  - language.
- Added canonical `SettingsHub` with sections:
  - General
  - Appearance
  - Models
  - Behavior
  - Workspace.
- Restored language preferences to settings system with explicit options:
  - English
  - Русский
  - Deutsch
  - Français
  - System (auto).
- Extended locale utilities to support `de` and `fr` in storage and system resolution.
- Kept previously added settings surfaces as non-canonical remnants (no longer exposed from top bar).

### Why
- Top bar had mixed concerns and high visual noise.
- Product interaction model is clearer when active controls and passive status are separated.
- A single settings entry point prevents duplicate and conflicting mental models.

### Validation
- npm run build
- npm run lint

### Result
- done

## Patch 7 — Runtime UX and action polish

### Goal
Turn chat into a clearer agent runtime console by improving execution readability, approval clarity, and result/action ergonomics without touching backend contracts or shell/settings/canvas architecture.

### Scope
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/chat-runtime/types.ts
- frontend/src/components/chat-runtime/RuntimeCard.tsx
- frontend/src/components/chat-runtime/ResultActionBar.tsx
- docs/frontend-refactor-log.md

### Changes
- Introduced a unified runtime card system (`RuntimeCard`) with variants:
  - execution
  - file activity
  - tool activity
  - approval
  - warning
  - result
  - reasoning
  - plan.
- Expanded runtime timeline model with dedicated activity types:
  - `file_activity`
  - `tool_activity`
  - `warning`
  - richer approval/result metadata.
- Added visual phase grouping layer for execution flow:
  - Analyze / Discover / Plan / Execute / Finalize
  - phase grouping is render-only (no new runtime state machine).
- Added summary-first execution rendering:
  - compact primary line in flow
  - collapsible `Details / Inspect` for lower-level telemetry.
- Improved approval gate UX:
  - always distinct visual block
  - risk badge + target summary
  - explicit `Approve / Review / Deny` actions
  - no auto-collapse behavior.
- Improved result card hierarchy and contextual action bar:
  - structured result header/body/footer
  - action visibility now contextual instead of always-on
  - consistent button size/height in action group.
- Clarified trace/context reveal:
  - explicit companion-opened runtime events
  - clearer labels (`Trace Companion`, `Context Companion`)
  - no duplicate interaction surfaces.

### Why
- Runtime UI needed to feel like a workstream console, not a generic chat feed.
- Summary-first rendering reduces noise while keeping inspectability.
- Contextual actions and stronger approval semantics improve decision confidence.

### Validation
- npm run build
- npm run lint

### Result
- done

## Patch 7.1 — Run-centric streaming correction

### Goal
Replace event-feed runtime perception with run-centric execution UX where one user request maps to one live runtime block plus one terminal result card.

### Scope
- frontend/src/components/ChatPanel.tsx
- frontend/src/components/chat-runtime/types.ts
- docs/frontend-refactor-log.md

### Changes
- Switched runtime rendering model from many top-level execution cards to a single `runtime_run` block per user request.
- Aggregated execution phases inside run block:
  - Analyze / Discover / Plan / Execute / Finalize
  - each phase has status + summary + collapsible details.
- Kept phase progression visually alive with:
  - active-phase spinner
  - phase-by-phase status transitions
  - run progress bar updates.
- Embedded approvals directly inside the run block as blocking gate UI (not separate feed message).
- Ensured terminal outcomes always render as distinct final result cards:
  - successful completion -> answer result card
  - failed/denied run -> failed terminal result card.
- Preserved summary-first UX while keeping tool/file/warning details inspectable within relevant phase details.

### Why
- Previous patch still looked like a styled event stream instead of a coherent run lifecycle.
- Run-centric aggregation better matches user mental model: process first, outcome second.

### Validation
- npm run build
- npm run lint

### Result
- done

## Patch 7.2a.1 — Backend quality recovery

### Goal
Restore response usefulness for safe/general queries by reducing over-restrictive degradation paths in backend policy/assembly while preserving hard safety boundaries for destructive actions.

### Scope
- src/services/answer/reasoning/llm_planner_policy.py
- src/services/answer/response_assembly.py
- src/services/answer/failure_policy.py
- src/services/answer/diagnostics/runtime_wiring.py
- src/services/answer/response/language.py
- src/layers/pro/reasoning/response_style.py
- tests/unit/layers/pro/test_reasoning_response_style.py
- docs/frontend-refactor-log.md

### Changes
- Relaxed plan guard from narrow `prepare_*_draft` allowlist to safe non-destructive planning actions while keeping destructive markers blocked.
- Added controlled safe degradation for empty-ready plans (`general_query` / `general_chat`) via synthetic `prepare_safe_outline_draft` instead of hard blank guard outcome.
- Expanded assistant recovery language policy to `ru/en/de/fr` across planner contract, runtime wiring, and language helpers.
- Disabled policy-level "forced fallback" by default for recovery violations (`fallback_on_policy_violation=false`) to avoid unnecessary hard degradation in non-destructive contexts.
- Narrowed low-evidence normalization behavior:
  - preserve substantive answers when they are already useful;
  - keep normalization for greeting/capability/ambiguous contexts;
  - generate a safe structured outline when substantive query has weak/empty answer.
- Upgraded controlled fallback response quality in failure policy:
  - short fallback for simple prompts;
  - structured "what can be done safely now" response for substantive prompts.
- Added explicit quality-trace markers in diagnostics (`quality_trace:*`) to expose when degradation paths were applied or bypassed.
- Added regression tests for substantive low-evidence behavior in response style.

### Why
- Main quality loss came from backend post-processing and policy clamps, not only frontend rendering.
- The patch keeps safety constraints but shifts behavior from hard refusal toward bounded useful assistance for safe scenarios.

### Validation
- `uv run pytest tests/unit/layers/pro/test_reasoning_response_style.py tests/unit/services/answer/test_response_assembly_truthfulness.py tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_wire_assistant_recovery_runtime_diagnostics_normalizes_policy`

### Result
- done

## Patch 7.2a.2 — Eliminate stub finalization

### Goal
Remove terminal `"(reasoning layer stub)"` outcomes for safe/general requests and replace them with useful safe responses, while keeping destructive safety blocks intact.

### Scope
- src/layers/pro/reasoning/response_style.py
- src/layers/pro/reasoning/evaluation/runtime_productization.py
- src/layers/pro/reasoning/graph/nodes.py
- src/services/answer/response_assembly.py
- src/services/answer/diagnostics/runtime_wiring.py
- tests/unit/layers/pro/test_reasoning_engine_synthesize.py
- tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_fallback.py
- tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_timeout.py
- tests/unit/services/answer/test_answer_service_debug_snapshot.py
- docs/frontend-refactor-log.md

### Changes
- Added safe terminal response helpers in reasoning style layer:
  - `is_reasoning_stub_answer`
  - `is_destructive_request`
  - `build_safe_terminal_response`
- Replaced direct stub returns in fallback runtime productization with safe terminal response generation.
- Replaced graph answer-node exception fallback from raw stub to safe terminal response.
- Added final stub-replacement guard in response assembly, so stub answers are converted before response finalization.
- Updated assistant fallback routing:
  - greetings keep friendly greeting behavior;
  - non-greeting safe/general requests now route to useful safe terminal responses (including structured baseline plan for substantive asks).
- Adjusted assistant recovery diagnostics wiring so `assistant_chat_recovery_policy_forced_fallback` is only added when `fallback_on_policy_violation=true`.
- Updated reasoning-engine unit tests from strict stub expectation to safe non-stub expectation.
- Updated debug snapshot assertions for greeting recovery policy to match non-forced fallback default.

### Why
- Quality bottleneck was no longer only policy constraints; terminal answer paths still emitted stub placeholders.
- The patch introduces a narrow terminal safety net to guarantee useful safe output for safe/general paths without enabling destructive behavior.

### Validation
- `uv run pytest tests/unit/layers/pro/test_reasoning_engine_synthesize.py tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_fallback.py tests/unit/layers/pro/test_reasoning_engine_synthesize_llm_timeout.py tests/unit/services/answer/test_response_assembly_truthfulness.py tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_assistant_fallback_localizes_russian tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_answer_service_recovery_policy_blocks_recovery_for_greeting tests/unit/services/answer/test_answer_service_debug_snapshot.py::test_wire_assistant_recovery_runtime_diagnostics_normalizes_policy`
- Live prompt check on patched backend (`:8010`) with 3 prompts:
  - safe/general substantive -> structured safe outline (no stub),
  - light ambiguous -> concise useful response (no stub),
  - destructive request -> explicit refusal with safe alternative (still blocked).

### Result
- done

## Patch 4.7c — Split handle and pane control consistency

### Goal
Fix remaining interaction gaps by making split resize clearly trustworthy in practice and consolidating pane open/close controls around top bar triggers.

### Scope
- frontend/src/components/shell/MainWorkspace.tsx
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/TopBar.tsx
- docs/frontend-refactor-log.md

### Changes
- Upgraded split divider interaction with explicit drag affordance:
  - stronger visible separator states (idle/hover/dragging)
  - wider hit area
  - stable drag cursor and constraints
  - persisted split ratio.
- Removed panel-local close buttons from side panes to avoid split control model.
- Kept `Esc` close behavior while making top bar pane controls the primary and explicit source of truth.
- Grouped top bar pane triggers into an intentional `Panes` control cluster.

### Why
- Previous state still felt dual-control and split drag confidence was not strong enough.
- Product interaction model requires one coherent pane control pattern and trustworthy split manipulation.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: settings/modal architecture and final UX polish.

## Patch 4.7b — Reflow panes correction

### Goal
Correct the 4.7 interaction mismatch by replacing overlay-like behavior with true workspace reflow panes and stronger split-resize interaction.

### Scope
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/MainWorkspace.tsx
- docs/frontend-refactor-log.md

### Changes
- Replaced overlay composition with true structural reflow compositor:
  - open left: `left | main`
  - open right: `main | right`
  - open both: `left | main | right`
  - closed panes are fully removed from layout columns.
- Removed modal-style backdrop/dimming for normal pane-open state.
- Tuned pane adjacency to near-flush surfaces with thin dividers and subtle tint separation.
- Kept side panes as workspace surfaces (no floating card styling, no pane shadows).
- Strengthened split interaction divider in `MainWorkspace`:
  - wider hit area
  - explicit resize cursor
  - visible active/hover feedback
  - stable min/max constraints with persisted ratio.

### Why
- Previous implementation still felt like overlays visually adjusted to mimic reflow.
- Product target requires true multi-pane workspace composition and trustworthy split manipulation.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: settings/modal architecture and final UX polish.

## Patch 4.7 — Workspace interaction polish

### Goal
Polish workspace interaction quality so overlay side panes and split chat/canvas resizing feel intentional, stable, and desktop-native.

### Scope
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/MainWorkspace.tsx
- frontend/src/components/shell/TopBar.tsx
- docs/frontend-refactor-log.md

### Changes
- Added soft workspace adaptation when side panes open: center surface shifts with adaptive clamp-based insets instead of abrupt compression.
- Tuned left/right side sheets to read as pane/sheet surfaces (thin separators, subtle tint) rather than floating cards.
- Kept top bar toggles as source-of-truth controls and synchronized visual pressed state (`aria-pressed` + active variant).
- Implemented first-class split resize using `react-resizable-panels` with:
  - visible but subtle divider
  - proper col-resize cursor
  - min/max panel constraints
  - persistent split ratio via autosave key.

### Why
- Overlay architecture needed interaction polish to feel like workspace surfaces, not modal overlays.
- Split mode requires high-quality resize ergonomics to be product-usable.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: settings/modal architecture and final UX polish.

## Patch 4.6 — Overlay sidebar architecture

### Goal
Convert left and right sidebars from persistent layout columns into overlay desktop drawers so the main workspace remains primary and keeps full width when panels are closed.

### Scope
- frontend/src/components/AppLayout.tsx
- frontend/src/components/shell/TopBar.tsx
- frontend/src/App.tsx
- docs/frontend-refactor-log.md

### Changes
- Replaced column-based sidebar layout with overlay drawers (`aside`) rendered above the workspace surface.
- Closed side panels now consume zero layout width; center workspace always owns the full base layout area.
- Moved primary panel open/close controls to TopBar with explicit left/right trigger buttons.
- Added light backdrop layer for click-outside close behavior while keeping non-modal visual separation.
- Added `Esc` key support to close open drawers.
- Kept left/sidebar content architecture and runtime/canvas/settings foundations unchanged.

### Why
- Structural columns made the shell feel like a dashboard and reduced main workspace primacy.
- Overlay drawers align better with IDE/operator workflows and preserve focus on the central surface.

### Validation
- npm run build
- npm run lint

### Result
- done

### Next patch
- Patch 5: settings/modal architecture and final UX polish.

---

## Natural Behavior Recovery — Stage 1 (Truth baseline)

### Goal
Stabilize environment (single backend port, frontend proxy), then capture a truth baseline on 10–15 key prompts for later comparison.

### Scope
- scripts/baseline_stage1.py (new)
- docs/baseline-stage1.json, docs/baseline-stage1.md (generated)
- docs/frontend-refactor-log.md

### Changes
- Added `scripts/baseline_stage1.py`: health check, POST /api/v1/answer for 12 prompts (safe/general, ambiguous, planning-with-operational-words, destructive).
- Saves per-response: answer, answer_preview, planning_reason_codes, quality_trace, assistant_recovery_policy slice; writes docs/baseline-stage1.json and docs/baseline-stage1.md.

### Baseline snapshot (2026-03-17)
- **Порт:** backend 8000, frontend proxy 8000 — ок.
- **Результаты:** stub-строка «(reasoning layer stub)» не встречается; многие safe/general запросы (1,2,3,5,9) дают короткий ответ «Я не знаю.» при violations `assistant_chat_recovery_intent_not_allowlisted`, `assistant_chat_recovery_requires_low_evidence`.
- Деструктивные (11, 12) корректно блокируются длинным сообщением.
- **Для Этапа 2:** убрать жёсткую перезапись на «Я не знаю» для safe/general; условная перезапись только при stub/empty/unknown.

### Validation
- `uv run python scripts/baseline_stage1.py --base-url http://127.0.0.1:8000` — все 12 запросов успешны, файлы записаны.

### Next
- Этап 2: условная перезапись fallback в оркестраторе, reason-codes preserve/fallback, smoke по 3 промптам.

---

## Natural Behavior Recovery — Stage 2 (Core routing fix)

### Goal
Убрать жёсткую перезапись полезных ответов и оставить fallback только для реально плохих терминальных исходов (stub/empty/unknown), сохранив safety-блок для destructive.

### Scope
- src/services/answer/orchestrator.py
- tests/unit/services/answer/test_answer_soft_failure_observability.py
- tests/unit/services/answer/test_answer_service_debug_snapshot.py
- docs/frontend-refactor-log.md

### Changes
- Подтверждена и закреплена условная перезапись в оркестраторе только для:
  - stub (`(reasoning layer stub)`),
  - unknown-style (`я не знаю`/`i don't know`),
  - empty answer.
- Сохранён reason-code контракт:
  - `assistant_orchestrator_fallback_applied`,
  - `assistant_orchestrator_answer_preserved`,
  - `assistant_orchestrator_template_answer_preserved`.
- Добавлен safety guard: для destructive-запросов без provenance оркестратор не сохраняет generic low-evidence ответ, а переводит в fallback-path (явный отказ + безопасная альтернатива).
- Обновлён snapshot-тест английского assistant fallback под новый preserve-контракт (не принудительный fallback при полезном ответе).
- Добавлен unit-тест: destructive-запрос без provenance должен получать fallback и reason code `assistant_orchestrator_fallback_applied`.

### Validation
- `uv run pytest tests/unit/services/answer/test_answer_soft_failure_observability.py tests/unit/services/answer/test_answer_service_debug_snapshot.py` -> 61 passed.
- Smoke (3 prompts, live API):
  - safe/general: структурный план вместо `Я не знаю`.
  - light ambiguous: короткий полезный ответ.
  - destructive: явный блок с безопасной альтернативой.

### Result
- done

### Next
- Этап 3: risk-tier policy (вынос в `src/services/answer/risk_tier.py` + diagnostics wiring `risk_tier`/`risk_tier_reason`), только после подтверждения.

---

## Natural Behavior Recovery — Stage 3 (Steps 3–5: tier terminal contract)

### Goal
Привязать risk_tier к контракту терминального ответа: L0/L1 — без stub/empty/unknown; L2 — plan/preview + confirm; L3 — block + safe alternative (уже в оркестраторе).

### Scope
- src/services/answer/risk_tier.py (build_l2_safe_terminal)
- src/services/answer/response_assembly.py (tier contract enforcement)
- tests/unit/services/answer/test_risk_tier.py, test_response_assembly_truthfulness.py, test_answer_service_debug_snapshot.py

### Changes
- В response_assembly: сначала L2 — при пустом/stub ответе подставляется build_l2_safe_terminal (план + подтверждение); иначе для L0/L1 при stub/empty/unknown_style — build_helpful_safe_alternative с current_answer="".
- Добавлены quality_trace: tier_contract_l2_enforced, tier_contract_l0_l1_enforced; reason_codes: assistant_l2_terminal_contract_enforced, assistant_terminal_answer_replaced.
- Тесты: L1 — замена unknown_style на полезную структуру; L2 — пустой терминал заменяется на L2-сообщение с план/подтверждение; тест normalize_unknown_low_evidence допускает либо low_evidence_friendliness, либо terminal_answer_replaced.

### Validation
- `uv run pytest tests/unit/services/answer/` — 125 passed.

### Result
- done

---

## Anchor A0 / Patch A0.1 — Single execution line governance

### Goal
Create one authoritative execution document to keep anchor-by-anchor delivery synchronized and prevent scope drift.

### Scope
- docs/agent-anchor-plan.md (new)

### Changes
- Added a mandatory execution protocol document:
  - read before every anchor/patch,
  - strict sequential anchor order,
  - commit after each patch,
  - push only after all anchors and user verification.
- Added anchor checklist with statuses and active patch tracking.
- Added patch reporting template to standardize updates.

### Result
- done
