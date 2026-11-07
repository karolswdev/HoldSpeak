# HS-S42 · File meeting decisions deliberately and correct the right object

**Detailed conditional proposal; implementation not authorized.** Epic: [HS-E40](../epics/HS-E40-director-context.md). Decision: D19/G42, still pending. Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Source review is not a reproduced live incident or passing test.

## Job and source finding

A leader authors a decision in a meeting, sees which project it will be filed to, receives an honest creation/filing result, and can later change that decision's current project membership without changing its meeting or source history.

Today's helper chooses the first ranked meeting association and loses the distinction between no project and a failed lookup. The canonical POST retains a Desk source decision; a separate PUT files `decision_record:<id>`. That PUT can fail after creation. The meeting well then reports a generic save failure without retaining the canonical identity for recovery. A malformed successful canonical response can trigger another, legacy creation POST. These are source-derived boundaries, not proof of an observed duplicate or wrong filing.

The correction command already exists. The inspected decision pullout resolves a canonical record, but its filing strip addresses the retained source ref. Simply replacing that strip's entire ref is also wrong: the strip uses it for collections as well as projects. The target must distinguish **current canonical project membership**, **source collection/drawer membership**, **recorded provenance** and **meeting association**.

Evidence: [creation and correction trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#director-context-appendix-a-meeting-association-becomes-an-authored-decisions-filing). No new store, workflow engine, canonical API or provenance migration is needed for the proposed branch.

## G42 local decisions before implementation

The following is a recommended coherent branch, not an accepted product policy:

1. **Visible decision scope.** One known meeting project may be visibly preselected and accepted by the final Save. Multiple candidates never silently select the first; the owner chooses a project or deliberately saves without explicit project filing. No linked project and project lookup unavailable have distinct words. An unavailable lookup does not block retaining the title; saving without a project requires an explicit unfiled choice, not an error-to-null fallback. A deliberate choice of another active project remains possible using the existing project list.
2. **Canonical meeting creation.** After attempting the canonical POST, malformed response, HTTP failure or transport loss must never trigger a second legacy creation. If a supported legacy-only meeting flow is required, define its pre-write capability/route decision separately before implementing it. No such mechanism was found in this chain. Keep the legacy API/source aliases and the separate global New Decision producer unchanged; this is not their retirement.
3. **Receipt before filing.** Validate and retain both the canonical record identity and the retained source decision before the membership write. A decision can be created while explicit project filing is unconfirmed/refused. Show that result and recover against the same known ID, never by creating again. Save without filing is also an explicit supported outcome under this branch.
4. **Correction target.** When one canonical record is authoritatively resolved, the Projects axis changes its current canonical membership. Collection/drawer axes remain on the existing source identity. Retained source project memberships remain separately visible/read-only in the canonical branch; do not hide or union them into a remove-all gesture. No mapping, ambiguous mapping and lookup failure must be distinguishable; do not guess the first canonical record or silently switch identities after failure. Verified legacy-only decisions retain their source-ref filing behavior.
5. **Relationship meaning.** The Project API has one live row per project/resource ref, carrying `relationship=member|source|output|related`. A matching project row does not necessarily confirm the requested `member` filing. Resolve the canonical Projects control's meaning explicitly: **membership-only** controls may change member edges while showing other relationship kinds separately without generic add/remove; **all-relationship** controls may retain the broader existing model only with truthful role/removal/replacement wording and an explicit accepted interaction. No branch is selected here. A known non-member row must never be silently declared a confirmed member filing or converted/deleted as generic filing recovery. This gate applies only to the revised canonical branch; unrelated and verified legacy strip consumers retain their own existing behavior.
6. **History is not current membership.** Removing a canonical edge does not rewrite recorded project sources, the retained decision's tags or meeting associations, and may not remove inherited Room visibility. The filing UI and receipt must not promise that it does. Source-history correction and reassignment of an entire meeting remain separate future work.

If G42's canonical-only meeting branch is not accepted, the correction task can be selected independently once its identity/display gate is accepted. Do not make useful canonical correction wait for a new legacy capability framework. No implementation can infer these choices from planning authorization.

## Target interaction and outcome custody

Keep the existing inline Meeting Decide well, per-meeting draft isolation, shared text/microphone controls and one-primary-action rule. Do not build a modal or move the user into another app. Keep the meeting ID, title, summary and explicitly selected scope together when submitting; none may be replaced by a later selected meeting or late project read.

The local result should distinguish the following facts. Exact TypeScript names are proposed, not existing public API:

| Fact | Honest result and allowed next action |
| --- | --- |
| No creation attempted | Title/scope can be changed or cancelled; no decision was created by opening the well |
| Known pre-creation refusal | Retain input and show the actual refusal. Do not claim all errors are pre-write |
| Canonical creation unconfirmed | Preserve input/uncertainty; refresh/read existing decisions for inspection. No automatic retry, legacy fallback or identity guessed from title |
| Canonical + source IDs acknowledged, no project chosen | Created without explicit project filing; preserve meeting/source context and open the acknowledged decision |
| IDs acknowledged, membership PUT pending/refused/unknown | Created, filing not confirmed. Retain IDs and chosen target; a retry cannot call either creation endpoint |
| Current read confirms the exact canonical ref/project and live `relationship="member"` row | Confirm the requested member filing; do not repeat the effect merely because its earlier response was lost |
| Same ref/project has a different relationship kind | Preserve/show that known relationship, distinguish it from member filing, and use only the accepted G42 role-change/removal interaction; generic recovery cannot overwrite or delete it |
| Valid complete read has no live row for that exact ref/project | Offer an explicit same-record/same-project member action under existing admission rules; do not automatically refile or replace a later owner decision. Missing/malformed shape or unknown relationship is not verified absence |
| Creation/filing acknowledged, later reveal or refresh fails | Keep acknowledged identity/outcome; offer read/reveal recovery, never generic Save again |
| Well closes/reopens or meeting changes while a write is pending | Closing is not cancellation. An old response must not clear a newer draft, alter a different meeting or reveal an abandoned flow |

**Bounded receipt persistence, proposed under G42:** use a separate versioned JSON value in the existing workspace draft map, keyed per meeting (exact key/name is proposed). Keep captured attempt/input/meeting/project identity and an attempted-but-unconfirmed creation stage, with no invented IDs, separately from the editable title. Record the pending attempt before sending; after timeout retain its unconfirmed state. On acknowledgement add the actual canonical/source IDs and separate filing stage. Successful-storage close/reopen or reload must not restore an unconfirmed attempt as ordinary title/Save. Preserve existing plain-title drafts. A local attempt/input version must distinguish an old A→B→A edit from the current A; equality of text alone is insufficient. An old response cannot clear newer input or replace a newer receipt. This is a small UI recovery record, not a second canonical store or a new backend journal.

Existing `keepDraft`/`keptDraft`/`forgetDraft` and the workspace handoff pattern support this. Storage catches localStorage failures, so the guarantee is same-browser close/reopen and reload **when storage succeeds**, not crash-proof, cross-browser/device or cleared-storage recovery. Keep in-memory acknowledgement honest even if persistence cannot be guaranteed. Reopening reconciles valid known IDs against the actual canonical/source mapping and current membership before further effects; draft metadata alone supplies no authority or current-state proof. Unknown creation without an acknowledged ID still has no safe replay protocol. Never automatically replay creation or filing on mount.

**Read/write reconciliation must include edge meaning.** Validate the relationship envelope and exact canonical resource ref/project/role, not just an array containing the project ID. The current GET returns all live relationship kinds. A member PUT upserts that single edge and replaces its relationship/source/confidence; DELETE removes that edge regardless of its kind. Thus a previously acknowledged member write can later coexist only as historical evidence with a current `source`/`output`/`related` row, not as another simultaneous member edge. Preserve the known creation receipt and current observed state without an automatic repair. Unknown kind, mismatched identity, malformed rows or an unavailable read stay unresolved. A DELETE response with `removed=false` is an acknowledged no-removal result, not proof that this press removed an edge; it can still record a command/revision.

A check then press is not a compare-and-swap guarantee. Neither the current helper nor strip supplies a project revision; concurrent changes can occur after the read. If G42 requires preventing all concurrent relation replacement/removal, specify the existing revision/read/command flow and caller scope before implementation. Do not claim that a client guard alone enforces that stronger promise or silently add a backend protocol.

Membership commands support optional `command_id`/`expected_revision`, but current frontend use must be inspected. Adding command keys is not assumed in this slice; it requires explicit G42 scope if desired. The preserved server replay contract can be tested independently. A replayed old successful PUT receipt does not prove current membership after a later DELETE or relationship-kind change; read present state. Canonical creation accepts neither a reusable client decision ID nor command key in this route, so membership replay must not be advertised as creation idempotency.

For correction, keep the original source `objectRef`/`objectId` for non-project axes. A **proposed project-axis-specific override** (or equally narrow local composition) can let the existing strip read/write canonical project membership without migrating source collection relationships. The canonical mapping is keyed to the current source decision; invalidate stale mapping/results on identity changes. Loading/error/ambiguity disables only the action whose identity is not established, rather than pretending a successful empty list.

The existing strip uses `apiRequest`, which can return non-OK responses without throwing. All touched project reads/writes must check actual response status before claiming success, playing success feedback or refreshing a successful receipt. A refresh failure after a known write is different from a refused write. Do not turn a network error into an empty-membership observation or automatically toggle again.

## Acceptance matrix

These are proposed cases. Existing assertions, new producer fixtures and browser observations must be labeled separately.

| ID | Required proof |
| --- | --- |
| C42-01 | One known project is visible before Save; multiple associations cannot silently choose rank/tie order; explicit unfiled/other-project choices are distinguishable |
| C42-02 | No association, failed lookup and stale lookup are distinct; a late A response cannot choose scope for B or overwrite a newer explicit selection |
| C42-03 | Opening/cancelling/typing creates nothing; empty title refuses locally; request captures the intended meeting/title/project; duplicate pending presses produce one create attempt |
| C42-04 | Real canonical route creates the expected canonical record plus retained source/provenance; membership PUT affects that canonical ID and no action/commitment is invented |
| C42-05 | Malformed/missing/wrong-type/empty IDs and uncertain canonical responses never trigger POST `/api/decisions` or another canonical POST, including timeout → close/reopen/reload with successful workspace storage |
| C42-06 | Membership refusal/lost response after acknowledged creation retains both IDs and does not offer new creation; read reconciliation distinguishes present/absent/unavailable |
| C42-07 | Explicit same-ID filing recovery and later reveal/refresh recovery do not create another decision; newer draft and other meeting survive late completion |
| C42-08 | Canonical lookup one/none/multiple/failure and A→B stale results produce explicit identity states, not arbitrary first-record or failed-read fallback |
| C42-09 | Canonical Projects toggle uses `decision_record:<id>`; source collection/drawer reads/writes retain the source ref/object ID; verified legacy aliases preserve their existing contract |
| C42-10 | A real admitted canonical PUT/DELETE changes current membership while retained source tags, canonical source provenance and meeting association remain unchanged |
| C42-11 | Non-OK project read/PUT/DELETE, transport loss and post-write refresh failure have distinct truthful feedback; no false success sound/count or automatic repeat |
| C42-12 | Removing explicit membership does not promise disappearance from inherited Room visibility or alteration of historical About context |
| C42-13 | Existing global New Decision, legacy ref correction, other filing-strip consumers and source decision editing retain their own identities/behavior |
| C42-14 | The actual inline well/correction UI works at 1440, 393 and narrow-in-wide layouts, with keyboard focus/Escape, shared mic custody and accessible hit targets |
| C42-15 | Exact canonical/project/member readback differs from source/output/related, malformed/unknown and absent rows; old member receipts cannot override a newer relation. The accepted role-change/removal interaction is explicit, unrelated strip consumers are unchanged, and no read-then-write atomicity is claimed |

Producer proof is required for C42-04/10 and relevant refusal/admission cases. App tests prove exact requests, outcome custody, identity transitions and draft races. Browser proof is required for geometry/focus/hit claims; a mock does not establish those facts.

## Exact source map and ownership

Read only these relevant symbols/sections, plus current repository-required guides. All existing paths refer to the pin; new names are proposed. This pass inspected the saved archive, not a fresh runtime or current checkout.

| Existing path | Relevant boundary | Edit status |
| --- | --- | --- |
| `web/src/desk/decide.ts` | `meetingProject` 29–41; `createDeskDecisionRecord` 69–101; `decideFromMeeting` 107–155 | Tasks02/03, serialized. One production caller of the shared canonical helper was found in the source scan |
| `web/src/meetings/MeetingDecideWell.tsx`; `meeting-decide.css` | Keyed wrapper 52–54; per-meeting title 64–79; save/receipt 86–109; controls 124–151 | Task03; CSS only if necessary for current container/focus layout |
| `web/src/desk/pullouts/DecisionPullout.tsx` | Canonical lookup/resource ref 88–105; compare-before-retire pattern 131–150/191–224; filing strip 378–388 | Task04; do not redirect source text editing or all filing axes |
| `web/src/desk/components/DeskFilingStrip.tsx` | Relationship reads 78–103; toggle 105–130; project axis 219–233; other-axis/source object identity | Task04. Preserve directory/KB behavior and distinguish canonical/source project rows |
| `web/src/desk/deskMemory.ts`; `store/compositorSlice.ts`; `store/workspaceStorage.ts` | Plain draft helpers 33–45; persist after draft write 306–312; localStorage failure swallowed 427–436 | Read-only shared infrastructure, not a new persistence layer |
| `web/src/desk/terminals/workspaceHandoff.ts`; `web/src/desk/conductor/StartAgent.tsx`; `web/src/desk/hooks/useWriteReceipt.ts` | Existing JSON known-ID/filed pattern 54–83 and 184–250; feedback/retry closure is not durable outcome custody | Read-only patterns; do not import the agent workflow or blindly replay its closure |
| `web/src/desk/store/dataSlice.ts` | Separate global New Decision producer 343,403–440 | Read-only and preserved; meeting fallback changes do not retire this producer |
| `holdspeak/web/routes/decision_records.py`; `holdspeak/services/decision_record_service.py`; `holdspeak/services/desk_kernel.py` | Canonical from-desk route 69–100; source/project provenance 190–196; fresh IDs 113–128/169–174 | Read-only creation/admission contract; no create idempotency invented |
| `holdspeak/web/routes/projects.py`; `holdspeak/services/project_service.py`; `holdspeak/services/project_kernel.py` | Member PUT/DELETE 344–384; add 4584–4676/remove 4736–4791; replay 213–220; Room inclusion 2930–2952; meeting unlink 5025–5034 | Read-only actual command/revision/replay and separate visibility contracts |
| `holdspeak/db/relationships.py`; `holdspeak/kernel/desk_codec.py`; `holdspeak/kernel/project_codec.py` | Exact canonical ref 17–40; relationship fields 65–85, one-edge upsert 189–221 and all-kind read 255–262; owner/scoped Desk grant 68–85; Project authority 62–117 | Read-only; do not bypass admission or introduce cross-ref aliases |
| `web/src/desk/pullouts/views/DecisionsView.tsx` | Historical About source/rationale 870–894 | Read-only; membership edits do not rewrite it |
| `tests/unit/test_philo5_the_loop.py`; `tests/unit/test_philo7_article_xi.py` | Real temporary hub `_boot` 130–166/teardown 169–175; operation counts/receipts 66–100; isolated agent auth 115–125 | Read-only setup patterns; do not run unrelated loop suites or inherit owner credentials for an agent case |
| `tests/unit/test_decision_records_routes.py`; `tests/integration/test_memory_desk_decision_ref.py`; `tests/integration/test_one_place_relationships.py` | Real bare canonical route 56–115; legacy spellings/old rows 70–147; independent axes 19–62 | Read-only preservation suites. Bare-edge anonymous status is not full-hub status |
| `web/src/desk/__tests__/deskDecisionRef.test.ts`, `philo1308Decide.test.tsx`, `decision.app.test.tsx`, `deskRemembers2.philo1307.test.tsx`; `web/src/desk/components/DeskFilingStrip.test.tsx` | Helper, meeting/pullout, close/reload and directory/KB cases | Editable only for accepted task subset. Old unknown-endpoint `{}` mocks must not mask canonical failures |

**Proposed new owned tests:** `tests/integration/test_meeting_decision_filing.py` (task02 creates and task04 extends; for correction-only scope, task04 creates the same bounded producer and its needed fixture subset itself) and `tests/e2e/test_meeting_decision_filing_glass.py` (tasks03/04 share by agreement). **Four proposed wire outputs only:** `web/src/desk/__tests__/fixtures/decision-filing/{created,filed,removed,refused}.json`. V42 defines their bounded producer and capture process. No other fixture paths are implicitly writable.

The old meeting producer in `tests/integration/test_desk_meetings.py:427–489` calls legacy creation; the old glass test is parked at `tests/e2e/_parked/test_philo13_08_decide_glass.py`. They are source/interaction references, not the new canonical proof and not tasks to unpark. `tests/e2e/glass_infra.py` and `tests/e2e/test_frame_glass.py:674–684` provide isolated setup and actual resize references for the proposed browser lane.

## Task order

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T42-01](../tasks/HS-T42-01-contract.md), then accepted local choices:

- [HS-T42-02](../tasks/HS-T42-02-creation-receipts.md): canonical creation and filing outcomes, no duplicate-create fallback.
- [HS-T42-03](../tasks/HS-T42-03-meeting-scope.md): visible meeting scope, guarded drafts and receipt UI, dependent on the creation contract.
- [HS-T42-04](../tasks/HS-T42-04-canonical-correction.md): correct current project membership without moving other axes. May be assigned independently under its own accepted G42 subset.
- [HS-T42-05](../tasks/HS-T42-05-verification.md): independent producer/app/browser and integrated proof of the accepted slice.

Use [V42](../VALIDATION.md#v42-meeting-decision-filing-verification), not the entire research library. The correction and meeting lanes share some test/store fixtures; serialize overlapping edits and final proof. Neither depends on Program creation/classifier completion.

## Rollback and stops

No schema/data migration is planned. Reverse only the approved UI/helper/test edits; preserve created records, membership receipts and unrelated lanes. Reverting the old frontend also restores its identity/uncertain-outcome limitations. A code reversal does not undo a known creation or filing command.

Stop for unresolved G42, a required legacy capability protocol, ambiguous canonical identity, new source-history rewriting, cross-axis migration, unsupported same-ID recovery, unsafe fixture effects, code-lane overlap or a necessary backend behavior change. No task may invent an accepted decision, new lifecycle or safe retry. Preserve [I13/I16/I17/I18/I21/I23/I25](../INVARIANTS.md).
