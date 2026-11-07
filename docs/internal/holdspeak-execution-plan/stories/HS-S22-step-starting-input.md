# HS-S22 · Start dependent work from an explicit repository snapshot

**Conditional build-journey plan; implementation not assigned.** Epic: [HS-E20](../epics/HS-E20-program-contracts.md). D17/D25/G22 remain pending. Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. No application or Git operation was run to author this plan.

## Job and evidence

When step B follows step A, the builder must know which repository state B actually receives. Readiness answers whether B may proceed; it does not prove A's code is in B's starting tree. Existing readiness deliberately includes owner-parked predecessors, so this story does not redefine every dependency as a successful merge.

Today, an ordinary new Program worktree uses the saved local base-branch name. The local-merge path can push A to the remote without advancing that local branch. B can therefore start from an older local state under that condition. Existing real local-Git tests prove final combined files and Done, but not B's input before work begins. This is a conditional source-contract gap, not a claim that every successor fails.

A second boundary matters: the runner reads worktree HEAD after the hand returns launched. An agent can already have changed it. That observation is not authoritative evidence of the worktree's initial commit. The proposed change ties a selected commit, verified new worktree and first instruction together before spawn, then carries the same proof into Program state.

Evidence: [repository lifecycle](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#repository-lifecycle-appendix) and [dependent-step trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#dependent-steps-readiness-does-not-establish-a-fresh-starting-tree-1400-follow-up). Exact source and proof ownership: [V22](../VALIDATION.md#v22-step-starting-input-verification).

## D25 and G22 choices

**A. Fresh remote-base snapshot for ordinary new Program worktrees.** Resolve one exact advertised base commit after launch admission, fetch that object successfully, verify it locally and create from its immutable ID. This detailed branch is a snapshot at the verified selection point, not a continuously latest tree or a guarantee that every predecessor was merged. The Program keeps its saved repository; project filing/reassociation does not move existing work.

**B. Deliberately fixed Program baseline.** Define when that baseline is selected, where it is retained, and how the owner deliberately advances it. Do not pretend the current mutable branch name is such a baseline. Selecting B stops A's implementation and requires the corresponding persistence/compatibility contract.

**G22 must settle A's compatibility and authority before execution:**

1. Apply freshness only to ordinary **new, local, non-helper Program worktrees**, after continuation/held-launch and capacity classification. Explicit checkpoint starts and existing-worktree continuation are separate paths. General hand-offs, helpers/reviewers, final delivery and end-check worktrees are not silently migrated.
2. Accept the remote-read effect inside the already claimed `process.spawn` operation for the bound source and policy. `agent.hand` is not the enforced admission boundary. No fetch belongs in `program_step_spec`, preview, validation, capacity waiting or pre-admission source lookup.
3. Decide local-only compatibility explicitly. This branch proposes a named refusal when `origin` or its base ref is absent. If supported local-only work must continue, choose a separately named local-snapshot rule before implementation; it must never be an automatic fallback after an unreachable/rejected configured remote. No useful local-only capability is silently removed.
4. The server owns the selector descriptor and validates it against the actual Program/step/source. A permissive nested request object is not new client authority. Revalidate the admitted source/policy after claim without mutating the admitted request hash or substituting the project's latest repository.
5. Missing/ambiguous remote ref, unsuccessful fetch, object/identity mismatch, failed proof persistence or unknown creation must stop before new spawn. Existing objects or a worktree path are not proof that this attempt succeeded. Do not retry into a new branch/worktree or reset/delete anything automatically.
6. Separately accept the checkpoint compatibility tightening included in this proposed branch: the current spec uses the stored ref but does not compare it to the stored checkpoint commit. The new no-fetch verifier would refuse a moved ref instead of silently using its new target. A missing ref already fails creation. If this tightening is not accepted, amend the checkpoint proof/claims before implementation.
7. Preserve current diff-base meaning on continuation. The initial worktree snapshot, current HEAD and carried `facts.base_commit` are distinct. Existing/legacy continuation does not become freshly verified because current HEAD can be read, and missing new proof does not by itself forbid an otherwise supported continuation.

D17's ordinary queued-hand repository policy remains separate. The source path is not an immutable guarantee against later external directory/remote replacement. Report what was bound and checked; do not claim a new repository-security sandbox.

## Proposed selection and durable proof

Use the existing local `LaunchService`, Git runner, `LaunchLedger` and worktree-create operation. No new scheduler, generic start-point registry, additional command-receipt framework or independent state machine is needed.

The proposed server-owned descriptor names ordinary-new Program selection policy, Program/step identity, bound source and base ref. It is part of the existing nested worktree request that `process.spawn` hashes. Exact field names are proposals, not existing APIs. It contains no fabricated remote commit before admission. For an explicit checkpoint, a separate server-derived expected-commit field can carry the already stored checkpoint commit alongside its exact ref; this is proposed metadata, not an existing API or a remote selector. Validation is read-only; selection begins only after claim and final new-worktree classification.

A candidate race-safe selection sequence is: obtain exactly the advertised `refs/heads/<base>` object ID, fetch that exact object with a successful result, validate it as a commit, then pass the frozen ID as the existing `start_point`. Do not resolve a shared `FETCH_HEAD` or stale tracking ref after an unrelated fetch. Official command semantics and installed capability checks are in V22. Raw-object fetch may be rejected by a server after ref movement; fail rather than substitute the local branch or call cached data fresh.

Persist bounded selection metadata in the existing launch record **before worktree creation**: policy/source/base identity, selected object ID and selection time. Do not retain credential-bearing remote URLs or secrets. Preserve these fields when the admitted record is replaced by the starting record; `record()` is not an implicit merge.

Require a positive creation result and matching source/worktree/attempt identity. Before any agent spawn, read the new worktree's actual HEAD, verify it equals the selected commit, and durably retain that verification. If a recorded creation result or required persistence is missing/uncertain, stop. Generic `worktree_created` receipts do not already contain commit provenance, and path existence alone is not this attempt's creation receipt.

Use the same stored proof in Program facts and the first instruction. The existing instruction is composed before admission and held only after launch; therefore this branch must explicitly add a bounded pre-spawn finalization step inside the existing launch flow, rather than merely changing returned text after spawn. Complete the bounded start-context text and check its final byte cap before spawn; do not discover an overlong first instruction only after launching. `process.input` hashes the actual text separately. Held-message resume sends the already retained text/proof and must not re-fetch or silently choose a newer base.

For a new worktree, set the initial diff base from verified pre-spawn input, not a later HEAD observation. For continuation, retain an existing diff base; represent any new current-HEAD observation separately. Legacy unknown proof remains unknown. No migration manufactures history for old launches.

## Preservation and failure boundaries

- The owner’s checkout branch, HEAD, index and working files remain unchanged. Fetch can change Git object storage/metadata; do not claim the whole repository directory is byte-identical.
- Explicit checkpoint start retains its exact ref/commit/checkpoint identity. Missing ref failure is current behavior; moved-ref comparison/refusal is the new G22-gated verification above. Neither case permits refreshing from the remote base. After the accepted comparison, freeze/pass the stored checkpoint commit rather than the mutable ref and verify created HEAD before spawn; retain the ref/IDs as provenance. Existing same-worktree Hand again/handoff retains uncommitted work and its original diff context.
- Source binding uses the Program's saved repository path. Changing project filing or the project's default repository does not migrate the Program. Missing bound source is a named refusal, not a guessed clone/other project.
- Capacity wait, held-brief recovery and replay of known launch identity must not fetch merely because a Program is read again. Unknown creation/spawn requires inspection of existing records, not repeated launch. Cleanup remains a separate deliberate operation.
- A selected snapshot can become older than a later remote head immediately afterward. Record it honestly; no endless freshness loop or fetch-until-stable behavior is proposed.
- Existing parked readiness, checkpoint starts, helper parent-branch starts, review posture, Program controls, credential issuance and first-message admission remain intact. No external PR approval or delivery is implied.

## Acceptance matrix

All new cases are proposed proof, not passing results.

| ID | Required boundary |
| --- | --- |
| C22-01 | A pushes a dependency to the temporary remote while the owner's local base remains older; ordinary new B contains that dependency before any agent work |
| C22-02 | Advertised exact ref, successful object fetch, commit validation, literal worktree start, pre-spawn verification and durable proof all name the same source/attempt/object |
| C22-03 | Concurrent unrelated fetch/ref movement cannot substitute another mutable ref; later advancement is recorded as an older selected snapshot, not falsely latest |
| C22-04 | Missing/unavailable remote, ambiguous/refused object or unsupported command capability causes no spawn and no stale/local fallback under the accepted policy |
| C22-05 | No fetch before enforced admission, on denied/expired claim, at capacity, on continuation or held-message resume; nested client metadata cannot expand scope |
| C22-06 | Selection/verification survives every launch-record replacement and reaches runner facts and the actual held/sent instruction; byte-limit failure happens before spawn |
| C22-07 | Mutating HEAD immediately after fake spawn does not rewrite initial proof or the new diff base |
| C22-08 | Checkpoint identity remains exact; missing ref keeps current failure and the accepted new comparison refuses an already moved ref, freezes the stored commit for creation and checks created HEAD even if the ref moves afterward, with no remote fallback. Hand again/handoff keeps worktree, dirty changes and prior diff base; legacy unknown proof stays unknown |
| C22-09 | Failed or unknown create/persistence retains truthful attempt identity and existing artifacts, with no reset/delete/automatic replacement launch |
| C22-10 | Owner checkout/index/work files remain unchanged; registered source and Program binding do not follow project reassociation |
| C22-11 | Parked predecessor readiness and existing successful final-output tests remain; no universal merged-predecessor or live-GitHub guarantee is claimed |

## Tasks and rollback

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T22-01](../tasks/HS-T22-01-contract.md) → accepted D25/G22-A → [HS-T22-02](../tasks/HS-T22-02-start-input.md) → [HS-T22-03](../tasks/HS-T22-03-verification.md). Use [V22](../VALIDATION.md#v22-step-starting-input-verification). D17's broader reassociation/queue question and other Program stories are not prerequisites; serialize shared Program runner/hand/launch files.

No schema migration or history backfill is intended. A code reversal cannot undo a created worktree, fetched object or started process. Preserve recorded input and launch identity, and review whether older code would discard proof or restore the original bare-branch selection. An older driver that ignores new proof/unknown-state metadata must not resume unresolved new-format attempts; reconcile them before any downgrade. Do not reset the owner checkout or erase records. Stop for unresolved local-only/checkpoint choices, unsafe effects, missing durable proof or a need to enlarge the four-file domain boundary. This package is a conditional plan, not an implementation assignment.
