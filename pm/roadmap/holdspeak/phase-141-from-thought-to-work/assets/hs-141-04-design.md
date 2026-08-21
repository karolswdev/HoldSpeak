# HS-141-04 design beat — one useful question

**Status:** design for counsel. This authorizes no product edits, model call,
context attachment UI, proposal, tool work, or PMO change.

## Tuesday flow — the actual owner walkthrough

Tuesday starts with an already-developed working Note. The owner opens it from
Inbox or **Resume unfinished thoughts**, sees the durable local text and
`Original kept`, and presses **Keep refining**. That is an immediate
owner-authorized, YOLO request for one useful AI question—never a setup screen,
model picker, confirmation, or autonomous continuation.

With a ready local model, the pullout shows **Finding one useful question…** as
plain status, not an action. **Stop** is the sole visible primary at 1440 and
393. Before the pre-dispatch callback commits, Stop is a durable revoke and
guarantees no provider send. After physical dispatch it reads
**Stopping… This result won’t change your note**, durably suppresses the result,
then releases the live slot. **Good enough** remains a quiet `Finish instead`
exit under More; it never competes as a second primary. A second Keep-refining
request is unavailable while this one is live.

With no ready local model, this story omits Keep refining, setup, and model
error UI entirely. **Good enough** remains the sole primary and local editing/
Original stay available. A refusal or timeout after an explicit request returns
to ordinary Working with a named quiet status, never a setup surface.
When the exact receipt-gated result is ready, the pullout shows one compact
`One useful question` card above the Note:

```text
One useful question
What would make this worthwhile by Friday?

Your answer [________________________________]
                         [Answer]
```

At 1440, **Reject** and **Edit working note** are quiet controls in the card;
at 393 they fold under More. **Answer** is the one primary. Pressing it is an
immediate owner write: the exact typed answer is incorporated as a clearly
marked `Clarification` block in the existing working Note. The block has compact
`Question: <exact reviewed question>` and `Answer: <exact owner answer>` lines,
then receives an `Answer added` receipt and returns to ordinary working state.
It does **not**
call a model again, infer a next question, or ask the owner to approve their
own answer. The owner may deliberately press Keep refining later, edit, attach
context in HS-141-05, or Good enough.

If the bounded model response is a validated synthesis instead of a question,
the card is labelled `Suggested working version`; **Accept** is its sole
primary and applies the preview through expected working/aggregate CAS. **Edit
working note** seeds no automatic overwrite: it opens the local owner editor,
whose next explicit save is the owner action. **Reject** changes neither Note
nor raw. The result is never presented as a tool proposal or an autonomous
plan. In this story's ordinary prompt, the requested/expected shape is one
question, so this synthesis branch exists only to make the persisted review
contract truthful and reviewable.

## Bounded result contract

The refinement prompt requires a compact, validated JSON object, not free-form
chat prose. Its grammar is sealed: fixed instruction/output-schema text remains
separate from typed untrusted raw, working title/body/tags, and hydrated blocks.
Each untrusted field is inside named delimiters and has a fixed per-field and
total-material cap; none can provide role text, instructions, delimiters, or a
schema. Invalid UTF-8, over-cap material, or malformed refs is named before
provider admission.

```json
{"kind":"question","question":"…","reason":"…"}
```

or

```json
{"kind":"synthesis","title":"…","body_markdown":"…","tags":["…"]}
```

The ordinary request asks for `kind:"question"` and one concise question. The
server parses this only after HS-141-02 has proven the exact native receipt,
projection stage, Ask result, and result hash. Invalid/oversized/wrong-shape
output is named `refinement_result_invalid`: it becomes a terminal named
failure, leaves the Note editable, and does not become a review card. No model
text is ever copied into a Note merely because it parsed.

The owner-only review projection returns only the validated card fields plus
honest placement/egress receipt and frozen cursors. It does not return raw,
Ask payload JSON, hydrated source text, credentials, provider diagnostics, or
kernel/Ask identifiers. It is a view of `refinement_review_results` and the
existing receipt-gated `ask_results` row, not a new response store.

## Durable execution and privacy law

`POST /api/thoughts/{id}/refine` accepts exactly a caller-stable `request_id`
and the current aggregate/working/attachment cursors. It accepts no browser
prompt text, model choice, copied raw/working text, or copied context. The
refinement service first calls the existing owner-only reservation transaction;
the immutable raw and working revision therefore already exist, and the
reservation binds the exact frozen triple before any admission or dispatch.

The coordinator owns every terminal path between reserve and kernel admission.
On unavailable target, placement refusal, sealed-payload validation failure,
hydration failure, or another pre-admission exception it runs one
`terminalize_reserved` transaction: require the exact `rinv_…`, request hash,
ordinal-1 `ask_…`, frozen cursor tuple, and `state='reserved'`; then mark the
attempt and logical invocation terminal with the named code. It creates no
kernel operation or receipt. Reload/retry sees that durable named terminal row,
not a phantom kernel operation; only a new owner request ID may reserve again.

At attachment revision zero (this story), the authoritative ref set is empty.
After HS-141-05, the service loads only the typed refs associated with the
frozen attachment revision and hydrates them server-side via the existing
grounding hydrator. Deleted/missing refs refuse before Ask admission. The
browser never serializes source material as authority.

`AskService` receives the HS-141-02 reserved `ask_invocation_id` and both
existing callbacks: `before_physical_dispatch(invocation_id)` and
`before_compatibility_retry(invocation_id)`. The former is the last durable
source/cursor veto before each provider send, including `_r2`; the latter keeps
the one earned compatibility child correlated. Reservation → bound kernel
operation → physical dispatch → receipt/stage/Ask projection → exact
`rresult_…` reconciliation is unchanged law.

The implementation must add a private refinement payload loader/sealed
dispatch seam: the provider sees server-assembled working/raw-as-authorized
prompt material and hydrated refs, while the kernel operation/journal receives
only service-contract digest, deployment revision, opaque refinement
invocation/ref identifiers, and data-class/placement facts. Passing the prompt
or thought text in kernel operation arguments, journal rows, receipt text, or
browser DTOs is forbidden. Existing `InferenceRunner` already journals the
service contract hash rather than `InvocationRequest.payload`; this seam must
preserve that property while retaining Ask's existing placement/egress result
receipt.

## Owner transitions and action receipts

Add one local, owner-only action ledger rather than treating review buttons as
ephemeral UI:

```sql
CREATE TABLE refinement_review_actions (
  action_id TEXT PRIMARY KEY,                 -- ract_…
  request_id TEXT NOT NULL UNIQUE,
  request_sha256 TEXT NOT NULL,
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  review_result_id TEXT NOT NULL REFERENCES refinement_review_results(id),
  action_kind TEXT NOT NULL CHECK (action_kind IN ('answer','accept','reject')),
  aggregate_revision INTEGER NOT NULL,
  working_revision INTEGER NOT NULL,
  lifecycle_revision INTEGER NOT NULL,
  attachment_revision INTEGER NOT NULL,
  post_aggregate_revision INTEGER NOT NULL,
  post_working_revision INTEGER NOT NULL,
  post_lifecycle_revision INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (review_result_id)
);
```

The request hash includes only `{request_id, thought_id, review_result_id,
action_kind, expected_aggregate_revision, expected_working_revision,
expected_attachment_revision, answer_sha256?}`. It never stores answer,
prompt, raw, working body, context, or model output. The `action_id` is the
stable local receipt identity; successful exact replay returns the committed
Thought DTO and same receipt. A changed request payload is
`refinement_review_action_payload_mismatch`; a later cursor/lifecycle movement
is `refinement_review_action_superseded` with current DTO.

`UNIQUE(review_result_id)` is the single-decision fence: exactly one Answer,
Accept, or Reject consumes a ready review. Exact replay returns its receipt and
stored post cursors only while the current aggregate equals those post cursors.
If later edit/Good-enough/Resume moved the thought, the same request returns
`refinement_review_action_superseded` with current DTO; it never replays a past
decision into newer state.

In a single `BEGIN IMMEDIATE` transaction, an Answer or Accept must verify all
of these facts before any Note write:

1. owner principal; working thought; exact aggregate/working/attachment CAS;
2. `review_result_id` belongs to the thought and its invocation's frozen triple
   equals the expected/current triple;
3. the review row's stage, Ask ID, operation, receipt, result ref, and result
   hash still exactly agree with the native receipt-gated Ask projection;
4. the review card validates under the bounded contract.

`answer` computes the new working body server-side from the current body plus
one delimited, owner-attributed `Clarification` block containing the exact
answer bytes. `accept` replaces title/body/tags only from the validated
synthesis card. Both reuse the canonical thought working-revision command/CAS
path, increment working and aggregate revisions once, store the action receipt,
and atomically terminalize the one `review_ready` invocation as
`superseded/owner_answered` or `superseded/owner_accepted`. They do not alter
raw, lifecycle, attachment membership, or completion.

`reject` verifies the same review identity/CAS but writes no Note revision; it
stores an exact reject receipt and terminalizes the review as
`superseded/owner_rejected`. **Edit working note** does not accept model text:
the owner editor's normal expected-revision save supersedes any live
`review_ready` invocation in that same transaction. Every path frees the
one-live-invocation constraint only after a durable owner decision. Every
action uses conditional `UPDATE ... WHERE state='review_ready'` with the exact
frozen/current cursors, so concurrent Reject and Answer yield one committed
decision and one named current/superseded result.

## Cancellation, Good enough, and late results

`Stop` is an owner command with a durable cancellation/suppression record for
the exact logical invocation and frozen tuple. Before the dispatch hook it uses
the same `terminalize_reserved` CAS with `owner_stopped`; the hook refuses and
zero provider send occurs. After the hook it persists
`owner_stopped_after_dispatch`, asks the existing runner to cancel the exact
Ask invocation, and releases the live slot only after suppression is durable.
A late receipt/stage may remain native proof but reconciliation must suppress
it: it cannot create `review_ready`, review content, a Note write, or an
automatic retry.

**Good enough** remains one immediate owner gesture while refinement is
reserved, in flight, awaiting projection, or review-ready. Its existing
completion transaction must first conditionally terminalize **all** local live
refinement invocations for that thought with `thought_completed`, including
outstanding attempts and review visibility, then append the completion command
and origin receipt atomically. It cannot leave a live slot or result that could
surface after completion. Resume starts no hidden retry; only a new explicit
Keep-refining request with a new request ID can reserve again.

## API and recovery projection

```text
POST /api/thoughts/{id}/refine
  {request_id, expected_aggregate_revision, expected_working_revision,
   expected_attachment_revision}
  → {thought, continuity}                    # reserve/known live identity

POST /api/thoughts/{id}/reconcile
  {expected_aggregate_revision, invocation_id?}
  → {thought}                                # lookup/finalize only, no dispatch

POST /api/thoughts/{id}/refinements/{invocation_id}/stop
  {expected_aggregate_revision}
  → {thought, continuity}                    # revoke/suppress only; no retry

GET /api/thoughts/{id}/reviews/{review_result_id}
  → {review:{kind, question?|reason?|suggestion?, frozen cursors,
             placement, egress}}

POST /api/thoughts/{id}/reviews/{review_result_id}/answer
POST /api/thoughts/{id}/reviews/{review_result_id}/accept
POST /api/thoughts/{id}/reviews/{review_result_id}/reject
  {request_id, expected_aggregate_revision, expected_working_revision,
   expected_attachment_revision, answer?}
  → {thought, receipt}
```

All routes are OWNER-only. NODE has only signed paired-sync aggregate
install/fast-forward authority and must be denied reserve, review projection,
answer/accept/reject, and generic owned Note mutation. Continuity and review
proof are hub-local: a paired peer exposes `continuity_unavailable_remote`, not
someone else's question/result/receipt.

Reload calls only `reconcile` for the known invocation. It may show a review
card only after exact proof is durable; it never retries/refines/answers on its
own. A lost owner-action response replays the same local action receipt. A
known refusal, unavailable target, timeout, invalid review, stale cursor, or
ambiguous result names the condition, clears the live spinner, and returns the
owner to editable working state with Good enough available. No failure claims
that a model answer was applied.

## State and conflict matrix

| Situation | Required outcome |
|---|---|
| two tabs press Keep refining | one reserve wins; loser receives current live continuity, zero second dispatch |
| edit/attach/Good enough before dispatch hook | hook vetoes; zero provider send; named stale/refusal |
| edit after physical dispatch | result reconciles `stale`; never overwrites Note |
| provider success but missing stage/result | `ask_result_unpublished`; no review card |
| reload after send/lost browser response | reconcile known request only; never re-dispatch |
| pre-admission target/placement/hydration/payload failure | `terminalize_reserved` names exact reserved request/attempt; no kernel operation or phantom dispatch |
| Stop before hook | durable revoke; hook refuses; zero provider send |
| Stop after hook | durable suppression + cancellation; late result never surfaces or writes |
| Finish instead (Good enough) during reserved/in-flight/review-ready | quiet/More exit atomically terminalizes all local live continuity, then completes; no late review |
| result proof mismatch/invalid JSON | no projection/action; named failure |
| answer/accept race with owner edit | expected-revision conflict with current DTO; no partial receipt/action |
| duplicate Answer request | exact thought plus same `Answer added` receipt; one revision/command |
| concurrent Reject and Answer | one `UNIQUE(review_result_id)` decision wins; the other receives named current/superseded state |
| action replay after Good enough/Resume | stored request never reapplies; `refinement_review_action_superseded` carries current DTO |
| Reject | no Note mutation; one reject receipt; no auto-next question |
| missing/refused/timeout model | working Note, local editing, and Good enough remain available |

## Exact seams and focused proof

* `holdspeak/services/refinement_thought_service.py:211-236, 240-270,
  479-630` — reservation, dispatch veto/retry plan, exact reconciliation;
  add coordinator terminalization, Stop/suppression, owner action/review
  projection, and Good-enough live-row terminalization without changing raw
  custody.
* `holdspeak/services/ask_service.py:117-201` — reserved invocation entry and
  server-only prompt assembly/placement receipt; no public Ask route extension.
* `holdspeak/kernel/inference_runner.py:155-250` — contract-digest admission
  and pre-dispatch callback; preserve no-content journal arguments.
* `holdspeak/grounding.py:392-410` — server-side qualified-ref hydration seam.
* `holdspeak/web/routes/primitives/thoughts.py` — narrow owner routes only.
* `web/src/desk/pullouts/NotePullout.tsx` and
  `web/src/desk/pullouts/editors/ThoughtNoteEditor.tsx` — Tuesday card,
  primary-action state, local editor authority; no chat console.
* `web/src/desk/thoughts.ts` — typed refine/reconcile/review/action client.

Focused tests must prove: exact reserve-before-dispatch and one live request;
all base/_r2 attempts have durable correlation; server-side refs hydrate and
browser copies are ignored; sealed grammar/caps isolate untrusted fields; no
thought text in kernel journal; every pre-admission failure terminalizes its
exact reserved request/attempt with no kernel row; receipt-gated review only;
reload reconciliation without dispatch; Answer/Accept CAS and same-request
receipt replay; concurrent Reject decision fence plus replay after
Good-enough/Resume; Reject no mutation; Stop as the sole visible live-wait
primary before/after dispatch, plus quiet/More Finish instead during
reserved/in-flight/review-ready with late-result suppression;
stale/deleted/refused/timeout remain locally useful; NODE denial plus valid
paired aggregate convergence; and Tuesday glass at 1440/393 has Stop as the
one live-wait primary (status is not actionable), no overflow, no model/setup
interstitial, and no automatic next question.

## Contract self-audit

* **HS-141-01:** raw bytes and source remain untouched; all working changes use
  the aggregate command/CAS ledger.
* **HS-141-02:** uses its immutable correlation tuple, every-attempt dispatch
  gate, native receipt reconciliation, and hub-local proof. It adds no blind
  retry or alternate result authority.
* **HS-141-03/06:** works in the same owned Note pullout, preserves Original,
  editor serialization, Inbox/Resume, and Good enough/Resume refining. A
  review never blocks the local no-model exit. Completion's atomic live-row
  terminalization and Stop suppression prevent a late model result from
  reopening, mutating, or visibly competing with a completed Note.
* **Charter/proposal:** one explicit owner question, one owner action to apply
  an answer, no autonomous chain, no generic chat/tool system, and truthful
  local fallback. Power-user/Yolo means no confirmation gate—not automatic AI.
