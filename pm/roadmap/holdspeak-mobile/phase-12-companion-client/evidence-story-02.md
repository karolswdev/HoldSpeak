# Evidence — HSM-12-02 (Meetings remote control)

**Date:** 2026-06-20
**Story:** [story-02-meetings-remote-control.md](./story-02-meetings-remote-control.md)
**Result:** DONE (core remote-control) — host-proven, no device. From the
phone/iPad the companion can **list the server's meetings** and **start / stop** a
meeting on the desktop, reflecting the **live runtime state** — all over the
desktop's existing API, through the `IDesktopClient` seam. `swift test`
**105 passed / 6 skipped / 0 failed** (+9 this story).

## What shipped

- **Seam (Providers, `IDesktopClient`):** `listMeetings()`, `runtimeState()`,
  `startMeeting(title:)`, `stopMeeting()` — the verbs throw on an erroring peer so
  the view-model can render unreachable. New decode types `MeetingSummary` (loose;
  only `id` required) + `RuntimeState`.
- **`HTTPDesktopClient`:** the four verbs over the real endpoints — `GET
  /api/meetings` (decoded to the server's exact shape: `id`/`title`/`started_at`/
  `ended_at`/`duration_seconds`/`segment_count`/`action_item_count`/`intel_status`),
  `GET /api/runtime/status`, `POST /api/meeting/start`, `POST /api/meeting/stop`.
  start/stop POST then read back `runtime/status` so the caller reflects what
  actually happened. Generalized the request helper for POST + JSON body; Bearer
  token still joined at call time.
- **View-model (RuntimeCore, `CompanionMeetings`):** list / live / start / stop, each
  returning a `Result` so an unreachable desktop is a rendered `.failure`, never a
  throw on the caller path (the "not a dumb terminal" degradation guarantee).

## Acceptance criteria → proof

- **List the server's meetings, decoded to the shared shape.**
  `DesktopClientTests.testListMeetingsDecodesServerShape` (two meetings, second with
  fields absent) + `CompanionMeetingsTests.testListsMeetings`. ✅
- **Start and stop a meeting from the device; live state reflected.**
  `testStartMeetingPostsThenReflectsLiveState` (POST then status read-back → active),
  `testStopMeetingPostsThenReflectsIdle`, `testRuntimeStateDecodesActiveMeeting`;
  `CompanionMeetingsTests.testStartReflectsLiveState` / `testStopReflectsIdle`. ✅
- **All through `IDesktopClient`; a fake desktop drives it; no concrete HTTP in the
  view layer.** `CompanionMeetings` depends only on the seam; the fake drives every
  flow. ✅
- **Unreachable handled gracefully (no crash/stall).**
  `testUnreachableDegradesToFailureResult` (every verb → `.failure`, no throw) +
  `testListMeetingsHTTPErrorThrows` (non-2xx → `DesktopClientError.http`). ✅

## Commands

```
$ swift build           → Build complete!
$ swift test            → Executed 105 tests, 6 skipped, 0 failures
```

## Scope note

Per-meeting **detail + full artifact rendering** (the AC's "open one") rides
**HSM-12-03** with the SwiftUI shell: the list already carries the summary fields
(counts, intel_status), and the artifact wire-shape → contract-`Artifact` decode is
best decided where the UI renders it. The remote-control verbs the owner named
("list of meetings, start meeting") are complete and tested here.
