# HSM-10-02 — Transport targets

- **Project:** holdspeak-mobile
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HSM-10-01
- **Unblocks:** HSM-10-04
- **Owner:** unassigned

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

- [ ] Change-sets push and pull between the phone and a desktop/homelab endpoint
      over a Tailscale network.
- [ ] Offline is tolerated: with no peer reachable the app fully works and sync
      resumes when a peer returns (sync is never on the capture/review path).
- [ ] The transport is one implementation of `ISyncProvider`; swapping it would
      not touch the Runtime Core.
- [ ] Sync egress is represented honestly (local + LAN target) per the egress-badge
      convention where surfaced.

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
