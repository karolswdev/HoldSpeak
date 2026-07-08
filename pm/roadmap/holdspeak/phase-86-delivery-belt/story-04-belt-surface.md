# HS-86-04 — The conveyor completes: station lights + evidence in place

- **Project:** holdspeak
- **Phase:** 86
- **Status:** done
- **Depends on:** HS-86-03
- **Unblocks:** HS-86-05
- **Owner:** unassigned

## Problem

**Re-scoped 2026-07-07 (mid-phase correction):** the conveyor exists
(Phase 82: `MissionControlConveyor` at the desk's foot — phases as
segments, stories as items, sessions pinned, the refusal-first
ticker). What the RFC's B1 still owes it: the **station lights** at
each lane's head (PR + CI from the new receipts, gate from the last
gate event, close from the phase's final-summary state), **evidence
opening in place** (filed objects stay openable — the standing
rule), and **frame-driven motion** (react to `scope:"belt"` frames
instead of only the private 15 s tick).

## Scope

- In: per-lane station lights on the conveyor — PR (open PRs, count
  + hover-free labels), CI (worst check conclusion of the newest
  PR's rollup: pass/fail/pending as Signal ok/danger/warn), gate
  (last `gate_pass`/`gate_refusal` event; a refusal wears its rule
  text as the in-world chip the ticker already styles), close (the
  current phase's `closed`/`open` from the feed) — all from data
  HS-86-03 + Phase 82 already deliver, no new derivation. Evidence
  in place: hub `GET /api/missioncontrol/file?repo=<name>&path=…`
  — path-allow-listed to `<repo>/pm/roadmap/**/*.md` resolved under
  the project map (the upstream workbench's file-endpoint
  containment is the precedent, mirrored in tests); a story item
  expands a pull-out panel rendering the markdown (display only,
  never state; no modal, no route away). Frame-driven refresh: the
  desk's existing `/ws` client triggers an immediate conveyor
  refresh on a `scope:"belt"` frame (poll stays the fallback).
  Desk tests + screenshots; api-surface manifest regenerated (this
  story lands the last new consumers).
- Out: any write affordance (the Phase-82 approval leg is the only
  writer, unchanged); portfolio redesign of the conveyor's layout
  (it summarizes already); iPad (B4).

## Acceptance criteria

- [ ] Screenshots: both repos' lanes with PR/CI/gate/close lights
      lit from live data; a gate refusal wearing its rule; an
      evidence file open in place on the desk.
- [ ] The file route refuses (404/400, tested) anything outside
      `<map repo>/pm/roadmap/**/*.md` — traversal, absolute paths,
      non-md, non-map repos.
- [ ] A `scope:"belt"` frame observed on `/ws` triggers a conveyor
      refresh without waiting for the tick (desk test on the
      handler; the live proof rides HS-86-05's walk).
- [ ] Desk lock patterns hold for the new UI (no dialog role, no
      reassurance prose); desk test suite + page-content tests
      green; `npm run build` clean; api-surface guard green.
- [ ] Full suite green.

## Test plan

- Unit: desk tests (`web/src/desk/__tests__/missioncontrol.test.ts`
  extensions) + route containment tests.
- Integration / Cypress: live screenshots via the existing
  Playwright scripts.
- Manual / device: the glance test — moving vs stalled and WHY, one
  look.

## Notes / open questions

- The file endpoint serves DISPLAY content; state is never derived
  from it (the counterpart's no-scraping rule §5 governs state
  derivation — reading a file to show a human stays honest, and the
  containment test keeps it narrow).
- Original story text (a new `/belt` page) superseded: the conveyor
  is the belt surface; B1 completes it rather than forking a second
  one.
