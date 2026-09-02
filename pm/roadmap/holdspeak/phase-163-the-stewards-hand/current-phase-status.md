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
| HS-163-03 | The bounded hand (the V0 effect set, verified, deduplicated) | backlog | [story-03-the-bounded-hand](./story-03-the-bounded-hand.md) | - |
| HS-163-04 | The wire (runs on HTTP: create/poll/stop; api-surface) | backlog | [story-04-the-wire](./story-04-the-wire.md) | - |
| HS-163-05 | The face (the Steward posture: run, watch, stop, receipts — OWNER VERDICT) | backlog | [story-05-the-face](./story-05-the-face.md) | - |
| HS-163-06 | The walk (STW-011 on glass: one real effect + a drafted update, receipted; the degraded legs) | backlog | [story-06-the-walk](./story-06-the-walk.md) | - |
| HS-163-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

2/7. HS-163-02 the run engine DONE (2026-09-02): ProjectStewardService
(holdspeak/services/project_steward_service.py) — run_once persists
the queued run durably BEFORE any phase work (STW-001; the pollable
row is visible mid-run), then executes OBSERVE->COMPARE->PROPOSE->
ACT->VERIFY->RECORD on the calling thread per the conductor pattern;
every transition = run phase update + a step checkpoint row; Stop is
a DB read between phases AND before effect slots (STW-003, no model
dependence); STW-002 surfaces as typed ActiveRunExistsError;
recover_on_startup wired in web_server _startup beside the other
recovery hooks — interrupted runs free the STW-002 slot, all through
repo methods (the raw-SQL third door was closed in-round). OBSERVE
delegates to the 160 collector, COMPARE/PROPOSE to the Delta; ACT is
the bounded no-op hook 03 fills. NOTE FOR 04: run_once is synchronous
— the POST route must spawn the daemon thread to honor the
immediate-id contract. Gates: 58 passed scoped (21 engine + 34
schema + 3 fence). Earlier: 1/7 the run ledger DONE (schema v71,
STW-002 DB law, the STW-005 substrate, real-DB reconcile on a COPY).
NEXT: HS-163-03 the bounded hand.

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
