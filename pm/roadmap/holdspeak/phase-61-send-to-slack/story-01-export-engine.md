# HS-61-01 — The export engine + route

- **Project:** holdspeak
- **Phase:** 61
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-61-02, HS-61-04
- **Owner:** unassigned

## Problem
The aftercare digest and the follow-up draft only leave by clipboard.
There is no Slack message builder, no export route, no `slack` connector
registration, and no config for a webhook URL.

## Scope
- **In:** `slack_message_for(meeting, what)` for `what in {digest,
  followup}` — Slack-mrkdwn-safe plain text reusing the aftercare
  builders, with an honest length cap (truncate with a visible marker,
  never silently). `POST /api/meetings/{id}/export/slack` with body
  `{what: "digest"|"followup"}` → 400 when `meeting.slack_webhook_url`
  is unconfigured, `what` is unknown, or the content is empty; 404 for a
  missing meeting; on success records a proposal (target `slack`, action
  `post_message`, preview == the exact message text, payload
  `{url, body: {text}}`) and broadcasts `actuator_proposed` wire-safely
  (no payload, no URL). Connector registration for `target="slack"`
  mirroring the GitHub target routing, built via the Phase-38
  `build_webhook_connector` with a manifest allow-listing exactly the
  configured URL's host. `MeetingConfig.slack_webhook_url` (default
  empty) + settings validation (must be https with a host, or empty).
- **Out:** UI buttons and the settings field markup (HS-61-02); docs
  (HS-61-03); rich blocks/OAuth/threads (out of phase).

## Acceptance criteria
- [ ] The message builder produces the digest and follow-up texts,
      mrkdwn-safe, capped honestly; empty meetings yield empty content
      (and the route refuses them).
- [ ] The route matrix holds: unconfigured → 400 (the off-proof at the
      API layer), unknown `what` → 400, missing meeting → 404, success
      records the proposal with preview byte-equal to the payload text.
- [ ] The wire-safety lock: no broadcast and no API response ever
      contains the webhook URL or the machine payload.
- [ ] Never-egress-unapproved: executor-pattern tests prove a recorded
      `slack` proposal POSTs nothing until approved, and the connector
      refuses any host other than the configured URL's host before
      egress.
- [ ] Config round-trips; malformed URLs (http, no host, garbage)
      refuse with clean 400s that change nothing.

## Test plan
- Unit: the message builder; the connector manifest host derivation.
- Integration: the route matrix; settings-boundary 400s; the
  never-egress-unapproved executor lock; the wire-safety lock.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
