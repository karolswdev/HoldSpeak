# Story 08 design spec — inert displaced work and settlement-gated activation

**Status:** v2 — amended per design-counsel round 1 (DO-NOT-RATIFY, all six
findings adopted; see `story-08-displaced-work-counsel-round1.md`).
**Scope:** `InferenceParentRouteBundleService` Stop handoff only (tranche C).
**Authority:** HANDOVER-STORY-08.md §8 P0 required closure 1–7;
`assets/architecture-contract.md` failure law (unknown effect ⇒ no advance,
never blind-replays).

## The defect being closed

`request_stop_handoff` runs the adopter's `provider.freeze(conn, …)` inside the
election transaction. When any fenced execution elects `stopping` (an old
physical attempt is at `dispatch_intent` / unknown), the handoff persists as
`pending_physical_settlement` — but the frozen displaced-work record is already
durable, and nothing in the `HandoffEvidenceProvider` contract prevents a real
adopter from persisting an immediately-runnable deferred job. Old egress may
still be in flight while the replacement starts: forbidden duplicate egress.

## Visible amendment vs the handover's prior direction

The pre-pause partial (and its test
`test_stop_handoff_pending_settles_after_unknown_dispatch_without_new_egress`)
settled the handoff after `reconcile_dispatch_intent` terminalized an
unknown-dispatch attempt. Counsel round 1 ruled that unlawful: the
reconciliation proves only a missing durable receipt, not that the old
physical call cannot still egress (`architecture-contract.md`: unknown has no
retry, no fallback, never blind-replays). The test is updated to the new law —
classification (a), old-posture assertion. The owner may overrule at the
sitting.

## Invariants (the law)

1. **Reserve-inert.** The election transaction persists only a *reserved*
   displaced-work record. `freeze()` MUST return evidence with
   `"state": "reserved"`. Any other state, or a `freeze()` that writes
   nothing, refuses the whole handoff transaction (rollback; no partial rows).
2. **Provider callbacks are transaction-bound.**
   `HandoffEvidenceProvider.freeze()`, `.reconstruct()`, and `.activate()`
   MUST perform durable writes only through the supplied SQLite connection.
   They MUST NOT dispatch work, call a network/queue API, use a second
   database connection, or produce any non-rollbackable side effect. A
   dispatcher may claim activated work only after the enclosing transaction
   commits. `reconstruct()` is read-only (`conn.total_changes` unchanged);
   `activate()` must write (`conn.total_changes` advanced). Every provider
   exception propagates so the enclosing transaction rolls back.
3. **No dispatch while reserved.** A reserved record is not claimable or
   dispatchable by the adopter. The provider contract carries this duty; the
   primitive proves it via the executable proof provider (invariant 9) and the
   independent-witness checks (invariant 6).
4. **Activation eligibility.** An execution terminalized as
   `dispatch_outcome_unknown`, `physical_outcome_unknown`, or
   `effect_indeterminate` is **not** activation-eligible.
   `reconcile_dispatch_intent` records the indeterminate terminal receipt but
   leaves the handoff pending and the displaced work reserved — forever, if
   nothing more is ever proven. `_settle_and_activate` may activate only after
   every fenced execution in `inference_parent_stop_handoff_executions` has
   left `{'active','stopping'}` into the closed set `{'stopped','terminal'}`
   **and** carries an activation-eligible terminal disposition (known
   pre-send refusal, known completed/failed receipt, owner-cancelled
   pre-dispatch, …), or after provider-attested evidence proves the old
   physical attempt cannot egress. A controller terminal state alone is
   insufficient. An execution state or disposition outside the known closed
   sets refuses (no guessing). Recovery of forever-reserved work is an
   independently admitted adopter-level action (new parent, new admission),
   never this primitive's activation and never model fallback.
5. **Atomic activation at settlement.** Exactly one settlement transaction
   both (a) inserts the append-only settlement row and (b) calls
   `provider.activate(conn, evidence_ref)`. Activation creates a unique
   append-only activation marker (never a mutation of the reserved material).
   After activation, `reconstruct()` returns `"state": "active"` with the SAME
   `evidence_ref` and `evidence_sha256` (the sha covers only the immutable
   reserved material, never lifecycle state). `_settle_and_activate` reads
   back the independent marker through `reconstruct()` before commit.
6. **Independent lifecycle witness.** `reconstruct()` MUST derive `reserved` /
   `active` from provider-owned durable reservation and activation-marker
   records keyed by `evidence_ref`; it MUST NOT read or infer lifecycle state
   from `inference_parent_stop_handoff_settlements` (that would make the
   service's expected-state check circular). The service's check: no
   settlement ⇒ expect `reserved`; settlement ⇒ expect `active`. A mismatch
   in either direction (early activation without settlement; missing
   activation despite settlement) is
   `inference_parent_stop_handoff_integrity_invalid`, on every path —
   including the settled-replay path of `reconcile_stop_handoff`, which MUST
   validate the stored settlement and then reconstruct with expected
   `active` before returning.
7. **Crash windows.** Reserve and settlement are each single SQLite
   transactions over conn-only provider writes, so the only observable states
   are: nothing; reserved+pending; reserved+pending after crash-and-restart
   (still inert); active+settled. No window exists where activation is
   durable without its settlement row or vice versa. Fault injection at each
   boundary (before settlement insert, after settlement insert, during
   activation) must leave no settlement, no active job, zero egress.
8. **Replay idempotence and settlement insert law.** Replayed settlement
   (same command) validates the stored identical settlement and returns it —
   it never re-activates. A conflicting existing settlement row refuses.
   Never `INSERT OR IGNORE`: return validated identical replay, refuse
   conflict, never silently ignore.
9. **Executable proof.** The proof provider persists *runnable* displaced
   work as three provider-owned structures: immutable
   `test_displaced_jobs` reservation rows; a unique append-only
   `test_displaced_job_activations(evidence_ref)` marker; a unique
   append-only `test_displaced_job_runs(evidence_ref)` claim/run receipt.
   `run_displaced(conn)` atomically inserts the run receipt only when the
   activation marker exists; it never mutates the reservation record; it
   records simulated egress. The matrix proves at minimum:
   - zero egress while pending, including across a simulated restart
     (fresh service instance);
   - (a) delayed old egress after indeterminate reconciliation: after
     `dispatch_intent`, reconcile to `dispatch_outcome_unknown`, then release
     a simulated old-provider egress — the replacement stays reserved and can
     never egress;
   - (b) crash/fault rollback at every reserve/settle/activate boundary;
   - (c) two-process/two-connection concurrent `reconcile_stop_handoff`;
   - (d) two-connection competing dispatchers: exactly one run receipt,
     exactly one simulated egress;
   - (e) `freeze()` returning `active` or writing nothing ⇒ whole-handoff
     rollback;
   - (f) `activate()` writing nothing or raising ⇒ whole-settlement rollback;
   - (g) forced `active` with no settlement refuses; forced `reserved` /
     missing activation marker with a settlement refuses (both directions);
   - (h) settlement effect/ref/SHA/provider-revision tamper and
     cross-command substitution refuse;
   - (i) Stop command/effect provenance tamper refuses;
   - (j) hostile-sync refusal for each new handoff table;
   - lawful settle: fenced execution reaches an activation-eligible known
     terminal ⇒ settlement activates atomically, job runs exactly once,
     replay never runs it again, and the old execution is terminal before
     the replacement ever runs.

## Contract changes

- `HandoffEvidenceProvider` gains `activate: Callable[[conn, evidence_ref], Any]`
  (required; validated callable at registration), under invariant 2's
  conn-only law.
- Evidence mapping schema `InferenceParentHandoffEvidence@1` gains mandatory
  `state ∈ {"reserved","active"}` (unshipped schema — redefined in place; no
  historical rows exist).
- `_validate_handoff_evidence(value, *, planning_reference, expected_state)`.
- `_reconstruct_handoff_evidence(conn, row, *, expected_state)` with
  `expected_state` derived by the caller from settlement presence in the same
  transaction.
- `_insert_handoff_settlement` becomes `_settle_and_activate(conn, command,
  effect, provider)` per invariants 5–8, used by both the
  immediate-`committed` path of `request_stop_handoff` and the settle path of
  `reconcile_stop_handoff`.
- `reconcile_stop_handoff` settlement precondition per invariant 4
  (activation-eligible dispositions, read from the fenced execution rows).

## Out of scope

Adopter dispatch loops and recovery-of-forever-reserved-work surfaces
(Phase B/C of the story) — this tranche ships the primitive plus its
executable proof provider only. No production entrance.

## Amendments after cold-audit round 1 (Sol, DO-NOT-RATIFY, 2026-08-22)

**A1 — Bundle seal (new law, closes audit Finding 1).** A route plan that is
a bundle member is sealed by its parent: the transaction that creates any
new route execution (every admission entrance) MUST derive the bundle
membership and parent operation from durable rows (bundle member join),
never from optional caller arguments, and MUST refuse admission unless the
kernel parent state is OPEN. After `fence_for_handoff` (CANCELLING) or any
terminal parent state, no new execution can be created on any of the
bundle's routes. Non-bundled route plans are unaffected. Executable tests:
post-handoff admission refused; post-terminal-parent admission refused;
pre-fence admission unaffected; refusal leaves no partial execution rows.

**A2 — Per-route policy fingerprints (closes audit Finding 2).**
Pre-admission resolution captures, per declaration, the resolved retry
policy fingerprint (id, revision, sha256, total_physical_attempts). The
bundle transaction compares each frozen route's policy fingerprint to the
captured one; ANY per-route mismatch refuses, even when the aggregate
budget is unchanged. The aggregate equality check remains as a second net.

**A3 — Frozen-definition projection (closes audit Finding 3).** Coordinator
projection/validation of a route's elected result MUST validate against the
frozen capability definition carried in the route's authority evidence,
not the current process registry. Historical v1 frozen routes execute
end-to-end through the coordinator using their exact historical adapters.
Executable test at the coordinator level, not adapter-only.

**A4 — Scope of the independent-witness claim (audit Finding 4, ruled a
recorded note per the owner's yolo rigor bar).** The conn-only and
independent-lifecycle-witness laws (invariants 2 and 6) are a PROVIDER
AUTHORSHIP CONTRACT. The primitive mechanically verifies: reserved-state
freeze, read-only reconstruct, write-advancing activate, settlement-derived
expected state, and ref/sha stability. It provably CANNOT verify which
tables an in-process callback read (Sol cold-audit probe 2). Providers are
composition-owned code with no trust boundary between them and this
service; hostile-provider defense is out of scope. Enforcement: per-adopter
counsel review at each Phase B–E adoption plus each adopter's own
executable proof tests (as the test provider models). Checkpoint claims are
scoped accordingly.
