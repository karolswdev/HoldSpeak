# HS-10-02 - Design token layer

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-10-01
- **Unblocks:** HS-10-03, HS-10-05
- **Owner:** unassigned

## Problem

Today's five inline `:root` blocks each define their own colors, radii,
and font stacks, with drift between them (compare `dashboard.html`'s
24px panel shadow + 30px radii against `activity.html`'s tighter, flat
look). Without a single token source, every component built downstream
will silently re-introduce inconsistency.

## Scope

- **In:**
  - `web/src/styles/tokens.css` — color, typography, spacing, radius,
    elevation, motion, and z-index tokens, expressed as CSS custom
    properties layered on top of Open Props defaults.
  - HoldSpeak palette: a refined, less-blue dark canvas with one
    deliberate accent (the "hold" cyan) and a calmer warm secondary;
    explicit success/warn/danger ramps.
  - Type scale anchored on a self-hosted UI face and self-hosted mono
    face (no Google Fonts at runtime). License files stored under
    `web/src/assets/fonts/`.
  - Spacing scale: 4px base, with named steps (`--space-1`..`--space-8`).
  - Motion tokens: duration short/medium/long, easing standard/emphasized,
    plus `@media (prefers-reduced-motion: reduce)` overrides that flatten
    durations to 0ms.
  - `tokens.css` imported once at the layout level so every page picks
    it up without re-importing.
- **Out:**
  - Light-theme tokens (deferred; recorded as resolved-deferred in
    `style-handoff.md` as part of HS-10-13).
  - Component CSS (HS-10-03).
  - Per-route theming.

## Acceptance Criteria

- [ ] `tokens.css` exists, is the single source of color/type/space/
  radius/motion variables, and is consumed by the design-check route
  from HS-10-01.
- [ ] Tokens cover every value currently hard-coded in the five inline
  `:root` blocks (an inventory table in the evidence file proves the
  mapping).
- [ ] Self-hosted fonts load from `holdspeak/static/` post-build, with
  no network requests to external font CDNs.
- [ ] `prefers-reduced-motion: reduce` collapses motion tokens to 0ms.
- [ ] WCAG AA contrast verified for body text on canvas, muted text on
  canvas, and accent on canvas (3 ratios reported in evidence).

## Test Plan

- Manual contrast audit using a color-contrast tool; ratios recorded in
  `evidence-story-02.md`.
- Manual `prefers-reduced-motion` toggle in DevTools, confirming
  durations flatten.
- Network-tab inspection on a built page: zero font requests to
  external origins.

## Notes

Tokens are the single highest-leverage artifact in this phase. Resist
the temptation to also start authoring components here — they belong
to HS-10-03, where token consumption can be reviewed in isolation.
