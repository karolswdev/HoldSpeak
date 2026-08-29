# HS-148-04 — Head + dock menus on the registry (the AA graduation)

- **Project:** holdspeak
- **Phase:** 148
- **Status:** ready
- **Depends on:** HS-148-01
- **Unblocks:** HS-148-06
- **Owner:** unassigned

## Problem

The window-head menu is three hardcoded items off-registry
(DeskWindow.tsx:901-941) with no keycaps despite ⌘W/⌘M existing;
the dock chip menu (Dock.tsx:272-301) has neither glyphs nor
keycaps. BACKLOG candidate AA's "window-head menus and keyboard
equivalents on the verb registry" graduates here.

## Scope

### In (settled-design D4)

- Head and dock menus derive their entries from the registry's
  window verbs via a windowId-scoped dispatch (an explicit override
  in the entry's onSelect — one adapter; registry verbs keep acting
  on the front window from the bar; NO parallel verb system).
- Keycaps shown where they act (⌘W, ⌘M — existing bindings only);
  VerbGlyph glyphs kept/extended (restore/maximize/minimize/close);
  the story-01 grammar (lanes, wells, stipple) applies
  automatically by construction.
- Snap Left/Right/Maximize gain VerbGlyph directionals in the
  Window BAR menu (mechanics jurisdiction).
- windows.test.tsx menu block updated WITH the change; a
  registry-derivation pin (the head menu's labels/keycaps come FROM
  the registry, greppable no-hardcode proof).

### Out

- New bindings; dock TILE rendering; window chrome beyond the menus.

## Acceptance criteria

1. Head + dock menus render registry-derived entries with keycaps
   and glyphs; minimize/maximize/close act on the CLICKED window,
   not the front one (pinned with two windows open).
2. The bar's Window menu still acts on the front window; snap items
   wear directionals.
3. No hardcoded menu labels remain in DeskWindow/Dock (grep pin).

## Test plan

web: windows.test.tsx (extended, two-window scoping case),
Dock test, a registry-derivation unit pin — focused vitest.
