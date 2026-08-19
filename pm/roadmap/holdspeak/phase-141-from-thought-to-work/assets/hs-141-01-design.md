# HS-141-01 design beat — raw custody before AI

**Status:** design for counsel; this document authorizes no product code.

## Decision and boundary

Add one durable `refinement_thought` aggregate, not a second mutable Note. Its
immutable raw UTF-8 byte snapshot is the custody record; its one normal `notes`
row is the editable working Note. The aggregate owns working revision,
`unfinished`/`completed` presentation, and the future attachment revision.

HS-141-01 has no model, UI, proposal, tool, or external-effect path. The
power-user/YOLO ruling therefore adds no approval, confirmation, or authority
mechanism here: local capture and edit are always available. This realizes the
raw-before-AI and separate-working-text laws
([proposal](../../proposals/thought-refinement-spine.md#L46-L53)) and the
story's CRUD/sync closure ([story](../story-01-raw-before-ai.md#L15-L29)).

## Persisted shape

Add these tables in `SCHEMA_SQL` after `notes` (the current Note has timestamps
and tombstones but no revision or ownership field:
[`holdspeak/db/schema.py:796-812`](../../../../../holdspeak/db/schema.py#L796-L812)).

```sql
CREATE TABLE refinement_thoughts (
  id TEXT PRIMARY KEY,                         -- `thought_…`; also raw ID
  create_request_id TEXT NOT NULL UNIQUE,      -- caller-stable idempotency key
  create_payload_sha256 TEXT NOT NULL,         -- raw + source + initial Note
  raw_utf8 BLOB NOT NULL,                      -- exact received UTF-8 bytes
  raw_sha256 TEXT NOT NULL,
  raw_source_kind TEXT NOT NULL,               -- typed | voice | note
  raw_source_ref TEXT,                         -- qualified ref when source=note
  raw_captured_at TEXT NOT NULL,
  working_note_id TEXT NOT NULL UNIQUE REFERENCES notes(id),
  working_revision INTEGER NOT NULL CHECK (working_revision >= 1),
  lifecycle_revision INTEGER NOT NULL DEFAULT 1 CHECK (lifecycle_revision >= 1),
  attachment_revision INTEGER NOT NULL DEFAULT 0 CHECK (attachment_revision >= 0),
  aggregate_revision INTEGER NOT NULL DEFAULT 1 CHECK (aggregate_revision >= 1),
  state TEXT NOT NULL CHECK (state IN ('working','completed','tombstoned')),
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  completed_at TEXT, tombstoned_at TEXT
);
CREATE INDEX idx_refinement_thoughts_resume
  ON refinement_thoughts(state, updated_at DESC);

CREATE TABLE refinement_working_revisions (
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  revision INTEGER NOT NULL CHECK (revision >= 1),
  title TEXT NOT NULL, body_markdown TEXT NOT NULL, tags_json TEXT NOT NULL,
  content_sha256 TEXT NOT NULL, accepted_at TEXT NOT NULL,
  PRIMARY KEY (thought_id, revision)
);
CREATE TABLE refinement_lifecycle_revisions (
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  lifecycle_revision INTEGER NOT NULL, aggregate_revision INTEGER NOT NULL,
  prior_state TEXT, state TEXT NOT NULL, command TEXT NOT NULL, occurred_at TEXT NOT NULL,
  entry_sha256 TEXT NOT NULL,
  PRIMARY KEY (thought_id, lifecycle_revision), UNIQUE (thought_id, aggregate_revision)
);
CREATE TABLE refinement_aggregate_commands (
  thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
  aggregate_revision INTEGER NOT NULL,
  command_kind TEXT NOT NULL,
  prior_working_revision INTEGER NOT NULL,
  next_working_revision INTEGER NOT NULL,
  prior_lifecycle_revision INTEGER NOT NULL,
  next_lifecycle_revision INTEGER NOT NULL,
  prior_attachment_revision INTEGER NOT NULL,
  next_attachment_revision INTEGER NOT NULL,
  canonical_sha256 TEXT NOT NULL,
  lifecycle_sha256 TEXT,
  accepted_at TEXT NOT NULL,
  PRIMARY KEY (thought_id, aggregate_revision)
);
```

Input is strict-UTF-8 encoded once, hashed with SHA-256, and never normalised,
regenerated, or updated. `raw_utf8` is returned only by an authorized
thought/original-cue DTO. The revision table is immutable history of one Note,
not a competing mutable Note; it preserves frozen working text for later Ask and
proposal slices. HS-141-01 writes `attachment_revision = 0` only; HS-141-05
owns attachment child records and must not install generic context JSON now.

Each lifecycle row has one canonical, hashable representation: UTF-8 bytes of
RFC 8785 canonical JSON with every key present — `thought_id`,
`lifecycle_revision`, `aggregate_revision`, `prior_state` (explicit `null` for
create), `state`, `command`, and `occurred_at`. `entry_sha256` is SHA-256 of
those exact bytes. No pretty JSON, omitted nullable field, timezone rewrite, or
re-serialization is equivalent. The aggregate command stores that exact hash
when it advances lifecycle and stores `NULL` only for a command that does not
change lifecycle.

There is deliberately no thought status/revision column on `notes`: status must
not look like ordinary Note metadata. Ownership is the unique aggregate
`working_note_id` lookup, exposed by a repository helper to every public writer.

## Circuit-breaker amendment — aggregate lifecycle clock

`working_revision` is a content clock, not a lifecycle clock. Same-content
complete/resume/tombstone cannot converge from it, and timestamps are never an
authority rule. HS-141-01 must add all three independent axis clocks and one
strong aggregate CAS clock now:

* `working_revision` advances only for working-Note changes;
* `lifecycle_revision` advances only for state transitions and has the immutable
  `refinement_lifecycle_revisions` ledger;
* `attachment_revision` advances only for the later typed attachment set; and
* `aggregate_revision` advances **once for every accepted aggregate command**.

Every command CASes `expected_aggregate_revision` and writes
`next_aggregate_revision = expected + 1` atomically. A working edit also checks
its content axis; an attachment command later checks its attachment axis. Thus
an edit, completion, resume, tombstone, or attachment update has one unambiguous
place in aggregate history. `refinement_aggregate_commands` is that one
immutable, ordered history: it includes `create` at aggregate revision 1, then
each `replace_working`, attachment operation, `complete`, `resume`, and
`tombstone`. Each row records the prior/next cursors for every axis, the
canonical aggregate hash (raw identity, working snapshot, lifecycle state, and
attachment cursor), plus the lifecycle-entry hash where applicable. The working
and lifecycle revision tables remain immutable evidence for their own axes;
they are not a second ordering rule. Add both `lifecycle_revision` and
`aggregate_revision` in HS-141-01: lifecycle alone cannot order it against an
edit/attachment, while aggregate alone loses useful axis/history cursors.

## Aggregate state and transitions

`COMPOSING_LOCAL` is browser recovery state only. The conceptual `RAW_DURABLE`
step is inside the creation transaction, so an API client can only observe the
committed `working` aggregate and its visible Note.

| From | Command | To | Condition/effect |
|---|---|---|---|
| absent | create | working, rev 1 | raw, Note, revision 1, Inbox filing, aggregate command 1 (zero→initial cursors) in one transaction |
| working | replace working | working | working rev +1; aggregate command/rev +1 |
| working | complete | completed | lifecycle rev +1; aggregate command/rev +1 |
| completed | explicit resume | working | lifecycle rev +1; aggregate command/rev +1; raw unchanged |
| working/completed | tombstone | tombstoned | lifecycle/aggregate command rev +1; tombstone Note + filing |
| tombstoned | edit/sync/create retry | tombstoned | named terminal conflict; never resurrect/create another Note |

Future refining/review operation state belongs to HS-141-04 records, not this
initial lifecycle enum. This remains compatible with the ruled
`WORKING → COMPLETED_NOTE` transition
([proposal](../../proposals/thought-refinement-spine.md#L132-L165)).

## Atomic creation and idempotency

`RefinementThoughtService.create` uses one `db._connection()` with `BEGIN
IMMEDIATE`. Repositories need `*_in_transaction(conn, …)` helpers so they do
not open nested connections. The connection context commits or rolls back its
whole block ([`holdspeak/db/connection.py:119-139`](../../../../../holdspeak/db/connection.py#L119-L139)); the workbench sync path already uses the
required explicit transaction style
([`holdspeak/services/sync_service.py:610-626`](../../../../../holdspeak/services/sync_service.py#L610-L626)).

1. Validate nonempty raw bytes, source enum/ref, IDs, and canonical Inbox before
   any write. Resolve Inbox from the server seed constant, never browser input.
2. Hash the complete semantic create payload. Same `create_request_id` + same
   digest returns the stored aggregate/Note/revision. A differing digest is
   `409 idempotency_payload_mismatch`; nothing chooses a winner silently.
3. Insert aggregate, ordinary Note, immutable revision 1, create lifecycle
   entry, aggregate command 1, and
   `directory_memberships.primitive_id = 'note:' || working_note_id` together.
   The existing filing map is a single-valued tombstoned relationship
   ([`holdspeak/db/primitives.py:1173-1184`](../../../../../holdspeak/db/primitives.py#L1173-L1184)); no thought-specific drawer map.
4. Commit and return `{thought_id, raw_id, raw_sha256, state, working_note,
   working_revision, attachment_revision}`. No model admission precedes this
   response.

Fault before commit leaves no aggregate, Note, revision, or filing. A response
lost after commit retries step 2 and returns exactly the same IDs. Filing is
organization, never custody: an owner may move/unfile the Note or delete its
directory without changing thought state. A missing/tombstoned filing is a
non-destructive repair condition: the normal read/resume DTO reports
`filing_status: missing`; the later Resume/UI path may offer re-file to Inbox or
another owner-selected directory, but no background process silently moves it.
Only a missing/tombstoned working Note terminalizes a live aggregate. Startup
reconcile marks that aggregate `tombstoned`, atomically and without recreating
anything; it never backfills ordinary existing Notes into thoughts.

## One CAS gate for all Note writers

The current Note repository is unconditional conflict-update
([`holdspeak/db/primitives.py:82-130`](../../../../../holdspeak/db/primitives.py#L82-L130)); `PrimitiveService.update_note` makes an unversioned
read-then-upsert ([`holdspeak/services/primitive_service.py:58-76`](../../../../../holdspeak/services/primitive_service.py#L58-L76)); and the ordinary route
exposes it ([`holdspeak/web/routes/primitives/notes.py:64-81`](../../../../../holdspeak/web/routes/primitives/notes.py#L64-L81)). These are the bypasses to close.

* `RefinementThoughtService.replace_working` is the sole writer for an owned
  Note. In one transaction it requires both `expected_aggregate_revision` and
  `expected_working_revision`, rejects tombstoned **and completed** state,
  conditionally advances both applicable cursors, updates the Note, inserts
  revision `expected + 1`, and appends the matching aggregate command. A
  zero-row CAS is `409 thought_revision_conflict` with `{thought_id,
  expected_aggregate_revision, actual_aggregate_revision,
  actual_lifecycle_revision,
  expected_working_revision, actual_working_revision, current_note}` for
  reload/reapply—never success. A completed thought accepts no generic edit,
  including same-content replacement, until an explicit `resume` wins its
  aggregate CAS.
* The canonical `PrimitiveService` and every route/CLI/MCP adapter reaching it
  resolve ownership first. Ordinary Notes keep present behavior. For an owned
  Note, PUT/delete require `expected_aggregate_revision` plus the applicable
  axis revision (`expected_working_revision` for PUT; lifecycle cursor for a
  terminal delete) and delegate to the same gate; absent/malformed is
  `409 thought_expected_revision_required`. POST/direct upsert with an existing
  owned ID is refused. Raw fields never appear in Note DTOs and no raw mutation
  endpoint exists.
* `NoteRepository.upsert/delete` stay low-level for non-thought Notes only.
  Public use on a resolved owned ID is forbidden by the service contract and
  tests; transaction helpers receive the current connection rather than calling
  public `upsert` recursively.

Owned Note deletion is the aggregate tombstone transition. It tombstones the
Note **and its matching qualified `note:` filing in the same transaction**; that
prevents a deleted thought from retaining a live drawer edge. This does not make
organization custody: moving, unfiling, or deleting a directory while the Note
is live remains non-terminal. Current Note delete is otherwise independent
([`holdspeak/db/primitives.py:158-169`](../../../../../holdspeak/db/primitives.py#L158-L169)). Raw and revision rows remain durable but are not listed as
unfinished. Retry delete is idempotent; retry create with that request ID returns
the terminal aggregate, not a new thought. Physical purge is out of scope.

## API and paired-device boundary

Use a narrow thought DTO/service; do not overload arbitrary Note fields.

`aggregate_revision` and `lifecycle_revision` are mandatory fields in **every**
thought create, read (including original-cue), mutation-success, sync-result,
and thought-conflict DTO. They are not response decoration. Every DTO that
returns the working Note also carries its mandatory `working_revision`; every
attachment-bearing DTO carries mandatory `attachment_revision` (zero is a real
value, not absence). Mutation requests always carry
`expected_aggregate_revision` and the applicable axis expectation:
`expected_working_revision` for working text, `expected_lifecycle_revision` for
complete/resume/tombstone, and later `expected_attachment_revision` for an
attachment operation. Conflict DTOs return every actual cursor relevant to the
attempt plus the mandatory aggregate/lifecycle pair, so reload/reapply needs no
implicit second read. Pre-aggregate validation failures (for example malformed
UTF-8) are not thought DTOs; every 409 that names an existing thought follows
this required cursor contract.

* `POST /api/thoughts`: `{request_id, raw_text, source:{kind,ref?},
  initial_note:{id?,title,body_markdown,tags}}` → committed creation DTO.
  Its response includes `aggregate_revision`, `lifecycle_revision`,
  `working_revision`, and `attachment_revision`; this content is authenticated
  transport, never telemetry/journal/event data.
* `GET /api/thoughts/{id}` and later resume list return state, source/time/hash,
  working Note and all four cursors. `GET /api/thoughts/{id}/original` also
  returns the mandatory aggregate/lifecycle pair with raw bytes/text for the
  later one-tap cue.
* `PATCH /api/thoughts/{id}/working` accepts exact
  `expected_aggregate_revision` and `expected_working_revision`. Generic
  `PUT /api/notes/{id}` accepts those fields only when owned and delegates; its
  delete accepts `expected_aggregate_revision` and
  `expected_lifecycle_revision` before delegating terminalization. Successful
  and conflict responses include the required cursor contract; none is stored
  on `notes`.

Current sync is unsafe: `notes` is mergeable in the registry
([`holdspeak/services/sync_service.py:20-65`](../../../../../holdspeak/services/sync_service.py#L20-L65)), and its merger compares only `last_modified` then calls
repository upsert ([`holdspeak/services/sync_service.py:570-607`](../../../../../holdspeak/services/sync_service.py#L570-L607)). Add a versioned
`refinement_thoughts` bucket/schema and a compound
`merge_refinement_thought_bundle` **before** generic Note merging:

### Compound sync/reconcile rule

A live bundle carries its aggregate expected/next pair, all three axis clocks,
the immutable **aggregate-command ledger** prefix/suffix, referenced working and
lifecycle entries, and the current Note content hash. `create` is command 1; a
normal update has `next_aggregate_revision = expected_aggregate_revision + 1`;
a catch-up bundle supplies a contiguous suffix of commands. The receiver
verifies raw identity, every aggregate command's contiguous key, prior/next axis
cursors, canonical hash, referenced axis-entry hashes, and current Note == the
ledger's declared working snapshot before writing. For each lifecycle-changing
command it also receives the lifecycle entry's canonical UTF-8 bytes (base64 on
the wire) and `entry_sha256`; it rejects a byte sequence that is not the exact
RFC 8785 encoding of the declared fields or whose SHA-256 does not equal both
the lifecycle row and command `lifecycle_sha256`.

A peer with a verified common command prefix fast-forwards the entire missing
suffix in one transaction (for example rev-1 peer receives rev-2 edit then
same-content rev-3 completion). Equal aggregate revision succeeds only for an
exact aggregate fingerprint: command ledger, state/lifecycle, Note snapshot,
and attachment cursor. An altered current snapshot or an altered historical
command is `thought_aggregate_conflict`, never timestamp LWW. A divergent prefix
returns named reload/reconcile. This is the required behavior for equal-content
completion/resume as well as edits.

A tombstone has no content value but carries the terminal aggregate command,
its expected/next aggregate revisions, lifecycle revision/hash, and working Note
ID. It must likewise carry the exact canonical terminal lifecycle entry bytes
and matching hash; the receiver recomputes and verifies both before installing
the high-water fence. Its durable high-water fence rejects delayed live bundles
at lower/equal aggregate revision; no live bundle clears it. Tombstone atomically removes the
Note and current membership. Live move/unfile stays ordinary organization, but a
tombstoned thought rejects all direct or stale membership writes.

* a thought record carries `raw_utf8_b64`, hash/source/time, state, attachment
  revision, current working Note snapshot, `expected_aggregate_revision`,
  `next_aggregate_revision`, all axis cursors, the aggregate-command suffix,
  and immutable referenced axis records (including canonical lifecycle bytes and
  `entry_sha256` for each lifecycle command);
* its matching normal `notes` record remains for cross-surface discovery but is
  consumed by the bundle, not LWW-merged. A record for a locally owned Note
  without the matching bundle and exact expected revision is rejected as
  `409 thought_sync_revision_required`/`thought_revision_conflict`, including
  tombstones, before any write;
* membership is deliberately **outside** aggregate CAS and the aggregate
  fingerprint. A live qualified membership owns its own monotonic version and
  existing organization conflict/LWW rule, so two peers can converge a move or
  unfile at the same aggregate revision without creating an aggregate conflict.
  The bundle may consume/gate only the exactly-correlated membership record while
  applying its own tombstone, preventing a stale generic membership write from
  surviving terminalization. A direct file/unfile of a tombstoned thought is
  rejected; a direct move/unfile of a live thought remains ordinary organization
  and does not mutate the aggregate.
* the bundle creates, edits, or tombstones aggregate+Note atomically. An exact
  retry is acknowledged only when stored immutable revision hash/state match;
  divergent equal/higher revisions return current aggregate for reload/reapply,
  never timestamp arbitration.

This is stricter than regular Note LWW, which pulls Notes and tombstones today
([`holdspeak/services/sync_service.py:684-705`](../../../../../holdspeak/services/sync_service.py#L684-L705)). An older/revisionless peer may read a stale
Note but cannot overwrite it; it gets named conflict and must pull first. Sync
route service errors already pass through the HTTP adapter
([`holdspeak/web/routes/sync.py:38-54`](../../../../../holdspeak/web/routes/sync.py#L38-L54)).

## Concurrency and fault matrix

| Case | Required result |
|---|---|
| same create request/digest, response lost | same thought, Note, filing, and mandatory aggregate/lifecycle/working/attachment cursors; no duplicate |
| same request ID, changed raw/source/initial Note | 409 idempotency mismatch; stored raw unchanged |
| fault before commit, including Inbox failure | zero aggregate, Note, revision, or membership rows |
| two local writers at revision *n* | one commits *n+1*; one named 409 with mandatory aggregate/lifecycle plus applicable actual axis cursors |
| same-content complete/resume | lifecycle/aggregate CAS decides; matching aggregate command replays, divergence conflicts |
| peer at aggregate rev 1, source at rev 3 | verify command-1 prefix then atomically install contiguous commands 2 and 3 plus referenced records |
| equal aggregate revision, altered command/state/note/attachment | `thought_aggregate_conflict`; no timestamp winner |
| generic PUT/POST/delete owned Note without rev | named 409; no state changes |
| create/read/mutation/conflict DTO lacks aggregate or lifecycle cursor | contract/test failure; cursor fields are never optional decoration |
| generic PUT against completed thought | named completed conflict until explicit resume wins aggregate CAS |
| stale/revisionless/divergent inbound thought sync | named 409; no LWW/upsert or false received count |
| exact inbound retry | idempotent success; no duplicate revision row |
| lifecycle command/tombstone has altered canonical bytes, omitted null, or mismatched hash | named sync conflict; no ledger/fence write |
| direct move/unfile/delete-directory of a live thought | organization changes only; aggregate/revision/raw unchanged; missing filing is reported for explicit repair |
| direct file/unfile of a tombstoned thought | named conflict; no organization resurrection |
| live move/unfile at unchanged aggregate revision | membership's own version/LWW rule converges; aggregate CAS/fingerprint unchanged |
| stale membership replay around tombstone | terminal bundle gates it; no organization resurrection |
| sync tombstone versus edit | same CAS; one wins, loser reloads; no resurrection |
| crash after commit before response | retry locates request/change and returns stored result |
| legacy tombstoned/missing working Note at restart | aggregate tombstoned; raw retained; no recreation |

## Migration, reconcile, and exact proofs

Schema reconciliation is additive/idempotent and does not drop/delete data
([`holdspeak/db/reconcile.py:41-65`](../../../../../holdspeak/db/reconcile.py#L41-L65),
[`holdspeak/db/reconcile.py:76-117`](../../../../../holdspeak/db/reconcile.py#L76-L117)). Add the three tables/indexes, repositories, and one idempotent thought
reconcile. Do not alter/backfill existing Notes, FirstWords/browser drafts, or
sync inboxes. Existing Note/directory wire shape stays compatible; add the new
bucket/schema rather than unrecognised thought fields to the established Note
contract.

Required focused tmp-DB tests (never real HOME):

1. `tests/unit/test_refinement_thought_repository.py`: additive reconcile; raw
   byte/hash equality; immutable revision ledger; no existing Note backfill;
   missing/tombstoned legacy working Note reconciliation; move/unfile/delete-
   directory leaves aggregate live and missing filing reports repairable state.
2. `tests/unit/test_refinement_thought_service.py`: transaction fault injection,
   same/different idempotency retry, qualified Inbox filing, two-instance CAS,
   completion/tombstone/restart, completed-edit refusal until resume, and every
   command's aggregate-ledger cursors/hash; required aggregate/lifecycle cursor
   fields on every success and conflict DTO.
3. `tests/unit/test_web_routes_thoughts.py`: DTO/raw boundary, named conflict
   reload payload with mandatory cursors, and no raw update.
4. Extend `tests/unit/test_web_routes_primitives.py`: owned generic PUT/POST/
   DELETE require/delegate expected revision; ordinary CRUD baseline remains.
5. Extend `tests/unit/test_web_routes_sync_primitives.py` and
   `tests/integration/test_primitive_framework_sync.py`: bundle order,
   exact/stale/revisionless/equal-divergent/tombstone sync, contiguous aggregate
   command suffix replay, edit/move/unfile versus tombstone, stale membership
   replay, and proof generic primitive merge never receives an owned Note or
   tombstone-gated bundled membership; reject lifecycle command/tombstone wire
   payloads with noncanonical bytes, omitted `prior_state: null`, or a bad hash.
6. Add two-peer aggregate-clock proofs: same-content complete/resume; rev-1 to
   rev-3 contiguous command suffix; equal-revision altered command/lifecycle/
   Note/attachment; completed generic edit refusal until Resume; tombstone-
   before-live fence; live move/unfile independently converging at one aggregate
   revision; and direct-delete/restart/missing-Note repair producing the same
   lifecycle/membership terminal result. Future attachment mutation must
   increment attachment + aggregate clocks, never working/lifecycle.

## Source anchors checked

* Story requirements: [`story-01-raw-before-ai.md:15-52`](../story-01-raw-before-ai.md#L15-L52).
* Phase ordering/gates/no-external scope: [`current-phase-status.md:60-94`](../current-phase-status.md#L60-L94).
* Note repository: [`holdspeak/db/primitives.py:77-169`](../../../../../holdspeak/db/primitives.py#L77-L169).
* Current CRUD service/route: [`holdspeak/services/primitive_service.py:41-82`](../../../../../holdspeak/services/primitive_service.py#L41-L82), [`holdspeak/web/routes/primitives/notes.py:36-91`](../../../../../holdspeak/web/routes/primitives/notes.py#L36-L91).
* Current sync dispatch: [`holdspeak/services/sync_service.py:570-628`](../../../../../holdspeak/services/sync_service.py#L570-L628), [`holdspeak/services/sync_service.py:795-807`](../../../../../holdspeak/services/sync_service.py#L795-L807), [`holdspeak/services/sync_service.py:952-957`](../../../../../holdspeak/services/sync_service.py#L952-L957).
* Qualified filing map: [`holdspeak/db/schema.py:1158-1169`](../../../../../holdspeak/db/schema.py#L1158-L1169), [`holdspeak/services/primitive_service.py:311-333`](../../../../../holdspeak/services/primitive_service.py#L311-L333).
