# HS-131-16 reduced candidate — repair round 1

**Status:** BINDING CONSOLIDATED BRIEF (orchestrator, 2026-08-14)
**Reviewed source:** 31 paths / 268,140 bytes at `e4193f12`
**Manifest:** `43a52b57920dfc95bb8b79c9f979dfbc38e53290e38e7f699b25aa729d4ca927`
**Complete diff:** `934a77d09745b388d099130b210b919f864c94adf88f538ca8707a62df908751`
**Verdicts:** hostile Sol review **FAIL**; Terra execution **BLOCKED** by foreign-worktree isolation and static review **FAIL**

## Ruling

The 31-path reduction succeeded as governance: it is small enough to expose the
actual protocol gaps. It is not a ship candidate. The findings below are the one
consolidated repair brief for the first reduced review round. No partial finding
was patched while counsel was still running.

Every sustained item has an ordinary production trigger or closes proof promised
by the story/design. Global process interception, generic database retirement,
hardware attestation, TLS, a persistent report outbox, and scheduler-hostile
bytecode probes remain out. A fresh Opus repairs this brief; the exhausted first
implementer is retired. Any path outside the amended acceptance map stops before
edit. A third reduced repair round stops for design/scope review; a fifth requires
an owner ruling.

## Sustained structural repairs

### R1 — Keep production observation content- and credential-free

A normal production `MeshService` call is observed by `SQLiteObserver`. Generic
argument/result summarization can persist `NodeCredentialSnapshot.token`, prompt,
completion, envelope/warrant, and signed offer into `pipeline_events`.

Repair inside the mesh service boundary: observed public methods expose only
fixed IDs/status/counts, while token/payload/report work moves through unobserved
private methods or an existing explicit redaction seam. Do not widen into a
generic observer refactor. Prove unique token/prompt/result/warrant/offer
sentinels are absent from observer rows after claim, complete, fail, and refusal.

### R2 — Make the production pairing path complete and node-only

The real parser still defaults `mesh serve` to `HOLDSPEAK_HUB_TOKEN`; change it to
`HOLDSPEAK_NODE_TOKEN` and remove the ambient owner-token posture. Pairing must
provide one deliberate export/import path that transfers the bearer token plus
stable node ID, credential generation, key ID, and offer **public** key into the
worker's owner-only custody. It must never export the offer private key.

The proof uses the product command/loader composition with distinct hub and worker
HOMEs. Tests may not hand-build a pin while claiming the production pairing path
works.

### R3 — Send a dedicated worker wire projection, never the hub warrant

`claim()` currently serializes `MeshRelayJob.to_dict()`, which includes the hub
kernel envelope/warrant. Replace it with a dedicated worker projection containing
only job ID and the canonical product payload needed for execution. Exclude the
hub envelope/warrant, deployment proof object, claim/context capability, stored
proof columns, status, result, and error. The content-free signed offer carries
only hashes/bindings.

### R4 — Serialize credential changes with claim and settlement

A fresh read before a SQL transaction is not a commit-boundary proof. Hold the
same node-custody lock from exact snapshot revalidation/signing-key access through
the hub claim commit. Rotate/revoke/re-pair and claim must have one winner.
Classify stale-snapshot refusal by name rather than leaking an HTTP 500.

First settlement likewise fresh-authenticates and holds the exact node/generation
snapshot through its commit. Credential revocation that wins first prevents
acceptance.

A legacy v1 token document must be explicitly and losslessly migrated or refused;
it may never be treated as `{}` and rewritten so unrelated pairings disappear.

### R5 — Bind every semantic offer field to the received job and live authority

After signature verification, compare the offer against the received job's exact
hub operation, `inference.invoke@1` operation kind, destination/node/generation,
relay revision, deployment/warrant binding, payload hash, nonce, and permitted
ordinal. Correctly re-signed wrong-operation, wrong-destination, wrong-revision,
wrong-warrant, and wrong-operation-kind offers refuse by their existing fixed
reasons before reservation, revision persistence, runner/factory construction,
or dispatch.

The offer's worker budget is the minimum remaining relay deadline, hub warrant
execution lifetime, and protocol cap at the claim commit—not a fresh 120 seconds.

### R6 — Make first settlement one transactional election

Move proof load, exact duplicate/conflict election, offer/report/MAC/cohort checks,
live operation/warrant/revocation/deadline checks, and the guarded relay terminal
update into one `BEGIN IMMEDIATE` repository operation on one connection. A
cancellation, warrant revocation, credential revoke, expiry, or competing report
that commits first must win. An exact duplicate after closure is read-only and
returns the original acknowledgement; a conflict cannot mutate proof or receipt.

### R7 — Close stop and ordinary two-process ownership gaps

`stop()` winning before lazy local-runner construction must be inherited by the
new runner before `invoke()`. Add the real claim-in-flight reproduction; do not
preconstruct the runner in the test.

Before startup reconciliation, acquire one narrow OS-released owner lock for the
worker database and hold it for the serve lifetime. A second ordinary
`mesh serve` process using the same worker DB refuses before touching
reservations; only a later owner after actual process exit reconciles residue.
This is a mesh-worker owner lock, not global fork/signal/descriptor machinery.

### R8 — Carry one absolute deadline end to end

Convert the signed remainder to one process-local monotonic deadline. Recompute
remaining time after revision persistence and immediately before admission,
provider dispatch, watchdog creation, retry sleep, and each transport request.
Cap request timeout to the remainder; no persistence or transport time may extend
physical authority. First hub settlement enforces the signed absolute hub
settlement deadline inside R6's transaction.

Liveness is similarly generation-bound: persist/query/touch exact
`(node_id, credential_generation)` with `0 <= age <= window`; G1 activity cannot
make G2 appear live.

### R9 — Validate the exact acknowledgement and classify HTTP refusal once

A 2xx body ends retransmission only when it has the strict expected field set and
matches job ID, offer ID, and canonical terminal-report digest. Unknown/malformed
or wrong-cohort acknowledgements refuse. Handle `HTTPError` before its `URLError`
superclass: a structured 4xx is a terminal named protocol response, not transport
loss. Retry only transport failure, bounded by count and R8's deadline, with no
model rerun.

### R10 — Make empty provider output honest

A successful empty string cannot receive a successful local receipt and then be
rejected only at the hub. Either accept every string result—including empty—and
bind its digest, or classify blank output as a local failure before the local
terminal receipt. Keep worker and hub semantics identical; the default ruling is
to accept an empty string because the result digest is authoritative.

### R11 — Enforce content-free terminal-report grammar at the hub boundary

A node MAC is authentication, not sanitization. Enforce bounded opaque grammars
for job/offer/operation/receipt/principal/claim IDs, exact lowercase SHA-256 where
required, exact outcome vocabulary, and the fixed safe failure/refusal classes.
An otherwise valid MACed report carrying prompt/credential sentinels in any proof
field refuses without persisting them. Do not claim hardware attestation or
prevent a compromised node from lying about execution; enforce only the declared
wire/storage grammar.

### R12 — Replace claimed proof with the missing proof

Add and run deterministic focused coverage for:

- RFC 8032 §7.1 public-key/signature vectors plus malformed lengths/encodings,
  tampered message, tampered signature, and non-canonical scalar refusal;
- correctly **re-signed** semantic wrong-operation/destination/revision/warrant/
  operation-kind offers, asserting zero reservation/construction/dispatch;
- rotate/revoke versus claim commit and revoke/cancel versus first settlement;
- v1 token-store migration/refusal without loss of unrelated nodes;
- stop during claim before lazy runner construction;
- second live worker owner refusal and post-exit residue reconciliation;
- generation-bound liveness;
- exact/malformed/wrong acknowledgement and HTTP 4xx terminal refusal;
- empty success semantics;
- hostile MACed content-bearing report rejection and observer hygiene;
- real two-process product pairing with separate hub/worker HOMEs and receipts.

Terra's execution leg remains unfulfilled. After repair and a new exact freeze,
the orchestrator will attach to the durable worktree under the owner's explicit
approval, run the focused Terra matrix with isolated HOME, read all output, and
return to the shared checkout.

## Recorded non-blocking notes

| Observation | Ruling / home |
|---|---|
| Low-order public keys and hex whitespace/case variants require replacement of the pinned hub key or custody compromise. | **ADVERSARIAL NOTE**; not a story blocker. |
| A signed `max_attempts=1` can still meet the unchanged runner's typed follow-up, but production emits only 2. | **ADVERSARIAL NOTE** until a producer emits budget 1; record for protocol hardening. |
| Legacy unauthenticated repository lifecycle verbs have no production caller. | **ADJACENT DEBT → HS-131-11** entry-point cleanup; no compatibility path may reattach them. |
| Cross-node crash recovery, hardware attestation, TLS pinning, forced provider termination, and persistent outbox. | Explicitly ruled out by the design/map. |

## Approved path expansion

The 40-path ceiling remains. In addition to the ratified map, this repair may
touch only these newly classified paths, hunk-scoped to R2/R12:

```text
holdspeak/main.py                              # mesh parser default/wiring only
holdspeak/commands/node_serve.py               # deliberate pairing export/import only
tests/unit/test_delivery_commands.py           # product CLI proof only
tests/unit/test_node_serve_worker.py            # pairing/worker command proof only
tests/unit/test_node_link_two_process.py        # custody coherence proof only
tests/unit/test_web_runtime.py                  # production observer wiring proof only
```

`holdspeak/services/observer.py`, `holdspeak/services/sqlite_observer.py`, generic
database/process files, and every previously forbidden product surface remain out.
If R1 cannot be repaired at the mesh boundary, stop for reclassification rather
than editing the generic observer.
