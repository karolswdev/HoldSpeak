# Desk sprites (web)

Pixel-art primitive sprites for the web diorama (`/desk`, Phase 71). These PNGs
are **copied verbatim from `apple/App/*.png`** — the same art the iPad DeskOS
diorama bundles. 128×128 RGBA; rendered pixel-crisp (`image-rendering: pixelated`).

The picker (`web/src/scripts/desk/sprites.js`) mirrors
`apple/App/SpriteStore.swift`: a djb2 stable hash of a primitive's id chooses its
variant from the kind's pool, so an object always wears the same sprite.

## Kind → pool (copied files)

| Kind | Pool | Files |
|---|---|---|
| meeting | `cassette` (17) | `cassette.png`, `cassette2..17.png` |
| note | `note` (16) | `note.png`, `note2..16.png` |
| kb | `crystal` (16) | `crystal.png`, `crystal2..16.png` |
| model / chain / workflow | `cartridge` (1) | `cartridge.png` |
| agent / coder | `agent_o` (16) | `agent_o0..15.png` |
| artifact / directory | `paper` (1) | `paper.png` |

## Refresh

Re-copy from `apple/App/` when the iPad art changes:

```
cp apple/App/{cassette,note,crystal}*.png apple/App/cartridge.png \
   apple/App/paper.png apple/App/agent_o{0..15}.png \
   web/public/desk/sprites/
```

Bump the pool counts in `web/src/scripts/desk/sprites.js` (and
`apple/App/SpriteStore.swift`) together if more variety art is added.
