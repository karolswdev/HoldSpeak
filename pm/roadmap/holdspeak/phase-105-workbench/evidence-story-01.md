# Evidence - HS-105-01

- **Story:** HS-105-01 - The icon system — handles, not mascots
- **Status:** done
- **Date:** 2026-07-25

## Proof

### Captured run — 2026-07-26T04:55:27Z

- **Command:** `sh -c cd web && npx vitest run src/desk/gl/__tests__/iconCell.test.ts 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f644e3b31aa785c4215a5bdff8df5f56faa4c7ec

```text

 Test Files  1 passed (1)
      Tests  7 passed (7)
   Start at  22:55:28
   Duration  331ms (transform 60ms, setup 38ms, import 55ms, tests 5ms, environment 165ms)
```

### Captured run — 2026-07-26T04:55:35Z

- **Command:** `sh -c cd web && npx tsc --noEmit -p . && npx vitest run 2>&1 | grep -E 'Tests|Files' && npm run tokens:gate 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f644e3b31aa785c4215a5bdff8df5f56faa4c7ec

```text
 Test Files  51 passed (51)
      Tests  325 passed (325)
token gate: clean (61 allow-listed exceptions, all in use)
```

## What shipped (the narrative)

The gate ran per AGENT_BRIEF §2: a real-art mockup (Pixellab dual-state
proof set, both form factors) with an own-eyes critique; the owner's
verdict, verbatim: "Gimmick comes from some of the art, but really from
the fact that there's no real idea of directories, properties of them,
and so on, and so forth, but also because of arts. I accept." Built as
mocked plus the two gate findings (distinct silhouette per kind; badges
anchor to art bounds at rest, box bounds selected).

- **The cell contract** (`sceneModel.ts`): SPRITE 88 → 64 (the sources
  are 64×64 pixel art — the old render was a FRACTIONAL 1.375× upscale,
  the mush behind the owner's "huge-ass icons"), one uniform cell for
  every kind (the small-note differential and paper overlay died), LIFT
  80 as the selection box, OBJ_W 104.
- **States are real images** (`web/scripts/gen-sprite-states.py`):
  deterministic `_sel` (brighten + 1px alpha-edge rim) and `_stale`
  (desaturate + dim) derived for all 68 sprites; the scene picks
  sel > stale > rest; the selected label inverts onto an accent chip;
  selection is a rounded-rect CELL, not an orbiting dashed circle.
- **A directory is a drawer**: the harvested Pixellab drawer keeper
  banked at 64px; `VARIANTS.directory = ["drawer"]` (was "paper" — the
  owner's "no real idea of directories" diagnosis, first payment).
- **Live badges only** (per research-badge-source-map.md): member count
  (kbs[].member_ids.length) bottom-right, freshness tick
  (last_modified ≤ 48h, adapters now KEEP the field they discarded)
  top-right, needs-you (Attention projection) top-left, NEW as before;
  coder wire's stale flag drives the stale image. No badge without a
  named route.
- **Integer-true motion**: the per-object random tilt and 0.92–1.08
  scale jitter died; the positional bob stays.

## The density walk (live, staged hub :8789, seeded-desk-43 + dense-desk)

Two defects caught BY the walk and fixed at cause, round-9 style:

1. First dense shot (assets/hs105-dense-desktop-1440.png): object
   overlaps and occluded labels at 33 objects — root cause the random
   jitter in `objUnit`'s default homes. Fix: deterministic clean grid
   (the Workbench Clean Up rule); jitter deleted.
2. Phone at 393: a 104px cell cannot grid 33 objects in a 393px world
   (soup, zone collisions). Fix per the story's own acceptance line:
   a compact desk with NO saved view choice leads with the LIST above
   16 objects (`defaultViewFor`, `COMPACT_LIST_THRESHOLD`); an explicit
   user choice (URL or saved key) always wins.

Final reads (own eyes, both read before this flip):
- assets/hs105-final-desktop-1440.png — 33 objects, zero overlaps,
  silhouettes sort by shape, counts 2/3/4/5 live, freshness ticks
  honest (everything just seeded), zones as trays.
- assets/hs105-final-phone-393.png — the list leads: "Showing 33 of
  33", zone chips with counts. (List interior craft = HS-105-03's
  altitude work.)

## Guards

`web/src/desk/gl/__tests__/iconCell.test.ts` (7 tests): constants
pinned integer-true; no tilt/scale jitter; base+_sel+_stale on disk
for EVERY pool sprite; directory=drawer; count/fresh/state from named
fields only. The discipline is written law at `web/ICON-DISCIPLINE.md`.

Captured above: the guard run and the full web chain (tsc clean,
vitest 325/325 across 51 files, tokens gate clean), both exit 0.
