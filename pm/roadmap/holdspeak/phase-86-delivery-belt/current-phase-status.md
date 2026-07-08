# Phase 86 — The Delivery Belt (read-only): the AI Headquarters floor, first light

**Last updated:** 2026-07-07 (HS-86-03 done).

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

- [x] `dw check` on this repo reports zero errors, and `dw doctor`
      reports healthy rails (HS-86-01, HS-86-02 —
      [evidence-01](./evidence-story-01.md), [evidence-02](./evidence-story-02.md)).
- [x] A commit of this phase lands through the refreshed stamped
      gate with PMO trailers (HS-86-02's own commit; `dw verify` ok
      in [evidence-03](./evidence-story-03.md)).
- [x] PR/CI receipts and change-driven `scope:"belt"` frames ride
      the existing mission-control routes/bus for ≥2 real repos,
      GET-only proven ([evidence-03](./evidence-story-03.md)).
- [x] The Phase-82 conveyor gains station lights (PR/CI/gate/close)
      and evidence opening in place, frame-driven, desk locks green
      ([evidence-04](./evidence-story-04.md) + screenshots).
- [x] The live walk: the closing story's motion observed on the belt
      and captured, zero belt-side writes
      ([evidence-05](./evidence-story-05.md), walk-1..4 + the
      all-GET access log; the merge beat lands post-commit on green
      CI per the cadence).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-86-01 | The clean tree — fix the 31 triaged desyncs | done | [story-01-clean-tree](./story-01-clean-tree.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-86-02 | The refreshed rails — stamped gate + embedded dw | done | [story-02-refreshed-rails](./story-02-refreshed-rails.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-86-03 | The receipts the conveyor lacks: gh lights + belt frames (hub) | done | [story-03-hub-belt-route](./story-03-hub-belt-route.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-86-04 | The conveyor completes: station lights + evidence in place | done | [story-04-belt-surface](./story-04-belt-surface.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-86-05 | The live walk + docs + closeout | done | [story-05-live-walk-and-docs](./story-05-live-walk-and-docs.md) | [evidence-story-05](./evidence-story-05.md) |

## Where we are

HS-86-01 done (2026-07-07): the tree is clean — `dw check` exits 0
across both projects (was 397 errors on v1.12.0, 31 after upstream
phase 16). 14 retrospective final summaries (labeled), phase-15
status doc backfilled, 7 placeholder rows became real story stubs,
the genuine drifts reconciled on whichever side was stale. Suite
3299 passed / 37 skipped. HS-86-02 done the same evening: the rails
refreshed from upstream main — stamped-fact gate + embedded dw +
managed CLAUDE.md block, doctor healthy, a hand-written contract
refused by name, and its own commit is the first through the new
gate. HS-86-03 done (re-scoped): `/api/missioncontrol/receipts` (gh PR +
check rollups per map repo, typed absence), `scope:"belt"` frames on
observed tree change, the three Phase-82 reads moved onto
asyncio.to_thread, GET-only fitness. 22/22 module tests; suite 3305.
HS-86-04 done: station lights on every lane head (PR/CI from the
new receipts, gate from the newest rail event — the shots caught a
REAL contract-missing refusal on the delivery-workbench lane),
evidence opening in place inside the conveyor, frame-driven refresh
on scope:belt. 39 route/lock/guard tests + 63 desk tests + suite
3312 (read from the file). HS-86-05 done: the walk ran live (one page session, never reloaded)
— the flip, the evidence capture, a REAL contract-missing refusal,
and PR #303's lights, each on the belt within a poll beat; the
access log holds 12 requests, all GET. Docs (USER_GUIDE, SECURITY
egress row, ARCHITECTURE read path) + BACKLOG/README cadence +
final-summary ship with this commit. The phase closes 5/5.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Retrofitting the stamped gate breaks the commit flow mid-phase | medium | HS-86-02 is its own story with the proof being its own commit; `update.sh` preserves `pre-commit.config`/`.local` seams; rollback = git checkout .githooks | two consecutive commits blocked for gate reasons unrelated to honesty |
| Shelling `dw` per request makes /api/belt slow | medium | `asyncio.to_thread` + a short in-process TTL cache (seconds, not a truth store — receipts stay the source) | route p95 > 2s with 2 repos |
| The belt surface drifts into prose/modals under feature pressure | low | desk locks extended to /belt in the same story that builds it | a lock test edit that weakens a rule |
| Retro final summaries read as fabricated history | low | every retro summary opens with "Retrospective closeout (2026-07-07), reconstructed from evidence + git history" | any summary claiming an unevidenced outcome |

## Lessons (recorded mid-phase)

- 2026-07-07 — HS-86-03's commit initially shipped false evidence
  ("suite green" written before the output was read; the output had
  been piped through `tail`, destroying the failure list). Corrected
  the same evening in a follow-up commit with the true record. The
  standing rule from it: the suite lands in a file, gets READ, and
  only then does the story flip — never chained.
- 2026-07-07 — the failures themselves unmasked a sixty-phase-old
  leak: the Phase-26 import-cycle test popped `holdspeak.web.routes`
  from sys.modules without restoring it. Fixed at the source
  (restore in `finally`); 21 order-dependent failures gone.

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
- 2026-07-07 (mid-phase correction) — HS-86-03/04 re-scoped: Phase 82
  already shipped the registry (the operator's project map), the
  three-document relay, the conveyor, AND the gated approval leg
  (B2's seed). B1's remaining truth: gh receipts, belt frames on the
  bus, station lights, evidence in place. The Phase-84 lesson
  (survey before scaffolding) recorded twice in one day.
- 2026-07-07 — belt frames are emitted on observed change during
  reads (the conveyor's 15 s poll is the heartbeat), not from a new
  background loop — zero new lifecycle; revisit in B2 if a
  poller-less surface appears.

## Decisions deferred

- Steering verbs from the belt (approve, dispatch, merge) — B2, after
  the read-only floor is walked — default: none in this phase.
- "New Project" from the desk (repo + rails install + agent intake) —
  B3 — default: registry entries are hand-authored config.
- The DeskOS diorama belt — B4 on the HSM track — default: web only.
- Remote/mesh repos in the registry — RFC §5 — default: local paths
  only, honest `no rails` for anything else.
