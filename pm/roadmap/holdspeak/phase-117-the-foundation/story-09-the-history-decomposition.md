# HS-117-09 — The history decomposition

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-07
- **Unblocks:** ---
- **Owner:** unassigned

## The thesis (the bar)

`HistoryCore.tsx` is 1,334 lines -- the second-largest core. It has
three heavyweight blocks: `MeetingDetail` (465 lines, 324-788) with
6 parallel API calls and 7 extractable JSX sub-sections, the
`HistoryCore` export itself (544 lines, 790-1333) with 16 `useState`
calls, and `ImportSection` (122 lines, already self-contained).
`MeetingDetail` alone contains a needs-you table builder, transcript
well, artifacts library, and aftercare gadgets -- four unrelated
concerns in one component.

When this story ships, `HistoryCore.tsx` is a thin shell (~200 lines)
that composes sub-components from `web/src/pages/cores/history/`.
Each sub-component owns its data and rendering. The file drops from
1,334 to ~200 lines.

**Articles served:** VI (honest construction -- 465-line components
mixing 4 concerns are not honest), X (sustainability -- isolated
meeting-detail sections are independently testable).

## Deliverables

### 1. Create `history/` directory and barrel

Create `web/src/pages/cores/history/index.ts` re-exporting every
sub-component. `HistoryCore.tsx` imports from the barrel only.

### 2. Extract and decompose `MeetingDetail` (lines 324-788)

Move to `history/MeetingDetail.tsx`, then decompose its 465 lines:

- `history/MeetingHeader.tsx` (lines 531-556): record header with
  state token, duration, clock time. ~40 lines.
- `history/CaptureSlab.tsx` (lines 559-581): the attention slab
  for active captures. ~30 lines.
- `history/ArtifactsLibrary.tsx` (lines 600-671): `SurfaceLibrary`
  with tile mapping for meeting artifacts. ~80 lines.
- `history/NeedsYouTable.tsx` (lines 451-526 builder + 676-695
  render): proposals + open actions mapped to a table. ~90 lines.
- `history/TranscriptWell.tsx` (lines 697-724): the transcript
  viewer with segment rendering. ~40 lines.
- `history/SettledList.tsx` (lines 726-745): settled actions with
  routing fold. ~30 lines.
- `history/AftercareGadgets.tsx` (lines 757-783): post-meeting
  follow-up gadgets. ~40 lines.
- `history/useMeetingData.ts`: hook owning the 6 `useState` calls
  and the `useEffect` with 6 parallel API fetches (lines 343-456).
  ~120 lines.

After extraction, `MeetingDetail.tsx` is ~80 lines of composition.

### 3. Extract the catalog rail (lines 960-1120)

Move to `history/CatalogRail.tsx`. The meeting ledger with date
grouping, filters, status tokens, and row rendering. ~160 lines,
self-contained.

### 4. Extract the door section (lines 1124-1227)

Move to `history/DoorSection.tsx`. Cross-meeting plumbing views
keyed by `DOOR_SECTIONS` (actions/speakers/projects/queues).
~104 lines.

### 5. Extract `ImportSection` (lines 201-322)

Move to `history/ImportSection.tsx`. Already self-contained at
122 lines: file drop/browse, metadata fields, form submission.
Pure relocation.

### 6. Extract helpers and constants (lines 81-196)

Move to `history/helpers.ts`: `displayState`, `stateToken`,
`StateTokenSpan`, `MONTHS`, `ledgerDate`, `durationToken`,
`clockTime`, `download`, `WINGS`, `DOOR_SECTIONS`. ~120 lines.

### 7. Slim down `HistoryCore.tsx`

The remaining shell: imports from `history/`, the `HistoryCore`
export composing sub-components via wings, the receipt bar footer
(1281-1330), and the face router (1240-1264). Target: ~200 lines.

## What NOT to do

- Do NOT change any rendering logic or visual output. Pure
  decomposition -- move code, do not rewrite it.
- Do NOT rename the `displayState`/`stateToken` helpers. Other
  files may import them.
- Do NOT merge `ImportSection` into another component. It is
  already well-isolated.
- Do NOT add new features or fix bugs found during the move.
- Do NOT refactor the 6 parallel API fetches into a single call.
  That is a backend concern, not a decomposition task.

## Test plan

1. `npx tsc --noEmit` -- zero type errors.
2. `npx vitest run` -- all existing web tests pass.
3. Verify `HistoryCore.tsx` is under 250 lines:
   `wc -l web/src/pages/cores/HistoryCore.tsx` < 250.
4. Verify the `history/` barrel exports all sub-components:
   `grep -c "export" web/src/pages/cores/history/index.ts` >= 8.
5. `uv run pytest -q` -- backend tests unaffected.
6. Playwright screenshot walk at 1440px and 393px -- the history
   surface (catalog, meeting detail, import, door sections)
   renders identically.

## Estimated scope

~1,130 lines moved into ~12 new files under `history/`. ~200
lines remain in `HistoryCore.tsx`. Net new lines: ~50 (imports,
barrel, prop interfaces for extracted components).
