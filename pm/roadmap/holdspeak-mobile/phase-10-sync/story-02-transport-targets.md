# HSM-10-02 — Transport targets

- **Project:** holdspeak-mobile
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HSM-10-01
- **Unblocks:** HSM-10-04
- **Owner:** unassigned

## Progress (2026-06-19) — the Swift transport + offline queue (PR-A)

Shipped in two PRs; this is the mobile half. The desktop **Python sync receiver**
is PR-B (`holdspeak/web/routes/sync.py`).

- `HTTPSyncProvider` (`apple/Sources/Providers/Sync/HTTPSyncProvider.swift`) — an
  `ISyncProvider` over HTTP: `push` → `POST {base}/api/sync/push`, `pull` →
  `GET {base}/api/sync/pull` (URLSession, Foundation; optional bearer; honest
  `egressLabel` "local + LAN → host"). Direct to the peer, no relay.
- `SyncQueue` (`apple/Sources/Providers/Sync/SyncQueue.swift`) — disk-backed FIFO;
  `flush(through:)` drains to a reachable peer and **leaves the queue intact +
  doesn't throw when the peer is down** (offline tolerated, resume later; sync never
  on the capture/review path).
- Proof: `swift test` **77/77** (6 opt-in skips) incl. 8 transport tests (push
  shape, pull decode, non-2xx error, egress label, FIFO order, drain-when-reachable,
  keep-when-unreachable, partial-resume).

## Problem

The sync object model needs a wire. The charter's targets are the user's own
infrastructure — HoldSpeak Desktop, a homelab, and Tailscale networks — not a
hosted cloud. The transport must move change-sets between the phone and those
peers, opportunistically and offline-tolerant.

## Scope

- **In:** a concrete `ISyncProvider` transport that reaches the desktop/homelab
  endpoint over a Tailscale network; push/pull of change-sets; offline tolerance
  (queue and resume, never block the app); the egress posture surfaced honestly
  (sync is local+LAN, shown via the egress badge where the UI touches it).
- **Out:** conflict resolution (HSM-10-03). The continuity gate (HSM-10-04). A
  third-party relay / hosted service. Auth beyond what Tailscale provides.

## Acceptance criteria

- [~] Change-sets push and pull between the phone and a desktop/homelab endpoint —
      the Swift transport (`HTTPSyncProvider`) is done + host-proven against a stub;
      the live desktop receiver is PR-B (Python sync API).
- [x] Offline is tolerated: `SyncQueue.flush` keeps the queue + never throws when
      the peer is unreachable; the app is unaffected (sync off the capture path).
- [x] The transport is one implementation of `ISyncProvider`; swapping it would not
      touch the Runtime Core.
- [x] Sync egress is represented honestly (`egressLabel` = "local + LAN → host");
      the badge wiring is the host UI's (Phases 8–9).

## Test plan

- Unit: the transport against a local stub endpoint → push/pull change-sets;
  simulate peer-unreachable → app unaffected, queue resumes.
- Manual / device: sync between a real phone and a desktop/homelab over Tailscale.

## Notes / open questions

- If the desktop product lacks a sync receiver, flag that as a `holdspeak`
  roadmap item (phase deferred decision) — the mobile side can't sync to a peer
  that can't receive.
- Direct over Tailscale, no relay (phase default) — keeps it local-first and
  dependency-light.
