# HS-141-05A design beat — default AI context

**Status:** implemented and glass-proven; final technical and owner-glass
counsel both **RATIFY**.

## Owner contract

An owner may tell this hub which qualified context refs to attempt on every
Thought created here from now on. The shipped default remains **None**. Once the
owner configures a non-empty default, every newly captured or adopted Thought
opens with those selections already visible in its **AI context** row when they
still resolve safely. If they do not, capture/adoption still succeeds empty and
shows a durable, named `Default AI context was not applied` receipt; it never
pretends the default was used.

This is a fast default, not hidden autonomy:

* applying it creates no model, Ask, kernel, proposal, or tool invocation;
* the resulting attachment is an ordinary immutable per-Thought attachment
  manifest, subject to every HS-141-05 stale, privacy, size, and receipt rule;
* changing the default never edits an existing Thought, even one that is still
  empty, idle, or has never been refined;
* **Remove from this Thought** changes only the open Thought. It does not disable
  the default;
* disabling the default is a separate explicit **Stop using by default** owner
  action; and
* a future explicit bulk action may offer to update existing Thoughts, but it is
  out of scope here. There is no implicit or startup backfill.

The preference means “attach the current versions of these refs when a future
Thought is born.” It is not a content snapshot. Each born Thought freezes the
exact visible containers and leaf versions it received. Later source changes
therefore affect later Thoughts, while already-created Thoughts become stale
under the existing named repair law rather than drifting.

## One compact owner interaction

Do not add a settings room, onboarding gate, or second context picker. Keep the
existing picker title **Attach context** and its existing pinned/recent/search/
Browse behavior.

The picker begins with two exact, non-truncated groups before its existing
candidate groups. **On this Thought** lists every currently attached visible ref.
**For new Thoughts** lists the complete configured default set. Each row shows
its human title; qualified ref remains available in the existing detail. At
393px rows stack, but neither group collapses into a count or horizontal strip.

With no attachment and no configured policy:

```text
On this Thought
None
Attach context to use it by default.

For new Thoughts
None
```

An empty **On this Thought** group has no **Use these by default** action. Once
one or more refs are attached, the group offers **Use these by default**. That
one action replaces the whole policy with the complete displayed On-this-Thought
set; it never appends a single hidden ref. The server receipt says exactly
`Used Everyday context + Project launch for new Thoughts` (with the complete
human-name set in detail).

Every attached row whose ref is also in the configured policy carries a
persistent **Default** marker. Its per-Thought action is exactly **Remove from
this Thought**, and its receipt says `Removed Everyday context from this Thought;
the default for new Thoughts is unchanged.` It never calls the default-policy
service. The detach receipt carries `scope: "this_thought"` and
`default_context_changed: false`.

When policy is non-empty, **For new Thoughts** lists every configured selection
and then exposes one **Stop using by default** action for the complete set:

```text
On this Thought
Everyday context               Default    Remove from this Thought
Project launch                            Remove from this Thought

For new Thoughts
Everyday context
Stop using by default
```

Stop replaces the whole policy with the empty set. Its exact scoped receipt is
`New Thoughts start with no AI context. This Thought is unchanged.` It does not
detach anything from the current or earlier Thoughts. The action is absent when
policy is already empty. Likewise, **Remove from this Thought** never changes
the For-new-Thoughts group. The server projection, not optimistic local state,
drives both complete lists and every Default marker.

The existing list-context application response is extended atomically with
`default_context` and `attachments[].default`. The default projection contains
the complete configured set including unavailable last-known rows. Thus one
server read drives both picker groups and markers; the browser does not join two
potentially different revisions or infer policy from a badge.

A newly created/adopted Thought renders the authoritative attached chips on its
first response, with a quiet `Attached by default` receipt disclosure. When a
configured source cannot be applied, that same first response renders
`AI context  None` and the named `Default AI context was not applied` receipt.
An empty-policy receipt remains in the API/restart proof but may be omitted from
the visual body. There is no loading state in which a committed response changes
afterward. At 393px the footer remains below the candidates in the same sheet,
does not autofocus search, and never displaces pinned Everyday context above the
keyboard.

The UI is only one client of the application service. MCP may replace the exact
default set directly, without manufacturing a temporary Thought.

## Authoritative split

There are two deliberately different records:

1. **Hub-local default policy:** a revisioned, owner-only list of qualified refs.
   It says what this hub should attempt for a future local create/adopt.
2. **Synced Thought fact:** the exact immutable visible/leaf manifest and v2
   aggregate command chain applied to one born Thought.

The default policy is never prompt material and never syncs. A peer installing a
Thought does not run its own local default. The born Thought's command and
attachment ledger sync normally, so the peer sees and validates the exact
context that was actually attached. A peer's own default remains unchanged.

This follows the existing local-policy boundary: paired-node authority may
install canonical aggregate state, but it may not configure an owner's local
automation posture. Owner HTTP and owner MCP are the only public authorities for
the preference.

## Persistence and canonical identity

Add four narrow local tables; do not put this preference in generic settings or
inside a mutable JSON blob.

```text
refinement_default_context_current
  id = 1
  revision
  configuration_sha256
  refs_json
  updated_at

refinement_default_context_revisions
  revision
  configuration_sha256
  refs_json
  labels_json
  created_at

refinement_default_context_actions
  action_id
  request_id UNIQUE
  request_sha256
  prior_revision
  post_revision
  post_configuration_sha256
  receipt_json
  created_at

refinement_default_context_applications
  application_id
  thought_id UNIQUE
  create_request_id UNIQUE
  default_revision
  default_configuration_sha256
  status = empty | applied | not_applied
  attachment_zero_sha256
  attachment_revision
  attachment_sha256
  error_code
  failure_json
  failure_sha256
  receipt_json
  created_at
```

`refs_json` is a canonical JSON array of unique qualified refs ordered by ref.
It contains no copied title, body, leaf list, prompt text, or browser-authored
metadata. Revision zero is seeded as the empty set. Its exact identity is:

```json
{"revision":0,"refs":[],"schema":"holdspeak.default-ai-context.v1"}
```

`configuration_sha256` is SHA-256 over that canonical UTF-8 JSON. Every
non-no-op replacement increments revision once and hashes the same structure
with the new revision and sorted refs. `labels_json` is a safe, immutable
receipt snapshot of server-resolved human titles and leaf counts. It is not an
authority input for later Thought creation.

The replacement request hash is SHA-256 over canonical JSON containing the
operation name, expected default revision, and sorted refs. The same request ID
and same payload returns the original action receipt while it remains the live
post-state. Reusing the ID with different content refuses. An exact replace-set
no-op does not increment the revision but still writes and returns an honest
`no_op: true` receipt. If its post-state was later superseded, replay refuses
with the current default projection rather than pretending to have applied now.

The default mutation receipt is:

```json
{
  "id": "rdctx_…",
  "action": "replace_default_context",
  "scope": "future_thoughts",
  "prior_revision": 2,
  "revision": 3,
  "configuration_sha256": "…",
  "refs": ["knowledge:hs-seed-everyday-context"],
  "selections": [
    {"ref": "knowledge:hs-seed-everyday-context", "title": "Everyday context", "leaf_count": 5}
  ],
  "no_op": false
}
```

Every replace/clear receipt also carries `existing_thoughts_changed: 0`. UI copy
may say “This Thought is unchanged” only when the action was launched from a
Thought picker; the transport receipt itself makes the broader exact claim.

Every local create/adopt writes exactly one application row and receipt. It
binds the exact policy revision/hash read under the birth transaction, the exact
per-Thought attachment-zero hash at command 1, and the final attachment
revision/hash returned after the optional command 2. A successful receipt is:

```json
{
  "id": "rdapp_…",
  "action": "apply_default_context",
  "scope": "this_thought",
  "thought_id": "thought_…",
  "default_revision": 3,
  "default_configuration_sha256": "…",
  "status": "applied",
  "attachment_zero_sha256": "…",
  "attachment_revision": 1,
  "attachment_sha256": "…",
  "attachments": [
    {"ref": "knowledge:hs-seed-everyday-context", "title": "Everyday context", "leaf_count": 5}
  ]
}
```

An empty-policy birth has `status: "empty"`, the exact policy revision/hash,
`attachment_zero_sha256` equal to `attachment_sha256`, attachment revision zero,
and `attachments: []`. This provenance is durable and returned over HTTP/MCP and
on retry even though the owner UI may quietly omit its receipt disclosure.

If a once-valid configured source cannot safely resolve at birth, the receipt
instead has `status: "not_applied"`, attachment revision zero and its exact
per-Thought empty/result hash, plus
`failure: {code, selections: [{ref, title}], leaf?: {ref, title}}`. Overlap names
both selections; missing/self-reference names the exact affected selection. It
contains no exception text or source body.

For `not_applied`, the application row also stores independent canonical
`failure_json` plus its SHA-256. That closed proof binds the stable code, the
sorted unique nonempty affected visible refs/titles, and any leaf ref/title to
one affected visible selection. Replay reconstructs `receipt.failure` from
those durable fields rather than trusting mutable receipt JSON; swapping the
failure to another valid default or an unrelated leaf refuses.

This local receipt survives restart and is returned on an exact create/adopt
retry. It contains no Note bodies. The synced create/adopt + optional
replace-attachments command chain and manifest are the portable native proof; no
sync consumer needs the hub-local preference or application receipt to validate
the Thought. If a request ID resolves to a sync-installed Thought on a peer but
that peer has no local application row, create/adopt retry refuses with
`default_context_application_proof_unavailable`; it never invents the origin
hub's policy revision/hash.

## Atomic Thought birth

Move public create and adopt entry into the same transport-neutral
`RefinementApplicationService` that owns context mutations. It coordinates the
existing custody service and `RefinementContextService` on **one database
connection and one `BEGIN IMMEDIATE` transaction**. Do not call a public service
method that opens a second connection.

For both a raw create and ordinary-Note adoption:

1. validate owner authority, request id, source preconditions, Inbox, and
   working-Note ownership exactly as today;
2. read and verify the single current default revision/hash;
3. allocate the Thought and working Note identities in memory;
4. insert the working Note, Thought, working revision, lifecycle revision,
   attachment-zero birth aggregate command, and Inbox membership;
5. resolve the configured refs through the existing context resolver against
   that actual working Note identity, enforcing self-reference, overlap,
   visible/leaf/UTF-8/total caps, supported kinds, deletion, and human names;
6. on success, append one ordinary attachment revision and v2
   `replace_attachments` command; on a named resolution failure, keep the
   attachment-zero birth and write a `not_applied` receipt instead; then write
   the mandatory `empty`, `applied`, or `not_applied` application row/receipt in
   the same transaction; and
7. return only after commit with the final Thought projection and that
   application receipt.

There is never an externally observable or separately committed intermediate.
A successfully applied non-empty default is born through two commands in the
same transaction:

```text
command 1
  aggregate_revision = 1
  working_revision = 1
  lifecycle_revision = 1
  attachment_revision = 0
  command_kind = create | adopt_note
  canonical_version = 2
  attachment_sha256 = per-Thought empty hash

command 2
  aggregate_revision = 2
  working_revision = 1
  lifecycle_revision = 1
  attachment_revision = 1
  command_kind = replace_attachments
  canonical_version = 2
  prior_attachment_revision = 0
  next_attachment_revision = 1
  attachment_sha256 = exact manifest hash
```

An empty default, or a named fail-open result, commits only command 1 at
attachment revision zero. Historical v1 hashes are untouched. There is no
v2-to-v1 downgrade and no rewriting of an older head. The attachment verifier
and sync validator keep their existing law that every nonzero attachment header
is owned by a matching v2 `replace_attachments` command. The successful default
path therefore reuses the ratified grammar instead of adding a birth exception.

Fail-open is narrow and honest: only resolution failures attributable to the
configured default become `not_applied`. A bad create/adopt request, source
precondition conflict, custody conflict, corrupt default ledger, database fault,
or invariant failure still rolls back/refuses normally. A `not_applied` result
never persists a partial manifest or some subset of the refs.

The caught set is closed and mapped to stable public codes:
`default_context_missing`, `default_context_empty`,
`default_context_kind_unsupported`, `default_context_self_reference`,
`default_context_leaf_overlap`, and `default_context_too_large`. Unexpected
`ValidationError`/`ConflictError` codes are not swallowed. Tests must prove a
database error, corrupt hash, malformed ordinal, or programmer exception cannot
masquerade as a convenience-policy miss.

The caller's create/adopt payload hash does **not** include the ambient default:
the caller did not author it. Retrying a committed request after the default
changes returns the originally born Thought and original application receipt;
it never reapplies the newer default.

## Default resolution rules

The same HS-141-05 resolver is authoritative. Do not build a lighter settings
validator that later disagrees with Thought creation.

* Only qualified `note:` refs and the exact supported seeded
  `knowledge:hs-seed-everyday-context` ref are accepted initially.
* Refs are de-duplicated and canonically ordered before validation.
* The set is limited to 8 visible selections, 16 unique leaves, 12,000 UTF-8
  bytes per formatted leaf, and 48,000 UTF-8 bytes of total canonical material.
  Counts happen before any truncation; the whole replacement refuses.
* Cross-visible leaf overlap refuses atomically and names both human selections.
* Configuration rejects missing, deleted, empty, unsupported, overlapping, or
  over-cap refs. Clearing to `[]` never requires a deleted old ref to resolve.
* Creation resolves the set again. Valid source edits and membership changes are
  intentionally reflected in future Thoughts and frozen there. A default that
  became invalid after configuration is not applied at all: the Thought commits
  empty with a durable receipt naming the last-known human selection and exact
  error. It never silently drops only one selection.
* Adopting a Note that is itself a direct default, or is contained by a default
  Knowledge selection, succeeds as an empty-context Thought with a named
  `default_context_self_reference` not-applied receipt. Custody is not made
  hostage to a stale local convenience policy.

`GET default` is useful even when a ref is now broken. It returns its last-known
name plus `state: "missing" | "invalid"`, the qualified ref, and the repair
action. It never substitutes another object. A current source rename may be
shown with the current name, while the immutable prior receipt keeps the name
that was true when configured.

## Exact application boundary and transports

Add the two default-policy operations and move the existing two custody ingress
operations behind the same transport-neutral application service:

```text
get_default_context(principal)
replace_default_context(principal, request_id, expected_revision, refs)
create_thought(principal, request_id, raw_text, source, initial_note)
adopt_note(principal, request_id, note_id,
           expected_source_content_sha256, expected_source_last_modified)
```

The create/adopt application operations also use this boundary internally; no
HTTP route or MCP handler resolves refs, writes tables, or applies defaults.

HTTP:

```text
GET /api/thoughts/default-context

PUT /api/thoughts/default-context
{
  "request_id": "…",
  "expected_revision": 3,
  "refs": ["knowledge:hs-seed-everyday-context"]
}
```

MCP mirrors it exactly:

```text
thought.get_default_context {}

thought.replace_default_context {
  "request_id": "…",
  "expected_revision": 3,
  "refs": ["knowledge:hs-seed-everyday-context"]
}

thought.create {
  "request_id": "…",
  "raw_text": "…",
  "source": {"kind": "typed", "ref": null},
  "initial_note": {"title": "…", "body_markdown": "…", "tags": []}
}

thought.adopt_note {
  "request_id": "…",
  "note_id": "…",
  "expected_source_content_sha256": "…",
  "expected_source_last_modified": "…"
}
```

Both transports use closed schemas. On default operations, unknown keys, copied
bodies, titles, leaf metadata, model names, prompts, and attachment hashes
refuse. Both return the same `{default_context}` or
`{default_context, receipt}` projection and the same error code/status semantics.
Default replacement does not require a Thought cursor because it has its own
revision/CAS domain.

For the two default operations, “refs-only” is absolute: no copied context
material crosses either transport. `thought.create` necessarily accepts its own
new raw/working Note content, just as HTTP create already does, but it accepts no
context material or default override. `thought.adopt_note` accepts only the Note
identity and exact source precondition. The HTTP create/adopt routes now call the
same application methods; they may not call `RefinementThoughtService` directly.

Static HTTP routes must be registered before `/{thought_id}`. Adding
`thought.create` and `thought.adopt_note` closes the existing transport gap so
HTTP and MCP have exact custody/default semantics, including the same final
Thought and application receipt on success or named fail-open.

Create/adopt return the same closed envelope on both transports:

```json
{
  "thought": {"id": "thought_…", "attachment_revision": 0, "attachments": []},
  "default_context_receipt": {
    "id": "rdapp_…",
    "action": "apply_default_context",
    "scope": "this_thought",
    "default_revision": 0,
    "default_configuration_sha256": "…",
    "status": "empty",
    "attachment_zero_sha256": "…",
    "attachment_revision": 0,
    "attachment_sha256": "…",
    "attachments": []
  }
}
```

`default_context_receipt` is mandatory for every local create/adopt and is the
exact `empty`, `applied`, or `not_applied` receipt above. The illustrative
Thought object's normal attachment projection is not abbreviated in the real
response. Sync installation is not local creation/adoption and does not invent
an application row or receipt.

The safe default projection is:

```json
{
  "default_context": {
    "revision": 3,
    "configuration_sha256": "…",
    "refs": ["knowledge:hs-seed-everyday-context"],
    "selections": [
      {"ref": "knowledge:hs-seed-everyday-context", "title": "Everyday context", "leaf_count": 5, "state": "current"}
    ]
  }
}
```

It exposes no body, tag set, prompt material, membership timestamps, or content
hashes. Pipeline events summarize counts and hashes, never refs plus bodies.

## CAS, concurrency, failure, and privacy matrix

| Event | Required result |
|---|---|
| fresh install/migration | revision-zero empty default; every existing Thought byte/revision/hash unchanged |
| local create/adopt under empty policy | normal attachment-zero birth plus mandatory durable `empty` application receipt binding policy and result hashes |
| owner replaces empty with Everyday context | one local default revision and receipt; no Thought/model/kernel mutation |
| requested replacement contains an invalid ref/set | replacement refuses atomically and retains the prior default head |
| exact replacement retry | original receipt/result; no new revision |
| request id reused with different refs | deterministic payload-mismatch refusal |
| two default replacements race | `BEGIN IMMEDIATE` + expected revision gives one winner; loser receives current safe projection |
| create/adopt races default replacement | serialization chooses the complete old or complete new set; application receipt proves which |
| source changes while create/adopt resolves | same-transaction resolution freezes one coherent version or commits empty with a named not-applied receipt; never mixed membership/leaves |
| valid source changed since default configuration | future Thought receives current exact version; prior Thoughts remain unchanged and may become stale |
| configured source deleted/unsupported/over cap | create/adopt succeeds empty; durable not-applied receipt names the selection/error; no partial attachment exists |
| adopted working Note overlaps default | adoption succeeds empty with named self-reference not-applied receipt |
| crash at any birth write | transaction rolls back the whole working Note/Thought/manifest/receipt unit |
| duplicate committed create after default changed | return original Thought/application receipt; never attach newer default |
| Remove from this Thought | ordinary attachment revision/CAS and scoped receipt; hub default is byte-for-byte unchanged |
| Stop using by default | writes empty default revision; receipt says current Thought unchanged; all existing Thought manifests unchanged |
| default changes during live refinement | live invocation and Thought are untouched; no supersession because policy is not Thought state |
| Thought born with default later refines | existing stale fence, immutable material, delimiter, and Ask byte checks apply unchanged |
| sync exports a born-attached Thought | export exact empty birth command, v2 replace command, and manifest; omit local default/actions/app receipt |
| peer installs that Thought | validate command/manifest exactly; do not apply or alter peer default |
| create/adopt request id matches sync-installed Thought without local app row | proof-unavailable conflict; return current Thought identity, never synthesize policy provenance |
| peer has different/missing live sources | existing sync validation/refusal and later named stale behavior; never trust copied default material |
| NODE or unauthenticated default request | owner-authority refusal over HTTP and MCP |
| malicious client sends bodies/metadata | closed-schema refusal before service mutation |

The default is local durable policy, not a privacy escape hatch. Configuration
and application receipts expose safe human names/counts only. Provider material
is still created only immediately before an explicit **Keep refining**, sealed
as untrusted canonical JSON, capped, hash-bound, and never returned by these
default APIs.

## Migration and restart

Schema reconciliation creates the four local tables and inserts the canonical
revision-zero empty current/revision rows. It does not scan Thoughts, infer a
default from recents, choose Everyday context, or append aggregate commands.
Fresh and upgraded installs therefore remain empty by default.

Restart reads the current singleton and verifies its canonical hash before use.
Malformed/missing nonzero history is `default_context_ledger_invalid`; creation
refuses rather than treating it as empty. The owner may repair through an
explicit replace only after the service can establish the current CAS head; a
reconciliation repair must be separately designed, not improvised by a route.

No default table enters sync exports, mobile sync schemas, cloud backup payloads,
or model prompts. Born Thoughts require no new sync kind: their existing command
chain, attachment header, visible rows, and leaf rows remain the exact portable
state.

## Required tests

### Domain and persistence

* migration/fresh DB seeds only revision-zero empty; existing Thoughts and all
  historical v1/v2 command hashes remain byte-identical;
* replace one/many/empty, canonical ref ordering, duplicate collapse, true
  no-op, exact retry, superseded retry, request mismatch, and expected-revision
  conflict;
* owner-only authority and closed refs-only inputs;
* restart preserves current default, immutable revision/action receipts, every
  `empty` application row, exact empty-policy create/adopt replay, and
  invalid-ledger refusal;
* missing/deleted/unsupported/empty Knowledge, direct/collection overlap, and
  exact 8/9 visible, 16/17 unique leaf, per-leaf UTF-8, and total formatted byte
  boundaries.

### Atomic creation/adoption

* empty default creates/adopts today's revision-zero attachment result plus one
  mandatory `empty` application row/receipt binding exact policy revision/hash,
  attachment-zero hash, and identical result hash;
* Everyday and multi-ref defaults create/adopt at aggregate 2 with attachment 1,
  exact manifest/hash, empty v2 birth command, v2 replace command, and one
  application receipt;
* both commands are durable audit history but no attachment-zero intermediate is
  separately committed or observable through a completed response;
* Note/default and Knowledge-member/default self-reference create/adopt safely
  with attachment zero and a named not-applied receipt;
* a default that became missing, overlapping, unsupported, or too large produces
  the complete empty Thought plus durable named receipt, never a partial set;
* changing/clearing default never mutates old Thoughts; per-Thought detach never
  mutates default; clearing never detaches existing Thoughts;
* committed create/adopt retry after a default change returns the original
  attachment and receipt;
* query spies assert one connection/transaction for preference read, source
  resolution, custody, manifest, command, membership, and receipt;
* fake model/kernel/Ask spies assert zero dispatch for get/replace/apply/disable.

### Concurrency and sync

* real two-connection barriers cover replace-vs-replace, create-vs-replace,
  adopt-vs-replace, create-vs-source-edit/delete, and clear-vs-create; every
  result is wholly before or wholly after, never mixed;
* explicit barriers prove both empty→nonempty race orders and both
  nonempty→empty race orders: each birth receipt binds the exact winning policy
  head and its matching empty/applied result;
* crash injection at each write boundary leaves either no birth or one complete
  birth and replay-safe receipt;
* born-attached create/adopt v2 bundles round-trip through sync; tampering the
  command transition, attachment hash/header/count/ordinal, visible metadata, or
  leaf metadata refuses with no partial install;
* sync installation never consults/applies the receiving hub default, never
  exports/imports default policy/action rows, and never changes the receiving
  hub's current default; a cross-hub create/adopt request-id replay without a
  local application row returns proof-unavailable rather than fabricated empty
  provenance.

### HTTP/MCP parity and glass

* GET/get and PUT/replace have reciprocal response/error fixtures, owner
  authority, exact additional-property refusal, and refs-only capture assertions;
* HTTP/MCP create and adopt have reciprocal success, not-applied, idempotency,
  authority, and closed-schema fixtures; the first response contains the final
  authoritative Thought and default application receipt;
* at 1440 and 393, the picker shows complete **On this Thought** and **For new
  Thoughts** groups; empty current context shows
  `Attach context to use it by default.` with no Use action; nonempty policy
  alone shows Stop, and configured attached rows keep their **Default** marker;
* attach Everyday context, choose **Use these by default**, create and adopt
  separate Thoughts, and capture both opening with visible
  `AI context  Everyday context · 5 notes` plus `Attached by default`;
* on one born Thought use **Remove from this Thought** and prove its scoped
  receipt says the default is unchanged and the next Thought still gets
  Everyday context; then press **Stop using by default** and prove its receipt
  says the current Thought is unchanged while the following Thought says
  `AI context  None`;
* edit a source after a default-born Thought exists: at both 1440 and 393 capture
  that existing Thought's visible explanation naming the stale selection,
  **Update context** as the sole state primary, and the successful Update result;
  then create a later Thought and prove it freezes the newer source version
  directly without mutating or reusing the earlier Thought's revision;
* configure a valid multi-ref default, invalidate one member, then at both 1440
  and 393 create/adopt and capture `AI context  None`, whole-set-skipped named
  detail, zero partial chips/leaves, the normal lifecycle primary action (the
  receipt is not a blocking primary), and **For new Thoughts** retaining the
  unavailable last-known selection plus **Stop using by default**;
* throughout every walk assert zero provider/kernel calls from policy or birth,
  no Note body in HTTP or MCP captures, no search autofocus at 393, no overflow,
  and no console/page errors.

## Out of scope

No retroactive update, implicit backfill, bulk mutation, per-project/profile
default, synced preference, default model selection, automatic refinement,
generic context registry, new settings screen, Rails/meeting/artifact/tool
attachment kind, or content-history store. A future bulk action must be an
explicit separately authorized command with its own per-Thought CAS/fault story;
this design reserves no hidden hook for it.

## Counsel questions

1. Is hub-local policy plus fully synced born-Thought manifests the correct
   boundary, or is there a concrete owner job requiring the preference itself
   to roam?
2. Does an empty v2 birth command followed by one ordinary v2 attachment command
   in the same transaction preserve the cleanest existing ledger grammar?
3. Is the narrow fail-open contract honest enough: capture/adoption succeeds
   empty only with a durable, human-named not-applied receipt and no partial set?
4. Can a tired owner distinguish **Remove from this Thought** from **Stop using
   by default** in the compact picker without another settings surface?

## Final rulings

- **Technical counsel — RATIFY.** The final ledger validates canonical revision
  zero, contiguous policy history, legal bounded refs and labels, action
  transition linkage, birth/application proofs, independent named failure
  attribution, v2 command/manifests, strict nested transport inputs, authority,
  restart, races, and sync exclusion. The last blocker was mutable-only
  not-applied attribution; canonical `failure_json` plus its digest and replay
  reconstruction closed it.
- **Owner-glass counsel — RATIFY.** The fresh 1440×900 and 393×900 walk kept the
  shipped default empty, showed complete current/future sets in the existing
  compact picker, made the Default/removal/stop scopes legible, opened later
  Thoughts with the final authoritative set, showed named whole-set fail-open,
  and preserved Update context as the sole stale-state primary. No policy or
  birth action invoked the model.
