# HS-62-01 — The egress badge on Qlippy cards

- **Project:** holdspeak
- **Phase:** 62
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-62-02, HS-62-04
- **Owner:** unassigned

## Problem
Every Qlippy card renders a `privacy:` paragraph (the Phase-56 "three
answers" pattern). The owner finds the narration cringey; the posture
should be one glance, not a paragraph.

## Scope
- **In:** the card shell (`qlippy.js` + `presence.astro`) renders a
  compact badge from a structured `egress` field — `local` (⌂ Local),
  `mixed` (⌂+☁), `cloud` (☁ + the target label) — replacing the
  `#qlippy-privacy` paragraph. Every card in `qlippy-events.js` swaps
  its privacy prose for the right state: proposal/result cards → cloud
  with target; learned/aftercare/wake cards → local. `privacyLine()`
  deleted. Locks updated to pin the badge (shell ids, wake card,
  actuator broadcast test, the doc-drift verbatim lock's js half moves
  to HS-62-03 with the doc).
- **Out:** the rest of the web UI prose (HS-62-02); docs (HS-62-03).

## Acceptance criteria
- [x] No card passes `privacy:` prose; the badge renders for all three
      states with the cloud target label surviving.
- [x] The badge is styled and VISIBLE on the live card (JS-rendered DOM —
      proven by screenshot or computed-style probe, not grep).
- [x] All previously-locked tests updated and green; no old-copy lock
      left half-alive.

      See `evidence-story-01.md`.

## Test plan
- Updated shell/event locks; a live render check in the story dogfood or
  the closeout's; the qlippy/presence/wake test slices green.
