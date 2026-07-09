# Phase 2 — The Inventory

**Last updated:** 2026-07-08 (scaffolded 0/5; **the directory pre-seed landed** — an 8-agent sweep produced the starting map the sweeps now verify)

## Goal

Before scenarios can be authored at scale, two things must exist that
never have: a **charter** stating what UAT *is* for this product
(jointly authored by owner and agent — verdict semantics, the
three-surface rule, sitting cadence, honesty rules), and an
**exhaustive inventory** of what the system can actually do — the
dictation copilot, meeting intelligence, the desk and its primitives,
the mesh and how work hands off between its participants, steering
live agents, the knowledge base — "literally everything, really,
really big material." The output is the matrix: every capability ×
its surface applicability (web / iPad / iPhone) × the state recipes
needed to test it × how much it matters — the single input from which
Phase 3's coverage pack is authored.

## Scope

- **In:** `uat/CHARTER.md` (jointly authored); three inventory sweeps
  (input & intelligence; meetings; the desk / the mesh / the agents)
  grounded in the phase record, git history, the docs corpus, and the
  live product on its real surfaces; `uat/features.yaml` v2 — every
  `unknown` applicability cell resolved (checked against the real
  surface, not assumed), required-state-recipe hints per capability,
  owner priority ranking; the owner review walkthrough; the derived
  Phase 3 authorship backlog and the induction-engine recipe worklist.
- **Out:** authoring the scenarios themselves (Phase 3); building new
  recipes (the worklist feeds HSU-1-02 riders or Phase 3); any product
  change; re-litigating what shipped (the record decides — where the
  record and the live product disagree, the live product wins and the
  discrepancy is itself an inventory finding).

## Exit criteria

- [ ] `uat/CHARTER.md` exists, owner-approved: what UAT is here, the
      verdict vocabulary and its semantics, the three-surface rule and
      the `n/a` discipline, sitting cadence, the honesty rules
      (timestamps, no proxy sittings), roles (the owner sits; the
      agent stages, reads, and triages).
- [ ] Every holdspeak phase (0–90+) and every holdspeak-mobile phase
      is accounted for in the ledger — mapped to capabilities or
      explicitly marked internal — with zero `unknown` surface cells
      remaining.
- [ ] Surface applicability was verified against the real surfaces
      for every cell that was `unknown` or contested — by opening the
      real app/site, not by reading docs.
- [ ] Every capability names the state recipe(s) a scenario for it
      would need; the aggregated recipe worklist is written.
- [ ] The owner walked the matrix and ranked it (must-test /
      should-test / spot-check / skip, or equivalent); the ranking is
      recorded in the ledger.
- [ ] The Phase 3 authorship backlog is derived and recorded in the
      final summary.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-2-01 | The UAT charter | backlog | [story-01](./story-01-the-uat-charter.md) | — |
| HSU-2-02 | Inventory sweep: input & intelligence | backlog | [story-02](./story-02-sweep-input-and-intelligence.md) | — |
| HSU-2-03 | Inventory sweep: meetings | backlog | [story-03](./story-03-sweep-meetings.md) | — |
| HSU-2-04 | Inventory sweep: the desk, the mesh, the agents | backlog | [story-04](./story-04-sweep-desk-mesh-agents.md) | — |
| HSU-2-05 | The matrix + the review sitting | backlog | [story-05](./story-05-the-matrix-and-review.md) | — |

## Where we are

Scaffolded 2026-07-08 on the owner's direction, the same conversation
that added three-surface UAT and the induction engine to Phase 1:
"a very, very important phase is going to be phase two — us gathering
what UAT is, us finally making an inventory of what the system can
do." Then, on the owner's explicit call for the agent fleet, an
**8-agent parallel sweep (Opus 4.8)** pounded the whole record (HS
0–90, HSM 1–27, the docs corpus) and produced the **directory
pre-seed** now under [`directory/`](./directory/): **255 capabilities**
across four domain files, each row carrying per-surface applicability
*with an evidence pointer*, needed state recipes, a priority hint, and
an expansion note — plus the sibling planning docs
[`PROTOCOL-NOTION.md`](./PROTOCOL-NOTION.md),
[`RECIPE-WORKLIST.md`](./RECIPE-WORKLIST.md), and
[`PHASE-3-PLAN.md`](./PHASE-3-PLAN.md) (the coverage-pack plan — the
output that IS Phase 3's input).

The headline finding is the parity gap: the record answers the web
desk (221/255 present) and the iPad (142 present, 98 unknown) but is
nearly silent on the **iPhone (25 present, 213 unknown)** — the single
largest thing the sweeps must resolve on real glass. **This directory
is a model's reading of the record, not a verdict**; the sweeps
(HSU-2-02/03/04) now *verify it on device* rather than start blank,
and HSU-2-05 ranks it with the owner. Nothing is actionable to *close*
until Phase 1 reaches HSU-1-03 (the ledger format the sweeps write
into), but the directory means the sweeps arrive with a map, not a
blank page. Next: Phase 1 → HSU-1-03, then the sweeps verify.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The inventory balloons into re-documenting the product | medium | An entry is one ledger row (key, phases, surfaces, recipes, rank), never prose; the docs corpus is linked, not rewritten | A sweep story producing pages instead of rows |
| Surface applicability asserted from memory/docs instead of the real device | high | The exit criterion says verified by opening the real surface; contested cells get a screenshot | An `unknown`→`yes` flip with no verification note |
| The owner review never happens and the agent ranks alone | medium | HSU-2-05 is jointly held by construction, like Phase 1's sitting; the phase cannot close without it | 4/5 done and stalled |
| Sweeps drift into fixing what they find | low | The record-vs-product discrepancy is a *finding row*, never a fix | Any product diff in a sweep commit |

## Decisions made

| Date | Decision | Reason | Authority |
|---|---|---|---|
| 2026-07-08 | The inventory is its own phase, before any coverage pack | The material is too big to enumerate as a side task; the matrix must exist before authoring at scale | owner |
| 2026-07-08 | Three sweeps by domain, not one mega-sweep | Reviewable chunks; each sweep is one sitting of owner attention | agent, owner-amendable |
| 2026-07-08 | Where record and live product disagree, the live product wins | UAT tests what IS; the discrepancy itself is a finding | owner + agent |

## Decisions deferred

| Decision | Trigger | Default |
|---|---|---|
| Whether the mobile roadmap (HSM) gets its own ledger namespace or folds into one | HSU-2-05 merge | One ledger, `surface:` columns carry the distinction |
| The ranking vocabulary (must/should/spot/skip vs numeric) | HSU-2-05 review sitting | must-test / should-test / spot-check / skip |
| Remote-machine mesh nodes in scenarios | A must-test capability requires one | Local nodes only; escalate to a Phase 3 rider |
