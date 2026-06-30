# Evidence — HS-69-12: Web /companion → the Agent Desk

**Date:** 2026-06-30
**Verdict:** done. `/companion` is no longer a static docs portal — it is the
Agent Desk: a living desk of the real agents + the live companion link.

## What shipped

- **`web/src/pages/companion.astro`** rewritten as the Agent Desk (Alpine
  `companionDesk()`): a header with the **link chip** (`is-{idle|ok|needs}`,
  pulsing) + the egress badge; a warn-spined **Needs you** zone (the coders
  awaiting you); an **Agents** zone of persona cards (avatar, role, tool chips,
  kb chip, "Open on desk"); a "How it connects" `<details>` footer carrying the
  pairing steps + the credential rule. Signal-crafted throughout (signal-card,
  zone spines, the web status palette).
- **`web/src/scripts/companion-desk.js`** — the Alpine factory: fetches
  `/api/agents` (the personas) + polls `/api/companion/status` (the device link +
  the awaiting agent sessions), with the derived `linkLabel` / `linkScope` /
  `awaiting`. No backend change — it rides the existing API.
- The old static docs hero + capability-card sections were removed; the
  now-unused `companion-app.js` is left untouched (no longer referenced).

## Proof

- **`screenshots/companion-agent-desk.png`** (`scripts/screenshot_phase69_companion.py`,
  real server with 3 seeded agents + a route-mocked awaiting session): "The Agent
  Desk" with the **"1 need you"** link chip, the **Needs you** card
  ("claude-on-ledgerline — Waiting on you: which migration strategy…"), three
  real agent cards (Reviewer / Summarizer with web+kb chips / Triage with a
  github chip, each "Open on desk"), and the "How it connects" footer.
  (`agent cards: 3 | needs-you cards: 1 | link: "1 need you"`.)
- **Tests:** the companion page tests in `test_web_server.py` cover the
  `/api/companion/status` ENDPOINT (unaffected by the page rewrite); the route
  pre-flight loads `/companion` (the new Alpine app + API fetches) with **zero
  page errors**; pre-flight + density guard = **7 passed**. Build green.

## Honest scope note

This delivers the Agent Desk *surface* + the real agents + the awaiting-link. The
deeper iPad CompanionBoard live-session interactions (select / pin / inject into
a live coder, which `/api/companion/select|pin|dismiss` already back) are a
follow-up — surfaced, not silently dropped.
