# HS-88-04 — Reach: rail events from another machine (scoped)

- **Project:** holdspeak
- **Phase:** 88
- **Status:** backlog
- **Depends on:** HS-88-03
- **Unblocks:** HS-88-05
- **Owner:** unassigned

## Problem

The owner's phrase: "happening on another computer, for example." The
observer journals the local rails; a repo whose `dw` lives on another
machine should reach the journal too — over the proven mesh relay,
with the same honest liveness. This is the ONE reach story; it is
scoped deliberately narrow so the wire is proven, not sprawled.

## Scope

- In: the far node's mesh worker (the Phase-85 pull worker) tails its
  OWN `dw events` and pushes rail-event ENVELOPES to the hub over the
  existing relay; the observer (HS-88-03) merges remote envelopes into
  the journal, each entry NAMING its origin node; honest liveness (a
  node gone quiet reads stale, its events stop, never fabricated);
  off by default, per node.
- Out: remote GROUNDING of a far repo's story files (the reach here is
  EVENTS, not file hydration — hydrating a remote file is a later
  phase); steering a remote session (Phase-87 deferred); more than the
  one-remote proof.

## Acceptance criteria

- [ ] A remote node's `dw events` reach the local journal as envelopes
      over the mesh relay, each journal entry naming the origin node
      (a receipt, not a claim).
- [ ] Honest liveness: when the remote node goes quiet, its stream
      reads stale and STOPS; the observer never invents a remote event
      (the Phase-85 liveness rule, reused).
- [ ] The remote leg is off by default and per-node; with no remote
      configured the observer is exactly HS-88-03 (a test pins the
      no-regression).
- [ ] The envelope carries EVENTS only — no repo file contents cross
      the wire (the reach is deliberately events-only); a test asserts
      the envelope shape.
- [ ] Full suite green (read from the file).

## Test plan

- Unit: the envelope shape + the origin-naming, the liveness stale/stop
  path, the off-by-default no-regression, the events-only invariant —
  all with a fake relay + fake remote worker.
- Integration: a second local process (`holdspeak mesh serve`, the
  Phase-85 walk pattern) tailing its own `dw events` and pushing to
  the hub; a real flip on the "remote" reaching the journal (captured).
- Manual / device: two rails machines if available; else the
  two-process local proof (the Phase-85 precedent).

## Implementation direction

- **The precedent:** this is the coder-queue/mesh-worker PULL pattern
  inverted to a PUSH of events — the worker tails `dw events` (bounded,
  injectable runner) and enqueues envelopes on the SAME relay
  `intel/mesh_relay.py` uses; do NOT open a second transport.
- **The envelope:** `{node, ts, events: [<dw event dicts>]}` — events
  only, no file bodies; the observer folds them into the journal with
  the node named in the provenance line.
- **Liveness:** reuse `db.mesh_relay.worker_last_seen` + the
  `DEFAULT_LIVENESS_WINDOW_SECONDS` posture; a stale node's stream
  stops and reads stale, never fabricated.
- **Scope discipline:** if the relay-of-events wire proves heavier
  than the story budget, ship the local-two-process proof and record
  the real cross-machine relay as a deferred rider — the phase's
  reach criterion is the wire PROVEN on one remote, not a fleet.
