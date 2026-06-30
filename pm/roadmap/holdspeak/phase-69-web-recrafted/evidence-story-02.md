# Evidence — HS-69-02: The shared Signal card primitive (broadened across the cockpit)

**Date:** 2026-06-29
**Verdict:** done. The `.signal-card` primitive now rides the surfaces the
Phase-68 audit flagged as under-applied — `/desk` (the flagship authoring
surface) and `/activity` (the least-migrated page) — in addition to the
dashboard / history / settings it already lifted. Proven on the real DOM with
computed-style probes (not just a class in the bundle) and full-page
screenshots.

## What shipped

- **The primitive is now composable** (`web/src/styles/global.css`): the
  surface reads `var(--signal-card-surface, var(--surface-1))`. The default is
  unchanged (every existing consumer is byte-identical), but cards nested inside
  an already-raised surface can set `--signal-card-surface: var(--surface-2)` to
  keep their depth contrast against the parent. Additive; zero risk to the five
  surfaces that already adopted it.
- **`/desk`** (`web/src/pages/desk.astro`): all eight primitive cards
  (meeting / artifact / note / agent / chain / workflow / directory / kb) carry
  `signal-card`. The `.card` rule was trimmed to layout + the per-kind hover
  accent, with `--signal-card-surface: var(--surface-2)` so cards stay raised
  against the `surface-1` zone columns. No `hs-materialize` on desk cards (the
  Alpine `x-for` re-renders would re-trigger the entrance), and no `glyph-chip`
  on the zone icons (they are per-kind colour-keyed, not the accent gradient).
- **`/activity`** (`web/src/pages/activity.astro`, `web/src/scripts/activity-app.js`):
  the Alpine `.nudge-card` and the four JS-injected `.rule-item` variants
  (list + candidate-preview + candidate-saved) carry `signal-card`. The
  `.nudge-card` scoped surface was trimmed to layout + its left accent spine +
  the selected state, deferring the base to the primitive.

## The latent bug this surfaced

`/activity` uses Astro's **default `'attribute'` scope strategy**, so its
`<style>` rules compile to `.rule-item[data-astro-cid-…]`. The `.rule-item`
cards are emitted by `activity-app.js` via `innerHTML`, so they **never carry
the cid attribute** — the page's own scoped card styles never reached them
(the standing scoped-CSS-on-JS-DOM gotcha; the Phase-54 precedent). The
*global* `.signal-card` primitive is what now actually styles these cards. The
fix is therefore also a repair, not only a polish.

## Proof

- **Computed-style probes on the live, seeded DOM** (`screenshots/probes.json`):
  - `/desk .card.signal-card` → `box-shadow: …0px 8px 24px…` (`--elev-2`),
    `border-top-left-radius: 18px` (`--radius-5`),
    `background-color: rgb(28, 31, 39)` (`--surface-2`, the override works),
    `::before background-image: linear-gradient(rgba(255,255,255,0.12…` (the
    top-lit hairline paints).
  - `/activity .rule-item.signal-card` (JS-injected) → same elevation + 18px
    radius + `rgb(21, 23, 29)` (`--surface-1`) + the hairline — i.e. the global
    primitive reaches the JS DOM the scoped CSS could not.
  - `/activity .nudge-card.signal-card` → elevation + 18px radius + the hairline
    + `animation-name: hs-materialize` (the arrival motion is live, HS-69-04).
- **Screenshots** (`screenshots/desk.png`, `screenshots/activity.png`,
  `screenshots/history.png`) captured by `scripts/screenshot_phase69_substrate.py`
  (boots the real `MeetingWebServer` against a seeded temp DB; bundle built
  first). Reviewed by eye: desk cards read as raised glass tiles against their
  zones; activity nudge + rule cards are crafted signal-cards with the egress
  badge, no longer flat boxes.
- **Tests:** `npm run build` green (16 pages); `.signal-card` confirmed global
  (no cid) in the built CSS. `uv run pytest` slice — frontend density guard +
  `test_web_activity_api` + `test_web_activity_nudges_api` +
  `test_primitive_framework_sync` = **65 passed**; the route pre-flight
  zero-page-error sweep = **2 passed**. Full baseline this session: 3040 passed.
