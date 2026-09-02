# Core Memory design council record

**Date:** 2026-09-01

**Status:** Design record; no implementation authorization

**Subsequent normative integration detail:**
[HoldSpeak Continuity SRS](CORE_MEMORY_INTEGRATION_SRS.md)

> This record preserves the original conservative sitting and the later
> reopened sitting. The reopened verdict supersedes the original release-scope
> recommendation while retaining its constitutional safety findings.

## Nature of the council

This was a simulated design exercise, not a meeting with or impersonation of
the named historical figures. The seats used design lenses associated with
great personal-computing work: small powerful primitives, inspectable systems,
humane interaction, ruthless product simplification, and an independent
AI-memory/security review.

The council comprised three working seats:

- **Systems seat** — resource model, concurrency, crash recovery, integration
  waist, and composability; inspired by the practical elegance of the original
  Amiga systems team, including Jay Miner, R.J. Mical, and Dale Luck.
- **Product seat** — owner experience, naming, discoverability, and deletion of
  unnecessary product surface; informed by Steve Jobs's publicly associated
  insistence on end-to-end simplicity and humane product focus.
- **AI-memory seat** — temporal/evidence semantics, consolidation science,
  privacy, poisoning, evaluation, and forgetting.

No participant claimed to speak for any real person.

## Question put to the council

How should HoldSpeak gain a maintained Core Memory that grows and is pruned over
time without becoming an agent-owned profile, an authority store, an opaque
vector database, or another application silo?

## Unanimous conclusions

1. **Core Memory is an OS primitive, not an app world.** Its narrow waist is a
   revisioned `MemoryCell` plus one pure `MemoryCompiler`.
2. **The owner owns active Core.** Explicit owner commands may activate;
   inferred/model material remains a proposal forever until accepted.
3. **Memory never grants authority.** It may guide output but cannot approve,
   send, choose credentials, relax egress, or alter grants.
4. **V1 is manual and small.** Owner and Project scope, explicit Remember, one
   consumer, no extraction, no automatic cycle.
5. **The product language is ordinary.** Remember, Remembered, Suggestions,
   Search, Stop using, and Remove from Core. Internal storage vocabulary stays
   out of the main interaction.
6. **Correction belongs at the point of use.** Every result that relies on Core
   must disclose the exact revisions and offer correction/removal there.
7. **One complete context allocator is required.** Core cannot have an isolated
   budget while explicit and episodic evidence independently overfill prompts.
8. **Cyclic maintenance proposes; it does not govern.** It can discover,
   compare, expire suggestions, and raise review attention, but never silently
   promote, rewrite, demote, or delete active Core.

## Structural corrections to the first draft

| First-draft idea | Council resolution |
| --- | --- |
| Candidate as a state of a Core entry | Separate accepted `MemoryCell`/versions from `MemoryProposal`. |
| Free-form text plus semantic duplicate detection | Require an atomic scope-local `claim_key`; fuzzy similarity is review assistance only. |
| Owner/Project/Recipe/Workbench in V1 | Implement owner and exact Project only. Recipe/Workbench remain procedural bridges. |
| `procedure` as a Core kind | Keep procedures in procedural memory. |
| Inferred constraints in first extraction | Defer; constraints have a larger action-shaping/poisoning surface. |
| Pinning in V1 | Cut; active memory never auto-deletes and pinning must not weight truth. |
| 8,192-byte fixed Core budget | Reject; calibrate complete prompts and provisionally test 2/3/4 KB ceilings. |
| Candidate 30d, fact 90d, preference 180d as policy | Treat proposal expiry as an experiment; reject generic fact/preference clocks. |
| Timestamp-based watermark | Add a transactional monotonic source-change journal and adapter/scope cursors. |
| Thread compaction as special trigger | Treat compaction as an ordinary eligible canonical event. |
| Model-generated rationale persisted for review | Store reason codes and exact evidence spans, not secret-duplicating prose. |
| One standalone Memory app with Core/Recall/Review tabs | Use a search-reachable Memory lens: Remembered + Search; Suggestions is a state/count. |
| “Desk memory” for attention | Rename to Attention; retain System Shade as the internal surface name. |
| Generic Forget | Use truthful V1 Remove from Core and hold universal forgetting for owner ratification. |

## The minimal architecture selected

```text
authenticated Remember command
              │
              v
      MemoryCell + immutable version
              │
              v
 pure destination-aware MemoryCompiler
              │
              v
 shared complete context allocator
              │
              v
 eligible admitted inference + exact receipt

canonical source-change journal          (later)
              │
              v
 owner-triggered Suggest memories        (later)
              │
              v
 proposal + exact evidence ──owner accepts──► MemoryCell version
```

The compiler accepts principal, capability, destination, exact scope vector,
Project membership, `as_of`, policy revision, and total context grant. It emits
one canonical frozen artifact containing exact included revisions, shadowing,
omissions, serialized bytes, accounting revision, and digest.

## Council resolutions on the eight design decisions

1. **Automatic learning:** Manual Core on. Suggestions off. Begin later with
   owner-selected sources and owner-triggered runs; background thresholds must
   earn their way through measured quality and review burden.
2. **Initial scopes:** `owner:local` and exact Project only.
3. **Promotion:** Explicit authenticated owner writes may activate immediately.
   Every inferred/model proposal requires review regardless of confidence,
   recurrence, or control posture.
4. **People boundary:** Raw People and third-party personal claims are excluded
   from extraction even if copied into otherwise eligible containers.
5. **Model destination:** Local deterministic maintenance; assigned capability,
   visible destination, and per-entry egress for any model use—including
   ordinary inference, not only consolidation.
6. **Retention:** Active entries never auto-delete. Archive is reversible.
   Proposal expiry is disclosed and calibrated, not a universal truth clock.
7. **Context budget:** Reject 8,192 bytes. Test complete-prompt Core envelopes
   and ratify the smallest useful grant. 2,048/3,072/4,096 UTF-8 bytes are
   provisional ceilings for 8K/16K/32K+ dogfood, not canon.
8. **Product IA:** No top-level fifth app. One Memory primitive/lens,
   Remembered + Search, optional Suggestions state, and existing Attention.

## Important dissent that changed the result

The systems/product seats initially considered ordinary live-store Forget
sufficient if backup limitations were disclosed. The AI-memory review checked
the actual HoldSpeak persistence contract and found that admitted prompt
material is copied into immutable `inference_adoption_material_snapshots` rows.
Therefore a Core-only purge cannot erase historical prompt copies.

The final council adopted the stricter wording:

- **Remove from Core** purges Core-owned text and prevents future Core use.
- It does not claim to erase canonical sources, old immutable admitted
  payloads, provider retention, or backups.
- Stronger Forget requires a cross-cutting encrypted-payload/crypto-shredding
  design and explicit owner ratification because exact replay would be lost.

This was the council's clearest example of design improving through disagreement
rather than averaging opinions.

## Risks the council refuses to hand-wave

- Free-form contradiction detection without stable claim identity.
- Temporal hallucination or conflating `recorded_at` with when a fact is true.
- Treating repeated derived copies as independent corroboration.
- Sending local-only memory to an ordinary cloud inference assignment.
- Prompt injection hidden in copied source material or accepted memory.
- Serializing memory bodies into generic observability logs.
- Budgeting Core separately while episodic/full-body grounding crowds out the
  current task.
- Calling proposal acceptance “truth,” or using recall count as confidence.
- Making Suggestions an overdue-work inbox.
- Promising erasure that current immutable payload storage cannot deliver.

## Release sequence recommended

1. **Manual Core laboratory** — one consumer, owner/Project, exact contracts.
2. **Complete prompt waist** — every eligible consumer uses one allocator and
   compiler artifact; no learning yet.
3. **On-demand suggestion laboratory** — owner-selected sources, exact evidence,
   measured poisoning/privacy/review burden.
4. **Cyclic maintenance** — only after measured gates; no active autonomous
   mutation.
5. **Specialized bridges** — Recipe, Workbench, Dictation, and procedural memory
   only after separate evaluation.

## Held owner decisions

Only two questions remain intentionally open:

1. Should HoldSpeak introduce per-operation encryption and cryptographic
   shredding so a strong Forget can sacrifice exact replay of affected prompts,
   and what happens to legacy plaintext snapshots?
2. Which smallest measured Core context envelope creates useful task improvement
   without crowding out current work and explicit/episodic grounding?

Everything else above is the council's recommended design baseline. No schema,
route, prompt, UI, migration, commit, push, or PR is authorized by this record.

The later integration SRS preserves this baseline and resolves a question that
was outside the initial council brief: Core itself remains exact and
non-vectorized, while optional embeddings are confined to derived episodic
recall and possible human-review assistance. They never decide Core identity,
truth, conflict, promotion, or compilation.

## Reopened sitting — transformative Continuity mandate

The owner rejected the optimization toward the smallest safe primitive and
reconvened the same independent design lenses with this corrected question:

> Design the most transformative memory system HoldSpeak can responsibly ship,
> not the smallest primitive it can safely implement.

All three seats independently rejected the prior release posture. They agreed
that manual Core in Ask is a valuable hidden engineering checkpoint but an
inadequate product release.

### Reopened unanimous verdict

The first owner-facing release should be a **Continuity** program containing:

- one owner-authorized genesis over eligible existing canonical work;
- source-backed owner/Project resume briefs before claim acceptance;
- bounded structured claim proposals and batch selection;
- accepted standing and contextually retrieved memory;
- lexical, dense-semantic, and typed-relationship episodic recall;
- a universal frozen plan across all eligible inference consumers;
- point-of-use disclosure and correction;
- typed Dictation/Workbench/Recipe procedural bridges;
- owner-authorized ongoing extraction, conflict, temporal, and consolidation
  proposals; and
- an integrated real-corpus/seven-day-return proof rather than component demos.

They unanimously retained:

- owner activation for every inferred accepted-memory/behavior change;
- no autonomous rewrite, promotion, demotion, or accepted deletion;
- no memory-derived authority, credentials, destinations, grants, or approval;
- exact principal/scope/time/privacy/egress filtering;
- categorical People, profiling, secret, kernel, and failed-output exclusions;
- semantic similarity as discovery only, never truth/conflict/scope/precedence;
- Article-XI admission/receipts for all model work, including embeddings; and
- truthful removal limitations under immutable plaintext history/backups.

### Dissent and SRS resolution

| Question | Product lens | Systems lens | AI-memory lens | Integrated SRS resolution |
| --- | --- | --- | --- | --- |
| Accepted memory scale | Compact Core within expansive Continuity | Bounded resident set with residency control | Larger accepted library: `always` + `contextual` | Accept `always` + `contextual`; similarity locates accepted contextual claims only after exact eligibility. |
| Scope | Owner/Project Core; procedural bridges | Owner/Project/Recipe/Workbench vector | Composite optional Project/Recipe/Workbench dimensions | Accept composite dimensions; specialized procedures remain typed domain memory. |
| Product home | First-class Dock application | Powerful OS lens with Health | Unified Memory experience | First-class in-world Memory app; Health disclosed diagnostically; Project/result projections reuse services. |
| Embedding model | Measured bake-off | E5/Qwen/backend gates | Add EmbeddingGemma; consider it device reference | Mandatory E5/EmbeddingGemma/Qwen bake-off; no unmeasured default. |
| Reranker | Not central | Not required initially | Benchmark optional local reranker | Optional only if quality/latency gates pass; fused retrieval remains fallback. |
| Agent tool turns | Keep Core away initially | Enable only after adversarial gates | Contextual use after stale/poisoned action gates | `none` until gates; later contextual only, with canonical targets and no authority delta. |

The [integrated SRS](CORE_MEMORY_INTEGRATION_SRS.md) is normative where the
reopened sitting differs from the original conservative release advice.
