# Phase 86 — The Delivery Belt (read-only): the AI Headquarters floor, first light

**Last updated:** 2026-07-07 (phase scaffolded).

## Goal

Render the delivery pipeline as a desk-native, receipts-only surface:
a projects registry on the hub, a belt per registered rails repo
(phases as segments, stories riding stations, gate/CI as lights, the
live agent lane from real session correlation), spoken in the same
telegram grammar as everything else on the one bus — read-only end to
end. Owner frame: *"my AI Headquarters — build out projects, steer
projects, finalize projects"* — this phase is the floor those later
verbs stand on.

## Scope

- In: the HoldSpeak-side cleanup the upstream triage named (31 real
  desyncs); the framework install refresh (stamped gate, embedded
  `dw`, agent-docs block); hub `belt` config + `GET /api/belt/state`
  composing `dw state`/`sessions`/`events` per registered repo +
  `gh` PR/check receipts + `scope:"belt"` frames on `/ws`; the
  `/belt` web-desk surface (Signal, no prose, no modals, evidence
  opens in place); the live walk (a real story crosses the belt
  during this phase's own shipping); docs + BACKLOG/README cadence.
- Out: ANY write path from the belt (approve/dispatch/merge/scaffold
  — B2/B3 per the RFC); the DeskOS (iPad) belt (B4, HSM track);
  upstream dw changes (phase 16 shipped them); multi-machine/mesh
  belts (RFC §5 defers them).

## Exit criteria (evidence required)

- [ ] `dw check` on this repo reports zero errors, and `dw doctor`
      reports healthy rails (HS-86-01, HS-86-02).
- [ ] A commit of this phase lands through the refreshed stamped
      gate with PMO trailers (HS-86-02 evidence shows the trailer).
- [ ] `GET /api/belt/state` returns registry-shaped belt state for
      ≥2 real repos, with a fitness test proving no mutation route
      exists under `/api/belt` (HS-86-03).
- [ ] The `/belt` surface renders both belts live (screenshots:
      stations, lights, agent lane, evidence opened in place), and
      the desk locks pass (HS-86-04).
- [ ] The live walk: a real story's motion (in-progress → evidence →
      done → gate pass → PR → CI green → merge) observed on the belt
      and captured (HS-86-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-86-01 | The clean tree — fix the 31 triaged desyncs | backlog | [story-01-clean-tree](./story-01-clean-tree.md) | - |
| HS-86-02 | The refreshed rails — stamped gate + embedded dw | backlog | [story-02-refreshed-rails](./story-02-refreshed-rails.md) | - |
| HS-86-03 | The hub belt: registry, state route, belt frames | backlog | [story-03-hub-belt-route](./story-03-hub-belt-route.md) | - |
| HS-86-04 | The belt surface on the web desk | backlog | [story-04-belt-surface](./story-04-belt-surface.md) | - |
| HS-86-05 | The live walk + docs + closeout | backlog | [story-05-live-walk-and-docs](./story-05-live-walk-and-docs.md) | - |

## Where we are

Scaffolded 2026-07-07, the same day the substrate learned to read
this repo (delivery-workbench phase 16: 397 spurious check errors →
31 real, triaged upstream in that phase's evidence-story-04). Next:
HS-86-01 consumes that triage list.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Retrofitting the stamped gate breaks the commit flow mid-phase | medium | HS-86-02 is its own story with the proof being its own commit; `update.sh` preserves `pre-commit.config`/`.local` seams; rollback = git checkout .githooks | two consecutive commits blocked for gate reasons unrelated to honesty |
| Shelling `dw` per request makes /api/belt slow | medium | `asyncio.to_thread` + a short in-process TTL cache (seconds, not a truth store — receipts stay the source) | route p95 > 2s with 2 repos |
| The belt surface drifts into prose/modals under feature pressure | low | desk locks extended to /belt in the same story that builds it | a lock test edit that weakens a rule |
| Retro final summaries read as fabricated history | low | every retro summary opens with "Retrospective closeout (2026-07-07), reconstructed from evidence + git history" | any summary claiming an unevidenced outcome |

## Decisions made (this phase)

- 2026-07-07 — The Belt is registry-shaped from day one (never
  single-project) — owner: "my AI Headquarters… build out, steer,
  finalize projects" — B2/B3 land on a portfolio surface, not a
  retrofit.
- 2026-07-07 — Hub shells the repo-embedded `.githooks/dw` per
  registered repo (never imports dw_pmo) — each repo's rails answer
  for themselves; version skew is a feature — AGENT-BRIEF.
- 2026-07-07 — Belt state rides the one `/ws` bus as
  `scope:"belt"` frames in the `_run_frame` vocabulary — owner
  interop steer + Phase-72 one-bus canon.
- 2026-07-07 — B1 is read-only with a fitness proof, mirroring the
  upstream workbench's mission-control guard — RFC non-negotiable #2.

## Decisions deferred

- Steering verbs from the belt (approve, dispatch, merge) — B2, after
  the read-only floor is walked — default: none in this phase.
- "New Project" from the desk (repo + rails install + agent intake) —
  B3 — default: registry entries are hand-authored config.
- The DeskOS diorama belt — B4 on the HSM track — default: web only.
- Remote/mesh repos in the registry — RFC §5 — default: local paths
  only, honest `no rails` for anything else.
