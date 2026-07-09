# HSU-1-03 — The scenario contract + the feature ledger

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-02
- **Owner:** unassigned

## Problem

The scenario is the unit of UAT, and it needs a contract: what world
to stage (deck + seeds + nodes), what to tell the human to do, what
they should expect, and what verdict to collect. Just as important:
scenarios must cite *which shipped feature they cover*, against an
enumerated ledger of everything the 90 phases actually delivered — the
owner's standing point: **we have git; coverage is derived from the
record, not remembered.** Without the ledger, a green sitting proves
only that we tested what we happened to think of.

## Scope

- In:
  - **The scenario contract** — `uat/scenarios/<pack>/<nn>-<slug>.yaml`:
    `id`, `title`, `features: [ledger keys]`, `deck`, `seeds`,
    `nodes`, ordered `steps` (each: `do` — the instruction to the
    human, `expect` — the honest pass bar, optional `where` — the
    product route/surface to open), optional `mid_run` actions the
    conductor performs between steps (restart with another deck, kill
    a node — the HSU-1-01/02 verbs), and `teardown`. Loader +
    validation with named, greppable errors.
  - **The feature ledger** — `uat/features.yaml`: the shipped surface
    enumerated as stable keys (e.g. `dictation.pipeline`,
    `meetings.import.transcript`, `desk.steering.arm`,
    `mesh.relay`, …), each entry naming the holdspeak phase(s) that
    shipped it. Built by walking `pm/roadmap/holdspeak/README.md`'s
    phase index (with git history as the tiebreaker for what survived
    later phases), reviewed by hand — the derivation script
    (`uat/tools/build_ledger.py`) proposes, the committed YAML is
    canon. Retired features are marked `retired`, not deleted.
  - **Coverage math** — given a pack (or a finished sitting), compute
    features covered / total live features; exposed via the conductor
    API for HSU-1-04/05 to render.
  - **The smoke pack** — `uat/scenarios/smoke/`: 6–8 scenarios proving
    the rig's whole vocabulary: a dictation-surface walk on
    `golden-local`, a meeting round-trip on a seeded imported meeting,
    a desk walk over seeded primitives, one `bad-endpoint` honest-
    failure scenario, one `no-model` first-run-truth scenario, one
    mesh-node scenario with a mid-run node kill.
- Out: rendering (HSU-1-04), verdict storage semantics (HSU-1-04),
  full-coverage pack authorship (Phase 2 — the ledger will make the
  gap list explicit).

## Acceptance criteria

- [ ] The contract is schema-validated; a malformed scenario fails
      load with a named error naming the file and field.
- [ ] Every scenario must cite ≥1 ledger key that exists; an unknown
      key fails validation.
- [ ] `uat/features.yaml` exists with every holdspeak phase (0–90)
      mapped to at least one ledger entry or an explicit
      `internal/no-uat-surface` marker — no phase silently absent.
- [ ] Coverage math is exact and tested (covered, uncovered, retired
      excluded).
- [ ] The smoke pack loads clean, cites real ledger keys, and
      exercises: both golden decks' postures, both bad decks, seeding,
      and one mid-run conductor action.
- [ ] Tests green under `uv run pytest -q tests/uat/`.

## Test plan

- Unit: schema validation (positive + negative fixtures), ledger
  integrity (keys unique, phases exhaustive), coverage math.
- Integration: load the smoke pack end to end; dry-run a scenario's
  staging (deck applied, seeds applied, nodes up) without a human.
- Manual / device: the pack is *sat through* in HSU-1-06.

## Notes / open questions

- `expect` lines are written against POSITIONING canon voice: honest
  pass bars ("the badge reads local", "doctor names the dead
  endpoint"), never marketing.
- The ledger doubles as the Phase-2 work generator: uncovered keys ARE
  the scenario backlog.
