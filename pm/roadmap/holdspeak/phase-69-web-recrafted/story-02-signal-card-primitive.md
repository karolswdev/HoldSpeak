# HS-69-02 — The shared Signal card primitive (broadened)

- **Status:** done
- **Priority:** HIGH (lifts everything at once)
- **Depends on:** —
- **Catalog pattern(s):** §1 depth, §8 motion (hairline)
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Goal

One reusable `.signal-card` utility — surface + gradient top-lit hairline +
elevation + the `.glyph-chip` — composing the iPad `.signalCard()` modifier on
the web, applied across the cockpit (not just the five pages the initial
substrate touched). The Phase-68 audit flagged `/desk` and `/activity` as
under-applied; this story broadens the primitive onto them.

## Scope

- Make the primitive **composable** so nested cards keep their depth hierarchy
  (`--signal-card-surface` override, default `--surface-1` unchanged).
- Apply to `/desk` (all primitive cards) with the surface-2 override.
- Apply to `/activity` (the Alpine nudge card + the JS-injected rule cards).
- Authored GLOBAL (already is) so it reaches runtime-injected DOM.

## Proof required

One `.signal-card` utility; before/after screenshots of ≥3 surfaces; the
gradient hairline visibly directional, not flat; computed-style probes proving
it applies on the real (incl. JS-injected) DOM, not just a class in the bundle.

## Done

Shipped and proven — see the evidence file. The primitive is composable; `/desk`
(8 cards) and `/activity` (nudge + 4 rule cards) adopt it; applying it to
`/activity` repaired a latent Astro-scope-on-JS-DOM gap. Computed-style probes +
three screenshots; build green; slice 65 passed; route pre-flight 2 passed.
