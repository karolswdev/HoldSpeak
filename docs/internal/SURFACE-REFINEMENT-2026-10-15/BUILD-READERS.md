# Readers — built and focused checks complete

Source frozen; HOLD FOR SHIP. Base `a81364a0d`. Root owns live inspection,
quick check and release. No browser, build, install, stage or commit ran here.

History now uses StringGadget with its existing mic scope, keeps the stream
and source strip, and names unavailable changes with a real handleRefresh
retry. Both stream and footer suppress quiet-day/week claims for non-OK
changes. Successful reads distinguish No history yet, No changes from the
chosen source and No matching changes. Clear filters resets source/query
locally; current wing, History item opening and folded Writes stay in place.

Knowledge uses one Entries section and one wrapping room ledger. Every
stored reference retains its row identity (`data-member-ref`, title and
line label). Resolved members have real Open; unresolved members have
Item unavailable/Unavailable and no Open. Copy keeps stored order and uses
each resolved title or exact unresolved ref. Only true empty membership
says No entries. Reader membership remains aggregate-only. Filing strip,
Edit/Done and footer receipts/actions retain their existing paths.

Owned changes:

- `web/src/features/project-room/ProjectRoomCore.tsx` — History and its footer.
- `web/src/features/project-room/project-room.css` — removes the custom raw
  search style; lets the library gadget fill its existing search slot.
- `web/src/desk/pullouts/KbPullout.tsx` — member rows and honest Copy.
- `web/src/features/project-room/__tests__/room.app.test.tsx` — five new
  rendered state/retry/filter checks using the recorded BARE_ROOM envelope
  and exact producer section states.
- `web/src/desk/pullouts/KbPullout.test.tsx` — four new rendered checks with
  embedded exact selected rows from root's real `/api/kbs` and `/api/notes`
  answers at `.tmp/surface-refinement/recorded-wire/wire.json`.

The approved existing `web/src/desk/components/InlineEditor.test.tsx` and
`web/src/desk/pullouts/editors/editorRepair.test.tsx` ran unchanged. No
controller, backend, shared kit, sibling, canon or status file changed.

Exact scoped commands (worktree root; helper isolates HOME and takes the
machine test lock; all paths below are relative to `web/`):

```sh
.venv/bin/python .tmp/surface-refinement/locked.py readers-collect --web ./node_modules/.bin/vitest list src/features/project-room/__tests__/room.app.test.tsx src/desk/pullouts/KbPullout.test.tsx src/desk/components/InlineEditor.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx --maxWorkers=2
.venv/bin/python .tmp/surface-refinement/locked.py readers-red --web ./node_modules/.bin/vitest run src/features/project-room/__tests__/room.app.test.tsx src/desk/pullouts/KbPullout.test.tsx src/desk/components/InlineEditor.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx --maxWorkers=2 --reporter=dot
.venv/bin/python .tmp/surface-refinement/locked.py readers-green-freeze --web ./node_modules/.bin/vitest run src/features/project-room/__tests__/room.app.test.tsx src/desk/pullouts/KbPullout.test.tsx src/desk/components/InlineEditor.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx --maxWorkers=2 --reporter=dot
```

Collection exit 0; 62 tests listed in `readers-collect.log`. The new names:

```text
Knowledge reader membership > retains available and unavailable stored members, with Open only on a real object
Knowledge reader membership > keeps all-unavailable membership distinct from an empty collection and copies its ref
Knowledge reader membership > copies every member in stored order using real titles or unresolved qualified refs
Knowledge reader membership > reserves No entries for genuinely empty stored membership
History reader states > names degraded history without false quiet claims and retries into the same wing
History reader states > names absent history without false quiet claims and retries into the same wing
History reader states > shows true empty history after a successful read
History reader states > names a source miss and clears it back to the recorded changes
History reader states > uses the library search with its mic, names a query miss and clears query and source
```

Original source, after test additions and before product edits:

```text
Test Files  2 failed | 2 passed (4)
     Tests  8 failed | 54 passed (62)
  Duration  5.07s
```

`readers-red.log` names three Knowledge failures (lost rows/shortened Copy)
and all five History failures (missing unavailable/empty/miss states and raw
search). True empty Knowledge already passed. Intermediate repair runs
corrected the StateChip import and test assumptions about the existing
Created label, unsupported mic suffix and the Room's inference-editor POST.

Final source, public StateChip import included, exit 0:

```text
Test Files  4 passed (4)
     Tests  62 passed (62)
  Start at  02:01:53
  Duration  4.79s (transform 1.60s, setup 197ms, import 2.67s, tests 4.22s, environment 718ms)
```

Logs are `.tmp/surface-refinement/readers-{collect,red,green-freeze}.log`.
Existing React act warnings in RoomFilesSection/InlineEditor are also in
the original-source red run. `git diff --check` on the five owned source/test
paths was clean. No wider check was requested or run.

Unknown: production fit at 1440/393, pointer ownership, voice capture and
browser clipboard. The focused checks prove rendered state, opener arguments,
copy payload/receipt, and existing editor custody; they do not prove glass.
Root has the real before captures and owns the corresponding after walk.
