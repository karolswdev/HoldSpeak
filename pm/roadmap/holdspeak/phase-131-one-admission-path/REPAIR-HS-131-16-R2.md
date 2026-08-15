# HS-131-16 reduced candidate — repair round 2

**Status:** SHIPPED AT OWNER FUNCTIONAL BAR (2026-08-14)
**Reviewed source:** 33 paths / 380,139 bytes at `e4193f12`
**Reviewed manifest:** `e48fe5eaefb0bc181563f44b7b7eef04223a6a7fe992d74ab2565f3d1e501781`
**Reviewed complete diff:** `419fcfaa7549d575c168529dc91355cd7b977d556ff0dda6fe7d52d85813a7ca`
**R1 executable gate:** 574 passed, 1 environmental skip, 0 failed; source unchanged
**Hostile verdict:** **FAIL** — nine product defects plus one transactional-proof deficit
**Final source:** 40 paths; manifest `24e25287380abcbad6527d5037f051afccbf155620059b38f11069f8085b1413`; complete diff `17cb83aaf53082bfccf1e963b942c7304e43fad8f76aca2038fea4e018b14450`
**Final gates:** 864 focused + 4,643 full-unit candidate-lane tests passed
**Owner ruling:** no R3 hostile repair; concrete functional reds repaired; orchestrator SHIP

## Ruling

R1 repaired real defects, and the attached executable matrix is green. Green is
not enough: the second hostile read found ordinary paths that still violate the
settled protocol. This is the second reduced repair round, consolidated once.
A fresh implementer owns it; the R1 agent is retired. If the next review fails,
entering a third repair round requires the ORCHESTRATION three-round stop and a
new design/scope ruling before any patch.

The owner's realism bar removes no item below: each has an ordinary CLI,
credential, deadline, process, or protocol trigger. Hardware attestation, TLS,
persistent outbox, global fork/signal policy, constant-time purity, and custody-
compromise-only hardening remain out.

After R2 implementation, the owner stopped this process for repeating the same
failure in academic form: too much hostile protocol work, not enough functional
product focus. The final attached union produced one concrete red only:
`test_one_path_cardinality.py` still used an unpaired fake node after R2.5 removed
that fallback. The final candidate repairs it through the real pairing seam, plus
three demonstrated schema-v59 assertions and the broker density guard. The
scheduler-sensitive 8 ms timeout proof was narrowed to the transport seam it
actually claims. The 46-file functional matrix and candidate unit lane are green;
remaining hostile hypotheses are notes and no R3 brief was opened.

## R2 design clarifications

### Content-free independent authority expectation

R3's worker projection remains warrant-free, but it may carry one content-free
`authority_expectation` sibling derived directly from the persisted queue row and
kernel envelope inside the claim transaction. It contains only exact operation
ID/kind, destination node ID/generation, relay and execution revision IDs,
warrant binding, ordinal, and bounded deadlines. The signed offer binds the
canonical hash of that projection. The worker recomputes the hash and compares
every semantic field before reservation. Product payload remains a separate exact
projection and hash. No warrant, signature secret, claim witness, context,
credential, prompt copy, proof row, status, result, or error joins authority
metadata.

This catches crossed/stale hub construction and wire swaps without inventing a
third authority factor. A malicious hub signer remains inside the design's stated
compromise boundary.

### HTTP 5xx delivery ruling

R1 is amended narrowly: a structured 4xx is a terminal named protocol refusal;
a malformed/wrong-cohort 2xx is a terminal acknowledgement refusal. A 5xx means
the hub did not acknowledge and may retry the **same immutable report** within
the signed count/deadline bounds, then end as fixed `mesh_hub_unavailable`.
No response body or exception text enters proof. This preserves useful delivery
without rerunning the model or misnaming a 4xx as transport loss.

## Sustained repairs

### R2.1 — Bind the offer to independent live expectations

Add `authority_expectation` and its signed canonical hash as ruled above. Worker
verification compares valid alternate operation IDs, operation kind
`inference.invoke@1`, valid alternate warrant bindings, fully self-consistent
alternate relay/execution revisions, destination/generation, ordinal, and
bounded deadlines before replay reservation or any local persistence/work.

The hub's live-authority read must verify the persisted kernel operation's actual
name/version, not write the expected constant into an offer regardless of state.
Tests use correctly signed, grammatically valid alternate values—not malformed
stand-ins—and assert zero reservation, revision, runner, engine, or dispatch.

### R2.2 — Put every production serve mode under one worker owner

`run_once()` and `run_forever()` enter the same owner-lock scope before startup
reconciliation, claim, or reservation. Two real ordinary CLI processes against
one worker HOME cannot touch the ledger concurrently; after the owner exits, the
next process may reconcile residue. A failed terminal reservation CAS on **every**
path, including local refusal, is lost ledger authority and halts serving.

### R2.3 — Elect stop versus first publication

Add one lock-protected terminal-publication election. If stop wins before the
first `/complete` or `/fail` send begins, discard the body and send nothing. If
publication wins first, later stop cannot unsend it and byte-identical bounded
retransmission continues. Stop during claim, local execution, receipt-to-report,
and the pre-send interval each receive deterministic proof. Do not redefine a
cancelled local receipt as permission to publish after stop won.

### R2.4 — Preserve one monotonic instant through physical dispatch

Carry an absolute monotonic deadline, not a duration that can restart. Recompute
remaining time immediately before admission, watchdog creation, engine/provider
dispatch, retry sleep, and every HTTP request. The existing `InferenceRunner`
receives a surgical immediate pre-dispatch deadline fence if its current contract
cannot enforce this; that conditional path is now demonstrated and approved.
Derive any wall deadline/timer from the latest remainder. Remove the 50 ms request
floor; no request starts when no usable remainder remains, and sleeps cannot
overshoot.

Prove persistence/admission/construction consumption and a sub-50-ms remainder,
not only a multi-second timeout.

### R2.5 — Delete name-only liveness from the admitted path

No pairing, unreadable pairing, revocation, or generation mismatch is an
immediate fixed refusal. Never enqueue `("", 0)` and never fall back to a name-
only timestamp. Hold node custody across the exact pairing read, exact
`(node_id, generation)` liveness check with `0 <= age <= window`, and enqueue so
rotation/re-pair cannot split them. G1 cannot make G2 live.

### R2.6 — Refuse every unknown or malformed custody shape before interpretation

Check document schema before reading `nodes`. A future/unknown schema, a known
schema with non-dictionary nodes, or any malformed node entry raises one fixed
custody refusal and cannot be rewritten by create/rotate/re-pair. V1 migration is
lossless for every node or refuses without write. Tests cover unknown schema plus
non-dict nodes and malformed entries, then assert original bytes unchanged.

### R2.7 — Use one fixed terminal failure vocabulary

Define one shared explicit `SAFE_FAILURE_CLASSES`. The worker maps every unknown
local exception/reason to a fixed generic class; the hub rejects any report value
outside the set. Test short content-bearing tokens that satisfy the old regex
(`credential`, `prompt`, `token`) in a valid-MAC report and prove no persistence.

### R2.8 — Preserve refusal names and distinguish HTTP response from delivery loss

Parse a strict structured 4xx error body and surface its fixed `code` once. A
malformed 2xx or wrong acknowledgement is terminal protocol refusal. A 5xx may
retry only under the clarification above; after exhaustion it becomes fixed
`mesh_hub_unavailable`. Socket/connection/timeout failure remains bounded delivery
retry. Tests must not label 5xx as transport, and no raw body/exception escapes.

### R2.9 — Export one credential generation atomically

One `NodeTokenStore` method returns the public snapshot and bearer token from one
document under one custody lock. Pairing export builds only from that exact
snapshot; rotation/re-pair cannot mix G1 identity/pin with a G2 token. Add the
barrier race and prove imported transfer authenticates to its matching generation
or export refuses cleanly.

### R2.10 — Make claim and settlement one-connection elections and prove both winners

Repository callbacks receive the outer `BEGIN IMMEDIATE` connection. Every queue,
kernel-operation, warrant, deadline, duplicate/conflict, and terminal update read
that determines claim/settlement uses that same connection; no nested repository
checkout creates a second snapshot. Thread the connection or issue narrow direct
queries inside the mesh repository/authority seams—do not change generic database
connection machinery.

Use independent real SQLite connections/process barriers for both winner orders:
rotate/revoke versus claim commit, and cancel/revoke/expiry/conflicting report
versus first settlement. The loser signs/settles nothing and terminal proof is
unchanged. Sequential fake-store mutation is supplemental, not this proof.

## Approved path activation

The 40-path ceiling remains. The conditional existing path below is now activated
only for R2.4 and its focused proof:

```text
holdspeak/kernel/inference_runner.py       # immediate deadline fence only
tests/unit/test_inference_runner.py        # exact pre-dispatch deadline proof only
tests/unit/test_mesh_relay_provider.py     # R2.5 pairing/liveness regression only
```

`tests/unit/test_mesh_relay_provider.py` is activated after the implementer
produced the exact before/after regression: six existing tests created only a
name-stamped, unpaired node and therefore depended on the R2.5 fallback that must
be deleted. Repair them through the real paired-node store and assert the fixed
absence/offline/generation refusals; do not preserve a test-only compatibility
path.

All other work stays inside the 33 current paths. `holdspeak/kernel/journal.py`,
generic connection/database files, observer files, and every previously forbidden
surface remain out. If R2.10 cannot use the outer connection without another
path, stop before edit for an explicit ruling.

## Re-verification

Freeze one new complete fingerprint. Run the exact 30-file attached matrix under
a fresh isolated HOME and read complete output. One bounded hostile re-review then
tries to refute R2.1–R2.10 on the same bytes. No evidence, story flip, stage,
contract, commit, push, CI, or PR action precedes an explicit SHIP decision.
