# HS-71-02 — The sprite pipeline: hand-drawn objects on the web

- **Status:** done
- **Priority:** HIGH (the art layer — objects can't float without art)
- **Depends on:** —
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Goal

Get the iPad's pixel-art primitive sprites onto the web, with the same
deterministic per-object variety, so every kind has its hand-drawn object
instead of an SVG line-icon.

## Scope

- **Copy the needed primitive PNGs** from `apple/App/` into
  `web/public/desk/sprites/` (committed; `web/public` is not gitignored). The
  kinds the web desk surfaces, per `SpriteStore.swift`:
  - meetings → `cassette.png` … `cassette17.png`
  - notes → `note.png` … `note16.png`
  - KBs → `crystal.png` … `crystal16.png`
  - models → `cartridge.png`; agents → the `agent_*` avatar pool; games →
    `game_*` covers (as available)
  - a fallback per kind for chains/workflows/directories/coder/artifact (reuse an
    existing sprite or a simple object; do not invent a whole new art set).
- A JS **sprite picker** `spriteFor(kind, id)` using a **djb2 stable hash**
  matching `SpriteStore.stableHash` (so an id maps to the same variant the iPad
  would pick), plus the per-kind pool sizes. Pixel-crisp:
  `image-rendering: pixelated`.
- A tiny provenance note (`web/public/desk/sprites/README.md`) recording which
  `apple/App/*.png` files were copied and the kind→pool map, so it can be
  refreshed.

## Proof required

A screenshot sheet showing each kind's sprite rendering crisply at desk scale;
the stable-hash picker proven (same id → same sprite across reloads; different
ids spread across the pool). The PNGs committed under `web/public/desk/sprites/`.

## Done

Shipped and proven. 67 primitive PNGs copied verbatim from `apple/App/` into
`web/public/desk/sprites/` (cassette/note/crystal/cartridge/agent_o/paper) + a
provenance README; `web/src/scripts/desk/sprites.js` is the picker (djb2 with
exact 64-bit wrap matching `SpriteStore.swift`, the `VARIANTS` pools, `spriteUrl`
via Astro `BASE_URL`), attached to `window.__deskSprites`. Sprite sheet renders
crisp; picker stable per id + 8/8 spread on the pooled kinds. Route pre-flight 2
passed; full suite 3045 passed. See [evidence-story-02.md](./evidence-story-02.md).
