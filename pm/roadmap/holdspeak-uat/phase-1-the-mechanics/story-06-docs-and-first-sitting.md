# HSU-1-06 — Docs + the first sitting

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-05
- **Owner:** unassigned

## Problem

The rig is only real once a human has sat through it — the exact
failure mode this project exists to prevent is a beautiful harness
nobody runs (Phase 67's `PROTOCOL.md`). This story writes the docs
that make the rig operable without this conversation in context, then
closes the phase the only honest way: the owner runs the smoke pack
live on this Mac, end to end, and the first findings get triaged
through the real protocol.

## Scope

- In:
  - **`uat/README.md`** — the operator doc: one-command start
    (`uv run python -m uat.conductor`), the port map (conductor 8799 /
    product-under-test 8788 / real hub 8765 untouched), how a sitting
    flows, where runs/debriefs land, prerequisites per deck (which
    need `.43`, which are fully local).
  - **`uat/AUTHORING.md`** — how to add a scenario, a deck, a seed
    manifest; the ledger-key rule; the honest-`expect` voice rule;
    how to run contract validation.
  - **Dogfood supersession** — `dogfood/PROTOCOL.md` gains a header
    pointing here as the way UAT is now run; dogfood assets the
    conductor reuses stay put and documented; anything the absorption
    made dead is deleted, not left to rot.
  - **The first sitting** — the owner runs the smoke pack live:
    staging on `golden-43`, the walkthrough on real surfaces
    **including the three-surface scenario sat on web, iPad, and
    iPhone** (at least one verdict cast from a device's own browser
    over LAN), the `bad-endpoint` and `no-model` scenarios failing
    honestly, the mid-run node kill observed, the debrief generated
    with its per-surface scores, and the joint triage held — at least
    one finding dispositioned, and any `fix` landed in
    `pm/roadmap/holdspeak/BACKLOG.md` through the gate.
  - Evidence: the sitting's debrief packet + walkthrough screenshots
    copied into this phase's evidence assets.
- Out: fixing any product bug the sitting finds (findings feed
  BACKLOG; fixes are holdspeak phases), Phase-2 scaffolding (the
  ledger's uncovered keys are its input, recorded in the final
  summary).

## Acceptance criteria

- [ ] Both docs exist and are sufficient: a cold reader can start the
      conductor, run a sitting, and author a scenario without reading
      harness source.
- [ ] `dogfood/PROTOCOL.md` points here; no dead absorbed files
      remain.
- [ ] The sitting happened on real metal: a completed smoke-pack run
      in the run DB with a generated debrief, every scenario visited,
      the three-surface scenario carrying verdicts on all three
      surfaces with ≥1 cast from a device, real verdicts (a sitting
      of ten PASSes cast in ten seconds is not a sitting — timestamps
      are part of the evidence).
- [ ] The triage ritual was held per `uat/TRIAGE.md`; ≥1 finding
      dispositioned; any `fix` visible in
      `pm/roadmap/holdspeak/BACKLOG.md`.
- [ ] Phase exit criteria in `current-phase-status.md` all check;
      final summary written with the Phase-2 handoff (uncovered ledger
      keys as the scenario backlog).

## Test plan

- Unit: n/a — docs + the live proof.
- Integration: full suite green
  (`uv run pytest -q` excluding `tests/e2e/test_metal.py`).
- Manual / device: the sitting itself — owner-gated, on this Mac, with
  `.43` up for the `golden-43` deck.

## Notes / open questions

- The sitting is the phase's closing gate and cannot be delegated to
  an agent or a simulator — that is the point of the project.
- Keep the smoke sitting short (~30–40 min) so it actually happens;
  depth belongs to Phase 2's coverage pack.
