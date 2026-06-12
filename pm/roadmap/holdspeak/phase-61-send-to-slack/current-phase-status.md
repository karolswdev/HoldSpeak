# Phase 61 — Send to Slack

**Status:** in progress (1/4). Opened 2026-06-11 on owner direction: candidate
**L** scoped to one easy connector ("Export Connectors are fine…, but let's
just choose an easy one"); the pick is the Slack **incoming webhook** (one
POST, no OAuth) because Phase 38's gated webhook connector was built for
exactly it. In the same direction, **N (Windows) was rejected by the owner**
("Absolutely not. Not by me. If someone wants it, they will port it.") and
is recorded as community-port-welcome, not roadmap work.

**Last updated:** 2026-06-11 (**HS-61-01 done:** the engine + route + the
execute leg. `slack_export.py` builds the exact message (mrkdwn, visible
truncation cap), the export route records a wire-safe proposal whose preview
is byte-equal to the stored body, and — a ground-truth find — the repo had NO
production execute path at all, so the decision route now executes approved
`slack` proposals through the full `ActuatorExecutor` guard stack (other
targets unchanged, locked). The credential rule is structural: the URL never
enters the payload; the connector joins it in memory at execution time, so
`GET .../proposals` cannot leak it by construction. One shared URL rule
(https with a host; loopback http only, for the real-receiver closeout)
enforced at config AND settings. +39 tests; suite **2762 passed, 17
skipped**. Earlier: scaffolded — seams verified: the Phase-38
`build_webhook_connector` is host-gated `network:outbound` and documents
Slack incoming webhooks as its target case; the Phase-49 file-issue route is
the proposal-creation template; Phase-56's Qlippy decision/result cards ride
the `actuator_proposed`/`actuator_result` broadcasts for free.)

## The thesis — why this phase

The meeting loop closes locally (digest, follow-up draft) but the results
only leave by clipboard. One outbound door — Send to Slack — makes the
aftercare shareable where teams actually look, without inventing anything:
the approval flow, the gated connector, and the ambient approval card all
exist. The pitch stays honest: nothing is sent without a per-action
approval, and the preview IS the message.

## Goal

A "Send to Slack" action on the meeting digest and the follow-up draft:
configured by one webhook URL (default empty = invisible), every send a
proposal whose preview is the exact message, approved like any actuator,
POSTed by the host-gated connector. Off by default; byte-identical when
unconfigured.

## Scope

- **In:** the message builder + export route + connector registration +
  config (HS-61-01); the aftercare buttons + the settings field
  (HS-61-02); docs (HS-61-03); the real-POST closeout (HS-61-04).
- **Out:** Notion / Google Docs (parked); Slack OAuth/rich blocks/threads;
  per-artifact export (digest + follow-up only, v1); auto-send anything.

## Exit criteria (evidence required)

- The route records a wire-safe proposal whose preview equals the exact
  message text; unconfigured → 400 + invisible UI; the connector refuses
  any host but the configured URL's (before egress); never-egress-
  unapproved locked. (HS-61-01)
- The aftercare surfaces gain the buttons (configured-only); settings
  field with honest copy; screenshots; build clean. (HS-61-02)
- Docs canon-clean; the SECURITY egress row; the POSITIONING row.
  (HS-61-03)
- Live: real approval → a REAL POST to a real local receiver, body
  byte-equal to the preview; the off-proof. Full suite; final-summary;
  BACKLOG L flipped; PR merged on green. (HS-61-04)

## Invariants

- **Executed == previewed; nothing egresses unapproved** (Phase 37,
  untouched).
- **The webhook URL is treated as a credential**: never in previews,
  broadcasts, or responses.
- **Unconfigured is byte-identical** (no buttons, 400 on the route).

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-61-01 | The export engine + route | done | none |
| HS-61-02 | The surfaces | backlog | HS-61-01 |
| HS-61-03 | Docs: Send to Slack | backlog | HS-61-02 |
| HS-61-04 | Closeout: the real POST + final-summary + PR | backlog | HS-61-01..03 |

## Where we are

HS-61-01 is done: the whole Python side works end to end (propose → approve
→ the real gated POST), proven against the full connector stack with only
the transport faked. Next is **HS-61-02 — the surfaces** (the aftercare
buttons, configured-only, + the settings field).
