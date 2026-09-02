# HoldSpeak Continuity Core — architecture RFC

**Status:** Council revision for owner ratification; design only; no implementation
is authorized by this document

**Date:** 2026-09-01

**Branch context:** `feat/relationship-aware-memory`

**Related:** [relationship-aware memory](../RELATIONSHIP_AWARE_MEMORY.md),
[the Constitution](CONSTITUTION.md),
[long-horizon retrieval](../../pm/roadmap/holdspeak/phase-109-the-long-memory/story-04-retrieval.md),
the [integration SRS](CORE_MEMORY_INTEGRATION_SRS.md),
and the [council record](CORE_MEMORY_COUNCIL.md)

## 1. Ratification statement

HoldSpeak should add **Continuity** as a flagship memory system. Core is its
owner-approved structured-claim layer; episodic, procedural, and working
memory join it through one frozen plan. After one owner-authorized local
genesis, Continuity should index eligible existing work, produce source-backed
resume briefs, propose durable memories, recall lexical/semantic/related
evidence, and apply accepted claims and corrections consistently across every
eligible intelligence surface.

Internal construction may be staged and feature-flagged. The first
owner-facing product claim is nevertheless ecosystem-wide: manual Remember,
existing-work genesis, hybrid recall, accepted always/contextual memory,
procedural bridges, universal planning, point-of-use correction, and an
owner-authorized living proposal cycle.

Owner-authenticated writes may activate immediately. Models may discover,
compare, consolidate, and propose after opt-in, but never silently activate,
rewrite, demote, or delete accepted memory. No memory may grant authority.

## 2. Product thesis

HoldSpeak should feel as though it knows the owner, not as though the owner
administers a memory database:

> Tell HoldSpeak what matters once. It carries that forward quietly. When it
> relies on memory, show why and allow correction in place.

The internal vocabulary is **Core, Episodic, Procedural, Working**. The normal
owner vocabulary is:

- **Remember** — create an explicit memory.
- **Remembered** — inspect what HoldSpeak currently carries.
- **Continue** — reconstruct where work stands and resume it.
- **Review** — inspect proposed additions, changes, conflicts, and lessons.
- **Recall** — find prior work through lexical, semantic, and relationship recall.
- **Remove from Core** — stop future Core search and compilation under the
  truthful V1 retention contract.

Memory is a first-class in-world Desk application with **Continue,
Remembered, Recall, and Review**. Project Rooms project the same scoped system;
result disclosures provide contextual inspection/correction. Health remains a
diagnostic posture rather than database administration. This requires an
explicit amendment to the current four-application positioning rule before UI
implementation. The existing “Desk memory” attention/receipt projection should
be renamed **Attention**; System Shade remains its internal surface name.

## 3. The four-memory model

| Layer | Question answered | Contract |
| --- | --- | --- |
| **Core** | What approved claim should remain guiding across turns? | Owner-governed structured claims; `always` claims compile deterministically and `contextual` claims compile when relevant. |
| **Episodic** | What relevant canonical work happened? | Existing relationship-aware retrieval over canonical work objects. |
| **Procedural** | What learned correction improves one operation? | Specialized stores such as Dictation corrections and Workbench lessons; never authority. |
| **Working** | What exact material does this invocation see? | One frozen admitted context: system + task + explicit grounding + Core + episodic + output reserve. |

Recipe behavior, Dictation corrections, and Workbench lessons remain procedural
but join the first complete release through typed adapters. A bridge may propose
a structured Core claim through normal evidence/review; it never flattens its
domain store or authority contract into Core.

## 4. Constitutional invariants

1. **The owner owns active memory.** An authenticated owner command may create,
   replace, archive, restore, or remove. A model may only create a proposal.
2. **Memory is not authority.** It cannot approve an effect, grant a right,
   choose credentials, relax egress, or override policy/current authenticated
   input. “Always send this” may guide a draft; it never authorizes sending.
3. **One atomic claim per cell.** Every accepted cell has a scope-local
   `claim_key`; free-form semantic similarity does not define identity.
4. **Evidence before inference.** Every proposal names immutable source
   revisions, exact evidence spans, root lineage, origin, assertor, and privacy
   class. Model rationale is not evidence and is not persisted as prose.
5. **People and third-party profiling stay out.** Raw People records and
   person-linked claims are categorically ineligible for extraction regardless
   of which Note or Thread contains them. Owner self-preferences may be eligible.
6. **Local-only by default.** Each cell/evidence item has an egress policy.
   Assigning a cloud model to Ask does not silently make all Core cloud-readable.
7. **No silent promotion, rewrite, or active deletion.** Confidence,
   recurrence, recall count, or age never changes active bytes.
8. **Exact scope is an access-control boundary.** Compilation requires the
   principal, eligible capability, destination, Project membership, and scope.
9. **Time is explicit.** World validity, source-event time, and database record
   time are distinct. Unknown time stays unknown.
10. **Compiled bytes are frozen bytes.** Planning, allocation, admission,
    dispatch, disclosure, and receipt agree on the exact artifact and hash.
11. **Memory is untrusted advisory data.** Delimiters are not a security
    boundary. Encoding, policy precedence, and authority separation still apply.
12. **Removal claims are literal.** The first release promises removal from future Core use,
    not retroactive universal erasure. Section 12 defines the boundary.

Articles I–III, V–VII, IX, and XI of the Constitution apply directly.

## 5. Continuity Core information model

### 5.1 Accepted memory and proposals are different resources

A rejected suggestion was never Core Memory. Do not represent proposals as
`MemoryCell(state=candidate)`.

```text
MemoryCell                       stable accepted identity
  id
  subject / predicate / qualifiers
  scope tuple                    optional Project / Recipe / Workbench bindings
  claim_key                      canonical structured scope-local slot
  kind                           preference | fact | convention | constraint
  compile_mode                   always | contextual
  head_version
  lifecycle                      active | archived | removed
  egress_policy                  local_only | allowed_for_assigned_destination
  revision                       optimistic-concurrency revision

MemoryVersion                    immutable accepted value
  cell_id + version
  value                          structured value
  display_text
  provenance_kind                explicit | accepted_proposal | imported
  recorded_at
  source_event_at
  valid_from / valid_until       half-open [from, until)
  temporal_basis                 owner | explicit_source | inferred | unknown
  temporal_precision / timezone
  prior_version

MemoryProposal                   not an accepted memory
  id
  operation                      add | replace | archive | review
  scope + claim_key + kind
  proposed value/display text
  target cell/version, if any
  status                         pending | accepted | rejected | expired
  frozen manifest digest
  reason codes
  expiry policy revision

MemoryEvidence
  owner ref                      proposal or accepted version
  canonical source ref/revision/digest
  exact evidence span or bounded review excerpt
  root_event_id                  prevents derived copies counting twice
  origin/trust + assertor class
  privacy and egress class

MemoryMaintenanceRun
  exact scope
  frozen source-change interval and manifest
  policy/assignment/model/parser revisions
  optional kernel invocation/receipt
  typed terminal result; no duplicated memory prose
```

Accepted text versions are immutable. Replacement appends a version and moves
the cell head with compare-and-swap. Use the existing service-event ledger and
kernel receipts for operational facts; do not create a second audit universe
containing memory text.

### 5.2 Claim identity and conflict law

Examples:

```text
presentation.summary.verbosity = concise
project.deploy.strategy = blue-green
term.rail = delivery rail
database.migrations.allowed = false
```

Required rules:

- At most one current active value exists for the same `(scope tuple, claim_key,
  overlapping valid interval)`.
- Same key + overlapping different value is a conflict.
- Same key + non-overlapping later interval is a temporal update.
- The most-specific matching Project/Recipe/Workbench tuple may shadow broader
  tuples for that invocation; it never mutates them.
- Supersession/version chains cannot fork or cycle.
- Fuzzy retrieval may find related claims for review, but cannot establish
  duplicate identity, contradiction, or precedence.

### 5.3 Kinds and source boundaries

| Kind | Example | Rule |
| --- | --- | --- |
| `preference` | Prefer concise implementation summaries. | Presentation guidance only. |
| `fact` | Orion deploys through blue-green releases. | Carries explicit temporal semantics. |
| `convention` | “The rail” means the delivery rail. | Normally Project-scoped. |
| `constraint` | Database migrations are not allowed for this Project. | Advisory; inferred constraints remain proposals until accepted. |

Proposal extraction may cover `preference`, `fact`, `convention`, and
`constraint` under stricter action-shaping validation. Procedures remain typed
procedural memory and require owner acceptance before changing behavior.

Explicit owner-authored text is eligible after secret/privacy validation.
Models, rejected drafts, streaming partials, failed output, hidden prompts,
People, credentials, kernel records, and raw activity are not evidence. An
owner-authored container is not automatically a trusted assertion: copied web,
repository, connector, model, and tool content retains its origin class.

## 6. Composite scope, capability, and egress

Accepted Core uses an exact optional-dimension tuple:

```text
project_id?
recipe_id?
workbench_id?
```

No bound dimension means owner-wide. Thread, person, device, and arbitrary
scopes remain absent. A claim matches only when every bound dimension equals
the frozen invocation context; the most-specific same-key tuple shadows broader
matches for that invocation.

Every model-bearing capability declares independent Core, episodic,
procedural, working, and action-use policies as defined by the integrated SRS.
Absence means no memory.

This prevents accidental injection into transcription, routing classifiers,
embeddings, or consumers that do not need standing memory. Compilation receives
the principal, capability/assignment, frozen destination/route, exact scope
vector and Project membership, `as_of`, and total context allocation.

An entry compiles only if its egress ceiling permits every disclosed route leg.
If routing is not frozen, use the conservative intersection of possible
destinations or omit the entry. Receipts name privacy omissions. At a cloud
decision, the owner sees that Core is included.

## 7. Commands, concurrency, and lifecycle

Every write carries:

```text
command_id
request_hash
authenticated actor
scope
expected_revision or expected_absent
```

The same ID + hash returns the stored result. The same ID with changed bytes
returns `idempotency_conflict`. Stale CAS returns `stale_revision`; no partial
state changes.

Owner commands are `remember`, `replace`, `accept_proposal`, `reject_proposal`,
`archive`, `restore`, and `remove_from_core`. There is no pin command in V1:
active memories never auto-delete, and pinning must not decide truth or prompt
precedence.

Explicit Remember activates atomically if valid under scope, privacy,
claim-conflict, and context policy. If capacity cannot admit the active set, it
returns `budget_conflict` with exact remedies; it does not quietly turn the
command into a suggestion or silently omit another accepted claim.

A current-turn owner correction governs the task but mutates storage only via
a separate command. Accepting a replacement proposal atomically compares its
frozen target revision and supersedes it or returns a named conflict.

## 8. Complete prompt waist

Core and episodic memory answer different questions but compete inside one
finite allocation:

```text
system + current task + explicit grounding + Core + episodic + output reserve
```

One pure `MemoryCompiler` creates a `MemorySnapshot` for every eligible
consumer. No UI, HTTP route, MCP tool, or inference path formats Core itself.

```text
compile(principal, capability, destination, scope_set, as_of,
        total_context_grant, policy_revision) -> MemorySnapshot
```

The snapshot contains cell/version refs, claim keys, labeled scopes, shadowing,
temporal/privacy omissions, exact encoded bytes, template/accounting revisions,
`as_of`, and a digest. Canonical serialization escapes values so memory cannot
escape its data container. The system instruction treats it as advisory.

Compilation is local, model-free, network-free, read-only, and uses one database
snapshot. It admits whole entries only. Future claims do not compile early;
expired claims do not compile; `review_due_at` affects attention, not truth.

### 8.1 Budget policy

No constant is ratified. The earlier 8,192-byte proposal is rejected. Benchmark
0/256/512/1,024-token Core envelopes across supported models/tokenizers and
representative complete prompts. Choose the smallest useful envelope that does
not crowd out explicit grounding or the task.

Provisional dogfood ceilings:

| Assignment context | Core ceiling under test |
| --- | ---: |
| 8K | 2,048 UTF-8 bytes |
| 16K | 3,072 UTF-8 bytes |
| 32K+ | 4,096 UTF-8 bytes |

The tested hard ceiling is 4,096 bytes including wrappers; maximum canonical
entry text is 512 bytes. Project and owner begin with equal shares and may
borrow unused space. These are hypotheses, not constitutional constants. Hash
exact UTF-8 bytes even when allocation is also tokenizer-aware.

The accepted library may grow. Capacity applies strictly to the `always`
partition; all eligible always claims compile or produce a named capacity
conflict. Eligible `contextual` claims are admitted whole from the request's
remaining Continuity allocation through receipted lexical/semantic relevance.
Any omission is named. Scope shadowing and contextual relevance are not truth
weighting.

### 8.2 Relationship retrieval and embeddings

Core identity, conflict, and `always` compilation do not use vectors. Accepted
Core is structured and selected first by exact principal, scope, identity,
validity, egress, and policy. Only then may local lexical/semantic retrieval
locate an already-accepted `contextual` claim; cosine similarity never decides
truth, precedence, scope, or authority.

Semantic vectors are also a launch-gated third lane for the existing
**episodic** relationship-memory system. They can retrieve canonical
evidence expressed with different vocabulary, then join the existing lexical
FTS and authoritative typed-relationship passes through deterministic rank
fusion. The source is always rehydrated from its canonical store before prompt
use. A vector is derived search material, never evidence, truth, relationship,
authority, or a Core promotion signal.

The first semantic implementation uses the existing SQLite domain rather than
an external vector database, starts with exact vector scan, and treats
`sqlite-vec` only as a qualified accelerator after scale and supply-chain gates.
Embedding model, tokenizer, templates, pooling, dimensions, runtime, chunker,
and artifact hashes form one immutable generation; changes rebuild in parallel
and atomically swap only after coverage and quality gates.

The [integration SRS](CORE_MEMORY_INTEGRATION_SRS.md) owns the concrete model
selection, schema, kernel, hybrid-ranking, migration, performance, privacy, and
cross-consumer requirements. It mandates a measured bake-off among
multilingual E5-small, EmbeddingGemma, and Qwen3-Embedding-0.6B rather than an
unmeasured permanent product choice.

## 9. Living cyclic maintenance

### 9.1 Source-change journal

Timestamp ordering is not a watermark. Every eligible canonical mutation must
transactionally append:

```text
event_seq
source_ref + source_revision
operation                       create | update | delete
root_event_id
eligibility/privacy/origin class
committed_at
```

The mutation and journal event commit together. Each adapter/scope stream owns
a monotonic `(adapter, scope, through_sequence)` cursor.

### 9.2 Run protocol

1. Freeze source interval/revisions, policy, active revisions, needed proposal
   set, destination, and manifest digest transactionally.
2. Run eligibility, time, privacy, key, and budget checks locally.
3. If owner-triggered and assigned, invoke a model outside the transaction
   through the kernel.
4. Validate a closed schema; persist reason codes/evidence spans, not rationale.
5. Publish proposals and advance the cursor atomically with CAS.
6. Deduplicate by policy, scope, revisions, manifest, and proposal fingerprint.
7. Record bounded terminal failures/skipped intervals and permit explicit replay.

Wake policy is separate from semantics. Thread compaction is merely a canonical
event, not a privileged learning trigger.

Deterministic maintenance may mark temporal ineligibility, expiry, unavailable
provenance, conflict, or review attention. A model may propose only `add`,
`replace`, `archive`, `review`, or `no_change`. Proposal merging belongs in
Review unless the candidate set is frozen. Usage has no truth weight. Evidence
independence is by root lineage, not repeated derived copies.

Candidate expiry is calibrated; 30 days is a dogfood hypothesis. Generic
90/180-day fact/preference rules are rejected because stability varies. Manual
Remember is always available. One explicit **Learn from my work** gesture may
authorize bounded local genesis and ongoing proposal cycles; it never
authorizes activation. Owner-selected source subsets remain an advanced control.

## 10. Product experience

### 10.1 Remember once

Select text, a Decision, or a Project object and invoke **Remember**, or say
“Remember that…”. An unambiguous current Project is proposed as scope;
**Everywhere** is the alternative. There is no kind selector or database modal.

```text
Remembered · Orion                 Undo
```

The receipt contains exact cell/version, source, scope, bytes, and command.

### 10.2 Correct at the point of use

When a result uses memory, show a quiet `Remembered 2` disclosure. Opening it
shows exact entries/sources with **Edit**, **Stop using** (archive), and
**Remove from Core**. The next invocation uses only the accepted new revision.
Point-of-use correction matters more than a management screen.

### 10.3 Review without an inbox

After learning is enabled, proposals use the existing attention ladder without
interrupting. Each shows bytes, scope, evidence, and **Remember / Edit /
Dismiss**. Suggestions expire without becoming active, overdue, or escalating.

### 10.4 First-class Memory application

One in-world **Memory** application presents **Continue, Remembered, Recall,
and Review**, with Health available through disclosure. Project Room links to
the same scoped services and projections; it does not implement another memory
system. Technical storage details remain diagnostics, not the normal UI.

## 11. Security and observability

- Core is untrusted data below policy and authenticated current input.
- It never grants tool permission or turns a remembered target into a trusted
  action target.
- Test direct, indirect, slow-drip, cross-scope, and post-consolidation poison.
- Generic observation logs only IDs, hashes, counts, classes, and outcomes—not
  cell/proposal text, excerpts, or rationale.
- Secret/personal proposals are rejected before durable proposal storage;
  failure observations do not echo bodies.
- Ordinary inference and consolidation independently enforce per-entry egress.

## 12. Truthful removal and the held retention decision

HoldSpeak presently stores exact admitted context in
`inference_adoption_material_snapshots.payload_json` under no-update/no-delete
triggers. Once Core participates in inference, universal “Forget” cannot be
truthfully promised by the memory feature alone.

V1 therefore offers **Remove from Core**:

- Purge Core bodies, textual versions, proposals, excerpts, and Core indexes.
- Prevent future Core search and compilation.
- Retain a content-free Core tombstone and purge receipt.
- Disclose that canonical sources, historical immutable inference payloads,
  provider copies, and backups are not erased.
- Return `forget_everywhere_unsupported` for a stronger request.

The owner must separately ratify whether HoldSpeak should surrender indefinite
plaintext replay for stronger forgetting. A credible design keeps immutable
receipt metadata/hashes, encrypts each operation's private payload under a
per-operation key, records Core-to-request lineage, and cryptographically shreds
affected keys on Forget—accepting loss of exact replay. Provider/backup limits
and a legacy-plaintext migration policy remain explicit. This changes
cross-cutting Articles IX/XI behavior; Core cannot decide it by implication.

## 13. Failure contracts

| Failure | Required result |
| --- | --- |
| Same command retried | Stored result for same hash; `idempotency_conflict` for changed bytes. |
| Concurrent edit | `stale_revision`; no partial changes. |
| Same-key contradiction | Current active remains; explicit replace or reviewed proposal required. |
| Scope mismatch | `scope_ineligible`; cross-Project isolation proven. |
| Destination forbids entry | `egress_ineligible`; disclosure names omission. |
| Active set exceeds policy | `budget_conflict` or named omission; no hidden truncation. |
| Future/expired fact | Omitted according to frozen `as_of`; review attention as appropriate. |
| Poisoned text | Advisory encoded data; no authority change. |
| Maintenance crash | Same manifest retries or uniqueness makes replay a no-op. |
| Owner removes memory | Future Core use fails; retention limits disclosed exactly. |
| Context plan differs from dispatch | Admission fails; one artifact/hash governs both. |

## 14. Evaluation and release gates

Evaluate the write–manage–read–act pipeline:

- **Write:** proposal precision/recall, atomicity, attribution, span fidelity,
  sensitive duplication, poisoning write rate, personal-claim rejection.
- **Manage:** conflict recall, temporal update accuracy, stale survival,
  idempotency, concurrency, root-lineage independence, deletion residue.
- **Read:** scope/destination leakage, stale recall, abstention, budget, latency,
  frozen bytes across preview/admission/dispatch/restart/model switch.
- **Act:** counterfactual tasks with no, correct, and stale/poisoned Core; prove
  there is no authority/tool/destination-policy delta.
- **Human:** acceptance/rewrite/rejection, time to review/correct, comprehension
  of scope/source/use/removal, and no overdue-Suggestion behavior.

Use model/version matrices, not the extraction model as its sole evaluator.
Real-model gates include wrong-memory correction, scope leak, restart continuity,
destination leakage, poisoning, context crowd-out, and sentinel residue.

## 15. Continuity release train

The [integrated SRS](CORE_MEMORY_INTEGRATION_SRS.md) is normative. Construction
uses hidden gates—contracts/retention, genesis/retrieval, universal shadow
planning, closed-loop dogfood, and product/cross-device proof—but the first
owner-facing claim requires all of them together.

Ask-only manual Core is a diagnostic checkpoint, not a release. No isolated
schema, vector index, prompt block, proposal queue, or UI may claim integrated
Continuity. The release must prove real corpus genesis, source-backed resume,
accepted always/contextual memory, hybrid recall, procedural adapters, living
proposal maintenance, point-of-use correction, and the same frozen plan across
every eligible consumer.

## 16. Prior-art decisions

RAGFlow validates raw/semantic/episodic/procedural separation, inspectable
extraction, and off-hot-path work. HoldSpeak rejects FIFO for active Core,
duplicate raw-message authority, and a vector dependency for active memory.
Its temporal and prompt-wiring bugs reinforce server validation and frozen-byte
proof.

- <https://github.com/infiniflow/ragflow/blob/main/common/constants.py>
- <https://github.com/infiniflow/ragflow/issues/18413>
- <https://github.com/infiniflow/ragflow/issues/18415>

Memory-first agents validate compact labeled blocks and off-hot-path reflection.
HoldSpeak turns reflection into proposals; agents never rewrite accepted blocks.

- <https://github.com/letta-ai/letta-code>
- <https://github.com/letta-ai/sleep-time-compute>

Context engineering validates finite context; HoldSpeak additionally allocates
one envelope across current work, Core, and episodic evidence.

- <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

Evaluation should use temporal updates/abstention, invalidated-memory reuse,
and adversarial extraction research—not one aggregate score.

- <https://proceedings.iclr.cc/paper_files/paper/2025/file/d813d324dbf0598bbdc9c8e79740ed01-Paper-Conference.pdf>
- <https://aclanthology.org/people/kumar-shubham/>
- <https://aclanthology.org/2025.acl-long.1227/>

## 17. Settled decisions and held questions

Settled for the proposed Continuity program:

1. Manual Remember is available; automatic proposals begin only after one
   explicit Learn-from-my-work authorization.
2. Accepted claims support exact optional Project/Recipe/Workbench scope
   dimensions and `always`/`contextual` compilation.
3. Owner writes may activate; every inferred/model item requires review forever.
4. Existing-work genesis, hybrid recall, procedural adapters, universal
   planning, and living maintenance are parts of the first complete release.
5. People and third-party personal claims are excluded from extraction.
6. Per-entry egress and Article-XI admission apply to every model operation.
7. Active entries never auto-delete; proposal expiry is calibrated, not canon.
8. No context constant or embedding model is ratified without complete-prompt
   and HoldSpeak-specific benchmark gates.
9. Memory is a first-class Desk application; Attention remains the separate
   receipt/attention projection.

Held for the owner:

1. **Strong forgetting:** should encrypted admitted payloads sacrifice exact
   replay through cryptographic erasure, and how should legacy plaintext migrate?
2. **Measured context/model grant:** which complete-context envelopes,
   embedding model/runtime, and optional reranker clear the usefulness,
   latency, license, and crowd-out gates?

Until ratification, there should be no schema, route, prompt, UI, or migration
implementation.

## 18. Non-goals

- A profile, relationship assessment, sentiment model, or surveillance system.
- Similarity-based Core identity, truth, conflict, or precedence.
- Replacing Notes, Knowledge, Projects, Threads, or episodic retrieval.
- A grant system or automatic action based on remembered text.
- Agent self-modification of prompts, personas, Skills, or active memory.
- Cross-device sync or universal backup/provider erasure guarantees.
- Implementation in this design pass.
