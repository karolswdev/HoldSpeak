# PHILO-8-01 canvas: the zone name field in the list row

**Status: RATIFIED by the owner, 2026-09-26 (AskUserQuestion; review page https://claude.ai/artifact/CdReb8UtJBjXe98Cpv7MJz).** His answers, verbatim: (1) **"Ratify as drawn"** — the in-row field exactly as boards 1–6 and 8–10 show (the name selected; typing replaces; Enter or a click elsewhere saves; Escape keeps "New zone 2"; spaces only keeps the name; the field's style as drawn); (2) **"Chip on the list and the Floor"** — `✗ NAME TAKEN` on its own line under the field on both faces, replacing the Floor's 11 px sentence; a failed save (422 / network) in the same slot (`NOT SAVED`); a refusal after the field closed goes to the write receipt `RENAME ZONE` with Retry; (3) **"Keep F2 on zone rows"**. Built in half B (`web/src/desk/components/ZoneRenameRow.tsx`); the product shots are in `../story-01-shots/`.

- Review page (every board embedded, both widths): `docs/internal/philo/phase-8/rename-canvas/index.html`.
- Boards: `shots/<n>-<board>-<width>.png`; rendered facts: `shots/facts.json`.

## What the boards are, exactly

- **Everything is live.** `harness/shoot.py` starts a REAL hub (`scripts/graph_walk.py serve`, isolated HOME and database) and serves the PRODUCT app (`web/index.html`, `web/src/main.tsx`) with vite. The harness swaps ONE module: DeskApp's `./components/DeskListView` resolves to `harness/ProposedDeskListView.tsx` (`harness/vite.config.mjs`). Every other part of the Desk (DeskApp, DeskChrome, the palette, the store, the hub, the 409) is the product on this branch.
- **The proposal** (`harness/ProposedDeskListView.tsx`, three blocks marked `PROPOSAL`) is a copy of `web/src/desk/components/DeskListView.tsx` with:
  1. the zone row whose id is `renamingZoneId` draws the field in its Name cell: `input.desk-zone-rename` and the library `MicButton` (speak to fill), from the ONE rename behaviour `web/src/desk/hooks/useZoneRenameField.ts` (Enter writes, leaving the field writes, Escape keeps the name). The name opens selected, so typing replaces it;
  2. a refused name (the hub's `409 zone_name_taken`) shows on the row as the library `StateChip` `failure`, `✗ NAME TAKEN`, with `data-code="zone_name_taken"`; the field stays open with focus;
  3. F2 on a focused zone row opens the same field.
- **Boards 0 and 7** are the product as built on this branch (half A), served by the hub itself, not by the harness.
- **Writes are real.** Every board's POST/PUT/DELETE on `/api/directories` and its status is in `facts.json` (`writes`, cumulative per width).

## Boards

| # | Board | What it shows | Hub |
|---|---|---|---|
| 0 | Today (built, half A) | New Zone on the list makes `New zone 2`; nothing opens | `POST /api/directories` 201 |
| 1 | New Zone, the field opens | the `New zone 2` row holds the field, focused, the whole name selected (`facts.json` `field_selection` start 0, end 10 of 10), the mic beside it | 201 |
| 2 | Typing | `Platform team` in the field (typing replaced the selected name) | — |
| 3 | Enter | the row reads `Platform team`; the field is closed | `PUT /api/directories/{id}` 200; `GET /api/directories` lists `Platform team` |
| 4 | Escape | New Zone again, then Escape: the row keeps `New zone 2`, the field is closed | 201; no PUT |
| 5 | Refused | the field holds `Inbox` (a zone that exists); `✗ NAME TAKEN` on its own line under the field; the field stays open with focus. The columns do not move (the Kind head at x 676 on boards 1 and 5 at 1440, 249 at 393); the row grows from 41 to 75 px at 1440 (65 to 75 at 393), so the rows under it move down | PUT 409 `zone_name_taken` |
| 6 | F2 on a zone row | focus the `Platform team` row, press F2: the same field opens on that row | — |
| 7 | The Chair (built, half A) | the Chair's search for `New Zone`: no New Zone verb. It still lists the zone `New zone` under OBJECTS, to open it (it dives into the zone): Q2 (c) withholds only the verb that makes a zone. Shot after a reload, so the list matches the hub | — |
| 8 | A long name (MISSED state) | 8a: `Quarterly architecture review and platform roadmap` in the field (it scrolls inside the field); 8b: committed, the row shows it on one line; at 393 it runs past the right edge and pushes the Kind column off the screen (the table sizes columns by content: inherited, BACKLOG "PHILO-8-01 follow-ups") | PUT 200 |
| 9 | Spaces only (MISSED state) | New Zone, type three spaces, Enter: the name trims to nothing, no PUT is sent (`puts_added` 0), the field closes and the row keeps its default name (the same as Escape) | 201; no PUT |
| 10 | Two fast New Zone presses (MISSED state) | two presses inside one refresh: two zones (`New zone 5`, `New zone 6` on this run), zero 409s; the field opens on the LAST zone made; the first keeps its default name | 201, 201 |

## The strings (exact)

| Slot | String |
|---|---|
| The field's accessible name | `Zone name` |
| The default name (half A, built) | `New zone`, then `New zone 2`, `New zone 3`, … |
| Refused (StateChip `failure`) | `✗ NAME TAKEN` (`data-code="zone_name_taken"`) |
| Verbs | none new. The field has no Button: Enter writes, Escape keeps. The mic is the library `MicButton` (`Speak to fill`, its own label) |

No prose, no modal, no counter of zero. In the row, nothing is under 12 px: the field is 13 px (`--font-size-sm`), the chip 12 px. The MicButton is the library Button. The rest of the list is not: see Limits.

## Three questions for the owner

1. **The field in the row, as drawn?** The name field opens in the new zone's row with the name selected; Enter writes, a click elsewhere writes, Escape keeps the name (`New zone 2`) and closes the field. The same field serves F2. The field uses the Floor's field style (monospace, bold) while the row names are sans: keep it, or match the row? Recommended: yes to the field; the style is your call.
2. **A refused name: `✗ NAME TAKEN` on its own line under the field?** The field stays open with focus; the columns stay put and the row grows. The same chip also replaces the spatial Floor's sentence (`A zone named "Inbox" already exists`, 11 px, `web/src/desk/desk.css:245-252`, under the 12 px floor), so both faces show one species. Recommended: yes, on both faces.
3. **F2 on a focused zone row opens the field?** Zone rows cannot be selected on the list, so the registry's F2 does not reach them today. No row menu is proposed for zones. Recommended: yes.

## Fence sketch (the build after ratification; not built)

Real hub, isolated HOME, rendered at 1440 and 393, each red on main or on this branch before the face build:

| After | Assert | Red today |
|---|---|---|
| New Zone on the list | the `New zone 2` row holds `input.desk-zone-rename`, focused, its value selected | no field (board 0) |
| Type + Enter | `PUT` 200; `GET /api/directories` lists the name; the row reads it; no field | no field |
| Escape | no `PUT`; the row reads `New zone 2`; no field | no field |
| A taken name + Enter | `PUT` 409; the row's `[data-code=zone_name_taken]` reads `NAME TAKEN`; the field keeps focus; the Floor overlay shows the same chip | the list: no field; the Floor: the sentence |
| F2 on a focused zone row | the field opens on that row with focus | nothing happens |
| New Zone on the list, then Spatial view | no field on the Floor (built in half A: `test_no_stale_rename_field_after_a_face_change`) | green on this branch |
| A 422 / a network failure on Enter | the same chip slot shows the reason or `NOT SAVED`; the field keeps focus | reverts without a word |
| A taken name, then a click to another face | the write-receipt line reads `RENAME ZONE` with Retry | reverts without a word |
| A refusal on the row | the Kind head's x is the same before and after | — (board 5 measures it) |
| Every state | one Enter/blur/Escape path (`useZoneRenameField`); no text under 12 px in the row; the mic is `.btn` | — |

## Limits (what the boards are not)

- The boards are real interactions on a real hub, but the list module is a copy with the proposal; the product list is unchanged.
- **A failed rename is not drawn yet.** In half B a failed rename shows in the same chip slot: a 422 or a network failure as a StateChip `failure` with the hub's reason or `NOT SAVED`, the field keeping focus; a refusal that arrives after the field closed (a taken name, then a click to another face) goes to the desk's write-receipt line (`RENAME ZONE`, with Retry). One fence each (the Astra-role check r1, ruling on question 6). Today `renameZone` reverts these without a word (`web/src/desk/store/dataSlice.ts`, `renameZone`).
- **Inherited, not in this story** (BACKLOG "PHILO-8-01 follow-ups"): the list's census line reads `17 ITEMS · 8 ZONES` and `17 SHOWNS OF 17` (the bad plural from `countToken(visible.length, "SHOWN")`, `web/src/desk/components/DeskListView.tsx:289`), 10 px, as are the column heads, band heads and Kind/Zone cells (`facts.json` `small_text`); the 4 sort-header `<button>`s are raw (`web/src/desk/components/DeskSortableTable.tsx:96`, a UX-CANON §A.1 bounce); at 393 the Zone column is cut at the right edge, and one long name pushes the Kind column off the screen (board 8b).
- About 4.7 s pass from New Zone to the field (the field waits for the whole post-create refresh; cause of the duration unknown; BACKLOG).
- Board 10's zone numbers (5 and 6) come from the zones earlier boards made on the same hub.

## Reproduce

```bash
cd web && npm ci --ignore-scripts && npm run build && cd ..
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run python pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/harness/shoot.py
uv run python pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/harness/build_review.py
```
