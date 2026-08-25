# Story 08 design counsel — round 1 (2026-08-22)

Reviewer: fresh Terra session (owner per-task model order), static-only.
Subject: story-08-displaced-work-inertness-spec.md v1.
Verdict: **DO-NOT-RATIFY**. All six findings adopted into spec v2 by the
orchestrator; finding 1 changes behavior the pre-pause partial asserted
(pending handoff settled after reconcile_dispatch_intent) — visible
amendment recorded in spec v2, owner may overrule at the sitting.

## Findings (abridged; amendments folded into spec v2 verbatim)

1. **P0** — `dispatch_outcome_unknown` was activation-eligible, permitting
   duplicate egress: reconcile_dispatch_intent proves only a missing durable
   receipt (controller lines 777–827), not that the old physical call cannot
   still egress. Contract: unknown has no retry/fallback, never blind-replays.
   → Unknown/indeterminate dispositions are never activation-eligible;
   handoff stays pending, displaced work reserved forever; recovery is an
   independently admitted adopter action. Delayed-old-egress executable test
   required.
2. **P0** — provider callbacks were arbitrary callables; external
   (non-rollbackable) side effects in freeze()/activate() would survive
   rollback. → conn-only law + fault-injection tests at every boundary.
3. **P1** — settlement-presence-derived expected_state is circular if
   reconstruct() reads the settlements table. → provider-owned independent
   lifecycle witness (reservation rows + append-only activation marker);
   both-direction tamper tests.
4. **P1** — mutable single-row test provider left exactly-once dispatch
   unproven. → immutable reservation + append-only activation marker +
   append-only run receipt; two-connection competing-dispatcher test.
5. **P1** — settled replay in reconcile_stop_handoff returned without
   reconstructing evidence (service lines 546–561). → settled replay must
   reconstruct with expected `active`; refusal test for missing/corrupted
   activation after settlement.
6. **P1** — test matrix missing crash/concurrency/provenance/hostile-sync
   cases. → matrix (a)–(j) in spec v2 invariant 9.

## Static determinations (counsel-verified)

- `inference_route_executions.state` is exactly {active, stopping, stopped,
  terminal} (schema.py:2741–2765); the defect is unknown *dispositions*
  inside `terminal` (dispatch_outcome_unknown, physical_outcome_unknown,
  effect_indeterminate; schema.py:2754–2755).
- `inference_parent_stop_handoff_settlements` HAS immutable UPDATE/DELETE
  triggers (schema.py:3025–3030, 3047–3054).
- Removing `INSERT OR IGNORE` is replay-safe: validate identical replay,
  refuse conflicting row, never silently ignore.
- Activation is an adopter-level action, never controller fallback or model
  retry.

## Round 1b — Sol sounding board (2026-08-22)

Reviewer: fresh Sol session (owner's bouncing-board order), read-only.
Subject: the adopted Finding-1 ruling (unknown-disposition terminals never
activation-eligible; displaced work reserved forever; recovery = independent
admission).
Verdict: **CONCUR-WITH-NOTES**. The ruling stands with two minds.

Determinations:
- Elapsed-time activation is unlawful: frozen `deadline_at` is an admission/
  budget fence, not evidence the provider terminated the exact request
  (contract 304–322, 324–340, 387–403). "Deadline + provider timeout + grace"
  still guesses. The only lawful shortcut stays spec v2's provider-attested
  evidence tied to the physical attempt (a provider-side terminal/cancel
  receipt proving that attempt can no longer egress; socket closure / client
  timeout / SLA / local timer never qualify).

Forward obligations banked for later phases (flag at each charter):
1. **B→C cutover dependency:** Phase B must not production-enable Stop
   handoff before Phase C can preserve, expose, and refuse claims on
   forever-reserved work. Minimum adopter obligation: the deferred queue
   keeps every forever-reserved handoff durably and owner-visibly marked
   "analysis not completed; old outcome unknown", never counts it as
   completed/runnable, and offers an explicit re-request creating a new
   parent + admission.
2. **Phase C keeps two recovery paths semantically separate:** crash
   recovery adopts the exact claimed parent/route bundle; unknown-terminal
   recovery creates a NEW parent. No backoff/manual-retry/restart-scan/
   age-sweeper may turn the latter into activation of the old reservation.
3. **Phase D/E restart machinery inherits the distinction:** "terminal" with
   an unknown disposition is never sufficient proof for replay or
   replacement activation.
4. **Phase F migration preserves lifecycle posture, not merely assignment
   truth:** reserved unknown-terminal handoffs stay nonclaimable across
   marker/restart/backfill/reader cutover; never infer `active` from age,
   elapsed deadline, or the existence of a deferred job. Post-marker
   explosion tests must cover legacy deferred claim/requeue paths too.

## Owner direction (2026-08-22) — the yolo lens on recovery

The owner, mid-checkpoint: do not hamstring real use; the tool runs in YOLO
mode always; over-engineering is the recurring failure mode. Applied to this
tranche's law:

- The forever-reserved rule forbids ONLY silent reactivation of the old
  reservation while old egress is unknown. It does NOT forbid the deferred
  queue from automatically re-requesting the work as a fresh admission.
- Phase B/C charter posture: stuck-unknown deferred work AUTO-RE-RUNS as a
  new admission by default on the local boundary (worst case = wasted local
  compute); the receipt records both attempts; the owner sees "analysis
  re-ran; original outcome unknown" as a ledger line, never a stuck item
  behind a button. Cross-boundary (local→cloud) re-runs still require the
  already-saved visible consent, per the assignment chain — no new prompts.
- Sol round 1b obligation 1 is amended accordingly: owner-visible marking
  yes; mandatory manual re-request NO on the local boundary. Ceremony buys
  the receipt, never a question. Standing test at each charter: "will you
  use this on a Tuesday?"
