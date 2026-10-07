# Desk sprites (web)

The world sprites for the desk: one 64x64 icon for each kind, in the D1
"Workbench+" mold (PHILO Phase 14, ruling in
`docs/internal/philo/phase-14/icons/README.md`). The kind-to-file map is
`VARIANTS` in `web/src/desk/sprites.ts`. One kind has one silhouette.

Each base file has two state images, `<name>_sel.png` and
`<name>_stale.png`, made by `web/scripts/gen-sprite-states.py`. Run the
script again after you add a base sprite.

- `system/`: the Dock and chrome sprites (32x32), registered in
  `web/src/desk/systemSprites.ts`.
- `settings/`: the Settings index sprites.
- `_parked-2026-10-07/`: the old mold, parked. Nothing references it.
