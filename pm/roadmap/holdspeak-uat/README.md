# HoldSpeak UAT — Roadmap

**Last updated:** 2026-07-08 (project scaffolded; Phase 1 — The Mechanics — 0/6)
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

Two principles anchor it:

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
| 1 | The Mechanics: the conductor (hosted runs, config decks, desk seeding, mesh nodes), the scenario contract + coverage ledger, the guided UAT site, the debrief + triage protocol, proven by one live smoke-pack sitting | in-progress (0/6) | [phase-1-the-mechanics](./phase-1-the-mechanics/) |

(Status values: `planning`, `in-progress`, `done`, `paused`, `cancelled`.)

Phase 2 (not yet scaffolded) is the first real coverage pack: scenario
authorship across the whole feature ledger — dictation, meetings,
desk, mesh, steering, the belt — sat through end to end.

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
- **Scenario** — a declarative script: deck + seeds + ordered steps,
  each step an instruction, an expectation, and a verdict prompt.
- **Pack** — a curated set of scenarios run as one sitting.
- **Sitting** — one human UAT run of a pack, end to end, on real metal.
- **Debrief packet** — the generated record of a sitting (verdicts,
  notes, screenshots, coverage) that the owner and the agent triage
  together.
- **Feature ledger** — `uat/features.yaml`: the enumerated shipped
  surface, derived from the holdspeak phase index; scenarios cite its
  keys; debriefs compute coverage against it.
