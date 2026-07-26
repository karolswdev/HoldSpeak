# HS-105-03 - Zones are windows — density with chosen altitude

- **Project:** holdspeak
- **Phase:** 105
- **Status:** done
- **Depends on:** HS-105-01
- **Unblocks:** HS-105-07
- **Owner:** unassigned

## The reference (the bar)

A Workbench drawer opened into a real window: an icon grid you
could re-view as Name/Date/Size lists, sort, clean up, and
SNAPSHOT — the window remembered its position, its view mode, and
every icon's place within it. Density was the user's choice, and
the arrangement was sacred at every level, not just the desktop.
The desk's zones today are containers with a face (the "2 items"
chip) but no interior altitude: opening one gives a single fixed
presentation, and a zone with thirty objects has nowhere honest to
put them.

## Problem

Zones cannot hold a working set. There is no list view, no sort, no
per-zone remembered arrangement, so the desk's answer to "forty
things" is either world sprawl or an undifferentiated pile — and an
OS is exactly the thing that answers "forty things" calmly.

## Recipe

1. **A zone opens into a real desk window.** The zone window rides
   the existing window grammar (Phase 97 placement/order/depth,
   the HS-101 fly-out from its object, the surface kit — no new
   window species). Its content area is the new part: a view of the
   zone's members.
2. **Two views, one truth.** Icon view: the HS-105-01 cell grid,
   snap-arranged, member positions remembered PER ZONE (extending
   the same persistence pattern as the world's arrangement — the
   sacred-arrangement clause reaches inside containers). List view:
   dense rows — icon glyph at list scale, name, kind, state badges,
   modified — sortable by name/kind/modified, sort remembered per
   zone. The view toggle and sort are window-level, remembered per
   zone (the Workbench window's own memory).
3. **The verbs come along.** Everything an object answers on the
   world it answers inside a zone window: the full click grammar,
   right-click menu, drag OUT to the world (un-filing), drag INTO
   another zone window or onto a drop-target (the HS-105-02 matrix
   applies verbatim — a zone window is just world at a different
   altitude). Multi-select with the existing lasso/mark grammar,
   group drag.
4. **Clean Up and Snapshot, by name.** "Clean up" re-grids the icon
   view (a verb, never automatic); "Snapshot" pins the current
   member arrangement. Both in the zone window's menu and the verb
   registry (HS-105-05 will surface them in the menu bar).
5. **The chip face stays honest.** The zone's world-icon badge
   (member count, the HS-105-01 contract) and its card face derive
   from the same member truth as the window views — one source, a
   census against parallel member lists.

## Out of scope

- Nested zones (a zone inside a zone — a real Workbench drawer
  behavior, but a world-model decision parked for the owner);
  smart/query zones; any new chrome.

## Acceptance

- A seeded 30-member zone opens into both views; sort works; view
  mode, sort, and icon positions survive reload (the HS-103-01
  restoration walk extended to cover it).
- Drag out to world, into another zone, and onto a HS-105-02 target
  from BOTH views, proven headed with real pointer sequences.
- Clean Up and Snapshot behave and persist; Reduce Motion honored on
  the re-grid.
- Density holds at 1440 and 393 (the list view is the phone's
  altitude; verify it leads there).

## Test plan

- **Unit:** view/sort state persistence keys; member-truth census;
  sort comparators.
- **Integration:** zone window store wiring; drag-out/drag-in
  producing the same mutations as the world paths.
- **Live (evidence):** the headed walk, both viewports + touch,
  screenshots read.

## Chef's notes

- The per-zone memory is the story. A view toggle that forgets is a
  widget; a window that remembers is an OS. Wire persistence first,
  demo second.
- List rows are where the no-prose rule gets tested — a row states
  name, kind, state, time. If a sentence sneaks into a row, it's the
  lamp again, horizontal.
- Reuse the delivery/list row treatments where they already exist
  (`DeskListView`, the Phase-102 Outcomes quiet treatment) before
  inventing row styles.
