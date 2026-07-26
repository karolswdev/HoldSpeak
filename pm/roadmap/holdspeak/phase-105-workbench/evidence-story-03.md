# Evidence - HS-105-03

- **Story:** HS-105-03 - Zones are windows — density with chosen altitude
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T16:01:49Z

- **Command:** `sh -c uv run pytest -q tests/unit/test_web_vocabulary_guard.py 2>&1 | tail -2 && cd web && npx tsc --noEmit -p . && npx vitest run 2>&1 | grep -E 'Tests|Files' && npm run tokens:gate 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 954a8e571468572dbe9ea890c18cb7ade28250f7

```text
.......                                                                  [100%]
7 passed in 0.41s
 Test Files  52 passed (52)
      Tests  328 passed (328)
token gate: clean (61 allow-listed exceptions, all in use)
```

## What shipped (the narrative)

Gated on a mockup over the real desk (both views, real sprites); the
owner's verdict: "Yes, it's better. But I do want you to continue
developing HS-105." Built with the drawer-icon amendment the owner's
own live catch forced (the tray + its "drop things here" prose died in
the HS-105-01 rider; this story gives the drawer its OPEN).

- **The open grammar**: double-click a drawer (touch: tap) → it opens
  as a REAL desk window (`ZoneWindow` on `DeskWindowFrame`, id
  `zone:<id>`) flying out of the gesture point; the desk stays
  visible; several zone windows COEXIST and wear dock chips via the
  existing panel system. Dive retired as the open grammar — it
  survives as the drawer context menu's Focus verb; the a11y layer
  opens the window.
- **Two views, one truth**: Icons (the world's cell contract — sprite,
  label, click-to-open-pullout) and List (Name / Kind / Modified,
  sortable both directions, member sprites at list scale, hover
  "Take out" un-files through the real removeFromDir). Modified reads
  the same lastModified/endedAt/createdAt truth the badges read.
- **The window REMEMBERS** (the story's soul): per-zone view + sort +
  direction persisted (`hs.desk.zone-views`), the open window set
  persisted (`hs.desk.zone-windows`, the HS-103-01 restoration rule),
  rect/stacking via the existing panel persistence. Honest absences:
  unresolved members count as "N unavailable"; an empty drawer says
  "Empty".

## The live walk (staged hub :8789, real seeded desk)

Beats, all green, screenshots in assets/ and READ:
1. Double-click the Decisions drawer → the window opens (Icons view,
   12 members in the cell grammar) — hs105-zonewin-icons.png.
2. Flip to List, sort by Modified — hs105-zonewin-list.png.
3. RELOAD → the window RESTORES with the List view and sort
   remembered — hs105-zonewin-restored.png.
4. Open a second drawer → two zone windows coexist over the living
   desk, both in the dock — hs105-zonewin-coexist.png.

The walk earned its keep round-9 style: the first run crashed the
world — a zustand selector returning a fresh fallback object per
snapshot check (an infinite-loop class bug) — fixed at cause
(module-level DEFAULT_PREF, raw-slot selector), rerun green.

## Guards + remainder

`zoneWindow.test.tsx` (3 pins: coexist+persist open set, close
persists remainder, per-zone view/sort remembered). Captured above:
vocabulary guard green, tsc clean, vitest 328/328 (52 files), tokens
gate clean. Recorded remainder for the sitting loop: Clean up /
Snapshot verbs + free member arrangement inside the icons view (they
need drag-reorder to mean anything), drag-out/drag-between-windows
as re-filing gestures.
