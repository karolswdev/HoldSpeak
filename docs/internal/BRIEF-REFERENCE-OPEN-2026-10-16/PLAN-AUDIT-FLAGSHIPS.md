# Flagship journeys — bounded audit

DRAFT / UNCHECKED — planning input, 2026-10-16. Candidate implementation
remains paused and unmerged. No product changes, tests, browser, build, or
owner hub access occurred during this audit.

Tuesday: the architect can find the next job, read its actual evidence, act
on the named subject, and return with the result visible. Tenets 2/3/5/7.

Anchor paths: `BriefView.tsx`, `TodayView.tsx` and `FollowThroughView.tsx` are
under `web/src/desk/pullouts/views/`; `PeopleCore.tsx` is
`web/src/pages/cores/PeopleCore.tsx`; `ProjectRoomCore.tsx` is
`web/src/features/project-room/ProjectRoomCore.tsx`; `openObject.ts` and
`standingPages.tsx` are under `web/src/desk/`; `DESIGN.md` is beside this file.

## Primary jobs and composition to keep

| Surface | Primary job | Existing useful composition |
| --- | --- | --- |
| Day | Prepare for the next meeting; finish recorded meetings afterward. | Time spine, next-meeting plate, real summary route and attempt receipts. |
| Brief | Understand changed work and obligations; open the cited source. | Standing pages, dated changes, person signals, selected-subject footer, folded Send. |
| Follow-through | Inspect accountable work, assign/date it, and close it. | Task/owner/date rows, exact source opening, in-place controls, exact Retry and Done/Undo. |
| People | Prepare a 1:1, review obligations both ways, and capture the agenda. | Next-1:1 plate, roster facts, retained person/lens, two obligation directions. |
| Project | Resolve what needs a decision, understand delivery progress, prepare an update. | Attention and Plan first, Signals beside them, supporting sections folded, dedicated review/update faces. |

## Ranked findings and proposals

1. **Blocked source journey: reading a source depends on normal-list visibility.**
   The previous diagnostic read found an open snoozed action and a pending-review
   artifact behind the owner's citations; neither is missing. Evidence:
   `DESIGN.md:13` records that read-only inspection. Source-inferred mechanism:
   `FollowThroughView.tsx:155` reads the ordinary board and `:188` silently
   ignores an absent focus; `openObject.ts:176` routes action refs there.
   Treat the retained backend candidate as partial work, not a completed repair.
   Compose an exact addressed read, expanded target, truthful hold/review chip,
   and a visible unavailable state. Include the artifact branch in the same
   journey. Normal lists and all source lifecycles retain their current meaning.

2. **Day gives old finishing work priority over the next meeting, and its
   decision shortcut offers less evidence than its meeting shortcut.**
   Prior actual-observed: the Oct14 production sweep at
   `/Users/karol/dev/tools/wt-deep-usability-20261014/.tmp/evidence-shots/desk-sweep/today-393.png`
   shows header/tabs and an old failed summary before NEXT, whose plate begins
   around y495. This is a prior shot, not current geometry proof. Current source
   still places finish rows before now/next (`TodayView.tsx:431`). Its TO DECIDE
   plate displays title/meeting title and directly confirms or defers the
   proposal (`:455`); no evidence/detail action is rendered there. Source-inferred
   interaction gap. Lead with the upcoming meeting and keep To finish below it;
   let the decision title open the existing proposal/review destination before
   the owner chooses a durable outcome. Reuse current controllers and routes.

3. **People offers unequal depth for the same commitment kind; creation fields
   precede much of the preparation evidence.**
   Source-inferred: You owe titles open CommitmentInspector
   (`PeopleCore.tsx:936`), while They owe you commitment titles have no opener
   (`:951`). Meeting action titles do open their source (`:959`). Three always
   mounted creation fields appear at `:923`, `:943`, and `:966`, before Last time,
   Open work and On the desk (`:972`). Give both commitment directions a clear
   detail action using the existing inspector, with its existing authority
   checked for that direction. Keep next meeting, agenda and obligation rows
   dominant; open the owning Add well on intent. Preserve drafts and calendar
   recovery. The existing People roster is a strength: the prior actual
   `/Users/karol/dev/tools/wt-deep-usability-20261014/.tmp/evidence-shots/desk-sweep/surface-people-393.png`
   shows a clear next 1:1, named person,
   and Open prep; it does not prove the unseen Prep geometry.

4. **Brief combines several reading levels and expands low-information
   source marks into separate rows on the phone.**
   Source-inferred ordering: all standing pages render before This week,
   lookback and People (`BriefView.tsx:426`, `:429`, `:478`, `:542`);
   `standingPages.tsx:154` adds the generic Standing pages heading above the
   already named questions. Prior actual-observed:
   `/Users/karol/dev/tools/wt-deep-usability-20261014/.tmp/evidence-shots/desk-sweep/brief-393.png`
   shows MTG using a full extra band beneath each
   meeting entry, consuming reading height. That shot contains no standing
   pages; it cannot establish their current size. Give the obligation question
   one clear lead, then changed-work rows with type/source/time together in the
   secondary facts; keep People signals reachable and Send folded. Use the
   existing readable row grammar and retain the full source sentence in its
   reader. Do not introduce another overview or another navigation level.

5. **Project's primary verb is independent of the attention it displays.**
   Source-inferred hierarchy, not an observed blocked action: Draft update is
   the head's primary (`ProjectRoomCore.tsx:429`), while pending Review is a
   ghost action (`:943`), even when unresolved work is the first body section
   (`:2985`). Choose the lead from actual work: open the pending review when
   it needs the architect; retain Draft update as a clear secondary action in
   that state. Preserve the existing attention/Plan/Signals structure and
   supporting folds (`:2983`, `:3020`). No wholesale Room redesign is justified
   by this audit. The inspected project-memory sweep image is unscoped Recall,
   so it is not evidence of scoped Project Room geometry.

## One coherent batch

Settle one native composition across the five surfaces, then implement and
verify the complete morning journey together: **next work → exact source →
evidence/detail → named action → visible outcome → return**. The source repair,
Day priority, Brief reading density, People detail symmetry, and Project lead
belong to that batch. Split builder ownership by files, not separate releases
of each symptom. Reuse SurfaceLedgerRow/SurfaceRow, SurfaceSection, SurfaceSplit,
SurfaceWell, SurfaceState, StateChip, ActionNotice, SurfaceFooter, StringGadget,
PadGadget, ScrollHint, AppHead/StatusStrip/Steps and the current source openers.
Exports are already present in `web/src/desk/surface/index.ts:3`, `:41`, `:117`.

Dependencies: confirm the exact proposed Day decision destination and People
inspector permissions before settling their controls; capture current populated
1440/393 faces for the source-inferred composition proposals; keep the paused
candidate's tested backend work available for integration. Navigation delivery
on a cold mount needs observation: the current zero-delay event is a risk
identified in source, not a reproduced failure.

## Measurable completion and parked work

- At 393 with a next meeting, its identity and preparation action are visible
  in the first content viewport; old summaries do not precede it.
- An explicit source press lands on the exact task/output, including held or
  awaiting-review sources; the task is expanded and its state is unchanged.
  A missing source or failed read has a visible truthful result and recovery.
- A decision can be inspected before Confirm; both commitment directions can
  be inspected. The rendered action and eventual receipt name the same subject.
- Add/edit wells retain newer drafts through refresh and refusal; Retry repeats
  the original request. Returning preserves the user's place and selection.
- At 1440 and 393, the lead job, primary action, owner/date/source facts and
  failures are readable; controls do not overlap. Capture actual outcomes for
  all five journeys, including populated, empty and relevant refused states.
- Keep canonical identity and encrypted People boundaries; a read never
  reactivates a hold, approves an output or creates a second obligation.

Park: new navigation/state frameworks, universal source-detail architecture,
model/page-engine changes, replacing Project's existing postures, blanket
renaming, decorative counters, global-list widening, and speculative completion
semantics for terminal tasks. Prior Brief-selection and Project-History failures
are already fixed in current source and are not new findings. Current contrast,
hit ownership, live layout, cold-open delivery and external/native behavior
remain unverified; this audit makes no claim that they pass or fail.
