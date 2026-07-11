# HSU-3-01 — Mesh dispatch: the handoff arc

- **Project:** holdspeak-uat
- **Phase:** 3
- **Status:** done
- **Depends on:** none (rides the shipped `mesh-node-alive` recipe)
- **Owner:** unassigned

## Problem

Pack E authors the mesh edge's headline claim — a run *moves onto* the worker
and returns badged (`author-on-iPad → run-on-hub → read-on-web`) — but the beats
that drive a real ask onto the node and read the `⇄ mesh` badge are
`n/a`/human-eyeball, because the induction engine can spawn a worker and read its
liveness (shipped) but cannot **dispatch a run onto it and verify the return**.
The re-eval ranks this the core of Pack E (`PROTOCOL-COVERAGE.md` §3.3).

## Scope

- In:
  - A recipe action verb `dispatch_run` (a.k.a. `ask_on_profile`): POST the
    product's own `/api/ask` (or the dictation-remote route) with the
    `uat-worker` meshNode profile, so the hub relays the run to the worker.
  - A probe `run_returned_badged`: the response carries the `⇄ mesh` egress
    scope / node badge; and a provenance probe reading the worker log (claimed
    the job) vs the hub (no model load) — the "the run moved, the model didn't"
    proof.
  - A recipe `mesh-run-on-worker` composing `mesh-node-alive` + the dispatch +
    the badge/provenance probe.
  - Flip pack-e-mesh-edge `02`/`03`/`06` from human-walked to staged-and-verified
    where the arc is machine-checkable.
- Out: cross-machine (remote) dispatch (a later story); the iPad *authoring* leg
  (device-gated, HSU-3-05); any product change.

## Acceptance criteria

- [x] `dispatch_run` drives a real ask onto `uat-worker` and the response reads
      badged `⇄ mesh` (not a local run). — `run_returned_badged` asserts
      `egress.scope == mesh`, `host == uat-worker`; green live on `.43`.
- [x] The provenance probe shows the worker claimed the job and the hub loaded no
      model (worker-completion delta before→after). — `run_claimed_by_worker`
      reads the worker's own CLAIM-marker delta (`node_log_text`, the shared
      `holdspeak.log`) and the hub's `provider == mesh`; "the run moved, the
      model didn't."
- [x] `mesh-run-on-worker` applies + verifies on `.43`, and tears the worker down
      cleanly (no orphan process). — `test_run_dispatched_onto_the_worker_returns_badged`
      applies the recipe, verifies all three probes, then `teardown` and asserts
      the run is not up (10 passed, 52.86s — see `evidence-story-01.md`).
- [x] The unblocked pack-e beats cite the recipe and carry real verdicts; the
      `.43`-gated test self-skips without the LAN. — pack-e `02`/`03`/`06` now
      cite `mesh-run-on-worker` with the treatment leg marked machine-verified;
      `test_mesh_dispatch.py` self-skips when `.43` is unreachable.

## Test plan

- Integration (`.43`-gated): boot `mesh-node`, spawn `uat-worker`, dispatch an
  ask, assert badged return + provenance, teardown.
- Manual/device: the iPad-authoring leg rides HSU-3-05.

## Notes / open questions

- Read `/api/ask` for how a profile/model override routes to the mesh relay, and
  the mesh badge shape in the response (Phase-85 `⇄ mesh` egress scope).
