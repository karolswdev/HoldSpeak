# Evidence - HS-105-04

- **Story:** HS-105-04 - Info on everything — the inspectable desk
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T16:22:29Z

- **Command:** `sh -c uv run pytest -q tests/unit/test_web_vocabulary_guard.py 2>&1 | tail -1 && cd web && npx tsc --noEmit -p . && npx vitest run 2>&1 | grep -E 'Tests|Files' && npm run tokens:gate 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3378be2d80203c2536e3763f44d2d10fa39a98df

```text
7 passed in 0.43s
 Test Files  53 passed (53)
      Tests  332 passed (332)
token gate: clean (61 allow-listed exceptions, all in use)
```

## What shipped (the narrative)

Gate: the Info-card mockup over the live desk, presented with two
NARROWING honesty constraints (Receipts v1 = only live-route truth;
the property vocabulary starts at keys with real update paths). The
owner's standing orders ("continue developing HS-105", "Keep going?",
the delivery goal) govern the proceed; the build implements the mock
MINUS the aspirational parts, exactly as flagged.

- **One card, contract-derived** (`infoContract.ts` + `InfoWindow.tsx`):
  a kind DECLARES footprint + property keys; the surface derives. No
  kind hand-builds its Info (guard-pinned). Right-click → Info on
  every world object AND every drawer; cards coexist as real desk
  windows (dock chips free).
- **Universal sections**: Identity (name edits IN PLACE through the
  real update paths — renameZone / updatePrimitive; kind; id;
  created/modified via humanTime), Footprint (declared measures:
  characters, members, segments — null renders as absence, never
  zero), Filed (zone chips opening the zone window), Lineage (the
  existing lineage() truth, ancestors openable).
- **Properties = tooltypes**: today's WHOLE honest vocabulary is one
  key — `recipe.runs_on` (the recipe PUT's profile_id) — and the
  guard PINS the list so aspiration can't creep in. Receipts: not
  rendered in v1 (no per-object queryable route exists; recorded as
  the kernel journal's future feed), per the gate's constraint.

## The live walk (staged hub :8788)

1. Right-click the KB → Info: the card opens with Identity/Footprint
   (assets/hs105-info-kb.png).
2. Rename in place → the REAL PUT: the world icon behind re-labels
   live ("Project KB (renamed)" visible under the sprite in
   assets/hs105-info-coexist.png).
3. Zone Info coexists with object Info (two cards, dock chips).
4. The property round-trip, proven against the wire: created a real
   profile, selected "LAN llama" in the card's runs_on →
   GET /api/recipes shows profile_id persisted
   (assets/hs105-info-recipe.png). First run honestly showed only
   "This device" — the staged desk had no profiles, and the choice
   list refused to invent one.

## Guards

`infoContract.test.ts` (4 pins: universal-only fallback, honest null
footprints, the property vocabulary pinned to exactly
["recipe.runs_on"], filedZones ref matching). Captured above:
vocabulary guard, tsc, vitest 332/332 (53 files), tokens gate — all
green. Remainder recorded: Receipts (kernel journal feed), property
keys grow one real field at a time, Info from window heads.
