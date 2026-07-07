# HSM-25-02 — Consent + the serving surface

- **Status:** done (2026-07-07) — toggle + serving surface, sim-proven against the REAL hub (doctor read "iPad: live (2s ago)"). Evidence: [evidence-story-02.md](./evidence-story-02.md).
- **Depends on:** HSM-25-01
- **Unblocks:** HSM-25-03

## Problem

No node serves the mesh implicitly (the HS-85 consent rule). The worker
from 25-01 needs its one honest switch — off by default — and serving
must be visible while it happens, not a silent battery drain.

## The design

- **The toggle**: a Settings card in the "WHERE INTELLIGENCE RUNS"
  section, the `diarizeCard` pattern (`AppSettings.swift:451`): glyph +
  "Serve my models to the mesh" + a `Toggle` bound to a new persisted
  `InferenceConfigStore.meshServeOn` (UserDefaults, **default false**).
- **Start/stop**: toggle on → `MeshServeWorker` starts (the
  `QueuePresence.startMeshPolling` task-loop pattern), serving as the
  device's mesh name — the SAME name the model manifest pushes on sync.
  Toggle off, scenePhase leaving `.active`, or app kill → the worker
  cancels; the hub's liveness window reads the node offline within
  seconds (nothing to clean up hub-side — polling IS liveness).
- **The recursion guard at the door**: with a meshNode/desktop active
  profile the toggle refuses to arm and says why in the card's subline —
  the same named reason as the per-job guard.
- **The serving state, no prose**: while on, the card's subline states
  `serving as <node> · <n> runs` and the last-claim age; while off, the
  single label. The egress grammar for a served run is the hub's concern
  (the caller's badge names this node); the device shows only its own
  serving state.

## Scope

- In: the toggle + persisted flag, worker lifecycle wiring
  (MeetingCaptureApp scenePhase), the serving state line, the at-the-door
  guard.
- Out: notifications, background serving, any hub-side change.

## Test plan

- `swift test`: the store persists `meshServeOn` (default false); the
  guard refuses arming for meshNode/desktop actives; worker start/stop
  follows the flag (injected worker spy).
- Sim: toggle renders in Settings; on → serving line appears; off →
  gone. Screenshot committed.

## Done when

Flipping one switch starts serving under the device's mesh name and
stopping is instant and honest — verified in the simulator, wired for
25-03's live proof.
