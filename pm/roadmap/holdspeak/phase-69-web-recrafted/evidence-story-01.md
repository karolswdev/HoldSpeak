# Evidence — HS-69-01: Egress badge → the cockpit

**Date:** 2026-06-30
**Verdict:** done. The structured egress badge rides cockpit surfaces, confirmed
global in the built CSS and visible in live screenshots.

## What shipped (substrate wave, confirmed)

- The global `.egress-badge` (`web/src/styles/global.css`) with `is-local`
  (`--ok`) / `is-mixed` / `is-cloud` (`--accent`) variants, and the
  `egress-badge.js` module that renders the `{scope,label}` chip.
- Confirmed **global** (no astro cid) in the built CSS, so it reaches the
  JS/Alpine-injected cockpit cards.

## Proof (existing screenshots + probes this phase)

- **`screenshots/qlippy-cockpit.png`** — the Qlippy decision card carries the
  **⌂ Local** badge in the main cockpit; **`presence-qlippy-regression.png`** —
  the **☁ github** badge on a result card.
- **`screenshots/activity.png`** — the pre-briefing nudge cards carry the egress
  badge; the activity agent runs-on chip uses it (`is-${scope}`).
- **`screenshots/companion-agent-desk.png`** — the "local + your LAN" badge in
  the Agent Desk header.
- POSITIONING's "egress is a badge, not prose" obligation is met on the cockpit,
  not only `/presence`. History/proposal cards remain badge-less by design
  (no egress data; a backend field would be needed — noted, not faked).
