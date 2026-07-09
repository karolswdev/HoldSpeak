# Phase 1 — The Mechanics

**Last updated:** 2026-07-08 (owner direction folded in pre-build:
three-surface UAT + the induction engine; still 0/6)

## Goal

Build the UAT rig itself — the conductor that hosts HoldSpeak on this
Mac under controlled conditions and reachable by the devices, the
induction engine (config decks good and bad, desk seeding, and named
**idempotent state recipes** with verify probes — repeatable worlds,
not stumbled-into ones), the **three-surface** scenario contract
(web / iPad / iPhone, verdict per surface, honest `n/a`) with an
enumerated feature ledger, the guided website that walks a human
through a pack and captures per-surface verdicts — from the device's
own browser too — and the debrief + triage protocol that turns a
sitting into backlog-ready findings — proven by one real smoke-pack
sitting run end to end by the owner across all three surfaces.

## Scope

- **In:** the `uat/` harness (conductor process, run lifecycle, run
  DB, LAN reachability for device sittings), the induction engine
  (config decks, seed manifests, idempotent state recipes with verify
  probes, mesh-node spawn/kill), the three-surface scenario YAML
  contract + loader + validation, `uat/features.yaml` v1 (the ledger
  seeded from the holdspeak phase index, per-surface applicability
  columns, `unknown` honest), one smoke pack (~6–8 scenarios incl. at
  least one deliberately-bad deck and one three-surface scenario),
  the React+Vite guided site with per-surface verdict capture usable
  from the devices' browsers, the debrief packet generator
  (per-surface scores, cross-surface splits first-class), the joint
  triage protocol, harness docs, the live closing sitting. Absorbing
  the dogfood substrate (isolated `_home` recipe, fixture generators,
  mock repos, transcripts).
- **Out:** the exhaustive capability inventory (Phase 2 — The
  Inventory); full scenario coverage of the product (Phase 3); any
  change to HoldSpeak product behavior (the harness drives the
  product through its existing CLI/config/API surface only — a
  product bug found here becomes a *finding*, not a fix in this
  phase); device-side state induction beyond hub-synced state (a
  Phase 2 inventory question); CI automation of sittings (a sitting
  is human by definition); packaging/publishing the harness.

## Exit criteria

- [ ] `uv run python -m uat.conductor` serves the guided site on a
      pinned local port (LAN-optable for device sittings); a run
      boots an isolated HoldSpeak with a chosen deck, health-checked,
      logs captured, torn down cleanly, and reports pairing facts a
      device app can use.
- [ ] At least five decks exist including two deliberately bad ones,
      and a scenario can assert the product *fails honestly* under
      them.
- [ ] The shipped state recipes apply idempotently and verify via
      probes read back through product routes — incl.
      `meeting-just-ended-open-actions` yielding a real meeting with
      a real open action.
- [ ] The scenario contract is validated by tests with the surface
      axis enforced (explicit applicability, `n/a` requires a
      reason); `uat/features.yaml` v1 enumerates the shipped surface
      with every holdspeak phase mapped and three applicability
      columns; the smoke pack loads clean.
- [ ] The guided site walks a pack step by step, captures
      pass/fail/partial/skip + note + screenshot **per (step,
      surface)** into the run DB, works from an iPhone-width browser
      over LAN, and survives a mid-sitting product restart.
- [ ] A finished sitting generates a debrief packet (markdown + JSON,
      per-surface scores + coverage %, cross-surface splits rendered
      as one finding); the triage protocol doc defines the joint
      review and the BACKLOG feed format.
- [ ] The closing sitting: the owner runs the smoke pack live on this
      Mac end to end — the three-surface scenario sat on web, iPad,
      and iPhone with ≥1 verdict cast from a device — the debrief is
      generated, and at least one finding is triaged through the
      protocol.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-1-01 | The conductor: hosted runs | backlog | [story-01](./story-01-the-conductor.md) | — |
| HSU-1-02 | The induction engine: decks, seeds, state recipes | backlog | [story-02](./story-02-the-induction-engine.md) | — |
| HSU-1-03 | The scenario contract + the feature ledger | backlog | [story-03](./story-03-scenario-contract-and-coverage.md) | — |
| HSU-1-04 | The guided site | backlog | [story-04](./story-04-the-guided-site.md) | — |
| HSU-1-05 | The debrief + the triage protocol | backlog | [story-05](./story-05-the-debrief.md) | — |
| HSU-1-06 | Docs + the first sitting | backlog | [story-06](./story-06-docs-and-first-sitting.md) | — |

## Where we are

Scaffolded 2026-07-08 from the owner's direct ask: a robust UAT
harness that forces a real human sitting — a guided website with
scenario scripts and per-step feedback capture, powerful enough to
host the server, flip good/bad configurations, and seed the desk.
Amended the same day, pre-build, on the owner's second direction:
(a) **three-surface UAT** — nearly every scenario aims at web, iPad,
and iPhone with a verdict per surface and `n/a` honest; (b) **the
induction engine** — decks/seeds generalized into named idempotent
state recipes with verify probes, so the protocol is repeatable; (c)
**Phase 2 re-chartered as The Inventory** (the joint capability
census), pushing the coverage pack to Phase 3. Decisions locked at
scaffold: standalone conductor (not an in-product route), absorb +
supersede the Phase-67 dogfood harness, coverage enumerated from the
git/phase record, mechanics + one smoke pack only. Next: HSU-1-01.

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
| 2026-07-08 | Phase 1 = mechanics + one smoke pack | Prove the rig on a thin vertical slice before authoring at scale | owner |
| 2026-07-08 | Story prefix `HSU`, code home `uat/` | Consistent with HS/HSM siblings; harness never ships in the package | owner |
| 2026-07-08 | Three surfaces (web/iPad/iPhone) are the default target of every scenario; verdicts per surface; `n/a` needs a stated reason | "Literally nearly all of the tests should aim for those three targets" — owner, directly | owner |
| 2026-07-08 | States are induced by named idempotent recipes with verify probes, never staged by hand | "Induce specific states, for a more idempotent, repeatable protocol" — owner, directly | owner |
| 2026-07-08 | Phase 2 = The Inventory (the joint capability census + charter); the coverage pack moves to Phase 3 | The matrix must exist before scenarios are authored at scale — "really, really big material" | owner |

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether dogfood's files physically move under `uat/` or are imported in place | HSU-1-01 implementation | Import/reuse in place; move only what the conductor must own |
| Speak-to-fill mic on the site's note fields (needs a transcriber; the product under test may be down) | HSU-1-04 | Ship typed notes first; mic rides the host product's transcribe route when it is up, degrades honestly when not |
| Whether a sitting can drive a remote mesh node on another machine | Phase 2 scenario needs | Phase 1 spawns local `mesh serve` processes only |
