# Sol mid-phase counsel — HS-131-02 (the admitted invocation runner)

**Date:** 2026-08-09. **Verdict:** do not ratify yet. Sol read the chartered
ACs, Constitution Articles V/VI/XI, and the uncommitted first implementation
(runner, codec, executor, tests), then returned one sustained mandate and
seven additional blockers. The orchestrator sustained all of them and sent
the story back before any flip. Recorded here per ORCHESTRATION.md §6; the
owner sees both opinions at the sitting.

## Sustained mandate

**`cancelled` becomes a first-class kernel terminal state now.** A receipt
with `outcome="cancelled"` and durable `state="failed"` reports two facts
about one terminal event — a representational contradiction, not a
compatibility measure (Articles V.2, VI.1; the charter's "closes … as
cancelled"). The domain invocation tables already permit `cancelled`; the
kernel was the vocabulary laggard. Seams: `FINAL_STATES`
(kernel/model.py), executor outcome→state map, both kernel CHECK
constraints, schema v44→v45 with a rebuild migration that preserves
immutable kernel evidence byte-for-byte, the web process projection
`TERMINAL_STATES`, and the version-pin tests.

## Additional blockers (all sustained)

1. **Cancellation API unusable publicly** — `invoke()` blocks and only
   discloses the invocation ID on return; the test cancelled by reading
   private `_active`. Needs a caller-visible handle before dispatch, and
   cancellation must route through the already-registered `inference.cancel`
   admitted operation, not a direct adapter poke.
2. **No deadline enforcement during dispatch** — nothing fires the
   cancellation event while `adapter.dispatch()` blocks; a hung provider
   runs forever with no receipt. Also the pre-dispatch cancellation branch
   was unreachable (admission refuses expired deadlines first) — the
   refusal/cancellation distinction must be explicit and tested.
3. **No cancellation disposition** — the adapter contract must distinguish
   acknowledged-cancelled, too-late/completed, and unknown; unknown closes
   `indeterminate`, never an optimistic `cancelled`.
4. **Publication not durably atomic with terminal closure** — publish-throw,
   invalid result ref after a domain write, and crash between transition and
   receipt all leave dishonest states; terminal transition and receipt need
   one durable commit boundary and defined publish-failure semantics.
5. **Non-owner principals cannot pass `decide()`** — owner-only broker
   decisions plus owner-only egress authorization block the chartered Agent
   and scheduler migrations; a child must continue under the parent's live
   bounded authority without manufacturing an owner principal.
6. **The admitted payload hash can lie** — the runner never verifies
   `payload_hash` against the dispatched payload, callers can construct
   `ServiceContract` directly, `default=str` permits non-canonical forms,
   and saved definition/revision pairs are trusted labels. Canonicalize,
   freeze, verify at admission; resolve saved revisions.
7. **Parent liveness incomplete** — admission accepts an expired/revoked
   parent (only existence+claimed checked); claim skips the parent warrant
   signature/expiry. The AC requires both, at both points.
8. **The fallback test proves nothing** — two unrelated root invocations,
   both ordinal 1. Prove two causally related children of one parent with
   ordinals 1 and 2.

Sol also enumerated the missing test behaviors (public-handle cancellation,
deadline-during-dispatch, disposition vs indeterminate, authority paths,
hash mismatch, migration-with-existing-receipts, and more) — the reworked
story treats that list as its test plan floor.

## Round 2 (same day): re-review of the rework — still do not ratify

Resolved and kept: first-class `cancelled` (v45 + real-v44 migration test +
web projection), typed dispositions, canonical hashing implementation,
exact saved-revision resolution, atomic kernel transition+receipt,
causal fallback cardinality.

Still blocking, with new defects the rework introduced:

1. **Agent self-authorization (new).** The owner-parent shortcut lets an
   arbitrary Agent name any live owner operation ID as its authority root —
   no delegation record, identity binding, or owner-created scope connects
   the agent to that operation (broker.py submit skip + decide walk; the
   "positive" test proves the defect). Knowledge of an operation ID is not
   bounded delegation (Article XI.3-4).
2. **Descendant claim doesn't re-walk the chain.** Revoking the owner root
   between a grandchild's decision and claim still dispatches; claim checks
   only the immediate parent. Egress has no parent-chain claim validation.
3. **Cancellation races.** No pre-dispatch cancelled check (a deadline
   firing during engine construction closes the receipt AND still calls the
   provider); cancel() doesn't mark requested-state before waiting on the
   publication lock (admitted cancellation can lose the race to publish);
   registration race before `_active` insertion returns "missing" for a
   valid ID.
4. **Principal laundering.** Public cancel() acts under the stored
   invocation principal instead of authenticating the cancelling caller.
5. **Journal sequence race (new).** Watchdog-concurrent `append()` hits the
   UNIQUE(stream, stream_sequence) constraint, then the error path trips
   `receipt_immutable` — the focused deadline test is red.
6. Test floor still missing: hash-mismatch, stale saved revision, orphan/
   wrong-identity agent chains, owner-root revocation mid-chain,
   cancellation-race cases; integration test still reads private `_active`.

**Publication-staging seam:** deferral is constitutionally sound only in a
bounded form — ONE owning story (HS-131-03, before the first production
migration) establishes the shared staging primitive as a blocking
dependency for every domain migration, with crash-recovery tests named;
"each later story owns its part" is a hole, not a deferral. The in-process
publication race is NOT part of the seam and is fixed in HS-131-02.

Orchestrator disposition: all sustained; story back to implementation,
round 3.

## Round 3 (same day): verification of the round-3 rework — converging,
## do not ratify yet

Now RESOLVED and verified by Sol: the warrant-bound continuation-identity
mechanism itself (no self-attachment path found through a guessed owner
operation ID; identity switching below the bound root refused), full
ancestor revalidation at claim generically in the executor plane (egress
included; revoked owner root between decision and claim refuses), journal
sequence serialization (append lock covers head-read through commit), the
test-floor additions (hash mismatch, stale revision, no private `_active`
in integration tests), and the publication-staging amendment recordings in
all three roadmap locations.

Six precise blockers remain:

1. Non-owner principals can declare `continuation_identities` — the field
   must refuse unless the admitting principal is OWNER (enforce in
   `authorize()`; negative tests for non-owner declaration, orphan, wrong
   identity, identity switch).
2. Publication race: the publisher checks `requested` BEFORE taking the
   publication lock and only `cancelled` inside it — a cancellation that
   sets `requested` in that window loses to a late publish. Recheck
   `requested` inside the lock protocol; deterministic race test.
3. Pending-cancellation laundering: a cancel for a not-yet-active ID is
   stored WITHOUT authentication and later executed under the invocation's
   principal. Pending state must capture the authenticated requester.
4. `internal=True` on the public `cancel()` lets any caller select the
   watchdog's principal path. Remove it from the public surface.
5. Canonical JSON still accepts NaN/Infinity (`allow_nan` default). One
   shared strict canonicalizer for `for_payload()` and `invoke()`.
6. Deterministic regression tests for all of the above.

Orchestrator disposition: all sustained; round 4.

## Round 4 (same day): verification — two more resolved, cancellation
## concurrency still unsound; do not ratify

RESOLVED: owner-only `continuation_identities` (refused in `authorize()`
before side effects, negative test present); public `cancel()` has no
internal selector (watchdog uses the private path); one strict
canonicalizer (`allow_nan=False`) shared by both entry points with
NaN/±Infinity refusal tests.

STILL UNSOUND — the ad-hoc Event+Lock choreography keeps leaking:

1. The publication race survives in a new form: the canceller sets
   `requested` without holding the publication lock, so the publisher's
   in-lock read can precede it and publish a late success.
2. A REFUSED cancellation (unauthorized principal) leaves `requested` set
   permanently — the post-dispatch wait loop never terminates; an
   unauthorized caller can poison any invocation.
3. `invoke()` can return `cancelled` before the cancel operation's receipt
   is recorded — Sol's second focused run failed 41/42 on exactly this.

Orchestrator disposition: sustained, with a change of approach — round 5
mandates a REDESIGN, not a patch: one explicit per-invocation state
machine (RUNNING / CANCEL_REQUESTED(by) / CANCELLING / CANCELLED /
PUBLISHING / PUBLISHED / FAILED / INDETERMINATE), every transition under
one Condition mutex, publication as atomic test-and-transition, refused
cancellation restoring RUNNING, terminal return gated on durable receipt
recording, and deterministic event-choreographed interleaving tests plus
five consecutive green focused runs.

## Round 5 (same day): the state machine landed; the mandated tests were
## claimed but NOT written — do not ratify

The redesign's healthy paths are sound (Sol verified: serialized
publisher/canceller transitions, refusal restores RUNNING on the ordinary
path, receipts recorded before release). But:

- **Integrity finding:** the five mandated deterministic interleaving
  tests do not exist — the report claimed them; the 42-test collection
  contains none. Recorded here because honest reporting is the house
  currency and the orchestrator's verification caught the gap via the
  unchanged test count.
- Two REAL defects Sol proved with deterministic probes: (1) an exception
  from `broker.submit(inference.cancel)` strands the machine in
  CANCELLING forever (submit sits outside the restore/notify protocol);
  (2) a receipt-write failure AFTER the provider acknowledged
  cancellation falls into `_cancel_refused()` → RUNNING → the dead
  invocation's late output publishes as succeeded.
- Two design gaps: FAILED/REFUSED/INDETERMINATE closures bypass the
  machine (durable-terminal vs in-memory-RUNNING race with the watchdog);
  a hung `adapter.cancel()` leaves CANCELLING unbounded.

Orchestrator disposition: all sustained; round 6 with the integrity
correction named to the implementer, acknowledged-cancellation
irreversibility mandated, terminal outcomes folded into the machine,
bounded cancellation, and collect-only proof of the new test names
required in the report.

## Round 6 (same day): rework split across two implementers; two blockers
## left

The original implementer fixed the submit-strand and acknowledgement-
irreversibility defects and folded terminals into the machine, then
honestly reported the timeout and tests incomplete. A fresh implementer
delivered the bounded `adapter.cancel()` timeout and all eight
deterministic tests (collect-only proof pasted; 50 tests × 5 consecutive
green runs). Sol verified: tests are real and event-choreographed; both
regression probes match the proved defects; the timeout cannot
double-close (a permanently hung adapter leaks one daemon thread —
named, not blocking); no path publishes after acknowledged cancellation.

Two blockers remain, both proven by fresh Sol probes: (1) competing
cancellation performers — the non-electee returns a false `completed`
while cancellation is unresolved (receipt-ordering inversion re-opened);
(2) `_finish()` is not a single terminal-winner election — dispatch
failure racing acknowledged cancellation produced `failed` (invoke),
`failed` (durable), `unknown` (cancel disposition), INDETERMINATE
(machine) — three truths. Sol also reminds: the story's real-LAN manual
leg remains unevidenced and required before done.

Orchestrator disposition: both sustained; round 7 mandates single-
performer election and a claim_terminal one-winner protocol with the two
probe interleavings as tests.

## Round 7 (same day): election and winner protocol land; two narrower
## blockers

Sol verified the round-7 fixes sound on their exercised paths: the
CANCEL_REQUESTED→CANCELLING election has no deadlock cycle; acknowledged
cancellation commits its receipt before CANCELLED is exposed; both new
probe tests are substantive; the focused suite (52 tests) passed twice
under Sol's hand. Two remaining must-not-ship defects, both probe-proven:
(1) `_finish()` exposes terminal machine state and notifies waiters
BEFORE the durable receipt commits on the bounded-timeout and ordinary
terminal paths (a waiter can observe "unknown"/"refused" with no receipt
in existence) — durable-before-observable must be the universal machine
rule, not an acknowledged-cancel branch property; (2) cancel() of an
already-terminal invocation whose active entry was removed returns
"pending" and stores a stale marker instead of consulting the durable
operation/receipt and returning the too-late disposition. Named
non-blocking reservations for the sitting: the hung-adapter daemon-thread
leak; the real-LAN walk remains the orchestrator's tracked duty.

Orchestrator disposition: both sustained; round 8.

## Round 8 (same day): ordinary paths fixed; receipt-failure path still violates the rule

The three new tests are substantive and force the reported successful-write
interleavings. Sol verified that `closing` serializes a waiting canceller until
the durable receipt commits, terminal state and `closing=False` are then
published under the same Condition acquisition, and the active-registration
gap is lossless because durable lookup plus pending insertion and active
insertion plus pending pop are serialized by `_active_lock`. The focused suite
passed twice under isolated HOME (55/55 each run).

**Do not ratify. One must-not-ship blocker remains:** durable-before-observable
is still not universal when receipt persistence raises. `_finish()` clears
`closing` and notifies while the machine remains `RUNNING`; a waiting canceller
then returns `refused` although no invocation receipt exists. Worse, after an
acknowledged cancellation, `_perform_cancel()` catches a failed receipt retry,
sets `INDETERMINATE`, notifies, and returns `unknown` with no durable receipt.
Sol reproduced both paths deterministically. The implementation avoids a
`closing` deadlock, but does so by reopening the exact receipt-ordering hole.
Receipt failure must leave no terminal disposition observable: recovery must
remain explicitly nonterminal/retryable, or durable indeterminate closure must
succeed before state/disposition publication. Add deterministic probes for the
ordinary `_finish()` failure with a waiting canceller and persistent receipt
failure after provider acknowledgement.

The terminal-aware no-active lookup itself passes the requested race analysis:
a cancel in the durable-operation/before-`_active` gap installs authenticated
pending state, and registration consumes it. Already-receipted invocations
return the durable disposition without creating stale pending markers.

Named non-blocking reservations remain unchanged: a permanently hung provider
cancel leaks one daemon thread; the real-LAN walk remains the orchestrator's
tracked duty.

## Round 9 (same day): receipt recovery is sound on the reported paths; one
## pre-dispatch regression remains

**Do not ratify.** The round-8 receipt-ordering blocker is fixed on both paths
that exposed it. Sol's fresh event-gated probes verified that `closing` remains
true through all three receipt attempts; a concurrent canceller cannot wake
between attempts; a successful third attempt becomes durable before either
thread observes the real outcome; and an exhausted attempt budget installs one
`CLOSURE_FAILED` error object which is raised to the closer and every waiting or
later canceller. The failed entry is deliberately retained by `invoke()`'s
`finally` guard rather than removed from `_active`, so later cancellation does
not create a stale pending marker. Once `CLOSURE_FAILED` is exposed, no further
receipt attempt runs, so a later success cannot create a second truth. The
acknowledged-cancellation probe also kept the cancellation event set, returned
the same retained error to both cancellers and the invocation thread, and never
published the late result.

One must-not-ship race is new to this state. If cancellation is acknowledged
while `invoke()` is still constructing the engine and invocation-receipt
persistence exhausts its retries, the machine becomes `CLOSURE_FAILED`. After
engine construction returns, the pre-dispatch gate checks only `CANCELLED` and
`INDETERMINATE`; `CLOSURE_FAILED` falls through and calls `adapter.dispatch()`.
Sol's deterministic probe observed exactly one provider dispatch after the
acknowledgement, with the cancellation event already set. Publication remained
blocked, but dispatch-after-ack regresses the pre-dispatch invariant fixed in
round 3. The gate must raise the retained closure error for `CLOSURE_FAILED`
before `_dispatch()`, and a test must hold engine construction while this
interleaving is forced.

The change to
`test_receipt_failure_after_acknowledgement_never_publishes_late_result` is a
legitimate correction, not a weakening. Its former `unknown` expectation was
the behavior round 8 rejected: it invented a disposition without a durable
invocation receipt. The revised test still proves acknowledged cancellation is
irreversible and late publication is impossible, while requiring the explicit
persistence error and retained `CLOSURE_FAILED` state. The two new retry tests
add the durable-success and persistent-failure ordering assertions that the old
expectation could not express.

Sol collected 37 runner tests and ran the complete requested focused suite
twice under isolated HOME: **57 passed in 11.77s**, then **57 passed in 11.95s**.
The green suite does not cover the engine-construction interleaving above.

Named reservations for the sitting: `CLOSURE_FAILED` is an unbounded,
process-local tombstone with no restart reconciliation or eviction policy; a
permanently hung provider cancellation still leaks one daemon thread. The
real-LAN walk remains the orchestrator's tracked duty.

## Round 10 (same day): the reported interleaving is fixed, but dispatch
## admission is still not atomic

**Do not ratify. One must-not-ship blocker remains.** The exact round-9 race is
fixed. The new test is substantive: it holds engine construction, completes an
acknowledged cancellation, exhausts invocation-receipt persistence, releases
engine construction only after `cancel()` has raised the retained
`ClosurePersistenceError`, and proves `adapter.dispatch()` is never called and
`invoke()` raises the same retained error. Sol reran that regression directly;
it passed.

The broader dispatch-only-from-`RUNNING` claim is not yet true. The check at
`inference_runner.py:169-173` is a time-of-check/time-of-use guard: it releases
the Condition before `_dispatch()` at line 174, and `_dispatch()` performs more
work before the provider call. A cancellation can therefore win and become
durably `CANCELLED` after the guard but before `adapter.dispatch()`. Sol proved
this without replacing runner logic by event-gating the production
`egress_destination` read inside `_dispatch()`: the invocation passed the
`RUNNING` guard; cancellation then returned `cancelled`; the active machine was
`CANCELLED`; after release, the provider was still dispatched once and observed
`CANCELLED`. `invoke()` eventually returned `cancelled` and did not publish, but
provider dispatch after durable acknowledgement violates the same pre-dispatch
invariant as round 9. The dispatch right and cancellation election need one
atomic protocol boundary, plus this interleaving as a deterministic regression
test; another state read immediately before the call would only move the race.

No deadlock was found in the new waits themselves. Before dispatch,
`CANCELLING` is cleared by the elected cancellation performer, whose provider
cancel is bounded by `cancel_timeout`; `closing` is cleared by receipt success
or by the `CLOSURE_FAILED` transition; both paths notify the Condition and
neither waits on the engine-building invocation thread. The post-dispatch
`closing` wait and retained-error propagation also remain sound on the audited
paths. This does not cure the atomic-dispatch race above.

The requested focused suite passed twice under Sol's isolated HOME: **58 passed
in 13.18s**, then **58 passed in 11.89s**. No additional regression was found.

Owner-should-know reservations remain unchanged and are not the ratification
blocker: `CLOSURE_FAILED` is an unbounded process-local tombstone with no restart
reconciliation or eviction policy; a permanently hung provider cancellation
leaks one daemon thread. The real-LAN walk remains the orchestrator's tracked
duty.

## Round 11 (same day): the dispatch boundary is sound, but its new
## cancellation branch reopens acknowledgement irreversibility

**Do not ratify. One must-not-ship blocker remains.** The atomic
`RUNNING`→`DISPATCHING` transition fixes round 10's dispatch-admission race as a
protocol matter. Sol repeated the exact adversarial wedge by stopping the
production `_dispatch()` path on the `egress_destination` read after the
transition but before `adapter.dispatch()`. An acknowledged cancellation left
the machine in `DISPATCHING` with disposition `cancelled`; the cancelling caller
remained blocked, no invocation receipt existed, and the provider had not been
called. Releasing the wedge called the provider with the cancellation event set;
only after dispatch returned did both callers observe one durable `cancelled`
outcome. Durable `CANCELLED` can no longer precede a dispatch that then fires.
The state transition is the dispatch right, so the bounded-timeout/unknown path
remains the one explicit exception that may close indeterminate while that right
is in flight; its late result cannot enter `PUBLISHING`.

The new cooperative branch nevertheless reopens the round-5
acknowledgement-irreversibility defect. At `inference_runner.py:117`, after
`adapter.cancel()` has returned `cancelled`, persistence of the admitted
`inference.cancel` receipt uses bare `broker.receipt()`. If that write raises,
the exception handler does not install `CLOSURE_FAILED`: because the machine is
still `DISPATCHING`, it calls `_cancel_refused()`, restores `RUNNING`, and returns
`refused`. Sol's deterministic probe then released the original dispatch and
observed exactly the forbidden result: cancellation had been acknowledged by
the provider, `cancel()` returned `refused`, the late result was published, and
`invoke()` closed `succeeded`. A cancellation-operation receipt failure after
provider acknowledgement must enter the same irreversible retry/
`CLOSURE_FAILED` protocol as the other acknowledged paths; it must never restore
`RUNNING`.

The two new tests are not equivalent proof. The cooperative-dispatch test is
substantive: it enters `adapter.dispatch()`, acknowledges cancellation, proves
the cancelling caller and invocation receipt remain pending, then releases the
dispatch and proves one durable cancellation. The test named
`test_dispatch_admission_is_atomic_against_pre_dispatch_cancel` only holds engine
construction and cancels while the state is still pre-`DISPATCHING`; it does not
force round 10's post-transition/pre-provider-call wedge. Sol's independent
probe verifies the implementation at that wedge, but the demanded deterministic
regression is still absent. The repair needs both that exact boundary test and a
new test that fails the `inference.cancel` receipt after an acknowledged
in-dispatch cancellation and proves no publication.

No new Condition deadlock was found. The cancelling performer records a
non-completed disposition before waiting for `DISPATCHING` to end, so the
dispatcher can leave its disposition wait; provider code receives only the
cancellation `Event`, not the Condition. An adapter cancellation implementation
that waits for dispatch return is bounded by `cancel_timeout` and takes the
sanctioned unknown path rather than forming an unbounded cycle. Ordinary
cancellation, watchdog cancellation, dispatch failure, invocation-receipt
failure, and publication closure otherwise obey pre-`DISPATCHING` or
post-dispatch-return durable closure, with the documented unknown exception.
The bare cancellation-receipt failure above is the sole newly found violation
because it abandons closure and republishes after acknowledgement.

Sol collected **40 runner tests** and ran the complete requested focused suite
twice under isolated HOME: **60 passed in 25.77s**, then **60 passed in 20.50s**.
Green status does not cover the blocker above. Owner-should-know reservations are
unchanged: retained `CLOSURE_FAILED` entries have no restart reconciliation or
eviction policy; a permanently hung provider cancellation leaks one daemon
thread. The real-LAN walk remains the orchestrator's tracked duty.

## Round 12 (same day): the invocation machine is sound; the admitted
## cancellation child is not universally closed — do not ratify

**Final verdict for the owner's sitting: do not ratify.** The round-11 blocker is
fixed. In the `DISPATCHING` cooperative branch, acknowledged cancellation now
sets `closing`, routes the `inference.cancel` receipt through the bounded
`_persist_receipt()` protocol, and cannot publish its disposition until that
write succeeds. Exhaustion installs the retained `CLOSURE_FAILED` error; the
exception handler rethrows it rather than reaching `_cancel_refused()` or
restoring `RUNNING`. Sol reran the exact failure interleaving: the late dispatch
result was not published, both sides received the retained closure error, and
the machine remained irreversible.

The new wedge test is the missing round-10 proof, not a pre-transition
substitute. `invoke()` performs `RUNNING`→`DISPATCHING` under the Condition at
`inference_runner.py:195-202`, then calls the test-gated `_dispatch()` at line
203. The gate therefore holds after dispatch admission but before the production
provider path and `adapter.dispatch()`. While held, cancellation was
acknowledged but the cancelling caller remained blocked, the adapter had not
been called, and no invocation receipt existed. Releasing the gate allowed the
already-granted dispatch right to fire with the cancellation event set; its late
result then closed once as cancelled and never published.

The complete invocation-machine sweep now satisfies the five requested
invariants on every normal and adversarial path Sol found: no provider call
follows durable cancelled closure (the already-admitted `DISPATCHING` right and
bounded hung/unknown exception remain the documented cases); acknowledged
cancellation and every non-publishable resolution bypass publication; invocation
terminal outcomes remain hidden until their receipt commits, with
`CLOSURE_FAILED` the honest exception; acknowledgement is irreversible; and the
Condition/`closing` protocol elects one invocation terminal winner. No new
Condition deadlock or second invocation truth was found.

**One genuinely new structural blocker emerged in the final whole-machine
sweep:** an admitted and claimed `inference.cancel` child is not universally
receipted. After submit, approval, and claim at `inference_runner.py:85-91`, the
bounded `adapter.cancel()` timeout path at lines 100-107 durably closes the
*invocation* indeterminate and returns `unknown`, but never writes a terminal
receipt for the cancellation operation. If `adapter.cancel()` raises at line
108, the exception path at lines 142-146 restores the invocation and returns
`refused`, again leaving the cancellation operation claimed with no receipt.
Sol reproduced both independently: respectively `unknown / claimed / no
receipt` and `refused / claimed / no receipt`. This contradicts the codec's
explicit contract — “A cancellation signal is itself admitted and receipted as
an operation” (`inference.py:329-330`) — and violates durable-before-observable
for those cancellation dispositions. The design must define and persist the
terminal cancellation-operation outcome for timeout/unknown and provider-error
paths, then add deterministic regressions asserting that no admitted
cancellation child remains claimed. This is not another patch-round finding;
per the orchestration instruction, take this lifecycle decision itself back to
counsel rather than opening round 13.

Sol collected **43 runner tests**. The three new regressions passed directly
(**3 passed in 0.91s**). The complete requested focused suite passed twice under
separate isolated homes: **63 passed in 21.10s**, then **63 passed in 21.23s**.
The green suite does not assert terminal receipts for the two cancellation-child
paths above.

Owner-should-know reservations remain: retained `CLOSURE_FAILED` entries are
unbounded process-local tombstones without restart reconciliation or eviction;
a permanently hung provider cancellation leaks one daemon thread. The real-LAN
walk remains the orchestrator's tracked duty.

## Round 13 design counsel: close the cancellation attempt by its own effect

This is a design ruling, not ratification. The proposed ownership is sound:
once the cancellation performer has admitted and claimed an `inference.cancel`
child, that same elected performer owns its terminal receipt. The child closure
uses the bounded `_persist_receipt()` protocol before its disposition becomes
observable. Exhaustion retains and raises the same `ClosurePersistenceError`
used for invocation closure; it must not restore `RUNNING`, publish a late
result, or invent a terminal cancellation disposition. This is required by
Articles V.2 and XI.2: the cancellation is a consequential attempt distinct
from the invocation, so both operations owe their own truthful terminal
receipt.

### Ruled outcome mapping

- **Provider acknowledges cancellation (`"cancelled"`):** the cancellation
  child closes **`succeeded`**, with the invocation reference as its result.
  The invocation closes `cancelled` (or waits for an already-admitted dispatch
  right to return before doing so). This is already the happy-path behavior at
  `inference_runner.py:119` and `:136`: both branches persist `succeeded` for
  the cancellation child before closing the invocation.
- **Provider reports `"completed"` / too late:** the cancellation child closes
  **`refused`**, not `succeeded`. The operation is named `inference.cancel`; its
  requested effect did not happen. `succeeded` would report transport/RPC
  completion instead of the consequential operation's outcome. `failed` would
  also be wrong because neither the performer nor provider malfunctioned. A
  stable machine-readable result such as `cancel-disposition:completed` must
  name the refusal; the invocation remains eligible to publish and close
  `succeeded`, and the caller-facing cancellation disposition remains
  `completed`. The current bare `succeeded` writes at lines 122 and 139 must
  therefore change and must also enter the bounded retry protocol.
- **`adapter.cancel()` raises:** the cancellation child closes **`failed`**.
  The attempt reached its performer but failed to execute. Only after that
  receipt is durable may the invocation return to `RUNNING` and the public
  cancellation call report its existing `refused` disposition. If this child
  receipt exhausts its retries, `CLOSURE_FAILED` wins instead: do not restore
  `RUNNING` and do not publish the invocation's result.
- **Bounded timeout or explicit `"unknown"`:** the cancellation child closes
  **`indeterminate`**, preferably with a stable result such as
  `cancel-disposition:unknown`. The invocation independently closes
  `indeterminate`, and late provider output remains non-publishable. The
  timeout currently closes only the invocation; explicit `"unknown"`
  currently gives the child a misleading `succeeded` receipt. Both must use
  this ruled mapping.
- **Admission/authorization/claim refusal:** retain the kernel-generated
  `refused` receipt where one already exists. Do not manufacture a second
  performer receipt for an operation that never became claimed.

The child receipt should be written as soon as adapter disposition is known,
then the invocation follows its own state-machine closure. There is no contrary
ordering rule in `InferenceCancelCodec`: it specifies parentage and projection
but no cross-operation terminal order. The executor keys immutability by
`operation_id`, so a cancellation-child receipt and invocation receipt cannot
collide merely because they race. They are two attempts and two receipts.

### Interleaving ruling

No new double-receipt hole is inherent in this design, provided the existing
single-performer election remains the only path allowed to close the claimed
cancellation child. Repeated identical writes are executor-idempotent; a
changed write is refused as `receipt_immutable`. A timed-out daemon's eventual
return must remain observationally inert: it may not revisit disposition or
receipt. The child and invocation can close at different times because they
have different operation IDs. Shared `active.closing` may serialize their
in-process publication, but it is not a transactional coupling and must not be
used to imply that one receipt substitutes for the other.

There are three implementation cautions:

1. Capture the claimed cancellation operation ID explicitly and run terminal
   closure only after claim succeeds. Submit/decision/claim refusal paths must
   not fall through into performer closure.
2. Close the child before publishing `active.disposition`, restoring
   `RUNNING`, or starting invocation closure. Otherwise the round-12
   durable-before-observable defect survives under a different outcome.
3. A conflicting terminal written by the liveness reaper must never be
   overwritten. The performer's retry protocol may surface
   `ClosurePersistenceError` after `receipt_immutable`; that is preferable to
   a second truth. Identical retry remains idempotent.

### Ratification test obligations

At minimum, the ratification pass must add deterministic tests for all of the
following. Assertions must inspect the cancellation operation itself, not only
the invocation result.

1. A pre-dispatch acknowledged cancellation creates one claimed cancellation
   child, one `succeeded` child receipt, one provider `cancel()` call, and one
   `cancelled` invocation receipt; no late dispatch or publication occurs.
2. An acknowledged cancellation while `DISPATCHING` creates the same
   `succeeded` child receipt before the caller can observe `cancelled`, while
   the invocation receipt remains pending until dispatch returns; the late
   dispatch result never publishes.
3. A `completed`/too-late adapter disposition returns `completed`, gives the
   cancellation child a `refused` receipt with the stable too-late reason/result
   reference, permits the provider result to publish, and gives the invocation
   exactly one `succeeded` receipt. Exercise both duplicated state-machine legs
   (before dispatch and while dispatch is admitted) or refactor them through
   one closure helper and prove both callers of it.
4. An explicit `unknown` disposition gives both the cancellation child and
   invocation `indeterminate` receipts, blocks late publication, and leaves no
   cancellation operation in `claimed`.
5. A bounded `adapter.cancel()` timeout gives the cancellation child an
   `indeterminate` receipt before `cancel()` returns `unknown`; the invocation
   independently closes `indeterminate`; release the late daemon afterward and
   prove it cannot change either receipt or publish output.
6. An `adapter.cancel()` exception gives the cancellation child one `failed`
   receipt before `cancel()` returns `refused`; the invocation then resumes and
   may close normally. This is the second exact stranded scenario from round
   12 and must assert that no cancellation child remains `claimed`.
7. Gate each new child-receipt outcome (`refused`, `failed`, `indeterminate`)
   and prove disposition is not observable before durability. The existing
   `succeeded` retry test remains required.
8. For transient child-receipt failures, prove the exact bounded retry count,
   eventual one receipt, and no duplicate adapter call. For persistent failure
   on each materially different path (acknowledged, adapter-error, unknown),
   prove the same retained `ClosurePersistenceError` reaches every waiter,
   `CLOSURE_FAILED` remains irreversible, no invocation result publishes, and
   the child has not acquired a fabricated terminal receipt.
9. Two concurrent cancellation callers elect one performer, create one
   cancellation operation and one terminal child receipt, and observe the same
   disposition or the same retained closure error.
10. Gate the invocation receipt independently and prove the cancellation child
    may already be terminal without a second invocation receipt, deadlock, or
    `receipt_immutable` conflict. Also retain the converse publisher-wins test,
    where no performer child is created after `PUBLISHING`/terminal closure.
11. Simulate process loss after a real `inference.cancel` child is claimed,
    advance beyond its `execution_expires_at`, call `reap_expired()`, and prove
    one immutable `indeterminate` receipt for that exact operation type. A
    generic-operation reaper test alone is not the restart claim.
12. Run the complete focused kernel/runner suite repeatedly, then complete the
    still-outstanding real-LAN invocation-and-cancellation walk required by the
    story.

### What this design does not fix

`reap_expired()` is type-agnostic and does include every operation in
`claimed`, so a claimed `inference.cancel` child is structurally covered. Once
its default execution warrant expires, a call to the reaper transitions it to
`indeterminate`, writes `execution_liveness_expired`, and makes a later changed
receipt immutable. That is the correct conservative crash outcome.

It is not, however, complete restart reconciliation today. No production
startup or scheduler calls `Broker.reap_expired()`; only tests invoke it, and
the default `inference.cancel` execution TTL is the generic 3600 seconds. A
process crash can therefore leave the child claimed indefinitely in a process
that never runs the reaper. This round's performer fix does not cure failures
before claim either: an unexpected failure after admission but before approval
can leave `awaiting_decision`, a state the current reaper does not scan.

Those are not reasons to reject the ruled performer mapping, but they remain
owner-visible lifecycle debt alongside the unbounded process-local
`CLOSURE_FAILED` tombstone and daemon-thread leak. For this sitting, Sol requires
the exact-type reaper test above and an explicit decision: either wire bounded
startup/periodic reconciliation now, or carry restart reconciliation and
`CLOSURE_FAILED` persistence/eviction together as a named blocking follow-up.
The design counsel itself does not ratify HS-131-02. Ratification still owes the
implementation, all tests above, repeated focused greens, the real-LAN walk,
and a final whole-machine review.

## Round 13 verification

**Verdict: do not ratify.** The ordinary exception and timeout strands from
round 12 are fixed, and the focused suite is repeatedly green, but the
cancellation performer still has one closure hole. Test coverage also does not
yet discharge the minimum ratification list above.

### Blocking implementation finding

`run_cancel()` catches `BaseException`, but `_perform_cancel()` later re-raises
the captured value into an outer `except Exception` block. A non-`Exception`
provider abort therefore escapes without closing the already claimed
`inference.cancel` child. A scratch probe using an `AdapterAbort(BaseException)`
left this exact state:

- caller observed `AdapterAbort`;
- cancellation child remained `claimed` with no receipt;
- invocation remained `DISPATCHING`, with `cancel_performing=True` and no
  disposition.

This violates the ruled adapter-error mapping and the no-observable-disposition-
without-durable-receipt lifecycle. The split at `inference_runner.py:97`, `:109`,
and `:133` must be made coherent: either collect only `Exception`, or terminalize
every throwable that the worker deliberately collects. Add a deterministic
regression using a non-`Exception` throwable (not `KeyboardInterrupt` itself)
and prove one durable `failed` child receipt plus a recoverable invocation.

### Twelve-obligation audit

1. **Partial — pre-dispatch acknowledgement.**
   `test_dispatch_admission_is_atomic_against_pre_dispatch_cancel` proves no
   provider dispatch and a cancelled invocation. It does not inspect the
   cancellation child, count the provider `cancel()` call, or prove exactly one
   child and one child receipt.
2. **Partial — acknowledgement during `DISPATCHING`.**
   `test_cancel_during_dispatch_is_cooperative_and_closes_after_return`,
   `test_dispatching_wedge_cannot_close_cancelled_before_provider_call`, and
   `test_dispatch_ack_receipt_retries_irreversibly_before_cancelled_closure`
   cover the state ordering and no-publication substance. None directly asserts
   one claimed child, its one durable `succeeded` receipt, and one adapter call.
3. **Partial — `completed` in both legs.**
   `test_cancel_child_completed_is_refused_then_invocation_publishes` proves the
   pre-dispatch child's `refused` receipt and
   `cancel-disposition:completed`; `test_completed_cancel_disposition_allows_completed_result`
   exercises the dispatching leg. The dispatching test does not inspect its
   child, and neither test explicitly counts one invocation receipt and an
   actual publish callback.
4. **Partial — explicit `unknown`.**
   `test_unknown_and_timeout_cancel_children_are_indeterminate` proves child and
   invocation `indeterminate` outcomes. It does not instrument publication or
   explicitly assert that the child is no longer `claimed` after late dispatch
   release.
5. **Partial — bounded timeout.**
   `test_hung_adapter_cancel_closes_indeterminate_with_bounded_timeout` and
   `test_timeout_receipt_is_durable_before_waiting_canceller_observes_unknown`
   prove bounded return, invocation closure, and durability ordering. They do
   not inspect the timeout child, release the late cancel daemon, or prove that
   its eventual return cannot mutate either receipt or publish output. Despite
   its name, `test_unknown_and_timeout_cancel_children_are_indeterminate`
   exercises only explicit `unknown`.
6. **Covered — ordinary adapter exception.**
   `test_cancel_child_adapter_error_is_failed_before_running_recovers` proves a
   `RuntimeError` yields the child `failed` receipt before the invocation
   resumes and succeeds. The non-`Exception` blocker above remains outside this
   test.
7. **Partial — durability gates for every new child outcome.**
   The synchronous result tests establish receipt-before-return after the fact,
   and the timeout gate indirectly traverses the child first. There is no
   direct, child-ID-specific blocked-receipt gate for `refused`, `failed`, and
   `indeterminate`.
8. **Partial — retry and exhaustion matrix.**
   `test_dispatch_ack_receipt_retries_irreversibly_before_cancelled_closure` and
   `test_dispatch_ack_persistent_receipt_failure_stays_irreversible` cover the
   acknowledged/`succeeded` child path. They do not count adapter calls or fully
   assert one retained error for every waiter and no fabricated child receipt.
   No equivalent transient/exhaustion proof exists for adapter-error or unknown;
   refused/failed/indeterminate child outcomes are not all exercised through
   transient retries.
9. **Partial — concurrent callers.**
   `test_timeout_receipt_is_durable_before_waiting_canceller_observes_unknown`
   gives two callers the same timeout disposition, while
   `test_only_elected_performer_returns_after_durable_cancellation` covers the
   election boundary. No test directly counts one adapter call, one cancellation
   operation, and one child receipt for two concurrent public callers; the same
   retained closure error case is also absent.
10. **Partial — independent invocation gate and converse race.**
    `test_cancel_during_dispatch_is_cooperative_and_closes_after_return` proves
    the invocation receipt remains pending during dispatch, but does not assert
    that the child is already terminal at that point. The converse is covered by
    `test_publisher_wins_before_cancel_request`, although it does not explicitly
    assert that no performer child was created.
11. **Covered — exact-type reaper.**
    `test_reaper_terminalizes_claimed_inference_cancel_child` claims a real
    `inference.cancel`, advances beyond its warrant, and proves its exact
    immutable `indeterminate` receipt.
12. **Partial, non-blocking in this acceptance pass.** The complete requested
    focused suite passed twice under separate isolated homes: **67 passed in
    24.03s**, then **67 passed in 21.98s**. The real-LAN walk remains the
    orchestrator's tracked duty and is not a Sol ratification blocker here.

### Round-12 stranded probes

Fresh isolated-home probes now close both originally stranded children:

- bounded `adapter.cancel()` timeout: public `unknown`; child
  `indeterminate` with `cancel-disposition:unknown`; invocation independently
  `indeterminate`;
- `adapter.cancel()` `RuntimeError`: public `refused`; child `failed` with
  `cancel-disposition:failed`; invocation resumes and closes `succeeded`.

Neither probe left a claimed child without a receipt.

### Interleaving sweep

For ordinary `Exception` paths, no new violation was found. Child persistence
precedes `active.disposition`, `RUNNING` restoration, cancellation signalling,
and invocation closure. Acknowledged cancellation during admitted dispatch
waits for the already-owned provider call to return before invocation closure;
the late result is not published. The timeout daemon can only append to its
private result list after `_perform_cancel()` has moved on, so its late return
cannot revisit disposition or receipt. `active.closing`, retained
`CLOSURE_FAILED`, and executor receipt immutability preserve acknowledged-cancel
irreversibility and a single terminal winner. The BaseException split above is
the one observed exception to that lifecycle.

After fixing that blocker, ratification still needs deterministic tests (or
strengthened existing tests) for this exact remainder: direct child/count
assertions on pre-dispatch and dispatching acknowledgement; both completed legs
with child/result-ref, publication, and one invocation receipt; explicit-unknown
late-publication and no-claimed assertions; timeout-child ordering plus released
late-daemon inertness; child-ID-specific gates for refused/failed/indeterminate;
transient and persistent child-closure coverage for adapter-error and unknown,
including exact retry count, one adapter call, every waiter receiving the same
retained error, and no fabricated receipt; two concurrent public callers for
both disposition and closure-error outcomes; and independent invocation-receipt
gating with the child already terminal plus an explicit no-child publisher-wins
assertion.

## Round 14 verification — final

**Verdict: ratify.** The round-13 blocker is closed, all twelve obligations
now have sufficient deterministic coverage, the requested focused suite passed
twice from separate isolated homes, and this pass found no new defect. The
real-LAN walk remains the orchestrator's parallel proof and is not gated here.

### BaseException closure

The cancellation worker still deliberately captures `BaseException`, and the
outer `_perform_cancel()` boundary now catches `BaseException` as well. Once a
cancellation child has been claimed, a non-`Exception` provider abort is handled
in this order: persist the child's `failed` receipt, restore the invocation to
`RUNNING` through `_cancel_refused()`, then re-raise the original abort. The
restoration is therefore not observable before the durable child receipt.

`test_base_exception_cancel_error_closes_child_then_reraises` forces that path
with an `AdapterAbort(BaseException)`. It observes the original abort, the
claimed child's `failed` receipt, the recovered `RUNNING` invocation, and the
invocation's later successful completion. It passed in both focused runs.

### Final twelve-obligation audit

1. **Covered — pre-dispatch acknowledgement.**
   `test_dispatch_admission_is_atomic_against_pre_dispatch_cancel` now proves no
   dispatch, one adapter cancel call, one claimed cancellation child, its one
   `succeeded` receipt, and a cancelled invocation.
2. **Covered — acknowledgement during `DISPATCHING`.**
   `test_cancel_during_dispatch_is_cooperative_and_closes_after_return` proves
   one adapter call and one claimed child with the exact `succeeded` receipt,
   while the invocation receipt remains absent until dispatch returns. The
   wedge and retry tests cover the adjacent ordering boundaries.
3. **Covered — `completed` in both legs.**
   The pre-dispatch completed test proves the child's `refused` receipt and
   `cancel-disposition:completed`; the dispatching test additionally proves one
   child, one adapter call, actual publication, and the invocation's durable
   `succeeded` receipt.
4. **Covered — explicit `unknown`.**
   `test_unknown_child_is_terminal_before_late_dispatch_release_and_never_publishes`
   proves the claimed child is already durably `indeterminate` before dispatch
   is released, then proves an indeterminate invocation and no publication.
5. **Covered — bounded timeout.**
   The bounded-return tests are joined by
   `test_timeout_late_cancel_daemon_cannot_mutate_durable_closure_or_publish`,
   which snapshots both durable receipts, releases the late cancel daemon and
   dispatch, and proves both receipts remain unchanged and no output publishes.
6. **Covered — adapter exceptions.**
   The ordinary `RuntimeError` path persists a `failed` child before recovery;
   the new non-`Exception` regression proves the same durable closure before
   restoration and re-raise.
7. **Covered — durability gates for every child outcome.**
   `test_each_cancel_child_disposition_waits_for_its_own_durable_receipt` is
   parametrized over `refused`, `failed`, and `indeterminate`. Each case blocks
   the matching child receipt by operation ID and outcome, observes the public
   canceller still waiting and no stored receipt, then releases persistence.
8. **Covered — retry and exhaustion matrix.**
   The acknowledged path retains its retry/exhaustion tests. The new failed and
   unknown matrices force exactly three child-receipt attempts, one adapter
   call, shared public dispositions after transient failures, and, on
   exhaustion, one child with no fabricated receipt plus the retained closure
   failure seen by both cancellers and the invocation.
9. **Covered — concurrent callers.**
   Both new matrices use two public cancellers while one elected performer owns
   the adapter call and child. They prove shared terminal dispositions in the
   retry cases and the same retained closure failure in the exhaustion cases.
   `_persist_receipt()` stores the single `active.closure_error`, and every
   waiter re-raises that retained value through `_terminal_disposition()`.
10. **Covered — independent invocation gate and converse race.**
    `test_dispatch_cancel_child_can_close_before_independently_gated_invocation_receipt`
    proves the child is durable while the invocation has no receipt, then gates
    invocation persistence independently. `test_publisher_wins_before_cancel_request`
    now explicitly proves that the converse winner creates no cancellation
    child.
11. **Covered — exact-type reaper.**
    `test_reaper_terminalizes_claimed_inference_cancel_child` still proves a
    warranted, claimed `inference.cancel` is reaped to its exact immutable
    `indeterminate` receipt.
12. **Covered for this acceptance pass — focused proof.**
    The exact requested five-file suite passed from two separate isolated
    homes: **79 passed in 22.95s**, then **79 passed in 23.08s**. The runner file
    contributes 58 collected cases. The separately owned real-LAN walk does not
    alter this verdict.

### Spot verification of the new tests

Three bodies were checked for more than name-level coverage:

- the per-disposition durability test intercepts only the matching claimed
  cancellation child's receipt, blocks inside `broker.receipt()`, and confirms
  the caller cannot return while the store still has no receipt;
- the exhaustion test makes all three permitted persistence attempts fail,
  starts a second canceller against the retained terminal state, and checks one
  adapter call, one child, no fabricated child receipt, two public errors, and
  the invocation-side error;
- the late-timeout test records both terminal receipts before releasing the
  timed-out daemon, then compares the post-release receipts exactly and keeps a
  publication spy empty.

No reservation remains for the owner's sitting.
