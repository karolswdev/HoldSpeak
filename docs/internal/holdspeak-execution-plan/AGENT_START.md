# Agent start: one assigned HoldSpeak task

**Detailed planning is authorized. Repository implementation is not yet assigned by this package.** Current hierarchy: [ordered plan](EXECUTION_INDEX.md). Research baseline: `80b641fa41c7352280cfa52e933acf6dbe8d3857`, main rechecked 3 November 2026 at 19:34 UTC.

HoldSpeak is a local hub and web Desk for capturing context, coordinating repository work, asking with sources and following through on technical leadership. The goal is coherent existing workflows, not a replacement platform. You receive one task, not the entire research agenda.

## Authority and checkout safety

1. Record the task ID, assigned role, authorized actions, checkout/worktree and decision resolution. If only given the package, plan/read only. Do not infer permission to change repository code, install dependencies, run product tests, use live providers/devices, push, merge or deploy.
2. Read current checkout `AGENTS.md`, `docs/internal/TWO-BRAINS.md`, current `CLAUDE.md` fast-cycle section, `pm/STATUS.md`, `docs/internal/CONSTITUTION.md`, then the guide for owned paths. Backend work adds `holdspeak/AGENTS.md` and `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`; doc/UI changes add their scoped instructions. Check `.agents/skills` for relevant missing skills. Current roles/model/worker instructions govern execution; this Markdown package does not override them or assign a new code lane.
3. Use the explicitly assigned isolated worktree. Never mutate the owner's main checkout; identify its protected location from the current repository instructions and environment assignment, not a machine-specific path copied from this plan. Do not create/switch worktrees or install dependencies until the environment assignment covers it. Never `stash`, `reset`, `checkout --`, `restore`, `clean` or `switch`; never repair another lane. Workers hold for SHIP and do not stage/commit.
4. Run [HS-T00](tasks/HS-T00-baseline.md) before implementation, and recheck SHA/status before each later task. If current behavior already satisfies the story, report that with proof rather than replaying the historical change.

## Exact reading contract

Read this safety section once, the assigned task, its linked story contract and listed invariant IDs. Then inspect only the named repository interface, implementation, relevant callers and proving tests. Repository-mandated onboarding still applies; the package does not require the entire evidence library or the full target design for a local fix.

Paths marked **existing** were inspected at the pin. Names marked **proposed** are plan suggestions, not existing APIs. Line numbers help rediscovery; symbols and actual current behavior decide drift. Each task owns explicit editable paths; its read-only context does not expand edit permission. A missing proving boundary or necessary additional file is a reason to request a bounded amendment, not improvise wider scope.

## One portable handoff, bounded reading

Supply this Markdown folder together at its preserved relative layout in the assigned environment, using an authorized transfer method. Do not make an agent reconstruct it from individual chat attachments or download every research record. Keeping the full folder available preserves reference navigation; it does **not** make every file required reading. No repository publication or transfer is performed or authorized by these instructions.

Alongside the folder, supply one assignment message or existing handover record with:

- Package version, exact task ID/accepted subset and role; authorized checkout and actions, including whether setup, collection, tests and code edits are allowed. Publication/shipping remains separate.
- The actual resolved local decision and its verifiable source, or an explicit pending decision. A story recommendation, hypothetical example or completed contract task with a pending gate is not acceptance.
- HS-T00 and required predecessor reports, linked or included in the handover with their actual checked revision/diff, outcome, owned files, proof and unresolved limits. Include accessible evidence locations where a claimed result depends on them. Do not rely on hidden conversation, unavailable local paths or a bare statement that checks passed.
- Any explicitly assigned joint proof and its additional local gates. If absent, the conditional creation-to-Room or review-to-delivery joins are outside this assignment, not automatically required or already passed.

Do not generate another repository dossier just to package these facts. If an authority, decision or predecessor record is missing, report that specific gap and pause only dependent work; a planning/contract assignment can still return a pending decision.

**Reading boundary:** the task's Mandatory context is the entry list. Read linked headings and named invariant rows, not every section in those files. A story's source bibliography, parent epic, another task's Next link and historical evidence links are navigation/reference, not an instruction to traverse the entire graph. Follow a reference further when the assigned contract actually depends on its detail or a source inconsistency needs resolution. Common validation safety/setup still applies; then use only the assigned V section and its explicitly required commands/cases. Current repository-mandated onboarding and applicable safety/authority constraints are never waived.

**Worked S11 handoff:** the complete baseline → contract → implementation → verification chain uses nine package files: this file; [HS-T00](tasks/HS-T00-baseline.md); [HS-S11](stories/HS-S11-program-creation-context.md); [T11-01](tasks/HS-T11-01-contract.md), [T11-02](tasks/HS-T11-02-implementation.md), [T11-03](tasks/HS-T11-03-verification.md); [Validation](VALIDATION.md#v11-program-creation-verification) (common rules and V11 only); [Invariants](INVARIANTS.md) (I02/I16/I17/I18/I21/I24/I25); and [Completion report](COMPLETION_REPORT_TEMPLATE.md). An agent assigned only T11-02 reads that task's named sections and predecessor reports, not every sibling task. This is a checked reading map, **not a separately exported nine-file bundle** with guaranteed complete navigation. Accepted decision/assignment records and the actual repository instructions/source remain additional inputs. S13 material is needed only if the joint proof is assigned.

## Work procedure

- Resolve the local behavior gate. The owner need not answer unrelated product questions to authorize one independent slice. Record the actual decision; silence is not an answer.
- Verify current callers and existing tests before changing them. Source-inspected assertions are not passing results. Capture baseline, collection and focused run evidence under [Validation’s command rules](VALIDATION.md#what-these-commands-mean) and the assigned task’s exact V section.
- Use existing fixtures/adapters with isolated state and no implicit real provider/device effects. Respect the machine-wide test lock. A unit test is not a live capability proof.
- Implement only the task's behavior. Do not bundle navigation cleanup, schema migration, cache replacement, general recovery/policy engines or opportunistic dead-code removal.
- Verify after the final edit, including new conflicts or later changes. Preserve exact failure/unknown outcomes rather than calling them success. Test failures do not authorize weakening guards or changing expected behavior without evidence.
- Return the [completion report](COMPLETION_REPORT_TEMPLATE.md): exact diff ownership, decision, evidence, remaining gaps and rollback boundary. Integration checks belong to the assigned integration role. Shipping remains a separate action.

## Stop and rollback

Stop dependent work for missing authority, changed domain semantics, an unapproved behavior choice, unknown effect state, unsafe fixtures, unexplained baseline failures or scope conflict. Report action, target, reason, completed work and denied/pending/uncertain status. Check an uncertain action before any retry.

Rollback is a reviewed, task-specific correction, not `git reset`. A code change cannot undo an external effect, a saved private copy or historical approval. Preserve owner data, unrelated work and audit truth. Restoration of old classifier behavior also restores its old limitation; disclose that.

## Detailed handoffs

Choose the assigned story and task from the single [ordered hierarchy](EXECUTION_INDEX.md#2-proposed-workstream-hierarchy). Each task names its own mandatory sections, local gate, source/edit budget, exact proving tests and stop/rollback contract. The hierarchy is navigation, not a requirement to read other slices. HS-S24 remains a contract-resolution task only; its presence does not authorize enforcement implementation.
