# HS-30-09 — Accessibility + motion + polish + phase exit

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
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

- [x] AA contrast **computed** (`evidence/a11y-contrast.py`) for the whole palette,
      not asserted: all functional pairings AA/AAA; the only FAIL (white-on-accent,
      2.84) is design-forbidden + never shipped, so no token change was needed.
- [x] Accent focus rings defined globally + per interactive component (visible on
      dark); skip-link, Settings drawer (Esc + focus move/return), nav are keyboard-
      operable.
- [x] `prefers-reduced-motion: reduce` honoured product-wide from one `tokens.css`
      media block (durations → 0, animations off) — covers pulse / spinner / caret.
- [x] Cross-route consistency confirmed across `after-hs0{4..8}/` — one Signal
      vocabulary, no route off-system.
- [x] `npm run build` green; full backend sweep `2062 passed, 14 skipped`.
- [x] `final-summary.md` written (goal met, exit criteria, `--wb-*` lesson, a11y
      posture, handoff). Phase doc frozen.

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
