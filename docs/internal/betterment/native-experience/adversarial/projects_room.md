# projects_room — adversarial review

workflow_id: projects_room  
job: See where a project stands, what changed and what needs me  
baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd (PR1430)  
reviewer task: review_projects_room  
evidence class: active React source and representative assertions read; no tests, live Desk walk, provider call, or owner observation

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at Go/Dock Projects or a project reference, reads health, next
date and newest update, opens one project by identity, then answers what needs
the owner, what waits on others, what changed, and what was decided. It also
includes Room source, Ask, Review, Update, Prepare, history, retry, and return.
`docs/USE_CASES.md:12` and the inventory record
(`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2403-2442`)
name only the broad job and shared codes. The active assertions show a better
baseline: ranked project rows and honest unread state
(`web/src/pages/cores/__tests__/projects.app.test.tsx:45-170`), history retry
without a false empty claim (`web/src/features/project-room/__tests__/room.app.test.tsx:1191-1260`),
and update/proposal recovery. The audit must carry those boundaries forward.

FINDINGS:

1. **P1 — The evidence brief is materially incomplete.** It records only the
first 120 lines of Room and first 100 lines of Projects
(`USE-CASE-INVENTORY.json:2410-2424`), omitting the controller, shell, postures,
and assertions that guard recovery. Owner cost: workers may duplicate useful
contracts, failing Tenets 2, 3 and 5. Correction: include
`useProjectRoomController.ts:122-205`, `ProjectRoomCore.tsx:1946-2204`,
`ProjectsCore.tsx:98-200`, and active tests; separate existing guards from gaps.

2. **P1 — Project identity is a single mutable window scope, with no rescope
or dirty-work policy.** The list opens `project:<id>`
(`web/src/pages/cores/ProjectsCore.tsx:166-174`); the compositor stores one
`surface-project-memory` instance and overwrites its scope on each open
(`web/src/desk/store/compositorSlice.ts:417-454`); the core remounts on that
scope (`ProjectRoomCore.tsx:1946-1951`). Opening another project can replace
active Review/Update/Prepare work without a stated return or draft rule. This
fails Tenets 3 and 5 and APP_ID/WIN_LIFE as an audit boundary; existing writer-specific draft guards may still protect text, and no actual loss was observed. Correction: preserve posture/draft
through a scoped handoff or use existing keyed instances; prove A→B→A and no
operation targets the wrong project. Do not add a second window manager.

3. **P1 — Fault isolation is uneven for the core question.** History and health
have named degraded faces, but proposal/source/nudge read failures are swallowed
(`useProjectRoomController.ts:187-205`), while NeedsYou and Sources return
`null` for every non-OK state (`ProjectRoomCore.tsx:619-635,1137-1146`). The
owner can see an empty Room when “what needs me” was not read. This fails
Tenets 3 and 6 and Article VI. Correction: preserve `absent`, render `degraded`
with a local failure and Retry, and keep receipts distinct from read failure.

## Convergence

Converge with `new_project` for `project:<id>` and source outcomes; first
consumers are DoorCore, Projects, and Room. Converge with `project_update` for
Room scope, draft/run identity, source refs, and receipts. Converge with
`source_context` and `memory` for `openRef`, About, citation, and
bounded search. `today_followthrough` and `meeting_aftercare` can reuse
Needs-you/action/decision identities and return openers. Keep faces separate:
their lifecycles differ; a generic “work explorer” would increase Tenet 1/3
cost without helping this job.

## User experience

Source inference: Projects ranks risk first;
Room puts headline and Needs you before quiet folds; History has filters and
retry; assertions retain an edited proposal and records draft after failure.
Not owner acceptance. The list waits for every project read before rows
(`ProjectsCore.tsx:104-115,139-142`), so one slow provider can delay the
Tuesday overview. Keep the stable-batch anti-jump guard, but define a bounded
loading/read-failed row. Phone Review remains unknown.

CONDITIONS: Expand the evidence set; settle scoped-window identity/return;
name degraded Needs/Sources/extras states with retry; define slow-list and
freshness boundaries while preserving current surface species.

MISSED:

1. A→B→A rescope while an Update/Review/Prepare draft is open (highest cost).
2. Needs/Sources/proposal reads failing independently while the Room stays up.
3. A slow or stale provider in the Projects fast path and its honest timestamp.
4. History item open, wing switch, and return with preserved project scroll.

TUESDAY: Promising for one already-loaded project; not yet reliable when comparing projects or when a core read is partial.

## Acceptance challenges

1. Open Projects with two projects; delay one Room read. The list must not
claim a state for that row, and either row must land on its exact `project:<id>`.
2. Open Project A, start an Update or Review, open Project B, then return to A.
The chosen one-window or multi-instance policy must preserve or explicitly
retain the draft, posture, selection, and scroll; no write may cross IDs.
3. Return a healthy Room with degraded `needsYou`, `sources`, and proposals.
Each section must say unavailable and offer Retry; it must not read as “nothing
needs me.” Retry only the failed read and keep unrelated sections.
4. Give History a stale source and long stream. Verify freshness, library
filters/search, real item open, and return to the same project place.
5. Confirm a proposal or write an update, fail the following Room read, then
retry/reopen. Verify one durable operation receipt, retained owner text, and
no duplicate write.

UNKNOWN: No tests, owner visual acceptance, 1440/393 capture, phone Review walk,
provider/native behavior, accessibility, performance, or freshness SLA was
proved. Anchors may drift; omission is not an observed failure.
