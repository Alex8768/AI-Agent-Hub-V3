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
