# Phase 164 - Project Rooms: The Unattended Desk (P5)

- **Project:** holdspeak
- **Status:** in-progress
- **Chartered:** 2026-09-02 off main `69e16678` (163 The Steward's Hand MERGED via PR #529 — the EIGHTH Project Rooms phase merged: #521 #522 #523 #524 #525 #527 #529)
- **Canon:** docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §14 P5 slice, §9.1-9.3 (run_due as an isolated conductor block; Watch-triggered run_once at the observation watermark, same-watermark requests dedupe to ONE run), §10 (steward event kinds; Cadence MAY project review_due/source_degraded/steward_intervention_required and MUST NOT become the schedule of record); CONSTITUTION.md; the owner's bounded-delegation ruling (enabling a schedule approves its exact work until disabled)

## The charter

P5's exit, verbatim: **Gate A observes at least two useful unattended
runs without confirmation prompts or duplicate effects.** The desk
works while the owner does not: `WatchService.evaluate_due()` and
`ProjectStewardService.run_due()` join the conductor as INDEPENDENT
failure boundaries (the _tick block idiom — a broken Project or
source never stops other conductor duties); Watch rules request
steward runs through the ALREADY-DECLARED `project.steward.run_once`
action kind (watch_validation.py:56, github_templates.py:96 — RIDE
the admitted door, never a second species) at the evaluation's
observation watermark, and multiple requests at the same watermark
deduplicate to ONE run (§9.3 — the watermark-scoped act-step key
built and glass-proven in 163 is the substrate); repeated source
failure opens a circuit (the HS-103-04 endpoint_health shape) instead
of hammering; the 163 carryover pays here: cooldown at the SCHEDULING
layer, and unattended acting is gated by an explicit per-project
opt-in honoring the bounded-delegation ruling. §10's missing steward
event kinds (configured / run_started / step_completed /
intervention_required — only run_completed exists today,
project_steward_service.py:1119) land at the seams, and Cadence
projects attention (review_due, source_degraded,
steward_intervention_required) WITHOUT becoming the schedule of
record. STW-010 carries: unattended eligible effects run with zero
confirmation prompts.

OUT: MCP (P6), Jira (P7), provider-write actuators, any new
inference entrance (the steward still routes only through the
admitted 160/162 verbs).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-164-01 | The due ledger (additive schema: cadence, unattended opt-in, circuit state; trace-first) | done | [story-01-the-due-ledger](./story-01-the-due-ledger.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-164-02 | evaluate_due (due Watches evaluate on cadence; isolation + circuit) | done | [story-02-evaluate-due](./story-02-evaluate-due.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-164-03 | run_due (the triggered hand: watermark requests, ONE run, scheduling cooldown) | done | [story-03-run-due](./story-03-run-due.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-164-04 | The conductor (two failure boundaries; §10 events; Cadence attention) | done | [story-04-the-conductor](./story-04-the-conductor.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-164-05 | The face (the unattended posture: opt-in, cadence, circuit, interventions — OWNER VERDICT) | done | [story-05-the-face](./story-05-the-face.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-164-06 | The walk (Gate A on glass: two useful unattended runs, zero prompts, zero duplicates) | done | [story-06-the-walk](./story-06-the-walk.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-164-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

6/7. THE OWNER'S VERDICT, verbatim: round 1 "Bounce" (scroll wells
must announce themselves + his model-wiring question — both recorded
verbatim in the story file), round 2 "PASS". Both findings paid: the
Door scroll-hint species ported vertical (rest-visible edge fades on
every scrolling steward well); the MODEL chip removed from Created
proposals (the Delta's augmentation is an identity no-op — the badge
over-claimed egress) and the honest chip on Drafted update names its
wiring (project.update_draft in Settings > Models, deterministic
fallback with a receipt on model failure). His question answered
plainly on the gallery itself. HS-164-05 the face DONE: web gates
2275 passed zero branch-new. Earlier: 5/7 walk (Gate A counted),
4/7 conductor, 3/7 run_due, 2/7 evaluate_due, 1/7 due ledger. NEXT:
HS-164-07 the close — the 27-name main baseline REMAINS VALID for
69e16678 (163's close fixed only branch-new breaks; nothing left
main's failing set) — full suite, sweep, counsel, PR, merge.

## Active risks

- The unattended dedup law spans TWO layers: request-level (same
  watermark ⇒ one run, §9.3) and effect-level (the 163 act-step
  key). Gate A's "no duplicate effects" needs BOTH proven across
  conductor ticks, not within one run.
- The circuit must be DURABLE enough to survive restart without
  becoming a new schedule-of-record; trace endpoint_health's
  in-memory design against STW-009 recovery before choosing.
- Legacy refresh_due_watches (ReactionService, already in _tick)
  vs the graduated WatchService: story-02 must TRACE the boundary —
  never two schedulers fighting over one watch.
- Debts carried in: 163 S-4 (route-layer command recording), N-1
  (thread pool), N-3 (recovery's second instance); 160 N-5/N-1/N-2;
  158 S-1/N-1/N-3; 159 seeding walls; 161 N-1 (React scope key).
