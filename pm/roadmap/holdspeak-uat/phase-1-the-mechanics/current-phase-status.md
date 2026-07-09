# Phase 1 — The Mechanics

**Last updated:** 2026-07-08 (scaffolded, 0/6)

## Goal

Build the UAT rig itself — the conductor that hosts HoldSpeak on this
Mac under controlled conditions (isolated HOME per run, named config
decks good and bad, desk seeding, mesh nodes), the scenario contract
with an enumerated feature ledger, the guided website that walks a
human through a pack and captures a verdict per step, and the debrief
+ triage protocol that turns a sitting into backlog-ready findings —
proven by one real smoke-pack sitting run end to end by the owner.

## Scope

- **In:** the `uat/` harness (conductor process, run lifecycle, run
  DB), config decks, seed manifests, mesh-node spawn/kill, the
  scenario YAML contract + loader + validation, `uat/features.yaml`
  (the coverage ledger derived from the holdspeak phase index), one
  smoke pack (~6–8 scenarios incl. at least one deliberately-bad
  deck), the React+Vite guided site, the debrief packet generator,
  the joint triage protocol, harness docs, the live closing sitting.
  Absorbing the dogfood substrate (isolated `_home` recipe, fixture
  generators, mock repos, transcripts).
- **Out:** full scenario coverage of the product (Phase 2); any change
  to HoldSpeak product behavior (the harness drives the product
  through its existing CLI/config/API surface only — a product bug
  found here becomes a *finding*, not a fix in this phase); CI
  automation of sittings (a sitting is human by definition);
  packaging/publishing the harness.

## Exit criteria

- [ ] `uv run python -m uat.conductor` serves the guided site on a
      pinned local port; a run boots an isolated HoldSpeak with a
      chosen deck, health-checked, logs captured, torn down cleanly.
- [ ] At least five decks exist including two deliberately bad ones,
      and a scenario can assert the product *fails honestly* under
      them.
- [ ] A seed manifest materializes a described desk (notes, KB,
      recipes, ≥1 imported meeting) before a scenario starts.
- [ ] The scenario contract is validated by tests;
      `uat/features.yaml` enumerates the shipped surface with every
      holdspeak phase mapped; the smoke pack loads clean.
- [ ] The guided site walks a pack step by step, captures
      pass/fail/partial/skip + note + screenshot per step into the run
      DB, and survives a mid-sitting product restart.
- [ ] A finished sitting generates a debrief packet (markdown + JSON,
      coverage % included); the triage protocol doc defines the joint
      review and the BACKLOG feed format.
- [ ] The closing sitting: the owner runs the smoke pack live on this
      Mac end to end, the debrief is generated, and at least one
      finding is triaged through the protocol.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-1-01 | The conductor: hosted runs | backlog | [story-01](./story-01-the-conductor.md) | — |
| HSU-1-02 | Decks, seeds, and the mesh | backlog | [story-02](./story-02-decks-and-seeding.md) | — |
| HSU-1-03 | The scenario contract + the feature ledger | backlog | [story-03](./story-03-scenario-contract-and-coverage.md) | — |
| HSU-1-04 | The guided site | backlog | [story-04](./story-04-the-guided-site.md) | — |
| HSU-1-05 | The debrief + the triage protocol | backlog | [story-05](./story-05-the-debrief.md) | — |
| HSU-1-06 | Docs + the first sitting | backlog | [story-06](./story-06-docs-and-first-sitting.md) | — |

## Where we are

Scaffolded 2026-07-08 from the owner's direct ask: a robust UAT
harness that forces a real human sitting — a guided website with
scenario scripts and per-step feedback capture, powerful enough to
host the server, flip good/bad configurations, and seed the desk.
Decisions locked at scaffold: standalone conductor (not an in-product
route), absorb + supersede the Phase-67 dogfood harness, coverage
enumerated from the git/phase record, mechanics + one smoke pack only
(full coverage is Phase 2). Next: HSU-1-01.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The conductor grows a second product (auth, users, deploy) instead of staying a dev rig | medium | Localhost-only, no auth, run DB is a local sqlite; scope "Out" list enforced at review | Any story adding harness features no scenario needs |
| Seeding via product APIs couples the harness to route churn | medium | Seed through the same public routes the web UI uses; contract tests pin the few routes used | A product route rename silently breaking seeds with no failing harness test |
| Bad decks bitrot as the config schema moves | medium | Decks are validated against `Config.load` round-trip in tests | A deck that no longer produces the failure its scenario asserts |
| The human sitting never happens and the rig joins PROTOCOL.md on the shelf | medium | The closing story IS the sitting; the phase cannot close without it | Phase open >2 weeks with 5/6 done |

## Decisions made

| Date | Decision | Reason | Authority |
|---|---|---|---|
| 2026-07-08 | Standalone conductor process, never an in-product route | The harness must boot/kill/reboot the product under bad configs; it cannot live inside the process under test | owner + agent |
| 2026-07-08 | Absorb and supersede dogfood (Phase 67) | One harness, no drift; the guided site replaces the fillable PROTOCOL.md | owner |
| 2026-07-08 | Coverage ledger derived from the phase index + git history | "We have git" — the shipped surface is enumerated from the record, not from memory | owner |
| 2026-07-08 | Phase 1 = mechanics + one smoke pack; full coverage is Phase 2 | Prove the rig on a thin vertical slice before authoring at scale | owner |
| 2026-07-08 | Story prefix `HSU`, code home `uat/` | Consistent with HS/HSM siblings; harness never ships in the package | owner |

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether dogfood's files physically move under `uat/` or are imported in place | HSU-1-01 implementation | Import/reuse in place; move only what the conductor must own |
| Speak-to-fill mic on the site's note fields (needs a transcriber; the product under test may be down) | HSU-1-04 | Ship typed notes first; mic rides the host product's transcribe route when it is up, degrades honestly when not |
| Whether a sitting can drive a remote mesh node on another machine | Phase 2 scenario needs | Phase 1 spawns local `mesh serve` processes only |
