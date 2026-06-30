# HS-69-04 — Materialize + stagger motion

- **Status:** done
- **Priority:** HIGH (cheap, broad)
- **Depends on:** HS-69-02
- **Catalog pattern(s):** §8 motion
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

## Goal

The arrival personality: cards glow + insert (fade + lift + a brief accent
shadow that settles) on the Signal settle ease where cards arrive, plus a
stagger helper so lists materialize in sequence. Reduced-motion gated.

## Scope

- `hs-materialize` keyframe (glow + insert/scale) + a `--i` stagger helper
  (already authored in `global.css` in the substrate wave).
- Applied where cards genuinely arrive without re-triggering on every reactive
  update: the dashboard recent-cards (keyed) and the `/activity` nudge list
  (keyed Alpine `x-for`, so only new nudges animate in).
- Verified rendering on seeded data (the original deferral: a fresh DB had no
  meetings/nudges to show the arrival).

## Proof required

The keyframe applied; stepped/seeded screenshots or a computed-style probe of
cards arriving with the glow; reduced-motion verified off.

## Done

Proven on the seeded `/activity` nudge cards: the computed `animation-name` is
`hs-materialize` (probes.json) and the keyframe carries the accent-glow lift;
the keyed `x-for` means only genuinely-new nudges animate (no re-trigger on
reactive updates). Reduced-motion is gated both by the global tokens
kill-switch and an explicit `@media (prefers-reduced-motion: reduce)` block
that zeroes the animation + stagger delay. See the evidence file.
