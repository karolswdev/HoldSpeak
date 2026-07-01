# Evidence — HS-71-02: The sprite pipeline — hand-drawn objects on the web

**Date:** 2026-07-01
**Verdict:** done. The iPad's pixel-art primitive sprites are on the web, with
the same deterministic per-object variety, ready for HS-71-03 to float them.

## What shipped

- **`web/public/desk/sprites/`** — **67 PNGs copied verbatim from `apple/App/`**
  (128×128 RGBA, the same art the iPad diorama bundles), plus a provenance
  `README.md` (kind→pool map + a refresh command):
  - `cassette.png` + `cassette2..17.png` (meetings, 17)
  - `note.png` + `note2..16.png` (notes, 16)
  - `crystal.png` + `crystal2..16.png` (KBs, 16)
  - `cartridge.png` (models / chains / workflows)
  - `agent_o0..15.png` (agents / coders, 16 avatars)
  - `paper.png` (artifacts / directories)
- **`web/src/scripts/desk/sprites.js`** — the picker, the port of
  `SpriteStore.swift`:
  - `stableHash(s)` — **djb2 with exact 64-bit two's-complement wrap** (BigInt,
    so it matches Swift's `h &* 33 &+ byte` + `abs()`; a plain JS Number would
    lose precision past 2^53). So a given id maps to the **same variant the iPad
    would pick** for the numbered kinds.
  - `VARIANTS` pools mirroring `DeskSprites.variants` (+ web-side avatar/paper/
    cartridge art for the kinds the iPad draws with SF Symbols).
  - `spriteName(kind,id)` / `spriteUrl(kind,id)` (base via Astro `BASE_URL`, so
    `/_built/desk/sprites/…`, matching how `/_built/qlippy/*` is served).
- **`web/src/pages/desk.astro`** — imports the module and attaches it to
  `window.__deskSprites` so the `?raw`-loaded `desk-app.js` factory (and
  HS-71-03's object render) can pick each primitive's sprite.

## Proof

- **`screenshots/02-sprite-sheet.png`** — every kind's sprites rendering **crisp
  and pixel-perfect** at desk scale: cassettes (meetings), notepads (notes),
  crystals (KBs), avatar objects (agents/coders), cartridges (chains/workflows/
  model), paper (artifacts/directories).
- **Picker verified in-page** (the proof script's `evaluate`):
  - **stable** — every kind returns identical sprites on a repeat call (`stable:
    true`), so an object never reshuffles across reloads.
  - **spread** — the pooled kinds (meeting/note/kb/agent/coder) return **8/8
    distinct** sprites across 8 sample ids; single-art kinds return their one.
- **Tests:** route pre-flight **2 passed** (`/desk` loads clean with the new
  import, zero page errors); full suite **3045 passed, 37 skipped**; build green;
  the 67 PNGs bundle into `_built/desk/sprites/` and serve.

## Note

The sprites are not on the desk itself yet (the desk still shows the card-list);
HS-71-03 renders each primitive as a floating sprite object using this picker.
This story is the art + picker foundation.
