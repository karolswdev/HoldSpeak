# HS-E10 · Keep the work's context through the journey

**Proposed product workstream; implementation not assigned.** Parent: [ordered plan](../EXECUTION_INDEX.md#2-proposed-workstream-hierarchy). The owner has authorized detailed planning, not any proposed behavior or repository execution.

## Outcome and boundaries

Starting technical work, finding its current Program and opening the exact pending decision should retain the right project, repository, target and request identity. Improve the existing Desk journey rather than build another workspace or a general navigation framework.

A display filter is not creation context. An application/window name is not the identity of a pending proposal. Navigation is not permission to save, accept, dispatch or expose private sources. Preserve actual contextual entry points before adding another chooser to them.

## Stories

| ID | Product outcome | Local decision and dependency |
| --- | --- | --- |
| **[HS-S11](../stories/HS-S11-program-creation-context.md)** | Global New Program gathers valid creation context and enters the existing drafting lifecycle | D13: repository-bound creation versus an unbound Draft. The detailed conditional branch fits today's bound service; it is not selected by writing it |
| **[HS-S12](../stories/HS-S12-focused-navigation.md)** | Cold/warm/recovery entry reveals the exact intended work without saving it | D12/G-OPEN: explicit admission/reveal owner, transient replay versus staged arrival, and caller closure before removing opener registration. Lazy and mount-read mechanisms remain separate |
| **[HS-S13](../stories/HS-S13-project-program-continuity.md)** | Find and inspect existing Programs from the current project journey | D15/G13: inline placement/read truth versus an actual project-scoped global transition. Existing projection/legacy render are not proof of today’s current overview |
| HS-S14 | Program detail readers share existing keyed query ownership | Earlier D01: reuse the existing cache; characterize actual identity transitions before claiming a reproduced stale-load bug |

HS-S11 can proceed independently of HS-S12–14 when D13 and its bounded scope are accepted. Do not make a local creation fix wait for a shell rewrite or silently add it to that rewrite. Shared Programs UI/API ownership still requires coordination; an unrelated Program classifier task can proceed in its separate files.

## Proposed delivery and proof

Begin each assigned slice with [HS-T00](../tasks/HS-T00-baseline.md). HS-S11 details the build journey: its source shows an actual producer/precondition mismatch and a mocked-success test that does not exercise that boundary. Retain both D13 branches, but provide an executable conditional plan only for the narrower existing-contract branch; selecting unbound Draft requires a new lifecycle design checkpoint.

Prove the real request contract in a temporary local backend rig, the actual UI press and acknowledgement, then the relevant narrow-window and integrated journey behavior. A frontend mock alone cannot prove backend acceptance; a backend API test alone cannot prove that the user can choose and retain the right context. Do not claim a live incident was reproduced from source inspection.

HS-S12 now supplies the connecting navigation branch: [contract/caller closure](../tasks/HS-T12-01-contract.md) → accepted G-OPEN → [state preparation](../tasks/HS-T12-02-dispatch-state.md) → [host cutover](../tasks/HS-T12-03-host-cutover.md) → [independent proof](../tasks/HS-T12-04-verification.md). This branch preserves separate transient and staged intent roles, the existing proposal handoff and domain authorities. State/host activation is cohesive; no partially enabled second dispatcher is shippable. Verify recovery, target reveal, aliases, storage faults and actual browser content, not only a ready marker or mock callback.

HS-S13 now supplies the project-to-existing-work link: [contract](../tasks/HS-T13-01-contract.md) → accepted G13-A → [current Room](../tasks/HS-T13-02-room-continuity.md) → [independent proof](../tasks/HS-T13-03-verification.md). Preserve the uncapped exact-project projection, existing Program detail identity and current frame fallback. Three frontend owners add truthful current/last-read/empty/unavailable states; no new dashboard/backend store, Program effect or shell dependency. Compose actual Room-to-host proof, not only a legacy component test. When both S11 and S13 are accepted, [the linked creation-to-Room gate](../VALIDATION.md#creation-to-room-integration-gate) belongs to T13-02/03, with S11 app-test ownership coordinated. It proves one project-only request across resolver, stored association, successful Room read and exact detail. S11 reload, Room notification and detail reveal are separate mechanisms; missing events need deliberate read recovery, not another create. Neither this joint proof nor either local fix requires S12.

## Completion, rollback and stops

Complete only the accepted stories and report the remainder as pending. Preserve [I16/I18/I21/I24/I25](../INVARIANTS.md), existing project/action launch provenance, source authority and separate Program completion/delivery. A successful create response identifies a Program; it does not authorize Start or retry an uncertain create.

No epic-wide migration or new navigation substrate is assumed. Each story names owned files, focused tests and a reverse-patch rollback. Stop for unresolved local semantics, missing authority, unsafe fixtures, source drift or new domain/storage requirements. Do not repair those by guessing a default project, adding an unbound state, clearing another lane's work or inventing global retry machinery.
