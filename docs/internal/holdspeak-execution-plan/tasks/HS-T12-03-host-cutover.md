# HS-T12-03 · Replace per-key host registration without changing the job

**Conditional implementation task.** Requires [HS-T12-02](HS-T12-02-dispatch-state.md), its accepted G-OPEN contract and scoped assignment. Parent: [HS-S12](../stories/HS-S12-focused-navigation.md). No independent shipping authority.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [ownership](../stories/HS-S12-focused-navigation.md#target-ownership), [matrix](../stories/HS-S12-focused-navigation.md#acceptance-matrix), [source map](../stories/HS-S12-focused-navigation.md#exact-source-owned-paths-and-task-handoff); [V12](../VALIDATION.md#v12-focused-navigation-verification); predecessor reports, current web instructions and [I16/I17/I18/I21/I25](../INVARIANTS.md).

## Owned scope

Existing production: `web/src/desk/shell.ts`, `web/src/desk/components/SurfaceWindows.tsx`, `web/src/desk/conductor/ConductorWindows.tsx`, `web/src/desk/drawer/DrawerWindows.tsx`, plus narrowly coordinated compositor/type adjustments from task02. Existing conductor/drawer stores, manifest/lazy loaders, Chair/Dock interception, proposal handoff/editor controllers and backend files remain read-only unless the accepted source map explicitly grants a necessary amendment. Test/browser targets are listed in V12.

## Work

1. Recheck the complete owned registration/caller list and supported keys. Switch existing shell wrappers to accepted direct resolution/admission/state behavior in the same logical change that removes per-key callback installation from the hosts. Do not leave an enabled dual path or a one-callback bridge renamed as a controller.
2. SurfaceWindows publishes the explicit lifecycle mode with matching cleanup and renders the shared off-glass/reveal state. Preserve clear-first-use versus retained windows, recovery aliases and normal staged consumption ordering. A recovered host must not consume normal arrival prematurely or let stale cleanup erase a new host's readiness.
3. Preserve the existing lazy host construction, chunk failure handling, mounted-read/layout infrastructure and host context slots. If the old readiness DOM attribute remains for compatibility, document that it now means explicit navigation readiness, not a component registry. It is not proof the target finished rendering.
4. Route Conductor and retained Drawer compatibility through their existing imperative stores, under the accepted admission rule. Do not feed them to `openSurfaceWindow`. Preserve current delayed focus behavior unless a separate adapter/focus change was accepted; command FIFO does not prove final cross-family focus. Do not promote parked Drawer into a newly required feature or delete it by assumption.
5. Retain first-answer/Dock behavior at the existing UI boundary. Only the existing fresh-launch compact Dictate compatibility branch applies; running/minimized chips and non-Dock actions are not hijacked. No claim of a current phone Speak tile or live recording test follows.
6. Keep exact project-proposal handoff unchanged. Test the overview→project/proposal/request chain against the new navigation boundary, including same-target reveal and editor step-aside. If adapting that map/event is necessary, stop for a bounded amendment rather than adding a second proposal queue or silently merging its authority.
7. Retire the obsolete opener Map/register export only after all known supported callers and tests are migrated. Keep the documented compatibility wrappers and current route/query handoff. If closure is incomplete, report the exact unresolved caller; do not leave a hidden fallback that still dispatches both ways.
8. Run task03's focused and browser proof, then the accepted-slice union. Inspect actual changed-state behavior and producer requests, not only a removed identifier count. Do not reroute Save/Confirm/publish/Send or clear draft/window data to make a test pass.

## Acceptance

Per-key opener registration is no longer the active built-in dispatch mechanism; one explicit admission/reveal/state owner performs the job. Staged and transient semantics match G-OPEN, public/fallback behavior remains bounded, and all C12 preservation cases have appropriate proof or explicit incomplete status. Existing lazy, hub-window, proposal/draft and recovery contracts remain intact.

Return [completion evidence](../COMPLETION_REPORT_TEMPLATE.md) with the caller/removal map, state/persistence assertions, observed focus limits, tests/screenshots and rollback. Hold for independent task04 proof and separate SHIP authority.

## Rollback and stops

Use one reviewed reverse patch covering wrappers, state and hosts; never restore only a Map or only a readiness effect. No data migration is expected. Stop for undiscovered active callers, generic fallback routes outside the contract, broader lifecycle/persistence changes, new cycles, dual application, target-context loss or changed editor/consent behavior.
