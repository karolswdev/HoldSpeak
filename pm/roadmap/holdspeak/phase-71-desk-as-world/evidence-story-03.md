# Evidence — HS-71-03: Objects that float (the diorama's heartbeat)

**Date:** 2026-07-01
**Verdict:** done. `/desk` stopped being a document. Every primitive now floats
on the warm stage as a hand-drawn pixel-art object with a detached ground
shadow, a per-kind glow, and a bob. This is the story where the web Desk becomes
a world.

## What shipped

- **`web/src/scripts/desk-app.js`** — the world model + layout helpers:
  - `worldObjects()` flattens `this.items[kind]` across every kind into one
    stably-ordered list of `{kind, id, title, ref}`.
  - `objSprite(o)` picks the sprite via `window.__deskSprites` (HS-71-02).
  - `objStyle(o, i, n)` auto-lays-out objects in a loose, density-aware grid with
    per-object jitter, and sets the CSS custom props that drive the life:
    `--phase` (float offset from the id hash, so they don't bob in sync),
    `--tilt`, `--oscale`, `--k` (the per-kind glow tint via `objGlow`).
  - (HS-71-04 replaces the auto-layout with a saved, draggable position.)
- **`web/src/pages/desk.astro`** — the world render (Alpine `x-for` over
  `worldObjects()`), each object a `.desk-obj`:
  - `.desk-obj-lift` **floats** (`desk-bob` keyframes, ~4.6s, delayed by
    `--phase`, tilting),
  - `.desk-obj-sprite` the pixel-crisp PNG with a drop shadow,
  - `.desk-obj-glow` the per-kind radial pool,
  - `.desk-obj-shadow` the **detached ground shadow** that stays on the floor and
    softens/narrows as the object lifts (the "floating above a surface" cue,
    counter-animated on the same `--phase`),
  - a two-line label.
  - The old grouped card-list + authoring UI is preserved under a collapsed
    **"Browse as a list"** `<details>` beneath the world (nothing lost; the world
    is the star).
  - All object CSS is `<style is:global>` (Alpine-injected DOM).
- **Reduced motion** — the float + shadow animations hold still.

## Proof

- **`screenshots/03-world.png`** — a **12-object mixed desk** (4 meetings + 3
  notes + 2 KBs + 2 agents + 1 directory, seeded via the real `/api/*` POSTs)
  floating on the warm room: cassettes, notepads, crystals, avatar objects, and
  paper, each with a glow, a detached shadow, and a label, scattered across the
  stage. (Compare to the flat card-list `/desk` from the Phase-71 scope.)
- **Tests:** route pre-flight **2 passed** (`/desk` swept, **zero page errors** —
  the Alpine `x-for` + `window.__deskSprites` render is clean); full suite
  **3045 passed, 37 skipped**; build green. Objects render live (`.desk-obj`
  count = 12).

## Note

Performance stays cheap: the float/glow/shadow are pure **CSS keyframes** with a
per-object `--phase` (no rAF loop over N objects). Free drag-to-arrange + the
density-aware `looseHome` layout + persistence are HS-71-04; tapping an object to
open it + in-world Qlippy are HS-71-06.
