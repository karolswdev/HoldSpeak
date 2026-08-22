# Phase 143 - The Intelligence Router

**Last updated:** 2026-08-21.

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
| HSEGHS001HS104-143-04 | Assignment Store and Resolver | backlog | [story-04-assignment-store-resolver](./story-04-assignment-store-resolver.md) | - |
| HSEGHS001HS104-143-05 | Frozen Route Plans | backlog | [story-05-frozen-route-plans](./story-05-frozen-route-plans.md) | - |
| HSEGHS001HS104-143-06 | Fallback Controller and Failure Law | backlog | [story-06-fallback-controller-failure-law](./story-06-fallback-controller-failure-law.md) | - |
| HSEGHS001HS104-143-07 | Thoughts Ask and Writing Adoption | backlog | [story-07-thoughts-ask-writing-adoption](./story-07-thoughts-ask-writing-adoption.md) | - |
| HSEGHS001HS104-143-08 | Meetings Speech and Background Adoption | backlog | [story-08-meetings-speech-background-adoption](./story-08-meetings-speech-background-adoption.md) | - |
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

Stories 01 and 02 are done. Three generated, mutation-tested ledgers now fail closed on a
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
does not rewrite a Thoughts assignment. Stories 04–06 then add assignments, frozen plans, and
the durable controller before product families migrate in Stories 07–10.
Stories 11–13 ship parity and the two owner jobs: Model Library and Assignments.
Story 14 is the cross-product chaos/glass gate.

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
