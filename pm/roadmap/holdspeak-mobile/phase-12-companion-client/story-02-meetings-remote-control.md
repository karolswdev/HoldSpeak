# HSM-12-02 — Meetings remote control

- **Project:** holdspeak-mobile
- **Phase:** 12
- **Status:** backlog
- **Depends on:** HSM-12-01
- **Unblocks:** HSM-12-03, HSM-12-04
- **Owner:** unassigned

## Problem

The owner named it directly: "start meeting, list of meetings." When the iPad is
pointed at the same server you are coding against, you should be able to see the
server's meetings and start or stop one from the iPad — the remote-control half of
the companion. The desktop already serves these endpoints; this story makes the
client drive them through the seam.

## Scope

- **In:** client methods + Runtime-Core view-models over the existing desktop
  endpoints — list the server's meetings (`GET /api/meetings`, with
  `/api/meetings/facets` available for filtering), open one
  (`GET /api/meetings/{id}` + `/artifacts`), **start a meeting on the desktop**
  (`POST /api/meeting/start`), **stop it** (`POST /api/meeting/stop`), and reflect
  live runtime state (`GET /api/runtime/status`). All through `IDesktopClient`; the
  view-models expose list/detail/start/stop/live-state without UIKit.
- **Out:** the SwiftUI screens themselves (HSM-12-03 renders these view-models).
  Dictation / answering the coder (Phase 13). Meeting *import* and faceted search
  depth (desktop Phase 55 — the client reads what the server returns, it does not
  re-implement faceting). Editing/deleting server meetings from the iPad (parked).

## Acceptance criteria

- [ ] A view-model lists the server's meetings from `/api/meetings` and opens one
      (detail + artifacts) — decoded into the shared contract types, validated where
      the Phase-0 schemas overlap.
- [ ] From the iPad, `start` and `stop` a meeting on the desktop via
      `/api/meeting/start` + `/api/meeting/stop`, and the resulting live state is
      reflected from `/api/runtime/status`.
- [ ] All of it runs through `IDesktopClient`; a fake desktop drives the flow in
      tests; no concrete HTTP in the view layer or the view-models' callers.
- [ ] Unreachable/again-reachable transitions are handled gracefully (the list and
      controls show a clear unreachable state and recover; no crash, no stall).

## Test plan

- Unit: against a fake desktop, list → open → start → stop → live-state transitions
  produce the expected view-model state; payloads decode/validate; start/stop are
  driven through the seam.
- Unit: a `/api/runtime/status` poll reflects an in-progress meeting and returns to
  idle on stop.
- Manual / device: deferred to HSM-12-04 (real desktop, real meeting).

## Notes / open questions

- Live state: poll `/api/runtime/status` first (the phase default); an event/stream
  transport is a later optimization that Phase 13's companion board also wants —
  flag it, don't build it here.
- Respect the server's own state machine — the iPad requests start/stop; the
  desktop owns whether a meeting can start (mic, readiness). Surface the server's
  refusal honestly rather than second-guessing it on the client.
