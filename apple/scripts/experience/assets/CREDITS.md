# Desk asset credits + provenance

All 3D models below are **CC0 / Public Domain** (no attribution required; credited here as good practice).
Source: [poly.pizza](https://poly.pizza). Pipeline: glTF/GLB → OBJ (via `trimesh`) → SceneKit; for the
app, GLB → USDZ (Reality Converter / `usdzconvert`) → bundled, loaded natively by SceneKit.

| Model | File | Creator | License | Source |
|---|---|---|---|---|
| Light Desk (lamp) | `models/lightdesk.glb` / `.obj` | Quaternius | CC0 | poly.pizza/m/uJDWrSJGVH |

## Referenced for the barrier/building kit (HSM-14-22, not yet vendored)

| Model | Creator | License | Source |
|---|---|---|---|
| Modular Road Kit | Kenney | CC0 | poly.pizza/m/YClppstaHV |
| Road Bits | Kay Lousberg | CC0 | poly.pizza/m/5BPCPOycxC |

When vendoring any new asset, add its row here at fetch time. Prefer CC0; for CC-BY, the credit line is
mandatory in shipped builds.

## Vendored into the app (HSM-14-22 populated desk) — all CC0

| Model | App file | Creator | Source |
|---|---|---|---|
| Light Desk (lamp) | App/lightdesk.scn | Quaternius | poly.pizza/m/uJDWrSJGVH |
| Plant - White Pot | App/plant.scn | (poly.pizza CC0) | poly.pizza/m/7ig0HcyfT93 |
| Book Stack | App/books.scn | (poly.pizza CC0) | poly.pizza/m/1WggoIFq8tx |
| Mug | App/mug.scn | (poly.pizza CC0) | poly.pizza/m/2jVUdnj4mVP |
| Keyboard | App/keyboard.scn | (poly.pizza CC0) | poly.pizza/m/3oFfQCSsUmQ |

Pipeline used: poly.pizza GLB -> trimesh OBJ+texture -> `xcrun scntool` SCN -> bundled; palette texture
re-applied in code from the `*_tex.png` atlases.
