# HoldSpeak UAT — Roadmap

> 🎯 **Next agent, building the framework? START at
> [`HANDOVER.md`](./HANDOVER.md)** — the explicit goal, the build order, the
> source seams, the autonomy contract, and the definition of done. It is written
> to be executed unattended, end to end.

**Last updated:** 2026-07-09 (HSU-1-05 shipped — the debrief packet (md+json, per-surface scores + log slices) + findings/triage lifecycle + TRIAGE.md + the BACKLOG feed; Phase 1 at 5/6)
**Current phase:** [Phase 1 — The Mechanics](./phase-1-the-mechanics/current-phase-status.md)
**Status:** active

## Vision

Ninety-plus phases shipped features; almost every proof was an agent
proving its own work. What the product has never had is a **forcing
function for the human**: a rig that sits the owner down, walks them
through the real product scenario by scenario, and captures what they
actually saw — so the two of us (owner and agent) can look at the same
record afterwards and decide what to fix, what to cut, and what was
fine all along.

This project builds that rig: the **conductor** (a standalone process
that hosts HoldSpeak on this Mac — boots it with a chosen
configuration, good or deliberately bad, seeds the desk, spawns mesh
nodes, restarts it between scenarios) and the **guided UAT site** (a
local website that runs the script: "do this, expect this", one
verdict per step, notes and screenshots attached, everything landing
in a run database). A run ends in a **debrief packet** the owner and
the agent triage together; accepted findings feed
`pm/roadmap/holdspeak/BACKLOG.md` with the run as the citation.

Four principles anchor it:

1. **The harness stands outside the product.** It must be able to
   boot HoldSpeak broken, kill it, and boot it again differently — so
   it can never live inside the process under test. It supersedes the
   Phase-67 dogfood harness and absorbs its substrate (the isolated
   `_home`, the mock repos, the `say`-rendered fixtures); the guided
   site replaces the fillable `PROTOCOL.md` as how a human runs UAT.
2. **Coverage is enumerated, not remembered.** The shipped surface is
   derived from the record we already have — the 90-phase index and
   git history — into a feature ledger every scenario cites, so a
   debrief can honestly state what fraction of the product a sitting
   touched and what has never been sat through.
3. **Three surfaces, one script.** The iPad, the iPhone, and the web
   desk are the product's **claimed parity set** — that parity is the
   experience HoldSpeak is building, and UAT is the instrument that
   holds the product to the claim. Nearly every scenario aims at all
   three, a verdict is cast *per surface* (with `n/a` an honest
   first-class answer, reason stated), and a cross-surface verdict
   split is a **parity break** — a first-class finding class. A
   sitting that only touched the web is a partial sitting and the
   record says so.
4. **States are induced, not stumbled into.** A scenario's
   precondition is a named, idempotent **state recipe** the conductor
   executes and *verifies* ("a meeting just ended with three open
   actions", "an agent pane is awaiting input", "the node just
   died") — so two sittings a month apart start from the same world
   and their verdicts are comparable.

## Source canon

Phase content must be grounded in these. If a phase disagrees with
canon, canon wins.

- `dogfood/PROTOCOL.md` + `dogfood/` — the Phase-67 substrate this
  project absorbs (isolated HOME, fixtures, mock repos, `.43` wiring).
- `docs/ARCHITECTURE.md` — the system map the scenarios exercise.
- `docs/internal/POSITIONING.md` — the story the product must live up
  to under a stranger's hands; scenario "expect" lines are written
  against it.
- `pm/roadmap/holdspeak/README.md` (phase index) — the coverage
  ledger's source of truth for what shipped.
- `CLAUDE.md` — the PMO gate every commit passes.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | The Mechanics: the conductor (hosted runs reachable by the devices), the induction engine (decks, seeds, idempotent state recipes, mesh hands), the three-surface scenario contract + seed ledger, the guided UAT site with per-surface verdicts, the debrief + triage protocol, proven by one live smoke-pack sitting | in-progress (5/6) | [phase-1-the-mechanics](./phase-1-the-mechanics/) |
| 2 | The Inventory: owner + agent gather what UAT *is* here (the charter) and enumerate everything the system can do into the capability × surface × required-state matrix that Phase 3's coverage pack is authored from. **Directory pre-seeded** by an 8-agent sweep: 255 capabilities, the [directory](./phase-2-the-inventory/directory/), the [protocol notion](./phase-2-the-inventory/PROTOCOL-NOTION.md), the [recipe worklist](./phase-2-the-inventory/RECIPE-WORKLIST.md), and the [Phase 3 plan](./phase-2-the-inventory/PHASE-3-PLAN.md) | planning (0/5) | [phase-2-the-inventory](./phase-2-the-inventory/) |

(Status values: `planning`, `in-progress`, `done`, `paused`, `cancelled`.)

Phase 3 (not yet scaffolded) is the coverage pack: scenario authorship
across the whole inventory matrix, sat through end to end on all three
surfaces.

## Operating cadence

Per `pm/roadmap/roadmap-builder.md` §3, every shipping commit updates,
in the same commit:

1. The story file header (status flip).
2. The phase's `current-phase-status.md` story-status row + "Where we are".
3. This README's "Last updated" line.
4. Any project-canon doc touched by the story.

Per `pm/roadmap/PMO-CONTRACT.md`: the pre-commit hook gates every
commit on a fresh `.tmp/CONTRACT.md`.

## Project metadata

- **Slug:** `holdspeak-uat`
- **Story ID prefix:** `HSU` (e.g. `HSU-1-01`)
- **Code home:** `uat/` at the repo root (the conductor, decks,
  scenarios, the site). Dev harness — never part of the published
  `holdspeak` package.

## Glossary

- **Conductor** — the standalone harness process: hosts HoldSpeak as a
  managed subprocess per run, applies decks, seeds the desk, serves
  the guided site.
- **Deck** — a named configuration permutation (good or deliberately
  bad) written into the run's isolated HOME before boot.
- **Seed manifest** — a declarative description of desk/context state
  (notes, KB, recipes, meetings) injected before a scenario starts.
- **State recipe** — a named, idempotent, self-verifying procedure the
  conductor runs to induce a described world state (a deck + seeds +
  process/mesh actions, closed by a verify probe read back through
  product APIs). The unit of repeatability.
- **Surface** — where the human meets the product: `web`, `ipad`,
  `iphone`. Scenarios declare per-surface applicability; verdicts are
  cast per surface.
- **Scenario** — a declarative script: state recipe(s) + surfaces +
  ordered steps, each step an instruction, an expectation, and a
  verdict prompt.
- **Pack** — a curated set of scenarios run as one sitting.
- **Sitting** — one human UAT run of a pack, end to end, on real metal.
- **Debrief packet** — the generated record of a sitting (verdicts,
  notes, screenshots, coverage) that the owner and the agent triage
  together.
- **Feature ledger** — `uat/features.yaml`: the enumerated shipped
  capabilities; scenarios cite its keys; debriefs compute coverage
  against it. Phase 1 seeds it mechanically from the holdspeak phase
  index; Phase 2's inventory makes it exhaustive and adds the
  per-surface applicability + required-state columns (the matrix).
