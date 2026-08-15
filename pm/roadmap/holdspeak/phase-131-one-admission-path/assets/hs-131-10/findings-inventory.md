# HS-131-10 — model-execution inventory and final disposition

**Generated from:** `tests/unit/test_one_path_census.py` over production
`holdspeak/**/*.py` (tests excluded).

**Census date:** 2026-08-14.
**Disposition:** **CLOSED AT ZERO.** All five owner-chartered amendments,
HS-131-13 through HS-131-17, landed. Every one of the original eleven finding
families left by deletion or admission; no family became an adapter exception.

## Final census result — after HS-131-17

| Bucket | Function scopes | Executable sites |
|---|---:|---:|
| `AUTHORIZED_GATEWAY` | 2 | 1 context mint |
| `CLAIM_WITNESS_MINT` | 2 | 2 witness-issuer sites |
| `GATEWAY_FACTORY_BINDING` | 1 | 1 default-factory binding |
| `ADAPTER_ALLOWLIST` | 55 | 69 |
| `ADMITTED_SEAM_CALLERS` | 18 | 27 |
| `NAMED_FINDINGS` | — | **0** |
| Unregistered | — | **0** |
| **Total** | — | **100** |

The authorized gateway remains exactly `InferenceRunner._attempt` and
`InferenceRunner._dispatch`; public `InferenceRunner.invoke` orchestrates the
permitted attempt sequence and names no physical target. The one-shot issuer
installation at `ExecutorPlane` module scope, witness issuance in
`ExecutorPlane.claim`, and the default-factory reference in
`InferenceRunner.__init__` remain classified separately, not as adapters.

Every allowlisted factory validates the opaque, runner-issued `DispatchContext`
before construction. Execution leaves are reachable only through the dispatch
context carried by that admitted child. A context consumes the single-use witness
from the successful claim and binds the exact child operation, immutable
deployment revision, destination, positive attempt ordinal, and child warrant
basis. Missing, null, duck-typed, directly constructed, copied, wrong-operation,
wrong-revision, wrong-destination, wrong-attempt, invented, and replayed contexts
refuse by name before physical work.

The census recognizes existing-client SDK calls and first-class references such
as `client.chat.completions.create`, including literal
`getattr(receiver, "model_verb")` and SDK-chain getters regardless of the
container that holds them, without classifying availability probes or unrelated
repository/store `.create` methods. Physical cardinality is counted at the cloud
SDK, llama.cpp, mesh enqueue, and Whisper backend edges, not at engine
construction.

## Complete eleven-family disposition

| Original family | Owner | Final disposition |
|---|---|---|
| `cadence` | HS-131-13 | **Admitted.** Request-time drafting opens an authenticated bounded parent and exact-revision child. |
| `decisions-route` | HS-131-13 | **Deleted.** The duplicate route-side model seam is gone. |
| `delivery-legacy-factory` | HS-131-13 | **Deleted.** Dormant Delivery review and its uncontextual target factory are gone. |
| `plugin-default-provider` | HS-131-14 | **Deleted.** Builtins and `segment_probe` receive an admitted dispatch handle rather than constructing/caching providers. |
| `legacy-uncontextual-factory` | HS-131-14 | **Deleted.** The public configured-provider factory is gone; its private body is dominated by exact context validation. |
| `dictation-dry-run` | HS-131-15 | **Admitted when provider-backed; lexical otherwise.** Browser rehearsal/replay/template-preview mint no parent when no model work exists. |
| `dictation-command` | HS-131-15 | **Admitted.** Authenticated CLI dry-run opens a fresh bounded text-entry session. |
| `mesh-receiver` | HS-131-16 | **Admitted.** A hub-signed, node-bound, single-use offer verifies before worker-local `InferenceRunner` execution and its immutable local receipt. |
| `dormant-mir` | HS-131-17 | **Deleted.** Private session MIR flags, plugin enumeration, and post-stop `process_meeting_state()` are gone; deferred routing remains separately admitted. |
| `legacy-live-meeting-engine` | HS-131-17 | **Deleted.** Meeting startup reads frozen plan readiness and constructs no parallel `MeetingIntel`. |
| `bookmark-auto-label` | HS-131-17 | **Admitted.** Automatic refinement reaches `_admitted_bookmark_label`; deterministic/no-context/refused/failed/cancelled paths dispatch nothing or preserve the timestamp label. |

## Amendment ledger movement

| Checkpoint | Sites | Pinned findings | Blocking families | Unregistered |
|---|---:|---:|---:|---:|
| HS-131-10 blocked checkpoint | 145 | 48 | 11 | 0 |
| After HS-131-13 | 134 | 38 | 8 | 0 |
| After HS-131-14 | 105 | 6 | 6 | 0 |
| After HS-131-15 | 105 | 4 | 4 | 0 |
| After HS-131-16 | 103 | 2 | 3 | 0 |
| After HS-131-17 | **100** | **0** | **0** | **0** |

The count falls because executable sites were deleted or product callers moved
onto already-censused admitted seams. No command, meeting-session product module,
or other domain service was added to `ADAPTER_ALLOWLIST`. The final meeting
entries on that list are only the six pre-existing admitted dispatch closures
(live/deferred analysis, bookmark label, and auto-title), each marked as a leaf
inside one claimed child.

## Executable closure proof

The retired names remain dangerous even though their findings are gone. The
mutation matrix retypes direct/provider paths for all amendment families and
requires exact `UNREGISTERED_MODEL_EXECUTION` failures. HS-131-17's mutation in
particular restores both config-time `MeetingIntel` construction and the direct
`generate_bookmark_label` call; both are rejected by name. The clean census then
returns the 100/0/0 result above.

The companion one-path suites prove all named product surfaces traverse the
literal admission → claim → dispatch → immutable-terminal spine; provider
cardinality equals invocation-child and terminal-receipt cardinality across
success, failure, retry/fallback, cancellation, and indeterminate recovery; each
child carries causation, exact revision, and authenticated authority; and prompt,
token, transcript, dictation, and audio material stays out of kernel rows.

## Owner ruling satisfied

The 2026-08-12 ruling chartered HS-131-13 through HS-131-17 and prohibited any
finding from entering `ADAPTER_ALLOWLIST`. That condition is now satisfied in
full. HS-131-10 may close; HS-131-11 and HS-131-12 are unblocked.
