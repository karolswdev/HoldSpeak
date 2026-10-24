# Delivery plan: proposed native-feeling desktop

**Execution authorized by the owner — 2026-10-23.** Astra orchestrates Sol High
agents to deliver the complete plan. This task-specific direction supersedes
the earlier design-only hold and older reviewer-only/Luna defaults. It does
not imply owner aesthetic acceptance or a Muad'Dib review that did not occur.
The existing fast delivery cycle and domain boundaries remain.

This is the concrete implementation sequence derived from the proposed v1 [design proposal](DESIGN-PROPOSAL.md), [seven
journeys](design-proposal/JOURNEYS.md) and [paired canvas studies](design-proposal/CANVASES.md). It turns D1–D10 into ten bounded
packages. A package is a useful implementation boundary, not a new runtime enum, app registry, approval stage or deadline. The
[workflow map](design-proposal/WORKFLOW-MAP.md) links every audited family to one primary package; the family remains a traceability
unit, not a separate app.

## Delivery laws

- Keep React/TypeScript/DOM, the Desk compositor, existing public controls, RuntimeBus/Zustand, FastAPI and native adapters.
- Keep application, window, resource/document and operation identities distinct. Mounted views own local history, selection, focused
  row and scroll; existing services own drafts, writes, retained work and receipts.
- Use the existing command registry and extend its context. Commands are view-local, Desk-global or explicitly targeted. Configured
  voice macros do not become contextual proposals, and neither becomes a new command bus.
- Prefer an existing real consumer before extraction. Components is a fixture adapter and living design record; it is not a second
  production consumer.
- Keep CodeMirror, terminal, media, provider, calendar, account, Send and meeting authorities specialized. A shared composition does
  not erase a domain boundary.
- Resource work starts with registered-repository read/inspect. The current `repository.ts` writer accepts content without an
  expected revision, so no general file Edit is promised until a conflict-aware producer contract is settled. Stage uses explicit
  selected paths; commit uses the actual index; checkout names the repository and branch. Copy, move, rename and OS drop are not
  inferred from these APIs.
- Preserve active ThoughtWorkspaceWindow, active Project Room, Ask saved threads/Save as note, frozen Send bytes/replay identity,
  Today/Needs projections and disabled Presence. Keep the project-update Stop candidate parked until its identity and late-write
  boundary are proven.
- Each delivered face needs the existing 1440/393 visual and whole-job proof. The plan does not invent a local timing budget:
  measure representative scenes before setting one.

## Package dependencies

Packages are sliced, not all-or-nothing gates: existing P06/P07 services can serve P04/P07 before broader migration; P04↔P06 and P03↔P08 are not cyclic build gates. The minimal pilot is P01 with P02 and the first P10 reference. Next comes P08 Settings You, then P03 Thought/input, then P04 with the existing P06 source job; later packages migrate compatible domains.

## Order at a glance

1. **Foundation and first resource pattern:** [P01](#p01-window-view-and-command-foundation), [P02](#p02-resources-and-collections), and the first [P10](#p10-desktop-reference-feedback-and-native-boundary) Components seam. P10 starts here because shell/feedback/reference are cross-cutting, not because all P10 work waits until the end.
2. **Counterexamples before broad sharing:** [P08](#p08-readiness-and-preferences) Settings and [P03](#p03-authoring-input-and-voice) Thought/input prove that a useful common contract survives unlike consumers.
3. **Sourced work:** [P04](#p04-sourced-conversations-and-retrieval), then the first whole project/1:1 job in [P06](#p06-project-person-and-day).
4. **Compatible domain waves:** [P05](#p05-meeting-lifecycle), P06, [P07](#p07-delegated-and-repeated-work), with [P09](#p09-send) and P08 readiness at the point each job needs them.
5. **Adoption reconciliation:** finish P01/P02/P03/P04/P05/P06/P07/P08/P09/P10 consumers across all 47 families. This is one adoption review, not 47 gates and not a claim that every family needs a new face.

## Execution tracking

**Reality reconciliation — 2026-10-24 (owner check-in: 2026-10-23).** The 47 adversarial family reviews,
seven journeys, ten-package proposal and paired canvases define the work.
They do not measure implementation completion. Six workflow/component slices
have shipped: repository windows/read browser (#1438), Settings You (#1439),
Thought voice/Editing (#1443), source Ask/return (#1446), Note-version
pinning/saved links (#1448), and filed Project Note/source/return
([PR1453](https://github.com/karolswdev/HoldSpeak/pull/1453)).
Shared frame/zoom/growth and pending Stop repairs
are separate delivery, not additional completed packages. No full package,
whole seven-journey set, owner aesthetic acceptance or latest-main full-suite
green is claimed. Recipe closeout 115/117 measures another repair lane.

| Package | Actual delivery | Remaining adoption |
| --- | --- | --- |
| P01 windows/commands | Partial: repository identities, zoom policy #1444, arranged-growth #1449. Zoom/reload normal-rect repair #1454 has exact browser proof, local advisory RATIFY and required quick green; owner sizing stays separate. | View history/selection/scroll restoration, command origin, narrow chooser, usable default frames on a populated Desk, broad focus/close/reload behavior. |
| P02 resources | Partial: real registered-repository read/inspect and local reference. | Directory/KB second consumer, selection/range and broader provider/collection adoption. |
| P03 input/voice | Partial: active Thought captured target, recovery, writer/undo and shared Editing. | Ask/Settings/Pad policy adoption, native delivery, learning/macros and complete J1. |
| P04 conversations | Partial: Note-only version pinning, Ask/save/source/Thread doors and open/closed source return. #1451 removes the global run card that covered Stop. | Broader thread interruption/retrieval, Memory/Activity and complete J3. |
| P05 meetings | Modernization migration not started; existing meeting features remain. | Record/import/result/history/aftercare/calendar adoption and complete J2. |
| P06 project/person/day | Partial: filed-Note→Ask→saved links→exact Project return; five real-browser cases and required quick pass. | People/privacy/briefs, Today/Needs, updates/decisions, durable job return and complete J3/J4. |
| P07 agents/automation | Modernization migration not started; existing agent/automation features remain. | Hand/result/terminal/occurrence adoption and complete J4. |
| P08 preferences | Partial: Settings You truthful save/retry and shared Forms. | Other writers, Setup, Engines, Accounts and complete J6. |
| P09 Send | Modernization migration not started. Existing isolated real folder-byte jobs provide baseline evidence. | Producer/Needs/Delivery adoption, frozen identity/unknown/replay and complete cross-job egress. |
| P10 shell/reference/feedback | Partial: shared Resources, Forms, Editing and Conversation; local Files specimen delivered with P06; controlled Settings Firefox lifecycle #1455 proven through local speech stand-in. Feedback enabled; Presence off. | Ask report consumer/cross-window adoption, cohesive shell/visual and operation outcomes, configured-owner provider/hardware acceptance and measured native-feeling behavior. |

Final required quick and whole-tree typecheck pass for the first Project
slice. Integration corrections and bounded evidence are recorded in
[EXECUTION](EXECUTION.md). Browser contract repairs are #1452. The earlier
393 Send Back timeout has not reproduced; retained diagnostics do not prove
its cause is fixed. No latest-main full-suite green is claimed.

## Delivery adjustment: visible adoption alongside behavior

Behavior and architectural reuse are ahead of visual coherence. The latest
shots show working source/return behavior, but do not establish the desired
Workbench × Pop!_OS quality. Visual adoption is explicit unfinished work in
P01/P02/P03/P04/P06/P08/P10, not a final cosmetic step after every domain.

1. Finish the current bounded Room/list integration, including the observed
   return-focus attempt while its loading body is hidden. Reconcile the latest
   full-tape narrow Thought hit-ownership and late Room section movement
   findings before calling the existing cross-app path stable; the Files
   retained-refresh proof does not cover delayed Sources/Plan arrival. Ship
   only the actual passing slices.
2. Before widening migration to Meetings/Agents, reconcile the already-adopted
   Desk→resource→Note→Ask→Project and Settings views against their paired
   canvases and the living Components reference. Use the existing J1/J3/J5/
   J6/J7 paths, not a new app, gallery copy or workflow system.
3. Make the visual pass concrete in those consumers: consistent hierarchy,
   title and action placement, comfortable type/spacing, useful column density,
   bounded scroll, icons and restrained motion. The current Project return
   shot still gives inactive connection cards much of the viewport and shows
   empty list columns; Files working does not settle that layout. Revise the
   common composition/provider projection rather than applying local CSS to
   every window. Keep domain-specific writers and editor/terminal authorities.
4. Update the production composition, same-component reference state and
   affected canvas/contract together. Inspect populated, empty, busy and failed
   states at 1440/393, keyboard/selection/focus/return, and normal motion. Check
   the cross-app path, not only screenshots of one component. Measure actual
   responsiveness before naming a budget; retain the controlled Firefox Settings proof as a regression and extend
   report adoption to Ask/cross-window use. Owner visual judgment stays distinct from test success.
5. Continue P05/P06/P07/P08/P09 domain waves using those exercised patterns;
   reconcile adoption against all 47 map rows before calling the framework
   delivered. Preserve the original adversarial findings and unresolved scope.

**First visual slice: Project Room and the shared collection — built and
integrated quick green, pending merge.** The actual Room/reference cases pass
at1440/393, including stable retained refresh and presentation-ready exact
return focus. The public list contract and Canvas B/F track this adoption.
The following scope is implemented; owner visual acceptance remains open. Preserve the
Project lead and existing Ask entry; put filed work before optional Sources.
A Project without watched sources must not automatically expand three inactive
connection cards. Keep Sources compact with an explicit Add source action;
existing provider/account composition opens on intent or actionable failure.
Use the current ObjectList with an explicit optional visible-column set so
this Note-only provider shows Name/Kind rather than empty When/State columns.
Other consumers retain their declared columns, keyboard selection and Open
behavior. Retained-loading state belongs in the existing control row
so a background read does not push rows and pointer targets down the view.
Keep last-read qualification and current-read disabling; initial reads and
genuine failures remain explicit. This uses the existing section/state
composition rather than a new status controller. Mirror the same section in Components and revise Canvas B/F before
build. Project membership, Note reads, privacy and watch authority do not move.

This scope follows actual captures and source: ProjectRoomCore auto-opens
source setup when none is accepted, Sources precedes Files, DoorCore gives
each inactive provider a full row, and ObjectList always emits four columns.
The next bounded visual slice aligns short/busy/long Note and Ask content with
their head/foot controls, using existing editor/RunLine/footer compositions;
Settings You is the hierarchy comparator. Preserve reading/selection/scroll,
IME/undo, newer drafts, Stop and 44px targets; do not solve blank space by
shrinking every window or replacing specialized surfaces. Purposeful editor
and conversation workspace is valid; blank space alone is not a defect.
Change the balance where a concrete job loses hierarchy or access to controls.

Use the existing package sections, EXECUTION.md and pm/STATUS.md for these
facts. No extra approval stage, status database, review loop or percentage is
introduced. The next report names what merged, what whole job was observed,
what the owner has accepted visually, and what still contradicts the vision.

For each later implementation PR, name its package ID, journey and affected
workflow IDs. Update that package's section here with its actual PR and
remaining scope. Keep three facts separate: **delivery** (planned/in progress/
merged), **task evidence** (observed or unverified, with the existing evidence
pointer), and **owner experience** (open feedback or explicit acceptance).
One small PR can complete a slice without completing its entire package.

The [47-family map](design-proposal/WORKFLOW-MAP.md) holds the trace; it does not
become another task database. [TRACKER](../TRACKER.md) keeps actual recipe
merge state. `pm/STATUS.md` keeps the running-desk identity and open findings.
Update the affected contract, reference specimen and design/journey in the
same implementation change when behavior changes. Preserve the original audit
and dissent; append delivery and observation rather than rewriting history.

Progress updates state what completed, what was learned, what remains
unverified and the next bounded step. A green component check, a merged PR,
a completed whole job and owner visual acceptance are different milestones.

Each bounded delivery and its remaining scope are recorded in
[EXECUTION.md](EXECUTION.md). A slice can span several packages without
completing those packages or all 47 families.

## P01: Window, view and command foundation

**Delivery:** partial slice merged in [PR1438](https://github.com/karolswdev/HoldSpeak/pull/1438).
Independent repository view/resource identity, exact close/raise, compatible
restoration and sibling placement are observed in isolated browser cases.
The #1444 zoom policy repair preserves content auto height. A further bounded
shared growth clamp is [PR1449](https://github.com/karolswdev/HoldSpeak/pull/1449), reviewed and quick green: a low owner-arranged
fitContent window lifts into the work band when its material grows, keeping
saved height and identity. Full history/selection/scroll persistence,
cross-app command origin and the narrow visible chooser remain open. See [execution](EXECUTION.md).

**Primary families:** `windows`, `navigation_commands`.

**Source homes:** `web/src/desk/components/DeskWindow.tsx`, `web/src/desk/components/window/windowRegistry.ts`,
`SurfaceWindows.tsx`, `web/src/desk/compositor/CompositorLayer.tsx`, `workspaceStorage.ts`, `applications.ts`, `verbRegistry.ts`,
`keymap.ts`, and existing focus/resize tests. Extend these seams; do not add a window manager or command bus.

**First and second real consumers:** first `RepoWindow`/repository resource view; second Settings You to
challenge frame/focus and retained edit ownership; active Thought is the next editor counterexample. Components may mirror both through fixtures, but is not the second production
consumer. Existing Ask, Settings and Thought single-instance decisions remain.

**Authority and dependencies:** the compositor owns window id, geometry, front/minimized state and opener link. A view owns
location/history, selection, focused row and scroll. Domain services own content, drafts and work. P02 depends on this
identity/context seam; P10 uses it immediately.

**Acceptance:** J5 opens two locations of one registered repository with independent history, selection, focus and restore; J7
proves menu/key/context commands use one captured origin and that incoming completion does not steal focus. Test pending, stale,
close, minimize, reload, missing location and return. A result that survives close must reopen by identity.

**Documentation with the change:** update the application model, command context/source anchors, surface adoption record and the
relevant canvas/state story together. Do not claim broad adoption from the foundation alone.

## P02: Resources and collections

**Delivery:** first real repository read/inspect consumer merged in
[PR1438](https://github.com/karolswdev/HoldSpeak/pull/1438), with stale/refused
read recovery and a matching local Components specimen. Directory/KB are
still the second real consumer to prove; range selection, revalidation and
broader collection adoption remain open. See [execution](EXECUTION.md).

**Primary families:** `explorer_repo`, `objects_pullouts`, `drawers`, `knowledge_drawers`.

**Source homes:** `RepoWindow.tsx`, `repository.ts`, `holdspeak/services/project_repository.py`, `ObjectList`, `objectMenu.ts`,
`DrawerWindow.tsx`, `DirectoryPullout.tsx`, `KbPullout.tsx`, `SurfaceRows`/`SurfaceSplit`, and provider-specific membership
adapters.

**First and second real consumers:** first the registered repository read/inspect workload; second active Directory/KB collection
behavior. A Components resource fixture is not a second production consumer. Semantic object, directory/KB membership and repository
paths keep distinct providers.

**Authority and dependencies:** resource adapters own qualified identity, children, content, revisions, permissions and supported
effects. P01 supplies window/history/selection/command context. `explorer_repo` is a proposed workload, not shipped generic
filesystem access.

**Acceptance:** J5 reads a registered tree and supported file, preserves two window locations, selection/range/focused row, view
mode and scroll, and returns after a refusal. A missing path is `NOT FOUND` with Retry, not empty. Editing is read-only until a
conflict-aware write exists. Stage names explicit selected paths; commit names repository/branch/index; checkout has its own
dirty/index refusal. Copy/move/rename/drop and fake success stay out.

**Documentation with the change:** update provider capability boundaries, application model, workflow map row notes and the resource
canvas. Record which operations are actually supported; do not turn source presence into a user-job claim.

## P03: Authoring, input and voice

**Delivery:** first active Thought/CodeMirror voice slice is
[PR1443](https://github.com/karolswdev/HoldSpeak/pull/1443), fix re-check ratified; six browser cases and the required quick check pass. It shares the production
editor, captured-target binder and retained-voice recovery with Components
Editing through local IO. Settings/Ask/Pad policy adoption, native OS delivery,
learning and macro whole jobs remain open. See [execution](EXECUTION.md).

**Primary families:** `capture_thought`, `speech_dictation`, `speech_learning`, `voice_commands`, `notes_editor`, `native_input`.

**Source homes:** active Thought workspace/writer, `DeskEditor.tsx`, `ThoughtNoteEditor.tsx`, `surface/gadgets.tsx`, `MicButton`,
`micSession.ts`, `DictationCore.tsx`, `verbRegistry.ts` and the existing command/voice paths. The legacy NoteEditor route is not the
target for ordinary notes.

**First and second real consumers:** Settings field replacement has already challenged revision/draft ownership in P08; active Thought then
challenges selection/IME/undo using its own writer, followed by Ask composer append. These retain the per-consumer policies in D5;
Components is fixture-only.

**Authority and dependencies:** document services own Thought identity, draft, revision and save; CodeMirror owns native
editor behavior and its undo transactions; micSession owns one microphone authority; configured macros retain their policy. P01 supplies focus/command origin;
P08 is the counterexample, not a generic form engine.

**Acceptance:** J1 keeps first words when create/open refuses, inserts a late voice result only at its captured caret/generation,
preserves IME/undo and a newer draft, and returns to the originating resource. Test correction/journal state separately from
learning and command execution. No speech page or replacement editor runtime.

**Documentation with the change:** update interaction/input contracts, Thought/source handoff, voice policy, journey J1 and the B
canvas state story with the actual target and recovery semantics.

## P04: Sourced conversations and retrieval

**Delivery:** first selected-Thought source/Ask/save/return slice is [PR1446](https://github.com/karolswdev/HoldSpeak/pull/1446),
browser and required quick green. It owns context separately from floor selection, restores
an unchanged source range/scroll after open or closed-window return, refuses
stale range application, and saves editable qualified provenance. Components
shares the same controlled source view with local IO. The Note-version continuation below delivers server admission/pinning.
The first Project filed-Note source/return job is delivered; People source jobs, Memory/Activity
retrieval and whole J3 remain open. See [execution](EXECUTION.md).

The Note-version/Linked items continuation is [PR1448](https://github.com/karolswdev/HoldSpeak/pull/1448), independently rechecked
and required quick green:
server admission retains exact selected Note bytes without changing original
Memory scope; active saved Notes have real source/thread doors; Clear quote
and whole-Note Ask retain origin caret. This closes those #1446 follow-ons,
not the Project/People job. See the fifth delivery in [execution](EXECUTION.md).

**Primary families:** `ask_whole_desk`, `threads`, `keep_answer`, `source_context`, `memory`, `activity_context`.

**Source homes:** `AskPanel.tsx`, `ComposerWell`, `ReadingDocument`, `useReadingEndAnchor`, `askAbout.ts`, `ThreadToAsk.tsx`,
MemoryCore, ActivityCore and existing thread/memory/source services.

**First and second real consumers:** first Ask opened from a supported selected Thought; Project Room then People are
subsequent source-handoff consumers for the first J3 job, not a second conversation controller. Extract a shared Ask controller only
after an actual second conversation consumer exists; otherwise keep the controller local and share the composition. Memory and
activity remain their own providers. Components may show fixture retrieval states only.

**Authority and dependencies:** Ask owns request snapshot, thread, draft, stream and receipt; source adapters own qualified refs and
provenance; Memory owns search; Activity owns collector/context revision. P01/P02 provide source selection and return; P03 provides
editor/voice insertion; P06 supplies the project/person producer.

**Acceptance:** J3 carries a selected source snapshot into Ask, preserves reading and composer during streaming, fences A/B thread
loads, handles no hit, refusal, interruption and source gone, saves as an editable Note with lineage, and returns to the same
source/selection. Repository/file Ask stays unavailable without a declared provider capability and real qualified material/provenance/return contract;
unsupported retains selection and never broadens scope. There is no Keep/Bin path or generic retrieval explorer.

**Documentation with the change:** update source/Ask contracts, saved-thread and Save-as-note wording, provenance/egress placement,
J3 and B canvas handoff. Name display-only Memory hits and unavailable sources honestly.

## P05: Meeting lifecycle

**Delivery:** no modernization migration has shipped in this package yet.
Existing meeting capabilities and baseline repairs are not package adoption.

**Primary families:** `meeting_record`, `meeting_import`, `meeting_intelligence`, `meeting_aftercare`, `meeting_archive`,
`calendar_record`.

**Source homes:** `LiveCore.tsx`, `RecordOrb.tsx`, meeting capture/import/ intelligence services, `HistoryCore.tsx`,
`MeetingWindow.tsx`, `DecisionsView.tsx`, `CalendarSnapshotReviewCore.tsx`, `ScheduleCreateWindow.tsx` and existing meeting
persistence/receipt paths.

**First and second real consumers:** first a live recorded Meeting; second an imported Meeting using the same durable meeting/detail
identity. Calendar, aftercare and Decisions consume typed outputs without owning capture custody. Components is not a second meeting
implementation.

**Authority and dependencies:** capture owns microphone/session lifecycle; import owns source custody/parsing; intelligence owns
model run and result; calendar owns event/occurrence/schedule; aftercare and Decisions own consent and successor/action records. P01
supplies lifecycle; P09 supplies explicit Nudge/Send when a commitment leaves the Desk.

**Acceptance:** J2 records or imports, distinguishes stopped/saved/partial/ failed, runs intelligence with
queued/running/failed/finished identity, finds the same meeting after restart, reviews a source-linked decision, and returns through
Today/Needs. Import retains filename/format, real/synthetic timing, provenance, editable suggested date and its terminal receipt; Re-import
reacquires bytes for a correlated same-Meeting attempt, separate from summary Retry. Existing auto-summary setting/consent governs
whether Run summary is needed; never enqueue twice. Close does not cancel retained work; no automatic Send or invented capture resume.

**Documentation with the change:** update meeting state/receipt contracts, calendar boundary, aftercare/action projection, J2 and D
canvas state story.

## P06: Project, person and day

**Delivery:** first filed Project Note/source/return slice is
[PR1453](https://github.com/karolswdev/HoldSpeak/pull/1453), delivered from
`wt-native-project-source-wave7-20261023`. Five browser cases pass across
focused runs at 1440/393, including missing/moved/failed reads and local Files
reference. Navigation and Room received final Sol advisory RATIFY; these are
not Muad'Dib checks. Required integration quick and whole-tree typecheck pass. This is
transient job navigation, not automatic filing or added Project model scope.
People/brief/Today/Needs and full J3 remain open; source and shots are recorded
in EXECUTION.md.

**Primary families:** `people_prep`, `projects_room`, `new_project`, `project_update`, `decisions`, `today_followthrough`.

**Source homes:** `PeopleCore.tsx`, `PeoplePullout.tsx`, `ProjectsCore.tsx`, `ProjectRoomCore.tsx`, `DoorCore.tsx`,
`useDoorController.ts`, project-update editor/services, `DecisionsCore.tsx`, `IntelligencePullout.tsx` and `NeedsDrawer.tsx`.

**First and second real consumers:** first Project Room plus People source selection for J3; second Today/Needs return and one
decision/action lineage for J2/J4. People privacy, Project Room, Decisions and Today remain separate domain projections, not a
universal work explorer.

**Authority and dependencies:** project/person providers own scoped data and privacy; Door owns project creation/source linking;
update owns derived draft and run; Decisions owns successor lineage; Today/Needs owns its shared snapshot and action projection.
P01/P02/P04 are prerequisites; P08/P09 join where readiness or external Nudge is required.

**Acceptance:** J3 selects one project/person and source, asks, saves a Note, prepares a brief and returns with scope; J4 retains
update/run identity through close and late completion; J2/J4 return to canonical action rows. Partial reads are not empty; stale
drafts survive; Stop/Save/Publish/Send have separate outcomes. The parked project-update Stop candidate remains unverified until
these boundaries are real.

**Documentation with the change:** update Room/People/Today contracts, decision/action lineage, source and Send handoff, J3/J4, and
the relevant workflow rows. Keep the active Room; do not revive the DrawerWindow as a primary host.

## P07: Delegated and repeated work

**Delivery:** no modernization migration has shipped in this package yet.
Existing agent/automation/terminal capabilities are not package adoption.

**Primary families:** `agents_conductor`, `agent_hand`, `agent_result`, `automation_build`, `automation_schedule`, `mcp_tools`,
`terminals_processes`.

**Source homes:** `ConductorWindow.tsx`, `LaneWindow.tsx`/`ResultBlock`, `HandSheet.tsx`, `AutomationWindow.tsx`,
`WorkbenchWindow.tsx`, `UsedLines.tsx`, `ProcessCore.tsx`, `DeskToolInspector.tsx`, Workbench, agent/session services and kernel
receipts.

**First and second real consumers:** first Agent Hand → Conductor/Result; second Automation occurrence and terminal/run-monitor
inspection. The Components fixture can show states but is not the second consumer.

**Authority and dependencies:** kernel owns admission/receipt; agent launch, session, turn and reviewer authority stay distinct;
Workbench owns workbench/item/occurrence; terminal owns pane/session input and stop; MCP trace is a child projection, not Gate
authority. P01/P06 provide origin and return; P08 provides actual engine placement; P09 handles explicit Send.

**Acceptance:** J4 retains source/target through Hand, partial start, queued cancel, result answer/approval, close/reopen,
automation Stop/late outcome, terminal follow/pause/stop and unknown transport. Existing Hand preview uses Launch or Start when one is free; a delivery failure retries Send again without relaunch.
Result identity includes launchId/sessionKey/turnId and branch/worktree, used resources, review and New/seen. Answer and Gate
Approve/Deny keep separate authority. Two launches never share a result. No universal task
board, scheduler, monitor or replacement terminal.

**Documentation with the change:** update identity/receipt maps, operation and Gate boundaries, terminal exception notes, J4 and the
workflow rows.

## P08: Readiness and preferences

**Delivery:** first Settings You slice is [PR1439](https://github.com/karolswdev/HoldSpeak/pull/1439): shared production fields and
the existing domain writer now supply immediate Edited, captured Saving,
authoritative Saved and retained Not saved/Retry. The Components Forms
specimen uses that same composition/controller with isolated IO. The fix re-check and six browser cases pass; the final required quick is green. Setup/Engines/Accounts and
other preference writers remain later scope; this does not complete P08.

**Primary families:** `engines_assignment`, `accounts`, `settings`, `setup`.

**Source homes:** `SettingsCore.tsx`, `settingsPrefs.tsx`, connection and destination panes, `RunsOnCore.tsx`, `SetupCore.tsx`,
setup/assignment services and existing revision/receipt tests.

**First and second real consumers:** first Settings You dirty/save/conflict pattern; active Thought is its unlike input counterexample in P03.
Setup adoption, then Engines assignment/Accounts return exercise readiness with their own domain authority. Components is fixture-only.

**Authority and dependencies:** Settings writer owns field revisions and save policy; Accounts owns connection identity/permission;
Engines owns assignment/readiness; Setup owns found-resource adoption and doctor boundary. P01 supplies inspector window/focus; P03
provides the editing counterexample; P07/P09 consume readiness facts without copying credentials or keys.

**Acceptance:** J6 shows Edited immediately, then Saving/Saved, and later-edit conflict across section leave/return; adopts one found
engine without claiming all jobs ready; keeps account selection/sign-in failure/destination egress; returns focus to the originating
draft. No generic doctor wizard or merged account/engine/destination object.

**Documentation with the change:** update settings/readiness contracts, account/egress rules, setup-to-engine handoff, J6 and C
canvas state story.

## P09: Send

**Delivery:** no modernization migration has shipped in this package yet.
Existing isolated folder-byte browser jobs are baseline evidence, not external
delivery authorization or broad producer/receipt adoption. The earlier 393
Back/editor timeout remains unclassified until failure-state evidence exists.

**Primary families:** `send_prepare`, `send_commit`.

**Source homes:** existing `SendWell`/`NoteSendWells`, channel destination and account adapters, Delivery/Tracker history, kernel
send receipts and Needs return paths.

**First and second real consumers:** first project update and Ask/Note producer prepare rows; second Today/Needs Nudge and meeting
aftercare. The producer keeps its source/draft ownership; Send is not a generic outbound page.

**Authority and dependencies:** prepare freezes bytes, source and destination; commit is owner-authorized external effect; Accounts
supplies readiness; Delivery/Needs retain receipt lineage. P04/P05/P06/P07 provide producers; P08 provides account/destination
facts; P10 provides row/footer feedback.

**Acceptance:** J2/J3/J4 show egress at the action, preserve prepared bytes after source change, separate Discard/Retry/unknown
far-side outcome, use one replay key/receipt and return to source plus Needs/Delivery. No automatic Send, no lost receipt on a Needs
press, and no source-wide freshness gate.

**Documentation with the change:** update Send policy and receipt lineage, producer handoff, J2/J3/J4 and row proof. Keep
Edit-to-note distinct from external Send.

## P10: Desktop, reference, feedback and native boundary

**Delivery:** the Resources reference merged with its production consumer in
[PR1438](https://github.com/karolswdev/HoldSpeak/pull/1438). Forms (#1439), Editing (#1443), and Conversation (#1446/#1448) also use
production compositions with local IO. P06 adds the same Filed Notes section
as a local Lists example, with no real-resource IO. #1451 parks duplicate
run-scoped global status so producer Stop remains reachable. The controlled combined Firefox Settings lifecycle now has real 1440/393
proof: three saved bundles, capture cancellation, byte-stable ASR-only retry,
late-generation fencing and usable return. The configured speech seam uses
an isolated admitted stand-in; this does not prove owner hardware/provider
quality or latency. Shell/visual/operation adoption remains incomplete. Presence stays disabled.

**Primary families:** `native_presence`, `desktop_workspace`, `feedback`, `components_reference`.

**Source homes:** `DeskApp.tsx`, `applications.ts`, compositor/frame sources, `feedback/runtime.ts`, `UiFeedbackHost.tsx`, `ProcessCore.tsx`, `processWindowReducer.ts`,
`ComponentsCore.tsx`/ `DesignReference`, existing surface contract and Presence adapter/state.

**Production consumers and fixture mirror:** RepoWindow is the first production application/view consumer. Components renders
its same P01/P02 seam with isolated fixture data; it never counts as a production consumer. Operation-outcome projection starts
with ProcessCore, then SendWell challenges egress/unknown/replay. Separately UiFeedbackHost reports start from
Settings, then Ask challenges window-generation/return. Components remains fixture-only; Presence stays disabled.

**Authority and dependencies:** compositor owns arrival/front state; ProcessCore projects domain/kernel operation receipts, while
UiFeedbackHost owns window/element generation, screenshot/state/audio bundle and configured ASR retry. Reporting never changes
the operation outcome; Components uses a fixture adapter against the same pattern/controller; native Presence remains an explicit
disabled boundary. P01 is required, but P10 begins in Wave 1 and returns for cross-package reconciliation.

**Acceptance:** J7 restores Desk/window state, raises the intended target, keeps bounded terminal/editor exceptions, captures
reports with one saved bundle ID, ASR-only retry, cancel fencing and origin return, separately from operation target/egress/receipt
and unknown/readback/replay. Include three consecutive Firefox Settings reports with transcript status,
same-bundle ASR-only retry, cancellation/late-generation fencing and usable
Settings return; capture loaded/empty/busy/failed/resumed fixture
states as applicable. Validate 1440/393 layout and return. Do not re-enable Presence or claim portable-client coverage.

**Documentation with the change:** update shell/reference adoption, feedback/egress placement, Components consumer links, Presence
disabled record, J7 and the applicable canvas. Record measurements; do not invent a performance budget.

## Journey and package intersections

| Journey | Package path | First whole-job proof |
| --- | --- | --- |
| J1 Thought | P01 → P03 → P04 → P08 | Capture, caret/voice, existing Thought Done/writer, source return and settings/readiness interruption. |
| J2 Meeting | P01 → P05 → P06 → P09 → P10 | Record/import, stop/save truth, intelligence, aftercare, Today and explicit Send. |
| J3 Project or 1:1 | P01 → P02 → P03 → P04 → P06 → P08/P09 | Scoped resource, Ask, saved Note/brief, project/person return and account/egress boundary. |
| J4 Delegate | P01 → P06 → P07 → P08/P09 → P10 | Hand/run, result, retained operation, Stop/late outcome, follow-through and Send. |
| J5 Resources | P01 → P02 → P04/P06 → P10 | Two registered-repository views, inspect, file/context, project source and refusal recovery. |
| J6 Readiness | P01 → P08 → P10 | Settings conflict, Setup adoption, per-job engine/account facts and focus return. |
| J7 Desktop | P01 → P03/P07 → P10 | Go/Dock/menu, window physics, editor/terminal exception, feedback and fixture states. |

## Evidence and documentation close

Each package is complete only when its named real job is observed at the actual Desk in populated, empty, busy, refused,
interrupted, resumed and narrow states as applicable. Evidence must show entry, identity/target, useful outcome,
interruption/recovery and return; source conformance or a green check alone is not acceptance. Use isolated data and the existing
quick-check, browser and screenshot procedures. No provider/native action or owner-state walk is authorized by this document.

The package change and its record travel together: update the relevant surface/API contract, adoption inventory, workflow row,
journey/canvas state story and evidence pointer in the same implementation change. A specialized exception is recorded where it is
first needed (editor, terminal, media, provider, calendar, account, Send); repeated exceptions are a signal to improve the smaller
shared behavior, not to add a universal controller.

There are no dates, 47 package gates, new approval ceremony or full-suite claim here. The owner may change order after the first
real sitting. This is the owner-authorized implementation plan. Actual task proof, independent
review findings and owner visual judgment remain separate delivery facts.
