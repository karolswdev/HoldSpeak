# HoldSpeak Continuity CF-0 — domain and contract SRS

**Document ID:** `SRS-HS-CONTINUITY-CF0`

**Status:** Draft for owner ratification; normative subordinate specification

**Version:** 1.0-council-review

**Date:** 2026-09-01

**Parent:** [Continuity integrated SRS](CORE_MEMORY_INTEGRATION_SRS.md)

**Authorities:** [Constitution](CONSTITUTION.md), canonical HoldSpeak schemas and
service contracts, then this document. Where this document conflicts with its
parent, the safer requirement applies and the conflict blocks implementation.

## 1. Purpose, completion rule, and boundary

CF-0 turns Continuity from an architectural promise into an implementation-
derivable contract. A team must be able to derive schema migrations, service
interfaces, state-transition tests, adapters, redacted observations, feature
flags, rollback steps, and CF-1 fixtures without inventing product semantics.

CF-0 is complete only when every requirement marked `MUST` below has an owner,
test or inspection method, and retained evidence. A table existing is not
completion. A model demo is not completion. A design document without ratified
retention and product amendments is not authorization to process owner data.

CF-0 SHALL:

1. ratify or explicitly block on the prospective encrypted-and-shreddable
   admitted-material policy;
2. define the canonical Continuity domain and mutations;
3. define a closed, immutable `ContinuityPlan@1` and use receipt;
4. census every canonical source and inference capability;
5. establish content-free observation, migration, and rollback contracts; and
6. support shadow construction without injecting memory into a model request.

CF-0 SHALL NOT run corpus genesis, generate production embeddings, activate a
memory claim, change prompt material, or present Continuity as released.
Isolated disposable contract fixtures MAY exercise every state/command with
fake data; this does not authorize production owner-data activation.

## 2. Requirement vocabulary and verification

`MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` are normative.
Requirement identifiers never change meaning after ratification. Superseded
requirements remain in an amendment ledger.

Verification codes are:

| Code | Meaning |
| --- | --- |
| `T` | automated test |
| `I` | code/schema inspection |
| `D` | owner-visible demonstration |
| `R` | retained, content-free receipt or report |
| `B` | benchmark or fault-injection campaign |
| `A` | owner amendment/ratification |

## 3. Cross-cutting invariants

| ID | Requirement | Verify |
| --- | --- | --- |
| CF0-INV-001 | Canonical source rows and accepted memory versions MUST be authorities; FTS, vectors, graph projections, briefs, and excerpts MUST be rebuildable derivatives. | T,I |
| CF0-INV-002 | Search similarity, repetition, model confidence, and graph degree MUST NOT establish truth, identity, scope, permission, or activation. | T,I |
| CF0-INV-003 | Only an authenticated owner command MAY accept, replace, archive, restore, or remove accepted memory. | T,I |
| CF0-INV-004 | Model/assistant prose MAY originate a proposal but MUST NOT support a factual claim as evidence; tool/connector/third-party material is untrusted evidence only when its authoritative source and taint are preserved. | T,I |
| CF0-INV-005 | Every mutation MUST be atomic, idempotent, compare-and-swap protected where it addresses existing state, and durably receipted. | T,B |
| CF0-INV-006 | Every model invocation for extraction, embedding, reranking, consolidation, or briefing MUST use the existing admission/terminal-receipt law. | T,I |
| CF0-INV-007 | Authorization MUST be decided on canonical metadata before text, chunks, vectors, or graph neighbors are read into a candidate set. | T,I |
| CF0-INV-008 | Removal MUST synchronously make a ref ineligible for compilation and asynchronously purge all derivatives with repairable tombstone evidence. | T,B |
| CF0-INV-009 | No observation, receipt, exception, metric, or analytics event MAY contain source prose, prompts, vectors, typed values, filenames, raw queries, or stable owner-authored labels. | T,I |
| CF0-INV-010 | One inference operation MUST consume at most one frozen `ContinuityPlan`; consumers MUST NOT append undisclosed memory afterward. | T,I |
| CF0-INV-011 | A degraded or omitted layer MUST be named in the plan and receipt; silent fallback is forbidden. | T,R |
| CF0-INV-012 | People and speaker embeddings MUST remain outside Continuity storage and joins unless a future owner-ratified SRS explicitly admits them. | T,I,A |

## 4. Canonical identifiers, time, serialization, and digests

### 4.1 Primitive contracts

- Newly minted Continuity aggregate IDs are a closed lower-case prefix plus UUIDv7, for example
  `mcell_<canonical-uuid>`. Prefixes are: `ccmd`, `mcell`, `mprop`, `mevd`,
  `pless`, `pprop`, `mse`, `mobs`, `mgen`, `mrun`, `egen`, `sjob`, `gedge`,
  `cplan`, `cbrief`, `rbatch`, `fgtop`, and `pmat`. Deterministic observations, edges,
  chunks, proposals, and jobs hash length-prefixed canonical identity parts.
  Existing source, capability, operation, planning, and receipt refs preserve
  their owning domain's ID grammar.
- Timestamps are RFC 3339 UTC with microseconds and a `Z` suffix.
- Revisions are positive, monotonically increasing integers scoped to one
  aggregate. Revision zero means “must be absent” only in command preconditions.
- New Continuity content digests are lower-case hex SHA-256 over the exact bytes
  named by the field. Referenced-domain digests preserve their canonical
  encoding (including `sha256:<hex>` where required) and declare their digest
  type; encodings are never compared interchangeably.
- JSON digests use UTF-8 RFC 8785 JSON Canonicalization Scheme bytes. Floating
  point values are forbidden from canonical command and plan envelopes. Text
  is Unicode NFC; object schemas reject additional properties and impose
  explicit byte/item/depth bounds.
- Enumerations are closed. Unknown values fail closed with `unsupported_revision`.
- Optional fields are omitted, never serialized as ambiguous empty strings.
- Human prose is never used as an identifier.

### 4.2 Composite scope

`ContinuityScope@1` is a closed object:

```text
owner_id: string                    required
project_id: string                  optional
recipe_id: string                   optional
workbench_id: string                optional
```

At least `owner_id` is present. Every non-owner member MUST resolve through its
canonical service and belong to the owner. A claim may bind any explicit
combination. Matching uses conjunctive equality: an invocation is eligible only
when it contains every dimension bound by the claim. Missing dimensions never
act as wildcards. Scope broadening requires a new owner command. Same-key scope
precedence is all-three, Workbench+Recipe, Workbench+Project, Recipe+Project,
Workbench, Recipe, Project, then owner-wide. A same-rank overlapping
disagreement blocks compilation and enters Review; no timestamp tie-break is
permitted.

If Workbench and Recipe are both bound, the Recipe MUST equal the Workbench's
frozen Recipe unless a future explicit cross-Recipe Workbench contract exists.
Syntactic match and Project authorization are independently enforced.

`EgressGrant@1` is `{allowed_boundaries[], allowed_destination_ids[],
allowed_destination_classes[], allow_any_destination, revision, sha256}`.
Boundaries are an unordered closed set `local|private_network|mesh|cloud`, not
a fictional security total order. A route leg satisfies one grant only when
its boundary is listed and every nonempty constraint matches: ID in IDs and
class in classes. Both lists empty denies unless `allow_any_destination=true`;
that flag requires an owner policy and still obeys boundary. The effective
grant enumerates route-registry legs satisfying **every** source, claim,
procedure, request, and policy predicate. Zero legs refuses before text access.
Every primary/fallback leg must be in that enumerated set. Output/proposal/
consolidation grants cannot admit a leg rejected by any input grant.

### 4.3 Claim identity

`claim_key` is SHA-256 over ASCII `holdspeak.claim-key@1`, NUL, the 8-byte
big-endian canonical-JSON length, then canonical `ClaimIdentity@1`:

```text
contract: "holdspeak.continuity.claim-identity@1"
subject: {kind, ref | owner}
predicate: controlled lower-case dotted identifier
qualifiers: sorted array of {name, typed_scalar}
```

Scope, kind, typed value, display wording, evidence, compile mode, confidence,
and time validity are deliberately absent from identity. Qualifiers distinguish claims
only when the predicate schema declares that qualifier identity-bearing.
Unknown predicates enter a `predicate_alias` review proposal but cannot be
accepted. Subject kinds come from a registry allow-list; models may not mint
arbitrary subjects or Person/third-party subjects. Typed values are a bounded
tagged union of `string|integer|decimal|boolean|enum|ref|list`, separately
digested. `integer` is bounded signed 64-bit; `decimal` is a bounded canonical
string matching `-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?` with no exponent, negative
zero, or trailing fractional zero. IEEE floating point never enters identity or
value hashes.

### 4.4 Qualified-reference registry

Before Continuity writes, the central reference registry MUST canonically
represent: `owner`, `project`, `recipe`, `workbench`, `workbench_item`,
`meeting`, `transcript`, `decision`, `decision_record`, `desk_decision`,
`artifact`, `note`, `thread`, `action_item`, `project_item`, `cadence_loop`,
`memory_cell`, `memory_proposal`, `procedure_lesson`, `continuity_plan`,
`continuity_run`, `memory_forget_operation`, `continuity_command`, and
`continuity_receipt`. `memory_forget_operation` maps exactly to `fgtop_*`.
Legacy read aliases include `action|door -> action_item`,
`cadence -> cadence_loop`, and `person -> people`. `agent` MUST NOT alias
Recipe. A persisted-ref census and dual-read/canonical-write migration precede
registry activation; an unknown canonical ref fails closed.

## 5. Logical schema contract

This section is logical and normative. SQLite names MAY receive a stable
prefix during implementation, but field meaning, constraints, and uniqueness
MUST remain exact. All foreign keys are enabled. Domain rows use additive
migrations and application-owned services; direct route writes are forbidden.

### 5.1 Accepted cells and immutable versions

`memory_cells`

| Field | Contract |
| --- | --- |
| `id` | PK, prefixed UUIDv7 |
| `claim_key` | non-null semantic identity SHA-256 |
| `identity_json` | non-null canonical `ClaimIdentity@1` |
| `owner_id` | non-null |
| `project_id`, `recipe_id`, `workbench_id` | nullable scope members |
| `scope_digest`, `generation` | canonical scope digest and positive identity generation |
| `kind` | closed claim-kind enum |
| `compile_mode`, `egress_grant_sha256` | current projections from head version |
| `lifecycle` | `active`, `archived`, `moved`, or `removed` |
| `head_version` | positive integer |
| `revision` | positive aggregate CAS revision |
| `created_at`, `changed_at` | canonical timestamps |

`memory_versions`

| Field | Contract |
| --- | --- |
| `(cell_id, version)` | composite PK; version starts at 1 |
| `value_schema`, `value_sha256`, `display_sha256` | content-free value metadata |
| `kind`, `compile_mode`, `egress_grant_json`, `scope_digest` | historical accepted configuration |
| `provenance_kind` | `owner_authored`, `proposal_accepted`, `owner_correction`, `imported_owner_authored` |
| `recorded_at`, `source_event_at` | system record time and nullable evidence event time |
| `validity_kind` | `timeless`, `bounded`, or `unknown` |
| `valid_from`, `valid_until` | required only for bounded validity; half-open interval |
| `temporal_basis` | `explicit`, `source`, `inferred`, or `unknown` |
| `precision`, `timezone` | closed temporal metadata; timezone nullable only when irrelevant |
| `prior_version` | null for v1; otherwise same-cell `version - 1` |
| `correction_lineage_ref` | nullable immutable receipt ref |
| `value_sha256` | digest of canonical typed value |

Cells are mutable only through the command service. Versions are append-only.
`head_version` MUST resolve to exactly one version. Bounded `valid_until` MUST
exceed `valid_from`. `unknown` is not silently treated as timeless and overlaps
conservatively for conflict detection. The model cannot invent missing bounds.
At most one accepted current value exists per claim key/scope and overlapping
world interval; application validation plus `BEGIN IMMEDIATE`/CAS enforces this
rather than relying on a partial unique index. Correction lineage is acyclic.

`memory_identity_heads` is unique on `(owner_id, claim_key, scope_digest)` and
points to the current cell generation or a removal tombstone. A removed cell is
terminal. Explicit owner re-entry creates a new generation and atomically moves
the head only after removal/Forget policy permits it; historical rows remain.

World validity and record acceptance are separate. Append-only
`memory_version_transitions` records predecessor, successor, acceptance record
time, and successor world-effective time. At `(record_as_of, world_as_of)`, use
only transitions accepted by `record_as_of`; a predecessor ends at the earlier
of its asserted `valid_until` or successor effective time. Future successors do
not hide their predecessor early. Zero candidates means absence; more than one
is `memory_interval_corrupt` and compilation refuses. Precision is exactly
`instant|day|month|year|unknown`; bounded UTC time preserves source IANA
timezone, while timezone is null only for timeless/unknown source time.

Required indexes: lifecycle/scope/compile mode; claim key; changed time; and
predicate/scope. No index may contain `display_text` outside the authorized FTS
derivative.

`memory_version_values` contains `(cell_id, version)`, mandatory private-
envelope ref/digest, and no plaintext. The decrypted closed payload contains
canonical predicate-validated `typed_value_json` and owner-facing
`display_text`. It is immutable while present but purgeable/key-shreddable on
removal/Forget; the version metadata and hashes survive. Effective selection ends a version at the earlier of its
asserted `valid_until` or the world-effective time in its accepted
`memory_version_transition`. The transition record is the sole supersession
authority; successor `valid_from` is descriptive validity and MUST equal the
transition effective time when bounded. Timeless/unknown successors require an
explicit transition effective time. Future versions do not compile early.
More than one effective version is `memory_interval_corrupt`; zero means absence.

### 5.2 Proposals and evidence

`memory_proposals` contains `id`, `owner_id`, `operation`, content-free proposed
identity/value digests, target cell/revision when replacing, compile and
egress suggestions, `state`, `reason_codes_json`, `input_manifest_sha256`,
`proposal_fingerprint`,
`expires_at`, `created_at`, `decided_at`, and `revision`.

States are `pending`, `accepted`, `rejected`, `dismissed`, and `expired`.
Uniqueness is `(owner_id, proposal_fingerprint)` for non-expired proposals. A
proposal manifest freezes extractor capability/revision, model assignment,
destination, source revisions/digests, policy revision, predicate schema,
prompt-template digest, and output digest without retaining prompt prose.
Candidate identity/value/rendering lives in purgeable encrypted
`memory_proposal_payloads`. Proposal states additionally include `superseded`;
operations are `add|replace|temporal_successor|change_scope|change_mode|archive|review`.
Rejection suppresses the exact `(claim_key, scope_digest, value_digest,
operation, evidence-root digest)` until an explicit expiry/policy revision;
dismissal suppresses nothing. One input manifest may publish many proposals.

`memory_evidence` contains `id`, exactly one of `(proposal_id, cell_id,
cell_version)`, canonical `source_kind`, `source_id`, `source_revision`,
`source_digest`, optional byte span, `root_event_id`, `origin`, `assertor_class`,
privacy/egress classes, role `supports|contradicts|temporal|scope`, encrypted
excerpt-envelope ref/digest, and `captured_at`. Spans are half-open UTF-8 byte
offsets and MUST validate against the frozen source revision. The bounded
encrypted excerpt preserves reviewability after a source edit and is shredded
when its source lineage is forgotten. Evidence never grants scope or egress
eligibility.

### 5.3 Transactional outbox and normalized observations

The mutation outbox and rich source observation are deliberately separate.
`continuity_source_events` is the minimal content-free atomic outbox:
monotonic `INTEGER PRIMARY KEY AUTOINCREMENT event_seq`, unique event ID,
canonical source ref, operation `upsert|delete|membership|privacy|backfill`,
mutation origin, revision hint, root event, and created time. Canonical writes
append it in the same transaction, using revisioned table-specific triggers
where repositories cannot share the caller connection. Triggers contain no
source prose and cover content plus Project/Knowledge membership, visibility,
privacy, finalization/status, and deletion changes.

`SourceCaptureRegistry@1` has exactly one row per canonical table/mutation,
declaring capture owner `service|trigger`, revision/hash, canonical parent-ref
resolver, and enabled state. Both paths for one mutation are forbidden by CI
and migration Doctor. Event ID deterministically hashes capture registry
revision, transaction mutation identity, canonical parent ref, operation, and
native revision hint, so retry deduplicates without hiding distinct mutations.

`continuity_source_observations` is the adapter-normalized post-commit record:
observation ID, event sequence, adapter ID/revision, source ref, state
`current|deleted|ineligible|transient`, normalized revision/digest, origin,
assertor, privacy, allowed destinations/boundaries, occurred time, scope-
manifest digest, observation digest, and independent uses
`episodic|brief|core_candidate|procedure_candidate|graph`. Source membership is
normalized into a filterable child table rather than JSON alone. Uniqueness is
adapter/revision/ref/source-revision/observation digest. It contains no prose.

Origin/taint is a monotonic lattice:
`owner_explicit > owner_authored > owner_adopted > canonical_system >
assistant_generated > tool_external > connector_external > web_external >
unknown`. Copying external content into an owner container does not erase its
root-event taint when instrumented import/quote lineage exists. Untraceable
paste/manual origin is honestly `unknown` for automatic extraction, not inferred
owner authorship from its container. Promotion requires an explicit owner-
adoption receipt, and the trust meet selects the least-trusted root. Automatic
claim extraction is limited to eligible owner-explicit/authored/adopted
material. Every source freezes an `EgressGrant@1`; mixed evidence uses the
exact all-input leg predicate.

V1 `continuity_source_cursors` has one global ordered cursor per adapter—no
Project/scope partition, so every multi-membership event has one position. It contains
`through_seq`, revision, lease token/epoch/expiry, state
`idle|leased|degraded`, safe last error, reconciliation digest, and changed
time. `SourceEventDisposition@1` is `published|deleted|ineligible|
skipped_terminal|retryable`; only the first four are terminal. Publication of
observations/dispositions and cursor advance commits atomically over the
greatest contiguous terminal sequence. `retryable` blocks advance. Terminal
skips retain safe reason/replay tokens and can be explicitly re-enqueued as new
events; no interval silently wedges or disappears.

`ContinuitySourceAdapter@1` exposes identity/schema hash, supported ref types,
paged inventory, `observe(ref, through_seq, snapshot)`, revision/digest-checked
hydrate, revisioned chunking, and typed graph projections. Source revision is a
closed adapter token, not assumed to be an integer: it canonicalizes native
integer, timestamp, content digest, or multi-table manifest revisions. A
bounded inventory/live handoff enables capture, records start sequence,
inventories deterministic pages, processes later events, freezes catch-up,
revalidates current digests/memberships, and activates only stable coverage.
Long blocking snapshots and startup model/corpus work are forbidden.

### 5.4 Procedures, graph, and semantic-generation foundations

CF-0 creates contracts, not production projections:

- `procedure_lessons`: domain, adapter revision, typed trigger/payload refs,
  scope, lifecycle, head version, authority and receipt refs.
- `procedure_proposals`: same proposal lifecycle as claims and a domain-owned
  payload schema. Dictation correction remains authoritative in its existing
  store and is referenced, not copied.
- `memory_graph_edges`: source and target canonical refs, edge kind, trust class
  `authoritative|accepted|derived`, direction flag, endpoint revisions/digests,
  scope/privacy/destination projection, validity, provenance/source-event/
  generation, lifecycle `active|invalidated`, and identity unique over
  endpoints/kind/trust/provenance/generation. Derived edges require a generation;
  accepted edges require accepted memory/procedure provenance; authoritative
  edges require a canonical relationship. Derived edges never establish truth
  or authorization.
- `embedding_generations`: immutable profile contract, model/tokenizer/runtime
  artifact digests, license decision ref, dimensions, element type, distance,
  pooling, normalization, templates, max tokens, chunker revision, corpus
  manifest, state, validation evidence, and activation/retirement times.

Generation states are `declared`, `building`, `validating`, `active`, `retired`,
`failed`, `purging`, and `purged`. Exactly one generation per vector family MAY
be active. Activation
is an atomic compare-and-swap after validation. Failed or retired generations
are never queried. CF-0 MAY insert `declared` test fixtures only.

Semantic jobs transition `queued -> leased -> completed|stale|refused|failed`.
An expired lease returns to queued only with a higher lease epoch; publication
after lease loss is refused. Genesis and maintenance rows store command/hash,
state/revision, frozen policy/adapter registry, inventory/catch-up/activation
cursors, corpus manifest, assignment/operation/receipt refs, lease epoch,
content-free counts, pause target, terminal code, and timestamps.

`continuity_briefs` has prefixed ID, positive revision, canonical scope/digest,
`as_of`, source-journal through-sequence, computed/expiry times, run and
generation refs, state `building|ready|stale|partial|blocked|removed`, manifest
digest, and encrypted atomic statement-set ref. Every ordered item has stable
item ID/ordinal, kind `where_left_off|moving|changed|language`, assertion class
`observed|accepted|derived`, freshness basis/time, purgeable body/digest, resume
verb/ref when canonical, and at least one exact evidence row. Brief publication
atomically swaps the scope head under CAS. Any evidence revision, scope/privacy
epoch, accepted-memory revision, or policy change marks the head stale before
read; stale items are labelled/withheld by policy and queue rebuild. `memory_review_batches` freezes ordered proposal IDs/revisions,
scope, run, limit, and lifecycle. Accept-selected enumerates each reviewed
proposal revision; batch membership grants no authority over later additions.
`memory_review_drafts` is owner/hub-shared and keyed by batch/owner, with CAS
revision, ordered selected proposal revisions, encrypted edited payload refs,
expanded evidence refs, posture/filter/scroll/selection cursor, updated time,
and client instance for conflict display. Window/device caches are projections;
they are not authority. Concurrent stale saves return `stale_revision` and
never overwrite another glass.

Direct owner-authored Remember MAY use its authenticated continuity command and
receipt as provenance evidence without a canonical source span. It remains
`owner_authored`; later model proposal extraction still requires eligible
source evidence under the normal contract.

### 5.5 Policy, command ledger, plans, and use lineage

- `continuity_policies`: append-only policy revisions containing layer budgets,
  source/capability eligibility, scope law, destination law, retention class,
  model-generation refs, and canonical digest.
- `continuity_commands`: unique `command_id`, actor/owner, operation,
  server-derived `request_sha256`, terminal state `completed|refused`, aggregate
  refs, result or error envelope digest, created/completed timestamps. A
  synchronous command never leaves pending; mutation and result commit together.
  Private result bytes follow the ratified shreddable retention contract.
- `continuity_plans`: immutable content-free `ContinuityPlan@1` descriptor,
  mandatory shreddable encrypted-material ref for every content-bearing byte,
  public manifest, digest, policy/capability refs, and creation time. No update
  is permitted.
- `continuity_usage_refs`: operation/plan plus layer, canonical supplied ref and
  revision, disposition `included|selected|shadowed|omitted|procedural_applied`,
  reason, rank ordinal, byte/token accounting, and correction lineage. It
  contains no copied prose. HoldSpeak claims that material was supplied,
  selected, omitted, shadowed, or a deterministic procedure applied—not that
  prompt text causally influenced generated tokens.

### 5.6 Admitted-material vault and lineage

The new Continuity path MUST replace content-bearing plaintext adoption fields
with a split header/vault design:

- `inference_material_headers`: immutable planning/operation/capability/
  contract revisions, input/output digests, budgets, retention class, crypto
  revision, and timestamps; no prose;
- `inference_private_envelopes`: envelope/operation IDs, direction
  `input|output|evidence_excerpt|projection`, AES-256-GCM ciphertext, unique
  `(native key ID, 96-bit nonce)`, AAD digest, plaintext digest, and format revision;
- `inference_material_lineage`: immutable operation/envelope to source kind,
  ref, revision/digest, optional memory/procedure version, and lineage role;
- `inference_key_shred_events`: immutable key/command/hash, lineage digest,
  request/completion timestamps, and typed result.
- `inference_key_intents`: operation/key ID, state
  `reserved|key_created|active|destroying|destroyed|orphaned`, revision,
  envelope count, and safe error/receipt refs.

Associated data binds envelope ID, operation ID, direction, capability,
contract/revision, plaintext digest, and crypto revision. Encryption happens
before SQLite receives content. A native keystore holds a per-operation data-
encryption key; production has no file, environment, or plaintext fallback.
One affected lineage ref shreds the entire operation key. Decryption checks
shred state before key lookup and is allowed only for the admitted execution
lease or explicit owner audit/replay policy. Python memory zeroization is
best-effort and MUST NOT be claimed as guaranteed.

Content-free receipt attestations MAY remain immutable plaintext. Existing
plaintext adoption and attempt-result tables are `legacy_plaintext`, excluded
from Strong Forget. Before new writes activate, every SQL dependency on their
payload JSON MUST move to indexed content-free correlation fields.

`memory_forget_operations` is the asynchronous saga authority: prefixed ID,
initiating command, scope-manifest/key-set digests, barrier revision, total/
destroyed/failed/excluded counts, lifecycle
`requested|access_barrier_installed|key_destroying|completed|incomplete`, CAS revision,
disclosed exclusions, safe last error, and terminal receipt ref. The initiating
synchronous command returns `saga_started` plus this ref, never owner-facing
Forget success. Status/retry commands read/CAS the saga; only `completed` after
all in-scope native deletion receipts renders Forget complete.

## 6. Aggregate state machines

Only transitions listed here are legal. Every transition emits a command
receipt and source event when applicable.
Cell/proposal decisions and genesis pause/resume/cancel/rebuild require the
authenticated owner; proposal expiry is the only clock actor; maintenance run
transitions require an unrevoked standing-learning grant and leased system
principal; semantic jobs require the current lease epoch; key transitions are
owned only by `PrivateMaterialService` under an admitted Forget/retention
operation. Every transition CASes the expected revision and its exhaustive
transition-table test names actor, event, receipt, and terminal behavior.

### 6.1 Accepted cell

```text
absent --remember/accept--> active
active --replace----------> active (new immutable version)
active --change-mode------> active (new immutable configuration version)
active --archive----------> archived
archived --restore--------> active
active|archived --remove--> removed
active --change-scope-----> moved + new active target cell
removed ------------------> terminal
moved --------------------> terminal
```

V1 scope change has no merge/replace disposition. In one CAS transaction it
requires an absent destination identity head, creates a new target-scope cell
generation/v1 with re-encrypted value/configuration and move lineage, marks the
source `moved` with `moved_to_ref`, tombstones/moves the old head, creates the
destination head, emits events, and returns both changed refs. A destination
head of any lifecycle returns `claim_conflict`; the owner resolves it with
separate explicit commands. Historical versions retain their exact scope digest.

Removal/moved are terminal; restoring removed material requires a new cell generation
under the same semantic key only after the removal barrier permits re-entry. An active claim-
key conflict returns `claim_conflict`; it does not auto-merge.

### 6.2 Proposal

```text
pending --accept--> accepted
pending --reject--> rejected
pending --dismiss--> dismissed
pending --clock sweep--> expired
pending --newer manifest--> superseded
```

All terminal states are immutable. Acceptance atomically creates/replaces a
cell and finalizes the proposal. Rejection records “do not propose this exact
fingerprint/suppression key during its policy window”; dismissal does not.
Expiry is not owner rejection.

### 6.3 Genesis and maintenance run

```text
requested -> inventorying -> indexing -> extracting -> catching_up -> validating -> publishing -> completed
any running state -> paused_owner|paused_system -> prior running state
any nonterminal -> cancelling -> purging_incomplete -> cancelled
any nonterminal -> failed_retryable|failed_terminal
failed_retryable -> requested (new run referencing predecessor)
```

Runs freeze source range, policy, model assignments, adapter revisions, and
budgets before `inventorying`. `completed` requires a published cursor and terminal
receipts. A retry is a new run; terminal rows are immutable.

### 6.4 Plan

A plan has no mutable lifecycle. `build` either returns one purpose-typed
immutable artifact or a typed failure. Preview/shadow are non-admitted and
non-dispatchable; execution alone may bind to admission. Adoption and inference
receipts reference the plan digest. Replanning creates a different plan ID.

### 6.5 Forget operation

```text
requested -> access_barrier_installed -> key_destroying
key_destroying -> completed | incomplete
incomplete -> key_destroying (explicit retry, same command lineage)
```

Forget success requires a terminal native deletion result for every in-scope
key and zero eligible live derivatives. Partial provider/backup/legacy limits
are separate disclosed exclusions, not silently counted as completed local
keys. Completed is terminal; incomplete remains barred from reads.

## 7. Command and result contracts

### 7.1 Common envelope

The caller submits closed `ContinuityCommandRequest@1` with no principal,
owner, session, authority, or timestamp:

```text
contract: "holdspeak.continuity.command-request@1"
command_id: ccmd_<UUIDv7>
operation: closed operation enum
requested_scope: {project_id?, recipe_id?, workbench_id?}
preconditions: ordered discriminated union of
  ref_revision {ref, revision}
  identity_absent {claim_key, scope_digest, expected_head_generation?}
body: operation-specific object
request_sha256: optional caller comparison; server derives authority digest
```

The edge authenticates the principal. The service injects stable hub-local
owner, authenticated principal/authority basis, authorized canonical scope, and
server time into private `ContinuityCommandEnvelope@1`; callers supply none of
them. The server derives the request hash over contract, operation, requested
scope, complete ordered preconditions, and body, excluding command ID/hash and
all server-derived authority/time. A caller hash is comparison-only. The same
`command_id` and hash returns the exact stored result without a second
effect. The same ID with different bytes returns `idempotency_conflict`.

`ContinuityCommandResult@1` contains command ID, operation, outcome
`applied|replayed|rejected`, ordered `changed_refs[{ref,old_revision?,
new_revision}]`, receipt ref,
result digest, and completion time. It contains owner-facing rendering only in
the private application response, never observations.

`MemoryForgetStartResult@1` is an operation-specific body under common outcome
`applied|replayed`: `{saga_state:"saga_started", forget_operation_ref:
"fgtop_<UUIDv7>", access_barrier_revision, key_count, excluded_count}`. It is
not Forget success. Only saga state `completed` and its terminal receipt render
owner-facing Forget completion.

### 7.2 Operations

| Operation | Required body | Preconditions/effect |
| --- | --- | --- |
| `memory.remember` | complete identity, typed value, compile/egress, optional existing evidence refs | `expected.absent`; source-less owner command atomically mints command/receipt provenance; creates v1 |
| `memory.replace` | cell ID, typed value, temporal/correction reason, optional existing evidence refs | exact revision; owner correction atomically links receipt provenance; appends version |
| `memory.change_mode` | cell ID, compile mode | exact revision; appends historical configuration version |
| `memory.change_scope` | active cell ID/revision, new scope, `destination_expected:absent` | atomically creates target cell generation/v1, marks source `moved`, moves heads; destination collision refuses |
| `memory.archive` | cell ID, reason code | active at exact revision |
| `memory.restore` | cell ID | archived at exact revision and no active claim conflict |
| `memory.remove` | cell ID, removal class | active/archived; installs synchronous eligibility barrier |
| `memory.forget` | source/cell/operation lineage scope, disclosed exclusions | installs barrier and returns `saga_started`; saga alone may later report success |
| `memory.forget.status|retry` | forget-operation ID/revision | content-free status or resume incomplete key destruction |
| `proposal.accept` | proposal ID, optional owner edits | pending at exact revision; atomically applies cell mutation |
| `proposal.reject` | proposal ID, reason code | pending at exact revision; suppress exact fingerprint-derived key for policy window |
| `proposal.dismiss` | proposal ID | pending at exact revision |
| `continuity.genesis.start` | frozen source range, policy revision, budget | amendment and capability gates satisfied |
| `continuity.genesis.pause|resume|cancel` | run ID and reason | legal run transition |
| `continuity.genesis.rebuild` | prior run, new preflight/policy revision | creates a new run; never mutates prior generation |
| `continuity.learning.enable|disable` | policy revision and cadence | explicit standing authorization only |
| `continuity.plan.preview` | operation/capability/scope/destination/material budget | builds private non-injecting plan and disclosure |
| `review.draft.save|discard` | batch ID/revision, selected proposal revisions, encrypted edits, UI cursor | owner-scoped hub CAS; no acceptance authority |
| `proof.status|list|purge|export_preview|export` | retention range/filter/export-preview digest as applicable | local owner-only proof-ledger service |

### 7.3 Stable failures

Errors use `ContinuityError@1` with code, safe message key, retryability,
command ID, and content-free details. Closed codes:

`invalid_contract`, `unsupported_revision`, `validation_failed`,
`authentication_required`, `owner_mismatch`, `scope_ineligible`,
`source_ineligible`, `destination_ineligible`, `egress_ineligible`,
`privacy_ineligible`, `retention_unavailable`, `amendment_required`,
`unknown_aggregate`, `wrong_lifecycle`, `stale_revision`,
`idempotency_conflict`, `claim_conflict`, `predicate_unknown`,
`memory_interval_corrupt`, `continuity_plan_stale`,
`evidence_stale`, `source_changed`, `policy_changed`, `budget_exhausted`,
`generation_not_ready`, `assignment_incompatible`, `model_unavailable`,
`invalid_model_output`, `integrity_failure`, and `temporarily_degraded`.

Specialized closed families additionally include:

- material: `material_encryption_failed`, `material_key_store_unavailable`,
  `material_key_unavailable`, `material_integrity_failed`, `material_shredded`,
  `material_decryption_forbidden`, `material_crypto_revision_unsupported`,
  `material_lineage_missing`, `forget_scope_incomplete`,
  `legacy_plaintext_retention`, `backup_retention_uncontrolled`, and
  `provider_retention_uncontrolled`;
- representation: `representation_capability_unassigned`,
  `representation_route_not_local`, `representation_generation_mismatch`,
  `representation_shape_invalid`, `representation_nonfinite`,
  `representation_norm_invalid`, `representation_output_count_mismatch`, and
  `representation_publication_conflict`;
- claim/proposal: `claim_subject_ineligible`, `claim_key_mismatch`,
  `claim_interval_overlap`, `claim_evidence_unavailable`,
  `claim_third_party_forbidden`, `proposal_source_not_in_manifest`,
  `proposal_target_not_in_manifest`, `proposal_taint_downgrade`,
  `proposal_output_limit`, `proposal_duplicate`, and `proposal_target_stale`;
- derivative: `semantic_generation_mixed`, `semantic_source_stale`,
  `semantic_scope_stale`, `semantic_privacy_stale`,
  `derived_data_lineage_missing`, `graph_edge_untrusted`, and
  `graph_path_ineligible`.

Only `temporarily_degraded`, `model_unavailable`, and an explicitly classified
storage-busy case are automatically retryable. Validation, authority, privacy,
and conflict errors are never retried without changed input or policy.

The error envelope is exactly `{contract, code, stage, retryable, operation_id,
receipt_id?, safe_context, remediation}`. `safe_context` is a per-code closed
allow-list of IDs, digests, enums, and counts—not generic details. Article-XI
mapping is normative: policy/preflight rejection before dispatch is `refused`;
attempted computation, authentication/integrity failure, invalid model output,
or failed publication is `failed` with zero publication; `indeterminate` is
reserved for genuinely unknown external physical/effect outcomes; a valid
lexical/authoritative result with unavailable semantic lane is `succeeded` plus
named `semantic_degraded`. A stale CAS retries only with a new frozen manifest.
CI lints every backticked service-returned failure/status against the appropriate
closed registry; prose cannot silently mint a new error code.

## 8. `ContinuityPlan@1` — the complete prompt waist

### 8.1 Closed private artifact

```text
contract: "holdspeak.continuity.plan@1"
plan_id: cplan_<UUIDv7>
purpose: preview | shadow | execution
planning_reference: string
operation_id: op_<kernel-id>             required only for execution
parent_run_ref: string                   optional; never operation identity
application_invocation_ref: string       optional; never authority
created_at: timestamp
principal: {owner_id, session_ref}
capability: {id, revision, schema_sha256}
assignment: {profile_id, profile_revision, route_plan_id, route_plan_sha256,
             ordered_legs:[{destination_id, destination_class, boundary,
                            deployment_revision}]}
scope: ContinuityScope@1
working_scope: {thread_id?}
policy: {revision, sha256}
generations: [{family, generation_id, profile_sha256}]
input: {request_digest, requested_context_tokens, reserved_output_tokens}
layers: [ContinuityLayer@1]
omissions: [{layer, reason, eligible_count, omitted_count}]
accounting: {context_limit, available_tokens, used_tokens, used_utf8_bytes,
             tokenizer_ref, tokenizer_revision}
integrity: {canonical_sha256}
```

Layer order is fixed: `constitutional`, `capability`, `accepted_core_always`,
`accepted_core_contextual`, `working`, `episodic`, `procedural`, `request`.
Every `ContinuityLayer@1` contains layer ID/revision, ordered item refs,
canonical ref revisions/digests, rendered UTF-8 byte length, exact token count,
budget, disposition, and optional omission reason. Only the private artifact
contains rendered text; public descriptors/manifests contain digests and counts.
The descriptor additionally freezes route-plan ID/digest, ordered destination
and boundary/deployment revisions, principal authority-basis digest/rights
revision, query digest, material-slot IDs, template revision, per-layer policy,
generation revisions, serialized-request digest, and encrypted-material ref.

Closed omission reasons are `not_authorized`, `not_applicable`, `no_candidates`,
`privacy_fence`, `egress_fence`, `scope_fence`, `time_fence`, `budget_fence`,
`generation_unavailable`, `source_unavailable`, `integrity_failure`, and
`feature_disabled`. `integrity_failure` blocks dispatch; it is not a fallback.

### 8.2 Budget and freeze law

The planner MUST use the exact tokenizer revision of the assigned model. Token
budgets are integers and cannot be estimated from characters at dispatch.
Constitutional/capability material and reserved output are admitted first.
Layer budgets are revisioned policy. Within a layer, deterministic ordering is
score/rule, event time, canonical kind, then ref. Items are indivisible unless
the source adapter declares a revisioned, source-addressable chunk boundary.

After the digest is computed, payload, target, authority, scope, ordering,
rendering, assignment, destination, and budgets are immutable. Any difference
requires a new operation and plan. The inference adoption record MUST reference
the plan ID/digest and MUST prove its exact material snapshot digest derives
from that plan. Preview plans are explicitly non-admitted and can never be
dispatched.

Preview/shadow plans use only `planning_reference`. For execution, the kernel
first mints its exact child `op_*` operation; a broker-owned pre-dispatch
material callback then builds and immutably binds the execution plan before
adoption material freezes. `operation_id` always means that kernel child—not a
genesis/maintenance run or application invocation. Existing consumers cannot
mint or substitute it. Later binding of preview/shadow is forbidden.

Immediately before adoption commits, the service revalidates accepted-cell,
procedure, source, policy, route, working-state, and destination revisions in
the same `BEGIN IMMEDIATE` transaction that binds plan, encrypted material,
operation, and route evidence. Mismatch returns `continuity_plan_stale` and
requires replanning. Dispatch reconstructs solely from persisted plan/material;
it never reruns retrieval or formatting.

### 8.3 Use receipt and correction lineage

`ContinuityReceipt@1` contains operation/plan IDs and digests, terminal outcome,
capability/assignment/policy revisions, included and omitted counts by layer,
supplied canonical refs/revisions, timing buckets, degraded reasons, and
owner-visible “why this was used” refs. It contains no prompt or source prose.

When the owner corrects a supplied cell, the new command receipt references
the prior usage ref. This increases review priority only; it never rewrites a
historical immutable inference record or increments a truth score.

## 9. Transaction, concurrency, and crash law

| ID | Required protocol | Verify |
| --- | --- | --- |
| CF0-TXN-001 | Canonical mutation, aggregate revision, command result, and source-journal event MUST commit in one SQLite transaction. | T,B |
| CF0-TXN-002 | Command ledger insertion claims `command_id` before effect; concurrent identical commands converge on one stored result. | T,B |
| CF0-TXN-003 | Replace/archive/restore/remove and proposal decisions MUST use SQL CAS on expected lifecycle and revision; zero changed rows returns a typed conflict. | T,B |
| CF0-TXN-004 | Proposal acceptance MUST atomically finalize proposal and create/replace the cell; neither half may survive a crash. | T,B |
| CF0-TXN-005 | Plan build MUST read from one stable SQLite snapshot, persist private artifact and public manifest atomically, then become eligible for adoption. | T,B |
| CF0-TXN-006 | Embedding generation activation MUST atomically retire the prior active generation and activate one validated generation. | T,B |
| CF0-TXN-007 | Source cursor advancement MUST be atomic with the journal batch and publish receipt. | T,B |
| CF0-TXN-008 | Removal MUST write a canonical tombstone and exclusion barrier before returning success; derivative purge is idempotent queued work. | T,B |
| CF0-TXN-009 | Startup reconciliation MUST resume/quarantine abandoned run leases, publication states, derivative jobs, and key intents without duplicating effects; synchronous commands have no pending state. | T,B |
| CF0-TXN-010 | Corruption, digest mismatch, or impossible state MUST fail closed, preserve evidence, and expose repair—not silently rebuild over the discrepancy. | T,B,D |

SQLite uses bounded busy retries only before an effect is known to commit. A
client timeout after commit is resolved by replaying `command_id`, never by
inventing a second command. Background jobs lease bounded ranges; lease expiry
allows idempotent resumption from the last published cursor.

## 10. Canonical source adapter census

Each adapter MUST emit revision/digest, origin, privacy, egress, event time,
owner and projected scope without copying prose into the journal. `Eligible`
means eligible for authorized lexical/semantic retrieval; proposal generation
has its own column. Every row defaults to deny when required metadata is absent.

| Canonical family | Retrieval | Proposals | Scope/revision contract | Notes |
| --- | --- | --- | --- | --- |
| Decisions | yes | yes | decision revision + Project memberships | owner-authored authority; supersession preserved |
| Notes | yes | yes | note revision + Project memberships | drafts/private classes obey source policy |
| Artifacts | yes | conditional | artifact digest/version + Project | generated output requires explicit adoption |
| Meeting segments | yes | conditional | meeting + segment revision + Project | attendee/leadership/private policy applied before text |
| Threads/user parts | yes | conditional | thread/message/part revision + Project | owner user text eligible; assistant/tool parts evidence-only by default |
| Actions/Commitments | yes | yes | canonical action revision + Project | status/event time is structured authority |
| Project items/documents | yes | yes | project item revision | must remain inside exact Project scope |
| Workbench results | yes | conditional | workbench/item/run revision | only adopted successful results; run advice stays procedural |
| Cadence | yes | conditional | loop/action/evidence revision + Project | nudges/drafts are not facts |
| Knowledge and `.hs/` | yes | conditional | content digest + membership revision | owner-authored; path/label excluded from telemetry |
| Recipe definitions | yes | yes | recipe revision | procedural scope; never grants tool authority |
| Dictation corrections | procedural | no generic claim | correction revision + target profile | reference existing authority; do not duplicate text |
| Corpus files/imports | conditional | conditional | import manifest + content digest | quarantine until origin/privacy/license known |
| People | no | no | none | separate encrypted third-party domain |
| Speaker embeddings | no | no | none | biometric-adjacent and out of scope |
| Assistant/model prose | no factual evidence | proposal-origin only | producing operation/receipt | untrusted; eligible source inputs/owner command provide evidence |
| Tool/connector output | evidence-only | conditional | tool receipt + origin/authority | untrusted external content; injection defenses required |
| Secrets/credentials/kernel material | no | no | none | forbidden before any model or index work |

Every adapter owns golden fixtures for create, update, deletion, privacy change,
scope change, stale revision, empty content, malformed content, and removal.
CF-1 cannot begin for a row until its fixtures and reconciliation law pass.

## 11. Inference capability policy census

The implementation SHALL generate this census from
`holdspeak/inference_capabilities.py` and fail CI on uncategorized registry
changes. `ContinuityCapabilityPolicy@1` is keyed by exact capability ID/revision
and freezes independently: `core_policy` plus modes; `episodic_policy`;
`procedural_policy` plus adapter IDs; `working_policy`; `memory_action_use`;
allowed scope dimensions; exact layer/token budgets; query source;
explicit-grounding interaction; destination rule; and parent-inheritance rule.
Each field is `none|bounded` with explicit closed contents—`full` is display
shorthand only and cannot future-expand. `internal-parent` names and verifies
the exact already-frozen parent plan and never replans. Unknown/plugin/future
defaults are an explicit all-none policy, not absence.

The table's `full shadow` labels therefore mean a revisioned bounded policy
whose current explicit contents include every presently eligible layer; they
are not wildcard schema values.

| Capability family/IDs | CF-0 target policy | Constraint |
| --- | --- | --- |
| `ask.answer`, `thought.interview`, `chat.turn` | full shadow | no injection until CF-3 |
| `recipe.run`, `sequence.step`, `workflow.node`, `workbench.item` | full shadow | definition scope plus invocation scope |
| `agent.plan`, `agent.code` | full shadow | memory cannot authorize effects |
| `agent.tool_turn` | none | remains forbidden until tool-turn security gates are separately ratified |
| `speech.rewrite` | bounded: always Core + dictation procedure | exact target profile and strict latency budget |
| `speech.intent_classify`, `speech.target_classify` | none | memory must not alter routing/authority classification |
| `speech.punctuate` | none/future | unavailable until its future capability is ratified |
| `speech.transcribe`, `speech.preload` | none | audio contract only |
| `meeting.live_analysis` | bounded: scope + working + episodic | attendee/privacy fence; live latency priority |
| `meeting.bookmark_label`, `meeting.auto_title`, `meeting.deferred_analysis` | bounded: scope + episodic | no unrelated contextual Core |
| `voice.reference_resolve` | bounded: Workbench scope | entity refs only; no general persona material |
| `project_doc.suggest_update` | full shadow within Project | output is suggestion, never direct mutation |
| `background.rails_summary`, `background.cadence_draft`, `decision.promotion_draft`, `delivery.pr_review_draft` | bounded shadow | exact Project/origin; draft remains untrusted |
| `calendar.snapshot_extract` | none | extraction must reflect only admitted image/request |
| `chat.guardrail` | bounded: policy/working only | no semantic episodic lane |
| `chat.compact` | bounded: thread working memory only | cannot promote compacted prose to accepted truth |
| `internal.*` | internal-parent | never independently builds or broadens a plan |
| `apple.*` future capabilities | none | unavailable until canonical route adoption and a census amendment |
| `meeting.plugin.*` installed capabilities | none by default | each plugin requires explicit revisioned policy and privacy review |
| Coder steering (`ContinuityConsumerDefinition@1`) | full shadow | separate from inference registry; freezes a plan before process input admission |
| `memory.embed` | source payload only | separate typed contract; local by default |
| `memory.rerank` | eligible candidates only | cannot change authorization or identity |
| `memory.claim_extract`, `memory.claim_consolidate` | authorized proposal corpus only | standing learning authorization required |
| `memory.continuity_brief` | eligible source refs only | output is source-backed and non-authoritative |

Shadow construction MUST still enforce destination, privacy, egress, token, and
scope rules. “Not injected” is not permission to expose data to a model.

### 11.1 Service ownership

Application services are `CoreMemoryService`, `ProcedureMemoryService`,
`ContinuityPlanner`, `ContinuityGenesisService`,
`ContinuityMaintenanceService`, `ContinuityRetrievalService`,
`ContinuityBriefService`, `ContinuityHealthService`,
`ContinuityProofService`, and `PrivateMaterialService`. Private infrastructure
is repositories, SourceAdapterRegistry, ContinuityPolicyRegistry,
RepresentationRunner, GraphProjector, and SemanticIndex.

Repositories persist but do not authorize. Services authenticate principal and
scope and own commands. Planner alone composes context. Retrieval/adapters never
activate memory. Model tools are proposal-only. HTTP/MCP/Web/native call
services, not repositories. Existing `MemoryService.search` delegates to
Continuity retrieval; `include_memory` is deprecated in favor of exact policy/
plan. Coder freezes a plan before process input admission.

## 12. Retention, encryption, and forgetting

### 12.1 Required owner amendment

CF-0 implementation is blocked until the owner ratifies a prospective policy
that permits application-owned private inference material to be encrypted per
operation and cryptographically shredded. The amendment MUST explicitly state:

1. payload classes covered: plans, prompts/context material, model responses,
   temporary extraction/rerank/embedding batches, and private command results;
2. key hierarchy and storage boundary;
3. retention windows by successful, failed, cancelled, and debug operation;
4. whether removal destroys an operation data-encryption key immediately or
   after a disclosed recovery interval;
5. backup behavior and the maximum persistence of destroyed ciphertext;
6. sync exclusion for keys and private payloads;
7. immutable public receipt fields that survive shredding; and
8. migration truth for existing immutable plaintext adoption snapshots,
   attempt results, and any staged/application projections.

The recommended V1 semantic is prospective and exact: **Forget** applies to
Continuity-owned live content and derivatives plus every locally retained
admitted input, output, evidence excerpt, or projection whose lineage intersects
the forgotten source/memory revision. It shreds those operation keys while
content-free metadata/hashes remain. It does not claim erasure of legacy
plaintext, pre-migration backups, provider copies, exports, or remote peers.
**Remove from Memory** is narrower: stop compilation, invalidate and purge live
Continuity claims/proposals/evidence/indexes without deleting canonical source.
Universal historical Forget is prohibited.

### 12.2 Prospective storage contract

Each private payload uses a random per-operation data-encryption key (DEK) and authenticated
encryption with associated data binding table, row ID, contract, owner, digest,
and schema revision. Each DEK is a separate native-keystore entry; V1 has no
DB-stored wrapped DEK or ordinary-file/environment fallback. Key lineage stores
only key IDs, algorithm revision, creation/destruction receipts, and ciphertext
digest. Keys and ciphertext never sync together. Decryption occurs only after
the same authorization that admitted the operation.

Cross-store creation is a recoverable saga: commit a reserved intent; create
the native key idempotently; encrypt; atomically persist envelopes and mark
active. Recovery destroys orphan keys, resumes `key_created` intents, and marks
an active row with missing key as integrity failure. Shred first commits an
access barrier/`destroying`, then idempotently deletes the native key, then
commits `destroyed` and its receipt. It never reports completion before native
deletion succeeds; missing key plus a valid destroying intent is completed
idempotently, while an unexplained missing active key is corruption.

`Remove from Memory` synchronously denies reads and queues feature-owned value/
derivative purge, but does not destroy historical admitted-operation keys.
`Forget` separately applies the ratified DEK destruction rule to every
intersecting lineage. FTS rows, vectors, graph edges, caches, previews,
and excerpts are purged. Public immutable receipts survive without prose.
Historical provider copies, OS/filesystem remnants, exported backups, and
pre-amendment plaintext are disclosed limitations, never described as erased.
Content-bearing `inference_adoption_attempt_results.result_json`, observer
arguments/results/exceptions, Ask/tool results, staged projections, exports,
and backups MUST each be enveloped, proven canonical under another retention
contract, or excluded from Forget. Encrypting inputs alone is non-compliant.

## 13. Model admission, poisoning, and egress

| ID | Requirement | Verify |
| --- | --- | --- |
| CF0-AI-001 | Embedding, rerank, extraction, consolidation, and briefing MUST be distinct sealed capabilities with exact input/output contracts. | T,I |
| CF0-AI-002 | Model/destination assignment MUST freeze before private payload assembly; incompatible egress fails before text access. | T,I |
| CF0-AI-003 | Extractor output MUST validate closed predicate/value/qualifier schemas, source spans, scope, temporal fields, and evidence revisions before becoming a proposal. | T |
| CF0-AI-004 | Imported, connector, tool, assistant, and quoted instruction text MUST be marked untrusted and isolated from system/policy instructions. | T,B |
| CF0-AI-005 | Retrieved content MUST never supply capability IDs, tool targets, destinations, credentials, scope, egress, or permission. | T,B |
| CF0-AI-006 | Vector and graph queries MUST receive already-authorized candidate identities or enforce equivalent exact metadata predicates before similarity/traversal. | T,B |
| CF0-AI-007 | A model confidence score MAY order proposals but MUST NOT alter acceptance, truth, retention, or suppression. | T,I |
| CF0-AI-008 | Malformed, overlong, non-finite, wrong-dimension, stale-generation, or digest-mismatched model results fail closed and are terminally receipted. | T,B |
| CF0-AI-009 | Remote model use requires an owner-compatible destination and source egress policy; local unavailability MUST NOT silently route remotely. | T,B |
| CF0-AI-010 | Proposal clustering and consolidation MUST preserve every evidence ref and surface contradictions rather than averaging them away. | T,D |

### 13.1 Sealed representation contracts

Every representation/extraction operation is an Article-XI admitted child with
a frozen capability revision, route, manifest, budget, private envelope, and
terminal receipt. CF-0 supplies deterministic fake local runners only.

All five registry entries are revision 1. Shared `MemoryBatchRequest@1` freezes
operation/planning refs, capability/policy/generation, ordered items
`{item_id,source_ref,source_revision,source_digest,byte_span,text_digest,
private_envelope_ref}`, exact tokenizer/token counts, deadline, and child
budget. It permits at most 128 items, 262,144 UTF-8 plaintext bytes, and 32,768
input tokens; lower capability/generation limits win. Results contain no text.

- `memory.embed@1` accepts bounded ordered item manifests and exact private text
  envelopes; `EmbeddingBatch@1` returns generation, ordered IDs, dimension, and
  a private vector-envelope ref. Vector bytes are contiguous little-endian
  IEEE-754 float32 row-major `[item_count, generation_dimension]`; JSON stores
  dtype/endian/shape/plaintext hash only. Count/order/dimension, all finite,
  nonzero norm, and `abs(L2_norm-1)<=0.0001` validate before publication.
- `memory.rerank@1` accepts exact query digest and eligible candidate manifest;
  at most 128 candidates; it returns only a permutation and score strings using
  the canonical decimal grammar, range `[-1000000,1000000]`, at most 9
  fractional digits. Query material is terminal-shredded.
- `memory.claim_extract@1` accepts a frozen evidence manifest plus scope,
  trust/time/egress policy and returns at most 32 closed proposal operations and
  65,536 canonical JSON bytes.
- `memory.claim_consolidate@1` accepts frozen active/proposal versions and
  returns at most 32 proposal transformations from at most 128 input versions;
  the same 65,536-byte output cap applies.
- `memory.continuity_brief@1` returns source-backed statement records, never
  authority or activation, with at most 64 items/65,536 output bytes and at
  least one manifest evidence ref per item.

Wrong contract/revision, cap, order, encoding, hash, score grammar, or output
shape is `invalid_model_output` and publishes zero rows. Capability-specific
input/result JSON Schemas are closed/no-extras and golden-fixture hashed.

### 13.2 Proposal validation and publication order

Model output contains no activation field. The discriminated claim union uses
exactly `add|replace|temporal_successor|change_scope|change_mode|archive|review`;
the separate procedure union routes `add|replace|archive|review` only to
`procedure_proposals` under its adapter schema. It may reference only source and target
IDs present in the frozen manifest and is bounded by item/byte limits. The
server applies this exact order: strict schema/no extras; manifest membership;
subject/scope/People rules; recompute identity/value digests; evidence span and
digest; temporal rules; taint/egress intersection; conflict classification;
deterministic fingerprint/deduplication; CAS publication.

The proposal fingerprint covers policy revision, input-manifest digest,
operation, scope digest, claim key, value digest, and target version. If a
source/target changes, publication creates no proposals and ends with a stale
receipt/replay token. Invalid output cannot wedge a source cursor: the interval
is terminally recorded and remains explicitly replayable.

If acceptance includes owner edits, the server recomputes identity/value/time,
revalidates cited evidence against the edited claim, and marks unsupported
edited portions `owner_authored`; it never carries misleading model evidence
forward. Assistant/model text is proposal-origin material only. Its eligible
frozen inputs or the owner's explicit command—not its prose—are factual evidence.

### 13.3 Derived-data invalidation

Vectors are sensitive derived data. Chunk, vector, and edge rows carry source
lineage/revision/digest, scope/membership revision, privacy, egress, taint,
lifecycle, and generation. Canonical update/delete/Forget/privacy/scope change
atomically advances an invalidation epoch. Retrieval rechecks current epochs
before loading vectors or traversing edges; post-top-K filtering is forbidden.
Async purge follows synchronous ineligibility. Query vectors are ephemeral and
uncached in CF-0. Derived stores are local-only and excluded from ordinary sync;
backup, if later allowed, inherits the removal disclosure.

`continuity_invalidation_heads` is keyed by canonical source ref and stores only
a monotonic epoch; the canonical writer/minimal outbox transaction CASes it
without needing adapter-normalized metadata. Adapter publication writes
`continuity_derivative_heads` with source ref, that current epoch, normalized
source revision/digest, scope-membership revision, privacy revision, and
generation. Every chunk/vector stores the published tuple. Each graph edge
stores the published tuple for **both** source and target. Pre-traversal SQL
joins both invalidation heads, both normalized derivative heads, and generation;
target removal,
scope, or privacy change therefore fences the edge even when source is stable.
Chunk/vector candidate SQL joins current invalidation plus normalized heads and exact generation before
vector bytes load; any mismatch is synchronously ineligible. Purge jobs key on
`(source_ref, invalidation_epoch, generation)` and are idempotent.

## 14. First-class Memory product contract

The product amendment SHALL establish **Memory** as a first-class Desk
application. CF-0 defines states and contracts; CF-4 ships the complete UI.
CF-0 also lands a development-flagged persisted application shell with mocked
state services solely to validate those contracts; it performs no production
genesis, inference, activation, or prompt injection.

### 14.1 Information architecture

- **Continue:** source-backed Project/Recipe/Workbench briefs and recent change.
- **Remembered:** active/archived accepted claims with scope and compile mode.
- **Recall:** authorized episodic search with lexical/semantic/relationship
  explanations and exact source opening.
- **Review:** bounded, non-escalating proposals, conflicts, and maintenance.
- **Health:** a disclosed diagnostic posture, not a fifth everyday workflow.

### 14.2 Required states

Every surface defines `first_run`, `ready`, `empty`, `loading`, `partial`,
`paused`, `degraded`, `offline`, `blocked_by_policy`, `failed_repairable`, and
`removed`. The owner can always determine whether a statement is canonical
source, accepted memory, proposal, or generated brief.

Consent must name source classes, exclusions, local/remote destination, model
profile, approximate work, interruption behavior, and removal limitations.
Standing “Learn from my work” authorization is separate from one-time genesis
and can be revoked without losing accepted memory.

### 14.3 Parity, accessibility, and disclosure

HTTP, MCP, desktop, and phone projections use the same application services,
command envelopes, scope law, and receipts. MCP cannot bypass review. Every
mutation exposes expected revision and conflict handling. UI controls require
keyboard navigation, screen-reader names, visible focus, non-color state, text
scaling, reduced motion, and WCAG 2.2 AA contrast. Degraded operation must
retain lexical recall, accepted always Core where authorized, source opening,
and correction/removal.

Analytics are local and content-free by default: state transitions, duration
buckets, counts, error codes, layer omission codes, and owner-invoked actions.
No stable source labels or cross-install identifier leave the device.

### 14.4 Owner-journey requirements

| ID | Requirement | Verify |
| --- | --- | --- |
| CF0-UX-001 | First open MUST perform no download/model/build write and show one `Build from my work` action, destination badge, eligible/excluded counts, model readiness, estimated disk, and duration before authorization. | T,D |
| CF0-UX-002 | With zero eligible work, Memory MUST show an honest empty state while Remember and Recall remain usable; it MUST NOT offer fictional genesis. | T,D |
| CF0-UX-003 | Genesis MUST remain durable while the Memory window closes or other Desk apps run; reopening MUST show the same run without duplicate work. | T,B,D |
| CF0-UX-004 | The first authoritative/lexical brief value MUST NOT wait for proposal review, semantic completion, or graph completion. | T,D |
| CF0-UX-005 | Every brief statement MUST disclose freshness, `accepted|observed|derived`, and openable canonical source refs. | T,D |
| CF0-UX-006 | Continue MUST expose a real canonical resume verb when available; a summary-only panel does not satisfy Continue. | T,D |
| CF0-UX-007 | Proposal batches MUST begin unselected; acceptance requires deliberate item/range selection. | T,D |
| CF0-UX-008 | Leaving a review MUST preserve selection, edits, evidence expansion, filter, and scroll state. | T,D |
| CF0-UX-009 | Point-of-use correction MUST preserve the originating surface, show its receipt, and change the next eligible invocation across every consumer. | T,D |
| CF0-UX-010 | Disabling learning MUST stop future proposal cycles without altering accepted Core; deterministic integrity/removal work continues. | T,D |
| CF0-UX-011 | The seven-day return ritual MUST require no SQL, raw API, fixture, or Health diagnostic. | D |
| CF0-UX-012 | Stable deep links MUST restore Memory posture, scope, filter, and selected canonical object. | T,D |

### 14.5 Application grammar and owner amendments

Memory is one persisted Desk window/Dock program, not a route-owned page or
modal world. Its four postures are exactly Continue, Remembered, Recall, and
Review. Continue answers where the owner left off, what changed, what remains
open, and what can resume. Remembered visually separates accepted claims from
procedural lessons and filters Everywhere/Project/Recipe/Workbench. Recall
labels direct, conceptual, and related-path hits; any graph has a linear text
equivalent. Review filters additions, replacements, conflicts, time changes,
procedures, stale provenance, and terminal history and is never “overdue work.”

Health reuses Doctor/model/index diagnostic contracts and links each degraded
row to its exact repair verb. Project Room and Memory operate on identical IDs,
revisions, commands, and review state. Memory participates in the Desk window,
Dock, Exposé, palette, global verb, context-menu, deep-link, shortcut-sheet, and
System Shade contracts.

Owner amendment must freeze application positioning, Dock order, program ID,
whether `Command-5` is the shortcut, launch-local-only genesis, first-run Dock
presence, phone genesis authority, required procedure adapters, suggestion caps
per scope, the proposed composite-scope precedence, proof-ledger retention, Strong
Forget availability, and whether resume recommendations may be model-derived.

Normative IA IDs are: `CF0-IA-001` one persisted Desk/Dock window;
`CF0-IA-002` exactly four primary postures and diagnostic-only Health;
`CF0-IA-003` Continue's four questions/no empty theater; `CF0-IA-004`
Remembered authority separation and scope filters; `CF0-IA-005` Recall's hit
classes plus linear path; `CF0-IA-006` Review's fixed non-overdue filters;
`CF0-IA-007` Project Room identity; `CF0-IA-008` window/posture/draft
persistence; `CF0-IA-009` Desk integration; and `CF0-IA-010` shared
Health/Doctor contracts. Each is `MUST` and needs contract tests and fixtures.

### 14.6 Consent and removal vocabulary

Genesis preflight freezes source census, route/destinations, policy revision,
model readiness, disk and duration estimates. A material change requires a new
preflight. Start, pause, resume, cancel, and rebuild are distinct commands and
receipts; cancel prevents publication and offers purge of incomplete derived
material. Genesis completion never enables learning.

Standing authorization is displayed as `Learn from my work — [destination] —
Suggestions only` and freezes capabilities, source categories, scopes,
destination, cadence/threshold policy, and authorization revision. Destination
expansion, source-category expansion, or local-to-egress change invalidates it
and requires a new gesture. Disabling stops unpublished runs; an in-flight
admitted operation ends with a named disposition, and pending proposals remain
unless separately removed.

The owner-facing destructive ladder is fixed:

| Verb | Meaning |
| --- | --- |
| **Stop using** | reversible archive; standard Undo receipt |
| **Remove from Memory** | stop/purge live Continuity material while preserving canonical sources |
| **Forget** | irreversible cryptographic removal where supported, with replay/provider/backup/legacy limits |

Removing canonical source and accepted memory are separate commands. Every
confirmation enumerates affected resource classes. `Forget everywhere` MUST
NOT appear when the system cannot provide it, and completed key shredding MUST
NOT offer false Undo.

Normative consent IDs are: `CF0-CON-001` open performs no work;
`CF0-CON-002` frozen/renewed preflight; `CF0-CON-003` launch destination and
disclosure; `CF0-CON-004` distinct run commands/receipts/purge;
`CF0-CON-005` no implicit learning; `CF0-CON-006` complete standing grant;
`CF0-CON-007` expansion invalidates consent; `CF0-CON-008` suggestions-only;
`CF0-CON-009` disable/in-flight/pending law; `CF0-CON-010` affected classes;
`CF0-CON-011` preserve source; `CF0-CON-012` separate source/memory removal;
`CF0-CON-013` Forget limits; `CF0-CON-014` truthful Undo; and `CF0-CON-015`
no false Forget-everywhere. Each is `MUST` and needs service/fixture evidence.

### 14.7 Cross-surface parity

| ID | Requirement | Verify |
| --- | --- | --- |
| CF0-PAR-001 | Web, desktop, phone, HTTP, and MCP MUST project the same refs, versions, scopes, paths, run states, omissions, commands, and typed errors. | T |
| CF0-PAR-002 | Desktop/Web MUST support all Memory postures and owner commands. Phone MUST support the four postures, source opening, review/edit/reject, correction, archive/removal, run status/pause/resume, and learning disable. | T,D |
| CF0-PAR-003 | Phone MUST use authenticated hub state, not a second replicated memory authority; host-only model acquisition MAY deep-link to Settings. | T,I |
| CF0-PAR-004 | Ask, Thought, Thread, Agent, Recipe, Workbench, Workflow, and Coder MUST share one disclosure and correction vocabulary. | T,D |
| CF0-PAR-005 | HTTP/MCP MUST expose every required resource transition with identical typed outcome; non-owner/model principals remain proposal-only. | T |
| CF0-PAR-006 | Project Room MUST NOT create duplicate proposal, selection, or dismissal state. | T,I |
| CF0-PAR-007 | Voice Remember MUST arm an editable in-world command under normal voice confirmation unless separately ratified. | T,D |
| CF0-PAR-008 | A parity fixture MUST replay every ratified state/command and compare normalized schemas; responsive Web MUST NOT count as native-phone proof. | T,D |
| CF0-PAR-009 | The proof matrix MUST be generated from every capability/consumer policy that is not `none`, with a content-free receipt proof where no owner-facing result exists. | T,R |

### 14.8 Accessibility contract

Posture tabs use correct tab semantics, roving arrows, Home/End, selection, and
stable focus. Recall, Remembered, Review, Health, and source lists are one Tab
stop each with row roving, Home/End, type-ahead, and visible full-row focus.
Review supports Space toggle, Shift+Arrow ranges, select-none, and announced
selection count. Pointer-only review fails release.

Frozen progress uses a named progressbar; indeterminate work uses status and
in-flow failures use alert, with throttled announcements. Origin, destination,
scope, authority, conflict, and degradation never rely on color. Source chips
name kind/title; paths have ordered text equivalents. Inline editors restore
focus. All confirmation remains in-world, keyboard-operable, and non-modal.
Reduced motion removes animation without hiding change. At `<=720px`, the
standard bottom sheet has no horizontal overflow and preserves coarse-pointer
verbs. VoiceOver on macOS/iPhone and the supported Linux reader MUST complete
preflight, review, Recall, correction, and removal. Automated scans require
zero serious/critical findings but do not replace keyboard/reader demos.

Normative accessibility IDs `CF0-A11Y-001` through `013`, in paragraph order,
cover: posture tabs; roving lists; keyboard range review; progress/status/alert;
non-color semantics; named sources/text paths; focus restoration; in-world
keyboard confirmation; reduced motion; compact/coarse-pointer layout; target
floor; screen-reader critical flows; and automated-plus-human proof. The target
floor is 44 CSS px/Web and the equivalent native platform minimum. An owner-
ratified `AccessibilityMatrix@1` freezes exact production builds, browsers,
macOS VoiceOver, iPhone/iOS VoiceOver, Linux screen reader, keyboard/pointer,
100/200% text scaling, contrast, and reduced-motion versions for evidence.

### 14.9 Product and lane state grammar

Genesis uses exactly: `not_built`, `preflight_ready`, `queued`, `scanning`,
`indexing`, `extracting`, `reconciling`, `paused_owner`, `paused_system`,
`blocked_model`, `blocked_disk`, `blocked_destination`, `failed_retryable`,
`failed_terminal`, `canceled`, `ready`, and `ready_degraded`. Each state exposes
a label, known completed/eligible/failed/excluded counts, currently available
capabilities, one recovery verb where possible, typed API state, and a System
Shade transition if Memory was closed.

Independent lanes do not collapse into one “degraded” flag:

| Lane | Closed states |
| --- | --- |
| Recall | `lexical_ready`, `semantic_absent`, `building`, `ready`, `stale`, `corrupt`, `degraded` |
| Brief | `absent`, `building`, `ready`, `stale`, `partial`, `blocked` |
| Core | `empty`, `ready`, `conflict`, `capacity_blocked` |
| Review | `empty`, `available`, `conflict`, `source_unavailable` |
| Learning | `off`, `ready`, `running`, `paused_owner`, `paused_system`, `destination_invalid`, `failed` |
| Procedure | `unavailable`, `importing`, `ready`, `degraded`, `policy_blocked` |

Lexical/authoritative recall survives semantic failure; no partial generation
serves; proposal-model failure does not invalidate Core/Recall; destination
change stops work rather than rerouting; disk failure preserves the prior
active generation; capacity conflict names exact Always claims/remedies;
missing scope never falls back globally; unavailable provenance remains named.

Durable run-to-product mapping is closed:

| Durable state | Owner state | Available/primary verb | Shade |
| --- | --- | --- | --- |
| absent / requested | `not_built` / `queued` | Recall/Remember; Cancel when queued | none |
| inventorying | `scanning` | lexical Recall; Pause | progress bucket |
| indexing | `indexing` | lexical Recall; Pause | progress bucket |
| extracting | `extracting` | lexical/ready Recall; Pause | progress bucket |
| catching_up / validating / publishing | `reconciling` | prior active lanes; Pause except atomic publish | progress bucket |
| paused_owner / paused_system | same named owner state | current safe lanes; Resume or Health | one pause notice |
| cancelling / purging_incomplete | `canceled` pending cleanup | current prior generation; purge status | one cancellation notice |
| failed_retryable / failed_terminal | corresponding failed state | prior safe lanes; Retry/Health or Health | one failure notice |
| completed | `ready` or `ready_degraded` from lane states | all qualified lanes; Rebuild | one completion notice |

`preflight_ready` is an owner/application state before a durable run exists.
`blocked_model|blocked_disk|blocked_destination` are preflight or paused-system
reason projections, never invented run states. `offline` means cached owner UI
plus no hub mutations: local canonical source opening/lexical behavior remains
only where that glass owns it; all commands name offline and wait for reconnection.

Normative state IDs are: `CF0-STATE-001` closed genesis states;
`002` per-state counts/capability/recovery/Shade projection; `003` independent
lane states; `004` lexical continuity; `005` atomic-generation service;
`006` failure isolation; `007` no destination reroute; `008` prior-generation
disk safety; `009` exact capacity/scope/provenance failures; and `010` durable-
to-owner/offline mapping. Each is `MUST` with exhaustive state-fixture tests.

## 15. Observability and diagnostics

Required metrics/events:

- command outcomes and conflict codes by operation;
- source journal lag/count by adapter and eligibility reason;
- plan construction duration, layer count, budget and omission reason;
- generation state, coverage count, and validation outcome;
- removal barrier/purge lag and unresolved derivative count;
- run state, cursor, skipped count/reason, and replay outcome; and
- integrity/reconciliation state.

This is a local proof ledger, not telemetry. It has owner-ratified bounded
retention, is inspectable/purgeable, and never leaves the machine
automatically. Allowed fields are event enum, posture, typed state/outcome,
duration bucket, counts, scope-kind enum, destination class, contract/model/
policy revisions, and content-free operation correlation. Forbidden fields are
queries, values, display text, source excerpts/titles/refs, Project/Recipe/
Workbench names, vectors, rationale, paths, and prompt material.

The ledger MAY measure review selection/edit/accept/reject/dismiss, review
duration, source opening, resume-verb use, correction propagation, degradation,
and recovery. Frequency or recall count never changes memory authority.
“Search success” is a labeled proxy requiring a downstream open/resume gesture,
not merely returned results. Export is an explicit owner action with preview
and sentinel scan; release reports name missing samples rather than fabricating
success.

Cardinality is bounded. IDs are ephemeral correlation IDs or keyed install-
local hashes and never exported by default. Diagnostic export requires an
owner preview that enumerates fields and redacts paths, prose, query text,
values, vector bytes, model payloads, secrets, and third-party identity.

Continuity services MUST NOT use the generic observer's argument/result/
exception serialization. They emit typed content-free observation envelopes;
exception classes map to safe codes and `repr`, message, stack locals, and
payload fragments are discarded before observation. A sentinel test covers DB,
WAL, logs, metrics, errors, crash artifacts, receipts, and exported reports.

Normative proof IDs are: `CF0-MEAS-001` no automatic egress; `002` allowed
fields; `003` forbidden fields; `004` bounded inspectable/purgeable retention;
`005` permitted product gestures; `006` no authority feedback; `007` explicit
previewed export; `008` sentinel scan; `009` labelled search proxy; and `010`
honest versioned release computation. `ContinuityProofService@1` owns the
commands in section 7.2; Health exposes retention, purge, preview, export, and
leakage-scan status/verbs with receipts.

## 16. Migration, flags, rollback, and compatibility

### 16.1 Migration sequence

1. record preflight schema/application version and create the existing safe
   database backup **before** the first Continuity DDL/trigger change on a
   populated database; verify the backup can be opened;
2. apply additive tables, indexes, triggers, and closed contract registries;
3. validate foreign keys, trigger laws, canonical digests, and empty-state
   application services;
4. deploy source adapters in journal-only reconciliation mode;
5. enable plan build in local no-model shadow mode;
6. retain migration and reconciliation receipts; and
7. leave all prompt injection, genesis, learning, vectors, and product claims
   disabled.

No CF-0 migration mutates canonical source prose or current relationship-aware
indexes. Legacy inference plaintext is inventoried and disclosed; it is not
silently rewritten or falsely marked shreddable.

Vault cutover uses additive `inference_adoption_material_v2` and
`inference_attempt_results_v2` content-free headers pointing to mandatory
private envelopes; current immutable `NOT NULL` plaintext tables remain
read-only `legacy_plaintext`. `InferenceMaterialResolver@2` dispatches by an
immutable operation material-version registry: v2 decrypt/verify, or explicit
legacy parser. Activation order is: install v2; land resolver; migrate every
enumerated reader to resolver; migrate writers; prove reader/writer census and
replay; atomically flip **new writes to v2 only**. Content is never dual-written
to legacy. Known adoption service, Workbench retry, attempt-result, Ask/tool,
export, and projection readers/writers are named in a checked census artifact;
CI/AST search fails on direct payload/result JSON access outside the legacy
resolver.

Rollback after v2 activation may disable affected inference/Continuity work but
MUST NOT reactivate a plaintext writer. An older binary unable to resolve v2 is
blocked from starting model-bearing operations; it may open canonical work in
the documented degraded posture. Legacy rows stay readable/disclosed and are
never rewritten as erasable history.

Schema ensure/reconciliation MUST NOT run corpus scans, embedding, extraction,
proposal generation, JSONL import, or destructive cleanup. Trigger definitions
are revisioned/hash-compared and replaced through an approved migration;
`CREATE TRIGGER IF NOT EXISTS` alone is insufficient. Capture installs disabled.
The database layer MUST verify its actual journal mode; documentation is not
evidence that WAL is enabled. CF-1 long-read/catch-up design either qualifies
WAL on every supported platform or uses bounded snapshots without assuming it.

Legacy Workbench JSONL import uses a file digest/checkpoint, never deletes the
file in CF-0, and repeated import is a no-op. The post-migration Doctor checks
FKs, trigger hashes, ref aliases, command uniqueness, closed states, active-
generation uniqueness, cursor monotonicity, legacy plaintext posture, key
provider readiness, and absence of protected prose in observations.

### 16.2 Feature flags

Closed flags default false:

`continuity_contracts`, `continuity_source_journal`,
`continuity_plan_shadow_local`, `continuity_plan_shadow_model`,
`continuity_genesis`, `continuity_learning`, `continuity_prompt_injection`,
`continuity_semantic`, and `continuity_memory_app`.

CF-0 may enable only the first three, and `continuity_plan_shadow_model` remains
false unless destination admission and retention amendments are ratified.

### 16.3 Rollback

Operational rollback stops workers, disables capture triggers/flags, and
returns all consumers to the existing
relationship-aware path without dropping data. Additive tables remain for
forensics/retry. A schema down-migration is a separately approved maintenance
operation with backup verification; automatic destructive down migration is
forbidden. Rollback success proves existing Ask, Thread, Recipe, Workflow,
Workbench, Coder, HTTP, and MCP retrieval contracts still pass.
Older code may reopen only after capture and encrypted-new-path writers stop;
it must tolerate additive dormant tables. A backup restore occurs only with
HoldSpeak stopped and all database connections closed.

## 17. CF-0 story and evidence map

| Work package | Roadmap story | Outcome | Requirements | Required evidence |
| --- | --- | --- | --- | --- |
| CF0-01 Owner amendments | [HS-162-01](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-01-the-owner-canon.md) | retention, Memory app, model-license posture ratified | INV-012, section 12, section 14 | signed amendment refs |
| CF0-02 Domain schema | [HS-162-02](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-02-the-domain-grammar.md) | claims, proposals, evidence, journal, policy, generation foundations | sections 4–6 | migration/constraint tests |
| CF0-03 Command core | [HS-162-03](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-03-the-command-core.md) | idempotent CAS mutations and stable errors | section 7, TXN-001–004 | concurrency/crash suite |
| CF0-04 Source journal | [HS-162-04](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-04-the-source-spine.md) | adapter registry, cursors, eligibility fixtures | section 10, TXN-007 | reconciliation reports |
| CF0-05 Plan waist | [HS-162-05](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-05-the-plan-waist.md) | canonical planner artifact, digest, budgets, receipt | section 8, TXN-005 | golden plans/token tests |
| CF0-06 Privacy core | [HS-162-06](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-06-the-private-material-vault.md), [HS-162-07](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-07-the-private-material-cutover.md), [HS-162-08](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-08-remove-and-forget.md) | key saga, encrypted resolver/cutover, removal barrier and Forget | INV-008/009, sections 12/15 | crypto/cutover/shred/removal/log scans |
| CF0-07 Foundation registries | [HS-162-09](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-09-the-derived-foundations.md) | procedure, graph, embedding-generation contracts | section 5.4, section 13 | state/constraint tests |
| CF0-08 Capability census | [HS-162-10](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-10-the-total-policy-census.md) | every registry ID assigned explicit policy | section 11 | generated census/CI drift test |
| CF0-09 Bounded shadow adapters | [HS-162-11](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-11-bounded-shadow-adoption.md) | planner contract plus representative Ask, Thread, Recipe, and Coder adapters construct but never inject local fake-runner plans; CF-2 completes the universal census rollout | INV-010/011, section 16 | per-capability goldens |
| CF0-10 Product shell/state fixtures | [HS-162-12](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-12-the-memory-contract-shell.md) | dev-only persisted Memory shell, mock service states, parity and accessibility grammar | UX/IA/CON/PAR/A11Y/STATE | wire fixtures, schema parity, keyboard/AT walkthrough |
| CF0-11 Local proof harness | [HS-162-13](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-13-the-local-proof-harness.md) | owner proof service, retention, preview/export, leakage scan | MEAS-001–010 | sanitized local report |
| CF0-12 Close and rollback | [HS-162-14](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/story-14-the-cf0-close.md) | fault campaigns, compatibility, evidence index | sections 9/16/18 | CF-0 close report |

The fourteen roadmap stories are PR-sized implementation contracts derived
from these twelve work packages, not evidence that CF-0 has shipped. CF0-06 is
deliberately split into three ordered privacy stories after council review.
Their live state and dependency graph are maintained in the
[Phase 162 status](../../pm/roadmap/holdspeak/phase-162-continuity-contracts/current-phase-status.md).

## 18. Acceptance gates

CF-0 exits only when all gates pass:

1. **Authority:** the explicit decision checklist in section 14.5 is fully
   ratified (positioning; Dock/program/shortcut; vocabulary; launch destination;
   first-run placement; phone authority; procedure adapters; per-scope caps;
   scope precedence; learning invalidation; retention/Forget; model/license;
   proof retention/export; accessibility matrix; reference hardware/corpus;
   resume synthesis) and no constitutional conflict remains. Counts or umbrella
   links cannot hide an unresolved decision.
2. **Schema:** a clean database and representative upgraded database satisfy
   constraints, foreign-key checks, state machines, and backup law.
3. **Commands:** replay, conflicting replay, concurrent CAS, crash-before-
   commit, crash-after-commit, and recovery have deterministic outcomes.
4. **Plan:** representative CF-0 adapters produce deterministic per-capability
   golden plans for identical frozen inputs/policies. Common included
   ref/revision/template rendering is byte-identical, while capability-specific
   plans correctly differ in operation, policy, scope, assignment, and budget.
   Token totals match the assigned tokenizer; no production plan is injected.
5. **Census:** all built-in, internal, future, installed plugin capability IDs,
   and Coder consumer have an explicit policy; registry drift fails CI. CF-2
   proves universal runtime plan construction.
6. **Sources:** every adapter fixture covers revision, deletion, privacy,
   scope, staleness, and reconciliation without prose in the journal.
7. **Privacy:** canary scans find no prose/value/query/vector/path in logs,
   receipts, metrics, crash reports, or public manifests.
8. **Removal:** success immediately blocks compile/retrieval and eventual purge
   reaches zero derivatives after injected crashes.
9. **Compatibility:** the existing relationship-aware focused suite and each
   named consumer contract remain green with all Continuity flags off.
10. **Rollback:** disabling CF-0 flags restores the exact pre-CF-0 runtime path
    without data loss or schema destruction.
11. **Product contract:** the dev-only application shell and mocked service
    fixtures prove every first-run, blocked, partial, degraded, conflict,
    removal, source-opening, parity, and accessibility wire contract. They do
    not claim real genesis or Continuity behavior.
12. **Evidence:** an indexed close report maps every CF0 requirement to test,
    inspection, demonstration, receipt, benchmark, or amendment evidence.

Any open severity-1/2 privacy, authority, corruption, deletion, or cross-scope
defect blocks exit. A waived lower-severity defect names owner, expiry, affected
requirements, safe degraded behavior, and verification date.

### 18.1 Mandatory structural and fault fixtures

- crypto: known-answer, AAD tamper, nonce uniqueness, locked/missing/deleted
  key, backup without native key, crash across envelope/admission, idempotent
  shred, multi-source whole-operation shred, legacy disclosure, and proof that
  no crypto failure falls back to plaintext;
- representation: correct/wrong dimension, NaN/Inf/zero vector, order/count
  mismatch, stale source before publication, and local route with cloud
  fallback denied;
- claims: Unicode/NFC, qualifier ordering, every composite scope, bounded/
  unknown interval boundaries and DST, simultaneous CAS, correction fork/cycle,
  UTF-8 evidence spans, edited/deleted evidence, fabricated time/target/source,
  and third-party subject denial;
- poisoning/egress: root-event duplicate and slow-drip external content,
  mixed destination restrictions, privilege/tool-target text, taint downgrade,
  invalid proposal extras, output cap, and stale consolidation manifest;
- derivatives: generation build/swap/crash, mixed generation rejection,
  source/privacy/Project-membership invalidation before top-K, graph path fences,
  purge crash/resume, and missing lineage;
- publication: proposal replay, crash before/after atomic publish, command
  timeout after commit, cursor non-wedging, and startup reconciliation; and
- product: every genesis/lane state, close/reopen persistence, empty preflight,
  unselected review, destination-consent invalidation, keyboard/reader flows,
  normalized parity, and canonical deep links.

CF-0 quality gates are structural. Real embedding choice, recall quality,
ranking latency, proposal acceptance, seven-day impact, and Wow gates remain
CF-1/CF-3 evidence and MUST NOT be fabricated with fake runners.

### 18.2 Staged product proof package

CF-0 captures **development-only contract fixtures** at 1440×900 and 393×852
from the persisted Memory shell and versioned mock services for every state,
consent, draft, conflict, focus, reduced-motion, compact-layout, and typed-error
contract. These prove wire/interaction derivability only and are watermarked
`CF-0 fixture — no owner data/model behavior`; they cannot appear in release
copy or satisfy a later product gate.

CF-3/CF-4 rerun the package against the production bundle and real application
services: preflight/zero-source; running/pause/crash/reopen; source-backed
Continue/resume; unselected edited review/conflict; composite scopes;
direct/conceptual/related Recall; disclosures/correction across the generated
non-none capability/consumer census; learning consent; semantic/destination/
disk/capacity/provenance degradation; archive/Remove/Forget; Shade/Health;
keyboard/range/reduced-motion/text path; and native-phone Continue/Review/
correction/removal. Recordings prove keyboard-only review, screen-reader flows,
recovery, and next-invocation correction. Hard-coded production demo state and
responsive-Web-as-phone evidence are rejected.

## 19. Traceability to the parent SRS

| Parent requirement family | CF-0 derivation |
| --- | --- |
| GEN-001–010 | source journal/run schemas, adapter census, retention gate, CF0-04/06 |
| CORE-001–012 | identity, cells/versions/proposals, state machines, commands, product states |
| RET-001–012 | authorized derivative foundations, generation/graph law, source reconciliation |
| PROC-001–007 | procedure envelopes and domain-authority boundary |
| PLAN-001–010 | `ContinuityPlan@1`, capability census, transaction/budget/failure law |
| MT-001–012 | learning authorization, proposal contracts, run lifecycle, removal propagation |
| SEC-001–012 | invariants, egress/poisoning, retention, telemetry, removal campaigns |
| NFR-001–012 | deterministic contracts, compatibility, accessibility, observability, rollback |
| CF0-UX/IA/CON/PAR/A11Y/STATE/MEAS | CF0-10/11 product shell, consent, parity, accessibility, state and proof fixtures |

The machine-readable implementation traceability artifact SHALL record:
`requirement_id`, `story_id`, `code_owner`, `test_refs`, `evidence_refs`,
`status`, `last_verified_at`, and `waiver_ref`. CI fails on unknown, duplicate,
or unowned IDs and on a `MUST` marked complete without evidence.

## 20. Explicitly deferred to later gates

CF-0 does not select the winning embedding model, tune rank fusion, implement
semantic chunks/vectors, extract real proposals, run corpus genesis, enable
living maintenance, inject a plan, ship the complete Memory app, or claim the
seven-day owner ritual. It establishes the binding contracts and safe substrate
from which CF-1 through CF-5 are derived without shrinking the product promise.
