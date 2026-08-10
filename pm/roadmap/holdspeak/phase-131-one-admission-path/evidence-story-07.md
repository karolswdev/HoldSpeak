# Evidence - HS-131-07

- **Story:** HS-131-07 - The remaining direct callers join the spine
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-10T22:31:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7gGeEb8ocq uv run pytest -q tests/unit/test_voice_resolve.py tests/unit/test_rails_observer.py tests/unit/test_intel_egress_invariant.py tests/unit/test_mesh_serve_worker.py tests/unit/test_mesh_relay_provider.py tests/unit/test_mesh_relay_queue.py tests/unit/test_decision_record_service.py tests/unit/test_kernel_effect_fence.py tests/unit/test_sequence_workflow_runner_migration.py tests/unit/test_workbench_runner_migration.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e7cba26f811d096ed0582f1a3445aa7cef865270

```text
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
192 passed in 23.45s
```

## Verification narrative

### The design beat (committed separately as 35a9d5c3)

Terra drafted [DESIGN-HS-131-07](./DESIGN-HS-131-07.md); Sol ruled it
RATIFY-AS-AMENDED in ONE round with four binding amendments (explicit
non-owner rails-observer service principal with journal-only basis; trusted
parent-context propagation into every Decision/Delivery/Voice child; the
voice callable finalizes each child receipt before returning a string; a
mesh relay envelope carrying the admitted revision + warrant, killing
worker-side provider re-resolution). The design itself surfaced two latent
defects on paper: the silent owner-elevation fallback in voice resolution
(`workbench_service.py:354`) and mesh workers resolving their own
configured provider with zero admitted-revision validation.

### What shipped

- **One generic operation**: every census caller dispatches
  `inference.invoke@1` with a versioned ServiceContract
  (`holdspeak.rails-summary@1`, `holdspeak.decision-promotion-draft@1`,
  `holdspeak.delivery-pr-review@1`, `holdspeak.voice-reference-resolve@1`)
  through the broker-owned shared InferenceRunner. No domain conditional
  entered the runner or broker (kernel fence green; broker.py at 299).
- **Rails** (`rails_observer.py`): the summarizer is runner-backed under an
  explicit `PrincipalKind.SERVICE` principal (`rails-observer`, allowed
  operations = {inference.invoke@1}, `authority_basis=
  rails-observer:journal-only`) issued at hub-loop startup
  (`web_server.py`). Root invocation; the journal note is receipt-gated;
  refusal/failure degrades to the honest event-only entry. Off-by-default
  and events-only behavior preserved; the pre-existing event-read bridge
  stays as-is (Sol ruled it outside this charter).
- **Decision promotion** (`services/decision_lifecycle_service.py`): real
  domain parent `decision.promotion-draft@1` (replacing the generic
  `inference.run@1` placeholder), authenticated route principal, one child
  with the trusted parent context, and the promoted artifact written INSIDE
  the projection-finalization transaction by a real materializer
  (`kernel/rails_journal_projection.py`) — Sol ratified the materializer as
  the legitimate native write for the model-assisted path (deterministic
  promoted artifact id, causal structured body, model_assisted=true,
  decision/meeting sources); the gesture-only `promote()` path untouched.
- **Delivery PR review** (`web/routes/delivery_prs.py`): parent
  `delivery.pr-review-draft@1`; canonical payload carries the diff SHA-256
  (the diff body is dispatched, never journaled); the review artifact is
  materialized in the finalization transaction; non-success persists
  nothing and returns the classified error.
- **Voice resolution** (`services/workbench_service.py` +
  `voice_resolver.py`): the owner-elevation fallback is DELETED — a missing
  principal refuses `resolver_principal_required` before any admission.
  Each actual retry is one admitted child (attempt ordinals) whose raw
  output finalizes behind its receipt before the parser sees a string;
  deadline cancellation maps to TimeoutError; the final refs are returned
  only from a succeeded parent election (`resolver_cancelled` otherwise).
  Sol: "discharged exactly."
- **Mesh** (`intel/mesh_relay.py`, `commands/mesh_serve.py`,
  `services/mesh_service.py`, `kernel/broker.py`,
  `kernel/inference_invoke.py`): dispatch carries an envelope {admitted
  deployment revision (all frozen fields + content-addressed id), signed
  warrant}. Every warrant now signs a generic `target_binding` (the
  operation's admitted target_ref; inference operations bind
  `deployment-revision:<id>`). The WORKER refuses `mesh_envelope_missing`,
  `mesh_envelope_invalid` (tamper via content-address recompute),
  `mesh_envelope_node_mismatch`, and `mesh_envelope_revision_mismatch`
  (valid warrant paired with a swapped revision), and builds its engine
  ONLY from the frozen fields (per-revision cache; node-local secrets stay
  local; the recursion guard stands). The HUB authoritatively re-validates
  the stored warrant (signature, liveness, non-revocation, claimed state,
  expiry) AND warrant/operation/envelope revision agreement before
  accepting complete/fail results (`mesh_result_warrant_invalid`). The
  legacy "whatever provider this node currently selects" behavior is dead
  by design — it was silent retargeting. Envelope transport rides the
  existing opaque hub-local relay column (Sol: acceptable, no schema
  change needed for it).
- **Schema v53**: the `kernel_parent_runs.kind` CHECK physically rejected
  the three new domain-parent kinds; bumped with a migration (Sol:
  "necessary and ratified"). Version-pin tests updated across the known
  four extra files.
- **Census boundary**: Cadence's `get_loop` LLM call
  (`services/cadence_service.py:131`) is recorded as a NAMED HS-131-10
  fence finding requiring a charter amendment — not absorbed.

### The counsel ledger (implementation)

Sol rode THREE implementation rounds to RATIFY-WITH-RESERVATIONS:

- **Round 1** (3 blockers): mesh warrant transported but only dict-checked;
  Decision/Delivery artifact writes escaped the projection election
  (cancellation could publish under a cancelled parent); voice could return
  refs from a cancelled parent.
- **Round 2** (1 blocker): the warrant and revision were each valid but
  never bound — a valid warrant for operation A could pair with a
  different self-consistent revision B.
- **Round 3**: signed `target_binding` closed the pairing;
  **RATIFY-WITH-RESERVATIONS**, all four amendments discharged, all eight
  charter ACs pass.

### Defects caught by the layered verification

1. **Walk-caught (100% deterministic)**: the migrated review route used
   artifact source type "inference," which is not in
   VALID_ARTIFACT_SOURCE_TYPES — persistence failed on every call; fixed to
   the in-vocabulary "invocation."
2. **Orchestrator diff-read**: the delivery route and decision service
   passed the InvocationOutcome OBJECT to parent close() — on child
   failure, close() raised receipt_outcome_unknown, turning an honest 409
   into a 500 with the parent left open; fixed to the scalar outcome.
3. **Orchestrator diff-read**: decision/delivery projections were staged
   under the copy-pasted kind "voice-resolver-attempt" — a dishonest
   durable record; real kinds registered.
4. **Sol round-1**: the three blockers above, each a real race or silent
   retargeting.

### Sol's sitting-visible reservations (final, four)

1. **R1 — Rails note crash gap**: the receipt-gated summary projection
   precedes the direct journal-note write; process death between them
   leaves a succeeded projection without its note (root invocation, not a
   cancellation-driven late write).
2. **R2 — Exceptional parent cleanup**: an unexpected exception after
   opening a Decision/Delivery parent can leave it open until lease
   reconciliation.
3. **R3 — Mesh proof scope**: mesh is unit-proven (envelope build/validate,
   frozen-field engine construction, hub acceptance checks); no live worker
   execution was available on this walk.
4. **R4 — Parent-close boundary**: Decision/Delivery close their parent
   immediately after transactional publication rather than within the same
   transaction; with publication already committed and no exposed
   cancellation route, below the blocking bar.

### The verification liturgy

1. **Focused suites** (orchestrator re-ran after every round, output read
   from files): 207 tests green under isolated HOME across all touched
   suites plus every HS-131-05/06 regression suite, the schema suites
   (v53 pins), and the kernel fence.
2. **Real-metal walk**
   (`assets/hs-131-07/walk_service_callers_lan.py` against live llama.cpp
   on .43; output in `assets/hs-131-07/walk-output.txt`): all four legs
   green after every code round — Rails summary with the exact
   service/rails-observer/journal-only receipt tuple; Decision promotion
   under its real parent with one succeeded child and a drafted artifact;
   Voice with three attempts = three admitted children each carrying
   terminal receipts (the .43 server forces a JSON response format that
   broke the resolver's zone_ids contract → honest parse_failure — an
   endpoint-configuration observation, not a code defect); Delivery PR
   review through the REAL route (TestClient + stubbed PR source + real
   model) persisting a real artifact with both receipts.
3. **Full gate** on the quiet tree: accounting below.

### Gate triage (first run → fixes → clean re-run)

The first full gate surfaced TEN new names vs the HS-131-06 baseline
(94 names). All ten reproduced serially — deterministic fallout from the
story's ratified seam changes — and were dispositioned exactly:

- **Eight test migrations** (no product defect): the mesh relay wire tests
  migrated to the signed-envelope contract; the one-dial resolver census
  moved from `resolve_inference_target` to admitted `resolve_placement`;
  the pr-follow operation-matrix guard now names the three deliberate new
  parent operations exactly (its spirit — an exact, deliberate list —
  preserved); the web-route ask/primitives injected engine-factory doubles
  accept the admitted builder context (deployment_revision/warrant kwargs).
- **One REAL contract collision, product-fixed**: the round-1 blanket
  post-dispatch parent-liveness recheck in InferenceRunner and the
  unconditional cancelled-parent discard in ProjectionStager violated the
  RATIFIED HS-131-04 contract (on a parent-cancel race the child's earned
  receipt survives and the stale checkpoint blocks late output) — the
  sequence route returned 502 with no checkpoint row. Correction: the
  runner recheck is REMOVED (redundant once the in-transaction
  materializers landed), and the cancelled-parent discard became a
  per-kind REGISTRATION property (`discard_on_parent_cancel=True`)
  applied to decision-promotion-draft / delivery-pr-review /
  voice-resolver-attempt — the kinds with no checkpoint CAS, where the
  parent election is the only publication fence. The decision late-cancel
  test now asserts the corrected contract (earned child receipt, zero
  artifacts, cancelled parent). **Sol reviewed the correction and
  CONFIRMED it** ("restores the ratified HS-131-04/05 distinction …
  eliminates the competing terminal-receipt race. No objection.").
- **One integration flake**: test_cloud_stream_forwards_endpoint_deltas
  passed serially.

### Gate accounting (final run)

Baseline: `assets/hs-131-06/gate-failures.txt` (94 normalized names).
Final gate: `assets/hs-131-07/gate-failures.txt` (100 names,
`gate-tail.txt` alongside). Diff: **ZERO deterministic new names, TWO
repaired** (`tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_
the_worker_returns_badged` — the mesh envelope work repaired this
inherited name — and the 06 run's accounted deadline-expiry flake, green
here). Eight new names are one accounted flake family:
tests/unit/test_github_issue_actuator.py (6) +
test_github_pr_actuator.py (2), subprocess-heavy tests that passed 15/15
in an immediate serial run on identical code and were absent from the
previous gate run — xdist load flakes, not regressions.

### Post-verification focused totals

326 focused tests green under isolated HOME across every touched suite
plus the HS-131-04/05/06 regression suites, schema suites (v53 pins), and
the kernel line-budget fence. The real-metal walk ran green after every
code round, including after the gate-triage correction.
