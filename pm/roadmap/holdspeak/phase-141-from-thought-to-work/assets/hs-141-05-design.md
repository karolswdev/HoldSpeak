# HS-141-05 design beat — context you can see

**Status:** design for counsel. This authorizes no product code, PMO/status,
evidence, stage, commit, model call, proposal, tool, Rails, meeting, artifact, or
external-effect change.

## Decision

One Thought has one visible, revisioned attachment set. It starts empty. The
owner can immediately attach a Note or the seeded **Everyday context** Knowledge
collection from the Note pullout; there is no setup, Apply, confirmation, hidden
enrichment, guessed context, or browser-authored material.

The server resolves every selected qualified ref into an immutable manifest:

```text
visible selection                 exact expanded leaves
knowledge:hs-seed-everyday…  -->  note:about-me @ content/version hash
  "Everyday context"              note:current-priorities @ content/version hash
  container/membership hash       note:how-i-like-help @ content/version hash
                                  note:people-vocabulary @ content/version hash
                                  note:meeting-preferences @ content/version hash
```

That manifest—not a mutable collection name and not browser-copied text—is the
attachment revision. It is committed by hash into the Thought aggregate command
and synchronized with the aggregate. A model turn expands only the exact
manifest it reserved. If a container, membership, name, leaf, content hash, or
deletion state differs before dispatch, the request refuses by human name and
offers **Update context** or **Remove it**. It never silently adopts current membership,
uses a different version, or claims old content remains retrievable.

This story supports only:

* ordinary live `note:<id>` refs, excluding the Thought's own working Note; and
* exactly `knowledge:hs-seed-everyday-context`, whose live members must all be
  supported Notes.

Meetings, transcripts, Artifacts, other Knowledge collections, projects,
drawers/zones, People, files, Rails objects, integrations, and tool state remain
out. A malformed, cyclic, nested, unsupported, self-referential, over-cap, or
partially missing selection refuses in full. There is no best-effort expansion
and no silent 16-leaf truncation.

## Tuesday flow — one compact Attach interaction

An unfinished Thought shows an in-body **AI context** row, above the working Note and
outside the footer action competition:

```text
AI context   None                                   Attach
```

**Attach** is directly visible at 1440 and 393. It is a secondary context
control, not another primary lifecycle action. Pressing it opens a compact,
search-focused popover at 1440 and a bottom sheet at 393:

```text
Attach context
[ Search notes                                  ]

Pinned
  Everyday context                                5 notes

Recent
  Current priorities
  Launch notes

Browse all notes
```

The initial view contains only:

1. **Pinned:** the live seeded Everyday context first, labelled with its exact
   current supported leaf count;
2. **Recent:** at most three distinct, still-live server-derived visible refs
   previously attached by this owner on this hub; and
3. search plus an explicit **Browse all notes** disclosure.

It never renders the full catalog on open. Search is server-side, title-only,
bounded, and keyset paged. Browse is explicit and paginated. Empty search,
missing seed, and no recent items are honest small states, not setup screens.

Selecting a row immediately attaches it through the server command. There is no
Apply or Save. The row stays pending until the authoritative response returns;
the browser never paints an attachment as committed optimistically. A lost
response retries the same request ID. Success always closes the picker and
focuses the authoritative AI context chip. On success the body shows compact
visible chips and human names:

```text
AI context   Everyday context · 5 notes              Attach
```

Opening the chip's quiet detail names the exact leaves used by the current
revision, for example `About me`, `Current priorities`, and their concise
version labels. The version labels are owner-readable (`version from 10:42`),
while the full hashes remain API/receipt proof rather than visual noise.
**Remove it** is immediate. **Update context** appears only when the server says
the stored manifest no longer matches current source state. Both are one owner
gesture with no confirmation. The transport/service operation remains the
precise `refresh_context`; only the human-facing verb is Update context.

The default set remains empty even when Everyday context exists. Pinned means
easy to choose, never preselected. No attached ref is inherited from Ask,
Agents, a drawer, a project, Rails, browser storage, or a prior Thought.

The existing footer keeps one primary per state. Attach remains available in
the body while Working; during a live turn or review it may still be invoked,
but any successful attachment mutation atomically supersedes that exact live or
review-ready turn before the new attachment revision becomes visible. A late
result cannot surface. The owner deliberately presses the refinement action
again to use the new context.

Staleness changes the action hierarchy, not merely a warning:

* idle + stale: no model turn is available. **Update context** is the sole
  primary for a changed-but-live selection; **Remove it** is the sole primary
  when the selected source is missing/deleted. With multiple stale selections,
  the first canonical visible ref owns that one repair primary and the other
  named issues remain listed for the next deterministic repair;
* stale question already shown: **Answer** remains the sole primary because it
  writes the owner's text, not model prose. Update context/Remove it is quiet;
  choosing it supersedes the question immediately; and
* stale synthesis already shown: Accept is absent. **Update context** (or
  **Remove it** for a missing source) is the sole primary and no model text can
  be applied.

Successful attach/update/remove closes the picker and moves focus to the
authoritative attached chip or AI context row. A validation, conflict, or network
error keeps the picker open, preserves the prior authoritative selection, and
focuses/names the exact failing row. At 393 the sheet never auto-focuses search:
Pinned Everyday context is visible above the software-keyboard line on open
and remains above the search results when the owner deliberately enters search.

When a receipt-gated question or synthesis is shown, its quiet receipt line
reads, for example, **Used Everyday context · 5 notes**. Detail expands to the
visible container and exact leaf names/versions. It never says merely
“grounded,” never implies current mutable membership, and never exposes prompt
text.

## Existing seams and the gap

The implementation must consolidate around existing paths rather than create a
second context system:

* `web/src/desk/grounding.ts` already proves `GroundingSelection.resources`
  sends qualified refs only. Its optional client `title`, `kind`, `id`, and
  `chars` fields are display/cache data and are not authority.
* `holdspeak/grounding.py` is the shared Ask/steer qualified-ref resolver and
  already hydrates Notes and Knowledge server-side. Its current Knowledge block
  contains only a mutable container plus current children; it does not expose
  exact leaf versions, and its global cap can truncate after expansion. That is
  insufficient for a refinement attachment receipt.
* `AskService` already owns grounded prompt assembly, placement, immutable
  deployment capture, kernel admission, result projection, and egress receipt.
  Refinement must feed it a trusted server-frozen grounding snapshot; the
  public Ask route does not gain a client-supplied snapshot or copied-material
  field.
* `grounding_rails.py` remains a separate Rails hydration adapter. It does not
  participate in this story.
* `knowledge_memberships` is the qualified many-to-many edge truth and syncs;
  `kbs.member_ids_json` is compatibility state. Membership writes do not by
  themselves give a sufficient container revision, so a manifest hash must
  include the exact live membership edge identities/versions and leaf hashes.
* the furnished seed already creates `knowledge:hs-seed-everyday-context` and
  five editable Notes while explicitly promising no automatic inclusion.
* `refinement_thoughts.attachment_revision`, the aggregate command ledger, the
  frozen invocation triple, dispatch hooks, and sync bundle are the correct
  lifecycle. They currently carry only an attachment number and no attachment
  manifest. The number alone cannot prove what was used.
* `RefinementApplicationService` is the transport-neutral Thought API shared by
  HTTP and MCP. All context listing and mutations must enter here.
* `NotePullout` is the one owner surface. Reusing the 14-item Ask grounding wall
  or introducing a context/settings screen would fail this story.

## Canonical manifest and hashes

All hashes use UTF-8 canonical JSON: sorted keys, compact separators,
`ensure_ascii=false`, `allow_nan=false`, and SHA-256 lowercase hex. Array order
is explicitly defined; database row order and locale collation are never hash
inputs. Visible records and their persisted ordinals are sorted by canonical
qualified `visible_ref`; leaf records and their persisted ordinals are sorted
by canonical qualified `leaf_ref`. There is no owner-order field in the durable
manifest. Picker/presentation ranking is a read projection and cannot change a
hash or ordinal.

For a live Note leaf:

```text
leaf_content_sha256 = sha256(canonical_json({
  "ref": "note:<id>",
  "title": <exact title>,
  "body_markdown": <exact body>,
  "tags": <exact ordered tags>,
  "last_modified": <synced source version>,
  "deleted": false
}))
```

Including `last_modified` distinguishes delete/recreate or same-byte later
versions; including the bytes proves exact model material. The hash is stored,
not the content. An attachment table is not a shadow Note history.

One visible selection record has:

```text
visible_sha256 = sha256(canonical_json({
  "visible_ref": <qualified ref>,
  "visible_kind": "note" | "knowledge",
  "visible_title": <exact server title>,
  "source_last_modified": <Note or Knowledge source version>,
  "membership": [
    {"leaf_ref": <ref>, "membership_last_modified": <edge version>,
     "leaf_content_sha256": <hash>}, ...
  ]
}))
```

Direct Notes have a one-element membership array whose edge version is empty.
Knowledge leaves and visible selections use the canonical orders above, so the
same set has one identity:

```text
attachment_sha256 = sha256(canonical_json({
  "schema_version": 1,
  "thought_id": <id>,
  "attachment_revision": <n>,
  "visible": [
    {"visible_ref": ..., "visible_sha256": ...,
     "leaves": [{"leaf_ref": ..., "leaf_content_sha256": ...}, ...]}, ...
  ]
}))
```

Revision zero has a named constant empty-manifest hash computed by this same
grammar. Existing aggregate command hashes are historical evidence and are
never rewritten or reinterpreted. Add an explicit `canonical_version`:

* the existing command prefix remains byte-for-byte **v1**, verified with the
  existing canonical grammar and its existing hashes;
* every command created after this migration is **v2**, including a no-context
  edit/lifecycle/review command. V2 hashes the prior canonical command fields
  plus `canonical_version:2` and the exact `attachment_sha256`;
* a command history may be `v1* -> v2*` only. Once a v2 row appears, a later v1
  row is invalid locally and over sync. There is no v2-to-v1 downgrade path;
* migration backfills only the Thought head's revision-zero empty attachment
  hash. It does not change a v1 command row, version, canonical bytes, or hash;
  and
* a nonzero legacy attachment revision without a valid child manifest is a
  startup integrity refusal, never guessed empty or repaired by hash rewrite.

Thus every v2 aggregate command carries the attachment hash—including working
edits, lifecycle transitions, review actions, and no-context refinement—and the
hash is committed state rather than an unbound side table.

## Durable schema

Add immutable aggregate-owned child rows and one local request receipt ledger:

```sql
CREATE TABLE refinement_attachment_revisions (
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  attachment_revision INTEGER NOT NULL CHECK (attachment_revision >= 1),
  aggregate_revision INTEGER NOT NULL,
  attachment_sha256 TEXT NOT NULL,
  visible_count INTEGER NOT NULL,
  leaf_count INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (thought_id, attachment_revision),
  UNIQUE (thought_id, aggregate_revision),
  UNIQUE (thought_id, attachment_sha256, attachment_revision)
);

CREATE TABLE refinement_attachment_visible (
  thought_id TEXT NOT NULL,
  attachment_revision INTEGER NOT NULL,
  ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
  visible_ref TEXT NOT NULL,
  visible_kind TEXT NOT NULL CHECK (visible_kind IN ('note','knowledge')),
  visible_title TEXT NOT NULL,
  source_last_modified TEXT NOT NULL,
  visible_sha256 TEXT NOT NULL,
  PRIMARY KEY (thought_id, attachment_revision, ordinal),
  UNIQUE (thought_id, attachment_revision, visible_ref),
  FOREIGN KEY (thought_id, attachment_revision)
    REFERENCES refinement_attachment_revisions(thought_id, attachment_revision)
);

CREATE TABLE refinement_attachment_leaves (
  thought_id TEXT NOT NULL,
  attachment_revision INTEGER NOT NULL,
  visible_ordinal INTEGER NOT NULL CHECK (visible_ordinal >= 0),
  leaf_ordinal INTEGER NOT NULL CHECK (leaf_ordinal >= 0),
  leaf_ref TEXT NOT NULL,
  leaf_title TEXT NOT NULL,
  source_last_modified TEXT NOT NULL,
  membership_last_modified TEXT NOT NULL,
  leaf_content_sha256 TEXT NOT NULL,
  PRIMARY KEY (thought_id, attachment_revision, visible_ordinal, leaf_ordinal),
  UNIQUE (thought_id, attachment_revision, visible_ordinal, leaf_ref),
  FOREIGN KEY (thought_id, attachment_revision, visible_ordinal)
    REFERENCES refinement_attachment_visible(thought_id, attachment_revision, ordinal)
);

CREATE TABLE refinement_context_actions (
  action_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL UNIQUE,
  request_sha256 TEXT NOT NULL,
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  action_kind TEXT NOT NULL CHECK (action_kind IN ('attach','detach','refresh')),
  visible_ref TEXT NOT NULL,
  prior_aggregate_revision INTEGER NOT NULL,
  prior_attachment_revision INTEGER NOT NULL,
  post_aggregate_revision INTEGER NOT NULL,
  post_attachment_revision INTEGER NOT NULL,
  post_attachment_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

`refinement_thoughts` gains `attachment_sha256 NOT NULL`. The aggregate command
ledger gains `canonical_version INTEGER NOT NULL DEFAULT 1` and a conditionally
required `attachment_sha256`: v1 historical rows retain `NULL` and their exact
old hash; every v2 row requires a 64-character hash. Validation enforces a v1
prefix followed by a v2-only suffix. `refinement_invocations` gains mandatory
`frozen_attachment_sha256 TEXT NOT NULL`; an optional revision join is not
sufficient. Review/result receipts project the exact visible/leaf manifest
joined by the frozen revision and hash.

Ordinals are zero-based, contiguous, and canonical: visible ordinal `n` is the
`n`th `visible_ref` in ascending UTF-8 byte order; leaf ordinal `n` is the `n`th
`leaf_ref` for that visible selection in the same order. Local reads and sync
validation recompute and require these exact positions; merely having a unique
set of refs is insufficient.

No attachment row stores Note body, prompt, raw Thought, answer, credentials,
or model output. Existing Ask/kernel payload custody remains the only durable
model-material path. Attachment histories are bounded by the Thought ledger and
cannot be pruned independently while an aggregate command, invocation, review,
or proposal references them.

## One canonical context service

Add a narrow refinement-context domain service, consumed only through
`RefinementApplicationService`. It owns four operations:

```text
list_context(principal, thought_id, query?, view, cursor?, limit)
attach_context(principal, thought_id, visible_ref, request_id, expected triple)
detach_context(principal, thought_id, visible_ref, request_id, expected triple)
refresh_context(principal, thought_id, visible_ref, request_id, expected triple)
```

All require OWNER. `NODE` remains restricted to validated signed aggregate
sync. List returns safe metadata only: qualified ref, kind, current title,
supported leaf count, selected/current/stale state, and cursor. It never returns
leaf body, snippets, hashes intended only for receipt detail, raw, or hidden
membership from an unsupported collection.

The three writes enter one private `replace_attachment_set` transaction. The
browser/MCP supplies exactly one qualified ref plus stable request ID and the
current aggregate/working/attachment cursors—not a replacement array, title,
kind, leaf list, content, membership, hash, or timestamp. The server derives
the desired set from current immutable rows:

* attach adds the one ref if absent;
* detach removes the one ref if present;
* refresh retains the set but re-resolves the named ref and its exact leaves.

The request hash binds action, Thought, ref, and expected triple. Exact replay
returns the same post-cursor Thought and receipt only while it is still current;
a changed payload is `context_request_payload_mismatch`, and replay after later
aggregate movement is `context_request_superseded` with current DTO.

Within one `BEGIN IMMEDIATE`, the service verifies the Thought is working, the
working Note is live, and all cursors match; resolves the complete desired set;
validates supported kinds, self-reference, cycles, duplicates, leaf count, and
every live source; constructs the canonical immutable manifest; and compares it
to the current manifest. If it differs, it increments attachment and aggregate
exactly once, inserts all child rows, updates `attachment_sha256`, inserts the
aggregate `replace_attachments` command with unchanged working/lifecycle
cursors and the new hash, stores the context action receipt, and atomically
terminalizes all reserved/in-flight/awaiting/review-ready refinement rows as
`owner_context_changed`. If the action is already semantically satisfied and
the newly resolved manifest is byte-identical, it stores a no-op receipt with
the same pre/post cursors and no aggregate command.

No partial attachment commits. Everyday context is accepted only if its exact
seed ref is live, its container metadata is readable, it has at least one and
at most 16 leaves, and every member is one unique
live supported Note other than the current working Note.

The Phase-141 limits are exact and apply before Ask:

* at most **8 visible selections**;
* at most **16 unique expanded leaves** across the entire set;
* at most **12,000 UTF-8 bytes per canonical formatted leaf block**; and
* at most **48,000 UTF-8 bytes for the complete canonical formatted context
  material**, including provenance, JSON punctuation/escaping, and the fixed
  untrusted-context delimiters.

Resolution counts the complete set and formats every complete block before any
limit decision. No character count substitutes for bytes; no generic Ask cap
runs later and truncates an accepted snapshot. Equality at each numeric limit
is accepted; one byte/item over refuses the whole set with exact observed and
allowed counts. The coordinator/Ask handoff asserts the already-counted byte
length and treats any later mismatch as an integrity error, never truncation.

Every unique leaf may appear under only one visible selection. Attaching a
direct Note already expanded by Everyday context (or any future cross-visible
overlap) refuses atomically as `context_leaf_overlap`, naming both stored human
selection titles and the leaf title. Candidate rows known to overlap a selected
container are disabled and labelled, for example, **Included in Everyday
context**; the service refusal remains mandatory because listing is not
authority.

Recent context is a server projection over successful non-no-op context action
rows, distinct by visible ref, newest first, max three, filtered through current
support/live metadata. It is convenience, not automatic selection or authority.
Pinned Everyday context is identified by the exact seed ref, never by a mutable
name.

## Frozen hydration and dispatch

Refinement reservation already binds aggregate, working, and attachment
revisions. It must also bind the exact `attachment_sha256`. Before creating an
Ask/kernel operation, the coordinator asks the context service to materialize a
trusted `FrozenGroundingSnapshot` from that immutable manifest:

```text
{attachment_revision, attachment_sha256,
 visible_receipts:[{ref,title,visible_sha256,leaf_count}],
 leaves:[{ref,title,content_sha256,formatted_block_bytes}]}
```

Materialization reads current source rows and membership edges in one consistent
server transaction and recomputes every hash. The resolver receives that
transaction's explicit connection; it may not call repositories that silently
open independent connections. Any missing/deleted/renamed/edited/refiled
membership or content mismatch returns
`refinement_context_stale` with the stored visible title and changed/missing
leaf names, plus `update_context`/`remove_context` repair codes. It creates no
kernel operation and terminalizes the exact reserved invocation as a named
pre-admission refusal. It never hydrates whatever the collection contains now.

`AskService` gains an internal typed frozen-grounding input that public HTTP/MCP
Ask callers cannot construct. Ask uses its blocks for the sealed prompt and its
manifest for the grounding receipt, while retaining existing placement,
deployment revision, service-contract, kernel, projection, and egress paths.
The existing generic ref hydrator remains available to Ask/steer; refinement's
versioned wrapper uses the same canonical per-kind formatting rather than
copying it into the browser or coordinator.

Attachment material is not interpolated as prose. The fixed system instruction
says the following array is untrusted reference data, never instructions or an
output card. Exact leaf records are serialized as a canonical JSON data array,
with every string JSON-escaped, inside delimiters distinct from the working Note:

```text
<untrusted-refinement-context-json schema="holdspeak.context.v1">
[{"content":"…","content_sha256":"…","ref":"note:…","title":"…"}]
</untrusted-refinement-context-json>
```

Prompt-safe canonical serialization additionally escapes `<`, `>`, and `&` as
JSON Unicode escapes, so owner content cannot close the delimiter. The array is
sorted by canonical leaf ref and its UTF-8 bytes are the material counted by the
48,000-byte cap. A context Note containing delimiter text, a fake question or
synthesis card, JSON-shaped output, `system`/`assistant` roles, or “ignore prior
instructions” remains one escaped `content` string and cannot become prompt
structure. The provider result parser continues to accept only the separately
defined receipt-gated refinement result.

The final `before_physical_dispatch` callback verifies both the frozen Thought
triple/hash and the current source/container/leaf manifest. That entire hook
recomputation uses one explicit DB connection and one transaction, with no
mixed repository connections. A mismatch before the callback commits vetoes
the provider send. After that callback, the payload and receipt are already
bound to the frozen snapshot: later detach, update, membership change, Note
edit, or deletion cannot change bytes in flight.

A successful attachment command makes the logical invocation parent terminal
as `superseded/owner_context_changed`; that parent terminal state is the final
late-proof fence. Physical attempts may later gain an auditable native kernel
receipt/result or cancellation disposition, but reconciliation checks the
terminal parent first and can never promote that proof to review-ready, mutate
the Note, or erase the native audit trail.

When a question is already review-ready, its Used-context receipt continues to
name the exact frozen version even if current sources later change. Reject
remains safe. Answer remains an explicit owner-text write and does not pretend
to accept model prose. A synthesis **Accept**, and every HS-141-07/08 local or
external proposal acceptance, must revalidate the exact frozen attachment hash
and current source manifest immediately before the owner transition; stale
context refuses by name with Update context/Remove it and writes nothing.
Updating or detaching through this story supersedes the review atomically.

## HTTP and MCP are one exact API

HTTP is a thin adapter over the application service:

```text
GET /api/thoughts/{id}/context
  ?view=compact|browse&query=&limit=&cursor=
  -> {attachments, pinned, recent, results, next_cursor}

POST /api/thoughts/{id}/context/attach
POST /api/thoughts/{id}/context/detach
POST /api/thoughts/{id}/context/refresh
  {request_id, ref,
   expected_aggregate_revision,
   expected_working_revision,
   expected_attachment_revision}
  -> {thought, receipt}
```

MCP exposes the same service operations and schemas:

```text
thought.list_context
thought.attach_context
thought.detach_context
thought.refresh_context
```

`thought.list_context` takes `thought_id`, optional title query, explicit
`compact|browse`, bounded limit, and opaque cursor. Mutation tools take exactly
the same ref/request/cursors as HTTP. Their schemas set
`additionalProperties:false`; descriptions explicitly say refs only and no
copied context. MCP cannot select a model, inject a prompt, submit Note bytes,
invent leaves, or bypass application-service validation.

The existing `holdspeak://thoughts/{id}` owner resource includes the same safe
current `attachments` projection as the HTTP Thought DTO. It does not expose
raw context bodies, Ask/kernel IDs, hidden candidates, or continuity on a
remote peer. HTTP/MCP parity tests call reciprocal transports against the same
database and compare post cursors, attachment hash, receipt identity, visible
refs, leaf receipts, stale errors, and idempotent replay.

## DTO and receipt projection

Every owner Thought DTO gains:

```json
{
  "attachment_revision": 2,
  "attachment_sha256": "…",
  "attachments": [{
    "ref": "knowledge:hs-seed-everyday-context",
    "kind": "knowledge",
    "title": "Everyday context",
    "leaf_count": 5,
    "state": "current",
    "leaves": [{"ref":"note:…","title":"About me","version_label":"…"}]
  }]
}
```

Current Thought reads may mark a stored selection `stale` by comparing hashes,
but never mutate it or replace stored names. Hash comparison failure is an
honest availability state, not a reason to omit the attachment. Ordinary list
projections may return only ref/title/count/state; the full owner Thought and
review receipt may expand leaf names/versions. NODE/paired projections carry
the validated aggregate attachment ledger but no hub-local invocation/review
continuity.

Context action receipts name action, visible ref/title, exact post revision and
attachment hash, and expanded leaf names/version hashes. Refinement review
receipts name all visible selections and exact leaves actually sent, placement,
and egress. Neither receipt contains Note bodies, prompts, raw Thought text,
credentials, browser cache fields, or unsupported source material.

## Concurrency, sync, privacy, and fault matrix

| Situation | Required outcome |
|---|---|
| new/fresh Thought | revision 0, canonical empty hash, `attachments:[]`; Everyday remains merely pinned |
| two tabs attach against one cursor | one aggregate revision wins; loser gets current DTO; no merged guess or lost ref |
| exact lost-response attach retry | same action receipt and post cursors; no second revision |
| same ref attached with a new request | byte-identical no-op receipt; no aggregate churn |
| attach unsupported/malformed/self-working Note | named refusal; zero child rows/command/receipt |
| Everyday contains unsupported/nested/cyclic/duplicate/missing/self leaf | whole selection refuses by visible name; no partial expansion |
| selection exceeds leaf cap | named exact counts; no truncation or provider send |
| container renamed, membership changed, or leaf edited/deleted before refine | stale by stored human names; Update context/Remove it; no kernel operation |
| source changes after materialization but before dispatch hook | hook refuses; zero provider send |
| source changes after committed dispatch hook | provider receives frozen old bytes; receipt names exact old hashes; current mutable bytes never substitute |
| attach/detach/refresh during reserved/live/review turn | one attachment command and atomic `owner_context_changed` supersession; late result cannot surface |
| stale synthesis Accept | named context conflict; no Note revision/action receipt |
| Answer to an already shown frozen question | exact owner answer may write; Used receipt keeps old version truth; no model auto-turn |
| stale proposal acceptance in later stories | named context conflict; update proposal only after explicit Update context and regeneration |
| provider failure/refusal/timeout | attachments remain visible/current or stale; working Note stays editable and finishable |
| browser sends title/body/leaves/hash fields | route/schema rejects extras; service accepts refs/cursors only |
| malicious MCP supplies copied context or unsupported ref | schema/service refusal identical to HTTP; no alternate path |
| sync receives revision number without complete child rows | reject entire Thought bundle; do not install partial aggregate |
| sync receives changed/reordered child rows with same hash | canonical recomputation mismatch; reject entire bundle |
| peer has ledger but source primitive has not arrived | install valid metadata ledger, show unavailable/stale on that hub, refuse refine until source converges or owner removes |
| delayed older sync bundle | existing aggregate CAS/high-water law wins; cannot roll attachment set back |
| attachment mutation races working edit/Good enough | aggregate CAS chooses one; loser receives current DTO; no split command state |
| DB failure after child insert but before aggregate/action row | transaction rolls back completely |
| restart after committed attachment | exact chips, names, hashes, revision, and stale state reload; no browser cache required |
| search/browse source disappears between list and attach | attach re-resolves and refuses by listed ref/name; candidate metadata is never authority |

### Sync law

The refinement sync schema carries every attachment revision referenced by its
command ledger, each visible row, and each exact leaf row. Sync validation must:

1. require contiguous attachment revisions from 1 through the advertised
   `attachment_revision` (revision zero is the canonical empty set);
2. preserve every v1 command/hash exactly, require histories to be a v1 prefix
   followed by a v2-only suffix, reject v2-to-v1 downgrade, and recompute v2
   with its mandatory attachment hash—never “upgrade” a v1 hash in place;
3. require one revision row per `replace_attachments` command and matching
   aggregate revision;
4. reject missing/extra/duplicate visible or leaf children, unsupported kinds,
   non-qualified refs, self-working refs, count mismatches, cross-visible leaf
   overlap, or any ordinal other than the exact zero-based canonical-ref
   position;
5. recompute every leaf/visible/attachment hash from wire metadata, then require
   the aggregate command's and Thought head's `attachment_sha256` to agree;
6. validate the complete bundle before inserting any Thought, Note, command, or
   attachment child; and
7. keep attachment action receipts, recents, model invocations, reviews, and Ask
   proof hub-local. They are not sync authority.

A peer does not re-resolve current local content during bundle validation and
thereby rewrite history. It validates the cryptographic metadata ledger, then
separately reports current source availability/staleness. Only a later explicit
owner Update context (`refresh_context` on the transport) creates a new
attachment revision.

## Exact implementation seams

* `holdspeak/db/schema.py`, `holdspeak/db/refinement_thoughts.py`, and
  `holdspeak/services/refinement_thought_service.py` — immutable attachment
  children, action receipts, aggregate/hash integration, DTO, CAS,
  terminalization, and sync ledger validation.
* `pm/roadmap/holdspeak-mobile/contracts/schemas/refinement-thought.schema.json`
  and sync service validation — full versioned attachment child contract;
  continuity/action receipts stay local.
* a narrow `holdspeak/services/refinement_context_service.py` (or equivalently
  named domain service) — supported catalog, canonical resolution/versioning,
  replace-set command, recents, stale checks, and frozen snapshot. It is not a
  generic context registry or tool router.
* `holdspeak/grounding.py` — extract/reuse canonical Note/Knowledge block
  formatting and add exact untruncated versioned resolution; preserve generic
  Ask/steer behavior outside this flow.
* `holdspeak/services/refinement_application_service.py` — the sole shared
  list/attach/detach/refresh boundary for HTTP and MCP.
* `holdspeak/services/refinement_coordinator.py` and
  `holdspeak/services/ask_service.py` — trusted frozen snapshot, pre-admission
  and pre-dispatch manifest fences, truthful Used-context result projection;
  no public copied-material input.
* `holdspeak/web/routes/primitives/thoughts.py` and
  `holdspeak/mcp/families/thought.py` — exact thin transport parity.
* `web/src/desk/thoughts.ts` — refs/cursors-only typed clients and authoritative
  DTO installation.
* `web/src/desk/pullouts/NotePullout.tsx` plus a small Thought-specific context
  picker component — in-body AI context row, pinned/recent/search/Browse,
  immediate mutation, chips/detail/stale repair. Do not mount the existing
  full `GroundingSection` catalog.
* furnished seed is reused unchanged; no automatic attachment flag or new
  personal facts are added.

## Exact focused tests

### Service, grounding, and aggregate

* revision zero has empty hash and no attachment rows; no model prompt contains
  Everyday context until an explicit attach commits;
* direct Note and seeded Everyday resolve to exact visible/leaf rows and hashes;
  edited seeded contents—not packaged defaults—are frozen;
* container name, membership edge version, leaf title/body/tags/version, and
  deletion each independently make the old manifest stale;
* unsupported kind, other Knowledge ref, nested/cyclic/duplicate membership,
  self-working Note, malformed ref, missing leaf, empty collection, and
  over-cap collection refuse atomically with human names and no truncation;
* direct-Note/Everyday and synthetic cross-container overlap refuse atomically,
  naming both human selections and the leaf; candidate projection marks the
  direct Note Included and disabled without weakening the service fence;
* canonical hashing is stable across DB row order and sync serialization and
  changes on every material source/version change;
* v1 fixture commands keep their exact canonical bytes/hashes; the first new
  command is v2 with the empty/current attachment hash, every later command is
  v2, and local/sync v2-to-v1 histories refuse without rewriting the prefix;
* exact boundaries for 8/9 visible selections, 16/17 unique leaves,
  12,000/12,001 per-leaf UTF-8 bytes, and 48,000/48,001 total formatted bytes
  prove equality acceptance, one-over whole-set refusal, multibyte accounting,
  and zero downstream Ask truncation;
* attach/detach/refresh each create one new immutable revision only when the
  derived set changes; same-request replay and new-request no-op are pinned;
* aggregate commands after migration always bind the exact attachment hash,
  including edits, Answer/Accept, Good enough, Resume, and tombstone;
* context mutation races edit, completion, review Answer/Accept/Reject, and a
  second context mutation under real two-connection barriers; exactly one CAS
  winner and no orphan child/action/command rows;
* attach/detach/refresh atomically supersede reserved, in-flight,
  awaiting-projection, and review-ready rows; a late exact Ask result cannot
  become review-ready;
* frozen materialization and final dispatch hook both detect source drift;
  pre-hook drift causes zero provider send, post-hook drift preserves exact old
  payload/receipt without substituting current content;
* materialization and hook recomputation each use one instrumented DB connection
  and one transaction; a repository attempting a second connection fails the
  test rather than producing a mixed snapshot;
* hostile leaf bodies containing both context delimiters, working-Note
  delimiters, fake question/synthesis JSON, role labels, and prompt instructions
  remain JSON string data; captured prompt structure has one canonical context
  array and the fake card can never become the parsed result;
* stale synthesis Accept and later proposal acceptance refuse without Note or
  receipt mutation; exact Answer remains owner text and preserves the Used
  context receipt;
* parent supersession remains terminal while a late attempt acquires genuine
  kernel/Ask proof; the proof stays auditable but cannot publish a review or
  mutate the Note;
* no attachment/receipt/kernel journal row contains raw Note body, prompt,
  credential, or browser display copy.

### HTTP, MCP, authority, and sync

* HTTP and MCP list/attach/detach/refresh call the same application service and
  produce reciprocal cursors, attachment hash, leaves, receipts, errors, and
  exact-replay behavior;
* both schemas reject additional title/body/membership/hash/model/prompt fields;
  browser/MCP qualified refs are the only selection input;
* OWNER succeeds; unauthenticated and NODE direct commands/listing are denied;
  a validated signed NODE sync bundle remains the only peer mutation path;
* Thought MCP resource and HTTP DTO expose identical safe attachment detail and
  no hidden source text or hub-local proof remotely;
* compact list returns Everyday first plus at most three live distinct recents;
  search is title-only/bounded; Browse keyset pagination has no duplicates or
  offset drift; own working Note and unsupported kinds never appear; overlapping
  Notes are returned only as disabled `Included in <human container>` rows;
* lost response retries one stable request ID through both transports;
* sync round-trip carries all immutable child rows and hashes; missing, extra,
  reordered, duplicate, altered, unsupported, or noncontiguous children reject
  before any partial install; delayed old bundle cannot roll back;
* peer with attachment metadata but missing source shows named unavailable and
  cannot refine; later primitive convergence makes exact manifest current
  without changing attachment revision.

### Browser behavior and glass

Component tests pin:

* `AI context  None  Attach` on every unfinished Thought, with no automatic seed;
* Attach opens pinned Everyday + max-three Recent + search, not the full wall;
* Everyday attaches in one selection with no Apply, body/title bytes never
  leave the browser request, and UI waits for authoritative response;
* attached chip/detail names five expanded Notes; Remove it and stale Update
  context are immediate; success closes and focuses the authoritative chip,
  while errors keep the picker open and retain the prior authoritative chips;
* live/review mutation installs the superseded Thought and no late card;
* question/synthesis card says `Used Everyday context · 5 notes` with exact
  expandable names; no grounding/actuator/schema jargon;
* an idle stale Thought removes the model action and has only Update context or
  Remove it as primary; a stale question keeps Answer primary with quiet Update;
  a stale synthesis has no Accept and only the context repair primary;
* at 393 only the state-specific action is primary, Attach remains directly
  reachable in-body, the sheet does not autofocus search, Everyday stays above
  the keyboard line, chips wrap vertically, and there is zero horizontal
  overflow.

Real isolated-HOME glass at 1440×900 and 393×900 must walk:

1. open an unfinished Thought and prove AI context is None;
2. edit one seeded leaf through its real Note API to contain the distinctive
   phrase `ORCHID CLOCK belongs in the launch note` before attaching it;
3. press Attach and capture the compact unopened-catalog state;
4. select Everyday context in that single interaction and capture the five
   human leaf names;
5. reload browser and restart hub; prove the same revision/chip and edited leaf
   version return;
6. run one genuine API/kernel refinement through the labelled deterministic
   provider. The
   provider fixture returns its question only when that exact phrase arrives in
   the exact expected formatted leaf block; capture `Used Everyday context · 5
   notes` and assert the provider-observed canonical context JSON, delimiters,
   leaf order, content hashes, and formatted bytes are byte-equal to the server
   manifest—not merely that the response contains the phrase. Explicitly
   **Answer** the question and prove that exact owner answer is written once;
7. edit that attached Note again, retaining the marker as `ORCHID CLOCK belongs
   in the launch note, version two`; from the now-idle Thought prove context is
   named stale, the model action is absent, and an API/MCP refine attempt causes
   zero provider sends;
8. press **Update context** once, rerun, capture the new Used-context version and
   exact version-two formatted bytes, then explicitly **Reject** that question
   and prove no Note mutation;
9. start a separate delayed refinement turn, detach context while it is live,
   and prove parent supersession plus late-result suppression; no review appears;
10. drive list/attach/refresh/detach through MCP against the same app service and
   show the browser reflecting each authoritative change after reload; and
11. record zero console errors, zero overflow, one primary per state, and no
    copied context material in HTTP/MCP request captures.

The walk uses an isolated HOME/database and a deterministic model provider only
for inference output. Its phrase-contingent response is the negative control:
without the exact frozen block it must refuse/fail, never emit the expected
question. The walk may not seed attachment/review rows directly or forge
receipts. All context operations travel through the real HTTP or MCP application
service.

## Contract self-audit

* **Power-user and YOLO first:** Everyday is one immediate choice, attachments
  commit without Apply/confirmation, and configured refinement runs normally.
  Nothing attaches or invokes a model without the owner's direct action.
* **Progressive disclosure:** the useful pinned/recent/search interaction is
  first; only the full Note catalog is behind Browse. The capability itself is
  not hidden.
* **Raw/working custody:** attachment commands change neither raw nor working
  bytes. They advance only attachment + aggregate revisions and use the existing
  command/CAS ledger.
* **One-question law:** context changes never start or continue refinement.
  They supersede an old turn; the owner explicitly requests the next one.
* **SOA/MCP law:** the application service is exact authority; browser and MCP
  are interchangeable thin adapters. No UI-only attachment state exists.
* **Privacy:** default empty; visible refs only; server-side exact hydration;
  no hidden membership drift, copied body authority, receipt text leakage, or
  unsupported context kind.
* **Failure stays useful:** stale/missing context has named Update context/Remove it;
  local editing and completion remain available with no model or context.
* **No parallel subsystem:** this extends the Thought aggregate and Ask
  grounding path. It does not create chat, agent memory, a generic context
  registry, planner, tool router, proposal lifecycle, or executor.
