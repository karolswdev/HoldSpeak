# PHILO-8-01 canvas: the zone name field in the list row

**Status: FOR THE OWNER'S RATIFICATION (2026-09-26).** Nothing on this canvas is built in the product. Half A of story 01 is built on this branch (the free name, the Chair without New Zone, the face-change rule); this canvas is the face half the owner ruled on in Q2 (c): "on the list, the name field opens in the new zone's row".

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
| 1 | New Zone, the field opens | the `New zone 2` row holds the field, focused, the name selected, the mic beside it | 201 |
| 2 | Typing | `Platform team` in the field | — |
| 3 | Enter | the row reads `Platform team`; the field is closed | `PUT /api/directories/{id}` 200; `GET /api/directories` lists `Platform team` |
| 4 | Escape | New Zone again, then Escape: the row keeps `New zone 2`, the field is closed | 201; no PUT |
| 5 | Refused | the field holds `Inbox` (a zone that exists); the row shows `✗ NAME TAKEN`; the field stays open with focus | PUT 409 `zone_name_taken` |
| 6 | F2 on a zone row | focus the `Platform team` row, press F2: the same field opens on that row | — |
| 7 | The Chair (built, half A) | the palette on the Chair: no New Zone | — |

## The strings (exact)

| Slot | String |
|---|---|
| The field's accessible name | `Zone name` |
| The default name (half A, built) | `New zone`, then `New zone 2`, `New zone 3`, … |
| Refused (StateChip `failure`) | `✗ NAME TAKEN` (`data-code="zone_name_taken"`) |
| Verbs | none new. The field has no Button: Enter writes, Escape keeps. The mic is the library `MicButton` (`Speak to fill`, its own label) |

No prose, no modal, no counter of zero. The field is 13 px (`--font-size-sm`); the chip is 12 px. Every Button in the row is the library Button (the MicButton); the 4 raw `<button>`s `facts.json` counts in the list are the sort headers of `DeskSortableTable.tsx:96`, inherited.

## Three questions for the owner

1. **The field in the row, as drawn?** The name field opens in the new zone's row with the name selected; Enter writes, a click elsewhere writes, Escape keeps the name (`New zone 2`) and closes the field. The same field serves F2. Recommended: yes.
2. **A refused name: `✗ NAME TAKEN` on the row?** The field stays open with focus. The same chip also replaces the spatial Floor's sentence (`A zone named "Inbox" already exists`, 11 px, `web/src/desk/desk.css:245-252`, under the 12 px floor), so both faces show one species. Recommended: yes, on both faces.
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
| Every state | one Enter/blur/Escape path (`useZoneRenameField`); no text under 12 px in the row; the mic is `.btn` | — |

## Limits (what the boards are not)

- The boards are real interactions on a real hub, but the list module is a copy with the proposal; the product list is unchanged.
- The rest of the list is inherited as it is: the census line `17 ITEMS · 8 ZONES` and `17 SHOWN of 17` are 10 px (under the floor), and at 393 the Zone column is cut at the right edge (`1 ITEM` reads `1 ITEI`). Not in this story's scope; filed with the story's follow-ups.
- `renameZone` drops a 422 and a network failure without a word (`web/src/desk/store/dataSlice.ts`, `renameZone`: "revert silently"). Observed, not changed here.

## Reproduce

```bash
cd web && npm ci --ignore-scripts && npm run build && cd ..
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run python pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/harness/shoot.py
uv run python pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/harness/build_review.py
```
