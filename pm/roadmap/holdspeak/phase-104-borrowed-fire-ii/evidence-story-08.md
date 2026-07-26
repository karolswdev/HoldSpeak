# Evidence - HS-104-08

- **Story:** HS-104-08 - The icon family reforged — Workbench 2.0, but amazing
- **Status:** done
- **Date:** 2026-07-26

## What shipped

The owner's sitting rider, verbatim: *"Gone are the 'crystals' for
KB, gone are cute-ass bitmojis, in are more Workbench
2.0-but-amazing icons."*

- **Generated with Pixellab** per the ICON-DISCIPLINE recipe (48px
  candidate packs, the documented prompt formula, one pack per
  family, ~140 generations): 16 cassettes (meeting), 12 memo pages
  (note), **13 bound tomes (kb — the crystal is gone)**, **14
  mechanical automaton heads (agent/recipe/coder — the bitmoji is
  gone)**, plus the drawer, cartridge, and paper singles. Candidates
  were picked against the discipline (crumpled/mushy silhouettes,
  fantasy crests, and gimmick stamps rejected); pool sizes in
  `sprites.ts` are the surviving picks.
- **Banked** on the 64px canvas (48 art centered, 1:1 rule intact),
  `gen-sprite-states.py` rerun: 58 bases × rest/_sel/_stale = 174
  images on disk. Old crystal*/agent_o*/cassette*/note* files
  removed; no code reference to the dead families remains.
- **Proven on the real staged desk** (`seeded-desk-watched-hand`,
  fresh build): icons-desk-desktop-1440.png + icons-desk-phone-393.png
  — the drawer zone, tome KBs, memo note, and automaton agent
  render crisp in the uniform cell at both densities. The
  family-contact-sheet.png shows all 58 + the three state rows in
  one frame. All shots READ before this flip.
- **Guards:** iconCell 7/7 (captured below with a byte-identical
  state-script rerun); tsc clean; build 0; tokens gate clean; desk
  suite 294/295 — the one failure is
  `DeskListView.test.tsx > pages by 100` timing out at 5s under
  full-suite load, reproduced IDENTICALLY on the clean pre-sprite
  tree (stash → run → same failure → pop) and passing alone:
  pre-existing, unrelated, documented per the exit-criteria rule.

## Proof

### Captured run — 2026-07-26T20:25:32Z

- **Command:** `bash -c cd web && npx vitest run src/desk/gl/__tests__/iconCell.test.ts && uv run python scripts/gen-sprite-states.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9620b2c913488f285f63f4043b49f27f5c2d245e

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  7 passed (7)
   Start at  14:25:33
   Duration  888ms (transform 136ms, setup 116ms, import 124ms, tests 11ms, environment 488ms)

derived sel+stale for 58 sprites in /Users/karol/dev/tools/HoldSpeak/web/public/desk/sprites
```
