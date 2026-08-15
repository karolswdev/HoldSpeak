# HS-131-16 acceptance map — reduced implementation boundary

**Status:** SHIP (orchestrator, 2026-08-14; owner functional bar)
**Story:** [HS-131-16](./story-16-mesh-receiver-authority.md)
**Design:** [DESIGN-HS-131-16](./DESIGN-HS-131-16.md), RATIFIED-AS-AMENDED
**Final repair:** [REPAIR-HS-131-16-R2](./REPAIR-HS-131-16-R2.md), implemented; no R3 review brief
**Clean base:** `e4193f12de0832892fea5946f3fb6aef4073ec5f`
**Final candidate:** 40 paths; manifest `24e25287380abcbad6527d5037f051afccbf155620059b38f11069f8085b1413`; complete diff `17cb83aaf53082bfccf1e963b942c7304e43fad8f76aca2038fea4e018b14450`
**Rejected ship candidate:** preserved read-only at 151 changed paths; manifest `332b62e95a00c996db9af663cb9b12be7b3da32361e4294ee5faa7a3ca76ef32`, complete diff `62e21a998c76af027f80791e7023f2dd43efa0775b1f9afc6882ae7a627bbb51`

## Purpose

HS-131-16 closes one side door: the mesh worker's physical model attempt. It
must preserve the ratified two-proof protocol without carrying the rejected
candidate's product-wide repair history. The full design remains the protocol
floor. Its implementation rulings apply at the mesh seams this story changes or
calls; they do not authorize unrelated profile, Setup, Doctor, meeting, browser
audio, Models UI, generic database-lifecycle, documentation, or final-walk
rewrites.

A concern rides in this story only when it is **CORE**, **PROOF**, or a
demonstrated **REGRESSION**. Any path outside the default ownership list requires
an orchestrator classification in this file before it is edited. Crossing 40
changed paths, touching a non-mesh web surface, or requiring a third repair round
is a stop signal for design/scope review rather than permission to widen the
patch.

## Owner functional ruling — 2026-08-14

The owner stopped the reduced hostile-review loop: the work had become academic
instead of functional. This ruling overrides the map's review-round machinery,
not its product contract.

The ship bar is now the ordinary product path:

- product pairing provisions node token plus public offer pin and `mesh serve`
  executes through the local admitted runner;
- forged, replayed, expired, wrong-node, and wrong-generation offers refuse before
  provider work;
- normal success, provider failure, stop, and byte-identical report retry leave
  honest separate worker/hub receipts without credential/content leakage;
- the real two-process loopback, focused functional matrix, and one-path census
  are green.

Hostile signer bugs, perfect cross-database transaction models, microscopic
scheduler windows, future custody schema shapes, and protocol-taxonomy disputes
remain recorded hardening notes unless a normal product action reproduces damage.
No more counsel or mutation expansion blocks this story. Repair concrete product
reds, run the functional gates, transfer, and let the orchestrator make the SHIP
call.

The orchestrator now rules **SHIP**. The transferred candidate repaired the stale
paired-node cardinality double, three schema-v59 assertions, the broker line
budget, and one scheduler-sensitive timeout test. The final 46-file matrix is
864/864; the full unit candidate lane is 4,643/4,643. Three unchanged backend
guards and two unchanged Speak mock files remain inherited baseline; all other
web tests (785), tokens, architecture, typecheck, and production build pass. None
of those baseline inputs differs from `e4193f12`, and no mesh red remains.

## Classification rule

- **CORE:** required for an authenticated, exact hub offer and a worker-local
  admitted, receipted, bounded physical attempt with independent hub settlement.
- **PROOF:** focused deterministic evidence for a CORE invariant.
- **REGRESSION:** behavior that the reduced CORE change demonstrably breaks on
  `e4193f12`; it needs a before/after reproducer, not a reviewer's suspicion.
- **ADJACENT DEBT:** real behavior neither required nor caused by HS-131-16.
- **ADVERSARIAL NOTE:** hardening beyond the owner's realistic-use bar without a
  shipped trigger or ordinary production failure.

## Concern map

| Concern from the frozen candidate | Class | Reduced-story ruling |
|---|---|---|
| Per-node bearer identity, stable node ID/generation, hub-held Ed25519 offer key, worker public-key pin | **CORE** | Keep. Node auth cannot forge hub authority; browser owner auth cannot substitute for a node. |
| Destination/generation/revision/operation/ordinal-bound signed offer, nonce and bounded monotonic freshness | **CORE** | Keep strict schema and fixed named refusals before reservation, construction, or dispatch. |
| Private identity-registered, single-use `VerifiedMeshOffer` plus atomic worker replay reservation | **CORE** | Keep. Caller-built labels, serialized capabilities, duck types, and replay do not carry authority. |
| Deterministic non-mesh worker execution revision and exact secret-slot custody | **CORE** | Keep only the pure mesh derivation and the narrow loader/validation seam it requires; do not sweep every product target surface. |
| Worker-local `InferenceRunner`, exact local operation/context/revision/receipt, one typed compatibility follow-up maximum | **CORE** | Keep. First attempt and optional compatibility follow-up are distinct physical attempts and immutable receipts; no third attempt. |
| Worker stop/cancel election, one end-to-end monotonic deadline, late-publication fence | **CORE** | Keep the mesh handoff and any strictly necessary existing runner seam. Forced provider termination and scheduler-hostile interleavings are not promised. |
| Content-free ordered terminal report, node MAC, independent hub revalidation, first-settlement transaction, exact retry idempotency | **CORE** | Keep. Transport retry resends fixed bytes and never reruns the model; conflicting retry refuses. |
| Relay/replay persistence and schema needed for offer, destination generation, local reservation, report, and settlement | **CORE** | Keep only columns/tables and guarded transitions required by this protocol. No generic database retirement framework rides along. |
| Receiver fence removal with no command allowlist | **CORE** | Keep the production migration; the census itself is **PROOF**. Both `mesh-receiver` findings must disappear through the authenticated local spine. |
| Forgery/tamper/replay/swap/expiry/revocation/cardinality/cancellation/report matrices | **PROOF** | Keep focused tests that fail on `e4193f12` for the exact invariant they claim. Avoid broad historical test rewrites. |
| Real two-process loopback with separate hub and worker databases/receipts | **PROOF** | Keep with an injected fake engine. LAN plus the real model remains HS-131-12. |
| Direct receiver `run_prompt` mutation caught by the one-path census | **PROOF** | Keep as a disposable mutation with byte-identical restoration; do not add an allowlist. |
| Existing mesh queue/provider/serve behavior broken by the reduced protocol | **REGRESSION** | Repair only after a focused old/new reproducer proves the reduced CORE change caused it. |
| Profile storage revisions, profile create/recreate CAS, Models UI authority/interleavings | **ADJACENT DEBT** | Drop from HS-131-16. Give any surviving defect a separately named home; no Models UI or generic profile route changes. |
| Setup/Doctor/Ask/planning snapshot unification and product-wide artifact/readiness canon | **ADJACENT DEBT** | Drop. At most use an existing frozen revision seam; do not refactor these surfaces in this story. |
| Browser mic/floor generations, open-mic cleanup, speak-to-fill, voice route lifecycle | **ADJACENT DEBT** | Drop. HS-131-16 does not touch browser audio or its React clients. |
| Meeting planning, observer projections, liveness screenshots/walk scripts | **ADJACENT DEBT** | Drop. The final live walk belongs to HS-131-12; meeting residuals belong to HS-131-17. |
| Product-wide database reset/retirement, inherited SQLite backup/finalization, generic connection registry | **ADJACENT DEBT** | Drop unless the reduced worker's own connection cannot close correctly; then fix only that local ownership regression with a reproducer. |
| Product-wide fork fencing, retained raw-fork interception, asynchronous `BaseException`/opcode-window probes, signal-time lock-free machinery | **ADVERSARIAL NOTE** | Record, do not block. Keep only an ordinary shipped process/fork continuation failure that can duplicate live mesh authority. |
| Docs, product copy, dependency-wide cleanup, UI geometry, and broad conftest/suite edits | **ADJACENT DEBT** | Drop. Entry-point docs are HS-131-11; dependency changes ride only if the selected Ed25519 implementation cannot use an already-pinned package. |

The read-only classification of the frozen candidate established no
**REGRESSION**. Existing broad test changes and hardening therefore transfer only
if the reduced implementation later supplies the required `e4193f12` control and
new-code reproducer.

## Reduced acceptance spine

The implementation is acceptable only if all of these are true on one frozen
fingerprint:

1. A claim authenticates one live node snapshot and transactionally signs one
   exact destination/generation/revision-bound offer whose private key never
   leaves the hub.
2. Strict worker verification plus one atomic reservation happens before local
   revision persistence, runner/factory construction, or provider dispatch.
3. The worker-local kernel consumes one exact offer and derives the local
   principal; every physical attempt reaches the existing admitted runner and
   ends in one immutable receipt.
4. The signed budget permits the first ordinal and at most one typed
   compatibility ordinal. Product retry creates a new hub operation and offer;
   transport retry repeats no physical work.
5. Stop/cancel/revoke/replay races cannot publish accepted late output. A won
   terminal publication continues byte-identical report delivery inside the
   signed monotonic window.
6. Hub settlement independently revalidates caller, offer, warrant, operation,
   destination, generation, revision, ordinal cohort, outcome, and result digest.
   Exact duplicate is read-only; conflict cannot mutate either node's receipt.
7. Prompt, completion, audio, token, credentials, private keys, raw provider
   exceptions, claim witnesses, contexts, and verified capabilities stay out of
   kernel rows, relay-proof metadata, logs, argv, repository content, and
   cross-node authority payloads.
8. Two real loopback processes expose separate worker and hub receipts, and the
   one-path census reaches zero `mesh-receiver` findings without a command
   allowlist.

## Default implementation ownership

This is a hunk-level budget, not permission to copy whole files from the frozen
candidate:

```text
holdspeak/mesh_authority/**
holdspeak/delivery/node_credentials.py
holdspeak/delivery/node_link.py
holdspeak/principals.py                          # NODE kind/right only
holdspeak/db/mesh_relay.py
holdspeak/db/mesh_worker.py
holdspeak/db/schema.py
holdspeak/db/migrations.py
holdspeak/db/__init__.py                         # mesh schema export only
holdspeak/db/models/__init__.py                  # mesh row model export only
holdspeak/services/mesh_relay_authority.py
holdspeak/services/mesh_service.py
holdspeak/commands/mesh_serve.py
holdspeak/commands/node_serve.py                # R1 production pairing only
holdspeak/main.py                               # R1 mesh parser/wiring only
holdspeak/web/routes/mesh.py
holdspeak/web_server.py                         # mesh edge wiring only
holdspeak/inference_targets.py                   # mesh-only executable target derivation
holdspeak/intel/mesh_relay.py
holdspeak/intel/models.py                        # conditional mesh result/context shape only
holdspeak/intel/providers.py                     # conditional exact secret-slot loading only
holdspeak/kernel/mesh_local_authority.py
holdspeak/kernel/mesh_local_runner.py
holdspeak/kernel/inference_runner.py             # surgical existing-runner seam only
holdspeak/kernel/inference_cancel_signal.py      # only if the mesh stop handoff proves it necessary
holdspeak/deployment_revisions.py                # pure execution-revision support only
tests/unit/test_mesh_receiver_authority.py
tests/unit/test_mesh_two_process.py
tests/unit/test_mesh_relay_queue.py              # regression additions only
tests/unit/test_mesh_relay_provider.py           # R2.5 paired-liveness regression only
tests/unit/test_mesh_serve_worker.py              # authenticated protocol replacement proof
tests/unit/test_delivery_node_link.py             # credential coherence/migration regression
tests/unit/test_delivery_commands.py              # R1 product CLI proof only
tests/unit/test_node_serve_worker.py               # R1 pairing/worker command proof only
tests/unit/test_node_link_two_process.py           # R1 custody coherence proof only
tests/unit/test_web_runtime.py                     # R1 observer wiring proof only
tests/unit/test_inference_runner.py                # R2 immediate deadline fence proof only
tests/unit/test_one_path_cardinality.py            # owner-bar paired-node test regression
tests/unit/test_one_path_census.py                # two findings plus mutation only
tests/unit/test_db.py                             # mesh schema/migration proof only
tests/unit/test_decision_commitments.py           # schema-v59 regression assertion only
tests/unit/test_decision_record_service.py        # schema-v59 regression assertion only
tests/unit/test_monday_brief_service.py           # schema-v59 regression assertion only
tests/fixtures/db_schema_canonical.txt            # schema snapshot only
```

`pyproject.toml` and `uv.lock` may join only if the clean implementation proves a
new cryptographic dependency is unavoidable. Any generic kernel, database,
profile, Setup/Doctor, speech, meeting, observer, documentation, script, or React
path is outside ownership until this map records a demonstrated reason.

## Implementation classifications — 2026-08-14

- **REGRESSION / approved path expansion:** HS-131-16 advances the database from
  schema v58 to v59 for the mesh worker authority ledger. The full unit gate
  demonstrated three hard-coded `SCHEMA_VERSION == 58` assertions outside the
  focused matrix in `test_decision_commitments.py`, `test_decision_record_service.py`,
  and `test_monday_brief_service.py`. Update only those expected literals to 59;
  no decision or brief behavior rides with the schema assertion repair.
- **REGRESSION / approved path expansion:** replacing `NodeTokenStore`'s stale
  in-memory `_nodes` cache with process-coherent fresh reads breaks the existing
  browser-token-poisoning test at
  `tests/unit/test_delivery_node_link.py::TestNodeTokens::test_web_token_never_authenticates_as_node`.
  The product refusal remains intact; repair the test through the store's locked
  mutation seam and keep its original assertion. This is the only established
  regression at the first reduced handback.
- **PROOF clarification:** `tests/unit/test_mesh_serve_worker.py` may replace its
  old unauthenticated-envelope tests rather than merely append cases: the old
  constructor/protocol is deliberately removed by this story. The replacement
  must prove the authenticated offer plus local-admission path and may not restore
  a compatibility shim.
- **ADJACENT DEBT → backlog:** `intel/providers.py::_resolve_cloud_api_key` can
  fall back to an ambient default key when an unrelated caller supplies an empty
  key slot. The reduced mesh path always supplies its destination-derived slot,
  so no mesh execution reaches that fallback. Revisit only in a product-wide
  keyless-destination custody story.
- **ADJACENT DEBT → HS-131-11:** `kernel/dispatch_context.py` still describes the
  mesh receiver as a `LEGACY_UNCONTEXTUAL` scope after the census removes that
  family. Correct the stale code documentation in the entry-point contract story,
  not by widening this implementation.

## Proof and review protocol

- Fresh implementation agent in a new worktree at `e4193f12`; no continuation of
  the exhausted agent and no wholesale patch application.
- Salvage by reviewed hunk or small module only. The 151-path tree is a reference,
  never a source of implicit scope.
- Terra runs focused tests only. The orchestrator, not the implementation agent,
  owns the full backend/web gates after approved transfer.
- Freeze one complete tracked-plus-untracked fingerprint. One hostile review and
  one Terra verification read that exact source.
- Consolidate one finding brief. Three repair rounds stop for design/scope review;
  five rounds require an owner ruling.
- No evidence, acceptance flip, staging, contract, commit, push, CI, or PR action
  occurs before an explicit orchestrator SHIP decision.
