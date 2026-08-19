# HS-141-06 design beat — Good enough means done

**Status:** implementation design; no model, setup, context, proposal, tool, or
external-effect work is authorized by this slice.

## Decision

`Good enough` is one owner-authorized, local completion command for the existing
working Note. It never clones, files, rewrites, or deletes the Note. In one
transaction it advances the refinement aggregate from `working` to `completed`,
writes the existing immutable lifecycle/aggregate command rows, and creates one
durable local completion receipt keyed by the caller-stable completion request.
The completed Note remains in its existing Inbox or owner-selected directory
membership. No model or other product state changes.

```text
working Note (same note:<id>)
  └─ Good enough(request id + aggregate/lifecycle CAS)
       ├─ complete lifecycle + aggregate command + local receipt (one tx)
       └─ completed Note: read-only, Original kept, Done receipt
  └─ Resume refining (later explicit lifecycle CAS)
       └─ working Note (same note:<id>)
```

The active thought editor remains local-only. Its serialized save queue must be
flushed and its final accepted Thought DTO observed before the completion call.
Thus completion always uses the last local working cursors; it cannot race a
debounced write and discard the owner’s final keystroke.

## Durable contract

Add `refinement_completion_receipts`, an aggregate-adjacent local receipt table
(not an external proposal or second lifecycle):

```sql
CREATE TABLE refinement_completion_receipts (
  receipt_id TEXT PRIMARY KEY,                -- rcomp_…; stable owner receipt
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  request_id TEXT NOT NULL UNIQUE,            -- caller-stable lost-response key
  request_sha256 TEXT NOT NULL,               -- thought + expected aggregate/lifecycle
  aggregate_revision INTEGER NOT NULL,
  lifecycle_revision INTEGER NOT NULL,
  working_note_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (thought_id, aggregate_revision)
);
```

The receipt row, completion lifecycle entry, aggregate command, and thought
state update commit under one `BEGIN IMMEDIATE`. Its semantic request hash is
canonical JSON of exactly `{thought_id, expected_aggregate_revision,
expected_lifecycle_revision}`. It contains no raw or working text.

`POST /api/thoughts/{thought_id}/complete` requires `request_id`,
`expected_aggregate_revision`, and `expected_lifecycle_revision`, and returns:

```json
{"thought": {"state":"completed", "aggregate_revision":8, "lifecycle_revision":3, "…":"mandatory cursors"},
 "receipt": {"id":"rcomp_…", "kind":"thought_completed", "thought_id":"thought_…",
             "note_ref":"note:note_…", "aggregate_revision":8}}
```

Exact request retry returns that same completed DTO and receipt. A request-ID
payload mismatch is `completion_request_payload_mismatch`. A retry after a
later Resume/edit does not resurrect completion: it returns a named
`completion_request_superseded` conflict with current cursors. A new request
against stale cursors returns the existing `thought_revision_conflict` current
DTO. The completion receipt is local proof and is deliberately not sync payload:
the existing immutable aggregate completion command is what peers synchronize.
Receipt replay is scoped to the originating hub: only the hub that committed
that request ID may return its receipt. A paired hub which learns the completion
through command sync has no receipt row and must return named
`thought_already_completed` plus its current DTO—not fabricate a receipt or
pretend it observed the originating request.

## Authority boundary

All public product commands are **OWNER-only**: thought create, Note adoption,
working-Note update, **Good enough**, **Resume refining**, and tombstone, as
well as generic owned Note `PUT`/`DELETE`. The old receipt-less `complete()`
entry point is retired from public routing (or made internal behind the same
receipt/CAS contract); no route may bypass the request ledger. A paired `NODE`
principal must be rejected by all of those public routes and service command
entry points even if it knows the exact thought, Note, request ID, and cursors.

`NODE` authority is deliberately narrower and sync-only. It may reach only
the signed, validated paired-sync aggregate install/fast-forward path in
`sync_service.py` and its aggregate install helpers. That path verifies the
pair/signature and command ledger before applying a lawful remote transition;
it is not a substitute for a browser completion/resume command and it cannot
write arbitrary owned Notes. Thus a valid paired peer may converge a completed
aggregate, while direct paired-node `POST /complete`, `POST /resume`, and owned
Note mutation remain forbidden.

## State/CAS law

| Current aggregate | Request | Result |
|---|---|---|
| `working`, exact aggregate + lifecycle cursors | first Good enough | lifecycle/aggregate +1, state `completed`, receipt atomically stored |
| `completed`, same request ID + same semantic hash + same completed revision | lost-response retry | exact stored receipt + completed DTO; no new command/Note |
| `completed`, same request ID after later aggregate movement | stale retry | `completion_request_superseded` + current DTO; no state change |
| `working` or `completed`, wrong current cursors/new request | stale command | `thought_revision_conflict` + current DTO |
| `tombstoned` | any completion | named terminal conflict; no receipt/write |
| `completed`, explicit Resume with aggregate/lifecycle CAS | Resume refining | state `working`, lifecycle/aggregate +1; same Note and raw |

Completion neither changes `working_revision` nor membership. It assigns a new
`resume_order` like the established lifecycle transition; the completed row is
excluded from `state='working'` Resume list and stays findable through the
ordinary Note surfaces.

## UI composition

`ThoughtNoteEditor` gains a narrow imperative `flush()` boundary owned only by
`NotePullout`. On the synchronous start of `Good enough`, it sets a finishing
fence before any `await`: reject further local edits, cancel the debounce, and
disable the sole primary as `Finishing…`. It then drains request A if in flight;
if accepted local edit B was already queued, it sends B serially on A's returned
cursors and drains that request too. Only when the save machine has no dirty
draft, no in-flight request, and the current authority epoch is established may
`flush()` return the latest authoritative Thought DTO and allow completion.

A save conflict/generic failure, parent-authority install, or changed epoch
clears the finishing fence and makes no completion call. Conflict installs the
current DTO and leaves the Note truthfully editable only after an explicit new
owner edit; generic failure retains the local draft with its retry state. Thus
the editable working Note remains useful and `Good enough` never completes a
version earlier than a locally accepted A→B edit sequence.

Working, not editing:

* quiet: `Copy`, `Edit`;
* sole primary: **Good enough**.

Working, editing:

* quiet: `Cancel`;
* sole primary: **Good enough**. It reads `Finishing…` while flush/complete is
  pending; there is no competing Save decision.

On success the same pullout stays open, exits editing, and renders the normal
read-only working Note plus `Original kept` and the concise truthful receipt
**Done**. This slice does not resolve a human directory name, so it never
guesses Inbox or another drawer in the receipt. Its only primary is **Resume refining**. Completed
re-entry is also read-only and offers exactly this lifecycle-CAS verb; it never
routes to generic Edit, which the aggregate correctly refuses.

At 393px the sole primary is full width. Quiet Copy/Original/other secondary
actions stay folded or non-primary; there is no horizontal overflow and no
model/setup console.

### Recovery copy

| Condition | Copy | Recovery |
|---|---|---|
| pending local flush/complete | **Finishing…** | one disabled primary; no second Save |
| success | **Done** | stable receipt remains while pullout is open |
| exact lost-response retry | same Done receipt | client retains request ID until receipt |
| stale working/current newer | **This thought changed elsewhere. Your latest version is shown. Review it, then try Good enough again.** | install current DTO; no automatic retry |
| already completed from another owner action | **This thought is already done.** | show completed read-only state and Resume refining |
| ambiguous completion/read failure | **We couldn't confirm whether this was completed. Retry Good enough.** | retain same request ID; no false Done |

## Contract self-audit

* **HS-141-01:** uses the existing lifecycle and aggregate clocks; no raw or
  Note metadata mutation; only the associated receipt table is new. The
  completion command remains sync-valid (`complete`) and peers never need the
  local retry receipt to converge.
* **HS-141-02:** completed is already a lifecycle state; Resume is explicit and
  working-only list membership is unchanged. No Ask/invocation dispatch or
  result state is introduced. Completion's frozen-state hook vetoes later
  dispatch, while reconciliation terminalizes any already-existing invocation
  continuity; this slice does not claim a new atomic invocation supersession.
* **HS-141-03:** builds on the thought-owned Note query/editor, preserves the
  Original cue and qualified Inbox membership, and reuses its serialized save
  authority rather than generic Note PUT. The only API client extension is
  complete/resume/receipt typing.
* **Authority:** public create/adopt/update/complete/resume/tombstone and
  generic owned Note mutation reject `NODE`; only signed paired-sync ledger
  install/fast-forward accepts `NODE`. A peer can converge a valid remote
  completion without gaining a second public command path or an ability to
  overwrite an owner’s working Note.
* **Charter/proposal:** Good enough is owner authorization, not confirmation;
  it is useful with no model and remains one primary action at 1440/393.
  No tool, context, model, setup, filing promise, or external effect is added.

### History wording stop

The story asks to preserve “refinement history access,” but the current product
has no owner-visible history route or truthful history projection—only the
durable aggregate/lifecycle/working ledgers. This slice preserves those ledgers
and Original access, but must not add a fake `History` affordance. Before close,
the story wording should be amended visibly from “preserve … history access” to
“preserve durable refinement history for subsequent lawful history UI,” unless
a separately scoped owner-readable history projection is authorized.

## Exact seams and tests

* `holdspeak/db/schema.py` — additive local completion receipt table only.
* `holdspeak/services/refinement_thought_service.py` — transactional complete
  receipt/idempotency/CAS result; existing resume lifecycle transition; explicit
  OWNER command guard separate from sync-node install guard; receipt-less
  completion made internal or removed from public use.
* `holdspeak/services/sync_service.py` — signed paired-sync validation and the
  sole NODE-authorized aggregate install/fast-forward seam.
* `holdspeak/web/routes/primitives/thoughts.py` — request ID and `{thought,
  receipt}` route projection.
* `web/src/desk/thoughts.ts` — completion/resume receipt DTO client.
* `web/src/desk/pullouts/editors/ThoughtNoteEditor.tsx` — serialized flush
  contract, no direct AI/model work.
* `web/src/desk/pullouts/NotePullout.tsx` — working/completed primary
  composition, receipt/copy/recovery, flush before complete.
* focused service/route/sync regression tests plus editor/pullout tests for
  flush → complete, exact A-save → accepted B-save → Good-enough sequencing,
  response-loss exact retry, stale conflict, completed reopen → resume, and 393
  primary/CSS contract.
* authority-matrix regressions: `NODE` is denied every public create/adopt/
  update/complete/resume/tombstone command and generic owned Note `PUT`/`DELETE`;
  a valid signed paired completion ledger bundle alone still
  installs/fast-forwards and converges on the peer.
* two-hub receipt regression: the originating hub's exact retry returns its
  committed DTO plus stable receipt; after command sync, the paired hub returns
  named `thought_already_completed` plus current state, with no invented
  receipt, extra command, membership, or Note.

## Source anchors checked

* Story: `story-06-good-enough-means-done.md:9-30`.
* Lifecycle implementation: `holdspeak/services/refinement_thought_service.py:312-343`.
* Completion/resume route: `holdspeak/web/routes/primitives/thoughts.py:128-150`.
* Aggregate ledger: `holdspeak/db/refinement_thoughts.py:93-137` and
  `holdspeak/db/schema.py:817-885`.
* Existing owned editor/pullout:
  `web/src/desk/pullouts/editors/ThoughtNoteEditor.tsx`
  and `web/src/desk/pullouts/NotePullout.tsx`.
* Phase laws: `current-phase-status.md:28-43, 66-94`; proposal §§2–4.
