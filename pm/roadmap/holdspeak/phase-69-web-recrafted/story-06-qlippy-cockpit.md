# HS-69-06 — Qlippy dock into the cockpit

- **Status:** done
- **Priority:** MED
- **Depends on:** HS-69-01 (the shared egress badge), HS-69-02
- **Catalog pattern(s):** §6, §9 (Qlippy reuse)
- **Evidence:** [evidence-story-06.md](./evidence-story-06.md)

## Goal

Bring Qlippy's rich dock + actionable cards off `/presence` (where they were
stranded for the native HUD) and into the main browser cockpit, reusing the
existing sprite pipeline; the cards carry the egress badge.

## Scope

- Extract the dock + card shell (markup + styles + the qlippy.js /
  qlippy-events.js drivers) out of `presence.astro` into a shared
  `components/Qlippy.astro` — one source, two surfaces.
- Mount `<Qlippy />` in `AppLayout` so it rides every cockpit route.
- Keep the native HUD (`/presence`) byte-for-byte equivalent (it now consumes
  the same component).
- Double-gated as before (presence.enabled + presence.mascot); off ⇒ nothing.

## Proof required

Qlippy dock + cards rendering in the main cockpit (not just `/presence`); cards
carry the egress badge; the existing sprite pipeline reused; the native HUD
unbroken.

## Done

Shipped and proven both ways. `qlippy-cockpit.png`: the dock + a "DECISION
NEEDED" card with the ⌂ Local egress badge and Approve/Decline/Later pills,
rendered on `/history` (a cockpit page). `presence-qlippy-regression.png`: the
native HUD still renders the same shell (a result card with the ☁ github badge).
The shell-lock test was retargeted to read the new component home; 49 passed
across the presence/Qlippy/web slices + route pre-flight.
