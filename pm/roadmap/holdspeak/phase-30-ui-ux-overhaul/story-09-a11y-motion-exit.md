# HS-30-09 — Accessibility + motion + polish + phase exit

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
- **Depends on:** HS-30-06, HS-30-07, HS-30-08
- **Owner:** unassigned

## Problem

A dark, bold identity is the place a11y quietly fails — low-contrast muted text,
orange-on-dark below AA, invisible focus rings, motion that ignores reduced-motion
preferences. This story is the quality gate: verify accessibility across every
route, finalize the motion grammar, sweep cross-route inconsistencies, and close
the phase.

## Scope

### In

- **Contrast:** verify AA across all routes on the Signal palette — body text,
  muted text, accent-on-dark, status colours, disabled states (4.5:1 text / 3:1
  large + non-text). Fix any failing token; this is verified, not eyeballed.
- **Focus + keyboard:** visible focus rings on the dark canvas for every
  interactive element; full keyboard navigability of nav, forms, modals, and the
  dashboard controls.
- **Motion:** finalize the Signal motion grammar (easing + durations) and ensure
  `prefers-reduced-motion: reduce` disables non-essential animation (incl. the
  live-status pulse, ambient/glow motion).
- **Polish sweep:** a cross-route consistency pass — spacing rhythm, alignment,
  empty/loading/error states, icon family — so the five routes read as one product.
- **Phase exit:** write `final-summary.md`; flip the RFC/canon references; record
  the deferred **light theme** handoff.

### Out

- New features; further structural redesign (that's done by HS-30-06/07/08).

## Acceptance criteria

- [ ] AA contrast verified across all five routes (results captured in evidence,
      not asserted); any failure fixed at the token level.
- [ ] Visible focus rings + full keyboard nav on every route (screenshots /
      capture of focus states).
- [ ] `prefers-reduced-motion` honoured everywhere (verified with the media query
      forced on).
- [ ] Cross-route consistency pass complete; no route is visibly off-system.
- [ ] `npm run build` green; full backend sweep
      `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.
- [ ] `final-summary.md` written: before/after, asset/test posture, deferred
      light-theme handoff. Phase doc frozen.

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (full sweep).
- A11y: contrast check per pairing (tooling or computed ratios — record numbers);
  keyboard walk of each route; reduced-motion forced-on check.
- Visual: `npm run dev`; final screenshots of all five routes for the summary.
- Build: `npm run build` exit 0.

## Notes / open questions

- The `ui-ux-pro-max` "Modern Dark" guidance flags accent-contrast on dark as the
  top a11y risk — give it the most scrutiny.
- Light theme stays deferred; the summary must hand off the token structure that
  makes it an additive layer.
