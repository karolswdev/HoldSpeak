# HS-96-01 — The token architecture

- **Project:** holdspeak
- **Phase:** 96
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-96-02, HS-96-03, HS-96-04

## Problem

`web/src/styles/tokens.css` is one flat layer mixing raw values with
purpose names, and most of the desk's visual truth never made it into
tokens at all: `desk.css` carries its palette (the DioPal gradients, the
glow pool, the zone tints), its z ladder, its radii and shadows as
literals. There is no single source a generator, a validator, a spec
table, or a future Swift port can consume.

## Scope

- In:
  - `web/design-tokens.json` as the one source of truth, three layers
    per the design-system skill: primitives (the palette, the type ramp,
    the spacing/radius/elevation/motion/z scales), semantics (surface,
    text, accent, border, glow, egress scopes, the ladder bands), and
    component tokens (window, dock, chip, orb, zone, sprite frame);
  - a generator (the skill's `generate-tokens.cjs`, adapted into
    `web/scripts/`) emitting `web/src/styles/tokens.css` with a
    do-not-edit header, wired into `npm run check`'s census;
  - today's COMPUTED VALUES preserved exactly — the generated file must
    produce a pixel-identical build (before/after screenshots at 1440
    and 393);
  - every existing `var(--…)` consumer keeps working (names preserved or
    aliased in the semantic layer);
  - each token documented with its purpose in the JSON.
- Out:
  - changing any rendered value (that is HS-96-04's craft pass);
  - the burn-down of non-token literals (HS-96-02);
  - Tailwind config emission (no Tailwind in this repo).

## Acceptance criteria

- [x] `design-tokens.json` exists with the three layers and doc strings;
      the generator emits `tokens.css` deterministically and
      `npm run check` fails when the CSS drifts from the JSON.
- [x] The generated `tokens.css` preserves every current custom property
      name and computed value — proven MECHANICALLY (117/117 originals,
      zero changed, 61 added; the fidelity check is in the evidence) —
      and the production build renders identically (shots at both
      viewports in `assets/`; identical values imply identical pixels,
      the shots confirm).
- [x] The desk's un-tokenized truths (glow pool, zone tints, z ladder,
      window chrome dimensions, motion durations) exist as tokens —
      consumed in HS-96-02, defined here.
- [x] The web suite passes unmodified.

## Test plan

- `npm --prefix web run check` (census + typecheck + suites + build).
- A generator determinism test (two runs, identical output).
- Playwright before/after screenshots at 1440/393 compared.

## Implementation direction

- Adapt the skill's script rather than importing it verbatim: the repo
  needs plain CSS output, no Tailwind block, and the existing token
  names kept stable.
- Primitives get skill-style scale names; semantics keep today's names
  (`--text`, `--surface-1`, `--accent`) so consumers do not churn.
- Component tokens for the OS chrome come from the values shipped in
  Phase 95 (Z_BASE 42, dock band 80, transient band 81, GRAB 72,
  cascade 26) — codify, do not change.

## Evidence required

- the JSON + generated CSS diff summary;
- determinism and check outputs;
- before/after screenshots.
