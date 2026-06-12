# Evidence — HS-61-01: The export engine + route

**Date:** 2026-06-11
**Verdict:** done. The engine, the route, the execute leg, the config, and
the settings boundary all ship, with 39 new tests and the full suite green.

## What shipped

- `holdspeak/slack_export.py` (new): `slack_message_for(digest, what)`
  (mrkdwn digest + the HS-49-04 follow-up draft converted; honest cap at
  3,800 chars with a visible truncation notice), `slack_webhook_host`
  (THE shared URL rule: https with a host; plain http for loopback only,
  so the closeout can prove the POST against a real local receiver), and
  `build_slack_connector` (wraps the Phase-38 `build_webhook_connector`
  with a manifest allow-listing exactly the configured URL's host).
- `POST /api/meetings/{id}/export/slack` `{what: digest|followup}` in
  `web/routes/meetings.py`, modeled on the HS-49-03 file-issue route:
  400 unconfigured / unknown kind / empty aftercare, 404 missing meeting;
  success records a `proposed` proposal (target `slack`, action
  `post_message`, **preview byte-equal to the stored body text**) and
  broadcasts `actuator_proposed` wire-safely. Content-hash idempotency:
  identical content dedupes, edited aftercare re-proposes.
- **The execute leg** (`_execute_slack_proposal`): a ground-truth finding
  at scaffold was that NO production execute path existed (the
  `ActuatorExecutor` was only ever host-injected in dogfoods/tests). For
  `slack` proposals the decision route now executes on approval through
  the full executor guard stack (status gate, payload parity, audit,
  `on_result` → `actuator_result` broadcast). Consent reasoning recorded
  in code: configuring the URL is consent for exactly that host (the
  Phase-52 model) PLUS the per-action approval — no third toggle. Other
  targets keep today's behavior (approval flips state only; locked).
- **The credential rule, structurally**: the webhook URL never enters the
  proposal payload — the stored payload is `{"body": {"text": ...}}` and
  the connector joins the URL in memory at execution time. So
  `GET /api/meetings/{id}/proposals` (which returns payloads) can never
  leak it, by construction.
- `MeetingConfig.slack_webhook_url` (default empty = invisible) with
  `__post_init__` delegating to the one shared rule; the settings route
  refuses malformed URLs with clean 400s that change nothing.

## Proof (tests written first, then read green)

- `tests/unit/test_slack_export.py` — 21 tests: builder content for both
  kinds, unknown-kind refusal, the visible-truncation cap, the URL rule
  matrix (valid https / loopback http; refused plain-http, ftp, hostless,
  garbage), config-field enforcement, connector POSTs stored body to the
  configured URL, credential-never-rests-on-the-proposal, smuggled-URL
  overwrite, the Phase-38 host-gate backstop, non-2xx raises.
- `tests/integration/test_web_slack_export.py` — 18 tests: the route
  matrix; preview == wire body; dedupe/re-propose; **never egress
  unapproved** (proposed refused by the executor with zero transport
  calls; rejection posts nothing); approval executes through the REAL
  gated-connector stack (only `_default_post` faked) with the body
  byte-equal to the preview and audit `proposed -> approved -> executed`;
  URL-removed-between-propose-and-approve fails honestly; GitHub
  approvals unchanged; the URL absent from every response and broadcast
  (string-probed against the full wire); `actuator_proposed`/
  `actuator_result` ride for Qlippy with no payload; settings round-trip
  + 4 malformed-URL 400s.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **2762 passed, 17 skipped** (was 2723; +39, no regressions).

## Notes

- The loopback-http carve-out exists so HS-61-04 can drive a REAL POST
  into a real local incoming-webhook-shaped receiver; real Slack URLs are
  always https and the rule still refuses plain http anywhere else.
