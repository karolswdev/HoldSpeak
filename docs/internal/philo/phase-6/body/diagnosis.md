# PHILO-6-05 diagnosis — an overlapping refresh erases the Decision body

Date: 2026-09-24

## Cause

The save is optimistic and the store has the new text before the request
resolves. A first probe held a `WorldObject` prop outside the production
host; that synthetic case rendered an empty body, but it is not the
production cause. The real host projection is `DeskApp.tsx:80,
133–135`: it subscribes to `items` and calls `objectByRef` on every render.
The full-host probe below shows that this path renders the new body
immediately after Done.

The production race is an overlapping refresh. Creating the decision emits
`desk_changed` (`holdspeak/runtime/composition.py:454–461` and `:175–190`).
The browser mounts `DeskChangedRefresh` in `main.tsx:16–23`;
`useDeskChangedRefresh.ts:38,52` waits 300 ms and starts a whole-desk
`refresh()`. In the continuous 393 trace, that CREATE refresh's
`GET /api/decisions` starts at 2287.1 ms and resolves blank at 2297.1 ms,
1.6 s before the Done PUT starts at 3928.3 ms. The PUT resolves with the saved
body at 3939.8 ms; the first unreadable frame is at 4087.1 ms (click+159.1).
The only delayed commit is `dataSlice.ts:164–168` waiting for the slower
`Promise.all([loadAll(), loadSetup()])`, then replacing the whole `items` map at
`:180`. The 1440 trace repeats the order: collection GET 2265.0 ms, PUT
3869.4–3880.7 ms, first unreadable frame at click+77.3 ms. The continuous
traces do not identify which `loadAll` sibling is slower; that is the remaining
runtime unknown. The "hub read still served the pre-PUT snapshot" hypothesis
is refuted by the GET resolving before the PUT begins. A later GET restores the
durable text. The retained S4 timing and the live first-paint probe prove this
order: the first read frame has the complete body at 11.9 ms, the delayed
observation has only the `DECISION` heading, and a later post-PUT read has the
saved sentence again.
This is not a window animation or child-retention effect.
`DeskWindowFrame` passes `children` directly at
`web/src/desk/components/DeskWindow.tsx:877`; the body can change only when
the pullout rerenders from changed store data. The live run saw a
`GET /api/decisions` after the click, consistent with a later refresh restoring
the durable value. The continuous trace records the request start times; only
the slower `loadAll` sibling remains unidentified.

The save seam remains `DecisionPullout.tsx:66–67`: it calls the real
`useDesk.getState().updatePrimitive(...)` and immediately leaves edit mode.
`dataSlice.ts:321–333` creates a new item and maps `decision_markdown` to
`decisionMarkdown` at line 302. `dataSlice.ts:344–369` handles the later
response and refusal path. Awaiting the save alone cannot fence the first
render, and the whole-desk refresh can erase the optimistic value before its
response arrives.

## Runtime/store probe

`web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx` contains both
the intentionally synthetic held-prop control and a full-host probe. The
full-host probe subscribes to `items`, derives `objectByRef` on every render,
drives the real `dataSlice.updatePrimitive`, and uses a transport double only
for HTTP. Its trace is:

```text
production host, after Done: store decisionMarkdown="Keep the local ledger"
production host, first read: Decision section contains "Keep the local ledger"
overlapping refresh resolves: store decisionMarkdown=""
overlapping refresh read: Decision section textContent="Decision"
```

The held-prop test is retained as an explicitly named synthetic negative
control only; it must not be cited as the production cause. The subscribed
host and the continuous S4 trace establish the cause independently.

The focused Vitest file has seven tests. The two controls are green against
the current behavior; the five fence assertions are intentionally red before
the repair. The run was made from `web/` with the repository's jsdom config:

```text
PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH \
  npm exec vitest run src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx --maxWorkers=1
Test Files  1 failed (1)
Tests       2 passed | 5 failed (7)
Failed: the slow refusal kept `Rejected new decision`, the failed read erased
the prior item, and the three refresh/write ordering cases committed an empty
`decisionMarkdown`.
```

This probe is the pre-fix evidence. It uses the real store producer and real
camel-case field mapping; only the network response is replaced.

## Live S4 evidence

The actual-atlas S4 run at
`docs/internal/philo/phase-6/body/red-s4-393/20260925T024432Z-case.closure.chain.s4_saved_content-astra-393/observation.json`
records:

```text
transition_probe.firstReadFrame.atMs = 11.900000005960464
transition_probe.firstReadFrame.editing = false
transition_probe.firstReadFrame.text = "DECISION\n\nKeep summary retrieval on the local desk after a hub restart. Owner: Leo Martinez."
initial_feedback.text = "DECISION"
terminal_outcome.first_satisfied_at_s = 1.374
```

The observer was armed before Done and saw a readable body immediately. The
900 ms delayed read then saw only the heading. The same observation's network
capture lists the successful PUT followed by a `GET /api/decisions` after the
click. This establishes that the initial transition is healthy and a later
refresh erases the body before a subsequent read restores it.

## Minimal repair proposed

Keep the current optimistic update at `dataSlice.ts:297–333`, and add a small
per-kind/item write version at that seam. A refresh snapshots those versions
before its reads. When a read resolves, it may replace an item only when that
item's version is unchanged; a decision write that began after the refresh
started therefore survives the stale response. This belongs in the store
refresh/update seam, so the production host and pullout keep one source of
truth. It does not require a local shadow in `DecisionPullout`.

At the same write seam, capture the prior item before applying the optimistic
patch. If the PUT refuses, restore that prior item synchronously when the
write version is still current, then call the existing
`reportWriteFailure`/receipt path and allow the refresh to continue. The
failed-save test keeps the prior body rendered while a slow or failed refresh
is pending. The version check prevents a late refusal from rolling back a
newer edit. This is the smallest repair that covers both the pre-write stale
read and the failed-save race without broad state-framework changes.
