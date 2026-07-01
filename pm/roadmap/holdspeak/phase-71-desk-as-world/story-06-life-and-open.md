# HS-71-06 — In-world Qlippy, the create beat, and open-an-object

- **Status:** todo
- **Priority:** MED
- **Depends on:** HS-71-03
- **Evidence:** _(added at close)_

## Goal

Add the life and the payoff: the mascot living in the world, new objects
arriving with a flourish, and tapping an object opening it — so the desk is
inhabited and usable, not just admired.

## Scope

- **In-world Qlippy** — the `DioCompanion` port: `web/public/qlippy/qlippy.png`
  (already web-ready) in the corner (`~90%, 86%`) with a gentle sway/bob + its
  own blurred ground shadow. Decorative, focus-safe, honors the presence/mascot
  toggle already in config (do not force it on).
- **The create beat** — a newly-created/just-arrived object gets the iPad "NEW"
  flourish: an accent halo + a pulsing ring + a short-lived NEW badge, then
  settles. Drives off the existing create flows in `desk-app.js`.
- **Open an object** — a tap (distinct from a drag, per HS-71-04's threshold)
  opens the primitive's existing detail/authoring surface (the current
  desk-app open path). No new detail UI; wire the gesture to what exists.
- Motion respects reduced-motion.

## Proof required

Screenshots: Qlippy in the corner with its shadow; a just-created object mid-NEW
beat; a tap opening an object (before/after). The mascot toggle honored (off →
no Qlippy). Tap vs. drag disambiguation proven.

## Done

_(filled at close)_
