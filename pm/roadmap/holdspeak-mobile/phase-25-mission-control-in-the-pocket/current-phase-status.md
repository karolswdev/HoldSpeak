# Phase 25 — Mission control in the pocket (the iOS conveyor)

**Status:** OPEN — 3/4.

**Last updated:** 2026-07-04 (HSM-25-03 done, 3/4: the event
ticker gains `formatMCEvent` (Contracts) so `gate_refusal` carries
its rule id verbatim, closing the one gap 25-02 left open; `swift
test` 484/0. The backend counterpart, HoldSpeak PR #247, merged
2026-07-05 — HSM-25-04's on-device leg is now unblocked pending a
hub actually running the merged `/api/missioncontrol/*` routes.)

## Why this phase exists

The backend grew a mission-control substrate (its Phase 82, PR #247):
three read-only endpoints relaying the Delivery Workbench feed,
correlation, and event log. The web Desk renders them as a belt.
Phase 82 scoped the iOS leg OUT and recorded it as a documented
compatibility note — this phase is that note paid off.

Nothing new is invented at the boundary: the JSON shapes are
frozen (`feed_schema` 1, `sessions_schema` 1), the HTTP client
already carries the owner Bearer token on every request, the poll
loop and the "unreachable is a rendered state" discipline already
exist (the coder-session poll). The conveyor is the Agent Desk's
bigger sibling and sits beside it.

## The load-bearing design call

**The contract crosses the language boundary first, golden-pinned.**
Like every mobile phase, story 01 lands the Codable wire types in
`Sources/Contracts` and proves them against literal backend JSON in
`swift test` — that test IS the drift guard against the FastAPI
shapes. The view, the live layer, and the on-device proof stack on
a contract that is already trustworthy.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HSM-25-01 | The mission-control wire contract + the client extension — **leads** | **done** ([evidence](./evidence-story-01.md): swift test 473/0, +8) | none |
| HSM-25-02 | The conveyor renders: phases as the belt, stories as the items | **done** ([evidence](./evidence-story-02.md): swift test 480/0, +7) | HSM-25-01 |
| HSM-25-03 | Sessions and events ride the belt | **done** ([evidence](./evidence-story-03.md): swift test 484/0, +4) | HSM-25-01, HSM-25-02 |
| HSM-25-04 | The pocket, proven on device | blocked | HSM-25-02, HSM-25-03 (backend PR #247 merged 2026-07-05 — unblocked pending a hub build)

## Where we are

Opened. Scope notes kept honest: the on-device proof (25-04)
depends on the backend's PR #247 being merged and a hub running the
`/api/missioncontrol/*` routes; until then 01–03 land against
frozen fixtures (the same split the backend's Phase 82 carried).
Owner-only auth is already the client's posture; a missing or
non-owner token renders as an honest "pair with the owner token"
state, not a thrown error.
