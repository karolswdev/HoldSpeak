# HSU-1-06 — Docs + the first sitting

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** HSU-1-05
- **Owner:** agent (docs + packs) / owner (the live sitting)

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

- [x] Both docs exist and are sufficient: `uat/README.md` (with the
      owner wake-up runbook at the top, the port map, the sitting flow,
      per-deck prerequisites, and an honest "Known state") + a cold
      reader can author a scenario/deck/seed/recipe from
      `uat/AUTHORING.md` without reading harness source.
- [x] `dogfood/PROTOCOL.md` points here as the way UAT is now run; no
      dead absorbed files remain (the substrate — `_home` recipe, mock
      repos, transcripts, `make_fixtures.py` — is reused and documented).
- [x] **Real scenario packs authored** (beyond the smoke pack, so the rig
      puts the app through its paces): **Pack D — Honest Failure & Trust**
      (6 scenarios, fully local, demos without the LAN), **Pack A —
      Meeting Aftercare** and **Pack C — Dictation Grounding** (`.43`
      web legs). All validate clean; Pack D stages locally end to end
      (`test_packs.py`).
- [ ] **OWNER-GATED — the live human sitting.** The rig is built up to
      the sitting; the sitting itself cannot be delegated to an agent or
      a simulator (that is the point of the project). Left for the owner:
      a completed pack run in the run DB with a generated debrief, the
      three-surface scenario carrying real verdicts on all three surfaces
      with ≥1 cast from a device.
- [ ] **OWNER-GATED — the joint triage** per `uat/TRIAGE.md`; ≥1 finding
      dispositioned; any `fix` landed in `pm/roadmap/holdspeak/BACKLOG.md`
      through the gate.
- [ ] **OWNER-GATED — phase close.** Phase exit criteria checked and the
      final summary written (with the Phase-2 handoff: the ledger's
      uncovered keys are Phase 3's scenario backlog) after the sitting.

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
