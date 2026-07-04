# HSM-25-01 — The mission-control wire contract + the client extension

- **Status:** done (2026-07-04) — **leads, load-bearing** (every conveyor surface decodes through it). Evidence: [evidence-story-01.md](./evidence-story-01.md). `swift test` 473/0 (+8).

## Problem

The backend grew three mission-control endpoints (its Phase 82:
`/api/missioncontrol/state|sessions|events`) relaying the frozen
Delivery Workbench documents. The iOS app has no model for them and
no client method to fetch them. Everything the conveyor renders
depends on those shapes decoding correctly, so the contract crosses
the language boundary first — golden-pinned against literal backend
JSON — the way every mobile phase leads with its contract.

## The design

- `Sources/Contracts/MissionControl.swift`: Codable structs mirroring
  the backend shapes — `MCStatePayload` / `MCRepoState` / `MCFeed` /
  `MCProject` / `MCPhase` / `MCStory`; `MCSessionsPayload` /
  `MCSessionsDoc` / `MCSession`; `MCEventsPayload` / `MCEvent`.
  snake_case decodes via the shared `.convertFromSnakeCase` decoder
  (no manual CodingKeys); a repo whose status is not `live` carries
  no `feed` (optional); event `detail` is `[String: JSONValue]` so a
  new detail key never breaks decode.
- `Sources/Providers/Desktop/HTTPDesktopClient+MissionControl.swift`:
  three GET methods on the existing client, same idiom as
  `+Activity` — self-contained request/send helpers joining the owner
  Bearer token off `config` at call time (the Phase-61 credential
  discipline; the token is never logged). A non-2xx throws
  `DesktopClientError.http` so a 401/403 becomes a rendered
  "pair with the owner token" state upstream.

## Test plan

`Tests/ProvidersTests/MissionControlClientTests.swift`, `URLProtocol`-
stubbed and offline: the live feed / correlation / events decode from
literal backend JSON (the drift guard against the FastAPI contract);
`compatibility` and `unavailable` statuses decode without a doc; the
owner Bearer rides every request and is absent when there is no
token; a 403 throws. `swift test` host-hermetic.
