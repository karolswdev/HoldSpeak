# HS-S43 · Explain obligation coverage and open People

**Detailed conditional proposal; implementation not assigned.** Epic: [HS-E40](../epics/HS-E40-director-context.md). D22 / local **G43** remains pending in [Decisions](../DECISIONS.md). Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`.

## Job and evidence

A director reviewing Needs you can tell what its “They owe me” filter covers and where the separate People commitments live. A clear attention list is not evidence that every obligation is complete. This slice improves understanding and access; it does **not** create a comprehensive leadership register or immediately reveal every omitted obligation.

Existing behavior is intentional and useful. `PeopleService.list_cards` includes open commitments owed **by the leader**, but excludes `report_owes` commitments owed **to the leader**. The exclusion applies to both shared-intent and leader-private People records. Relationship detail and 1:1 briefs retain those records, and People already exposes their supported Nudge/Done actions. This is not lost data or an absent People feature.

Needs you already has source-availability disclosure and a People-read failure indicator. Those describe whether selected sources were read, not which obligation directions belong to the view. The attention header and filtered chip counts also have different existing meanings; neither is an organizational obligation total. Linking a person to a project does not assign every commitment to that project. People cards are projectless, and backend project filtering intentionally excludes the People overlay.

Evidence: [director coverage trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#director-overview-appendix-they-owe-me-is-not-every-private-commitment-1100-follow-up). Exact current source, implementation/proof budget and proposed commands: [V43](../VALIDATION.md#v43-obligation-coverage-verification). Source assertions were inspected, not executed; no user-facing omission incident was reproduced.

## D22 and G43 choices

- **A, truthful scope plus ordinary People entry, specified here:** preserve the current attention projection, add a short static explanation, and open the existing People surface through its normal navigation contract. No private aggregate, count, new query or inferred project/person relationship.
- **B, immediate context-specific inspection:** if acceptance requires opening a particular person, unfiltered roster, Prep lens or exact obligation from this notice, design that intent separately. The generic entry cannot promise it. A verified `openPerson(id, "prep")` exists for an actual relationship ID, but ordinary owner names/filter keys are not that identity.
- **C, broader leadership coverage:** explicitly decide whether private report-owed records should join an overview, with source identity, privacy, direction, scope, ordering/count meaning and lawful transitions. This is a larger D22 branch, not a hidden addition to A.

Selecting B or C stops A's dependent implementation for an amended design. The user has authorized detailed planning, not selected any branch.

G43-A must accept all of these visible limits and behaviors:

1. The note is present in **every settled state**: populated, empty, Mine/They owe me/To decide, person/project/week filters, muted-only, incomplete sources and People unread. Keep the current initial read-or-cap loading veil; “always present” does not mean overriding it. The note's static space participates in the existing stable first reveal rather than arriving after another read.
2. Proposed concise copy: **“Needs you is an attention view. ‘They owe me’ excludes commitments recorded in People.”** Use the neutral action **Open People**. Exact wording may be refined at the gate, but it must name the omitted direction. Do not say all private/People commitments are absent, “all clear everywhere,” “View all,” or “Show missing.”
3. The action uses existing `openSurfaceOr("open-people", "/")` without a person/project/lens scope, query parameter or forced reset. It opens/restores the ordinary People place. A warm surface can retain a person, project-filtered roster, search and lens; a cold surface may restore a saved person. It does **not** promise an unfiltered roster, Prep, all obligations, or inheritance of the Needs filter. Users continue through existing People controls. If this is inadequate for the intended job, select B instead of silently resetting state.
4. Preserve the current header/counts/chip labels, filtering, source-read warnings and retry action. A static coverage statement is not a readiness check and must not suppress an unread warning. Do not fetch People details/counts merely to decide whether the note or button appears.
5. The note and action add no domain write, acceptance, Done, Nudge/Note creation, Send, private prefetch or export. Existing Needs meeting-seen bookkeeping and ordinary navigation/workspace persistence remain permitted and separately identified; the whole mounted screen is not globally read-only.
6. No private names, IDs, bodies, counts or availability inference are inserted into the static note. Existing domain admission and encrypted storage remain authoritative after navigation. An unavailable or not-configured People destination stays truthful; opening it neither sets it up nor bypasses a key/owner check.
7. Today/briefing and other attention surfaces are unchanged. Their due-date selection and limits differ; this one NeedsDrawer change is not a product-wide completeness claim.

## Narrow implementation design

Two existing production paths only:

- `web/src/desk/needs/NeedsDrawer.tsx`: render one cohesive static scope note and accessible existing `Button` after the toolbar and before the existing source disclosures. Keep it outside `chipRow || offer`, row-list, filter and muted conditions. Use the already imported normal opener. No hook, subscription, new state owner or data decoder is required.
- `web/src/desk/needs/needs.css`: narrowly scope the note's spacing/wrapping and button layout using current tokens. Preserve the drawer's flex/ledger scrolling and `[data-settling]` rules. Do not shrink/hide words on phone, add a new scrolling subpanel or change shared surface CSS. Exact class/test IDs are proposed, not existing APIs.

Keep existing `NeedsChipRow`, `passesChips`, `needsHead`, source coverage and PeopleReadFailed behavior intact. The note is not a member row, source gap, counted item or notification. Clicking it must not enter row-body delegation or dispatch row verbs. Adding this note does not justify moving the large cohesive file or building a general coverage registry.

The navigation proof must show actual People host content, not infer success from the opener's void return. Ready/admitted warm/cold host behavior is the acceptance contract. Registration is the pinned implementation, not a required future mechanism; its existing `/` fallback does not guarantee that People mounted. Apply the [conditional landing-order gate](../VALIDATION.md#navigation-and-people-landing-order-gate) if S12 or related People work is already present: preserve the actual accepted public entry/admission behavior rather than resurrecting registration or silently changing its fallback. S12 is not a prerequisite.

## Acceptance matrix

| ID | Required outcome and proof |
| --- | --- |
| C43-01 | Real encrypted producer has leader-owed and report-owed commitments under both supported visibilities; the former enter the allowed overlay, the latter remain in relationship/brief but not the overlay. No body copying to ordinary action storage |
| C43-02 | Ordinary waiting work still populates its current They owe me path; the note does not relabel every row as private or imply the list contains every ordinary obligation |
| C43-03 | Note/button remain present after normal settle or cap, including zero rows/no chips, filtered/muted empty, partial source coverage and People unread. Initial veil and row/tap stability remain unchanged |
| C43-04 | Header, chip counts, rankings, filters and source/unread warnings are unchanged on the same responses. No new query or private fields/count in the note; readiness is not confused with domain completeness |
| C43-05 | An actual ready/admitted host entry opens/restores People (registered at the pin) with no forced person/project/lens/reset. Same-name people do not produce guessed IDs; existing warm search/project/lens and cold saved-place behavior are honored and visibly verified |
| C43-06 | Project filtering never infers obligation membership from relationship.project_refs. While the Needs window remains mounted, its filters remain as they were on return; unmount may reset existing local chips, and no restoration is added. People context is its existing independent place, not a claimed transferred filter |
| C43-07 | Before/after CTA call ledgers show no new request/accept/Done/Nudge/Note/Send or private prefetch/export. Existing seen/window bookkeeping is explicitly allowed, not mistaken for domain effects |
| C43-08 | Existing People owner/key/not-configured/outage behavior remains, with actual producer admission/readiness cases and destination UI. The notice itself does not claim People is available or empty |
| C43-09 | At 1440×900, 393×852 and a genuinely narrow/short Needs window, note, source-gap disclosure, People warning, ledger and footer remain readable and keyboard/touch usable together. No hidden rows, overlapping hit areas or clipped CTA |
| C43-10 | Raw producer envelope flows through actual Needs store/drawer and existing People host. A mocked opener call or a source test name alone is insufficient. Source/fixture/runtime limits and unchanged Today scope are reported |

## Order and ownership

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T43-01 contract](../tasks/HS-T43-01-contract.md) → accepted D22/G43-A → [HS-T43-02 implementation](../tasks/HS-T43-02-coverage-entry.md) → [HS-T43-03 independent proof](../tasks/HS-T43-03-verification.md).

No People Add, identity, navigation rewrite or backend consolidation is a prerequisite. Serialize `NeedsDrawer`, its CSS, People app/capture/browser test owners and shared fixtures with S12/S33/S41 and any active Needs work. The implementation owns the one designated capture writer and all bounded test changes; no parallel node writes the same bundle.

## Rollback and stops

Reverse only the assigned two-file UI plus tests/capture diff. No durable schema or private record migration is involved. Reverting removes the new scope explanation/entry, not existing People obligations. Do not delete records, restore ordinary workspace history or undo meeting-seen markers as rollback.

Stop for unresolved destination/scope choice, source drift, unexpected backend change, required private aggregate or new route, forced context reset, unavailable safe producer/host proof, or geometry requiring undeclared shared styles. If current source already provides this explanation/entry, prove that instead of duplicating it. No shipping or implementation authority is conveyed by the plan.
