# HS-60-03 — The armed UX + settings

- **Project:** holdspeak
- **Phase:** 60
- **Status:** done
- **Depends on:** HS-60-02
- **Unblocks:** HS-60-05, HS-60-06
- **Owner:** unassigned

## Problem
The safety story depends on the armed state being unmissable and the
preview being one decisive glance: see it, type it, or ignore it.

## Scope
- **In:** the `armed` activity state across presence (STATE_META + web
  HUD) and the Qlippy dock map; the wake preview surfaced as a card
  (Qlippy when on; the /dictation cockpit always): the transcript +
  the pipeline result + **Type it** + Dismiss. Type it hits a one-shot
  route that types ONLY the server-stored preview (token burned on use,
  expiring with the armed session). The settings section: enable, model,
  threshold, window, action (with the honest preview-vs-type copy), the
  model-download affordance with the explicit egress note. Build clean;
  screenshots.
- **Out:** docs (HS-60-05).

## Acceptance criteria
- [x] The armed state renders in the presence HUD and the Qlippy dock
      (STATE_META + window-view + dock-map locks). The cockpit-banner
      idea was replaced by the recorded design decision: the broadcast
      reaches every socket surface, presence is the purpose-built
      always-visible indicator, and the settings copy recommends it
      (see `evidence-story-03.md` §2).
- [x] The Type-it route types the stored text exactly once and burns
      the token; refuses without a token (400), without a runtime
      (503), after burning (404) — and client-supplied text is
      structurally ignored (asserted with an injection payload).
- [x] Settings ship with strict refusals (HS-60-01) and the honest
      copy locked: the egress note, the false-detection warning on the
      type option, the presence recommendation. First-enable
      self-healing model download added (the documented egress moment).
- [x] Three screenshots reviewed (the armed HUD + the preview card is
      the keeper); `npm run build` clean; 0 `_built/` tracked.

## Test plan
- Route + page-lock tests; a live Playwright pass on the cockpit
  surfaces; full suite.
