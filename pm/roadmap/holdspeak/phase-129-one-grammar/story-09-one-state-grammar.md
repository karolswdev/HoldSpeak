# HS-129-09 — One state grammar

- **Project:** holdspeak
- **Phase:** 129
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

One product speaks one way about loading, emptiness, failure, and guts.
Audit C found the dialects; this story converges them on the existing
grammar — `SurfaceState` legs, compact named receipts, folded RAW wells,
fewest-word labels. No new components; the existing ones applied.

### What changes

1. **States → `SurfaceState`:** CompanionCore's literal "READING"/"NO
   AGENTS" (:181); AttentionDrawer's "Loading…" button copy (:269-274);
   CapabilitySection's raw `<p>` warning (:125-130); WorkbenchWindow's
   inlet failure chip becomes an error state with retry (:1453-1465) and
   its two scanning `LedMeter` loading dialects (:1315-1320, :1447-1452)
   become the quiet loading leg.
2. **Guts → RAW folds:** WorkbenchCore run output (:406-441) and
   DeskToolInspector's bare `<pre>` (:381) fold behind `RAW` wells (the
   LiveCore pattern, LiveCore.tsx:302-308).
3. **Prose → receipts:** Repo commit-failure sentence (:138) and Issues
   "coming soon" (:198); Coder failure/recovery sentences (:138-144);
   DeliveryTerminal's consequence paragraph (:128-136); Workbench "Drop to
   add" (:1310-1312) — each becomes a compact named state/receipt with a
   verb where recovery exists.
4. **RuntimeDocsCore** (deferred-decision default): restructured minimally —
   the how-to prose becomes compact labeled reference rows; full docs
   remain out-of-desk.
5. Verb-home convergence for the named divergent rooms (Decision pullout
   footer Edit, Workbench triple-home, Repo split) lands ONLY where it is
   a placement move, not a redesign; anything larger is named for the
   backlog.

## Acceptance criteria

1. No literal loading/empty strings outside `SurfaceState` in the touched
   rooms; a grep census in the test proves it.
2. No bare `<pre>`/`SurfaceCode` outside a RAW fold in the touched rooms.
3. Error legs carry a named state and a recovery verb where one exists;
   no sentence-prose error copy remains in the touched rooms.
4. Untouched rooms are pixel-identical (the story is a convergence, not a
   restyle).

## Test plan

- Web: per-room state-leg tests; the grep censuses as tests; full desk
  suite; typecheck.
- Walk: before/after of each touched room's loading/empty/error leg forced
  via seeded/failing data at 1440.
