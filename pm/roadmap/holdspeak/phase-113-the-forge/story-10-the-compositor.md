# HS-113-10 - The compositor

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The window system must behave like a real OS compositor, not
positioned web elements. Maximized windows must respect the dock
band. App dock chips must have minimize/restore. The z-index ladder
must be bounded. Windows must re-clamp on viewport resize. The
selection/open law must be enforced everywhere. Context menus must
be universal. Escape must cancel local work before closing windows.
When this ships, the window system IS the OS — not web chrome
that approximates one.

**Articles served:** VIII (native-grade craft, compositor-only
interaction motion, physics as non-regressible contract), VII (one
window grammar, one z-ladder, one dock), I (one persistent Desk
world).

## Ground (from the audit)

**Window compositor gaps:**
1. Maximized windows overlap dock — `DeskWindow.tsx:1253-1269`
   uses raw `top:54/bottom:10`, not the tokenized working band.
2. Drag/resize don't respect chrome bands —
   `DeskWindow.tsx:258-270,476-549`, `clampRect` clamps against
   raw viewport margins.
3. App dock chips bypass minimize/restore —
   `DeskWindow.tsx:1135-1212,1495-1594`. Speak/Meetings/Agents/
   Settings buttons don't populate `chipEls`, can't animate
   to/from chip, no dimmed parked state.
4. Edge snap can persist windows smaller than minimum —
   `DeskWindow.tsx:126-162,476-512`.
5. No re-clamp on viewport resize — `DeskWindow.tsx:325-428`.
6. Z-index ladder unbounded — `DeskWindow.tsx:580-594`,
   `desk.css:80-90`.
7. Persisted panel data trusted without validation —
   `store.ts:66-99`.
8. Reset Layout doesn't re-run collision-aware placement —
   `store.ts:1041-1049`.

**Interaction grammar gaps:**
9. Zone window items open on single click, violating
   single-click-select/double-click-open law —
   `ZoneWindow.tsx:125-199`.
10. Right-click context menus not universal — `Surface.tsx:684-742`
    supports it but Zone, Delivery, Companion don't wire it.
11. Zone verbs bypass the verb registry — `floorMenu.ts:64-86`.
12. Session Escape closes window before cancelling local work —
    `SessionPullout.tsx:342-369,454-475,646-657`.
13. Focus-visible removed on composer controls —
    `desk.css:1235-1248,1949-1959,2023-2037,2433-2449`.

**Dock gaps:**
14. Dock is flat, no frosted material, no magnification, no
    running marks — `DeskWindow.tsx:1446-1594`,
    `desk.css:3559-3575,3602-3619`.
15. Window title bars don't communicate active/inactive state —
    `DeskWindow.tsx:1086-1106,1319-1375`.

## Method

1. **Working band contract:** Define `--desk-work-top` and
   `--desk-work-bottom` CSS variables from the system bar height
   and dock height. ALL window operations (place, reopen, drag,
   resize, snap, maximize) use these. One function, one truth.

2. **Maximize respects dock:** `DeskWindow.tsx:1253-1269` —
   maximized windows use `--desk-work-top/bottom`, not hardcoded
   values.

3. **App dock chips as real windows:** The four app buttons
   populate `chipEls`, receive running/front/parked state, and
   support minimize-to-chip/restore-from-chip animation. They
   are windows on the dock, not navigation buttons.

4. **Bounded z-index:** Compact the z-order array periodically.
   Cap the ladder at the documented window z-band ceiling. No
   window can escape into dock/transient territory.

5. **Re-clamp on resize:** Add a viewport-resize listener that
   re-clamps all open windows to the current working band.
   Debounced, compositor-only.

6. **Edge snap respects minimums:** `snapForPointer()` applies
   `minW`/`minH` before returning the tile rect.

7. **Panel data validation:** Validate stored rects/order on
   load. Drop entries with non-finite numbers, stale IDs, or
   duplicate keys.

8. **Selection/open law in zone windows:** `ZoneWindow.tsx` —
   single click selects (highlight row/cell), double-click opens
   the pullout. Same as the desk floor.

9. **Universal right-click:** Wire `onLineContextMenu` to Zone,
   Delivery, Agents, and Companion rows. Use `DeskMenuList`
   vocabulary. Ghosted verbs with reasons for ineligible actions.

10. **Zone verbs through registry:** `floorMenu.ts:64-86` — zone
    Open/Info/Focus/Rename registered in `verbRegistry`, not
    minted locally.

11. **Escape bubbling:** `SessionPullout.tsx` — Escape first
    cancels rename/compose/deny. Only an unclaimed Escape in the
    window scope closes the front window.

12. **Restore focus-visible:** Remove all `outline: none` on
    `:focus` for composer controls. The global accent focus-visible
    outline is non-negotiable.

13. **Window title bar active/inactive:** Front window gets
    colored traffic lights. Background windows get dimmed/gray
    traffic lights. The visual difference must be instant and
    obvious.

## Test plan

- Visual: maximize a window — it fills the space between system
  bar and dock, never overlapping either.
- Visual: drag a window toward the dock — it stops at the dock
  edge, never goes behind.
- Visual: click an app dock chip — it minimizes/restores with
  the same animation as other windows.
- Visual: open 20 windows — z-order stays within the documented
  band, never overlaps the dock.
- Visual: resize the browser — all windows re-clamp inside the
  new viewport.
- Visual: single-click a zone item — it highlights but doesn't
  open. Double-click opens.
- Visual: right-click a zone item — context menu with registered
  verbs.
- Visual: Escape during a rename in SessionPullout — cancels the
  rename, doesn't close the window.
- Visual: focus a text input with keyboard — accent outline
  visible on every composer control.
- Visual: front window has colored traffic lights, background
  window has dimmed ones.
- Regression: all existing window behavior tests pass.
- Screenshot walk: 1440px — desk with 4 windows open (one
  maximized, one minimized, two normal), dock showing running
  marks.
