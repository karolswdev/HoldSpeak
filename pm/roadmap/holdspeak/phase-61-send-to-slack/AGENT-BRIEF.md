# Phase 61 — Agent Brief (read this first)

**Phase 61 — Send to Slack** for HoldSpeak. Backlog candidate **L**, scoped
by the owner to one easy connector ("Export Connectors are fine…, but let's
just choose an easy one"); Notion/Docs stay parked; **N (Windows) is
owner-rejected** and is not roadmap work.

## 0. Mission

A meeting ends with a digest and a follow-up draft that today only copy to
the clipboard. Give them one outbound door: **Send to Slack**, through an
incoming webhook (one POST, no OAuth), riding the existing
propose→approve→execute actuator flow. Nothing is ever sent without a
per-action approval; the preview IS the message.

## 1. The one thing you must not get wrong

**Executed == previewed, and nothing egresses unapproved** — the Phase-37
invariant, untouched. The proposal's preview is the exact text Slack will
receive; the gated connector refuses any host that isn't the configured
webhook's host, before egress.

## 2. Rules (the standing set)

PMO gate (7 boxes; evidence with done-flips; final-summary at exit); no
`Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-61-send-to-slack`, merged on green; tests via
`uv run pytest -q --ignore=tests/e2e/test_metal.py`; web source only +
`is:global` for JS-rendered DOM; docs under the live voice guard +
POSITIONING canon (new canonical row: "Send to Slack"); real-metal
closeout (a REAL HTTP POST to a local incoming-webhook-shaped receiver
after a REAL approval).

## 3. Ground truth (verified at scaffold)

- **`holdspeak/plugins/builtin/webhook_post_actuator.py` (Phase 38)**:
  `build_webhook_connector(...)` — a gated `network:outbound` connector,
  host-allow-listed, that POSTs a proposal payload's `{url, body}` JSON;
  "covers Slack / Teams incoming webhooks" by design. Non-2xx → `failed`
  + audit. `WebhookPostActuator` exists but is meeting-plugin-shaped; the
  export path records its own proposal directly (the aftercare
  file-issue route is the template).
- **The aftercare seams (Phase 49)**: `meeting_aftercare.py` builds the
  digest + `build_followup_draft` (local markdown); the file-issue route
  in `web/routes/meetings.py` shows the full pattern: build payload →
  `db.actuators.record_proposal(target=…, action=…, preview=…, payload=…)`
  → broadcast `actuator_proposed` (wire-safe, no payload) → the dashboard
  + Qlippy approval flow → `ActuatorExecutor` with an injected connector.
- **The executor wiring**: find where the runtime injects connectors for
  approved proposals (the GitHub path from HS-49-03) and register the
  Slack/webhook connector for `target="slack"` alongside it.
- **Config**: `MeetingConfig.webhook_allowed_hosts` exists (default
  empty). Add `meeting.slack_webhook_url` (default empty = the feature is
  invisible); the Slack connector's manifest allow-lists EXACTLY the
  configured URL's host (setting the URL is the consent for that host —
  no second list to maintain).
- **The surfaces**: the aftercare panel (follow-up draft + digest) in
  `history-app.js`/`history.astro` — "Send to Slack" beside the existing
  copy affordances, visible only when the URL is configured (the
  settings payload or a capability flag on the aftercare response).
- **Qlippy**: `actuator_proposed`/`actuator_result` broadcasts already
  drive his decision/result cards (Phase 56) — Slack proposals get them
  for free.

## 4. Stories

- **HS-61-01 — the export engine + route.** `slack_message_for(digest|
  followup)` (Slack-mrkdwn-safe plain text; the honest length cap),
  `POST /api/meetings/{id}/export/slack` `{what: "digest"|"followup"}` →
  400 when no URL configured / unknown `what` / empty content; records
  the proposal (target `slack`, action `post_message`, preview == the
  exact text, payload `{url, body:{text}}`), broadcasts wire-safely.
  The connector registration for `target="slack"` with the
  URL-host manifest. Config field + settings validation (a URL that
  isn't https or has no host → 400). Tests: route matrix, the
  never-egress-unapproved lock (executor tests pattern), config.
- **HS-61-02 — the surfaces.** "Send to Slack" buttons on the aftercare
  digest + follow-up draft (visible only when configured), wired to the
  route; the proposal then lives in the existing approval UI (and
  Qlippy). The settings field with honest copy (what is sent, only
  after approval, only to this URL's host). Page locks + screenshots;
  build clean.
- **HS-61-03 — docs.** The Meeting Mode Guide's aftercare section gains
  Send to Slack (the approval truth, the host gate, what the message
  contains); SECURITY's egress table gains the row; POSITIONING gains
  the canonical row. Voice guard green.
- **HS-61-04 — closeout.** Live: a real meeting → the real route → the
  real proposal → Qlippy/dashboard approval → the REAL connector POSTs
  to a REAL local incoming-webhook receiver (the message body asserted
  byte-equal to the preview); unconfigured = invisible + 400 (the
  off-proof). Full suite; final-summary; BACKLOG L flipped; README;
  PR merged on green.

## 5. Gotchas

- **The wire-safety rule**: the machine payload (with the URL) never
  rides a broadcast — preview only (the Phase-56 lock pattern).
- **The webhook URL is a secret-ish value** (Slack treats webhook URLs
  as credentials): never put the URL in previews, broadcasts, or the
  aftercare response — surfaces say "Slack" / the host at most.
- **Slack incoming webhooks want `{"text": ...}`** JSON; plain text with
  mrkdwn conventions (no rich blocks — the Phase-38 posture).
- **The executor's connector routing** is by target — confirm how the
  GitHub connector is selected and mirror it exactly.
- **The voice guard is live** for all doc prose.
