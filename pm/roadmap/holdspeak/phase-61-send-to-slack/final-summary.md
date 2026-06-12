# Phase 61 — Send to Slack: final summary

**Closed:** 2026-06-12, 4/4 stories, opened the day before on owner
direction (backlog **L** scoped to one easy connector: "Export Connectors
are fine…, but let's just choose an easy one"). In the same direction, **N
(Windows) was rejected by the owner** and is recorded in BACKLOG as
community-port-welcome, not roadmap work.

## What shipped

The meeting loop's results (the aftercare digest and the follow-up draft)
gained one outbound door: **Send to Slack**, through a Slack incoming
webhook (one POST, no OAuth, no rich blocks), riding the existing
propose→approve→execute actuator flow on the Phase-38 host-gated webhook
connector.

- **The engine** (`holdspeak/slack_export.py`): the exact message in Slack
  mrkdwn (digest built natively; the HS-49-04 follow-up draft converted),
  capped at 3,800 chars with a visible truncation notice, never silently.
- **The route** (`POST /api/meetings/{id}/export/slack`): records a
  proposal whose **preview is byte-equal to the wire body**; refuses
  honestly (unconfigured / unknown kind / empty aftercare → 400, missing
  meeting → 404); content-hash idempotency (identical content dedupes,
  edited aftercare re-proposes).
- **The execute leg the repo never had**: a scaffold ground-truth find was
  that NO production path ever executed an approved proposal (the
  `ActuatorExecutor` was host-injected in dogfoods only). The decision
  route now executes approved `slack` proposals through the full executor
  guard stack (status gate, payload parity, audit, the `actuator_result`
  broadcast). Consent model: configuring the URL is consent for exactly
  its host PLUS a per-action approval — approving IS the send, stated on
  the proposal card, in the flash, and in the docs. Other targets keep
  approval-flips-state-only, locked by test.
- **The credential rule, structural**: the webhook URL never enters a
  proposal payload, a broadcast, or a non-settings API response. The
  stored payload is `{"body": {"text": ...}}`; `build_slack_connector`
  joins the URL in memory at execution time, so `GET .../proposals`
  cannot leak it by construction.
- **The surfaces**: green-edged configured-only buttons on the aftercare
  digest + the draft view (gated on a `slack_configured` bool); honest
  notes that flip with configuration; the settings field whose copy states
  what is sent, when, and where the URL lives.
- **Docs under canon**: the Meeting Mode Guide section (with a real
  product screenshot), the SECURITY egress row + secrets entry, the
  POSITIONING canonical row, and the voice guard extended to ban "Slack
  integration"/"Slack export" (proven both ways).

## The closeout proof (no mocks anywhere)

A real local incoming-webhook-shaped receiver + a real Chromium driving
the real UI (`dogfood_story04.py`, 14/14 PASS, zero page errors):
clicking Send to Slack recorded one `proposed` proposal and **nothing
reached the receiver**; clicking Approve drove the real decision route →
the real gated connector → a real urllib POST; the receiver got **exactly
one** JSON POST whose body was **byte-equal** to the stored preview; the
audit reads proposed → approved → executed. The live wrong-host probe
(manifest 127.0.0.1, proposal pointing at 192.0.2.55, real transport)
refused before any socket opened. The off-proof: URL cleared → 400.

## Honest limits

- v1 exports the digest and the follow-up draft only; plain text (Slack
  mrkdwn), no rich blocks, no threads, no OAuth.
- A rejected proposal with byte-identical content cannot be re-proposed
  until the aftercare content changes (the idempotency key is
  content-hashed). Edit the aftercare or accept an item and the button
  works again.
- Plain http is accepted for loopback hosts only (it is how the closeout
  proves the real POST); real Slack URLs are https and the rule refuses
  plain http anywhere else.

## Numbers

- Final suite: **2768 passed, 17 skipped** (+45 over the Phase-60 close:
  21 + 18 engine/route, 6 surface locks, the guard extension).
- 4 commits, one per story, plus the scaffold; PR merged on green CI.

## Where this leaves the backlog

**L is shipped** (scoped to Slack; Notion/Docs stay parked). **N is
owner-rejected.** M is mostly absorbed (the wake preview is the M pattern
scoped to wake runs). The launch moment is the strongest remaining
strategic row.
