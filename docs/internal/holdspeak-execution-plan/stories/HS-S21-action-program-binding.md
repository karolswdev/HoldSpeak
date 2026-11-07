# HS-S21 · Carry action work into the intended Program step

**Conditional product-journey plan; implementation not assigned.** Epic: [HS-E20](../epics/HS-E20-program-contracts.md). D14/G21 is pending. Source baseline: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. This is source-inspected planning, not a reproduced runtime incident or passing-test claim.

## Job and actual gap

The owner launches a Program from a project action, chooses which new unit of work carries that action, and can find that binding after editing, splitting, running and reviewing the work. Informational Program provenance must not silently become an instruction for every step to complete the same obligation.

The existing project action → `RunAsProgram` → `ProgramService.from_action` path preserves action goal, project/repository and Program-level `action:<id>` provenance. Ordinary `plan` stores a step origin only when supplied. The current Add step UI does not supply it. The existing completion paths consult step origin, so Program provenance alone does not complete the source action. Explicit From the Desk/night plans already create step action origins and must remain supported.

There is a second continuity boundary: `ProgramWindow.toPlan` and frontend `PlanStep` currently omit `origin_ref`. Drafting Add step and other draft updates replace the plan from that projection. Adding a new origin once without preserving this roundtrip would lose it on a later edit. This story addresses that composed path rather than treating a checkbox as the whole feature.

Evidence: [workflow trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#workflow-follow-up-context-carried-through-real-work). Exact current source, proving tests and execution limits: [V21](../VALIDATION.md#v21-action-program-binding-verification).

## D14 and G21 choices

**A. Explicit step binding, using existing completion semantics.** This detailed branch adds an explicit choice only when creating a new live step. It preserves that step's origin through the scoped UI paths, existing finish/observer behavior and all current controls. The server’s legacy replacement API remains outside this UI preservation guarantee. It does not claim that action completion waits for whole-Program acceptance or final delivery.

**B. Accepted whole-Program fulfillment.** Keep step origins separate and define when the Program as a whole fulfills the action. This is a different lifecycle contract. `state == done`, `closed_at`, a successful delivery, all parked steps or imported history alone are not sufficient acceptance predicates. Choosing B stops branch A's implementation and requires explicit end-requirement/control/parking/history semantics before a new completion hook is designed.

**G21 must accept or redirect branch A's bounded meaning:**

1. The choice is explicit and initially off. It binds only the new row being added to this Program's exact action source. Never guess by task title/person/project, pick the first step, retroactively bind old work or copy origin to every step.
2. The choice assigns a logical work item, not permanently one physical row. Existing races can clone origin; an accepted split transfers it to the last part. Keep these existing rules visible and proven instead of adding an unrelated uniqueness engine.
3. Existing step origins are immutable through the text contract. This branch does not add arbitrary origin reassignment to started or existing rows. Removing/replacing bound work can leave the Program unbound; it must not silently transfer that obligation to another row.
4. A new Add uses append even while Drafting, preserving existing row IDs and requirements. For an action-backed Program or one containing any explicit action-origin step, the destructive bulk Runs-on choice is guarded; direct the owner to the existing per-step agent edit. Do not disable unrelated continuation/idle controls. This is an explicit UI compatibility tradeoff, not a new server replacement policy.
5. The existing Program transition hook and delivery follow-through observer can both complete an action. Their gates differ: Program step control/requirements and global delivery Secure confirmation are not one policy. Retaining that behavior is an explicit compatibility choice, not a claim that this slice consolidates completion authority. If the owner requires one acceptance boundary or protection from every reopened-between-actors case, stop and design that policy first.
6. The no-PR Done path is included in existing step completion: `gate_merge=none` can finish and complete an action without a merge. The current evidence field names are not proof of an actual merged commit. If only verified merge may fulfill the action, this branch needs a different accepted policy.
7. Binding display is not completion evidence. `origin_closed` or a Program checkpoint does not prove this Program caused completion, and does not prove the action is still done after an owner reopens it. Do not synthesize a new success badge from those markers. Existing source navigation does not establish a current exact-action read; the bounded presentation limit below must remain explicit.
8. This branch does not promise atomic Program/action writes, exactly-once fulfillment or automatic repair after partial failure. Preserve known identifiers, do not automatically repeat an unconfirmed plan write, and never start, accept, merge or complete anything merely to display its binding.

9. **Binding identity versus a usable source destination.** The proposed bounded branch adds a read-only exact action-origin line, not a new exact-action/status reader. Preserve existing Program origin and other source controls without claiming that they reveal this action. G21 must explicitly accept this identity-only new presentation or redirect it: a new ordinary Needs-you entry requires truthful overview wording and bounded destination/effect proof; a genuine exact-action/current-status destination needs a separately scoped navigation/read contract. Neither is silently supplied by calling `openRef`.

No alternative is accepted by inclusion. The owner may select a contract-only/preservation subset first. D13 global creation and the navigation rewrite are not prerequisites.

## Proposed interaction and preservation

Use the existing Program surface and Add step entry points. For a Program with a recorded, nonempty exact `action:<id>` origin, an in-flow choice explains that the new step will carry that action under the existing step/delivery rules. Display that recorded source identity and a clear consequence before the explicit Add press. The reference does not itself verify that the source still exists, is open or is currently actionable; do not add a backend eligibility rule or guess one from absence in Needs you. An appended step in an already-running Program can be picked up by its existing scheduler without another Start press; the well must disclose that consequence. Other Program origins retain ordinary Add behavior. Do not introduce a generic workflow editor, new application or hidden default.

The scope is **add-only**. Extend the existing `PlanStep` type with the already-supported `origin_ref` input and submit only the new row with `replace=false`, whether Drafting or running. Existing rows, origins, explicit gates and step-local requirements remain intact. Ordinary unbound Add also appends; it must not rebuild the whole Draft as an accidental side effect.

Do not try to make `toPlan` a lossless replacement serializer in this slice. It omits gates and other inputs, while the wire also resolves inherited defaults. Backend replacement generates new IDs; step-local requirements can remain attached to old IDs rather than follow the new rows. Copying more fields does not solve that custody problem. Guard only the destructive bulk agent `onPick` for action-backed/bound work and retain the current `StepFold` per-step PATCH alternative. The other picker callbacks use different commands and remain available where currently allowed. Recheck current loaded/readback state before a new guarded bulk write; an unavailable read must not permit the destructive path. This is still not a revision-CAS or cross-tab guarantee. Other public/MCP/text replacement behavior is unchanged and explicitly outside the claim.

Use the acknowledged Program response and step IDs as truth. Do not infer durable row identity from ordinal/title or an old client ID. Existing text origin immutability, split-to-last-part, race grouping and ordinary per-step PATCH semantics remain unchanged. Existing remove/replace operations are not a new implicit transfer of responsibility.

Do not add a broad backend origin-uniqueness rule or reinterpret public plan input. Existing callers may intentionally supply origins for multiple logical steps. If the current Program already has matching action-bound work, explain it and do not offer an accidental duplicate binding through the new affordance. Concurrent/API-created duplicates remain a separate compatibility limit; this UI is not a cross-process exclusivity guarantee.

Retain current public writer/admission controls and the normal step check/review/merge/requirement path. Imported history, parked/skipped work, failed work and a Program-level source link are not new completion triggers. Do not change completion of decision/decision-record origins or private People commitments.

After an acknowledged plan write, show the actual returned binding and keep that Program identity. On an ambiguous response, preserve the draft/selected source and ask for a read/review before any deliberate new write. A refresh can reveal current rows but cannot prove causal identity from matching titles. Closing a pending editor is not cancellation; late responses must not rewrite a newer draft or trigger an abandoned navigation.

## Action destination and current-status limit

At the pin, `openRef("action:<id>")` resolves through `openObject.ts:166–168,234–239` to `openIntelligence({view: "follow-through", followThroughId: id})`. `intelligenceNavigation.ts:31–42` opens `chair:needs` and emits the old focus event. The active `IntelligencePullout.tsx:38–46` listener explicitly ignores follow-through; no active Needs target consumer was found in the archive's TS/TSX spelling scan. This is source evidence of a missing exact-target consumer, not a runtime-reproduced failure or proof about unknown dynamic/external code.

The inspected tests establish less than an exact source reader: `web/src/desk/__tests__/needsYou.app.test.tsx:139–155` checks the Needs window opens, and `web/src/desk/chair/arrivalAttention.test.tsx:371–389` checks event payload. The Program app suite mocks `openRef`, so an exact argument assertion cannot prove row reveal or current state. Even the backend's optional `FollowThroughService.board(focus_id=...)` skips terminal actions before applying its snooze/defer exception (203–214); it preserves other filters. An absent row is not proof the action is missing or done.

Existing action-list APIs are counterevidence to inventing a missing backend capability: `holdspeak/web/routes/meetings/action_items.py:54–56` exposes `/api/all-action-items` with `include_completed`, and `holdspeak/web/routes/projects.py:466–469` exposes project actions. Their existence does not make the current ref opener an exact current-state reader, and querying them is not added to this branch. `from_action` checks action existence, not status; `plan` stores the supplied origin without an action-lifecycle check. Preserve that existing admission rather than silently enforcing a new eligibility rule.

**Proposed scope for the new binding line:** exact recorded identity in the shared StepFold presentation, no new clickable source control, no current-state badge and no fresh endpoint/query. Keep it findable when the owner opens the fold for planned, running/review and finished work, not only inside the editable PlannedBrief body. Existing Program origin/navigation behavior remains untouched. Preserve known action/step IDs and read actual action/commitment state in the real producer/completion proof; do not turn that test-only access into an unimplemented user-facing capability. A requirement for precise post-completion source inspection must stop for a targeted design/ownership amendment, not quietly add a navigation system to this UI slice.

## Completion boundaries that must stay truthful

`ProgramService._close_origin_task` saves after the step's finished transition, invokes FollowThrough's separate transaction, then persists a step marker/checkpoint. FollowThrough completes an action and its linked cadence/decision commitments together, but that does not make the surrounding Program write sequence atomic. A completed-action replay need not add a second domain receipt; the Program helper may still mark the step. A dismissed action is not implicitly reopened.

The delivery observer independently resolves `program_step` to an origin and uses its own confirmation/close state. Test both actor orders and a reopen between them. Record what the existing system does; do not claim a universal no-reclose guarantee or silently change one actor's authority. A failure in the Program hook may leave the step finished and action open; the new binding UI must not label that action complete. Any repair/automatic retry policy is a separate supervised change.

## Acceptance matrix

All cases below are proposed coverage, not executed results.

| ID | Proving boundary |
| --- | --- |
| C21-01 | Project action launch keeps exact Program/action/project provenance and creates no implicit step; ordinary Add is unbound by default |
| C21-02 | Explicit Add binds only the submitted new live row to the displayed action source; no first/every-step inference, existing-row reassignment, history import or guessed identity |
| C21-03 | Add uses append in Drafting and running; preexisting step IDs, origins, configured gates and step-local requirement IDs/links remain unchanged |
| C21-04 | Action-backed/bound bulk agent replacement is guarded, including From the Desk origins; no replacing request is sent, per-step edit stays usable and unrelated picker callbacks retain their commands |
| C21-05 | Matching/ambiguous existing bindings suppress the convenience choice without cleaning legacy data; races count as logical groups and split/overturn transfer semantics remain |
| C21-06 | Text/board and later append preserve origin; current readback IDs drive presentation; unavailable/stale reads never invent permission or a new source |
| C21-07 | Known refusal, acknowledged append, malformed/uncertain response, reload failure and unmount have distinct UI outcomes; no automatic repeat, false cancellation or late overwrite |
| C21-08 | Real from-action→append→existing finished transition completes the intended ordinary action and linked records, retaining step checks/review/control gates and receipt evidence |
| C21-09 | Park/failed/history and mere Program provenance do not become new triggers; no-PR Done and whole-Program Done/Close remain explicitly distinct |
| C21-10 | Existing actor ordering, mixed Program/global modes, replay/already-done/dismissed/reopened actions and write-failure windows are characterized without claiming one actor, causal credit or lifetime once-only behavior |
| C21-11 | Binding display does not infer current completion from markers or absent attention rows; the new read-only origin line issues no extra Start/acceptance/completion/Send command. Appended work in a running Program remains subject to its existing scheduler |
| C21-12 | 1440/393/narrow-in-wide and keyboard/focus/hit-target proof covers the actual new well and guarded interaction; producer/app/browser evidence are not substituted for one another |
| C21-13 | New origin presentation remains findable in planned, running/review and finished folds and is truthful recorded identity, not a verified current action or exact-target link. Existing origin controls remain unchanged; mocked opener/window/event evidence cannot be called source-state or exact-row proof |

## Tasks and rollback

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T21-01](../tasks/HS-T21-01-contract.md) → accepted D14/G21-A → [HS-T21-02](../tasks/HS-T21-02-binding.md) → [HS-T21-03](../tasks/HS-T21-03-verification.md). Use [V21](../VALIDATION.md#v21-action-program-binding-verification). The implementation task owns its producer/consumer cases; the final task independently verifies them. Other Program stories may proceed independently but shared files need one owner.

No schema or domain lifecycle change is intended. Reversing UI code cannot undo a created step or completed action. Preserve durable origins, action status, requirements and receipts; use existing deliberate domain operations for any later correction. A rollback that restores destructive Draft Add can reintroduce the original custody risk, so review that compatibility before shipping an older UI. Stop for a required single completion authority, whole-Program acceptance, global uniqueness, new recovery transaction or unsupported replacement guarantee. Those require a bounded design amendment, not hidden scope expansion.
