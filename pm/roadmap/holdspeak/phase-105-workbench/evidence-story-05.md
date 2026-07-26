# Evidence - HS-105-05

- **Story:** HS-105-05 - The menu bar — the system admits what it can do
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T16:37:45Z

- **Command:** `sh -c cd web && npx tsc --noEmit -p . && npx vitest run 2>&1 | grep -E 'Tests|Files' && npm run tokens:gate 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4a1467bd280d2b38ec8a6d301d91d16a31f4f960

```text
 Test Files  55 passed (55)
      Tests  340 passed (340)
token gate: clean (61 allow-listed exceptions, all in use)
```

## What shipped (the narrative)

The ARexx rule at its honest scope: a verb is a REGISTERED capability
and every face renders the same registry (`verbRegistry.ts`).

- **The registry**: typed rows {id, label, menu, ghost(ctx), run(ctx)}.
  Desk verbs (New Note/Knowledge/Agent/Zone, view toggle) run always;
  Object verbs (Open/Info/Edit) are selection-aware; the Go menu
  DERIVES from DESK_TOOLS — the ⌘K shelf's exact truth, so the two
  faces cannot drift (guard-pinned equality).
- **The menu bar** (`DeskMenuBar`, mounted in the chrome beside the
  HoldSpeak mark): real pull-down menus in the ONE menu vocabulary
  (DeskMenuList), context-sensitive, and GHOSTED WITH THE REASON
  rather than hidden ("Select an object", "Not editable") — the
  system admits what it can do. Phone: the bar folds away; the shelf
  face reaches every verb (one registry).
- **The third face (wire) deliberately WAITS for the kernel**:
  invoking store verbs over HTTP without the broker's consent model
  would widen authority (Article V); the kernel RFC's userland
  dispatch is its named landing (rung 6). Recorded, not waived.

## The live walk (staged hub :8788) — and the defect it caught

1. Object menu with nothing selected: all three verbs ghosted with
   the reason visible (assets/hs105-menu-ghost.png).
2. THE CATCH: the first walk failed because an open menu survived an
   outside click (page-level Escape never reaches DeskMenuList's
   focus-scoped handler) — a real dismissal-grammar defect. Fixed at
   cause: an open menu now closes on ANY outside pointer-down and on
   Escape from anywhere; re-proven (menu-dismissed-on-outside: True).
3. Select a note → Object > Info opens the Info card via the menu.
4. Desk > New Note creates in-world (31 → 32 objects).
5. Go lists all 10 tools (DESK_TOOLS parity) and opens surfaces
   (assets/hs105-menu-desk.png).

## Guards

`verbRegistry.test.ts` (unique ids, ghost-with-reason, desk always
runnable, Go ≡ DESK_TOOLS). Captured above: tsc clean, vitest
340/340 (55 files), tokens gate clean. Remainder: keyboard
equivalents beyond the shown ⌘K, the wire face (kernel), menus on
window heads.
