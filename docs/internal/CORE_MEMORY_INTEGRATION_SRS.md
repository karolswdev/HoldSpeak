# HoldSpeak Continuity — integrated memory system requirements specification

**Document ID:** `SRS-HS-CONTINUITY`

**Status:** Draft for owner ratification and implementation planning; no product
implementation is authorized by this document

**Version:** 1.0-council

**Date:** 2026-09-01

**Owner:** HoldSpeak product owner

**Related:** [Core architecture](CORE_MEMORY_DESIGN.md),
[council record](CORE_MEMORY_COUNCIL.md),
[implemented relationship-aware memory](../RELATIONSHIP_AWARE_MEMORY.md),
[Constitution](CONSTITUTION.md)

## 1. Purpose and product decision

This SRS defines **Continuity**, the ambitious HoldSpeak memory system that
turns existing and future canonical work into a living, inspectable model of:

- what remains true;
- where the owner left off;
- what changed;
- how a Project, Recipe, or Workbench operates;
- which explicit corrections should continue to apply; and
- which exact evidence influenced the current result.

Core Memory is one layer of Continuity, not the whole product.

The first owner-facing release SHALL be an integrated continuity release. It
MUST NOT be described or shipped as integrated memory when only a schema,
manual preference store, Ask-only prompt block, semantic index, or review queue
exists.

The launch promise is:

> After one owner-authorized local genesis, HoldSpeak reconstructs continuity
> from eligible existing work, proposes durable structured memories, recalls
> conceptually related evidence, applies accepted claims and procedural
> corrections consistently across every eligible intelligence surface, and
> makes every use inspectable and correctable.

## 2. Provenance: what RAGFlow contributed and what HoldSpeak built

Continuity builds on the relationship-aware retrieval already implemented on
`feat/relationship-aware-memory`.

That implementation is an original HoldSpeak adaptation of two RAGFlow ideas:

1. **Parent/child retrieval:** a matching segment or message part returns its
   coherent parent Meeting or Thread.
2. **Compiled relationship expansion:** deterministic direct matches seed a
   bounded traversal of already-authoritative adjacent relationships, after
   which canonical source passages are loaded.

No RAGFlow source was copied, vendored, or modified. HoldSpeak implements the
ideas through its own canonical objects, SQLite FTS5 indexes, typed
relationships, Project fences, grounding, admission, receipts, HTTP/MCP
contracts, UI, and tests.

The implemented branch baseline is:

| Commit | Contribution |
| --- | --- |
| `f5be54c3` | Relationship-aware retrieval integrated across HoldSpeak. |
| `72bf0ed0` | Desk discovery and search-highlight polish. |
| `f5ee7a3d` | Lifecycle documentation and production evidence. |

The branch is pushed to `origin/feat/relationship-aware-memory`. As of this
SRS, it has no GitHub pull request. The design documents are not part of those
commits.

Primary upstream references:

- RAGFlow: <https://github.com/infiniflow/ragflow>
- Compiled expansion inspected at `2af732d6072f050ead758edaf23dd4ebfec5526a`:
  <https://github.com/infiniflow/ragflow/blob/2af732d6072f050ead758edaf23dd4ebfec5526a/rag/advanced_rag/harness/tools/compiled_expansion.py>
- RAGFlow license: <https://github.com/infiniflow/ragflow/blob/main/LICENSE>

## 3. Existing HoldSpeak baseline

### 3.1 Episodic relationship retrieval

`holdspeak/db/memory.py` currently provides:

- FTS5/BM25 recall for Decisions, Artifacts, Notes, Meeting segments, and
  Thread parts;
- bounded canonical-table search for other ecosystem citizens;
- per-kind ranking and deterministic interleaving;
- parent hydration;
- authoritative typed one-hop relationship expansion;
- exact Project filtering; and
- stable origin/path metadata.

`holdspeak/grounding.py` hydrates canonical sources and currently caps prompt
hydration by source count. The source is the authority; the search index is
derived.

### 3.2 Existing consumers

The implemented episodic retrieval seam is used by:

| Consumer | Current code seam |
| --- | --- |
| Ask and Thought refinement | `holdspeak/services/ask_service.py` |
| Thread/chat | `holdspeak/services/thread_service.py` |
| Recipe/Agent paths | `holdspeak/services/recipe_service.py` |
| Sequence/Workflow model nodes | `holdspeak/services/sequence_workflow_service.py` |
| Workbench | `holdspeak/workbench_conductor.py` |
| Coder steering | `holdspeak/services/coder_service.py` |
| HTTP retrieval | `holdspeak/web/routes/memory.py` |
| MCP retrieval | `holdspeak/mcp/families/memory.py` |

These consumers currently call shared hydration, but still own portions of
their own prompt assembly. Continuity SHALL replace those forks with one frozen
planning artifact.

### 3.3 Related memory systems that retain their authority

- Dictation corrections are specialized procedural learning.
- Workbench `memory.jsonl` is bounded private run advice.
- Thread history and compaction are Thread working memory.
- Knowledge and `.hs/` files are owner-authored reference sources.
- People is an encrypted, separately governed third-party relationship store.
- Speaker embeddings are biometric-adjacent voiceprints, not text memory.

Continuity composes these systems through typed adapters. It does not flatten
their privacy, identity, retention, or authority contracts.

### 3.4 Inference and persistence laws

- `holdspeak/inference_capabilities.py` is the sealed model-capability census.
- Assignments freeze model, destination, capability, and context compatibility.
- Inference adoption freezes exact request material before dispatch.
- `inference_adoption_material_snapshots.payload_json` is currently immutable
  plaintext under no-update/no-delete triggers.
- Schema reconciliation is additive and backs up before shape changes.
- Article XI requires every model invocation, including embeddings and
  consolidation, to be admitted and end in a terminal receipt.

## 4. Product journeys

### 4.1 Build continuity from existing work

The owner opens the first-class **Memory** application and chooses:

```text
Build from my work                         Local
```

One authenticated gesture authorizes a bounded local genesis over eligible
canonical work. People, secrets, credentials, failed/draft output, private
leadership records, kernel material, and unadopted third-party claims are
excluded before model work.

While semantic indexing and proposal extraction continue, FTS/relationship
recall remains usable and progress states exact coverage.

### 4.2 Receive immediate value before accepting claims

Genesis produces source-backed Continuity Briefs without promoting inferred
claims:

```text
ORION

Where you left off
Deployment strategy settled; rollout checklist remains open.

Still moving
2 actions · 1 blocked coder · next cadence Friday

Changed
Rollback threshold was revised in the launch review.

Language in use
“the rail” → delivery rail
```

Every statement opens exact canonical evidence and declares observed fact,
accepted claim, or derived synthesis. Unsupported synthesis is omitted.

### 4.3 Create accepted continuity

The owner receives a bounded, clustered proposal bundle:

```text
Suggested for Orion                         8

✓ Orion uses blue-green deployment          Use when relevant
✓ “the rail” means delivery rail             Use when relevant
✓ Preserve reversible deployment paths       Always carry
```

Each proposal shows operation, structured claim, composite scope, temporal
basis, egress, evidence spans, and conflicts. The owner may select, edit, and
**Remember selected**. No unconditional Accept All exists.

### 4.4 Apply continuity everywhere

Eligible Ask, Thought, Chat, Agent planning, Recipe, Workflow, Workbench, and
Coder operations consume the same frozen `ContinuityPlan`. Results disclose:

```text
Core 4 · Recall 6 · Learned 1
```

Correction identifies the exact influencing claim, source, or procedure and
changes the next eligible invocation everywhere.

### 4.5 Keep continuity alive

The owner may enable:

```text
Learn from my work                         Local
```

Finalized eligible source events then drive incremental indexing, conflict and
temporal checks, bounded proposals, and correction-driven suggestions. The
standing setting authorizes maintenance runs, never activation of their output.

## 5. Memory model

Continuity contains four cooperating layers:

| Layer | Purpose | Selection |
| --- | --- | --- |
| **Core** | Owner-accepted structured claims. | Exact eligibility, then always or contextual compilation. |
| **Episodic** | Canonical work and history. | Lexical + dense semantic + typed graph retrieval. |
| **Procedural** | Accepted corrections and operation-specific lessons. | Typed adapter matching by operation and scope. |
| **Working** | Current Thread/Workbench/task state and exact admitted material. | Frozen for one invocation. |

### 5.1 Accepted Core versus compiled Core

Accepted memory may grow beyond one tiny prompt block. Every accepted claim has:

```text
compile_mode = always | contextual
```

- **always**: foundational preferences, constraints, and owner-selected facts;
  strictly bounded and deterministically present whenever eligible.
- **contextual**: accepted durable claims retrieved only when relevant to the
  current task after exact principal/scope/time/egress filtering.

Vectors may locate an accepted contextual claim. They never decide its identity,
truth, conflict, scope, temporal precedence, or authority.

### 5.2 Structured claim identity

```text
subject
predicate
value
qualifiers
scope tuple
valid interval
display text
```

Canonical `(subject, predicate, qualifiers)` produces `claim_key`. Display text
is presentation, not identity. A model may propose structure and aliases; owner
acceptance freezes identity.

Examples:

```text
subject=owner                  predicate=presentation.summary.verbosity
value=concise

subject=project:orion          predicate=deployment.strategy
value=blue-green
```

### 5.3 Composite scope

An accepted claim may bind any exact combination of:

```text
project_id?
recipe_id?
workbench_id?
```

No binding means owner-wide. Thread, person, device, and arbitrary scopes are
not Core scopes. A claim matches only if every bound dimension equals the frozen
invocation scope. Among same-key matching claims, the most-specific tuple
shadows broader tuples for that invocation; all remain unchanged.

Precedence is:

```text
authenticated current instruction
  > exact Workbench + Recipe + Project
  > exact Workbench/Recipe combinations
  > exact Project
  > owner-wide
```

The receipt names every shadowed version.

### 5.4 Conflict and time

- At most one accepted current value exists for the same claim key, exact scope
  tuple, and overlapping half-open valid interval `[from, until)`.
- An explicit owner correction atomically supersedes the prior value with CAS.
- A model-derived contradiction creates a proposal; it never selects a winner.
- Non-overlapping later validity is a temporal successor.
- Irreducible ambiguity produces clarification or abstention.
- `recorded_at`, `source_event_at`, world validity, temporal basis, precision,
  and timezone remain distinct.

## 6. Architecture decisions

| ID | Decision |
| --- | --- |
| AD-CF-001 | Continuity is the product; Core is one layer. |
| AD-CF-002 | The first owner release is ecosystem-wide; component slices are hidden engineering milestones. |
| AD-CF-003 | RAGFlow-inspired relationship retrieval is the implemented episodic substrate, not a copied dependency or external authority. |
| AD-CF-004 | One immutable `ContinuityPlan` is the complete prompt waist. |
| AD-CF-005 | Accepted Core supports `always` and `contextual` compile modes. |
| AD-CF-006 | Composite scope supports owner/Project/Recipe/Workbench dimensions. |
| AD-CF-007 | Semantic retrieval augments episodic and contextual accepted memory; it never establishes truth. |
| AD-CF-008 | One local derived vector store lives in SQLite; no external vector service ships initially. |
| AD-CF-009 | Every embedding configuration is an immutable generation and rebuilds atomically. |
| AD-CF-010 | Corpus genesis is a first-class durable, resumable, receipted operation. |
| AD-CF-011 | Procedural systems use a shared envelope plus typed domain adapters. |
| AD-CF-012 | Graph edges have authoritative, accepted, or derived trust classes. |
| AD-CF-013 | Models may automate discovery and proposals after opt-in; only the owner activates accepted memory or behavior. |
| AD-CF-014 | Memory is a first-class Desk application with Continue, Remembered, Recall, and Review; Health is a disclosed diagnostic posture. |
| AD-CF-015 | Strong forgetting requires encrypted/shreddable admitted payloads before memory-bearing corpus model work. |

## 7. System architecture

```text
canonical work + explicit teaching + corrections
                       │
                       v
              Continuity source journal
                       │
          ┌────────────┼─────────────┐
          v            v             v
     FTS / graph   vector index   proposal cycles
          │            │             │
          └──────┬─────┘             v
                 │              owner Review
                 v                    │
        episodic/contextual      accepted Core
                 │                    │
procedural adapters ─────────────┐    │
working state ───────────────────┼────┤
explicit grounding ──────────────┤    │
                                 v    v
                         ContinuityPlanner
                                 │
                                 v
                      immutable ContinuityPlan
                                 │
                                 v
                    kernel admission + execution
                                 │
                                 v
                    disclosure / correction / receipt
```

### 7.1 ContinuityPlan

```text
ContinuityPlan
  principal and authenticated rights evidence
  capability + continuity-policy revision
  destination/route and egress boundary
  exact composite scope
  as_of
  system and current-task material
  explicit grounding snapshot
  Core always/contextual snapshot
  episodic retrieval snapshot
  procedural snapshot
  Thread/Workbench working revision
  output/tool reservation
  exact bytes/tokens by layer
  omissions and reasons
  template/accounting/model/index generations
  digest
```

Every eligible consumer adopts this artifact before admission. Consumers may
declare layers `none`; they may not privately format or retrieve competing
memory blocks.

### 7.2 Continuity policy census

Every inference capability declares independently:

```text
core_policy        none | owner | composite
episodic_policy    none | global | exact_project
procedural_policy  none | operation_scoped
working_policy     none | thread | workbench | explicit
memory_action_use  forbidden | advisory_plan | gated_effect_proposal
```

Absence means `none`.

Initial policy:

| Capability/path | Core | Episodic | Procedural | Action use |
| --- | --- | --- | --- | --- |
| Ask, Thought, Chat | composite | Project/global | operation-scoped where relevant | forbidden |
| Agent plan/code | composite | exact Project | operation-scoped | advisory plan |
| Agent tool turn | none until adversarial action gates; then contextual only | exact canonical targets | operation-scoped | gated effect proposal |
| Recipe run | composite | exact Project | Recipe adapter | advisory plan |
| Sequence/Workflow node | explicit per node; default none | explicit per node | explicit per node | explicit per node |
| Workbench item | composite | exact Project | Workbench adapter | advisory plan |
| Coder steering | composite | exact Project/repository refs | Coder adapter when qualified | advisory plan |
| Meeting transcript extraction/identity | none | none | none | forbidden |
| Meeting summary rendering | owner presentation claims only | exact Meeting | none | forbidden |
| Speech transcription/intent/target | none | none | Dictation's existing typed correction path | forbidden |
| Chat compact/guardrail | none | exact Thread only | none | forbidden |
| Embedding/reranking/extraction | none | explicit frozen inputs only | none | forbidden |
| Plugin/future capability | none until registry revision | none | none | forbidden |

## 8. Functional requirements

Verification codes: **T** automated test, **I** inspection, **D** real product
demonstration, **U** owner verdict, **B** benchmark.

### 8.1 Genesis and source continuity

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| GEN-001 | MUST | `Build from my work` MUST create one authenticated durable genesis run with frozen policy, destination, corpus manifest, and command hash. | T,I,D |
| GEN-002 | MUST | Genesis MUST cover all eligible current Decisions, Notes, Artifacts, Meeting/Thread child units, Actions, Project items, Workbench results, Cadence evidence, owner messages/instructions, and typed correction bridges. | T,I |
| GEN-003 | MUST | Genesis MUST exclude People, third-party personal claims, secrets, credentials, kernel material, failed/draft output, assistant prose, and unadopted connector/tool/web claims. | T,I |
| GEN-004 | MUST | Legacy sources MUST receive synthetic backfill journal events with revision/digest/origin/privacy/scope metadata, then hand off without gap to the live cursor. | T |
| GEN-005 | MUST | Genesis MUST be pausable, restart-safe, idempotent, progress-visible, and reconcile concurrent source mutations before activation. | T,D |
| GEN-006 | MUST | Semantic generation activation MUST be atomic after coverage, integrity, leakage, quality, and latency gates. | T,B |
| GEN-007 | MUST | Genesis MUST produce source-backed Continuity Briefs before any proposal is accepted. | T,D,U |
| GEN-008 | MUST | The first proposal digest MUST be clustered by scope/claim and bounded to ten primary items per review batch. | T,D |
| GEN-009 | MUST | The owner MUST explicitly select each item or selected batch; unconditional Accept All MUST NOT exist. | T,D |
| GEN-010 | MUST | Genesis completion MUST report eligible/indexed/excluded/failed counts by source kind, model destination, generations, disk, and degraded intervals. | T,D |

### 8.2 Core claims

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| CORE-001 | MUST | Owner `remember` MUST create an accepted structured claim atomically with command ID/hash, expected absent/CAS, composite scope, compile mode, egress, provenance, and temporal semantics. | T,D |
| CORE-002 | MUST | Accepted cells/versions and proposals/evidence MUST be distinct resources and tables. | T,I |
| CORE-003 | MUST | Claim key MUST derive from structured subject/predicate/qualifiers; fuzzy similarity MUST NOT create identity or conflict. | T |
| CORE-004 | MUST | Explicit correction MUST replace with CAS and change the next eligible invocation everywhere. | T,D |
| CORE-005 | MUST | Normal authenticated contradiction MUST govern the current turn and MAY create one high-priority replacement proposal; it MUST NOT mutate accepted memory implicitly. | T,D |
| CORE-006 | MUST | Every model-derived add/replace/scope/time/compile-mode change MUST remain a proposal until owner activation. | T,I |
| CORE-007 | MUST | Same-key temporal/scope resolution MUST be deterministic, fork-free, cycle-free, and receipted. | T |
| CORE-008 | MUST | All eligible `always` claims MUST compile or return a named capacity conflict; none is silently ranked away. | T |
| CORE-009 | MUST | `contextual` claims MUST be filtered by principal/scope/time/egress before lexical/semantic relevance selection. | T,I |
| CORE-010 | MUST | Contextual similarity MUST NOT influence truth, precedence, confidence, or authority. | T,I |
| CORE-011 | MUST | Archive/restore/remove/change-mode/change-scope MUST use authenticated idempotent CAS commands. | T |
| CORE-012 | MUST | Remove from Core MUST purge Core-owned prose, proposals, excerpts, indexes, and future compilation while retaining only disclosed content-free lineage. | T,D |

### 8.3 Episodic retrieval and graph

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| RET-001 | MUST | Retrieval MUST preserve the implemented FTS, parent hydration, Project fence, and typed relationship behavior as its stable control/fallback. | T |
| RET-002 | MUST | The launch candidate MUST add a local dense semantic lane over eligible canonical chunks if model/backend gates pass. | T,B |
| RET-003 | MUST | Lexical and semantic parent ranks MUST fuse through a revisioned deterministic rank policy; raw BM25/cosine values MUST NOT be added. | T,B |
| RET-004 | MUST | Authorization, Project membership, privacy, time, and source availability MUST filter candidates before top-K ranking. | T,I |
| RET-005 | MUST | Every result MUST hydrate and digest-check the current canonical source; stale vectors/edges MUST be omitted and repair queued. | T |
| RET-006 | MUST | Explicit grounding MUST remain exact and bypass automatic selection. | T |
| RET-007 | MUST | Graph edges MUST be typed `authoritative`, `accepted`, or `derived`, with source and generation. | T,I |
| RET-008 | MUST | Traversal MUST be bounded by hop, fan-out, path, cycle, kind, and context budgets; launch maximum is two hops. | T |
| RET-009 | MUST | Derived/semantic adjacency MUST never masquerade as authoritative fact or relationship. | T,D |
| RET-010 | MUST | Hits and receipts MUST state lexical/semantic/hybrid/relationship origin and exact path provenance. | T,D |
| RET-011 | MUST | Missing/building/failed semantic state MUST preserve usable lexical/graph recall with an honest degraded status. | T,D |
| RET-012 | SHOULD | An optional local reranker MAY reorder the top fused eligible parents when it passes quality/latency gates; failure MUST fall back without scope or identity changes. | T,B |

### 8.4 Procedural continuity

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| PROC-001 | MUST | Procedural systems MUST expose a common `ProcedureLesson` envelope with operation family, typed trigger/payload, exact scope, provenance, lifecycle, revision, privacy, and egress. | T,I |
| PROC-002 | MUST | Each adapter MUST implement observe, propose, accept explicit correction, match, compile typed hint, report application, and remove. | T,I |
| PROC-003 | MUST | Explicit Dictation corrections MAY import as accepted lessons under their existing policy; no broader Core claim is implied. | T,D |
| PROC-004 | MUST | Model-authored Workbench JSONL observations MUST import as proposals, never accepted lessons. | T,D |
| PROC-005 | MUST | Recipe/Workbench/Dictation/Coder lessons MUST retain domain identity and MUST NOT flatten into free-form global Core. | T,I |
| PROC-006 | MUST | A procedural lesson MAY guide operation behavior but MUST NOT grant tool authority or establish a trusted target. | T |
| PROC-007 | MUST | Every applied lesson and omission MUST appear in the `ContinuityReceipt`; correction/removal affects the next eligible operation. | T,D |

### 8.5 Universal planning and use

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| PLAN-001 | MUST | One `ContinuityPlanner` MUST compose all permitted layers and serialize one immutable `ContinuityPlan`. | T,I |
| PLAN-002 | MUST | Every existing consumer in section 3.2 MUST adopt the common plan contract before release, subject to its explicit policy. | T,I |
| PLAN-003 | MUST | Planning MUST allocate system, task, explicit, Core, episodic, procedural, working, tool, and output material inside one total context budget. | T |
| PLAN-004 | MUST | Preview, reservation, admission, dispatch, result disclosure, and receipt MUST agree on exact bytes/accounting/digest. | T |
| PLAN-005 | MUST | Current authenticated input and policy MUST outrank every memory layer without implicitly mutating it. | T |
| PLAN-006 | MUST | Thread/Workbench working state MUST remain separately identified from durable accepted memory. | T,I |
| PLAN-007 | MUST | Point-of-use disclosure MUST identify every influencing layer/ref/revision and provide the appropriate correction path. | T,D,U |
| PLAN-008 | MUST | No adapter, HTTP route, MCP tool, UI, or model consumer may query tables or privately format memory prompt blocks. | T,I |
| PLAN-009 | MUST | HTTP, MCP, Web, desktop, and phone reads/reviews MUST use shared versioned schemas and application services. | T,I,D |
| PLAN-010 | MUST | Memory-induced output changes MUST produce zero authority, grant, credential, destination, or approval changes. | T |

### 8.6 Maintenance and suggestions

| ID | Pri | Requirement | Verify |
| --- | --- | --- | --- |
| MT-001 | MUST | Eligible source mutation and a monotonic source-change event MUST commit atomically. | T,I |
| MT-002 | MUST | Deterministic FTS/vector/graph/deletion reconciliation SHALL remain enabled once Continuity is built. | T |
| MT-003 | MUST | Model proposal cycles MUST require the standing `Learn from my work` authorization and a compatible assigned capability/destination. | T,D |
| MT-004 | MUST | Extraction and consolidation MUST be separate closed model contracts with frozen evidence, active/proposal revisions, policy, parser, and destination. | T,I |
| MT-005 | MUST | Model outputs MAY propose add, replace, temporal successor, alias, scope refinement, conflict, procedure, review, or no-change; they MUST NOT activate state. | T |
| MT-006 | MUST | Proposal publication and cursor advancement MUST commit atomically with CAS against frozen accepted revisions. | T |
| MT-007 | MUST | Runs MUST be resumable/idempotent and deduplicate by scope, policy, manifest, source revisions, and proposal fingerprint. | T |
| MT-008 | MUST | Suggestions MUST be clustered, capped, suppressible, expiring, non-escalating, and never overdue work. | T,D |
| MT-009 | MUST | Repeated overrides MAY increase replacement-proposal priority but MUST NOT increase truth/confidence or silently reinforce a claim. | T |
| MT-010 | MUST | Every skipped/degraded interval MUST be named, bounded, visible, and explicitly replayable. | T,D |
| MT-011 | MUST | Maintenance CPU/memory MUST yield to recording, transcription, meetings, and live interaction. | T,B |
| MT-012 | MUST | Removal/privacy changes MUST propagate across Core, proposals, procedures, vectors, graph, excerpts, and future compilation. | T |

## 9. Data model

### 9.1 Accepted Core

```text
memory_cells
  id / claim_key
  subject / predicate / qualifiers_json
  scope_project_id? / scope_recipe_id? / scope_workbench_id?
  kind                         preference | fact | convention | constraint
  compile_mode                 always | contextual
  egress_policy
  lifecycle                    active | archived | removed
  head_version / revision

memory_versions
  cell_id + version
  typed_value_json / display_text
  provenance_kind
  recorded_at / source_event_at
  valid_from / valid_until
  temporal_basis / precision / timezone
  prior_version / correction_lineage_ref

memory_proposals
  operation / structured proposed claim
  scope / target accepted revisions
  state / manifest / reason codes / expiry

memory_evidence
  proposal-or-version owner
  canonical source ref/revision/digest/span
  root_event_id / origin / assertor / privacy / egress
```

### 9.2 Source journal, genesis, and maintenance

```text
memory_source_events
  monotonic event_seq
  source ref/revision/digest
  create | update | delete
  root event / origin / eligibility / privacy / scope

memory_genesis_runs
memory_maintenance_runs
  frozen manifests, cursors, policies, assignments, receipts,
  terminal states/counts; no duplicated source or memory prose
```

### 9.3 Semantic generations

```text
embedding_generations
  lifecycle                     building | active | retired | failed
  profile/model/tokenizer/runtime artifacts and hashes
  dimension/type/distance/pooling/normalization
  query/document templates
  max tokens / chunker revision
  corpus manifest / activation evidence

semantic_memory_chunks
  chunk id / source ref/revision/digest
  ordinal / byte span / chunk digest
  kind / privacy / egress / projected memberships
  no duplicate source prose

semantic_memory_vectors
  generation + chunk primary key
  normalized float vector / vector hash

semantic_index_jobs
  idempotent upsert/delete/reconcile work lifecycle
```

Accepted contextual claims use a separate derived vector family keyed by exact
cell/version and generation. They never share authorization solely because a
vector table contains both families.

### 9.4 Graph and procedures

```text
memory_graph_edges
  source ref / target ref / edge kind
  trust class                    authoritative | accepted | derived
  provenance/generation/lifecycle

procedure_lessons
procedure_proposals
  domain-owned typed trigger and payload refs under shared lifecycle fields
```

### 9.5 Plans and use lineage

```text
continuity_plans
  immutable plan metadata, layer refs/revisions, accounting, digest

continuity_usage_refs
  plan + influencing ref/version + layer + omission/use/correction lineage
```

Use lineage stores identifiers, revisions, digests, and reasons—not duplicated
prose or a reinforcement/truth counter.

## 10. Model, vector, and ranking strategy

### 10.1 Representation capabilities

Separate admitted contracts SHALL exist for:

```text
memory.embed
memory.rerank
memory.claim_extract
memory.claim_consolidate
memory.continuity_brief
```

Embedding/reranking use dedicated typed runners, not `CanonicalPromptAdapter`.
Every vector must match exact shape, finiteness, normalization, and generation.
Receipts store IDs/digests/counts/outcomes, not vector or query/source prose.

### 10.2 Mandatory embedding bake-off

The launch default is selected on HoldSpeak fixtures, not reputation:

| Candidate | Role in bake-off |
| --- | --- |
| `intfloat/multilingual-e5-small` | Lightweight permissively licensed baseline; 384d, 512-token prefixed retrieval. |
| `google/embeddinggemma-300m` | Device-oriented multilingual/Matryoshka candidate; Gemma terms and runtime packaging require explicit review. |
| `Qwen/Qwen3-Embedding-0.6B` | Apache-2.0 quality/code challenger; runtime and Metal stability must pass. |

No model is canon until it clears section 15. Model, tokenizer, templates,
pooling, dimension, normalization, runtime, and chunker form one immutable
generation. Any change builds in parallel and atomically swaps after gates.

### 10.3 Vector backend

- First correctness backend: normalized float32 BLOBs in ordinary SQLite plus
  exact authorized NumPy cosine scan.
- Concurrent accelerator qualification: pinned `sqlite-vec` with exact-recall,
  metadata-fence, supply-chain, packaging, deletion, backup, corruption, and
  migration gates.
- `sqlite-vec` activates only when qualified and exact scan misses performance
  gates.
- No external vector daemon/service initially.
- If an extension is used, load only an allow-listed absolute artifact through
  SQLite's C API; keep SQL `load_extension()` unavailable.

### 10.4 Hybrid ranking

Lexical and dense lanes rank coherent parent refs independently. Revisioned
Reciprocal Rank Fusion is the laboratory default:

```text
score(ref) = w_lex / (k + lexical_rank)
           + w_sem / (k + semantic_rank)
```

`k=60`, equal weights, candidate counts, and reranker depth are hypotheses to
benchmark. Multiple chunks of one parent do not receive multiple votes. Typed
graph expansion follows fused seeds. A reranker may reorder only already
eligible candidates and cannot alter identity/scope/time/privacy.

## 11. Commands and interfaces

Every effect command includes `command_id`, `request_hash`, authenticated
actor, exact scope, and expected revision/absence. Same ID/hash replays the
stored result; changed bytes return `idempotency_conflict`; stale CAS returns
`stale_revision`; partial change is forbidden.

Owner application contracts:

```text
continuity.genesis.start / pause / resume / status
continuity.brief.get
memory.remember / replace / archive / restore / remove
memory.list / get / compile_preview
memory.proposals.list / accept / reject / dismiss
memory.search
memory.learning.enable / disable / status / replay
memory.health
```

HTTP and MCP are adapters over the same services. No generic
`memory(action,payload)`, raw-table, arbitrary-compile, or model activation tool
exists. Model tools may create closed proposals only.

Search extends existing `/api/memory/search` and `memory.search` compatibly with
semantic/graph provenance and degraded state. Stable canonical source refs do
not change.

## 12. Product information architecture

Memory is a first-class in-world Desk application and Dock entry. This requires
an explicit positioning amendment before UI implementation.

Primary postures:

- **Continue** — owner/Project briefs, changes, open loops, and resume actions.
- **Remembered** — accepted always/contextual Core plus procedural memory filters.
- **Recall** — hybrid search over canonical work with path provenance.
- **Review** — proposed additions, replacements, conflicts, temporal changes,
  procedures, and stale/unavailable provenance.

**Health** is an on-demand diagnostic posture containing genesis/index coverage,
generations, maintenance state, destination/egress, storage, and degraded
intervals. Normal owners never administer claim keys, vectors, bytes, watermarks,
or tables.

Project Rooms show the same Project-filtered Continue/Remembered/Recall/Review
projections. Result disclosures support correction without opening Memory.

## 13. Security, privacy, retention, and authority requirements

| ID | Requirement | Verify |
| --- | --- | --- |
| SEC-001 | Every read/rank/compile MUST authenticate principal rights and exact composite scope before material selection. | T,I |
| SEC-002 | People, profiling, secrets, credentials, private leadership material, kernel data, and unfiltered activity MUST remain excluded. | T,I |
| SEC-003 | Third-party claims remain excluded from automatic Core extraction regardless of container; owner adoption must be explicit. | T |
| SEC-004 | Vectors and derived graph edges inherit source privacy/removal classification. | T,I |
| SEC-005 | Local-only memory MUST never enter a route whose every leg is not allowed. | T |
| SEC-006 | Every model invocation, including query/document embedding, MUST be admitted and receipted. | T,I |
| SEC-007 | Generic observations MUST never serialize memory/proposal/source/query prose, vectors, or model rationale. | T,I |
| SEC-008 | Current instruction/policy outranks memory; memory creates zero authority, permission, credential, destination, or approval delta. | T |
| SEC-009 | Direct, indirect, slow-drip, cross-scope, post-consolidation, and tool-target poisoning MUST fail harm gates. | T,B |
| SEC-010 | Source delete/privacy change MUST make derived material synchronously ineligible and asynchronously purge it. | T |
| SEC-011 | Model/tokenizer/runtime artifacts MUST be checksum pinned and acquired through Model Library; production MUST NOT execute remote model code. | T,I |
| SEC-012 | Strong Forget MUST NOT be claimed for existing immutable plaintext snapshots/backups/provider copies. | T,D |

### 13.1 Prospective strong forgetting prerequisite

Before corpus embedding or accepted memory enters model-bearing admitted
payloads, HoldSpeak SHALL resolve the owner-held retention amendment:

- retain immutable operation metadata, hashes, IDs, and terminal receipts;
- encrypt private admitted material under per-operation data keys;
- retain exact lineage from memory/source revisions to operations;
- cryptographically shred affected keys on strong Forget;
- accept loss of exact plaintext replay for those operations; and
- disclose provider, backup, and legacy-plaintext limits separately.

Until then, **Remove from Core** purges Continuity-owned live text/indexes and
prevents future use, but does not promise universal historical erasure.

## 14. Reliability, performance, and operations requirements

| ID | Requirement | Gate |
| --- | --- | ---: |
| NFR-001 | Always-Core compile is local/model-free/network-free and p95 <20 ms for 100 eligible claims. | B |
| NFR-002 | Continuity planning adds p95 <50 ms excluding enabled model retrieval operations. | B |
| NFR-003 | Warm local query embedding p95 <150 ms on reference Mac and <300 ms on Linux reference. | B |
| NFR-004 | Hybrid retrieval excluding hydration p95 <250 ms at 50k chunks. | B |
| NFR-005 | Initial Continuity Brief after installed model appears within 3 minutes; useful lexical brief appears sooner when possible. | B,D |
| NFR-006 | Index/maintenance work is pausable/resumable and yields CPU/memory to live audio and interaction. | T,B |
| NFR-007 | Missing/corrupt semantic/reranker/model state preserves lexical/graph and names degradation. | T,D |
| NFR-008 | All compilation, fusion, graph traversal, plan serialization, and receipts are deterministic for frozen inputs. | T |
| NFR-009 | Schema changes are additive, backed up, restart-safe, and all derived indexes rebuild from canonical truth. | T,I |
| NFR-010 | Disk estimates include models, tokenizers, generation overlap, chunks/vectors, graph, SQLite overhead, and rollback window before acquisition. | T,D |
| NFR-011 | Maintenance replay after crash is idempotent in 100% of fixtures and never wedges a cursor. | T |
| NFR-012 | Suggestion presentation is capped initially at five unsolicited items per active Project/week after genesis. | T,D |

## 15. Evaluation and model/backend gates

### 15.1 Retrieval corpus

The versioned corpus SHALL include exact jargon, no-keyword paraphrase,
multilingual/cross-lingual queries used by the owner, code/repository terms,
hard negatives, temporal updates, Project/Recipe/Workbench scope, source-kind
balance, stale/deleted data, poisoning, and excluded private material.

Compare:

1. Implemented FTS + typed graph control.
2. Each embedding candidate with fused retrieval + graph.
3. Qualified optional reranker over the best fused candidate set.

### 15.2 Wow gates

| Outcome | Release gate |
| --- | ---: |
| Source-backed brief statements | 100% |
| Fabricated brief statements | 0 |
| Owner-rated useful/accurate brief statements | ≥8/10 |
| Initial proposal accepted or accepted after edit | ≥80% |
| Direct acceptance without edit | ≥60% |
| Initial ten-item review | median <2 minutes |
| Explicit relevant `always` claim use | 100% |
| Contextual accepted-claim Recall@5 | ≥90% |
| Preference/constraint adherence | ≥90% and ≥25-point memory-off improvement |
| Correction reflected next invocation | 100% across eligible consumers |
| Semantic no-keyword Recall@10 | ≥15 points over lexical control |
| Overall MRR@10 | no regression >2 points |
| Agent/task success with correct memory | ≥15-point memory-off improvement |
| Explicit grounding quality | no regression >2 points |
| Seven-day return: find state/open loop | <60 seconds |

### 15.3 Harm gates

All are zero-tolerance unless stated:

- Cross-principal/Project/Recipe/Workbench/People leakage: 0.
- Local-only material sent to disallowed destination: 0.
- Automatic accepted-memory promotion/rewrite/deletion: 0.
- Memory-derived authority, unauthorized effect, or trusted-target increase: 0.
- Stale/deleted vector or invalidated structured memory use: 0.
- Poisoned proposal automatically activated: 0.
- Poisoned memory changes system/tool policy: 0.
- Context overflow/hash mismatch: 0.
- Irreducible conflict silently resolved: 0.
- Generic log containing protected prose/vector: 0.
- Personalized safety regression: no more than 2 points.

The extraction model MUST NOT be its sole evaluator. Run model/version matrices
and no-memory/correct/stale/poisoned counterfactuals.

## 16. Acceptance scenarios

### A. Existing-work genesis

Build from a real eligible corpus while writes continue. Prove backfill/live
cursor handoff, progress, exclusions, restart, atomic vector activation,
source-backed brief, bounded proposal digest, and no accepted inferred claims.

### B. Whole-ecosystem correction

Accept one owner preference and Project fact. Prove identical eligible versions
across Ask, Thought, Chat, Agent plan, Recipe, Workflow, Workbench, and Coder.
Correct at one result; every next eligible consumer uses only the new revision.

### C. Contextual accepted memory

Accept a contextual claim. Ask with no shared words. Prove exact scope/time/egress
filtering precedes semantic selection, the claim is retrieved, and similarity
does not alter same-key precedence.

### D. Semantic and two-hop continuity

Recover differently worded Meeting evidence, its accepted Decision, related
Thread, and open Action through fused direct recall plus bounded typed paths.
Every source/path opens canonically.

### E. Procedural bridges

Import an explicit Dictation correction as accepted procedural memory and a
Workbench model observation as a proposal. Prove typed matching, application,
disclosure, correction, and no authority change.

### F. Composite scope

Exercise owner, Project, Recipe, Workbench, and combined same-key claims. Prove
exact matching, most-specific shadowing, no leak, and stable receipt ordering.

### G. Living cycle

Enable Learn from my work. Produce a temporal successor, contradiction,
repeated correction, procedure suggestion, expired proposal, crash, replay, and
calm zero state. Prove no autonomous activation.

### H. Poisoned/stale agent action

Feed stale and poisoned accepted/contextual/procedural memory into agent planning
and a gated tool-turn fixture. Prove no grant/target/approval delta and no
unauthorized effect.

### I. Degraded retrieval

Remove/corrupt the active vector/reranker/model runtime. Prove uninterrupted
lexical/graph service, honest state, repair, and no mixed generation.

### J. Removal and retention truth

Remove a unique sentinel across Core/proposals/procedures/vector/graph/search and
future compilation. Inspect generic logs and live stores. Verify historical
immutable/provider/backup limitations are stated rather than falsely erased.

### K. Seven-day owner ritual

Capture real work, leave for seven days, return through Continue, reconstruct
one Project in under a minute, resume useful work, correct one stale belief, and
obtain the owner's live verdict across desktop and phone screenshots.

## 17. Product release train

These are hidden construction gates under one owner-facing Continuity release.

### CF-0 — Contracts and retention

- Ratify encrypted/shreddable admitted-material policy.
- Land source journal, structured claims, composite scope, procedures, graph,
  embedding generations, continuity policy, and immutable plan schemas.
- Establish redacted observation and application-service contracts.

### CF-1 — Genesis and retrieval

- Build all eligible source adapters, backfill/live handoff, FTS reconciliation,
  vector generations, graph projection, procedural import, and model bake-off.
- Produce source-backed briefs and bounded proposals behind flags.

### CF-2 — Universal shadow planning

- Every eligible consumer builds but does not inject a `ContinuityPlan`.
- Compare current versus planned material and prove policy, scope, destination,
  accounting, latency, and receipt parity.

### CF-3 — Closed-loop dogfood

- Enable accepted always/contextual Core, hybrid episodic, procedural hints,
  correction, Review, and owner-authorized maintenance together.
- Run all security, crash, removal, and wrong-memory campaigns.

### CF-4 — Product and cross-device proof

- Ship Memory application postures, contextual result disclosures, Project Room
  projection, HTTP/MCP parity, desktop/phone screenshots, and accessibility.
- Run real genesis and seven-day owner ritual.

### CF-5 — Owner-facing release

Release only after sections 15–16 pass and the owner's live verdict approves.
Flags may permit rollback; no preceding gate may claim ecosystem-wide memory.

## 18. Traceability

| Product promise | Architecture | Requirements | Acceptance |
| --- | --- | --- | --- |
| Build from existing work | AD-CF-009/010 | GEN-001–010, MT-001–007 | A, G |
| Living accepted memory | AD-CF-005/006/013 | CORE-001–012 | B, C, F, G |
| Conceptual and related recall | AD-CF-003/007–009/012 | RET-001–012 | C, D, I |
| HoldSpeak-wide continuity | AD-CF-004/011 | PLAN-001–010, PROC-001–007 | B, E, F |
| Inspectable/correctable use | AD-CF-004/014 | CORE-004/011/012, PLAN-007/009 | B, J, K |
| Safe learning cycle | AD-CF-013 | MT-001–012, SEC-001–012 | G, H, J |
| Immediate impact | AD-CF-002/010/014 | GEN-007–010, NFR-005/012 | A, K |
| Proof over claim | all | sections 14–15 | A–K |

## 19. Implementation entry and exit criteria

Implementation may begin only after owner ratification of:

1. this integrated product/release scope;
2. the prospective encrypted/shreddable retention amendment;
3. the first-class Memory application positioning amendment;
4. the mandatory embedding bake-off and model-license posture; and
5. initial hardware/reference-corpus definitions for quantitative gates.

Planning then SHALL produce story-level requirement mappings, additive schema
and rollback plans, capability-policy census changes, real-model benchmark
harnesses, cross-consumer shadow evidence, screenshot scripts, and migration
receipts.

The program exits only at CF-5. Passing tests, landing code, building one index,
or demonstrating Ask is not completion.

## 20. Non-goals

- Automatic activation, rewrite, demotion, or deletion of accepted memory.
- A psychological/person/relationship profile or surveillance system.
- Memory-derived permission, credentials, trusted targets, or effects.
- Replacing canonical Notes, Projects, Meetings, Decisions, Threads, Knowledge,
  Workbench, Dictation correction, or People stores.
- An external vector database for the first single-owner release.
- Cloud embedding by default.
- Similarity-based truth, conflict, scope, or claim identity.
- Raw assistant/model prose as evidence.
- Cross-device synchronization before encryption and concurrent conflict design.
- Universal historical Forget under current immutable plaintext retention.
- Calling any partial construction milestone “integrated Continuity.”
