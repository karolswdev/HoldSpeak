# HS-131-16 design — The mesh receiver proves authority locally

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-13; hostile-review clarification 2026-08-14) — the six original amendments and the implementation rulings below are binding
**Decision boundary:** choose the combined protocol, not either incomplete alternative. The hub authenticates each worker with its existing per-node pairing token, then signs one destination-bound dispatch offer with a hub-held Ed25519 key whose public half the worker pinned at pairing. Verification mints one private, exact, single-use `VerifiedMeshOffer`; the worker-local kernel consumes it to derive narrow authority and sends each permitted physical provider attempt through a worker-local `InferenceRunner` with a fresh local warrant, claim witness, dispatch context, and immutable receipt. The hub's kernel warrant, master signing secret, offer private key, and in-memory claim witness never cross the process boundary.

## Context and constitutional test

The hub already admits the logical `inference.invoke@1` attempt and independently
revalidates its warrant before accepting a mesh result. The receiver remains a
side door: `MeshServeWorker` accepts recomputable revision fields and nonempty
warrant-shaped strings, constructs a provider with `LEGACY_UNCONTEXTUAL`, and
calls `run_prompt` directly. A forged, expired, replayed, or cancelled offer can
therefore cause the physical model act even when the hub later rejects its
result.

Article XI.1 denies a process/LAN exemption. XI.2 requires the physical provider
attempt to be admitted before it acts and to end in one immutable terminal
receipt. XI.3 requires the receiving kernel's principal and authority to come
from authentication, not `payload["node"]`, a caller-built context, source IP,
or possession of the browser owner token. Articles V.2–4 require a durable
receipt and named refusal; Article IX requires both nodes' claims to be
inspectable rather than inferred from a successful response.

Neither design-beat alternative is sufficient alone:

- verifying a cross-node envelope without local admission authenticates the hub
  but leaves the worker's physical provider act unreceipted;
- local admission without cryptographic offer verification faithfully admits a
  forgery.

The selected protocol composes both. A compromised paired node remains able to
lie about its own execution; preventing that requires hardware/remote
attestation and is outside this private-mesh story. One node credential cannot
forge another node, the hub, or arbitrary kernel warrants.

## 1. Trust root and principal ruling

Extend `NodeTokenStore`; do not invent a second mesh credential registry.

1. `holdspeak node token create|rotate|revoke <name>` remains the deliberate
   hub-side pairing act. Pairing creates a stable node ID, a per-node bearer
   token, and a per-node Ed25519 offer-signing keypair. The hub retains the
   private key in the locked protected store; the worker receives and pins only
   the public key plus key ID. Token, private key, and public-key pin remain
   outside repository and database content.
2. `holdspeak mesh serve` reads `HOLDSPEAK_NODE_TOKEN` for node-to-hub HTTP and
   its pinned hub offer public key from local pairing custody. The old shared-
   owner `HOLDSPEAK_HUB_TOKEN` posture is removed rather than retained as a
   compatibility fallback.
3. `/api/mesh/relay/claim|complete|fail` require the narrow node-link edge right
   **and** `PrincipalKind.NODE`. Owner, agent, unauthenticated, and payload-made
   identities refuse before queue mutation.
4. The token store performs a locked fresh read for every authentication,
   signing-key lookup, create, rotate, and revoke. Writers use an exclusive
   cross-process lock plus atomic replace. One authenticated snapshot returns
   node name, stable node ID, credential generation, key ID, and signing key;
   claim revalidates that same snapshot at its commit boundary.
5. Every queued relay row binds `destination_node_id` **and the exact
   enqueue-time credential generation** as well as the human-readable name.
   Rotate, revoke, or re-pair cannot transfer old queued work to a replacement
   credential or identity; claim must match both persisted values before it can
   mark liveness, move the row, or sign an offer.
6. Successful Ed25519 verification mints a private identity-registered
   `VerifiedMeshOffer` bound to the exact hub key ID, hub operation, job,
   destination node ID, execution revision, payload hash, freshness bounds, and
   permitted local ordinals. The worker-local kernel consumes that capability
   once and derives the narrow service principal internally. `MeshServeWorker`
   cannot construct a generic reusable `Principal(SERVICE, ...)` itself.

The node token authenticates worker requests and MACs terminal reports; it
cannot sign hub offers. The hub's `kernel_meta.warrant_secret` and Ed25519 offer
private key are never distributed. A `ClaimWitness`, `DispatchContext`, or
`VerifiedMeshOffer` is identity-bound in process memory and is never serialized
or recreated from caller fields.

## 2. Signed dispatch offer

Every claim request supplies a fresh random `claim_nonce` and records its local
monotonic start. The context-gated hub enqueue reads the attempt ordinal only
from the runner-issued `DispatchContext`, never from a relay caller field, and
persists a content-free authenticated handoff with the queued job.

The hub creates a schema-1 dispatch offer only inside one `BEGIN IMMEDIATE`
transaction that:

- fresh-reads and revalidates the paired credential snapshot and signing key;
- re-reads a still-queued job whose destination name, stable node ID, **and
  enqueue-time credential generation** match the authenticated HTTP principal;
- verifies the queued envelope's hub kernel warrant;
- verifies that the hub operation is still `claimed`, unrevoked, and inside
  execution expiry;
- verifies `inference.invoke@1`, exact admitted deployment revision, target
  binding, and the context-authenticated positive ordinal;
- validates the relay revision's content address and node binding;
- performs one guarded `queued → running` transition storing node ID and offer.

The offer contains content-free authority metadata only:

- schema, Ed25519 `key_id`, random `offer_id`, and echoed `claim_nonce`;
- relay `job_id` and hub `operation_id`;
- paired `node_name`, stable `node_id`, and credential generation;
- hub relay revision ID and deterministic worker execution revision ID;
- an exact first ordinal and a budget of at most one typed compatibility ordinal;
- bounded `dispatch_within` and `complete_within` durations plus hub absolute
  settlement deadline;
- SHA-256 of the canonical non-authority job payload;
- SHA-256/binding of the hub warrant, not the hub signing secret.

The hub signs strict domain-separated canonical bytes named
`holdspeak.mesh.dispatch-offer.v1` with the per-node Ed25519 private key and
persists the signed offer. The worker pins the public key/key ID from pairing,
requires the echoed nonce to match its current poll, verifies the signature, and
recomputes payload hash, relay and execution revisions, node/name/ID/generation,
warrant-operation binding, ordinal budget, and freshness bounds. Missing,
malformed, forged, tampered, replayed, wrong-node, wrong-destination,
wrong-revision, wrong-operation, or expired offers refuse by fixed safe reason
before replay reservation, revision persistence, runner construction, engine
construction, or provider dispatch.

Freshness does not assume synchronized wall clocks. The worker enforces the
signed bounded durations against monotonic elapsed time since the nonce-bearing
claim began; the hub's own clock and absolute deadlines remain authoritative at
claim and settlement. The offer permits ordinal `n` once and `n+1` only after
the local runner's typed `ProviderCompatibilityRetry`. It is not a reusable hub
warrant or generic inference grant.

A hub revocation that wins the claim transaction prevents an offer. A revocation
racing after a valid offer may be learned only at result settlement in a
distributed system; it can never make a late result acceptable. The worker's
own stop/cancel election prevents local publication when it wins first.

## 3. Frozen worker execution revision

The mesh relay revision describes the hub-to-node destination and must not be fed
directly back through target resolution, which would recurse into the mesh. A
single pure function derives the worker execution revision from the signed,
content-addressed relay revision:

- `model_path` present → `kind=this_device`, `engine=local`,
  `boundary=same_device`;
- otherwise a valid private endpoint → `kind=private_endpoint`,
  `engine=openai_compatible`, `boundary=private_network`;
- otherwise a valid external endpoint → `kind=external_service`,
  `engine=openai_compatible`, `boundary=external_service`;
- no usable local artifact or endpoint → named refusal.

Destination ID, model, endpoint, model path, node, and secret slot come only from
the signed relay revision. The derived fields produce a second content-addressed
`DeploymentRevision`; both hub and worker recompute the same ID. The worker
persists exactly that revision in its local deployment-revision registry before
admission. Mutable profile/config rows cannot retarget construction, model,
endpoint, secret slot, egress, or receipt after the offer is verified.

## 4. Worker-local admission and physical cardinality

For each verified offer, the worker uses its own local database and kernel:

1. Before revision persistence or runner construction, atomically reserve
   `(hub_key_id, hub_operation_id, first_ordinal)` in a worker-local replay table
   with `INSERT … ON CONFLICT DO NOTHING`. Only the winner receives a private
   reservation witness; duplicates refuse `mesh_offer_replayed`. A crash leaving
   a reservation without all terminal receipts reconciles indeterminate and is
   never rerun.
2. The local broker consumes both the exact identity-registered
   `VerifiedMeshOffer` and reservation witness once. It derives the narrow
   service principal internally; no public constructor accepts offer fields and
   no generic service grant survives this job.
3. Persist the exact derived execution revision.
4. Build the first `InvocationRequest` whose service contract is
   `holdspeak.mesh-receiver@1`, payload hash covers prompt material in memory,
   deadline is bounded by the offer, ordinal is the context-authenticated offered
   ordinal, and native invocation ID causally names the hub operation.
5. Invoke the worker-local `InferenceRunner`. The runner alone submits, decides,
   claims, mints each local witness and `DispatchContext`, constructs from the
   frozen execution revision, and dispatches through `CanonicalPromptAdapter`.
6. Capture provider output outside the kernel in the runner publisher and return
   only `mesh-result:<job_id>` as the local kernel result reference. Do not send
   anything to the hub until `invoke()` returns and every attempted ordinal has
   a durable local receipt.
7. The offer permits exactly one typed `ProviderCompatibilityRetry`. If it fires,
   the runner consumes the reserved second ordinal and creates a second local
   `inference.invoke@1` operation/receipt. The ordered terminal report lists both
   attempts. Any third ordinal refuses. A product retry is a fresh hub operation,
   job, offer, replay reservation, and local cohort. A transport retry of the same
   terminal report is idempotent and never repeats the model.

`MeshServeWorker` no longer owns an engine cache, calls
`build_meeting_intel_for_profile`, imports `LEGACY_UNCONTEXTUAL`, or calls
`engine.run_prompt`. Its injectable test factory is passed into the local runner
and therefore still receives the runner-issued context. The recursion guard is
structural: the derived execution revision cannot have `kind=mesh_node`, and a
factory returning a `MeshRelayIntel` refuses before adapter dispatch.

Physical-attempt cardinality is measured separately on each node:

- hub: one logical mesh cohort with one hub operation/warrant/receipt;
- worker: each physical provider attempt has one local operation/warrant/context/
  terminal receipt; the signed budget allows one first attempt and at most one
  typed compatibility follow-up;
- product retry starts a fresh hub/worker cohort, never mutation/reuse.

## 5. Cancellation, restart, and replay

- After offer verification the worker derives the deterministic local invocation
  ID and atomically publishes it as active while checking the stop flag. If stop
  already won, it calls `InferenceRunner.cancel(id)` before `invoke`, so the
  runner's pending-cancellation fence prevents admission/dispatch. `stop()`
  atomically sets the flag and cancels any visible ID. Verification-to-registration
  and registration-to-invoke have no uncovered handoff interval. If cancellation
  wins before local publication, no result is captured or reported.
- A provider that cannot be forcibly interrupted may finish physically after an
  acknowledged cancellation; the runner records cancelled/indeterminate and its
  publication gate discards the body. Forced native-call termination is outside
  the owner's rigor bar.
- Hub cancellation/revocation independently makes `_relay_warrant_live` false.
  Complete/fail settlement therefore cannot change the hub operation or relay
  result after cancellation wins, even if a worker call was already in flight.
- The atomic persistent replay reservation makes offer replay refuse before
  revision persistence or construction across concurrent workers and process
  restart. An interrupted reservation/claimed attempt reconciles indeterminate
  and is not retried under the same authority.
- Hub queue claim records `claimed_by_node_id`; completion/failure from another
  node refuses. Exact duplicate terminal transport reports return the original
  settlement; conflicting reports refuse and cannot mutate stored terminal proof.
- A worker crash after local receipt but before reporting leaves the truthful
  local receipt and a hub job that expires/fails. It does not rerun silently on
  restart. Cross-node automatic receipt reconciliation is deferred; HS-131-12
  inspects both sides during the assembled walk.

## 6. Attested terminal report and independent hub acceptance

After every local attempt receipt is durable, the worker creates a schema-1
terminal report containing only:

- offer, job, hub operation, node name/ID/generation, relay revision, execution
  revision, and claim nonce;
- an ordered `local_attempts` list naming each permitted ordinal, local operation
  and receipt ID, principal/claim identities, and immutable terminal outcome;
- result SHA-256 for final success, or one fixed safe failure/refusal class;
- no prompt, completion body, token, API key, warrant secret, offer private key,
  or raw provider exception.

The worker MACs strict domain-separated report bytes with the node token. The
product result travels as a separate relay field outside the kernel. First
terminal settlement runs in one `BEGIN IMMEDIATE` transaction that:

1. fresh-authenticates the HTTP caller as the same paired node/generation;
2. reloads the persisted signed offer and verifies its Ed25519 signature and
   exact bindings;
3. verifies the terminal-report MAC and exact offer/job/node/operation/ordinal
   cohort/revision/nonce bindings;
4. requires one report entry and receipt per attempted physical ordinal, with no
   gaps or ordinals outside the signed budget;
5. recomputes the success result hash and requires a succeeded final local
   outcome for `/complete`, or a non-success terminal outcome for `/fail`;
6. re-reads and validates the live hub warrant, operation state, target,
   revision, revocation, and execution expiry;
7. performs one guarded running-to-terminal update storing the content-free
   worker report and settlement.

An exact duplicate report is a read-only idempotency path: after node
authentication, compare it byte-for-byte with the persisted report and result
hash, and return the original settlement even though the hub operation is now
terminal. Do not re-run the live-authority check for that exact duplicate.
Conflicting duplicates always refuse. The HTTP acknowledgement has one strict
shape and binds the exact job, offer, and canonical terminal-report digest it
accepted; an acknowledgement for another report cannot end retransmission, and
unknown or malformed fields are a terminal protocol refusal.

Worker success cannot force hub acceptance. Missing local receipt proof, a
wrong-node caller, wrong operation/revision/ordinal, modified result, expired or
revoked hub authority, duplicate conflict, or late report refuses by name. The
hub never rewrites the worker's local receipt, and the worker never rewrites the
hub receipt.

## 7. Persistence and hygiene

Schema v59 adds explicit hub-local relay proof fields rather than extending the
legacy `task_kind` JSON tunnel:

- `destination_node_id` and `destination_generation` captured at enqueue;
- `claimed_by_node_id` and the matching claimed credential generation;
- signed `dispatch_offer_json` and claim nonce;
- content-free `worker_terminal_json`.

The worker-local schema adds the unique replay-reservation tuple and reconciliation
state. Token-store persistence uses cross-process locking and atomic replacement;
relay claim and first terminal settlement use guarded transitions in
`BEGIN IMMEDIATE` transactions.

The existing product prompts and result remain in `mesh_relay_jobs`; that table
is outside the kernel and already owns relay content. Kernel operation, event,
parent, and receipt rows on both nodes contain only IDs, hashes, revisions,
destinations, ordinals, timing, authority basis, fixed reason classes, and result
references. They contain no prompts, completions, token streams, API keys,
bearer/node tokens, HMAC secrets, or raw provider exceptions.

Logs may name job/operation/node/reason and elapsed/count facts. They must not log
the node token, signed offer body, prompt/completion, or raw provider exception.
Application error storage receives a fixed safe class; detailed local provider
diagnostics stay local and credential-scrubbed.

## 8. Invariants

1. A mesh worker authenticates requests only with its distinct paired node
   token; browser owner authority never substitutes, and that token cannot forge
   the hub's Ed25519 offer signature.
2. No signed offer exists unless one transaction proves the hub operation,
   warrant, revision, context ordinal, credential generation, and stable
   destination identity live together.
3. Signature/freshness verification and atomic replay reservation precede local
   revision persistence, runner construction, engine construction, and dispatch.
4. `VerifiedMeshOffer` and its replay witness are exact, private, and consumed
   once; they cannot become a generic service authority.
5. Every physical worker model attempt is one local `inference.invoke@1` with one
   exact execution revision, permitted positive ordinal, local context, and
   immutable receipt; at most one typed compatibility follow-up is permitted.
6. Hub master secret/private signing key/warrant witness and worker local
   secret/witness never cross nodes.
7. Persistent reservation makes an offer at-most-once across concurrency,
   retry, and restart; product retries use fresh hub authority and receipts.
8. No network report occurs until every local attempt receipt is durable.
9. Hub first settlement transactionally revalidates both original hub authority
   and worker terminal cohort; exact report retry is read-only and conflicting
   retry cannot mutate terminal state.
10. Cancellation/revocation/replay cannot publish an accepted late result or
    mutate either node's terminal receipt.
11. Kernel rows remain content- and credential-free.

## 9. Focused proof matrix

| Contract | Required proof |
| --- | --- |
| Edge authentication | Missing/wrong/browser/revoked/other-node tokens refuse; payload node cannot fabricate principal; locked fresh token reads derive exact stable ID/generation; rotate/revoke is visible cross-process without hub restart; re-pair cannot inherit queued work. |
| Hub authenticity | A node-token holder cannot forge an Ed25519 dispatch offer; wrong/unpinned key ID, signature, domain, canonical bytes, or credential generation refuses. Private key never leaves hub custody. |
| Offer matrix | Missing, malformed, forged signature, stale/mismatched nonce, payload/prompt-hash tamper, monotonic expiry, clock skew, wrong-node/name/ID, wrong-destination, wrong relay/execution revision, wrong hub operation, wrong context ordinal, invalid/revoked hub warrant all refuse before reservation/runner/factory/dispatch. |
| Exact authority | Copied/duck-typed/reused `VerifiedMeshOffer` or reservation witness refuses; local kernel derives the principal and permits only the exact revision/payload/ordinal budget. |
| Frozen construction | Mutate worker config/profile/registry after offer; construction and egress remain on deterministic execution revision and signed secret slot. |
| Local cardinality | Success, provider failure, refusal, cancellation, one typed compatibility follow-up, forbidden third attempt, and fresh product retry prove physical calls = ordered local dispatched operations = terminal receipts. |
| Replay/restart | Concurrent same-offer workers, same offer twice, altered replay, crash after reservation/claim, and crash after local receipt never repeat physical dispatch; stale reservation/claim reconciles indeterminate. |
| Claim transaction | Concurrent pollers, revoke/cancel during claim, stale credential snapshot, and re-pair race produce at most one signed offer from one live transactional snapshot. |
| Cancellation races | Stop before/after active-ID registration, before invoke, during provider call, and before report; hub revoke before claim and while worker runs; no uncovered handoff, losing settlement, or receipt mutation. |
| Terminal report | Missing/forged/swapped/gapped local attempt/receipt cohort, wrong node/revision/ordinal/outcome, modified result, transaction race, exact duplicate after hub closure, and conflicting duplicate are revalidated independently. |
| Two-process loopback | Real hub HTTP process plus real worker process with injected fake engine; inspect separate hub/worker SQLite rows, node identity, revisions, receipts, and accepted/refused settlement. No LAN/model needed. |
| Hygiene | Unique prompt/result/token/key/exception sentinels absent from both kernels and terminal metadata while relay content remains outside kernel. |
| Mutation | Restore a direct receiver factory/`run_prompt` call in a disposable edit; the exact `mesh-receiver` fence fails before source restoration. |
| Census | Remove both receiver findings, add no command scope to `ADAPTER_ALLOWLIST`, preserve zero unregistered execution. |

The final focused implementation suite runs under an isolated `HOME`. The
assembled real `.43` node/model proof remains HS-131-12's responsibility, but
this story must ship deterministic process-boundary proof and leave that walk a
stable protocol to repeat.

## Recorded notes

- A paired or compromised worker can invent claims about its own local database
  or bypass HoldSpeak and call hardware directly. The terminal MAC is an
  authenticated worker assertion, not hardware attestation or nonrepudiation.
- Existing private-mesh HTTP transport does not add TLS pinning in this story.
  Theft of the node token permits node impersonation and forged worker reports,
  but cannot forge the hub's Ed25519 dispatch authority. Credentials never enter
  logs, argv, repository, database, or kernel rows.
- A valid offer can race a later remote revocation because there is no atomic
  transaction across two machines. The binding guarantee is: revocation before
  offer blocks dispatch; revocation after offer independently blocks accepted
  publication. The worker also honors its local cancellation election.
- A provider that ignores cancellation may finish physically; its output remains
  unpublished and its local receipt is cancelled or indeterminate.
- A same-thread Python `os.fork()` while authority is being consumed, derived, or
  physically used is refused **before** CPython begins its at-fork callback list;
  no child is created and no stack-local authority can continue. Normal forks
  outside an authority continuation remain supported with fresh child-local
  registries. A fork from another thread waits for short authority mutations to
  quiesce, but waiting may not fence claim, cancellation, settlement, database,
  or other work an already-admitted attempt needs in order to finish.
- Cross-node automatic recovery of a local receipt after a worker crash is not
  required. At-most-once execution and honest hub timeout are preferred to an
  invisible rerun.
- Deployment revisions freeze identifiers, endpoint, model path, and secret-slot
  name, not model-file bytes, secret values, or honest hardware execution.
- The existing profile factory recomputes a key slot from destination ID. The
  implementation must consume or exactly validate the signed derived revision's
  `secret_slot`; ambient recomputation may not retarget credential custody.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The combined authenticated-offer plus local-runner
shape is required, but symmetric offer signing, generic service authority,
check-then-run replay handling, stale token-store reads, split claim/settlement,
and the worker-stop handoff were blockers.

### Binding amendments

1. **Authenticate the hub asymmetrically.** Pairing provisions a per-node
   Ed25519 offer keypair; the worker pins only the public key. Node bearer HMAC
   remains worker-to-hub/report authentication and cannot forge a hub offer.
2. **Make offer authority exact and kernel-consumed.** Verification mints one
   private `VerifiedMeshOffer`; the local kernel consumes it and derives
   authority. Context supplies the hub ordinal. The signed budget permits the
   first ordinal and at most one typed compatibility follow-up, each separately
   receipted and reported in order.
3. **Make pairing revocation process-coherent and queue identity stable.** Token
   custody fresh-reads under cross-process locking/atomic replacement; claim
   revalidates one credential snapshot; enqueue binds stable destination node ID
   **and enqueue-time credential generation** so rotate, revoke, or re-pair cannot
   let a replacement credential inherit old work.
4. **Add nonce freshness and atomic local replay reservation.** The offer echoes
   the current poll nonce and carries bounded durations enforced with monotonic
   elapsed time. One unique worker-local reservation elects the only executor;
   crash residue reconciles indeterminate and never reruns.
5. **Make claim and first settlement transactional.** Each uses one
   `BEGIN IMMEDIATE` live-authority snapshot and guarded transition. Exact
   duplicate reports are read-only idempotency after authentication; conflicting
   duplicates refuse.
6. **Close the worker-stop handoff.** Active deterministic invocation ID and stop
   state share one atomic election; pre-invoke cancellation enters the runner's
   pending fence, leaving no verification-to-dispatch gap.

### Orchestrator disposition

All six amendments are ADOPTED. They close realistic forgery, multi-process
revocation, duplicate execution, cancellation handoff, ordinal, and TOCTOU
failures without pretending to provide hardware attestation or atomicity across
two machines. With them, the design satisfies every HS-131-16 acceptance
criterion and is binding on implementation.

### Hostile-review implementation rulings — 2026-08-14

The exact round-four implementation did not satisfy the ratified design. These
rulings clarify the existing contract; they do not add a third authority factor,
hardware attestation, cross-node atomicity, or a persistent report outbox.

1. **Monotonic means end to end.** Offer verification converts the signed bounded
   remainder to a process-local monotonic deadline. Admission, watchdog,
   provider work, cancellation, and report delivery consume that same monotonic
   budget. A backward wall-clock step cannot extend physical execution or the
   signed settlement window. Hub wall time remains independently authoritative
   when the hub accepts a first settlement.
2. **Exact protocol and custody types are authority.** Booleans do not satisfy
   integer schema/version/ordinal fields. Malformed endpoint parsing always
   becomes the fixed named refusal. Existing private custody is refused before
   use unless one no-follow metadata-checked read proves a regular, owner-held,
   securely permissioned file and the opened inode matches the inspected path.
3. **One persisted revision, one snapshot, one liveness generation.** Every
   profile/target read surface returns the opaque write revision its update verb
   requires. Probe work revalidates that exact revision after I/O; fingerprints
   are not concurrency authority. Setup, Doctor, Ask, planning, and UI consume
   one immutable target snapshot. Name-based liveness holds shared custody
   through the exact `(node_id, credential_generation)` SQL read and uses
   `0 <= age <= window`.
4. **One engine-aware artifact and credential verdict.** Setup, Doctor,
   planning, deployment capture, and loaders share the canonical path-shape and
   readiness decision: llama.cpp is a regular file, MLX is a directory, and
   relative/tilde/empty paths refuse. A keyless destination sends no ambient or
   stale profile credential. A client-selected endpoint can never be paired
   with an independently selected ambient key.
5. **Browser audio authority is generation-bound.** The server-issued mic and
   floor generation binds open, audio submission, close, and release. Cleanup
   for interval A cannot close or release reopened interval B, and late A audio
   cannot be admitted under B.
6. **Continuation spans the whole authority and inherited-handle lifetime.** A
   same-thread fork is refused from before submit/approve/claim consumes
   authority through timer, sequence, active-state, receipt, and publication
   cleanup. SQLite backup/recovery handles are likewise covered from open
   through finalization. The shipped runtime has no retained pre-install raw
   `os.fork` alias; hypothetical embedding aliases are recorded, not a promised
   interception boundary.
7. **Process-local finalization is real.** Worker owner leases release on every
   exit. Startup reconciliation failures are named terminal command outcomes.
   Database reset does not publish a replacement singleton while an old checked-
   out transaction can still commit. Failed connection configuration closes and
   deregisters its exact handle. Signal handlers may not call Python lock-taking
   primitives such as `threading.Event.set()` under a false async-safe claim.
8. **Lost ledger authority halts serving.** A failed terminal reservation CAS
   means the worker no longer owns that reservation; it cannot classify the
   result as recorded and continue claiming work. Active duplicate profile
   create is a 409, while intentional recreation of a soft-deleted ID is a new
   incarnation with a fresh opaque revision, never a generic 500.
9. **Publication remains an election.** If stop wins before terminal
   publication, the body is discarded. Once terminal publication wins, a later
   stop cannot retroactively discard or unsend the fixed report: byte-identical
   delivery continues through the signed monotonic settlement window without
   rerunning the model.

Each ruling requires an old-code-failing deterministic proof at the narrow
boundary plus the assembled two-process and cardinality proofs already required
above. Green tests without those interleavings do not satisfy Article IX.
