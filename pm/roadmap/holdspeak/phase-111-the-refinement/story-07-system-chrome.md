# HS-111-07 - System chrome

- **Project:** holdspeak
- **Phase:** 111
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

Dropdown menus (Desk/Object/Go), context menus, the search palette
(Cmd+K), the shortcut sheet, and popovers are the OS's own voice —
they appear over every program. The bar: **system chrome speaks pure
Workbench 2.0: opaque rectangular menus with 1px bevels, full-width
highlight bands, mono labels; the palette is a command console, not
a Spotlight clone.**

## Owner riders (2026-08-01)

1. **The desktop right-click.** "How come we don't have a desktop
   right click? for like.. new->, launch-> and so on...?" The desk
   floor gets a real context menu in the Workbench menu grammar:
   `NEW >` (the creatable object types — note, canvas, workflow,
   agent…), `LAUNCH >` (the programs), plus the floor verbs that
   already exist elsewhere (arrange/overview/reset as applicable).
   Desk OBJECTS get their right-click too (open, file, info, bin —
   the verbs the object already owns; no new capabilities minted by
   the menu). Same opaque beveled menu species as the dropdowns —
   one grammar.
2. **The palette becomes a command deck** (usability doctrine P0
   F1/F2, owner-commissioned review): ⌘K currently dead-ends on
   Enter (no default selection — DeskToolShelf.tsx:268-285) and runs
   on a parallel DESK_TOOLS list. The refit: Enter runs the top hit,
   always; the palette derives from the SAME verb registry as menus
   and keys (doctrine principle 2), reaches Prefs deep-settings and
   meeting content search, and ranks (prefix > recents > substring).
   Also: the menu-bar dropdowns draw UNDER windows (z-30 chrome band
   vs z-42 windows) — portal them exactly like the palette already
   does (~10 lines, doctrine F5).
3. **The desk list view is a ledger, not naked HTML** (owner, with
   screenshot, 2026-08-01: "looks like absolute ass... pure HTML
   overlaid on stuff"). `DeskListView.tsx` currently renders
   proportional two-line HTML rows with no ledger grammar and no
   window discipline (open windows float over it mid-content). The
   refit: the list view is a `SurfaceLedger` face of the floor —
   26px mono rows (`ID/title | kind | fact | STATE`), roving focus
   (08 kit law), full-width bands, day/kind bands as appropriate —
   and it layers correctly with windows (the floor face never bleeds
   through chrome). Duplicate-object data hygiene (the dozen
   identical `PR-387 · Coder session · starting` rows in the owner's
   shot) is traced in HS-111-06's audit — whichever wire mints one
   desk object per session run gets deduped/expired there; this
   story only renders honestly what the wire provides.
4. **Debug information hides beautifully.** Any window's debug/wire
   material (drawers, opened files, IDs, raw JSON, routing guts)
   never sits on the face — it lives behind ONE deliberate access
   affordance (the folded `RAW` well: Disclosure → SurfaceWell, mono)
   and looks designed when opened. This is already the shipped
   pattern in Speak/Meetings/Agents; this story makes it LAW for the
   chrome and sweeps any remaining naked debug in system surfaces.

## Method (phase canon)

1. **Audit.** An agent opens every menu, the palette, the shortcut
   sheet, and each popover; files every macOS-ism and SaaS-ism —
   plus a census of debug/wire material sitting on window faces.
2. **Rethink.** Propose the native treatment against the phase
   question — one menu grammar for all of them, including the new
   desktop and object context menus.
3. **Implement** in `web/src`.
4. **Prove** with live screenshots on the real desk, 1440 and 393.

## Test plan

- Menus are opaque, 2px-cornered, beveled; hover is a full-width
  band, not a rounded chip.
- Right-click on the desk floor opens the context menu: `NEW >` and
  `LAUNCH >` submenus work end to end (a created object lands on the
  desk; a launched program opens). Right-click on an object offers
  its own verbs. Keyboard path exists (menu key / long-press at
  393).
- The context menu mints NO new capabilities — every verb routes
  through the exact existing create/launch/object paths.
- No debug/wire material on any chrome or window face — a census
  proves every raw surface sits behind the folded RAW well pattern.
- The Cmd+K palette renders in the same grammar (sunken input well,
  ledger results) AND behaves as the command deck: Enter runs the
  top hit; every verbRegistry verb, Prefs deep-setting, and meeting
  search reachable; menu-bar dropdowns draw over windows.
- The shortcut sheet and popovers share the treatment; no
  backdrop-filter anywhere in chrome.
- Screenshot walk at both viewports, including the open context
  menus and one opened RAW well.
