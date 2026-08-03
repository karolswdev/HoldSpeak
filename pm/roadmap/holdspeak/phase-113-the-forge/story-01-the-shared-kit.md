# HS-113-01 - The shared kit

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-113-03, HS-113-06, HS-113-07, HS-113-08
- **Owner:** unassigned

## The thesis (the bar)

Every primitive window on the Desk must compose from the same kit
of reusable building blocks. Today there are four independent table
implementations, four independent mic+text composers, and hand-rolled
tabs/badges/footers in every window. This story extracts the shared
kit and wires existing components to adopt it. When the kit ships,
a new primitive window is a composition exercise, not a greenfield
build. This IS the Workbench 2.0+ consistency promise.

**Articles served:** VII (one window grammar, quiet chrome),
VIII (native-grade craft, consistent quality), I (one persistent
Desk world — one visual language).

## Ground (from the pre-charter survey)

**Four independent table/list implementations:**
- `web/src/desk/components/ZoneWindow.tsx` — hand-rolled `<table>`
  with sort headers, icon column, name/kind/modified columns.
- `web/src/desk/surface/Surface.tsx` — `SurfaceLedger` and
  `SurfaceLedgerRow`, used by `DeskListView` for the desktop floor.
- `web/src/desk/components/PrReceiptsSection.tsx` — another
  hand-rolled `<table>` with verb columns and expandable rows.
- `web/src/desk/components/AttentionDrawer.tsx` — an `<ol>` with
  button children, severity marks, timestamps.

**Four independent mic+text composers:**
- Pullout's capability run section (`desk-chat-well`)
- Pullout's coder answer section (same classes, different structure)
- PrReceiptsSection's `desk-mic-row`
- AskBar's composer

**Existing kit components NOT adopted:**
- `SurfaceWings` in `gadgets.tsx` — exists but ZoneWindow hand-rolls
  its own tab buttons instead of using it.
- `EgressChip` in `gadgets.tsx` — exists but Pullout hand-rolls
  `<span className="egress-badge">`.
- `SurfaceState` — proper loading/error/empty treatment exists but
  ZoneWindow, PrReceiptsSection, and AttentionDrawer use ad-hoc
  paragraphs.

**Filing strip duplication:**
- Pullout has 70 lines of hand-rolled zone/KB/project membership
  UI. Any new filable primitive would duplicate this verbatim.

## Method

1. **DeskSortableTable** — extract a shared sortable, expandable
   table component with:
   - Generic `data` + `columns` + `sort` + `onSort` props
   - Sort header buttons with `aria-sort` and direction arrows
   - Roving keyboard focus
   - Optional row verbs (hover-reveal actions)
   - Optional row expansion (detail panels)
   - Consistent row height, mono font, hover state from shared CSS
   - `emptyLabel` prop (defaults to "Empty", never prose)

2. **DeskIconGrid** — extract the icon grid layout from ZoneWindow:
   - Generic items array with key/src/label
   - Configurable cell size (48 or 64)
   - `auto-fill` responsive grid

3. **DeskComposer** — extract the mic+text+action input well:
   - MicButton + text field + action button
   - `multiline` toggle (input vs textarea)
   - `draftScope` for persistent drafts
   - Optional footer slot (for grounding chips, model picker)

4. **DeskFilingStrip** — extract the membership/belonging section:
   - Takes objectRef, objectKind, objectId
   - Renders zone/KB/project chip toggles
   - Handles membership API calls internally

5. **DeskReceiptInset** — extract the aerogel receipt treatment:
   - Wraps `surface-aerogel` class with consistent structure
   - Optional timestamp stamp line

6. **DeskWindowFooter** — extract the window footer bar:
   - Left: status/count
   - Right: action chips (children)

7. **DeskPropertySheet** — extract key-value property display:
   - Entries array with key/label/value/editable/onEdit
   - In-place editing via EditInPlace where backed

8. **DeskSearchFilter** — extract in-window search + filters:
   - Query input + cycle/select filters + apply

9. **Adopt existing kit components:**
   - Wire `SurfaceWings` into ZoneWindow via DeskWindowFrame's
     `wings` prop (remove hand-rolled tabs)
   - Replace Pullout's hand-rolled egress span with `EgressChip`
   - Replace PrReceiptsSection's hand-rolled egress span
   - Replace ZoneWindow's `<p>Empty</p>` with `SurfaceState`
   - Replace PrReceiptsSection's ad-hoc empty with `SurfaceState`
   - Replace AttentionDrawer's ad-hoc empty with `SurfaceState`

10. **Retire SurfaceLedger from list-view use** — keep only if other
    non-list surfaces still reference it.

## Test plan

- Unit: each new component renders with minimal props.
- Unit: DeskSortableTable sorts by column, fires onSort, renders
  empty state, handles row expansion.
- Unit: DeskComposer fires onChange/onAction, renders mic button,
  supports multiline toggle.
- Unit: DeskFilingStrip renders zone/KB/project chips for a known
  object, toggles membership on click.
- Regression: ZoneWindow with SurfaceWings adoption still passes
  all existing tests.
- Regression: Pullout with EgressChip adoption matches existing
  behavior.
- Regression: all existing `DeskListView.test.tsx` tests pass after
  SurfaceLedger removal.
- Screenshot walk: 1440px — ZoneWindow list view, Pullout, PR
  receipts, AttentionDrawer. All four must look like one system.
- Screenshot walk: 393px — same four surfaces, responsive behavior
  preserved.
