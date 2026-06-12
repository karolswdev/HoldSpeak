# Evidence — HS-61-04: Closeout: the real POST + final-summary + PR

**Date:** 2026-06-12
**Verdict:** done. The live trace shipped (a real browser approval driving
a real HTTP POST byte-equal to the preview, into a real local receiver),
plus the off-proof, the wrong-host refusal, and the phase exit artifacts.

## The live trace (`dogfood_story04.py` — 14/14 PASS, zero page errors)

No mocks anywhere in the chain: a stdlib HTTP server shaped like a Slack
incoming webhook (answers 200 "ok") on loopback; real Chromium on the real
/history page; the real decision route; the real `build_slack_connector`
over the real gated-connector stack; the real urllib transport.

1. Clicking **Send to Slack** recorded exactly one `proposed` proposal —
   and the receiver had received **nothing** (never egress unapproved).
2. The proposal card stated the slack truth ("approving sends this exact
   message to Slack" — the per-target guard copy added this story, since
   the generic "only records your decision" copy became untrue for slack).
3. Clicking **Approve** flashed "Approved — sent to Slack." and the
   receiver got **exactly one** POST: the configured path, Content-Type
   application/json, body `{"text": <preview>}` **byte-equal** to the
   stored proposal preview (json-compared on the wire).
4. The proposal finished `executed`; audit `proposed → approved →
   executed`.
5. **The live wrong-host probe**: `build_webhook_connector` with a
   127.0.0.1-only manifest, handed a proposal pointing at `192.0.2.55`,
   refused with `ConnectorOperationRefused` BEFORE any socket opened
   (real transport — no fake client), and the receiver count stayed 1.
6. **The off-proof**: URL cleared from config → the export route refused
   with 400 "not configured". (The visible UI off-proof shipped in the
   HS-61-02 dogfood.)

Screenshots: `story04-proposed.png` (the proposal awaiting approval, with
the slack guard copy), `story04-executed.png` (the Executed card — whose
visible payload contains the body only, no URL: the credential rule on
screen).

## Phase exit

- Full suite: **2768 passed, 17 skipped** (+1: the guard-copy lock added
  to `test_history_slack_surfaces.py`; web rebuilt, 0 `_built/` tracked).
- `final-summary.md` written; BACKLOG **L flipped to shipped** (Notion/
  Docs stay parked; N stays owner-rejected); project README cadence done.
- PR opened from `phase-61-send-to-slack`, merged on green CI (see the
  status doc's Last updated for the link).
