# HS-164-03 - run_due: the triggered hand, one run per watermark

- **Project:** holdspeak
- **Phase:** 164
- **Status:** done
- **Depends on:** HS-164-02
- **Unblocks:** HS-164-04
- **Owner:** unassigned

## Problem

§9.3: a Watch rule MAY request run_once with Project ID and
observation watermark; multiple requests at the same watermark MUST
deduplicate to one Project run. The action kind
`project.steward.run_once` is ALREADY DECLARED
(watch_validation.py:56, github_templates.py:96) — ride the admitted
door. Gate A's no-duplicates spans conductor ticks.

## Scope

- **In:** ProjectStewardService.run_due(): drain pending steward
  requests (minted by watch effects carrying the evaluation's
  observation watermark), honoring: the per-project unattended
  opt-in (default OFF — no opt-in, no run, honest skip receipt); the
  SCHEDULING-layer cooldown (the 163 S-2 carryover: cooldown_seconds
  gates unattended runs here; manual runs keep the insert_run gate);
  request dedup — an active OR terminal run at the same watermark
  for the project means the request resolves to THAT run, creating
  nothing (the query rides steward_runs.watermark; the 163
  watermark-scoped act-step key remains the effect-level belt);
  STW-002 refusals absorbed as dedup, never errors; STW-010: zero
  confirmation prompts for eligible configured effects. The watch
  effect handler for project.steward.run_once wires request minting
  at evaluation time (through the 161 effect machinery, idempotency
  key = watch evaluation identity).
- **Out:** conductor wiring (04), UI (05).

## Acceptance criteria

- [ ] Same-watermark requests (repeated, concurrent-ish, across ticks) resolve to ONE run under test; the resolution is a receipt, not an error.
- [ ] No opt-in ⇒ no run + honest skip; cooldown gates unattended runs at this layer; both durable and visible in outcomes.
- [ ] The watch effect mints requests through the existing 161 effect path with a deterministic idempotency key; replaying the evaluation mints nothing new.

## Test plan

- **Unit:** tests/unit/test_steward_run_due.py (+ effect-handler coverage in the watch effect suite).

### Orchestrator correction (2026-09-02)

The report claimed idx_watch_effects_idempotency is UNIQUE. It is NOT
(schema.py:3776 — a plain index). Lookup-first is the ONLY minting
guard; that is sufficient today because effect recording has a single
writer (evaluate_due on the conductor thread). Recorded as honest
debt: if minting ever gains a second writer, the index must graduate
to UNIQUE (schema bump).
