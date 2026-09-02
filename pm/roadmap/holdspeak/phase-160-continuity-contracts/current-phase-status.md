# Phase 160 — Continuity Contracts (CF-0)

**Last updated:** 2026-09-01 — COUNCIL-RATIFIED CHARTER 0/14. Systems,
AI-memory, and product reviews report zero remaining severity-1/2 story
blockers. HS-160-01 is still intentionally blocked on explicit owner
ratification; all runtime stories remain backlog. No Continuity runtime,
embedding model, vector store, or released Memory application is claimed.

## Goal

Turn the council-cleared Continuity CF-0 contract into the smallest complete,
testable substrate on which HoldSpeak can safely build Core Memory: one domain
grammar, command boundary, source journal, privacy barrier, plan waist,
derivative registries, total capability census, bounded shadow integrations,
dev-only product contract shell, and local proof ledger. CF-0 proves structure,
safety, rollback, and integration seams. It deliberately does not prove recall
quality or ship memory into owner-visible model context.

Authority is the parent and child SRS suite:
[`CORE_MEMORY_INTEGRATION_SRS.md`](../../../../docs/internal/CORE_MEMORY_INTEGRATION_SRS.md)
and
[`CONTINUITY_CF0_CONTRACT_SRS.md`](../../../../docs/internal/CONTINUITY_CF0_CONTRACT_SRS.md).
The phase also answers to the
[`CONSTITUTION.md`](../../../../docs/internal/CONSTITUTION.md) and preserves the
existing relationship-aware memory contract in
[`RELATIONSHIP_AWARE_MEMORY.md`](../../../../docs/RELATIONSHIP_AWARE_MEMORY.md).

## Scope

- **In:** the fourteen one-story/one-PR units below, derived from twelve CF-0
  work packages; ratified owner amendments;
  additive schema and migrations; typed command and result contracts; source
  outbox/journal; encrypted private-material handling; deterministic
  `ContinuityPlan@1`; procedure/graph/embedding-generation foundations; a
  generated capability/source census; shadow-only representative adapters;
  persisted development product fixtures; local proof and rollback machinery.
- **Out:** selecting or downloading a production embedding/reranking model;
  measuring semantic recall quality; production vector indexing; injecting a
  Continuity plan into any model prompt; automatic claim acceptance; learned
  procedure execution; public Memory-app release; native-phone authority; CF-1
  genesis, CF-2 universal runtime adoption, and CF-3/CF-4 product proof.
- **Delivery law:** one story is one implementation PR. A story becomes `done`
  only with its own evidence file. No `final-summary.md` exists until all fourteen
  stories and every exit gate are closed. A close-campaign defect reopens its
  owning story or receives a numbered corrective story/PR; HS-160-14 remains a
  campaign/evidence/report PR rather than a product-fix bundle.
- **Charter bundle:** this planning commit alone creates and cross-links all
  fourteen backlog/blocked contracts atomically; it changes no story to `done`,
  ships no runtime, and creates no evidence. Implementation remains one PR per
  story under the delivery law above.

## Exit criteria (evidence required)

- [ ] **Authority (HS-160-01):** every decision in CF-0 §14.5 has an explicit
  owner verdict and amendment reference; no constitutional contradiction or
  umbrella approval hides an unresolved choice.
- [ ] **Schema (HS-160-02/04/06/07/09):** clean and representative upgraded
  databases satisfy constraints, state machines, foreign keys, backup law,
  encrypted-payload law, and additive rollback.
- [ ] **Commands (HS-160-03):** replay, conflicting replay, concurrent CAS,
  multi-precondition conflict, timeout-after-commit, and crash recovery have
  deterministic typed outcomes.
- [ ] **Plans (HS-160-05):** identical frozen inputs and policy yield
  byte-identical `ContinuityPlan@1` artifacts and tokenizer-exact budgets;
  capability differences remain explicit; no plan reaches production context.
- [ ] **Census (HS-160-10):** every built-in, internal, future, plugin, and
  Coder capability/source identifier has an explicit policy and CI fails on
  registry drift.
- [ ] **Sources and derivatives (HS-160-04/09):** fixtures prove revision,
  deletion, privacy, scope, staleness, reconciliation, generation fencing,
  graph fencing, and purge recovery without storing source prose in the
  journal.
- [ ] **Privacy and removal (HS-160-06/07/08):** canary scans find no private value,
  query, vector, prompt, or path in public stores/logs/receipts; Remove blocks
  admission immediately and Forget eventually reaches zero authorized
  derivatives through injected crashes.
- [ ] **Compatibility and bounded adoption (HS-160-11):** Ask, Thread, Recipe,
  Workflow, Workbench, Coder, HTTP, and MCP contracts remain green with flags
  off; representative adapters can construct—but never inject—shadow plans.
- [ ] **Product contract (HS-160-12):** 1440×900 and 393×852 persisted,
  watermarked fixtures cover every required state, consent, parity,
  accessibility, and canonical deep-link contract without implying real
  genesis or phone authority.
- [ ] **Proof and rollback (HS-160-13/14):** the local proof ledger maps every
  requirement to sanitized evidence; disabling CF-0 writers/adapters restores
  the pre-CF-0 runtime path without destructive down-migration or data loss.
- [ ] **Close (HS-160-14):** full structural/fault matrix, focused legacy suite,
  post-migration doctor, council review, and owner verdict contain no open
  severity-1/2 authority, privacy, corruption, deletion, or cross-scope defect.

## Story status

| ID | Story | Status | Depends on | Story file | Evidence |
| --- | --- | --- | --- | --- | --- |
| HS-160-01 | The owner canon | blocked | — | [story-01](./story-01-the-owner-canon.md) | not created |
| HS-160-02 | The domain grammar | backlog | 01 | [story-02](./story-02-the-domain-grammar.md) | not created |
| HS-160-03 | The command core | backlog | 02, 04 | [story-03](./story-03-the-command-core.md) | not created |
| HS-160-04 | The source spine | backlog | 01, 02 | [story-04](./story-04-the-source-spine.md) | not created |
| HS-160-05 | The plan waist | backlog | 02, 03, 06 | [story-05](./story-05-the-plan-waist.md) | not created |
| HS-160-06 | The private-material vault | backlog | 01, 02, 03 | [story-06](./story-06-the-private-material-vault.md) | not created |
| HS-160-07 | The private-material cutover | backlog | 04, 05, 06 | [story-07](./story-07-the-private-material-cutover.md) | not created |
| HS-160-08 | Remove and Forget | backlog | 03, 06, 07, 09 | [story-08](./story-08-remove-and-forget.md) | not created |
| HS-160-09 | The derived foundations | backlog | 02, 03, 04, 06 | [story-09](./story-09-the-derived-foundations.md) | not created |
| HS-160-10 | The total policy census | backlog | 01, 04, 05, 09 | [story-10](./story-10-the-total-policy-census.md) | not created |
| HS-160-11 | Bounded shadow adoption | backlog | 03, 04, 05, 07, 08, 10 | [story-11](./story-11-bounded-shadow-adoption.md) | not created |
| HS-160-12 | The Memory contract shell | backlog | 01, 02, 03, 08, 10 | [story-12](./story-12-the-memory-contract-shell.md) | not created |
| HS-160-13 | The local proof harness | backlog | 03–12 | [story-13](./story-13-the-local-proof-harness.md) | not created |
| HS-160-14 | The CF-0 close | backlog | 01–13 | [story-14](./story-14-the-cf0-close.md) | not created |

## Where we are

CHARTERED 2026-09-01 from the final council-cleared CF-0 SRS. Phase 109, The
Long Memory, is already closed and remains immutable; Phase 160 is the new
execution ledger. The relationship-aware RAGFlow-derived seam exists and its
focused tests were green at charter time, but it is not Continuity Core and is
not represented as one. The phase begins at an intentional authority gate:
HS-160-01 records owner decisions before a migration or private writer may
ship. Later stories may be designed and reviewed in parallel, but no runtime
story may merge past an unresolved governing decision it consumes.

The CF-0 boundary is unusually strict. Fake deterministic runners are required
to prove schemas and plans without silently making a model choice. Real
embedding generation, vector retrieval, reranking, and quality thresholds are
CF-1 work derived from CF-0's generation and policy contracts. Shadow adapters
must stop before context injection. Product fixtures must be visibly marked
`CF-0 fixture — no owner data/model behavior`.

## Council story review

The existing systems, AI-memory, and product council reviewed the stories—not
only the SRS—in two corrective rounds on 2026-09-01 and each returned
**RATIFY** with zero remaining severity-1/2 blockers. The review caused material
changes before charter close:

- accepted Core scope now refuses Person/People, speaker, Thread, and
  device/private pseudo-scopes; Thread is plan working scope only;
- source outbox ownership precedes the command transaction, retryable events
  block their adapter cursor, and canonical hydration stays with source owners;
- preview/shadow validation cannot mint kernel admission or injectable text;
- the privacy work package became three independently mergeable PRs: vault/key
  saga, encrypted resolver/cutover, and Remove/Forget;
- fake vectors/generations remain isolated test/dev fixtures, production
  generation tables stay empty, and all five sealed derivative capabilities
  include `memory.continuity_brief@1`;
- declared capability policy is separate from runtime adoption; the census says
  `planned_shadow` until HS-160-11 ships all four adapters and fences atomically;
- Forget preserves owner-ratified content-free immutable attestations while
  purging private payload/usage lineage; and
- rollback distinguishes current-binary flags-off behavior through v2 from an
  old-binary canonical-only degraded reopen that blocks model-bearing and
  plaintext-write paths.

Council ratification does not answer the owner decisions in HS-160-01 and does
not authorize implementation past that gate.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Authority is inferred from prose | high | HS-160-01 requires one verdict per §14.5 row | any runtime PR consumes an unresolved owner decision |
| Private material leaks through migration or telemetry | medium | encrypted v2 resolver, canary corpus, storage/WAL/log/backup scans | any canary appears outside the encrypted payload boundary |
| Source capture duplicates or loses revisions | medium | transactional outbox, idempotent observation identity, reconciliation | cursor advances without durable disposition or two live writers exist |
| Planner forks across consumers | medium | one canonical plan artifact and digest; generated census fence | a consumer builds context without the canonical planner |
| CF-0 fixture is mistaken for shipped memory | medium | dev gate, watermark, no production service wiring | unwatermarked fixture or production route exposes fake state |
| Work expands into CF-1 model/vector selection | medium | generation contracts use deterministic fakes only | a model download, production vector write, or recall-quality claim enters CF-0 |
| Rollback requires deleting owner data | low | additive dormant schema; stop writers before old-code reopen | rollback instructions require destructive down-migration |

## Decisions made

- Phase 160 is the execution home; the completed Phase 109 is not reopened.
- The twelve CF0 work packages derive fourteen PR-sized stories. CF0-06 is an
  ordered three-PR privacy train (HS-160-06/07/08); the other packages each map
  to one story. Numbering is traceability; the dependency graph controls order.
- Owner amendments are a merge gate, not a ceremonial close artifact.
- CF-0 constructs shadow plans only; no plan is injected into model context.
- A vector store and embedding model are intentionally not selected in CF-0;
  CF-0 defines the generation, dimensionality, lineage, route, and failure
  contracts from which CF-1 can make and measure that choice.
- Evidence files are write-once shipping artifacts and therefore do not exist
  at planning time.

## Decisions deferred

- Every owner verdict enumerated by CF-0 §14.5, owned by HS-160-01.
- Actual production embedding/reranking models and backend, concrete admitted
  licenses, performance hardware, evaluation corpus, and quality thresholds,
  owned by CF-1 after CF-0 ratifies only the license-admission law, structural
  fixture environments, and sanitized-corpus policy.
- Production product release, native-phone execution authority, learning
  automation, and universal runtime rollout, owned by CF-2 through CF-4.
