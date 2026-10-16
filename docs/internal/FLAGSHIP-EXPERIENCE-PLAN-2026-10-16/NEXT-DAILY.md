# Next daily batch — People preparation and Project review

Bounded source assessment, 2026-10-16. No product edits, tests, browser runs or
owner-state inspection. This continues batch C from README.md; it does not
reopen the flagship audit. First delivery remains frozen for root shipping.

Tuesday: prepare for a report, inspect either direction of an obligation, keep
the next words while the previous Add lands, then open the linked Project and
review its actual pending work. Tenets 3/5/7: existing faces and authorities.

## Concrete owner journey and remaining work

1. **People → the named report → Prep → either obligation title → detail →
   Close.** `PeopleCore.tsx:935` gives You owe an `onTitle` that selects the
   existing CommitmentInspector. The corresponding They owe you row at `:951`
   renders the same commitment kind without an opener. Its Done already uses
   the commitment writer, so this is unequal inspection depth rather than a
   missing obligation authority.

   Minimal fix: wire that title to the same inspector and render the selected
   inspector inside its owning obligation section. Do not display a report's
   obligation underneath You owe. Preserve canonical commitment ID and existing
   Done behavior. The current `Commitment` shape does not carry direction;
   determine the owning section from the two existing row sets or store the
   selected section with the ID. No new detail species is needed.

   Authority checked in source: `PeopleService.create_owed_to_you` at
   `holdspeak/services/people_service.py:236` stores `report_owes` as a commitment;
   `get_commitment` at `:317`, `attach_execution` at `:326`, and
   `satisfy_commitment` at `:352` require owner/relationship access and do not
   impose a leader-only direction filter. The existing execution GET and
   Workbench POST in `holdspeak/web/routes/people.py:278` and `:296` use those
   authorities. This is source inspection, not an executed report-direction
   Workbench dispatch. Do not claim a run or output was completed by opening it.

2. **Prep → type agenda/obligation A → Add → type B before A answers → A
   succeeds → retain B → Back/tab return → B remains with this person.**
   Prep's three inputs remain editable during their writes. Its success paths
   pass unconditional `forgetAgenda`, `forgetOwe`, and `forgetOwed` to `run`
   (`PeopleCore.tsx:797–815`); `run` invokes that callback after acceptance at
   `:795`. Thus a later typed draft can be cleared by an earlier accepted Add.
   This follows directly from the state/write code; no runtime reproduction is
   claimed here.

   Minimal fix: capture the raw submitted draft and clear only when
   `keptDraft(the same per-person key)` still equals it. Use the already adopted
   Context-note rule at `PeopleCore.tsx:1281–1290`. Keep the existing payload,
   visibility, writers and person keys. Refusal keeps the draft. Do not add a
   shared draft framework or alter encrypted People storage.

   Creation-field hierarchy remains the earlier source-backed craft candidate:
   agenda, You owe and They owe you inputs are always mounted at `:922`, `:942`
   and `:965`, before Last time/Open work. Compose the existing Add controls as
   intent-open wells in the same file; reopen a well when its keyed draft is
   present. Keep the next 1:1 and existing obligation rows dominant. Canvas and
   populated narrow shots must settle this small composition before build;
   current source alone does not establish a phone geometry defect.

3. **Prep → linked Project → pending Review → inspect evidence → decide or
   leave → return to the same Project.** `ProjectRoomCore.tsx:428` still gives
   Draft update the primary treatment independent of work. `NeedsYouSection`
   offers the real pending Review as a ghost control at `:943`; `pendingCount`
   comes from the successfully read review section at `:2846`.

   Minimal fix: when that actual pending count is positive, use the existing
   `reviewCtrl.enterReview()` as the head's primary and retain Draft update as
   secondary. With no verified pending work, retain Draft update as the lead.
   Keep the existing `quiet` treatment while Add source owns the primary, and
   keep review loading separate from inference readiness. This is hierarchy,
   not a blocked Review or a request for a new queue. Reuse the current Review
   posture/controller and the existing count; do not derive pending work from
   all attention rows or invent a successful review.

## Already working — preserve it

- People roster has a next-1:1 lead and real Open prep (`PeopleCore.tsx:425–438`).
  Prep records the exact linked event, opens meeting-action sources and linked
  Projects. Assertions are already present in `peoplePrepB4.test.tsx`; they
  were inspected here and not rerun.
- Prep agenda/obligation drafts already use per-person `useDeskDraft` keys at
  `PeopleCore.tsx:786–788`. Back clears selection/place at `:452`, not drafts.
  `desk/deskMemory.ts:15–33` restores those keyed values. Do not describe normal
  Back/tab/remount draft retention as broken. Context's closed draft, refusal,
  person isolation and newer pending text already have explicit assertions in
  `pages/cores/__tests__/peopleCore.test.tsx:44`, `:69`, and `:94`.
- Person windows intentionally use window Close instead of roster Back
  (`desk/pullouts/PeoplePullout.tsx`; `PeopleCore.tsx:600`). The scoped People
  close-to-Project focus return already has an assertion in
  `peopleCore.test.tsx:534`. Do not add a second return control to that window.
- Project attention/Plan/Signals and supporting folds are already composed
  (`ProjectRoomCore.tsx:2983–3035`). Project source openings delegate to
  `openRef` (`useProjectRoomController.ts:272`). The decision-citation test
  asserts the exact decision opens while the Room answer remains; History
  unavailable/empty/filter recovery is already asserted in `room.app.test.tsx`.
  These healed handoffs are preservation checks, not new repairs.

## Four-file implementation scope and smallest checks

| File | Bounded work |
| --- | --- |
| `web/src/pages/cores/PeopleCore.tsx` | Symmetric owning-section detail; snapshot-safe Prep draft clearing; intent-open Add wells in the existing composition. |
| `web/src/pages/cores/__tests__/peopleCore.test.tsx` | Both direction titles inspect the exact ID; Close returns to their owning row; parameterized delayed Add preserves a newer draft; refusal and Back/tab/person return retain the proper draft. |
| `web/src/features/project-room/ProjectRoomCore.tsx` | Pending Review becomes the head lead using the existing controller; Draft update stays available and quiet-source ownership remains intact. |
| `web/src/features/project-room/__tests__/ProjectRoomCore.test.tsx` | Pending/zero/unavailable review cases choose the truthful head action; pressing the lead renders the existing Review posture; source-add quiet state owns one primary. |

Use the existing focused Vitest files under the machine lock with isolated
HOME. Extend their recorded transport fixtures for addressed IDs and delayed
responses; assert rendered result and retained input, not only callback calls.
No backend, navigation, shared draft helper, global CSS or new browser file is
justified by this assessment. Root may reuse the generic isolated walkthrough
for populated 1440/393/narrow prep and Project evidence after implementation.

Unknown: actual current populated Prep geometry, report-direction inspector
execution behavior on a live isolated hub, pending-Add runtime reproduction,
keyboard/touch return and owner acceptance. Those are next-batch observations;
this document does not mark them passed. No broad redesign, History repair,
People storage migration or additional inventory is proposed.
