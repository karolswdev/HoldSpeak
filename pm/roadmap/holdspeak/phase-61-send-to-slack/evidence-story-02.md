# Evidence — HS-61-02: The surfaces

**Date:** 2026-06-12
**Verdict:** done. The aftercare buttons (configured-only), the settings
field with the honest copy, page locks, a live browser dogfood with zero
page errors, and four reviewed screenshots.

## What shipped

- **The capability flag**: `GET /api/meetings/{id}/aftercare` now carries
  `slack_configured` (a bool — the credential never rides the response;
  string-probed in the test).
- **The aftercare card** (`history.astro`): a green-edged "Send to Slack"
  pill in the head actions (the digest) and a second button beside "Copy
  draft" in the follow-up view — both gated on the flag, so an
  unconfigured install shows no visible Slack affordance anywhere. The
  draft's privacy note flips honestly: local-only copy when unconfigured,
  "creates a proposal; nothing is sent until you approve it below" when
  configured. The Slack accent is deliberately distinct (the `--ok`
  green): the eye separates "leaves the machine (after approval)" from
  the local-only affordances beside it.
- **The wiring** (`history-app.js`): `exportToSlack(what)` POSTs the
  HS-61-01 route and surfaces the proposal in the existing approval
  section (deduped on id); the decision flash now tells the truth about
  the execute-on-approve leg ("Approved — sent to Slack." / the failure
  variant), since approval is no longer state-only for slack targets.
- **The settings field** (`settings.astro`, Meetings & intel, searchable
  under "slack"): the URL input plus the honest copy — what is sent
  (digest or draft, exactly as previewed), only after a per-action
  approval, only to this URL's host, stored locally and shown nowhere
  else, empty keeps the feature off.
- **A polish fix found by reviewing the screenshot**: the head-action
  pills wrapped mid-word ("Send to Slack" over three lines); the action
  row now wraps as a whole with `white-space: nowrap` per pill.

## Proof

- `tests/integration/test_history_slack_surfaces.py` — 5 tests: the flag
  false/true at the API (and never the URL), the page gating locks (every
  Slack affordance behind `slack_configured`; both wirings present; both
  honest notes), the JS wiring lock, the settings honest-copy lock.
- **Live dogfood** (`dogfood_story02.py`, real server + real Chromium,
  11/11 PASS, zero page errors):
  1. unconfigured: zero visible Slack buttons; the draft note keeps the
     local-only truth;
  2. configured: both buttons render; the note states the approval truth;
  3. clicking creates EXACTLY one `proposed` proposal (no egress), with
     the "Nothing is sent yet" flash, and the credential appears nowhere
     on the proposal record;
  4. settings: the field surfaces under search "slack" with the honest
     copy.
- Screenshots (reviewed): `story02-off.png` (the off-proof),
  `story02-configured-card.png`, `story02-draft.png` (copy + send side
  by side), `story02-proposal.png`, `story02-settings.png`.
- `cd web && npm run build` clean (13 pages); 0 `_built/` files tracked.
- Full suite: **2767 passed, 17 skipped** (+5).
