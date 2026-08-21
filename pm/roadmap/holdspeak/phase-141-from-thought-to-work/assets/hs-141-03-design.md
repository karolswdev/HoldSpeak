# HS-141-03 design beat — Develop this thought

**Status:** design for counsel; this document authorizes no product code, model
dispatch, question flow, context attachment, proposal, or tool work.

## Decision

HS-141-03 is the owner-facing bridge into the HS-141-01/02 aggregate. The
ordinary Chair's primary capture verb is **Develop a thought**. It makes one
immutable raw snapshot and one editable working Note, files that Note in Inbox,
and opens the existing Note pullout. An ordinary existing Note instead takes
the in-place adoption path: that *same* Note becomes the working Note. It is
not cloned, rewritten, title/tag-inferred, or marked by a browser-only flag.

This is deliberately a local, useful slice. It has no model availability,
Keep-refining control, outstanding question, attachment picker, destination,
setup prompt, proposal, or tool call. The only continuing product state is an
editable working Note with durable raw custody. HS-141-04, -05, -06, -07, and
-08 own those later states respectively.

The result composition is:

```text
normal Chair ── Develop a thought ──> small capture composer
                                  └─> POST /api/thoughts (durable)
                                           └─> Inbox membership + open working Note

ordinary Note ── Develop this thought ──> POST /api/thoughts/adopt (durable)
                                           └─> same Note now owned + Inbox membership

working Note ── Original kept ──> GET /api/thoughts/{id}/original (read-only reveal)

normal Chair ── Resume unfinished thoughts ──> bounded HS-141-02 list
                                           └─> open its existing working Note
```

The first kept Phase-140 Note uses the second arrow without special treatment:
Phase 140 persists and stages an ordinary `note:<id>` ([`FirstWords.tsx:280-311`](../../../../../web/src/desk/components/FirstWords.tsx#L280-L311)); when its normal Note pullout opens, it has exactly the same visible bridge as every other ordinary Note. No title (`First dictation`), `dictation` tag, first-run disposition, timestamp, or one-time marker is an identity test.

## Existing facts this design rides

* HS-141-01 already makes a new thought, initial working Note, command/revision
  history, and `note:<id>` Inbox membership in one transaction
  ([`refinement_thought_service.py:39-92`](../../../../../holdspeak/services/refinement_thought_service.py#L39-L92)).
  That is the new-capture path; it must not be reimplemented in the web client.
* Its DTO exposes the four mandatory cursors and a raw-only read path
  ([`thoughts.py:62-89`](../../../../../holdspeak/web/routes/primitives/thoughts.py#L62-L89),
  [`refinement_thought_service.py:482-500`](../../../../../holdspeak/services/refinement_thought_service.py#L482-L500)).
  The new UI carries those cursors; it does not add them to an ordinary Note
  record or store them in browser persistence.
* The bounded, owner-only unfinished projection is already the resume source
  ([`refinement_thought_service.py:101-122`](../../../../../holdspeak/services/refinement_thought_service.py#L101-L122)).
  It is the only Chair list queried by this story.
* Ordinary Note opening and filing already converge in `NotePullout`
  ([`NotePullout.tsx:20-77`](../../../../../web/src/desk/pullouts/NotePullout.tsx#L20-L77));
  it is the one place to distinguish ordinary from thought-owned Note chrome.
* Generic Note updates currently debounce into `/api/notes/{id}`
  ([`useDebouncedSave.ts:5-16`](../../../../../web/src/desk/pullouts/editors/useDebouncedSave.ts#L5-L16)),
  while the canonical service delegates an owned Note to the aggregate service
  ([`primitive_service.py:55-100`](../../../../../holdspeak/services/primitive_service.py#L55-L100)).
  Adoption must close the ownership race at that seam, not make a new editor
  write route.
* The current `NoteEditor` can invoke `runAsk` directly
  ([`NoteEditor.tsx:63-90`](../../../../../web/src/desk/pullouts/editors/NoteEditor.tsx#L63-L90)).
  It is not lawful for a thought-owned Note: it lacks HS-141-02 reservation,
  cursor freezing, and receipt correlation. This story must render a local-only
  thought working editor and suppress that AI bar for an owned Note.

## Settled owner flow and composition

### 1. Normal Chair: direct capture, not the operations console

On a normal Chair, replace the control-room hero composition currently supplied
at [`ChairHome.tsx:52-56`](../../../../../web/src/desk/chair/ChairHome.tsx#L52-L56)
with `ThoughtEntry` as the ordinary hero. Its resting state has one primary
button, **Develop a thought**. Pressing it expands an in-place, focused compact
composer with a text area and a plain **Start developing** primary. A local
dictation affordance may use the existing browser capture primitives, but it is
labeled **Dictate** and fills the same editable field; it does not open the
Speak console or introduce operational vocabulary.

The draft stays in `durableDraft("thought-compose")` only as a crash/reload
recovery cache. The server request contains the text as received, encoded UTF-8
without browser normalization. The client mints and retains a `request_id`
until it receives the committed thought or deliberately discards the draft.
On success it clears only that cache, refreshes Desk data, stages/opens
`note:<working_note_id>` through the same pullout mechanism Phase 140 uses,
and enters the focused body editor directly. Response loss retries the same
request ID; it never creates a second Note. Only later re-entry (Inbox, Resume,
or a normal Note open) starts read-only and offers **Edit**.

The capture composer has no model status. If its text is empty, **Start
developing** is disabled with the field still usable; it does not create an
empty typed thought by accident. A network/refusal failure says **Your thought
is still here. Retry.** and preserves the exact local draft and request ID.

The existing Speak surface remains reachable only under a quiet **More capture
options** disclosure, which opens the registered `dictate` surface already
defined at [`SurfaceWindows.tsx:35-44`](../../../../../web/src/desk/components/SurfaceWindows.tsx#L35-L44).
It is neither mounted nor described by the ordinary flow. This is progressive
disclosure, not deletion.

### 2. Every ordinary Note: one adoption bridge

The unedited/read state of every ordinary Note footer shows one visible primary
verb: **Develop this thought**. Existing Copy and Dictate-about-this are quiet
secondary verbs or live in the existing More disclosure; the new action is
never conditional on Note title, tag, body length, initial-arrival state, or
directory. An empty ordinary Note still shows it. If pressed, its exact empty
body is a valid raw snapshot and its title/body/tags are the exact first
working revision; this makes the bridge truthful even for a blank scratchpad.

Clicking does a fresh owner-only note/thought lookup, then submits the returned
source precondition to the adoption endpoint below. It enters a single
"Developing…" press state. On committed success it refreshes the Desk, keeps
the same Note pullout open, and enters its focused editor directly on the
working body. There is no visual teleport to another Note and no browser-side
move into Inbox.

For a thought-owned Note, do not show **Develop this thought** again. Show the
persistent `Original kept · <source label> · <time>` cue above the edit
surface, and use the local-only thought editor. `source label` is derived from
the aggregate's actual source kind everywhere: `Typed`, `Voice`, or `This
note`; it is never hardcoded as `This note` for a typed/voice capture. The cue
is a compact button, not a second primary decision. It makes an owner-only GET
to `/api/thoughts/{id}/original` on press; the result opens a read-only folded
original block in the same pullout. It shows the exact decoded raw text, that
same source label, captured time, and `Original kept` status. Closing it
returns directly to editing. It has no Copy-to-working or Restore action in
this story.

### 3. Inbox and re-entry

Creation and adoption set the canonical existing directory-membership edge to
`note:<working_note_id> → hs-seed-inbox` in their commit transaction. The UI
labels this condition **Unfinished** only when the aggregate state is
`working`; it does not add a tag, an Inbox look-alike, or another membership
model. A pre-existing filing is intentionally moved to Inbox on adoption: the
map has one live directory edge per primitive, and the owner can file it
elsewhere with the existing filing strip afterward.

The normal Chair renders a quiet **Resume unfinished thoughts** secondary
control when the first bounded page has one or more items. It opens a compact
list (title plus `Updated <time>`) sourced only from `GET /api/thoughts?state=unfinished&limit=20`, and each row opens the listed `working_note_id` in
the normal Note pullout. The list owns its explicit **Show more** cursor request
when needed; it never queries all Notes, guesses by tag, or duplicates Inbox.
If the list is empty it is absent rather than a disabled teaser. A missing
filing in the DTO is not silently repaired in this story: the row says
**This thought isn't in a drawer yet. Open it to choose where it belongs.**
Its action opens the working Note directly to the existing filing control;
repair stays owner-directed and belongs to that existing filing surface rather
than an automatic move or a new filing model.

### One-primary-action rule

| Visible state | Primary action | Secondary / folded |
|---|---|---|
| Normal Chair | **Develop a thought** | Resume unfinished (when nonempty); More capture options |
| Capture composer | **Start developing** | Dictate; Cancel |
| Ordinary Note | **Develop this thought** | Copy; Dictate about this; filing |
| Freshly created/adopted working Note | **Save** (focused editing begins immediately) | Original kept; filing; Copy |
| Later working-Note re-entry | **Edit** while read-only, then **Save** while editing | Original kept; filing; Copy |
| Original reveal | no new decision (the editor action remains the sole primary) | Close original |
| Resume list | no row-wide competing primary; one row opens a Note | Show more / close |

At 393px the footer is a single-column action stack: its sole primary consumes
the row; secondary actions fold under one **More** trigger. The chair composer
and resume list use `min-width: 0`, `max-width: 100%`, wrapping labels, and no
fixed card minimum. The existing Chair grid already protects its lane wrapper
with `minmax(0, 1fr)` ([`chair.css:67-93`](../../../../../web/src/desk/chair/chair.css#L67-L93));
the new components must preserve that contract rather than introduce a
wide-button overflow.

## Adoption is a single custody transaction

### Contract

Add a dedicated owner-only route before the generic `/{thought_id}` route:

```text
GET  /api/thoughts/for-note/{note_id}
POST /api/thoughts/adopt
```

`for-note` is a narrow ownership/read-precondition projection, not a new Note
DTO. For an ordinary live Note it returns:

```json
{
  "ownership": "ordinary",
  "note": {"id":"note_…","title":"…","body_markdown":"…","tags":[],"last_modified":"…"},
  "source_precondition": {"content_sha256":"…","last_modified":"…"}
}
```

For an owned Note it returns `{ "ownership":"thought", "thought": ThoughtDTO }`.
For a missing/tombstoned Note it is 404. It is owner-only and must not expose raw
to a paired node; normal list Note responses are unchanged.

```json
POST /api/thoughts/adopt
{
  "request_id": "caller-stable UUID",
  "note_id": "note_…",
  "expected_source_content_sha256": "…",
  "expected_source_last_modified": "…"
}
```

The success body is the normal committed `ThoughtDTO`, with all four mandatory
cursors. The adoption request hash is canonical JSON over exactly
`{kind:"adopt_note", request_id, note_id, expected_source_content_sha256,
expected_source_last_modified}`. It contains no copied title/body/tags beyond
the source precondition. Same request ID and same digest returns the already
committed aggregate; same ID and another digest is
`409 idempotency_payload_mismatch`.

`content_sha256` is the existing canonical working-note content hash over the
stored title, body, and tags; `last_modified` protects the currently exposed
version as well. Both are required. They are a source CAS, not a timestamp-only
best effort. A later revision field may replace the pair only in a backwards
compatible, mandatory new protocol version.

### Exact transaction and invariants

`RefinementThoughtService.adopt_note` is the only adoption writer. In one
`BEGIN IMMEDIATE` transaction it does, in this order:

1. Look up `create_request_id`; if present, verify request digest and return
   its aggregate without reading or changing the source Note.
2. Read the source Note by ID. Refuse `404 note_not_found` or
   `409 note_tombstoned` if it is absent/deleted. Read any existing
   `refinement_thoughts.working_note_id` claim under the same lock. If claimed,
   return `409 note_already_a_thought` with that owner-only `ThoughtDTO`; a
   client recovering a lost response opens it instead of retrying an adoption.
3. Compute canonical Note content hash from the database row and require exact
   equality of both supplied preconditions. On mismatch, write nothing and
   return `409 note_adoption_conflict` with the fresh ordinary Note and fresh
   `source_precondition`. Do not select whatever happened to be newest and
   adopt it silently.
4. Encode the *stored* `body_markdown` as strict UTF-8 and insert it unchanged
   as `raw_utf8`, with its byte hash, `raw_source_kind='note'`, and
   `raw_source_ref='note:<note_id>'`. Empty bytes are valid for this
   source-specific adoption path. This is the immutable raw custody snapshot.
5. Allocate `resume_order=RefinementThoughtRepository.next_resume_order(conn)`
   in this same transaction, then insert `refinement_thoughts` with
   `working_note_id` equal to the existing `note_id`, state `working`, that
   allocated order, and all initial cursors (`aggregate=1`, `lifecycle=1`,
   `working=1`, `attachment=0`). Insert working revision 1 from the exact
   stored `(title, body_markdown, tags)` and append the initial lifecycle and
   aggregate command with `command_kind='adopt_note'`. An idempotent replay
   returns before this allocation and does not consume a new resume order.
6. Upsert the sole canonical `directory_memberships` row for `note:<note_id>`
   to Inbox. This changes only the filing edge. **There is no INSERT, UPDATE,
   or delete of the `notes` row anywhere in this transaction.**
7. Commit, then return the committed DTO. Nothing model-, question-, context-,
   proposal-, or tool-related is called before or after commit.

The immutable raw is exactly the original Note body bytes. The initial working
revision is exactly the original Note's full editable shape. They are related
but not interchangeable: later Note edits advance only the aggregate's working
revision and never mutate `raw_utf8` or its hash.

The current generic pre-check in `PrimitiveService.update_note` is insufficient
as the only guard because it observes ownership before its own eventual write.
Adoption and a stale ordinary edit could otherwise pass different observations.
The implementation must make **every public generic Note write and delete**
enter a shared write transaction, resolve ownership there, and either delegate
to the aggregate CAS or prove the Note remains unowned immediately before its
low-level mutation. The low-level Note repository remains internal; sync keeps
the HS-141-01 aggregate protocol. No code path may observe “ordinary”, wait for
adoption to commit, then mutate the now-owned Note without aggregate cursors.

This gives the required outcomes:

| Race / retry | Required result |
|---|---|
| Two tabs adopt the same ordinary Note with different request IDs | Exactly one commits; the other gets `note_already_a_thought` plus the committed DTO. |
| A Note edit wins before adoption lock | Adoption detects fingerprint mismatch and returns `note_adoption_conflict`; no ownership change. |
| Adoption wins before an ordinary edit | The edit resolves ownership inside its write transaction and must supply aggregate + working CAS; otherwise `thought_expected_revision_required`. |
| Response dies after adoption commit | Same persisted request ID returns the same thought; a forgotten ID recovers via `for-note`/`note_already_a_thought`; never a clone. |
| Inbox missing | `inbox_unavailable`, no raw/aggregate/working-history write and no ownership claim. |
| Note already tombstoned | No resurrection, no new thought. |

### Adoption provenance is validated before paired sync can install it

`holdspeak/services/sync_service.py` is an owned seam for this story. Its
refinement aggregate merge already decodes/verifies raw bytes before it calls
`_validate_thought_ledger_bundle`
([`sync_service.py:672-747`](../../../../../holdspeak/services/sync_service.py#L672-L747))
and its ledger validator presently permits only `create` as the first command
([`sync_service.py:782-844`](../../../../../holdspeak/services/sync_service.py#L782-L844)).
Extend that validator's input to receive the decoded `raw_utf8` and recognize
one additional initial law, `adopt_note`; do not relax the generic creation
law or trust an incoming command name by itself.

The validator may allow initial `command_kind='adopt_note'` only when all of
the following are true in the same incoming bundle:

1. It is aggregate command 1 with prior cursors `(0,0,0)`, next cursors
   `(1,1,0)`, and no prior state, exactly like a fresh aggregate creation.
2. Lifecycle revision 1 has `prior_state=null`, `state='working'`, and
   `command='adopt_note'`; its entry hash and command lifecycle hash remain the
   existing canonical hashes.
3. `source.kind` is exactly `note`, `source.ref` is exactly the qualified
   `note:<working_note.id>` string, and no coercion, alias, or unrelated Note
   ID is accepted.
4. Revision 1's `body_markdown` is a string encodable as strict UTF-8 and its
   encoded bytes are byte-equal to the decoded aggregate `raw_utf8`; the
   existing raw hash check must therefore also equal revision-1 body bytes.
   Revision 1 still has to pass its canonical title/body/tags content hash.

Any mismatch is `thought_adoption_provenance_invalid` and the peer installs
neither the aggregate, working Note, nor its membership. In particular, a
forged `adopt_note` over typed/voice provenance, a source ref for another Note,
a body changed after raw capture, or a claim that an ordinary `create` was an
adoption is refused. A valid adopted thought then uses the existing aggregate
install/fast-forward machinery; it remains one owner relationship, not a
special paired-device Note upsert.

## Resume ordering invariant

The new adoption's `next_resume_order(conn)` allocation is part of its custody
transaction, not a post-commit list decoration. HS-141-02's bounded list fixes
a high-water order on its first page
([`refinement_thought_service.py:101-124`](../../../../../holdspeak/services/refinement_thought_service.py#L101-L124)).
Therefore an adoption committed after that first page must have a strictly
higher order and cannot leak into a subsequent cursor page of that pre-existing
snapshot; a brand-new first page sees it normally. This gives Resume a stable
list rather than an item that appears halfway through paging.

## UI/API boundaries and recovery copy

Add a narrowly typed web client module for `ThoughtDTO`, `ThoughtListItem`, and
the two adoption responses. Keep it outside the generic `Note` wire type: the
aggregate cursors are ownership state, not fields syncable with every Note.
`NotePullout` loads this state only for its open Note; Desk refresh does not
fan out one request per Note.

The thought editor sends `PUT /api/notes/{working_note_id}` with the current
`expected_aggregate_revision` and `expected_working_revision`; the canonical
service then performs HS-141-01's ownership-gated update. Its debouncer must
retain and replace cursors from every success. A `thought_revision_conflict`
stops the pending debouncer, renders the returned current Note, and says:
**This thought changed elsewhere. Your latest version is shown. Review it,
then edit again.** It never resubmits a stale body automatically.

Required owner copy:

| Condition | Copy | Recovery |
|---|---|---|
| Chair rest | **Develop a thought** | Starts the small capture composer. |
| Capture label | **What are you working through?** | Type or Dictate; no model promise. |
| Capture failure | **Your thought is still here. Retry.** | Same request ID and unchanged draft. |
| Ordinary Note bridge | **Develop this thought** | Atomic adoption. |
| Adoption precondition conflict | **This note changed elsewhere. Review the latest version, then develop it.** | Refresh exact source; a new explicit press creates a new request. |
| Already owned recovery | **This note is already being developed.** | Open the returned working thought; no resend. |
| Owned cue | **Original kept · <Typed \| Voice \| This note> · <time>** | Reveal exact read-only original. |
| Resume control | **Resume unfinished thoughts** | Bounded working-thought list. |
| No unfinished work | no control | No empty-state pressure. |

`Original kept` is status plus a read action, never a claim that the raw can be
edited, restored over changes, attached to a model, or used as an execution
payload. The time uses the hub's `raw_captured_at`, not browser time.

## Files and seam ownership

Implementation should add/modify only the following seams; any apparent need
for Ask, grounding, actuator, kernel, policy, connector, or proposal edits is
a stop-and-report condition for this story.

| Plane | Intended seam | Why |
|---|---|---|
| Aggregate | `holdspeak/services/refinement_thought_service.py` | Dedicated adoption transaction, source lookup DTO, ownership-safe update boundary. |
| HTTP | `holdspeak/web/routes/primitives/thoughts.py` | Add static `for-note` before `/{thought_id}` and `adopt`; reuse error contract. |
| Generic Note authority | `holdspeak/services/primitive_service.py`, `holdspeak/db/primitives.py` | Move ownership check into the same write transaction as any generic Note mutation; no new route. |
| Paired sync | `holdspeak/services/sync_service.py` | Validate first-command `adopt_note` provenance against exact source/ref/raw/revision-1 bytes before aggregate install. |
| Typed client | `web/src/desk/thoughts.ts` (new) | Thought/adoption types, bounded list, open-state query; no mutation of generic Note shape. |
| Chair | `web/src/desk/chair/ChairHome.tsx`, new `web/src/desk/chair/ThoughtEntry.tsx`, `chair.css` | Ordinary primary capture, one quiet resume control, More disclosure. |
| Note surface | `web/src/desk/pullouts/NotePullout.tsx`, new thought-local editor/view component | Ordinary adoption bridge; owned cue and local editor; preserve current pullout/window identity. |
| Editor protection | `web/src/desk/pullouts/editors/NoteEditor.tsx`, `useDebouncedSave.ts` | Do not expose direct `runAsk` for owned Notes; carry authoritative cursors on local saves. |
| FirstWords | no Phase-140 identity branch | Its ordinary Note open naturally exposes the shared Note bridge. |

## Focused tests

Backend additions go in [`tests/unit/test_refinement_thought_service.py`](../../../../../tests/unit/test_refinement_thought_service.py),
[`tests/unit/test_web_routes_thoughts.py`](../../../../../tests/unit/test_web_routes_thoughts.py),
and [`tests/unit/test_web_routes_sync_primitives.py`](../../../../../tests/unit/test_web_routes_sync_primitives.py):

1. Fresh typed capture atomically yields byte-equal original, revision-1
   working Note, Inbox `note:` membership, all four cursors, and no model/
   invocation/attachment rows.
2. Adoption preserves the existing Note ID and exact title/body/tags; writes no
   second Note; raw bytes equal original body; command history begins
   `adopt_note`; Inbox is the only live filing edge.
3. Adoption accepts an empty source Note without converting it to fallback text.
4. Same request/digest is idempotent; same request/different digest refuses;
   two adoption requests produce one aggregate; response-loss recovery returns
   that aggregate rather than cloning.
5. A source edit between lookup and adoption returns the complete named
   precondition conflict and changes neither raw, ownership, membership, nor
   command ledger.
6. Barrier-controlled concurrent generic Note update/adoption proves exactly
   one ordering wins and no unversioned post-adoption Note mutation is possible.
7. Tombstoned/missing/already-owned/Inbox-missing sources all leave no partial
   aggregate; paired-node access to all new endpoints is refused.
8. Original endpoint returns byte-equal adopted text only for owner; normal
   thought/list DTOs do not leak raw source or text.
9. A paged unfinished-list snapshot taken before adoption does not return the
   newly adopted row on its old cursor; a fresh first page does. The adoption
   commit has allocated exactly one new, strictly higher `resume_order`.
10. Peer sync installs a valid adopted bundle and preserves its raw/source/
    revision-1 provenance; it rejects each forged variation (wrong command or
    lifecycle name, non-note source, wrong qualified ref, changed revision-1
    body/raw bytes, or raw hash mismatch) with
    `thought_adoption_provenance_invalid` and no partial peer records.

Web additions belong beside `FirstWords`, `ChairHome`, `NotePullout`, and
`NoteEditor` tests:

1. Normal Chair exposes one **Develop a thought** primary and hides Speak under
   More; opening the composer, capture success, retry, and response loss all
   use one stable request ID and open the working Note.
2. A mocked Phase-140 kept `note:<id>` and an arbitrary ordinary Note each
   render **Develop this thought** with no title/tag/arrival predicate; adopted
   success keeps the exact pullout identity and shows Original kept.
3. Owned Notes omit `EditorAIBar`/`runAsk`, load original only on cue press,
   propagate aggregate/working cursors on save, and stop on conflict without
   replaying a debounced save.
4. Resume consumes one bounded page/cursor and opens the exact listed working
   Note; it never scans ordinary Notes or uses a tag.
5. Layout assertions at 1440×900 and 393×900 enforce one `.is-primary` owner
   action per state, no horizontal scroll, wrapping long titles, and an intact
   existing filing disclosure.

## Live walk matrix (HS-141-09 will automate and evidence it)

| Walk | 1440 and 393 expected proof |
|---|---|
| Normal Chair | One visible **Develop a thought** primary; no Ask/model/tool/setup language; Speak only in More. |
| Typed capture → reload | Enter rough text, create, land in focused editing; reload hub/browser; same working Note is in Inbox and `Original kept · Typed · <time>` reveals byte-equal text. |
| Phase-140 first Keep | Dictate/edit/Keep through existing FirstWords path; normal Chair opens the Note; use **Develop this thought**; same Note becomes Unfinished and enters focused editing with `Original kept · This note · <time>`. |
| Arbitrary filed Note adoption | Start with a Note in Personal/Work, adopt it; title/body/tags survive exactly, it moves through the visible existing Inbox membership, no duplicate appears. |
| Concurrent adoption/edit | Use two browser contexts; force stale fingerprint or ownership race; one explicit named conflict, zero silent overwrite, one aggregate at most. |
| Original custody | Edit the working Note after adoption; original remains unchanged, folded/read-only, source-labeled truthfully, and is not accidentally placed in the editable text. |
| Resume unfinished | Leave/reload then use Chair Resume; list opens the same Note read-only with **Edit**, and no model request occurs. |
| Narrow glass | At 393px inspect every state above: one primary decision, no horizontal overflow, no clipped footer or hidden Original cue. |

## Out of scope / stop conditions

Do not make any model call, reserve a refinement invocation, show a question,
attach context, discover a tool, create a Decision, complete a thought, or
alter an actuator/kernel/policy path. Do not restore the Speak operations
console as ordinary capture. Do not introduce a generic chat, a copied source
Note, a second mutable working Note, a browser-authoritative context snapshot,
or a new filing model.

Stop for counsel if an implementation cannot make adoption a single
source-fingerprint-CAS transaction, cannot close the generic Note write race,
requires a second primary action at 393px, or needs an Ask/grounding/tool seam
to make this local bridge work.
