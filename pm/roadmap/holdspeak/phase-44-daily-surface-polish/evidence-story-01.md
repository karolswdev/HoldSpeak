# Evidence — HS-44-01 — Dashboard idle home + hero polish

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-44-daily-surface-polish`

## What shipped
A premium **idle "command center" home** on the dashboard (`/`) — the first
daily-driver surface lifted toward the Phase-43 wizard's bar, behavior-preserving.

- **Daily-action cards** (`web/src/pages/index.astro`, idle-only via
  `x-show="!meetingActive && !stopInProgress"`): **Dictation cockpit · Meeting
  history · Local activity · Settings** — each an elevated card (accent-tint icon
  + display title + a one-line description + a → that slides on hover), matching
  the wizard's "Done" cards. Warms up the home and guides a returning user to the
  surfaces they use daily.
- **An accent glow** behind the home (`.runtime::before` radial gradient), the
  same ambient treatment as the wizard.
- Reduced-motion safe (hover transform/arrow collapse); the live meeting view
  (hero, transcript, intel, actions) is untouched and reclaims the screen when a
  meeting is active.

## Verification
- **Live (Playwright):** the four cards render on the idle dashboard.
  Screenshot: [`dashboard_home.png`](./evidence/dashboard_home.png).
- `test_web_dashboard_home.py` — the cards + idle-gating + the four hrefs + glow +
  reduced-motion.

## Acceptance criteria
- [x] The dashboard idle home is visibly elevated (command-center cards + glow);
      behavior unchanged (idle-only; meeting view intact); reduced-motion + a11y;
      suite green; 0 `_built/`.
