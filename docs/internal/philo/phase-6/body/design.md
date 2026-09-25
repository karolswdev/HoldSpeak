# PHILO-6-05 proposed repair design

Date: 2026-09-24

Status: checked and implemented; hold for SHIP. Check:
`pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/story-05-design-astra-invoked-claude.md`.

## Evidence the design addresses

The production S4 observer is armed before Done and samples every frame. The
continuous 393 run is
`red-s4-393-continuous/20260925T025111Z-case.closure.chain.s4_saved_content-astra-393/observation.json`.
The matching 1440 run is
`red-s4-1440-continuous/20260925T025400Z-case.closure.chain.s4_saved_content-astra-1440/observation.json`.
Their captured decision traffic and transition traces show:

```text
GET /api/decisions started 2287.1 ms, resolved 2297.1 ms, blank body
PUT /api/decisions/<id> started 3928.3 ms, resolved 3939.8 ms, saved body
first post-Done frame 10.8 ms: full body readable
first unreadable frame 159.1 ms: text is only "DECISION"
GET /api/decisions (collection) started 4241.9 ms, resolved 4255.9 ms, saved body

1440 repeats the order: the first frame is readable at 10.1 ms, the first
unreadable frame is at 77.3 ms, the pre-write GET starts at 2265.0 ms, the
PUT completes at 3880.7 ms, and the post-PUT GET starts at 4180.4 ms.
```

The first frame is therefore already healthy. The defect is the later commit:
the CREATE emits `desk_changed`, `useDeskChangedRefresh.ts:38,52` starts its
refresh after the 300 ms trailing delay, and the pre-write decision read is one
member of `loadAll()`. The whole result waits on a slower sibling before it is
committed after Done. `dataSlice.ts:162–191` has no write fence around the
whole `items` replacement. The browser host is live: `DeskApp.tsx:80,
133–135` subscribes to `items` and derives the object on every render. The
continuous traces do not identify which `loadAll` sibling holds the commit;
that is the only remaining runtime unknown. The GET resolves before the PUT,
so a hub read serving a post-PUT stale snapshot is ruled out.

The red focused probe is
`web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx`; its raw tail
is `probe-tests.log`. It mounts the existing `useDeskWriteReceipt` channel
and asserts `SAVE FAILED` in the rendered receipt before checking the restored
body. It uses the real Zustand store and `updatePrimitive`; only transport
responses are controlled. Existing receipt coverage also remains green in
`receipt-tests.log` (the receipt suites plus `philo301RetryKept`) and the
existing DecisionPullout save path remains green in
`decision-pullout-tests.log`.

## Store-local state

Keep the repair in `createDataSlice`, so each store instance owns a small map
and tests do not share write state:

```ts
type PrimitiveWriteState = {
  version: number;
  pending: boolean;
  rollback?: { id: string; version: number; token: number };
};
const primitiveWrites = new Map<string, PrimitiveWriteState>();
```

The key is the normalized item bucket and id, for example
`decision:decision_probe`. A write increments its key's version immediately
before the optimistic patch and marks the state pending. The previous item is
captured at the same seam for refusal rollback.

No local shadow belongs in `DecisionPullout`; its existing
`updatePrimitive("decision", ...)` seam remains the producer.

## Refresh fence

At the first line of `refresh`, copy the write map before starting
`loadAll()`/`loadSetup()`:

```ts
const refreshSnapshot = new Map(
  [...primitiveWrites].map(([key, state]) => [key, { ...state }]),
);
```

When the reads finish, merge each incoming bucket with the current bucket
before committing `items`. Preserve the current item when either condition is
true:

1. its current version is greater than the snapshot version (the write began
   after this refresh started); or
2. the snapshot had the same version marked pending (the write was already in
   flight when this refresh started).

The second condition closes the during-write race. It keeps the optimistic
item even if the PUT resolves before the stale refresh commits. The merge must
preserve protected current items that are absent from the incoming bucket as
well as items with matching ids.

The refusal path starts one protected refresh with a transient rollback
descriptor `{ kind, id, version, token }`. If that refresh reports the
protected kind as unreachable, retain only the protected current item while
that refresh commits; do not retain the whole bucket or any other kind. An
empty fallback from that failed read is not an authoritative deletion and must
not erase the rollback body. Clear the descriptor when its own refresh
commits. A protected item missing from the incoming bucket can therefore
outlive a concurrent delete until that one refresh finishes; delete and rename
races are outside this story.

## Write result fence and refusal

`updatePrimitive` captures `{ previousItem, version }` before applying the
existing optimistic mapping. On success, it clears the receipt and records
`keptAt` only if its version is still current; an older success cannot clear a
newer write's refusal or claim that newer value was kept.

On refusal or transport failure:

1. If the key still has the failed write's version, synchronously restore its
   captured previous item, mark that version no longer pending, and issue the
   protected rollback refresh.
2. Keep the existing `reportWriteFailure` receipt visible for this current
   write while the rollback refresh is pending.
3. If a newer version exists, do not restore the older previous item, do not
   issue its refresh, and do not call `reportWriteFailure`. A stale refusal
   must not leave a Retry closure that can replay its superseded patch.

The current-version check is required on rollback, receipt publication, and
success handling. It prevents a late response from an older PUT from changing
the newer write or clearing its receipt.

## Focused red cases

The probe has seven tests. Two are controls: the held-prop synthetic case is
explicitly a negative control, and the subscribed production host renders the
optimistic value before refresh. Five are red before this repair:

- a refresh begun before Done must not overwrite the body when its whole
  `loadAll()` result commits later;
- a refresh begun while the PUT is pending must not overwrite the body after
  the PUT resolves;
- a failed save must restore the prior body before a delayed refresh resolves;
- a failed save must keep the prior body and receipt when the Decision read
  fails;
- a newer write that succeeds before an older refusal must keep its body and
  leave no stale SAVE FAILED receipt or Retry for the old patch.

The tests intentionally use the real store producer and rendered
`ProductionHost` projection. They do not establish the old held-prop probe as
the production cause.

## Acceptance distinction

The first-frame-only assertion was green on main. The first-frame criterion is
already satisfied by the live S4 trace at 10.8 ms. The strengthened criterion
is continuous: the observer is armed before the click, the first read frame is
readable, and every frame through terminal observation stays readable. The
continuous fence is the pre-fix red. The repair is therefore judged against
both the initial transition and the later refresh commit, with the failed-save
fence covering the receipt and prior body.

## Post-check scoped validation

The implementation changes only `web/src/desk/store/dataSlice.ts`; the
DecisionPullout seam remains `DecisionPullout.tsx:66–67`. The focused diagnosis,
DecisionPullout, receipt, Retry, and guard suites pass 29 tests. The exact
collected names are in `scoped-collect.log` and the verbose run tail is in
`scoped-green.log`. The origin/main overlay remains red before the product
change in `origin-main-red.log`, with its seven collected names in
`origin-main-collect.log`.
