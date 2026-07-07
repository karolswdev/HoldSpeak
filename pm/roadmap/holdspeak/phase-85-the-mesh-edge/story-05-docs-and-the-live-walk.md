# HS-85-05 — Docs + the live walk

- **Project:** holdspeak
- **Phase:** 85
- **Status:** done (2026-07-07 — all six beats proven live on the real hub; see [evidence](./evidence-story-05.md))
- **Depends on:** HS-85-01, HS-85-02, HS-85-03, HS-85-04
- **Unblocks:** none (closes the phase)
- **Owner:** unassigned

## Problem

The phase's claim — the request moves, the model and the key don't — has to
be proven with a real second process doing the work, and taught honestly
(including what a relay job row contains and when a node is simply not
there). Then the phase closes with the standing cadence.

## Scope

- In: docs — MODELS.md's "Runtime profiles" section grows the mesh-edge
  paragraphs (what serves, what moves, what never moves, liveness); a
  `holdspeak mesh serve` reference in the guides' natural homes; voice/
  drift guards green.
- In: the live walk (`scripts/walk_hs85_live.py`, staying as the
  regression rig), on the REAL hub with the worker as a second local
  process wearing its own node name:
  1. `holdspeak mesh serve` starts; doctor/setup-status show the edge live.
  2. A meshNode profile authored once (the editor), pointing at that node.
  3. An agent chat runs from the desk — the badge reads `Mesh · <node>`,
     and the WORKER's log line proves execution happened in that process.
  4. A meeting-intel run through the same profile (the Phase-84 picker)
     executes on the node.
  5. The worker is killed: the picker/models door show offline; a forced
     run refuses fast, naming the node — timed, inside the deadline.
  6. Cleanup: assignments restored, walk profile removed.
  Screenshots committed; every beat asserted.
- In: phase close — exit criteria re-run, `final-summary.md`, BACKLOG row
  T → shipped, roadmap README pointer + index row; the HSM follow-up (the
  Apple worker + consent toggle on this proven wire) recorded as the
  explicit handoff.
- Out: multi-machine walking (two local processes prove the wire; the
  second physical machine changes nothing about the code paths), Apple
  work.

## Acceptance criteria

- [ ] The walk passes end to end with the six beats asserted; the worker
  log captured in evidence proving where execution happened.
- [ ] The offline beat measured: refusal arrives named and fast (pinned:
  < 5s from ask to error), never a hang.
- [ ] Docs guards green; touched guides read product-tense.
- [ ] BACKLOG row T, roadmap README, phase status, final-summary updated
  in the closing commit(s).
- [ ] Full suite green: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Test plan

- Unit: the docs guards.
- Integration: the full suite command above.
- Manual / device: the live walk IS the proof (run outside the sandbox —
  LAN + subprocess rules; pin `HOLDSPEAK_WEB_PORT=8765` on any hub
  restart, per the Phase-84 ops note).

## Notes / open questions

- The walk's worker should carry a distinct node name (e.g. "walk-edge")
  so the badges and doctor lines are unambiguous in screenshots.
- If the owner wants the *phone* serving before the HSM follow-up lands,
  that is that track's first story on this wire — record interest, don't
  smuggle Swift here.
