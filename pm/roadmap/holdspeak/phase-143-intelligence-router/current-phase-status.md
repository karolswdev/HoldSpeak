# Phase 143 - The Intelligence Router

**Last updated:** 2026-08-22.

## Goal

Make every HoldSpeak AI workload resolve through one server-owned capability
route to a reusable model profile, with ordered qualified fallbacks, frozen
execution truth, and one delightful owner system: Model Library plus
Assignments.

## Scope

- **In:** Canonical capability registry; immutable model-profile revisions and
  hub-local bindings; ordered capability assignments; frozen route plans;
  durable retry/fallback control; migration of Thoughts, writing, speech,
  meetings, background, tools, agents, Workbenches, Recipes, and workflows;
  HTTP/MCP parity; Model Library, Providers, and Assignments owner surfaces;
  restart/privacy/sync/accessibility/chaos proof.
- **Out:** A second inference gateway or deployment-revision registry; ambient
  model access to owner MCP; silent model installation/assignment; browser-owned
  compatibility or retry law; synced active routes/bindings; hidden retries;
  fallback after unknown physical/effect completion.

## Exit criteria (evidence required)

- [ ] Every production inference call site belongs to one versioned capability.
- [ ] Every execution freezes one immutable route plan before first egress.
- [ ] Every physical generation remains a separately admitted `InferenceRunner`
  / `inference.invoke@1` child.
- [ ] Ordered fallback advances only for a closed eligible disposition and its
  receipt explains every leg, child, boundary, and terminal outcome.
- [ ] Config/profile/subject legacy pointers have one-way migrations and no
  competing authority remains after each family crosses.
- [ ] Adding/downloading/connecting a model changes zero assignments.
- [ ] Model Library and bounded Assignments glass pass at 1440, 393, and 200%
  zoom with keyboard/screen-reader/reduced-motion proof.
- [ ] HTTP/MCP parity, OWNER boundary, hub-local sync, restart, privacy, schema,
  API inventory, one-path census, full tests, and production build are green.
- [ ] All kill criteria in `assets/architecture-contract.md` have production-path
  evidence in Story 14's write-once ledger.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSEGHS001HS104-143-01 | Capability and Route Census | done | [story-01-capability-route-census](./story-01-capability-route-census.md) | [evidence](./evidence-story-01.md) |
| HSEGHS001HS104-143-02 | Canonical Capability Registry | done | [story-02-canonical-capability-registry](./story-02-canonical-capability-registry.md) | [evidence](./evidence-story-02.md) |
| HSEGHS001HS104-143-03 | Reusable Model Profile Authority | done | [story-03-reusable-model-profile-authority](./story-03-reusable-model-profile-authority.md) | [evidence](./evidence-story-03.md) |
| HSEGHS001HS104-143-04 | Assignment Store and Resolver | done | [story-04-assignment-store-resolver](./story-04-assignment-store-resolver.md) | [evidence](./evidence-story-04.md) |
| HSEGHS001HS104-143-05 | Frozen Route Plans | done | [story-05-frozen-route-plans](./story-05-frozen-route-plans.md) | [evidence](./evidence-story-05.md) |
| HSEGHS001HS104-143-06 | Fallback Controller and Failure Law | done | [story-06-fallback-controller-failure-law](./story-06-fallback-controller-failure-law.md) | [evidence](./evidence-story-06.md) |
| HSEGHS001HS104-143-07 | Thoughts Ask and Writing Adoption | done | [story-07-thoughts-ask-writing-adoption](./story-07-thoughts-ask-writing-adoption.md) | [evidence](./evidence-story-07.md) |
| HSEGHS001HS104-143-08 | Meetings Speech and Background Adoption | in-progress | [story-08-meetings-speech-background-adoption](./story-08-meetings-speech-background-adoption.md) | - |
| HSEGHS001HS104-143-09 | Tool Capability Foundation and Safe Routing | backlog | [story-09-tool-turn-routing-safe-fallback](./story-09-tool-turn-routing-safe-fallback.md) | - |
| HSEGHS001HS104-143-10 | Agents Workbenches and Recipes Adoption | backlog | [story-10-agents-workbenches-recipes-adoption](./story-10-agents-workbenches-recipes-adoption.md) | - |
| HSEGHS001HS104-143-11 | HTTP MCP Sync and Compatibility | backlog | [story-11-http-mcp-sync-compatibility](./story-11-http-mcp-sync-compatibility.md) | - |
| HSEGHS001HS104-143-12 | Model Library and Providers | backlog | [story-12-model-library-providers](./story-12-model-library-providers.md) | - |
| HSEGHS001HS104-143-13 | Capability Assignments Experience | backlog | [story-13-capability-assignments-experience](./story-13-capability-assignments-experience.md) | - |
| HSEGHS001HS104-143-14 | Chaos Glass and Closeout | backlog | [story-14-chaos-glass-closeout](./story-14-chaos-glass-closeout.md) | - |

## Where we are

The architecture and owner-experience contracts are ratified for planning. A
horizontal repository audit found the existing lawful foundation—immutable
`DeploymentRevision`, `InferenceRunner`, and meeting/speech frozen plans—and
the forks that must be removed: mutable Profile/Target conflation, unguarded
transport-neutral profile authority, scattered Config/subject pointers,
late-routing `inference.run`, raw-SQL Workbench resolution, fake workflow
fallback labels, and path-bearing profile sync.

Stories 01 through 07 are done. Three generated, mutation-tested ledgers now fail closed on a
new execution door, semantic helper caller, mutable resolver/pointer, browser
selector, or Swift physical/fallback path. The baseline records 99 Python
model-shaped sites, 14 Python physical leaves with zero bypasses, and seven
named Apple legacy leaves owned by Stories 06/10. Story 02 now supplies the
sealed, process-composed capability and retry-policy authority for all censused
jobs, including revision-bound meeting plugins and exact runtime result schemas.
Story 03 now establishes reusable profile/binding authority with immutable
content verification, hub-local CAS bindings, restart-visible readiness,
fail-closed dependency ownership, and a read-only v1 execution adapter.
Adding a local model now truthfully ends at `Added` in the Model Library and
does not rewrite a Thoughts assignment. Story 04 now supplies one sparse,
hub-local assignment authority with whole-chain precedence, bounded ordered
fallbacks, ABA-safe Use default, exact compatibility, migration markers, and a
fixed seven-row owner projection. Story 05 now freezes content-free route and
private request-plan evidence before execution, with deterministic replay and
independently reconstructable admission evidence. Story 06's durable controller,
failure law, receipt authority, and dormant routed-runtime seam are implemented
and green. Story 07 now supplies the first lawful saved local-to-cloud adopter
proof; Story 06's separate closeout remains an atomic tracking update rather
than being folded into this story's commit.
Story 07 routes Ask, Thought interview, speech intent, and rewrite through the
sealed coordinator with atomic frozen evidence, controller-owned fallback,
restart recovery, Stop fencing, and one-way legacy cutover. Lexical punctuation
is explicitly future/non-assignable until a model-backed stage exists.
Stories 11–13 ship parity and the two owner jobs: Model Library and Assignments.
Story 14 is the cross-product chaos/glass gate.

Story 08 is in progress on `feat/hs143-08-meeting-adoption` (2026-08-22).
Tranche A–C (semantic adapters, SERVICE route policy, atomic parent/route
bundles, reserve-inert Stop handoff with settlement-gated activation) is
**cold-ratified and committed**: two-round counsel (Terra design
DO-NOT-RATIFY → adopted; Sol cold audit DO-NOT-RATIFY → three fixes → Sol
RATIFY, all seventeen checkpoint items PASS). Key ruled law: unknown-dispatch
terminals never auto-activate displaced work; a bundle seal at the single
execution insert point refuses admission once the parent leaves OPEN.
Phase B (live Meeting + transcription cutover) is riding a Sol-ruled design
(`assets/story-08-phase-b-cutover-design.md`, RATIFY-WITH-AMENDMENTS + the
owner's minimal-migration scope ruling): slice 1 is COMPLETE — live
analysis/bookmark/title execute as routed controller-owned children on an
atomic five-member bundle with aggregate budget groups, deterministic
identities, election-gated cards, honest retry/fallback ordinals,
`record_only` degradation (raw capture never depends on model authority),
and recorder-failure unwind. Slice 2 is COMPLETE: Meeting transcription
(mic + system + devices + final pass) runs as routed controller-owned
children with actual-byte audio hashes, exact `{text, language}` results,
and timeout = unknown/terminal/no-second-model; the exact-local Whisper
migration (incl. deterministic `auto` resolution) creates a visible
library profile + assignment with day-one same-Meeting readiness bootstrap
proven end-to-end on a fresh DB; MLX warmup is one bounded preload child
with frozen candidate evidence (P=1, ceremony trimmed per the owner scope
ruling); load failure degrades to `record_only` with capture alive.
**Phase B is RATIFIED** (Sol checkpoint counsel, three rounds, 2026-08-22:
round 1 eight findings → hardening `13645888`; round 2 two claim-race
blockers → surgical `9dc8dde1`; round 3 RATIFY — "I would use this on a
tired Tuesday now"). Slice 3 detail: live Stop closes admission,
runs the final transcription pass, then one server-derived bundle
fence/cancel (durable fence before best-effort physical cancellation,
replay no-op), discards late routed results and transcripts, and then runs
the unchanged legacy deferred aftercare for every stopping meeting
(bundle-backed and `record_only` alike; Meeting-keyed upsert = idempotency
boundary), so meeting summaries survive until Phase C replaces the queue.
Remaining for Story 08: handover Phases C–F (deferred queue + plugins,
speech lifecycle, background adopters, migration cleanup).

Phase C (deferred queue + installed plugins) is underway against a
Sol-ruled design (`assets/story-08-phase-c-deferred-design.md`,
RATIFY-WITH-AMENDMENTS, six binding amendments). Slice C1a: an 11-test
executable inventory of every queue reader/writer, and the `intel_jobs`
evolution — deterministic `job_id` primary keys, immutable work
descriptors, an atomic fail-back migration — with Phase B's claim-gating
invariants preserved unmodified. Slice C1b: `start_in_transaction`
extracted from the bundle service (wrapper pinned by the primitives), the
real `meeting-intel-queue` SERVICE binder, the narrow
`meeting-deferred-route-assignments` startup family (slice 1a never
covered deferred analysis), and — via an outside code review — the
pre-admitted-parent seam sealed: prepare-time budget/fingerprints compared
in-transaction, orphan shells terminalized, race-tested inside the
released-writer window. A four-fix round then closed the review's
surviving findings: crash-recoverable post-election publication (Ask can
no longer strand at projection_not_published), a SYSTEMIC failure-law
repair (three adapters were remapping model refusals into retryable
errors — all now terminal), device-ID evidence as content-free hash
tokens (unicode device names no longer refuse bundles), and sync
round-tripping `record_only` (with hostile-sync guards). Best-effort
physical cancellation is a recorded limitation with a named
wasted-compute bound. Slice C1 is COMPLETE: the queue worker
executes bound-claimed jobs on stored parent/bundle ids only (no Config
reads), with all three transcript-hash fences (claim, staging,
publication) plus a completion guard, stored-id crash recovery with zero
duplicate egress, retry lineage and completion ledger events, a
typed-refusal terminal proof, and the legacy executor preserved for
pre-C1 claims. Phase D (speech lifecycle) is design-ruled with six
binding counsel amendments and queued behind Phase C. The owed
full-suite sweep ran 2026-08-23: 148 failures triaged against a fresh
main baseline (72, the known inherited local-env set) into 70 inherited
and 78 branch-new; all 78 were classified a/b/c and repaired — three
real regressions fixed (SERVICE-principal receipt read on the
no-reservation replay path, the C1 executor bypassing the
`intel.model_unavailable` fault seam, two meeting modules over the
density budget → extracted routed-child/bound-deferred modules), one
suite-wide pollution leak killed (a fixture blanket-updating every
readiness observation), and the streamed `intel_token` contract's
retirement completed across Python and web. Final quiet-tree sweep:
6392 passed, 71 failed, zero branch-new — every failure reproduces on
main (full record in the verification ledger's sweep section). Next:
the C1 counsel checkpoint, then C2 (plugins) and C3 (the Stop-handoff
provider — the ratified primitive's first real adopter).
Verification ledger:
[tranche A–C ledger](./assets/story-08-tranche-ac-verification-ledger.md);
counsel record:
[counsel round 1](./assets/story-08-displaced-work-counsel-round1.md);
ruled specs: [inertness spec](./assets/story-08-displaced-work-inertness-spec.md),
[Phase B cutover design](./assets/story-08-phase-b-cutover-design.md).
GitHub Actions minutes are out by owner order: all Story 08 verification is
local; CI is not consulted.

Normative assets: [architecture contract](./assets/architecture-contract.md),
[owner experience](./assets/owner-experience.md), [repository census](./assets/repository-census.md),
and [delivery map](./assets/delivery-map.md).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A fallback array is added to Config/ProfileRecord | high | Require profile/binding/assignment/plan separation | Any child resolves mutable target state after admission |
| Existing pointer families remain competing authorities | high | Generated census plus one-way family migration markers | A migrated caller still reads/writes its legacy pointer |
| Retry/fallback duplicates or hides provider calls | high | Durable controller above InferenceRunner; separate leg/attempt ordinals | A physical leaf lacks its own admitted child/receipt |
| Tool/model fallback repeats or expands an effect | high | Independent frozen ToolTurn lease and receipt adoption | Unknown/effectful result advances the model chain |
| Granular routing becomes a matrix/wizard | medium | Bounded group rows plus searchable overrides and one sheet | Default page height grows with capability count |
| Model setup silently rewrites jobs | medium | Separate Model Library from Assignments | Add/connect/download changes an assignment revision |
| Local binding data leaks through sync/DTO | medium | Hub-local bindings and reciprocal privacy fixtures | New path/secret/private endpoint appears in sync/public DTO |

## Decisions made (this phase)

- 2026-08-21 - Use Model Library + Assignments as the owner ontology; setup makes intelligence available and never silently assigns it - avoids a conflated wizard and hidden route mutation - owner ruling.
- 2026-08-21 - Separate immutable `ModelProfileRevision@2`, hub-local `ProfileBinding`, ordered `InferenceAssignment@1`, and frozen `InferenceRoutePlan@1` - prevents mutable profile/readiness/secret state from becoming execution identity; alternate policy/resolved-plan labels are non-persisted prose only - architecture audit.
- 2026-08-21 - Keep existing `DeploymentRevision` and `InferenceRunner` as the only execution revision/gateway - extends HoldSpeak's mature substrate rather than creating a parallel stack - one-path law.
- 2026-08-21 - Generalize MeetingIntelPlan/SpeechPlan's frozen ordered-revision pattern; distinguish route-leg and physical-attempt ordinals - preserves proven restart behavior and prevents dialect/fallback ordinal collision - repository census.
- 2026-08-21 - Assignments are sparse capability/group/subject overrides with ordered qualified fallbacks and an atomic Save - scales without a matrix and keeps inheritance explainable - product/architecture ruling.
- 2026-08-21 - Tool fallback cannot expand the independent capability lease or repeat/guess an effect; unknown completion stops - maintains YOLO speed inside explicit owner intent and policy - tool authority ruling.

## Decisions deferred

- The exact first shippable migration wave after Story 06 may split Thoughts from writing if implementation evidence shows separate database migrations are safer; default remains Story 07 together.
- Whether `known_pre_dispatch_unavailable` advances by default is deferred to the capability policy fixture; default is **no advance** until explicitly enabled and owner-visible.
- Tool-turn delivery remains gated on Story 09 Part A implementing the
  separately ruled Tool Capability Foundation. The shared owner surface ships
  first for migrated Thoughts; later groups activate only with Stories 08–10.
