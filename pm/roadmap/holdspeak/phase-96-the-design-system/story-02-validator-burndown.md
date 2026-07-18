# HS-96-02 — The validator gate and the burn-down

- **Project:** holdspeak
- **Phase:** 96
- **Status:** done
- **Depends on:** HS-96-01
- **Unblocks:** HS-96-04

## Problem

Nothing stops a raw `#ff6b35` or a hand-typed `z-index: 81` from landing
in a component style — that is exactly how `desk.css` accumulated
hundreds of literals. The design-system skill ships a validator for this;
the repo needs it as a mechanical lock, and needs the existing debt paid
down so the lock starts honest.

## Scope

- In:
  - the skill's `validate-tokens.cjs` adapted to the repo's CSS layout
    (component styles must reference tokens; the generated
    `tokens.css` and the GL texture generators are the allowed raw-value
    homes), wired into `npm run check` and CI;
  - the burn-down: `desk.css` and `react-app.css` literals replaced by
    the HS-96-01 tokens — colors, z indexes, radii, shadows, durations,
    chrome dimensions — with the build pixel-stable except where a
    literal was provably inconsistent (each such normalization named in
    the evidence);
  - the TS-side constants that mirror CSS (Z_BASE, GRAB, CASCADE, snap
    margins in `DeskWindow.tsx`; the glow pool in `world.ts`) read from
    one shared module generated alongside the CSS so the two can never
    drift;
  - an allow-list file for deliberate exceptions, each with a reason.
- Out:
  - visual redesign (HS-96-04);
  - the skill's Tailwind/slide tooling.

## Acceptance criteria

- [x] The validator runs in `npm run check` and CI; a planted raw hex in
      a component style fails it (shown in evidence, then removed).
- [x] `desk.css`/`react-app.css`/`global.css` pass the validator with a
      70-entry allow-list, every entry carrying its reason (atmosphere
      art, local stacking contexts, explicit zeros, and one-off shades
      HS-96-04's material fold consolidates). 86 literals burned down to
      tokens (colors, the z ladder, durations); the gate also fails on
      STALE allow-list entries so the list can only shrink honestly.
- [x] The TS mirror constants come from the generated module; a
      drift test locks CSS and TS to the same values.
- [x] The production build renders pixel-identically except for named
      normalizations; web suite and desk-lock guards pass.

## Test plan

- `npm --prefix web run check`; the planted-violation demonstration;
  the CSS/TS drift test; before/after screenshots at 1440/393.

## Implementation direction

- Burn down file-by-file with screenshot checks between sweeps; never a
  single big-bang regex over `desk.css`.
- Where two literals disagree for the same purpose (three different
  panel alphas, two grip sizes), pick one token and NAME the change.

## Evidence required

- validator wiring + planted-violation output;
- the allow-list with reasons;
- burn-down diff stats and screenshots.
