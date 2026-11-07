# HS-T12-02 · Prepare the single navigation state and resolution path

**Conditional implementation task, not a separately shippable change.** Requires accepted G-OPEN, [HS-T00](HS-T00-baseline.md), [HS-T12-01](HS-T12-01-contract.md) and a named code lane. Parent: [HS-S12](../stories/HS-S12-focused-navigation.md). [HS-T12-03](HS-T12-03-host-cutover.md) completes the logical cutover.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S12-focused-navigation.md#g-open-choices-and-proposed-bounded-branch), [ownership](../stories/HS-S12-focused-navigation.md#target-ownership), [matrix/source](../stories/HS-S12-focused-navigation.md#exact-source-owned-paths-and-task-handoff); [V12](../VALIDATION.md#v12-focused-navigation-verification); [I16/I17/I18/I21/I25](../INVARIANTS.md); accepted semantic/import/caller report.

## Owned scope

Existing production: `web/src/desk/shell.ts`, `web/src/desk/store/types.ts`, `web/src/desk/store/compositorSlice.ts`. Reuse manifest exports without duplicating application/alias tables. Serializer, hub-window transport, ordinary Program/Project actions and UI feature modules stay read-only. Tests are only the task02 targets in V12. Exact new helper/type/state names are proposed.

Add transient readiness/reveal state to the existing compositor slice type, its Pick and initialization; do not add another store, callback dispatcher registration or serialized window list. The final shell/store dependency must pass task01's narrow graph check. A new asynchronous import/drain pipeline is not an authorized workaround for an import cycle.

## Work

1. Recheck the accepted ordering and public-interface contracts. Create the explicit canonical/alias resolver from the existing manifest; compose alias/default and requested scope exactly once. Filter parked and non-surface rows before treating the existing void store action as a valid surface open.
2. Add explicit transient host lifecycle/admission and off-glass reveal ownership with stale-cleanup protection. Preserve initial clear versus reopened keep behavior. The state must be omitted from workspace/hub serialization; test reload/hydration cannot revive it as a durable task.
3. Define the single accepted state transition for an admitted open: remove the actual canonical window from the off-glass set, then call the existing compositor open operation. Preserve People/live-meeting redirects, same-window identity, scope, recent-open and fronting semantics. Do not reimplement those operations in shell.
4. Prepare the accepted transient FIFO command order and the separate single staged arrival, including one logical in-memory staged fallback. No duplicate queue/effect owner. Handle alternating storage failures and old stored values explicitly. Preserve best-effort reload limits; no durable exactly-once promise.
5. Preserve synchronous Boolean acceptance/fallback behavior for existing shell APIs and the separate explicit first-answer hook. Do not import Chair/UI feature modules into the command layer. Conductor/Drawer use their specific existing owners in task03, not a fake surface row.
6. Extend state/resolver tests for aliases, parked/unknown keys, admission modes, retained reveal, same-window scope, transient/staged precedence, invalid storage and stale lifecycle cleanup. Explicitly reset pending/staged resources between tests; the old reset seam cleared only Maps.
7. Keep preparation inert until task03 switches wrappers/hosts together. Old callbacks and the new path must never both apply an open. Record which intermediate tests pass and why the whole feature is not yet ready; do not deploy partial work.

## Acceptance

The target transition is testable under the accepted contract and has one local writer, while preserving existing hub/window authority. No transient lifecycle/pending state leaks into persisted payloads. The import/caller check is satisfied, not waved away by a dynamic wrapper or new registry. The scoped focused tests pass after the last edit, or the task is reported incomplete.

Return [completion evidence](../COMPLETION_REPORT_TEMPLATE.md), actual state/payload assertions, remaining cutover steps and exact owned diff. Task03 owns activation and final compatibility proof; no staging, commit, push or deployment follows from this task.

## Rollback and stops

Reverse only this unused/preparatory state/resolution/test patch before activation, preserving other lanes. After task03, reverse the cohesive host/dispatcher change together. Stop for an import cycle, a need to serialize transient state, missing reveal ownership, broadened recovery, unsupported public-interface change or a requirement for a new focus/scheduling protocol.
