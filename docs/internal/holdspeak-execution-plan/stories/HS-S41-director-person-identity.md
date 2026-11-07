# HS-S41 · Follow an obligation to the intended person

**Detailed conditional proposal; implementation not authorized.** Epic: [HS-E40](../epics/HS-E40-director-context.md). D16/G41 remain pending. Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Source inspection establishes contracts, not a reproduced live incident.

## Job and existing boundary

A leader confirms work from a meeting, understands whether its owner name identifies a person, and can deliberately resolve an ambiguous name without silently changing a wider identity mapping. Keep the existing meeting, ordinary obligation, Project Room and encrypted People feature set connected rather than create another assignment app.

Meeting's owner picker fetches relationship IDs but submits only a display-name string. Two identical names therefore express the same owner text. Confirm already preserves action/commitment identity; subsequent People navigation correctly comes from Door's mapping by **action ID**, not the picker. A missing Door mapping is deliberately inconclusive: ambiguity, unavailable People, absent/closed board cards and other exclusions are not distinguishable there.

Room already offers inline Resolve. Its candidate IDs differ, but identical labels are not informative; pressing a candidate immediately writes an alias and all failures are collapsed into a reread. The existing alias command stores a reusable, case-insensitive owner-name mapping in encrypted People. It can change attribution of other matching owner strings, including outside this project. It is not an assignment to one action. The two-field Room candidate projection intentionally excludes private context; its privacy test asserts that boundary.

Evidence: [director identity trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#director-context-appendix-selecting-a-name-is-not-selecting-a-durable-person) and [V41 source/proof map](../VALIDATION.md#v41-director-person-identity-verification). This branch changes two existing UI owners, not backend identity rules, wire schemas or storage.

## D16 and G41 choices

**Branch A, detailed here:** keep the current owner-text and reusable alias domain, make name selection honest, and require an informed, separate alias confirmation in the existing Room well. **Branch B:** introduce durable per-obligation assignment. B needs an explicit identity, private-data placement, authority, migration and propagation design; it is not implemented by sending a relationship ID in the current owner field. Neither branch is accepted by this plan.

Before A is implemented, accept these local choices:

1. **Name versus person.** Meeting owner editing is explicitly name text. Identical display-name options are collapsed without case-normalizing, rewriting existing drafts or pretending one person was selected. Keep `Me`, blank and previously stored custom owner text. No implicit alias write accompanies Confirm.
2. **Honest person navigation.** Keep exact action-ID-based known People navigation and conflict suppression. Add a bounded read state and explicit read-only Check for Door person metadata. Absence means no person destination established by this read, not a diagnosed ambiguity or a missing obligation. The existing Project action preserves the project, not an exact resolver-row reveal; no new navigation protocol is assumed.
3. **Private disambiguation where needed.** On explicit Room resolver expansion, read the existing authorized People relationship list and join only its current candidate IDs in memory. Display only name, relationship kind and role context needed to distinguish them. Do not add those fields to Room's wire, ordinary records, notes, logs, persisted workspace drafts or shared cache. The full hub HTTP list GET and alias POST are owner-only at the edge. Separately, PeopleService permits a live launched reader for authorized service/MCP reads, never alias writes; preserve that separate contract rather than widening REST admission.
4. **Deliberate reusable mapping.** Selecting/inspecting a candidate does not write. Before a separate Link action, show the exact owner string and chosen person/context and explain that the mapping applies to matching owner names beyond this obligation/project. Allow cancel without effect. Inspection opens the existing exact-ID People view. A name, UUID suffix or checked box is not proof the intended person is known: if the inline name/kind/role context still does not distinguish the candidates, keep inline Link unavailable and offer existing exact-ID People inspection. Any informed mapping made in that existing person’s Context view uses its existing alias action, outside this inline change; return to Room and explicitly press its proposed read-only Check. Keep Check available in the resolver after inspection even when no inline POST was made. Exact-person close is not the roster’s return signal and does not itself establish refreshed Room state or restored control focus. No checkbox or “I inspected it” bypass is added to the indistinguishable inline choices.
5. **Truthful outcomes.** Keep acknowledged alias write, later projection-refresh failure, known refusal and uncertain POST separate. No automatic repeat, alias transfer, unlink, meeting reconfirmation or obligation completion follows. Retain only in-memory attempt context. Reload/close can lose that receipt; this branch does not promise durable or cross-device recovery.
6. **Bounded continuity.** Existing eligible Room commitments can show current attribution after reread. Others may be closed, unfiled, parked or outside the Room. Preserve existing People management and exact known navigation for those cases; do not promise every meeting obligation can resolve in this Room or widen eligibility to make the demo work.

G41 must accept both the reusable mapping semantics and the scoped private-context display. If either is rejected, stop the dependent UI change rather than replacing the domain implicitly. Meeting's truthful name/read treatment may be accepted separately, but report the resolver journey incomplete.

## Interaction and outcome custody

### Meeting

Use the current owner control, outcome ledger and More menu. Preserve task/due drafts, proposal identity, Confirm/Dismiss/Done/Reopen behavior and the meeting's existing primary action. Name selection never creates a People record, assigns a relationship or calls alias POST.

The Door read is keyed to the current meeting/action set and explicit read attempt. Clear or disable stale person destinations while the current read is unresolved. A late response for an old identity or older attempt must not overwrite a newer read, clear a draft or navigate. On success, only one distinct relationship for the exact action ID can enable the existing People item. Repeated cards with that same relationship are not a conflict; differing relationship IDs suppress the destination. On failure, show a read failure without rewriting owner text or diagnosing the private store. Check only reissues the read. Keep project/source/follow-through actions independent; no save/confirm/send occurs from navigation.

The Project link opens the existing Room. It does not select an owner row. No-project or ineligible obligations are not fabricated into Room. Exact person navigation uses existing `openPerson(id, "prep")` or its default; `"info"` is not a supported public lens at this pin. The owner can inspect the existing Info/Context view after navigation.

### Room

Keep one inline well and shared controls. Scope metadata reads, selected candidate and request sequence to project + owner + candidate set. A project/owner change, close or protected-read failure must retire stale private context and selection. Do not fan out full person-detail reads; the existing list is sufficient for its authorized summary fields. A relationship missing from the current list is not selectable from stale candidate data. The owner-authorized list can return an empty list for an unconfigured/no-key store; this is not proof that a candidate was deleted or never existed. A single last-name suggestion also remains a candidate, not established identity.

Select and inspect are nonmutating. The exact-person window and People roster have different return paths: `openPerson` mounts `PersonWindowBody`, while the existing roster alone announces the return-to-task event on cleanup. Preserve the roster/Someone else behavior, but do not borrow its event or focus promise for exact Inspect. For that path, the owner returns to the existing Room and presses Check; it rereads the current authorized roster and Room projection without linking, reconfirming or completing anything. Reopening a closed resolver reads afresh. Do not arm the shared pending return-focus token for exact Inspect merely because the roster uses it, or add a global close listener/PeopleCore change to manufacture automatic continuity. Any broader automatic return is a separate scoped design choice.

Check remains available while the resolver is open, with or without an inline-write receipt. Its results obey the same current project/owner/candidate identity, privacy retirement and late-read rules as initial expansion. An alias added in the existing person's Context is observed as **current state**, never relabeled an acknowledgement of a Room write that never occurred. A failure retains an honest read/unknown state, not permission for a duplicate Link. Exact source and test limits are in [V41's inspection-return proof](../VALIDATION.md#exact-person-inspection-and-return-proof).

Capture immutable project, owner string, candidate ID and the original ordinary **commitment IDs** when Link is pressed; these are not action IDs. Disable duplicate presses for that attempt. A later read/row change cannot retarget the in-flight request. Do not move commitment rows optimistically or fabricate resolved counts.

| Result | Required presentation and next action |
| --- | --- |
| Known successful POST acknowledgement | Preserve that historical acknowledgement even if Room/People refresh later fails. Reread current state; do not present the refresh failure as a failed write |
| Explicit alias conflict | State that the name is already linked elsewhere, using only authorized structured error content. No automatic unlink, reassignment or retry; never render/stringify arbitrary raw error payloads |
| Reserved name, missing/archived candidate or forbidden writer | Preserve the known refusal class in plain language; retire stale protected context where applicable; allow read/inspection rather than silent success |
| Transport loss or ambiguous server failure | Outcome unconfirmed, not “nothing changed.” A generic 503 can mask a failure after the encrypted write, including its subsequent record read, and is not a known pre-write refusal. A separately observed readiness/read failure does not settle the POST outcome. Only explicit read/inspection; never repeat POST automatically |
| Exact saved owner literal is present on selected relationship in an authorized read | Positive current alias evidence. This is not proof which attempt wrote it or a perpetual mapping guarantee |
| Literal absent, read unavailable, or only a case-variant alias is present | Not definitive negative proof. Do not recreate Python Unicode casefold with JavaScript lowercasing or automatically replay the write; leave uncertain and offer existing People inspection |
| Original commitment IDs now appear under selected relationship | Positive current attribution for those exact commitments, separate from explicit alias ownership/write acknowledgement. Unique-name resolution can also produce attribution |
| Commitments disappear or owner row is absent | No inference of completion, successful alias write or loss. Eligibility may have changed; preserve acknowledged outcome independently |

The existing void helper discards the response body: a successful HTTP completion acknowledges the captured request, but this branch does not claim typed response-identity validation or current-state proof from that completion. Fresh authorized reads establish current state separately.

The existing service has sequential same-relationship idempotence and active-holder conflict checks. Its scan then replace is not evidence of a cross-process atomic uniqueness guarantee. This UI branch neither solves nor claims that stronger contract. Receipt state stays in memory; no plaintext persistence of relationship IDs/context is added. Closing a view does not cancel an in-flight POST, and reopening must read current state before any new explicit decision.

## Acceptance matrix

| ID | Required proof |
| --- | --- |
| C41-01 | Two identical display names yield one honest owner-name choice; Confirm sends existing text/owner/due only, not a person ID or alias write; custom text and newer edits survive |
| C41-02 | Real confirmation retains ordinary action/commitment/source IDs; later person destination is resolved by action ID, never guessed from selected label |
| C41-03 | Known, absent, conflicting and failed Door mappings produce distinct honest UI; closed/omitted cards are not diagnosed as ambiguity; explicit Check and late read races cannot overwrite newer context |
| C41-04 | Expanding/choosing/inspecting/cancelling Room resolution has zero writes; contextual display comes only from the authorized People list for exact current candidate IDs |
| C41-05 | Same names with differing role context are visibly distinguishable; indistinguishable/missing-current inline candidates keep Link unavailable, including after Inspect. Existing People Context mapping remains a separate explicit action; no ID/order/checkbox or inspected-flag bypass |
| C41-06 | Explicit Link displays exact reusable alias scope, sends one existing POST to captured relationship ID, and does not reconfirm/change/complete an ordinary obligation |
| C41-07 | Real alias link affects current attribution across two matching ordinary obligations while their stored owner/action/commitment identities remain unchanged; this branch introduces no private ID/context into ordinary action/commitment persistence or export, and no new private fields widen the existing authorized Room/Door ID/name projection or observer contracts |
| C41-08 | Owner versus live-reader/agent write authority, protected store, reserved name, archived/missing candidate and conflict remain enforced by actual service/routes |
| C41-09 | Known write + failed read remains acknowledged; lost response or post-put record-read failure remains uncertain; reads do not automatically POST, steal an alias or create another person/obligation |
| C41-10 | Exact-literal positive reconciliation, case-variant uncertainty, current commitment attribution and absent/closed/parked rows remain separate facts |
| C41-11 | Project/owner A→B→A, stale candidate reads, close/reopen and late write completion do not retarget effects, restore retired private context or overwrite newer drafts |
| C41-12 | Real browser proves inline geometry, keyboard/focus and hit ownership at 1440, 393 and a genuinely narrowed window; exact Inspect opens the actual person host, existing Context Add is followed by explicit Room Check with no synthetic return event or duplicate write, and roster return remains a distinct preserved path |

Use actual composed producer evidence for C41-02/07/08/10. App faults prove response handling, not live incidents. Browser layout proof is separate from HTTP/service semantics. Preserve [I16/I17/I18/I21/I23/I25](../INVARIANTS.md).

## Ownership and task order

Existing editable production files only:

- `web/src/pages/cores/history/MeetingDetail.tsx`: current `MeetingOutcomes` name control, Door read and destination menu.
- `web/src/features/project-room/RoomPeopleSection.tsx`: `ResolveWell`, selection/private-read state, `pick` and refresh outcome handling.

Use existing API/navigation/surface helpers; no new component/module, route, schema, DTO or cache is prescribed. Exact read-only source map, tests, producer outputs and browser file are in [V41](../VALIDATION.md#v41-director-person-identity-verification). Any required extra production/CSS path needs a bounded amendment, not silent expansion.

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T41-01 contract](../tasks/HS-T41-01-contract.md) → accepted G41 subset:

- [HS-T41-02 meeting continuity](../tasks/HS-T41-02-meeting-identity.md).
- [HS-T41-03 explicit Room resolution](../tasks/HS-T41-03-alias-resolution.md).
- [HS-T41-04 independent proof](../tasks/HS-T41-04-verification.md), covering the accepted subset and complete journey only when both UI branches are present.

Serialize shared producer/fixture/browser edits; do not make the slice depend on S12 opener changes, S42 canonical filing or a new People assignment model. S42 touches nearby meeting surfaces, so coordinate shared test ownership and integration.

## Rollback and stops

No data/schema migration. Reverse only owned UI/test changes after review, preserving ordinary records and encrypted aliases already written. A UI rollback neither cancels an in-flight write nor removes a reusable mapping; any alias removal is a separate explicit owner decision because it can affect other work. Old UI also restores immediate-link/opaque-error limitations. No automatic cleanup of owner data.

Stop for unsettled G41, insufficient identity evidence, protected metadata leaving its authorized in-memory face, required durable assignment, wider Room/People visibility, unexpected write/retry, unsupported lens/row-reveal semantics, unsafe fixtures, scope overlap or source drift. A bounded unresolved result is preferable to a guessed person.
