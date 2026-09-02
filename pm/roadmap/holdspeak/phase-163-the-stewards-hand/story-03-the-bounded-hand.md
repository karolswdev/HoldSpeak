# HS-163-03 - The bounded hand: the V0 effects, verified, never blindly replayed

- **Project:** holdspeak
- **Phase:** 163
- **Status:** done
- **Depends on:** HS-163-02
- **Unblocks:** HS-163-04
- **Owner:** unassigned

## Problem

§9.3's V0 effect set + the reliability laws STW-004..008, 010, 011.
The exit bar lives here: ONE real deduplicated effect per dogfood
run, receipted.

## Scope

- **In:** ACT fills with the bounded set, each effect a step row
  with an idempotency key, checked against Stop first, applied in
  YOLO for configured Project-owned kinds (STW-010), VERIFIED where
  a read path exists (expected vs observed recorded — STW-004):
  (1) refresh configured sources → persist observations (the 160
  collector; source failures isolate to partial coverage,
  STW-006); (2) deterministic proposals + evidence links (the
  Delta's machinery; model failure ⇒ deterministic fallback with an
  intelligible receipt, STW-007); (3) apply configured
  Project-owned proposal effects (the 160 decision verbs — accept
  with its one-transaction create_item, the 161 S-2 law); (4) draft
  or REPLACE-UNACCEPTED an update via 162's factory (UPD-004
  respected; never touch published); (5) EXACTLY ONE deduplicated
  Door item for the highest-material overdue/blocking item lacking
  canonical follow-through — a deterministic selection rule + an
  idempotency key that survives re-runs (a re-run with the same
  watermark creates ZERO additional items). STW-005: recovery of an
  indeterminate effect reconciles by idempotency key or read-back
  BEFORE re-acting (fault-injection test: kill between apply and
  record; the re-run reconciles, never doubles). STW-008: bounds
  from policy enforced (retries, per-run action count, cooldown).
- **Out:** provider-write effects (no verified actuator — out of V0), scheduling.

## Acceptance criteria

- [ ] Each effect kind: happy path + verification recorded + Stop-before-effect honored + STW-005 fault-injection proof (no double-apply).
- [ ] The ONE-Door-item law: deterministic selection proven; same-watermark re-run ⇒ zero new items; the dedup is an idempotency key, not a prayer.
- [ ] STW-008 bounds enforced by test; STW-011's shape ready: a run that performed ≥1 real effect carries its verification/receipt in the run summary.

## Test plan

- **Unit + integration:** tests/unit/test_steward_effects.py; a compounding integration test (watch observations → steward run → proposal applied → update drafted → Door item, all receipted).
