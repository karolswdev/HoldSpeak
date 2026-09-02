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
| HS-164-02 | evaluate_due (due Watches evaluate on cadence; isolation + circuit) | backlog | [story-02-evaluate-due](./story-02-evaluate-due.md) | - |
| HS-164-03 | run_due (the triggered hand: watermark requests, ONE run, scheduling cooldown) | backlog | [story-03-run-due](./story-03-run-due.md) | - |
| HS-164-04 | The conductor (two failure boundaries; §10 events; Cadence attention) | backlog | [story-04-the-conductor](./story-04-the-conductor.md) | - |
| HS-164-05 | The face (the unattended posture: opt-in, cadence, circuit, interventions — OWNER VERDICT) | backlog | [story-05-the-face](./story-05-the-face.md) | - |
| HS-164-06 | The walk (Gate A on glass: two useful unattended runs, zero prompts, zero duplicates) | backlog | [story-06-the-walk](./story-06-the-walk.md) | - |
| HS-164-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

1/7. HS-164-01 the due ledger DONE (2026-09-02): schema v72 additive —
connector_watches gains evaluation_cadence_minutes + durable circuit
columns (state/failure_streak/opened_at; half-open DERIVED from
opened_at + cooldown, never a second clock); steward_policies gains
unattended_enabled (explicit, NOT NULL, default OFF — the
bounded-delegation flag as a REAL column). The traces held: the
graduated watches ALREADY carry next_evaluation_at/last_evaluated_at
(HS-159-01 — reused, not duplicated); the legacy refresh_due_watches
reads JSON cadence and stays untouched (story 02 owns the boundary);
EndpointHealth stays in-memory for LLM endpoints — the watch circuit
is durable for STW-009. All four DB version pins found + updated
honestly (the 163 scar paid). Gates: 217 passed scoped; real-DB
reconcile to v72 on a COPY (2 passed). NEXT: HS-164-02 evaluate_due.

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
