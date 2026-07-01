# Evidence — HS-71-01: The room — the warm atmospheric stage

**Date:** 2026-07-01
**Verdict:** done. `/desk` no longer loads as flat black. A full-bleed
atmospheric room now sits behind the content: the DioPal vertical gradient, an
animated warm radial spotlight, and rising dust motes. It reads as a lit space,
the foundation the floating objects (HS-71-03) will live in.

## What shipped

- **`web/src/pages/desk.astro`** — a `.desk-stage` layer (static markup, first
  child of `.desk`; scoped CSS is fine here since it is not Alpine-injected):
  - **Gradient** — the DioPal base `linear-gradient(178deg, #0B0D12 → #16111F →
    #090A0E)`.
  - **Warm spotlight** — `.desk-stage-glow`: layered radial gradients (a warm
    orange core high at `50% 34%`, a violet undertone, a low warm floor), `mix-
    blend-mode: plus-lighter`, gently pulsing (`desk-spotlight` keyframes, 7s:
    opacity 0.72→1 + a slight rise/scale) — the port of the iPad's animated
    `sin`-pulsed radial.
  - **Dust motes** — a `<canvas id="desk-motes">` + a small script (the DioMotes
    port): ~18 slow translucent warm specks rising on one cheap rAF loop.
  - Placed at `z-index: -1` (behind the desk content, above the app canvas), so
    the existing card-list still renders on top unchanged (content becomes
    floating sprites in HS-71-03).
- **Reduced motion** — the spotlight holds still and the motes freeze under
  `prefers-reduced-motion: reduce` (the rAF loop is skipped; one static frame
  drawn).

## Proof

- **`screenshots/01-room-atmosphere.png`** — `/desk` with the warm lit room: the
  orange/violet spotlight glowing from the top over the dark DioPal gradient and
  a low warm vignette. (Compare to the flat-black `/desk` in the Phase-71 scope
  message.)
- **Tests:** route pre-flight **2 passed** (`/desk` swept, **zero page errors** —
  the new canvas + motes script are clean); full suite **3045 passed, 37
  skipped**; build green (18 pages).

## Note

The room is intentionally still partly hidden by the current card-list content;
HS-71-03 turns those cards into floating sprites, which reveals the atmosphere
across the whole stage. This story is the foundation, shipped and clean.
