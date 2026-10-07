# Parked: the old world sprites (2026-10-07)

These are the world sprites the desk wore before PHILO Phase 14. They are
parked, not deleted (the never-delete rule).

- The ruling: `docs/internal/philo/phase-14/icons/README.md`. The owner,
  2026-10-07: "the existing icons are pretty cringe and deserve a freaking
  overhaul". Muad'Dib picked D1 "Workbench+" for all 17 kinds.
- What is here: the 59 base sprites of the old mold (cassette x16, note x12,
  tome x13, automaton x14, drawer, paper, cartridge, people-ledger) and their
  `_sel` / `_stale` images. `README-old-mold.md` is the old folder README.
- `cartridge.png` is carried forward: a copy stays in the live folder for
  the capability kinds.
- Nothing in the product references this folder. The state script
  (`web/scripts/gen-sprite-states.py`) reads only the top level of
  `web/public/desk/sprites/`, so it does not touch these files.
