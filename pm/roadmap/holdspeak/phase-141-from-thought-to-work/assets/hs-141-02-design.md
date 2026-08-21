# HS-141-02 design beat — resumable thought custody and Ask correlation

**Status:** design for counsel; this document authorizes no product code, model dispatch, or UI.

## Decision and boundary

HS-141-01 already supplies the immutable raw/working aggregate and its four
cursors. HS-141-02 makes it safe to find, load, and recover without creating a
chat subsystem. It adds a narrow refinement-owned correlation ledger around the
existing Ask, kernel, projection-stage, receipt, and `ask_results` records.

```text
refinement thought --stable links--> Ask invocation / kernel operation / Ask result
                                  existing authorities --> dispatch and receipt
```

AskService and the kernel remain the execution authorities. The new ledger
records which frozen thought snapshot an existing Ask invocation belongs to and
whether a receipt-gated result exists for later owner review. It never copies
Ask payloads, hydrates browser context, or changes a working Note/lifecycle
because a model returned.

This story ships no Develop control, question prompt, Ask call, context picker,
availability logic, or review UI. Story 06 owns the owner-visible Good enough
completion and explicit completed-to-working resume semantics. HS-02 projects
those existing states but must not add another complete/reopen command or invoke
one on reload.

## Verified gap at `a957df48`

The current unfinished list returns every full DTO, has no bound/cursor, and
orders only on second-granularity `updated_at`
([`refinement_thought_service.py:88-96`](../../../../../holdspeak/services/refinement_thought_service.py#L88-L96),
[`refinement_thoughts.py:44-47`](../../../../../holdspeak/db/refinement_thoughts.py#L44-L47)).
The current one-thought DTO has no continuation/result identity
([`refinement_thought_service.py:249-259`](../../../../../holdspeak/services/refinement_thought_service.py#L249-L259)).

Ask creates `ask_<random>` inside `ask()` and immediately calls the runner
([`ask_service.py:117-161`](../../../../../holdspeak/services/ask_service.py#L117-L161)).
The broker creates `op_<random>` inside `submit`
([`broker.py:69-70`](../../../../../holdspeak/kernel/broker.py#L69-L70)); the
runner then reaches physical dispatch after admission and claim
([`inference_runner.py:196-230`](../../../../../holdspeak/kernel/inference_runner.py#L196-L230)).
Persisting a link only after `AskService.ask()` returns can therefore leave an
already-sent inference uncorrelated after a crash.

Reuse, rather than replace, the existing receipt-gated spine: a projection
stage binds an invocation to an operation
([`projection_stager.py:87-116`](../../../../../holdspeak/kernel/projection_stager.py#L87-L116));
finalization requires the matching terminal receipt
([`projection_stager.py:167-190`](../../../../../holdspeak/kernel/projection_stager.py#L167-L190));
and `ask_results` has unique stage/invocation/operation/receipt links
([`schema.py:1767-1795`](../../../../../holdspeak/db/schema.py#L1767-L1795)).

## Persisted shape

Keep the HS-141-01 aggregate and command ledger unchanged. Add these local
tables after `ask_results`. `canonical_sha256` is the existing canonical JSON
hash. IDs are opaque server-generated except the client request ID.

```sql
CREATE TABLE refinement_invocations (
  id TEXT PRIMARY KEY,                         -- rinv_…
  request_id TEXT NOT NULL UNIQUE,             -- caller-stable retry identity
  request_sha256 TEXT NOT NULL,                -- semantic metadata only
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  frozen_aggregate_revision INTEGER NOT NULL,
  frozen_working_revision INTEGER NOT NULL,
  frozen_attachment_revision INTEGER NOT NULL,
  review_result_id TEXT UNIQUE,                -- rresult_…, only with a verified result
  state TEXT NOT NULL CHECK (state IN (
    'reserved','in_flight','awaiting_projection','review_ready',
    'failed','refused','cancelled','indeterminate','unknown','stale','superseded'
  )),
  terminal_code TEXT NOT NULL DEFAULT '',      -- fixed control code, never provider prose
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, terminal_at TEXT
);
CREATE INDEX idx_refinement_invocations_resume
  ON refinement_invocations(thought_id, state, updated_at DESC);
CREATE UNIQUE INDEX one_live_refinement_invocation
  ON refinement_invocations(thought_id)
  WHERE state IN ('reserved','in_flight','awaiting_projection','review_ready');

CREATE TABLE refinement_invocation_attempts (
  invocation_id TEXT NOT NULL REFERENCES refinement_invocations(id),
  attempt_ordinal INTEGER NOT NULL CHECK (attempt_ordinal >= 1),
  ask_invocation_id TEXT NOT NULL UNIQUE,      -- ask_… then exact derived ask_…_r2
  kernel_operation_id TEXT UNIQUE,             -- op_…, bound by this attempt's hook
  projection_stage_id TEXT UNIQUE REFERENCES kernel_projection_stages(stage_id),
  ask_result_stage_id TEXT UNIQUE REFERENCES ask_results(projection_stage_id),
  receipt_id TEXT UNIQUE REFERENCES kernel_receipts(receipt_id),
  result_ref TEXT UNIQUE,
  state TEXT NOT NULL CHECK (state IN (
    'reserved','kernel_bound','in_flight','succeeded','failed','refused',
    'cancelled','indeterminate','orphaned_before_dispatch_binding'
  )),
  terminal_code TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL, bound_at TEXT, terminal_at TEXT,
  PRIMARY KEY (invocation_id, attempt_ordinal),
  UNIQUE (invocation_id, ask_invocation_id)
);

CREATE TABLE refinement_review_results (
  id TEXT PRIMARY KEY,                         -- rresult_…
  invocation_id TEXT NOT NULL UNIQUE REFERENCES refinement_invocations(id),
  attempt_ordinal INTEGER NOT NULL,
  ask_result_stage_id TEXT NOT NULL UNIQUE REFERENCES ask_results(projection_stage_id),
  ask_invocation_id TEXT NOT NULL UNIQUE,
  kernel_operation_id TEXT NOT NULL UNIQUE,
  receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
  result_ref TEXT NOT NULL UNIQUE,
  frozen_aggregate_revision INTEGER NOT NULL,
  frozen_working_revision INTEGER NOT NULL,
  frozen_attachment_revision INTEGER NOT NULL,
  result_sha256 TEXT NOT NULL,                 -- verified Ask projection hash
  created_at TEXT NOT NULL,
  FOREIGN KEY (invocation_id, attempt_ordinal)
    REFERENCES refinement_invocation_attempts(invocation_id, attempt_ordinal)
);
```

The semantic request hash contains exactly
`{request_id, thought_id, frozen_aggregate_revision, frozen_working_revision,
frozen_attachment_revision, purpose:"refinement"}`. It contains no raw/working
text, qualified ref, prompt, hydrated material, credential, destination, or
model output. Same request ID plus same hash returns the same correlation row;
a different hash is `409 refinement_request_payload_mismatch`.

The durable attachment link is
`(thought_id, frozen_attachment_revision, frozen_aggregate_revision)`, never a
naked integer or copied ref list. HS-141-01 correctly writes only attachment
revision zero. HS-02 must not add generic `context_json` or attachment child
records; HS-141-05 owns typed attachment revision rows. Every future nonzero
link must resolve server-side before reserve/dispatch. This preserves the
ratified HS-141-01 boundary while carrying the exact context revision that later
stories need.

`refinement_review_results` stores links and a hash, not another copy of
`ask_results.payload_json`. The existing receipt-gated Ask projection remains
the single durable response. A future owner-only review projection may select
owner-visible fields from that verified row, but list/sync/event DTOs never
receive the Ask payload.

| Identity | Stable creator | Meaning |
|---|---|---|
| `request_id` | caller once | idempotency identity for one owner request |
| `rinv_…` | refinement service | one logical refinement request and frozen thought snapshot |
| `ask_…`, `ask_…_r2` | attempt ledger / existing retry derivation | exact base or compatibility-follow-up Ask/kernel native identity |
| `op_…` | existing broker, one per attempt | admitted kernel operation bound before that attempt dispatches |
| stage ID / receipt / `result_ref` | existing projection stager, one per attempt | receipt-gated native result proof |
| `rresult_…` | reconciler | stable refinement review-result identity |

There is one live **logical** refinement invocation per thought, not merely per
working revision. It realizes the one-question law and prevents two tabs asking
two next questions. That logical invocation has immutable one-to-many attempt
rows: the base attempt is ordinal 1 and the existing dialect retry, when earned,
is ordinal 2 with the exact existing derived `ask_…_r2` identity. Both attempts
retain their own Ask ID, operation, stage, receipt, and terminal outcome.
Failed/refused/cancelled/indeterminate logical invocations remain history; a
later owner request has a new request and `rinv_…`. Stale/superseded results
remain linked to their frozen snapshot and never become current text.
`review_ready` is still live for this constraint: Story 04 must explicitly
supersede it when the owner accepts, edits, answers, or rejects the review
before another refinement request may reserve the thought.

## States and durable-before-dispatch order

Thought lifecycle remains `working | completed | tombstoned`. Invocation state
is a receipt/recovery ledger, never another thought lifecycle.

| From | Event | To | Durable effect |
|---|---|---|---|
| none | reserve (future HS-04) | `reserved` | validate owner/live Note/current cursors; commit `rinv_…` and immutable ordinal-1 `ask_…` attempt |
| attempt reserved | kernel admission | attempt `kernel_bound` | persist that attempt's broker `op_…` before physical dispatch |
| attempt kernel-bound | dispatch gate crosses | attempt `in_flight`; logical `in_flight` | hook must have durably permitted this exact attempt |
| base compatibility failure | existing runner retry rule | ordinal-2 attempt reserved | preserve base failed receipt; its own hook creates/binds exact derived `ask_…_r2` row before send |
| all attempts terminal non-success | receipt reconciliation | logical terminal state | retain fixed receipt/control codes; thought remains editable |
| winning success attempt | exact success receipt + stage + Ask result | `review_ready` | insert one `rresult_…` link; no Note/lifecycle write |
| review_ready | any frozen cursor differs now | `stale` | retain link; never present/apply as current |
| nonterminal | working Note missing or thought tombstoned | `superseded` | named custody refusal; no resurrection |
| reserved attempt with no kernel record after definitive lookup | reload | logical `unknown` | no claim that a provider ran |
| discoverable native op without attempt binding | reload | attempt `orphaned_before_dispatch_binding`; logical `unknown` | never bind/replay/result from it |

`awaiting_projection` means a known successful receipt whose native stage/result
is not yet materialized. Reconciliation may finalize an **existing** stage. It
may never submit, re-run, choose a model, or invent a provider result. Success
without an exact receipt-gated `ask_results` row is not a review result.

The required future dispatch sequence is:

1. In one transaction reserve the caller request, frozen aggregate/working/
   attachment cursors, `rinv_…`, and immutable ordinal-1 `ask_…`; commit.
2. Call an internal Ask entry point accepting that reserved `ask_invocation_id`.
   Current random-only `AskService.ask` is insufficient.
3. Add a narrow runner `before_physical_dispatch(operation_id, invocation_id,
   attempt_ordinal)` callback after admission/claim has generated `op_…` but
   immediately before `_dispatch`. It runs for **every physical attempt**,
   including the existing compatibility follow-up. It atomically validates the
   exact immutable attempt, writes that `op_…`, and marks it in flight. A
   callback failure/refusal means **zero provider dispatches** for that attempt.
4. On a compatibility signal the existing runner retains the base attempt's
   failed receipt and derives exactly one ordinal-2 ID. The ordinal-2
   pre-dispatch hook creates its immutable attempt row and binds its `op_…` in
   the same transaction, after verifying that exact base compatibility receipt,
   before its provider send. The compatibility retry remains one follow-up, not
   a new logical owner request.
5. Existing runner/stager writes attempt-specific stage and terminal receipt;
   existing Ask materializer writes `ask_results`. Reconcile inserts the one
   `rresult_…` only for the single successful attempt whose receipt, stage,
   result ref, and Ask row agree. If both attempt records could superficially
   qualify, that is `refinement_correlation_mismatch`, not a winner selection.
6. The resulting logical `review_ready` does not mutate Note, attachment,
   aggregate, or completed state. Story 04 owns explicit owner accept/edit/
   answer.

The current runner lacks the callback and therefore needs this seam. A
post-`ask()` write, a browser callback, or an AskPanel random ID is a blocker:
each permits an uncorrelated physical dispatch. The hook is a supplied domain
veto, not refinement policy inside the kernel. Its retry-aware contract is
essential: binding only the base ID would lose the earned `_r2` attempt or
misattribute its receipt.

## API / DTO contract

Every thought-bearing success and conflict DTO carries mandatory
`aggregate_revision`, `lifecycle_revision`, `working_revision`, and
`attachment_revision`. Zero attachment is a real cursor, never omitted.

### One thought

`GET /api/thoughts/{thought_id}`, authenticated owner only (never NODE/paired
sync authority):

```json
{"thought":{
  "id":"thought_…","state":"working",
  "aggregate_revision":7,"lifecycle_revision":1,"working_revision":4,"attachment_revision":0,
  "raw":{"available":true,"sha256":"…","captured_at":"…","source_kind":"typed"},
  "working_note":{"id":"note_…","title":"…","body_markdown":"…","tags":[],"deleted":false,"last_modified":"…"},
  "filing_status":"filed",
  "continuity":{"state":"idle|in_flight|review_ready|stale|named_failure|unavailable_remote",
                "invocation_id":"rinv_…?","review_result_id":"rresult_…?","code":""}
}}
```

Raw text stays only at `GET /api/thoughts/{id}/original`. Ordinary load omits
source ref. `continuity` omits prompt, hydrated context, destination
configuration, credentials, kernel/Ask payload, provider exception, operation
ID, and result body. A later Story-04 owner-review endpoint can use
`rresult_…` to project verified owner-visible result fields; it must never
return `ask_results.payload_json` wholesale.

### Bounded unfinished list

```text
GET /api/thoughts?state=unfinished&limit=20&cursor=<opaque; absent only on first page>
→ { items: [ThoughtListItem], next_cursor: string | null }
```

Unfinished means aggregate `state='working'`, including a live invocation.
Completed/tombstoned rows never enter. `limit` is strictly 1–50 (default 20
only for old clients). Returned continuation cursors are mandatory for later
pages; no offsets or client timestamps. An integrity-protected cursor contains
only `{version,state,high_water,last_resume_order,last_id}`; no content/ref/hash/
principal secret. First page fixes monotonic high water; later pages use stable
descending `(resume_order,id)` below it. A later change appears on a fresh first page, not
as a silent mid-page substitution.

```json
{"id":"thought_…","working_note_id":"note_…","title":"…","updated_at":"…",
 "state":"working","aggregate_revision":7,"lifecycle_revision":1,
 "working_revision":4,"attachment_revision":0,
 "continuity_state":"idle|in_flight|review_ready|stale|named_failure|unavailable_remote",
 "filing_status":"filed|missing"}
```

The list has no body, raw text/hash/ref, attachment refs, Ask/kernel IDs, result
text, prompt, hydrated context, credentials, or Ask payload.

### Reconcile

`POST /api/thoughts/{id}/reconcile` is owner-only and has no prompt/context/
model fields. It requires `expected_aggregate_revision` and accepts optional
`invocation_id` (`rinv_…`) so a stale tab cannot reconcile a newer request.
It returns the one-thought DTO. It is idempotent: it does only deterministic
lookups/finalization of existing records; it never calls `AskService.ask`,
constructs an `InvocationRequest`, hydrates refs, or writes a Note. It examines
attempts independently: the base and derived `_r2` attempt are not aliases.

If recovery discovers a kernel native operation for an expected Ask identity but
the matching attempt was never durably bound by its pre-dispatch hook, only the
continuity service may terminalize that attempt as
`orphaned_before_dispatch_binding` and terminalize the logical row as `unknown`
with that code. It records the discovered native ID only in server diagnostics,
not as a newly linked `op_…`. It must not rebind it, finalize its stage into a
review result, or re-dispatch it. A later owner retry is a fresh caller
`request_id` and new logical `rinv_…`, after the old logical row is terminal;
neither browser nor Ask service can recycle it.

## Ownership, stale/deleted facts, and Story 06 boundary

* `RefinementThoughtService` (or a narrow `RefinementContinuityService`)
  owns reservation, list/load, result-link insertion, and reconciliation.
* Ask owns server-side grounding/deployment/placement and native Ask result. It
  needs an internal reserved-invocation entry seam; normal `/api/ask` remains
  ordinary Ask and cannot receive a browser-supplied hidden refinement field.
* Kernel owns `op_…`, physical dispatch, and receipts. The supplied callback
  only vetoes before dispatch; it never makes authority/placement policy.
* ProjectionStager and `ask_results` own materialization. A continuity link is
  accepted only when the **one winning attempt's** stage, Ask ID, op ID,
  receipt, and `result_ref` agree.
* Existing aggregate `complete`/`resume` methods are lifecycle primitives
  ([`refinement_thought_service.py:146-154`](../../../../../holdspeak/services/refinement_thought_service.py#L146-L154)).
  Story 06 owns their owner-facing decision/receipt semantics. HS-02 does not
  call them and reconciliation cannot complete/reopen anything.

| Condition | Named result | Required behavior |
|---|---|---|
| working Note absent/deleted or aggregate tombstoned | `thought_tombstoned` | HS-141-01 terminal fence wins; no list/review resurrection |
| aggregate completed | `thought_completed` | load normally; no new reserve until Story-06 explicit reopen CAS |
| nonzero attachment rev absent/deleted (after HS-05) | `thought_attachment_revision_missing` | no dispatch/current result |
| current cursor differs from frozen | `refinement_result_stale` | retain immutable link, do not apply |
| reserved Ask has no kernel row after recovery | `kernel_operation_missing` | named unknown, no inferred dispatch/retry |
| discoverable native op lacks durable attempt binding | `orphaned_before_dispatch_binding` | terminal unknown; never rebind, finalize, or redispatch |
| receipt/stage/Ask IDs disagree | `refinement_correlation_mismatch` | refuse link; server diagnostics only |
| success receipt but no receipt-gated Ask result | `ask_result_unpublished` | await/unknown, never fabricate answer |

Deletion of a raw source Note does not delete the immutable stored raw bytes.
Deletion of the working Note is different and terminalizes custody. Missing
filing is only `filing_status: missing`, never an automatic refile.

## Fault / concurrency matrix

| Fault or race | Required outcome |
|---|---|
| response lost after reserve | same request/hash returns exact `rinv_…` / `ask_…`; changed payload conflicts |
| two tabs reserve | one live-row transaction wins; loser receives current continuity/cursors |
| edit/attach/complete after reserve, before hook | callback rejects before provider dispatch |
| edit/attach after physical dispatch | result stays frozen and reconciles stale; it never overwrites Note |
| crash before kernel admission | reserved/no op; no inference claim |
| crash after admission before hook commit | no hook permission means no provider send; named recovery, no created result |
| crash after hook before/while send | durable op link; reload reads known receipt/stage, never blind reissues |
| provider returns before browser response | existing receipt/stage/Ask row reconciles to one `rresult_…` |
| success receipt but stage missing/discarded | `ask_result_unpublished`; no review content |
| tombstone before late result | terminal fence wins; late link cannot revive thought |
| result-link retry | unique invocation/stage/result keys return existing result only if all IDs/hash agree |
| paired peer loads a synced thought | continuity is `unavailable_remote`; it receives no local native proof IDs or result claim |
| paired peer asks to reconcile hub-local continuity | `continuity_unavailable_remote`; no remote lookup, inferred result, or redispatch |

Continuity/invocation/result links are hub-local and are **not paired-sync
replicated**. Their foreign keys point at native kernel/stage/receipt/Ask-result
proof rows that are local to one hub; copying their names would manufacture a
false proof and break both foreign-key and privacy contracts. The synced thought
bundle therefore carries no invocation, attempt, `op_…`, stage, receipt,
`result_ref`, or `rresult_…` identity. A paired peer projects
`continuity_state: unavailable_remote` and names
`continuity_unavailable_remote` on explicit reconcile; it never queries a
remote hub, claims a result exists, or reissues work. The local hub may still
retain its immutable links for its own restart reconciliation.

## Exact implementation and proof anchors

Expected owned source seams:

* `holdspeak/db/schema.py` after `ask_results` — correlation/link tables and
  list index ([lines 1767-1795](../../../../../holdspeak/db/schema.py#L1767-L1795)).
* `holdspeak/db/refinement_thoughts.py` — in-transaction keyed list and
  correlation/reconciliation lookups; replace whole-table list
  ([lines 26-62](../../../../../holdspeak/db/refinement_thoughts.py#L26-L62)).
* `holdspeak/services/refinement_thought_service.py` — privacy-aware load/list
  DTOs and named recovery; preserve existing owned-Note CAS
  ([lines 98-144](../../../../../holdspeak/services/refinement_thought_service.py#L98-L144)).
* `holdspeak/web/routes/primitives/thoughts.py` — paged list/reconcile
  transport only ([lines 33-106](../../../../../holdspeak/web/routes/primitives/thoughts.py#L33-L106)).
* `holdspeak/services/ask_service.py` — later reserved-ID Ask seam; preserve
  ordinary `/api/ask` behavior ([lines 117-173](../../../../../holdspeak/services/ask_service.py#L117-L173)).
* `holdspeak/kernel/inference_runner.py` — pre-dispatch callback before
  current `_dispatch`; a failed callback must reach zero provider calls
  ([lines 196-230](../../../../../holdspeak/kernel/inference_runner.py#L196-L230)).
* `holdspeak/kernel/ask_projection.py` and `kernel/projection_stager.py` —
  consume, do not duplicate, the receipt-gated native result
  ([`ask_projection.py:12-32`](../../../../../holdspeak/kernel/ask_projection.py#L12-L32)).
* `holdspeak/services/sync_service.py` — explicitly exclude hub-local
  continuity/attempt/result links; never generic-merge or fabricate them.

Focused proof matrix (no browser or model fixture):

1. `tests/unit/test_refinement_thought_service.py`: one-thought/list privacy,
   cursor bounds/order/high-water/tie, mandatory cursors, tombstone/completed
   read behavior, and idempotent reconcile.
2. `tests/unit/test_web_routes_thoughts.py`: owner authority, no raw/source
   ref/body leakage in list, malformed/foreign cursor, and named stale/deleted
   results.
3. New `tests/unit/test_refinement_continuity.py`: reservation idempotency,
   one-live race, base plus compatibility-follow-up attempt provenance, frozen
   attachment link, exact single-winning-result linkage, lost response,
   orphan-before-binding terminalization, unknown/mismatch legs, and restart
   recovery.
4. Extend `tests/unit/test_ask_runner_migration.py` and
   `tests/unit/test_inference_runner.py`: supplied stable Ask ID, callback is
   durable-before-adapter dispatch, callback failure dispatches zero times, and
   ordinary Ask remains behavior-equivalent.
5. Extend `tests/unit/test_web_routes_sync_primitives.py` and
   `tests/integration/test_primitive_framework_sync.py`: thought custody still
   converges while all local continuity/attempt/result rows are excluded; paired
   load/reconcile reports `unavailable_remote` rather than an invented result.

## Counsel questions

## Counsel amendment — ordering and retry lineage

`refinement_thoughts.resume_order` is a local monotonic sequence allocated in
the same transaction as create, working edit, lifecycle transition, tombstone,
and incoming sync application. Old rows are deterministically backfilled; list
cursors fence and order by this integer, never timestamps, so same-second
inserts cannot disappear between pages.

Dialect retry has a durable `refinement_retry_plans` lineage row before the
derived child is admitted: `{logical invocation, parent ordinal 1, child ordinal
2, retry_invocation_id(base,2), fixed dialect reason}`. The child pre-dispatch
hook requires that exact plan and the base failed receipt. An arbitrary failed
receipt or forged child ID refuses. The full result winner tuple is exact native
receipt + matching attempt Ask ID + published `ask-result` stage (same
invocation/operation/receipt/result ref) + matching Ask result and projection
hash. Multiple apparent winners or a mismatch refuse; retry verifies an existing
review row against that full tuple.

Product `get`, `original`, list, and reconcile are OWNER-only. Paired sync is a
separate internal authority which copies only thought custody and omits all
local continuity rows; it does not receive product DTOs or raw continuity.

1. Is the generic runner pre-physical-dispatch veto the smallest lawful seam for
   persisting broker-generated `op_…` before provider send?
2. Does deferring concrete attachment child rows to HS-141-05 preserve the
   HS-141-01 ruling while retaining the exact attachment revision link now?
3. Does returning only continuity/result identity—not response text or Ask
   payload—correctly keep this daily-custody beat out of Story-04 review UI?
