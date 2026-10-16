# People, projects and common controls — Lane C

Status: implemented; HOLD FOR SHIP. No staging, commit or push.
Worktree: `/Users/karol/dev/tools/wt-cohesive-workflows-20261015`.
Branch: `feat/cohesive-workflows-20261015`; base `7f3345745`.
Direction: `DESIGN.md`, Lane C. GO received after root read the library
canvas at 1440 and 393. Tuesday: a failed lookup keeps the draft; a merged
source action waits for every attempt and retries only failed watches.

## Changes

- `PeopleCore.tsx`: calendar loading, named failure with Retry, and true empty
  are separate states inside the existing picker. Retry retains the note and
  selected person. Creating a Workbench item no longer invents model egress.
- `ProjectRoomCore.tsx`: Pause, Resume and Remove use `Promise.allSettled`, then
  await the authoritative Room reload. Per-source failures retain only rejected
  watch IDs. Retry calls those IDs only; accepted siblings are not replayed.
  The existing Room read failure owns a failed reload after accepted writes.
  A ref guards repeated presses until the attempts and reload finish.
- `MeetingDetail.tsx`: the People read has a pending fact and one compact
  ActionNotice beside the first active owner gap. Retry retains task/date/owner
  draft state and updates the People choices.
- `DoorCore.tsx`: New Project uses a labeled StringGadget with its existing
  mic authority and outcome setter. The old field wrapper is removed, so the
  library owns the well. The length limit and test/input identity remain.
- `ZoneWindow.tsx`: genuine empty renders `No items`, with no dead action.
- `InfoWindow.tsx` and INFO rules in `window-chrome.css`: lineage, rename and
  summary actions are library Buttons; unresolved lineage is disabled. Names,
  lineage and property values are bounded; narrow properties use the existing
  surface container. No unrelated chrome rules changed.
- `SurfaceWindows.tsx`: lazy loading uses SurfaceState.
- `DeskMenu.tsx`: Left at 393 climbs one level, as Back does. Left from a wide
  submenu focuses the actual opener, including the second trigger.
- `CapabilitySection.tsx`, `DeliveryBoard.tsx`, `WorkbenchResourceful.tsx`:
  custom raw action buttons become library Buttons. Existing action arguments
  remain. Resourceful policy actions expose pending state and guard one write.

Tenets: 2/3 (the owner's first working flow and recovery), 4 (plain state
labels), 5 (the existing component framework). No new framework, route,
service, storage contract or store. Needs you scrolling was not changed.

## Focused proof

All runs used `.venv/bin/python .tmp/cohesive/locked.py LABEL --web node
node_modules/vitest/vitest.mjs ...`, which takes the shared machine test lock,
uses an isolated HOME and disables machine-state integration. No native mic,
owner DB, Keychain, provider, tmux, build, typecheck or broad suite was run.

Original lane collection, before the follow-up seam below: `list` of the ten
files below. Actual output:

```
COLLECTION: 140 tests, 10 files
 8 src/desk/__tests__/infoContract.test.ts
 7 src/desk/__tests__/workMenu.philo1315.test.tsx
20 src/desk/__tests__/workMenu.test.tsx
 2 src/desk/components/DeliveryBoard.test.tsx
 4 src/desk/components/__tests__/commonControls.test.tsx
 3 src/desk/components/__tests__/zoneWindow.test.tsx
 6 src/features/project-room/__tests__/room175sources.test.tsx
37 src/features/project-room/door/__tests__/DoorCore.test.tsx
27 src/pages/cores/__tests__/peopleCore.test.tsx
26 src/pages/cores/history/__tests__/meetingKit.phase16.test.tsx
```

Collection log: `.tmp/cohesive/lane-c-final-collect.log`.

Original lane run: `run --maxWorkers=2` of exactly those ten paths. Actual tail:

```
 Test Files  10 passed (10)
      Tests  140 passed (140)
   Start at  23:20:33
   Duration  6.16s (transform 1.68s, setup 407ms, import 3.09s, tests 6.21s, environment 1.65s)
```

Run log: `.tmp/cohesive/lane-c-final-focused.log`.
First pass: 138/139 passed; the sole failure required the removed invented
cloud badge. Its obsolete assertions now check absence. Log:
`.tmp/cohesive/lane-c-focused.log`.

New regressions drive rendered outcomes: merged Pause/Resume/Remove partial
failure and sibling settlement; read-only recovery after accepted writes;
calendar failure/loading/empty with a retained note; People lookup retry with
retained task/date; narrow one-level Left and the second wide submenu opener;
Delivery source/dossier argument authority; resolved/unresolved Info lineage;
passive Zone empty; one pending resourceful write; capability busy/output/
artifact/assignment actions. The Door mock carries the library's label,
input attributes and one mic callback.

## Limits and handoff

The tests use API/store doubles. They establish local transitions and argument
contracts, not provider behavior or live appearance. Root owns the built-bundle
walk at 1440/393, especially Door material, Info long names/properties, compact
Meeting failure, and plated Button fit/hit ownership. Root owns final complete
quick checks and TypeScript. No screenshot or live capture claim is made here.


## Follow-up seams — final freeze

Root granted `desk/lineage.ts` and focused `desk/__tests__/lineage.test.ts`
after the live Get Info fixture preparation exposed canonical `note:<id>`
sources as falsely unavailable. The resolver now normalizes qualified aliases
with `api.qualifiedRef`, restricts qualified candidates to exact canonical
identity, and uses `world.objectByRef` for resolution and names. It supports
bare legacy IDs, canonical note/knowledge/project refs, and the existing
kb/zone/persona/sequence aliases. A raw ID in another kind cannot capture a
qualified reference. The stored lineage `ref` remains intact; the chosen
canonical `actionRef` drives Get Info's open action.

Root's finished-source check also found that `useWriteReceipt` Retry replays
the inner callback, bypassing the Resourceful policy pending guard. The same
local guard/loading ownership now lives inside that replayed callback. No
shared receipt hook or other surface was changed for this correction.

Focused collection: `list src/desk/__tests__/lineage.test.ts
src/desk/components/__tests__/commonControls.test.tsx` under the same helper.
Actual collection: 16 lineage tests, 6 common control tests, 22 total.
Log: `.tmp/cohesive/lane-c-seam-collect.log`.

Final follow-up run: `run --maxWorkers=2` of those two paths, under the same
machine lock and isolated HOME. Actual tail:

```
 Test Files  2 passed (2)
      Tests  22 passed (22)
   Start at  23:36:06
   Duration  1.25s (transform 448ms, setup 117ms, import 581ms, tests 440ms, environment 358ms)
```

Log: `.tmp/cohesive/lane-c-seam-final-focused.log`.

The lineage cases include same-ID Note/Meeting/Knowledge/Project collisions,
qualified-looking raw IDs in the wrong kind, missing canonical targets,
qualified aliases, legacy bare IDs and preserved via identity. Common controls
now drive an Artifact's canonical Note lineage Button through the real
`useDesk.openPullout` and assert the Note pullout, with a same-ID Meeting
present; loaded Knowledge and Project Buttons remain enabled, missing sources
disabled. The resourceful regression uses the real receipt hook: refused
Enable → Retry pending → Pause disabled → Enable settles → Pause succeeds,
with write flags `[true, true, false]`.

Source freeze: HOLD FOR SHIP, unstaged, no commit/push. The original lane run
and this follow-up are separate scoped results; root owns the final combined
quick/TypeScript and real canonical lineage walk at 1440 and 393.
