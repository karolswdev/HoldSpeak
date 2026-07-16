# HS-94-08 — Delivery work inhabits the Web Desk

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-04, HS-94-05, HS-94-06, HS-94-07; Phase 93 Desk grammar
- **Unblocks:** HS-94-09, HS-94-10

## Problem

The current conveyor is a compact global fixture limited to the current phase.
Past Stories and evidence are inaccessible there, session correlation is a
separate store, and terminal/factory controls depend on implicit global node
state. Phase 93 explicitly says advanced power should live through familiar Desk
objects and processes, not another dashboard.

## Scope

- In:
  - Project object opens a delivery inspector/window;
  - Story board/list/belt views over the same read model;
  - current and historical phases, parked/paused work, search and direct links;
  - Work attempt and Coder session process rows/cards;
  - immutable target terminal window with streaming/fallback;
  - evidence dossier browser;
  - commit/gate/PR/CI/command/launch completion Receipts;
  - attention for waiting agent, node/source offline, gate/CI refusal/failure,
    missing evidence, and unknown command outcome;
  - create/attach/launch/steer/factory/rail-mutation entry points through shared
    policy and exact verbs;
  - desktop, compact/iPad Web, keyboard, screen reader, touch, reduced motion;
  - migration from `missioncontrol.ts`/`steering.ts` stores and compatibility
    facade parity.
- Out:
  - new primary nav dashboard or control center;
  - deleting compatibility routes before consumers move;
  - duplicating Phase 93 tool shelf, inspector, Receipt, Attention, or policy;
  - hover/drag/spatial-only capability.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the owner-observed north-star walk on production Web moves to
[BACKLOG candidate Y](../BACKLOG.md); every Desk-expression and no-authority
invariant is machine-verified here, including an API-backed production walk
in which HS-94-08's own Work attempt renders on the Desk.


- [x] Project, Story, Work attempt, Coder session, Evidence dossier, and Receipt
      use existing Desk identity/selection/inspector patterns.
- [x] A past completed Phase and Story are reachable and their dossier opens
      without changing routes to a separate Delivery Workbench app.
- [x] Active work names Story, agent, node, worktree/branch/head, lifecycle,
      freshness, and terminal target.
- [x] Changing node/worktree occurs by selecting a different target; it cannot
      reinterpret an open target.
- [x] Voice fills every free-text delivery input; exact destination/consequence
      is visible at send/launch/mutation boundaries.
- [x] `unknown` command outcome, stale/offline source, incompatible schema, and
      unavailable evidence each render a distinct recovery action.
- [x] Desktop and compact Web have no horizontal overflow, hidden-only action,
      unnamed control, or modal-only flow; keyboard/screen-reader journey passes.
- [x] Existing belt verbs and direct URLs survive through compatibility
      selectors until generated parity permits cleanup.
- [x] No UI field or `localStorage` record is authority for Story association,
      target, policy, grant, or command status.

## Test plan

- component/store selectors against shared contract fixtures;
- target-switch regression and stale factory-state regression;
- Story history/evidence navigation;
- all typed failure states;
- voice/transcribe request and retained draft on failure;
- browser E2E at desktop and iPad widths;
- keyboard, VoiceOver/screen reader, reduced motion;
- route/verb/API compatibility census.

## Implementation direction

- Build views from the normalized Delivery Runtime selectors, not nested private
  fetches in components.
- Keep the belt as a compact view if useful; do not make it the domain owner.
- Use Phase 93's Project inspector/window and tool shelf rather than adding
  permanent chrome.
- Retain unsent instructions and selected grounding across network failure and
  target refresh.
- Product labels follow Phase 93: Projects, Stories, Coder sessions, Evidence,
  Receipts, Runs on/Node as finalized; compatibility names stay internal.

## Evidence required

- before/after production-root captures;
- desktop/compact four-journey video or screenshot sequence;
- keyboard/screen-reader transcript;
- failure-state gallery;
- generated compatibility/consumer report.
