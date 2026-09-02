# Phase 163 - Project Rooms: The Steward's Hand (P4)

- **Project:** holdspeak
- **Status:** in-progress
- **Chartered:** 2026-09-02 off main `45385a4c` (162 The Update Factory MERGED via PR #527 — the SEVENTH Project Rooms phase merged: #521 #522 #523 #524 #525 #527)
- **Canon:** docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §9 (the Steward: 9.1 runtime ruling, 9.2 run lifecycle, 9.3 V0 eligible effects, 9.4 STW-001..011), §14 P4 slice; the frozen contracts; CONSTITUTION.md

## The charter

P4's exit, verbatim: **a manual run performs one real deduplicated
effect and drafts an update with a durable receipt.** The Steward is
NOT a prompt sent to Workbench (§9.1's runtime ruling):
`ProjectStewardService` owns run coordination and persistence,
reusing the conductor's heartbeat/failure-isolation patterns, the
frozen inference routing, and the Cadence projection. The lifecycle
is six checkpointed phases — OBSERVE → COMPARE → PROPOSE → ACT →
VERIFY → RECORD — every phase durable before asynchronous work
begins (STW-001), one active run per Project (STW-002), Stop as a
durable request checked between steps and before every effect,
never dependent on a model response (STW-003). A V0 run MAY:
refresh sources and persist observations; create deterministic
proposals + evidence links; apply configured Project-owned proposal
effects in YOLO (STW-010 — no confirmation prompts for eligible
configured effects); draft or replace an UNACCEPTED update through
162's factory; create EXACTLY ONE deduplicated Door item for the
highest-material overdue/blocking item lacking canonical
follow-through. Effects with a read path are VERIFIED
(expected-vs-observed, STW-004); indeterminate effects are never
blindly replayed (STW-005); source failures isolate into partial
coverage (STW-006); model failure falls back to deterministic
Delta/update behavior with an intelligible receipt (STW-007);
retries/action counts/cooldowns bounded by policy (STW-008);
startup recovery marks abandoned runs interrupted and reconciles
safe resumability (STW-009). Manual `run_once` ONLY — scheduling
(`run_due`, Watch-triggered requests, the conductor block) is P5's.

OUT: scheduling/unattended (P5), MCP (P6), Jira (P7), remote
delivery-system mutation (no verified actuator exists — an actuator
omission, not an approval policy).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-163-01 | The run ledger (schema v71: policy/run/step/command persistence; STW-001) | done | [story-01-the-run-ledger](./story-01-the-run-ledger.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-163-02 | The run engine (six checkpointed phases; uniqueness, Stop, recovery) | done | [story-02-the-run-engine](./story-02-the-run-engine.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-163-03 | The bounded hand (the V0 effect set, verified, deduplicated) | done | [story-03-the-bounded-hand](./story-03-the-bounded-hand.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-163-04 | The wire (runs on HTTP: create/poll/stop; api-surface) | done | [story-04-the-wire](./story-04-the-wire.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-163-05 | The face (the Steward posture: run, watch, stop, receipts — OWNER VERDICT) | in-progress | [story-05-the-face](./story-05-the-face.md) | - |
| HS-163-06 | The walk (STW-011 on glass: one real effect + a drafted update, receipted; the degraded legs) | done | [story-06-the-walk](./story-06-the-walk.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-163-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

5/7 committed; 05 awaits THE OWNER'S VERDICT. HS-163-06 the walk DONE
(2026-09-02): tests/e2e/test_hs163_steward_glass.py, four legs, 8
passed x2 deterministic, both viewports, no-raw-ids law asserted. The
rig EARNED ITS KEEP - three product defects found and fixed in-round:
(1) DoorService built without db= in web_server (create_door_item
failed on every run; one line); (2) the door idem key was
item+watermark scoped AND never stored on any step - the promised
same-watermark dedup was a phantom held up by a self-seeded unit
fixture (the 161 scar); redesigned: watermark-scoped key ON the act
step, so the ordinary step-key reconcile catches every same-watermark
re-run - manual presses (no watermark) are governed by the
follow-through read-back; (3) step seq collided across the engine
loop and ACT (interleaved chronology on glass) - seq now allocates
from the live step count. Face consequence round: visible toggle
labels, PARTIAL COVERAGE chip (STW-006 visible + rig-asserted),
substance secondary lines ('5 effects'), honest pluralization;
decodeSummary now reads effects from phase_results. The degraded seam
is honest: a MISSING watch row (watch_not_found), not a dead
connector (WatchAdapter never calls providers). Stale-bundle law
paid: the rig had no build step - evidence wrapper builds first.
Measured: 5 effects one press; same-watermark re-run 0 new items;
manual re-press only ever doors the NEXT uncovered item. Gates:
glass 8x2 + steward 104 + web 2254 zero branch-new. Earlier: 4/7
wire, 3/7 hand, 2/7 engine, 1/7 ledger. NEXT: owner verdict on 05,
then 07 the close.

## Active risks

- STW-005 (indeterminate effects never blindly replayed) is the
  phase's hardest honesty problem: recovery must reconcile by
  idempotency key or read-back BEFORE re-acting. The run ledger's
  step/command records are the reconciliation substrate — design
  them for it from story 01.
- The ONE-Door-item dedup ("exactly one, for the highest-material
  item lacking canonical follow-through") needs a deterministic
  selection rule and an idempotency key that survives re-runs.
- Debts carried in: 160's N-5 (widen the no-fetch spy), N-1 (Space
  preview), N-2 (server-side undismiss); 158's S-1/N-1/N-3; 159's
  seeding walls; 161 counsel N-1 (React scope key).
