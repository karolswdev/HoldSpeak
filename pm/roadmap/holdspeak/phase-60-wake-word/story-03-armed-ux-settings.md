# HS-60-03 — The armed UX + settings

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
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
- [ ] The armed state renders in the presence HUD and the Qlippy dock
      (page/dock-map locks); the cockpit banner shows armed + preview.
- [ ] The Type-it route refuses without a valid token, types the stored
      text verbatim once, and burns the token (route tests).
- [ ] Settings round-trip with refusals; the download affordance states
      the egress plainly (page lock).
- [ ] Screenshots reviewed; `npm run build` clean; 0 `_built/` tracked.

## Test plan
- Route + page-lock tests; a live Playwright pass on the cockpit
  surfaces; full suite.
