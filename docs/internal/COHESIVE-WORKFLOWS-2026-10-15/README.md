# Cohesive workflows

Owner goal: all interfaces cohesive, pleasant and functionally tested.
Base `7f3345745fb44f9238215ea980559f0cafa7a454`; branch
`feat/cohesive-workflows-20261015`, isolated tree `wt-cohesive-workflows-20261015`.
[Source audit](AUDIT.md), [settled direction and seam decisions](DESIGN.md),
[work/decisions](BUILD-WORK.md), [preferences/context](BUILD-PREFERENCES.md),
[people/common controls](BUILD-PEOPLE-CONTROLS.md), [bounded source counsel](REVIEW.md).

## Delivered scope

This is the next whole-app audit batch after #1215's Thread/Ask/notice refinement.
It fixes actual work loss and dishonest outcomes using the existing Workbench
component system. No new service, route, schema, framework or generalized writer.

- Workbench body drafts survive immediate Close, refusal and reopen, including
  empty text. Per-item saves run in order across reopen. Add and exact Retry
  share one pending guard; Coder Send preserves newer reply text. An empty
  template catalogue permits a real Blank workbench.
- Conductor and the opened lane report actual decision failures. Only the named
  already-decided409 is a race. Accepted decisions with failed reads offer read
  recovery, not another decision POST. Resourceful policy Retry owns the same
  guard as Save/Pause.
- Account Recheck sends the selected ref on the existing route. One pending
  action owns the UI; old reads cannot repaint newer results. Calendar Save A
  cannot close or erase a newer draft B.
- Speech test cleanup releases its own listening capture, including a deferred
  successful start after Close. Stop relinquishes ownership before transcription
  awaits. Shared transcription cleanup releases the floor in finally when no
  newer hold owns it, preserving the real success/failure outcome and newer audio.
- People calendar and meeting owner reads distinguish loading/failure/empty,
  with actual Retry and retained drafts. No invented cloud egress is shown for
  merely creating a Workbench item. Project source changes settle every watch,
  reread, report partial failure and retry only rejected IDs.
- Context fields/rows use the existing library. Local request IDs survive
  unavailable session storage and accepted receipts apply even if cleanup fails.
  The normal owned Thought is ThoughtWorkspaceWindow/Add a note; that active
  Reads well is repaired and tested, separately from the older Note picker.
- Get Info uses library actions and responsive bounded identity/properties.
  Canonical qualified sources resolve by kind and open the correct object;
  missing sources are disabled. New Project has a labeled library field.
  Empty Zone has no dead action; hosted app loading uses SurfaceState.
  Menu Left follows one-level Back and returns focus to the actual opener.
  Capability, Delivery and Workbench policy verbs use library Buttons.

## Before and design

Three bounded source audits cover the active manifest/hosts and work, settings,
objects, projects, people, meetings, transient controls and remaining custom
primitives. Source facts and unobserved visual hypotheses are separated in AUDIT.
Root inspected the load-bearing code before briefing. Six library direction
states were read at1440/393, `.tmp/cohesive/canvas-settled-{1440,393}/`, no page
errors. Initial sketch column misuse was corrected to the existing kit ledger
before GO. These sample directions are not runtime claims.

Real before walks use the preceding bundle228dd99cb87915de, fresh isolated DB:
`before-complete-1440/` and `before-compact-393/`, seven states each. Root read
observations and the populated Workbench/GetInfo/activeThought/calendar faces.
The actual immediate edit→Close→reopen loses the last Workbench edit on that
bundle. Early rig attempts needed People store initialization, the active owned
Thought route, correct People kind/tab/Links entry and the phone More menu.
Those stops are retained; they are rig setup/navigation errors, not extra product
bugs. The real active Thought route exposed a same-family storage seam missed
by the initial source census; it was added before final verification.

## Focused tests and wider-check findings

Root read actual collection names, test source and run tails. Lane A final
collection130: Workbench26, Template9, Conductor30, Gate7, Coder3, Lane55.
Initial focused run126pass/1fail exposed an impossible fixture approving then
denying one settled proposal; separate tests verify each decision once. Final
Lane55 and ordered-body26 pass; four unchanged files49 passed in the initial
run; Template9 passes again after a test mock callable typing repair. Exact logs
and the repaired Vitest list CLI overwrite incident are in BUILD-WORK.

Lane B final union243 across nine files. Final counsel/wire scope132pass in five
files: RunsOn52, micOwner5, speakToFill6, accountsPane54, accountsApp15; Calendar26
and Thoughts85 remain green. Local storage tests include acceptedA cleanup
refusal followed by newB set refusal and exact retryB. Initial two Connections
failures were a new test querying the row line instead of its enclosing well;
fixed without product waiver. Exact logs/names are in BUILD-PREFERENCES.

Lane C original140pass in ten files; follow-up22pass in lineage16 and common
controls6. Original old People test required the invented cloud badge and was
aligned to absence. Merged watch partial/settling/read recovery, retained People/
meeting drafts, menu hierarchy/focus and library action contracts are exercised.
The Info regression drives the real Desk opener with a same-ID meeting present.
Exact names and logs are in BUILD-PEOPLE-CONTROLS; overlapping scopes are not added
into an inflated combined count.

Initial complete quick:3949web passes/1failure,672affectedPython passes,
107sweeps with two existing xfails,17canon. The old accounts app assertion
required peer Recheck to stay enabled while another check was pending. Exact
failure reproduced; peer disabled/selected loading/exact{ref}/no secondPOST are
now asserted. First TypeScript found one new test mock union typing error;
its exact correction and focused rerun changed no product source.

Source counsel round1 found two concrete overlap paths: old RunsOn cleanup
could abort a newer hold during transcription, and policy Retry bypassed its
outer pending guard. Both were fixed in the one allowed recheck. Root also
found qualified lineage was compared only with bare IDs; same-kind narrowing
and canonical action identity are now tested. Final counsel RATIFY is source
only, not Muad'Dib's formal review. Root owns final build and live observations.

## Visual census and boundaries

The first quick captured109 actual Desk/surface/wing screenshots on built
`a1d6c523b9916c1d`, before the final mic/policy/lineage repairs. Those repairs do
not change ordinary sampled layout; this distinction is retained. A delegated
read-only pass inspected twelve desktop/phone pairs: Today, Brief, Week, Capture,
Needs you, Activity, Rhythm, Dictation, Live, Workbenches, Commands and Processes.
That twelve-pair subset found no pressing visual blocker; Needs393's large header leaves about two
complete rows, and Week1440's short lower-right window leaves one complete
meeting. These are observed density concerns, not proved broken scrolling.
Root read populated Conductor/Room/Person/Meeting, Memory,Agents,Setup,Engines,
Accounts plus actual Note/GetInfo/Workbench/calendar before states. A further
six pairs cover Places, Calendar snapshot, Components, Search palette, Desk and
Settings Guide. Phone Search has no obvious touch dismissal and two meeting
choices have identical text. Their existing distinct IDs must be preserved;
explicit Close and meeting date/time are the next bounded refinement. Populated
Calendar snapshot remains unassessed because its captured state cannot read.
The final actual walk also caught an attached-context footer squeezed into five
fragments beside desktop actions; its narrow full-action layout is corrected
and separately verified, beyond the finished source counsel.

Checks use machine lock, isolated HOME/DB, engine none and native capture off.
People uses an isolated file keystore; no owner DB, microphone, Keychain,
clipboard, provider account or owner tmux is used. Actual state/receipt/DB proof
is distinguished from replayed HTTP timing/failures. Speech ownership uses
focused software boundary tests, not real audio. General shared mic handoffs,
hardware performance, natural provider operation, remoteCI/fullnightly and formal
postmerge review are separate. Normal idle owner hub deployment follows merge.

## Final verification

On build6655519fc60c8605, complete quick GREEN:4039web in424files,672affected
Python,107sweeps with two existing xfails,17canon; final TypeScript exit0. Root
read actual tails and exits. Documentation generator/check covers ten outputs;
graph join check passes with fourteen existing subtype notes.

Root read fourteen-state real task walks at1440 and393,
`after-final-{1440,393}/observation.json`, no page errors: immediate Workbench
Close/reopen keeps last edit; Get Info opens the canonical Note and disables the
missing source; context attach/detach accepted refs are reread from the isolated
DB-backed endpoint despite declared session-storage refusal; People held read
then declared503 shows failure, actual Retry reads empty; delayed calendar A
write is forwarded to the real writer and preserves newer editor B. Synthetic
objects use real isolated writers; the lineage artifact uses the isolated
Database.plugins writer. HTTP timing/failure and session-storage substitutions
are explicit in observations; no actual provider/audio execution.

Real Search→NewProject graph cases pass at1440/393 (native touch on phone):
`graph-project-1440/20261016T054612Z-case.desk.project.name.ready-astra-1440/`
and `graph-project-393/20261016T055223Z-case.desk.project.name.ready-astra-393/`.
Root read provenance, initial/terminal observations and before/after shots;
real window POST200, field ready within1.1s, all nine sampled hit points owned,
no console errors. These prove entry and labeled field, not project creation.

Final attached-context correction:43collected/43pass behavior regressions.
Rebuilt fourteen-state task walks `after-footer-{1440,393}` pass on build
`c5c94f74427b5104`, no page errors. The desktop attached footer context has488px
and one readable line; phone keeps Finish/More. Root read observation, geometry
and actual screenshot. Context attach/detach and calendar A/B remain accepted.

The first post-CSS complete quick passed4039web,672Python and17canon but one
phone Door GitHub picker click timed out before the fence (106pass/2xfail).
Exact isolated `door-picked-393` reproduction passes unchanged in6.89s.
Complete unchanged quick rerun and deployment follow; this transient stop is
retained rather than waived or labeled a product fix.
Raw logs/images remain under `.tmp/cohesive/` and
`.tmp/evidence-shots/desk-sweep/`; no committed screenshot archive.

## Release check

Complete unchanged rerun `.tmp/cohesive/quick-final.log` exits0/GREEN:
4039web/424files,672affectedPython,107sweeps/twoexistingxfails,17canon.
The earlier phone-picker timeout did not recur; no product/test change or
waiver was made for it. Final bundle remainsc5c94f74427b5104. TypeScript passes
on final TS source (the later amendment is CSS only). Final task observations
are `after-footer-{1440,393}`; graph field cases use the pre-footer6655519 build
with unchanged New Project source. Canvas directions were separately read at
1440/393 and are not runtime proof. Formal postmerge review remains separate.

Next bounded pass: explicit Search Close and distinct meeting context, portal
mic hit ownership, empty Context meters and Needs button spacing; Week zoom
and populated calendar snapshot remain to assess. The whole-app goal remains
active until required refinements and their functional checks are delivered.
