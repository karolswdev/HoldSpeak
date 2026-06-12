# HS-61-02 — The surfaces

- **Project:** holdspeak
- **Phase:** 61
- **Status:** done
- **Depends on:** HS-61-01
- **Unblocks:** HS-61-03, HS-61-04
- **Owner:** unassigned

## Problem
The route exists but nothing in the UI reaches it, and there is nowhere
to set the webhook URL without editing the config file.

## Scope
- **In:** "Send to Slack" buttons on the aftercare digest and the
  follow-up draft (history surfaces), beside the existing copy
  affordances — rendered only when a webhook URL is configured (a
  capability flag; never the URL itself), wired to the export route;
  after a send the user is pointed at the approval flow (the proposal
  lives in the existing dashboard + Qlippy cards — no new approval UI).
  The settings field for `meeting.slack_webhook_url` with honest copy:
  what is sent, only after a per-action approval, only to this URL's
  host; the URL is stored locally and treated as a credential. Page
  locks + screenshots; `cd web && npm run build` clean; source only.
- **Out:** the engine/route (HS-61-01); docs prose (HS-61-03).

## Acceptance criteria
- [x] Unconfigured shows no visible Slack affordance on the aftercare
      surfaces: no buttons, no Slack mention (locked by the gating test
      and proven visibly in the live dogfood; hidden x-show markup is
      the product's standard Alpine gating).
- [x] Configured: both buttons render, POST the route with the right
      `what`, and surface the "waiting for your approval" outcome; a
      route error surfaces honestly (the flash carries the error).
- [x] The settings field round-trips through the settings API; the
      honest copy ships verbatim (page lock); the URL is never echoed
      into any non-settings surface (string-probed at the aftercare
      API and on the proposal record).
- [x] Screenshots of the configured aftercare panel and the settings
      field ship with the evidence; the web build is clean and no
      `_built/` file is tracked.
      See `evidence-story-02.md`.

## Test plan
- Integration: surface locks (gating, copy, wiring markers) following
  the Phase-60 settings-lock pattern; settings round-trip.
- Manual: screenshots against the live web UI.
- Full suite + web build.
