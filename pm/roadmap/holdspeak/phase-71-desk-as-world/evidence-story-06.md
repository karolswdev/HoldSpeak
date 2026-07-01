# Evidence — HS-71-06: In-world Qlippy, the create beat, open-an-object

**Date:** 2026-07-01
**Verdict:** done. The desk is inhabited and usable now: Qlippy lives in the
corner, freshly-created objects arrive with a flourish, and tapping an object
opens it.

## What shipped

- **In-world Qlippy** (`web/src/pages/desk.astro` + `desk-app.js`):
  `web/public/qlippy/qlippy.png` (already web-ready) sits fixed in the
  bottom-right corner with a gentle sway/bob + its own ground shadow, decorative
  and pointer-events-none. **Gated on the mascot toggle**: `loadMascot()` reads
  `config.presence.mascot` from `/api/settings` (default **off**; not forced on).
- **The create beat** (`markNew(id)` / `isNew(o)`): a freshly-created object
  gets an accent glow, a pulsing ring (`desk-obj-ring`, 3 pulses), and a short
  **NEW** badge, then settles (4.5s). Wired into the real create flows
  (`submitNote` / `submitAgent` / `submitKb`).
- **Open an object** (`openObject(o)`): a tap (distinct from a drag, via the
  HS-71-04 movement threshold — `justDragged` guards it) opens the primitive.
  Meetings navigate to their detail (`/history?meeting=<id>`); the other kinds
  (no standalone detail route) reveal their full card in the "Browse as a list"
  detail. No new detail UI — the gesture wires to what exists.
- Motion respects `prefers-reduced-motion` (Qlippy + the ring freeze).

## Proof (Playwright, mascot enabled in the seed config)

- **Qlippy shown:** `True` — the corner sprite renders with the mascot toggle on.
- **NEW badge visible:** `True` — `markNew('m0')` lit the accent glow + NEW badge.
- **Tap-to-open:** clicking a meeting object navigated to
  **`/history?meeting=m0`** (`opened URL: True`).
- **`screenshots/06-qlippy-newbeat.png`** — Qlippy in the corner + the first
  object mid create-beat (accent glow).
- **Tests:** route pre-flight **2 passed** (zero page errors on `/desk`); full
  suite **3045 passed, 37 skipped**; build green.
