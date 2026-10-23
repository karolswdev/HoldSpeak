# Desk sprites (web)

The world sprites for the desk: one 64x64 icon for each kind. The owner chose
crisp illustrated icons on 2026-10-22, superseding the older D1 hard-pixel
material. The kind-to-file map is
`VARIANTS` in `web/src/desk/sprites.ts`. One kind has one silhouette.

`32/` holds the optical list-row set: small detail is suppressed and outlines
strengthened before rendering at 32x32. The list species (ObjectList, Needs you, the confirm
line, the PR card, a badge) read it through `listSprite` or
`spriteUrl(..., size 32)` in `web/src/desk/sprites.ts`.

SVG originals live in `web/design/icons/{world,system,settings}`. Export with
`uv run --with pillow python web/scripts/gen-illustrated-icons.py`; use
`--check` to verify fresh base PNGs without changing files. The exporter also
derives `<name>_sel.png` and `<name>_stale.png` through the existing
`gen-sprite-states.py`. PNG URLs, dimensions and state names remain shared by
DOM and GPU consumers. Use smooth sampling for this illustrated family.

- `system/`: the Dock and chrome sprites (32x32), registered in
  `web/src/desk/systemSprites.ts`.
- `settings/`: the Settings index sprites.
- `_parked-2026-10-07/`: the old mold, parked. Nothing references it.
- `web/design/icons/_parked-pixel-2026-10-22/`: the previous active PNG family,
  preserved once by the exporter.
- `web/design/icons/_parked-illustrated-v1-2026-10-22/`: the first illustrated
  SVG/PNG family, parked after the owner's live review. Current art uses
  shallow perspective, layered materials and finer seams.
