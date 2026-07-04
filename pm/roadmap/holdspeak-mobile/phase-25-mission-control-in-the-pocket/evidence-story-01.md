# Evidence — HSM-25-01 — The wire contract + the client extension

**Status:** done (2026-07-04).

## The move

Two files land the mission-control contract on the iOS side:

- `apple/Sources/Contracts/MissionControl.swift` — the Codable wire
  types mirroring the backend's frozen shapes (`feed_schema` 1,
  `sessions_schema` 1): `MCStatePayload`/`MCRepoState`/`MCFeed`/
  `MCProject`/`MCPhase`/`MCStory`, `MCSessionsPayload`/
  `MCSessionsDoc`/`MCSession`, `MCEventsPayload`/`MCEvent`.
  snake_case decodes through the shared `.convertFromSnakeCase`
  decoder; a non-`live` repo carries no `feed` (optional); event
  `detail` is `[String: JSONValue]` so a new key never breaks decode.
- `apple/Sources/Providers/Desktop/HTTPDesktopClient+MissionControl.swift`
  — three GET methods, the `+Activity` idiom, joining the owner
  Bearer token off `config` at call time (never logged). A non-2xx
  throws `DesktopClientError.http`.

## Proof

`cd apple && swift test` (host-hermetic, no simulator):

```text
swift build → Build complete! (48.23s)

MissionControlClientTests — Executed 8 tests, 0 failures:
  testStateDecodesTheLiveFeed
  testStateCompatibilityHasNoFeed
  testSessionsDecodeCorrelation
  testSessionsUnavailableDecodesWithoutDoc
  testEventsDecodeWithFreeFormDetail
  testOwnerTokenRidesEveryRequest
  testNoTokenSendsNoAuthHeader
  testOwnerOnlyRejectionThrowsHTTP

Full suite — Executed 473 tests, with 9 skipped and 0 failures
```

The eight new tests decode literal backend JSON (the exact
`/api/missioncontrol/*` shapes), so the suite doubles as the drift
guard against the FastAPI contract: if the server shape moves, these
fail. The owner Bearer rides every request and is absent when there
is no token; a 403 throws so the conveyor can render an owner-only
auth state rather than crash. The full 473-test package suite is
green, so the additions regressed nothing.
