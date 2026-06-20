# HSM-12-01 — Desktop client seam + pairing

- **Project:** holdspeak-mobile
- **Phase:** 12
- **Status:** backlog
- **Depends on:** HSM-0-04 (contracts), HSM-1-01 (SPM layout), HSM-10-02 (transport posture to reuse)
- **Unblocks:** HSM-12-02, HSM-12-03, HSM-13-01
- **Owner:** unassigned

## Problem

The iPad cannot act as a companion until it can point at, reach, and trust a
desktop/homelab server — the same server your tmux + hooks coding session points
at. That connection must be a clean Runtime-Core seam (so views and business logic
never hold a raw HTTP client), and it must be offline-tolerant: the iPad's own
on-device runtime can never stall because a server is unreachable. This is the
spine the whole track hangs off.

## Scope

- **In:** an `IDesktopClient` abstraction (Layer 3) the Runtime Core depends on;
  configuration of a desktop peer (host/port + token over the user's own LAN /
  Tailscale, reusing the Phase-10 transport posture — direct to the peer, no
  third-party relay); a handshake/health check against the desktop's `/health` +
  `/api/runtime/status`; an honest egress descriptor for the connection (positioning
  canon: one badge, never a privacy novel); offline tolerance (every call fails
  soft and never blocks the on-device path).
- **Out:** the meeting/dictation/companion calls themselves (HSM-12-02, Phase 13).
  The shell/UI (HSM-12-03). Any on-device feature change (the local runtime is
  untouched). Discovery/Bonjour (parked; manual host:port + token first).

## Acceptance criteria

- [ ] `IDesktopClient` exists; the Runtime Core depends on the interface, and a
      fake client drives the connection flow in tests (no concrete HTTP in the
      core's callers).
- [ ] The iPad can be configured with a desktop peer (host/port + token) and a
      handshake succeeds against a server presenting `/health` + `/api/runtime/status`,
      surfacing reachable/unreachable + runtime readiness.
- [ ] The connection carries an honest egress descriptor (e.g. `local + LAN →
      <host>`); no privacy-novel prose.
- [ ] Every client call is offline-tolerant: when the peer is down the call fails
      soft (no throw on the capture/UI path), and a test proves the on-device flow
      is unaffected by an unreachable peer.

## Test plan

- Unit: drive the connect/handshake/health flow against a fake desktop (reachable,
  unreachable, not-ready) → correct state transitions; egress descriptor correct;
  unreachable peer never throws on the caller path.
- Unit: a Runtime-Core flow that uses the on-device runtime while the desktop is
  unreachable completes unaffected (the "not blocked by the server" guarantee).
- Manual / device: deferred to HSM-12-04 (real desktop on the LAN).

## Notes / open questions

- Reuse the Phase-10 `HTTPSyncProvider`/`SyncQueue` posture for transport hygiene
  (direct to the peer, honest egress, never-throw-when-down) — but this is the
  *live* client, distinct from the store-reconciling sync provider; do not conflate
  the two seams.
- The token is a credential: join it at call time, never log it, never put it in a
  payload echoed back to the UI (mirror the Phase-61 Slack-URL discipline).
- Keep the seam minimal here — just connect/health/egress. The verb methods (list
  meetings, start meeting, post dictation) are added by the stories that need them.
