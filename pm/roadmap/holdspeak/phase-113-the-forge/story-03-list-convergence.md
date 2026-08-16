# HS-113-03 - List convergence

- **Project:** holdspeak
- **Phase:** 113
- **Status:** done
- **Depends on:** HS-113-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The desktop list view and the drawer list view must be the same visual
language. A user switching between "everything on my desk" and "inside
this drawer" should see the same table structure, the same columns,
the same sort affordances, the same row density, and the same
interaction grammar. The desktop list is a drawer scoped to the whole
desk, not a different component.

**Articles served:** I (one persistent Desk world), VII (one window
grammar), VIII (native-grade craft).

## Ground (from the pre-charter survey)

- `web/src/desk/components/DeskListView.tsx` — the desktop list uses
  `SurfaceLedger` with fixed 26px mono rows, textual `[x]/[ ]`
  selection marks, kind-banded grouping, and a census header
  (`ITEMS n . ZONES n . ATTN n`).
- `web/src/desk/surface/Surface.tsx` — `SurfaceLedger` and
  `SurfaceLedgerRow` are the shared ledger components. They use
  roving focus and a flex layout with selection mark, flexible title,
  and fact/state cells.
- `web/src/desk/components/ZoneWindow.tsx` — the drawer list uses a
  proper HTML `<table>` with sprite icons, sortable Name/Kind/Modified
  headers, hover-reveal "Take out" action, and item count footer.
  Default view is icon grid; list is an explicit toggle.
- `web/src/desk/desk.css` lines ~2938-3060 — desktop list styling.
  Lines ~4987-5075 — zone window styling.
- `web/src/desk/world.ts` — `worldObjects()` and `worldZones()`
  already project all desk items into a unified shape. The data is
  there; only the presentation diverges.
- `web/src/desk/store.ts` — `DeskView = "spatial" | "list"`;
  `ZoneViewPref` with `view: "icons" | "list"`, `sort`, `dir`.
  Desktop list has no per-column sort; drawer list does.

## Method

1. Extract the drawer list table from `ZoneWindow.tsx` into a shared
   `DeskTable` component that accepts a generic item array, column
   definitions, sort state, and row actions.
2. Define column sets:
   - **Drawer scope:** icon, Name, Kind, Modified, Take out.
   - **Desk scope:** icon, Name, Kind, Zone, Attention, context menu.
   Zone and Attention replace Take out. Selection (for Ask context)
   becomes a checkbox column, not a textual `[x]`.
3. Rebuild `DeskListView.tsx` to render `DeskTable` with the
   desk-scope columns and the full `worldObjects()` data set.
   Kind-banded section headers remain as `<tbody>` group rows.
4. Rebuild `ZoneWindow.tsx` list mode to render `DeskTable` with
   drawer-scope columns.
5. Both tables inherit the same row height, font, hover state, and
   sort affordance styling from shared CSS.
6. Preserve zone-level Icons/List toggle in `ZoneWindow`. Add the
   same toggle to `DeskListView` — desktop gets an icon grid too.
7. Retire `SurfaceLedger` from list-view use (keep it only if other
   surfaces still reference it; otherwise delete).

## Test plan

- Unit: `DeskTable` renders with desk-scope columns, sorts by each
  column, fires row actions.
- Unit: `DeskTable` renders with drawer-scope columns, sorts, fires
  Take out.
- Unit: `DeskListView` uses `DeskTable`, shows kind-banded groups,
  preserves Ask-context selection via checkbox.
- Unit: `ZoneWindow` list mode uses `DeskTable`, preserves Take out
  and sort persistence.
- Visual regression: existing `DeskListView` tests still pass.
- Screenshot walk: 1440px desktop list with 20+ items across 4+
  kinds. Compare side-by-side with a drawer list of the same items.
  They must read as one system.
- Screenshot walk: 393px mobile — table scrolls horizontally in its
  own container, no body overflow.
