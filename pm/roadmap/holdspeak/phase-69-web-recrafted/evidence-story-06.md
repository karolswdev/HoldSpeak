# Evidence — HS-69-06: Qlippy dock into the cockpit

**Date:** 2026-06-29
**Verdict:** done. Qlippy's dock + actionable cards now ride the main browser
cockpit (not only the native HUD), via a shared component — proven in the
cockpit and proven non-regressive on `/presence`.

## What shipped

- **`web/src/components/Qlippy.astro`** (new): the dock + card shell markup, the
  full `q-*` styles (authored `is:global`), and the `qlippy.js` /
  `qlippy-events.js` `<script src>` drivers — lifted verbatim out of
  `presence.astro` (HS-56-02). One source, two surfaces.
- **`web/src/layouts/AppLayout.astro`**: mounts `<Qlippy />` so it rides every
  cockpit route. Positioned bottom-right; the Queue HUD is top-center, so no
  collision.
- **`web/src/pages/presence.astro`**: the inline Qlippy markup + the `q-*`
  styles + the two driver scripts were removed and replaced with `<Qlippy />`
  (385 → 144 lines); the presence-card + presence-app.js stay.
- **`tests/integration/test_presence_qlippy_shell.py`**: `_page()` retargeted to
  read `presence.astro` + `Qlippy.astro` (the shell relocated; the contract — a
  static hidden skeleton, the sprite grammar, the motion spec — is unchanged).

Double-gated unchanged: qlippy.js still un-hides only when `/api/settings`
reports presence.enabled AND presence.mascot; off ⇒ nothing renders.

## Proof

- **`screenshots/qlippy-cockpit.png`** — on `/history` (a cockpit page) with
  presence+mascot on: the bottom-right dock sprite plus a slid-in "DECISION
  NEEDED" card with the ⌂ Local egress badge and Approve / Decline / Later pills
  (driven via `window.qlippyCard.present(...)`,
  `scripts/screenshot_phase69_qlippy.py`).
- **`screenshots/presence-qlippy-regression.png`** — the native HUD `/presence`
  still renders the same shell from the component (a RESULT card with the
  ☁ github egress badge + a View pill + the dock), confirming the extraction did
  not regress the load-bearing overlay.
- **Tests:** the retargeted shell locks + the mascot gate + the
  actuator/learning/aftercare broadcasts + the presence indicator + the density
  guard + the route pre-flight = **49 passed**.
