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
| HS-163-02 | The run engine (six checkpointed phases; uniqueness, Stop, recovery) | backlog | [story-02-the-run-engine](./story-02-the-run-engine.md) | - |
| HS-163-03 | The bounded hand (the V0 effect set, verified, deduplicated) | backlog | [story-03-the-bounded-hand](./story-03-the-bounded-hand.md) | - |
| HS-163-04 | The wire (runs on HTTP: create/poll/stop; api-surface) | backlog | [story-04-the-wire](./story-04-the-wire.md) | - |
| HS-163-05 | The face (the Steward posture: run, watch, stop, receipts — OWNER VERDICT) | backlog | [story-05-the-face](./story-05-the-face.md) | - |
| HS-163-06 | The walk (STW-011 on glass: one real effect + a drafted update, receipted; the degraded legs) | backlog | [story-06-the-walk](./story-06-the-walk.md) | - |
| HS-163-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

1/7. HS-163-01 the run ledger DONE (2026-09-02): schema v71 —
steward_policies / steward_runs / steward_steps / steward_commands,
additive, named columns; STW-002 as a DB law (partial unique index
uq_steward_runs_one_active_per_project WHERE state IN queued/running/
stopping, typed ActiveRunExistsError at the repo); the step record
carries idempotency_key + expected/observed JSON — the STW-005
reconciliation substrate; four repos with conn-accepting
*_in_transaction variants; snapshot regenerated; reconcile-from-v70 +
idempotence under test; real-DB reconcile proven on a COPY (evidence
leg 2, 1 passed). Gates: 140 passed 1 skipped scoped; positional-
INSERT fence green. NEXT: HS-163-02 the run engine.

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
