# Evidence — HS-69-04: Materialize + stagger motion

**Date:** 2026-06-29
**Verdict:** done. The `hs-materialize` entrance (glow + lift + settle) is
applied where cards arrive and is proven rendering on seeded data — closing the
original deferral (a fresh DB had nothing to animate).

## What shipped

- The `hs-materialize` keyframe + the `--i` stagger helper live in
  `web/src/styles/global.css` (authored in the substrate wave): the card fades
  in from `translateY(6px) scale(0.985)` with a brief `--accent-glow` ring/shadow
  that settles to `--elev-2`; the stagger is `animation-delay: calc(var(--i) * 40ms)`.
- Applied on the `/activity` nudge list (`web/src/pages/activity.astro`): the
  keyed Alpine `x-for="(nudge, idx) in nudges" :key="nudge?.key"` carries
  `hs-materialize` with `:style="--i: ${idx}"`. Keying means Alpine reuses the
  DOM nodes of unchanged nudges, so **only genuinely-new nudges animate in** —
  no re-trigger on every reactive update.
- Already on the dashboard recent-cards (`web/src/pages/index.astro`).

## Proof

- **Computed-style probe on the live seeded DOM** (`screenshots/probes.json`,
  via `scripts/screenshot_phase69_substrate.py`): `/activity .nudge-card.signal-card`
  reports `animation-name: hs-materialize` — the entrance is wired and active on
  real, seeded nudges (two activity records → two nudges).
- **Screenshot** `screenshots/activity.png`: the nudge cards are present and
  rendered (the settled end-state of the entrance), each a signal-card with its
  egress badge.
- **Reduced-motion is gated twice**: the global `prefers-reduced-motion: reduce`
  kill-switch in `tokens.css` (forces `animation-duration: 0ms`) plus an explicit
  block in `global.css` that sets `.hs-materialize { animation: none;
  animation-delay: 0ms }` — the card still appears, it just does not animate in.
- Slice + route pre-flight green (65 + 2 passed); build green.
