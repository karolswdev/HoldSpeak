# HS-88-03 — The ambient dw observer: the local rail journal

- **Project:** holdspeak
- **Phase:** 88
- **Status:** backlog
- **Depends on:** HS-88-01
- **Unblocks:** HS-88-04, HS-88-05
- **Owner:** unassigned

## Problem

The owner wants "the local model to keep a note of everything
happening with dw in the background." The rails already emit events
(story flips, gate refusals, evidence captures, phase closes) onto the
one bus and through `dw events`. An ambient observer turns that stream
into a running journal a human can open, rope, and ground in turn —
running on a local model, read-only, off by default.

## Scope

- In: a hub-side observer (a bounded loop / small runtime component)
  that consumes `scope:"belt"`/`scope:"coder"` frames + a bounded
  `dw events` tail, batches them, and summarizes each batch on a
  RuntimeProfile-resolved model (`asyncio.to_thread`, the Phase-85
  rule) into a journal primitive (a note tagged `rails-journal`, the
  deferred-decision default); a config flag `rails_observer.enabled`
  (default OFF); the journal openable + groundable (HS-88-01 grounds
  it like any object); a `GET /api/rails/journal` read; anything the
  observer wants to DO is an actuator PROPOSAL, never a direct write.
- Out: cross-machine events (04); the picker (02); the observer
  editing rails files; any autonomous flip/issue (proposal-only).

## Acceptance criteria

- [ ] With the flag OFF (default), the observer runs NOTHING — no
      loop, no model call, no journal — asserted in a test.
- [ ] With the flag ON, a real rail-event batch (a story flip + a gate
      refusal on the bus) becomes a journal entry summarized by the
      configured RuntimeProfile model; the entry names the events it
      saw (receipts, not invention).
- [ ] The journal is a desk primitive: it opens in a pull-out, files
      into a zone, and can itself be grounded into a run (the
      filed-objects-stay-openable rule).
- [ ] The observer never writes to the rails: a test proves that a
      "recommended flip" it surfaces is an actuator PROPOSAL through
      the existing flow, off by default, human-approved.
- [ ] The model call runs off the event loop (`to_thread`); with the
      model unreachable the observer degrades to a typed, event-only
      journal entry (no fabricated summary), never a hang.
- [ ] Full suite green (read from the file); api-surface regen.

## Test plan

- Unit: the flag gate (off = inert), the batch→summary path with a
  fake model + fake events, the proposal-not-write invariant, the
  model-unreachable degrade.
- Integration: the observer ON against a real `dw events` tail on THIS
  repo, journaling a real flip (captured), on a real RuntimeProfile.
- Manual / device: flip a real story; watch the journal entry appear.

## Implementation direction

- **The seam:** mirror the Phase-87 `_coder_frames_loop` shape — a
  hub background task, gated by the config flag, that subscribes to
  the existing frames and tails `dw events` (bounded, via the
  injectable runner). Do NOT invent a second event source.
- **The model:** resolve the summarizer through the RuntimeProfile the
  owner names (`rails_observer.profile_id`); reuse the existing
  capability-run/relay seam so on-device, endpoint, and mesh all work;
  `to_thread` the call (the Phase-85 deadlock lesson).
- **The journal:** a note primitive tagged `rails-journal`, one entry
  per batch, body naming the events + the model's summary + a
  provenance line; `db.notes.upsert` (no new store). It grounds via
  HS-88-01's note path (already a grounding kind).
- **The consent posture:** the observer READS and summarizes; a
  suggested action is `db.actuators.record_proposal` (off by default,
  the desk-origin posture), never a direct rail write — the standing
  actuator rule.
- **SECURITY.md:** add a row — the observer reads your own `dw` and
  runs a local model; the journal is local; nothing new egresses.
