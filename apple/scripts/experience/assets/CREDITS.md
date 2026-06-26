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

## Tailored-agent "Pixel" avatar group (HSM-14)
- 16 bespoke pixel-art agent characters generated via PixelLab (create_1_direction_object, 64x64,
  sidescroller view), object 28d05da0-577e-451f-a8c7-a7e42896d89a. Bundled as App/agent_p0..p15.png.
  Order: robot, owl, fox, wizard, dragon, cat-mage, lion, wolf, rabbit, jellyfish, axolotl, android,
  bear, crystal-golem, ghost, bee. © generated content via PixelLab (pixellab.ai).
- 16 "Objects" anthropomorphized everyday objects (school bus/mug/lamp/…), object ba53dbf6-9e05-42e9-8d07-3dce08667cd3, App/agent_o0..o15.png.
- 16 "Snacks" anthropomorphized foods (donut/taco/avocado/…), object 5a67be7e-bea3-479b-b0cb-f9ec95e2434c, App/agent_s0..s15.png.
