# HS-E40 · Keep leadership decisions and follow-through coherent

**Proposed outcome workstream; implementation not assigned.** Parent: [ordered plan](../EXECUTION_INDEX.md#2-proposed-workstream-hierarchy). The owner has authorized detailed planning, not any proposed decision, storage change or external communication.

## Outcome

A technical leader can move from a meeting or concern to the intended decision, person and follow-through without reconstructing context or losing track of what is authoritative. Existing canonical decisions, source evidence, ordinary obligations and encrypted People records remain distinct. Coherent presentation is not a universal outcome store or an organization-permissions feature.

## Stories and local gates

| ID | Outcome | Gate and preserved boundary |
| --- | --- | --- |
| **[HS-S41](../stories/HS-S41-director-person-identity.md)** | Follow an ordinary obligation to the intended person with explicit reusable alias scope | D16/G41: name-only Meeting choice, authorized in-memory candidate context, separate alias confirmation and truthful current/unknown outcomes; per-obligation assignment remains separate |
| **[HS-S42](../stories/HS-S42-decision-filing.md)** | Author a meeting decision with visible filing scope, then correct that decision's current project membership | D19/G42: explicit scope/unresolved handling, canonical creation outcome and exact membership target; preserve provenance and meeting associations |
| **[HS-S43](../stories/HS-S43-obligation-coverage.md)** | Know what Needs you covers and open the existing People place | D22/G43: static directional disclosure plus normal saved-place entry; targeted reveal and broader authorized aggregate remain separate choices |
| HS-S44 | Prepare a nudge without obscuring where a private source becomes an ordinary copy | D24: transient/protected preparation versus intentional ordinary saved Note; Send remains a separate reviewed action |

HS-S41 and HS-S42 are detailed proposals for complementary existing leadership journeys: person/obligation continuity and canonical decision filing/correction. S41 retains two existing UI owners and the encrypted alias contract rather than invent a person-assignment store. S42 follows an existing meeting-to-decision journey and correction API. It does not depend on a new shell, Program creation or a People-storage redesign. Sharing navigation work with HS-S12 later must not introduce autosave, confirmation or broader visibility.

HS-S43 now specifies the bounded attention-coverage branch: two existing UI paths, no extra private read/projection and no count change. It explicitly preserves current People person/project/search/lens state rather than promising a global obligations screen. Source availability, domain coverage and navigation are separate facts. S33's recovery receipt and S44's Nudge custody are not absorbed into it.

## Delivery and proof

Use [HS-T00](../tasks/HS-T00-baseline.md), the assigned story and its exact context. Resolve only that story's local gate. Verify actual producer, persistence and identity paths before extending UI. Tests must distinguish created-but-unfiled, unknown creation, current explicit membership and inherited/historical visibility; a single mocked success is insufficient.

A correction must name what it changes: current decision membership, recorded source context, meeting association or person alias. These have different effects and permissions. Never remove a meeting or rewrite source history to make a UI count disappear. No action-kind obligations are created merely because a decision was authored.

Complete the accepted slice, independently review it and compose the selected director journey through the [HS-S92 identity and delivery map](../EXECUTION_INDEX.md#director-decisions-through-project-delivery). It distinguishes decision-only confirmation, deliberate raw-decision commitment, action-kind confirmation and S42 authored filing; these are not interchangeable producers or automatic transitions. Report other stories as pending. Preserve [I13/I16/I17/I18/I21/I23/I25](../INVARIANTS.md), actual principal/revision/replay controls and private source boundaries.

## Rollback and stops

No epic-wide data migration is assumed. Each task bounds editable files, verification and rollback. A code reversal cannot erase a created canonical decision, its retained source row or an acknowledged membership command. Stop for unsupported compatibility assumptions, uncertain effects, identity ambiguity, missing authority or required source-history changes. Ask for the smallest decision/path amendment instead of inventing a common lifecycle or retry engine.
