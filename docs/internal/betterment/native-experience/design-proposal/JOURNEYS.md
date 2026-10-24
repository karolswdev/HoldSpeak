# Seven whole jobs for the native-feeling Desk

**Design record — UNCHECKED by Muad'Dib.** 23 October 2026. The owner's later
direction authorizes execution of the [delivery plan](../DELIVERY-PLAN.md),
superseding the original design-only hold. These seven Tuesday jobs remain
acceptance definitions, not claims of executed workflows, provider/native
coverage or owner aesthetic acceptance. The [47-review synthesis](../adversarial/SYNTHESIS.md)
separates inspection, checks, and owner acceptance.

The [nine paired canvas studies](CANVASES.md) make the main compositions and
return scenes inspectable at desktop and narrow sizes. They illustrate these
proposed acceptance paths; they do not execute them.

## Common desk contract

The product remains the current React/TypeScript/DOM stack and Workbench ×
Pop!_OS material: quiet frame, readable work well, library Button,
StateChip, EgressChip, ProvenanceChip, SurfaceWell, SurfaceFooter, ScrollHint,
MicButton, and the Desk compositor. No second stack, process model,
window manager, command bus, global task board, wizard, universal run monitor,
or automatic egress. Labels are one line: `New note`, `Talk`, `Run`,
`Retry`, `Save as note`, `Hand`, `Done`, `Nudge`, `Send`. Faces show facts and
verbs, not help paragraphs; no modal or zero counter. Refusals name
the failed rule and keep the next lawful verb.

Every object keeps distinct identities: application, window instance, and
resource/document. Shared axes are **W** identity/lifecycle,
**F** focus, **S** selection, **N** navigation/history, **C** command scope,
**E** editing/IME/voice/undo, **V** collection view, **T** transfer,
**X** panes/scroll, **A** async snapshot/dirty/retry/cancel, **O** operation,
permission/receipt, **K** keyboard/accessibility, **P** native boundary/feedback.
The application owns supported resource kinds. The window
owns location, history, selection, focused row, scroll and view mode. The
resource service owns content, revisions and effects. A menu,
toolbar, context menu and keyboard shortcut call the same scoped command with
the same target. A voice proposal uses that scope and asks for confirmation;
an owner-configured saved macro may fire by policy. Native editing keeps
the caret, selection, IME and undo. The web mic gesture captures its candidate editor/selection before focus
moves; Talk release validates and binds that generation before asynchronous
transcription/delivery. The native path binds the OS target at release.
A retained result cannot be inserted into a different target. The
[consumer input policies](../DESIGN-PROPOSAL.md#d5-editing-preserves-current-work-and-native-input-behavior)
retain selection replacement, Pad append and field replacement separately. If authority
is lost, the result stays recoverable in the originating task.

Mounted views do not own background work. Reopening a view uses stable
identity and its actual retained operation/result/receipt. The proposed
[lifecycle matrix](../DESIGN-PROPOSAL.md#lifecycle-by-application) distinguishes
minimize/close from reload/restart and unsupported continuation; these are
acceptance requirements, not claims that every producer already supports them.
Preserve Thought writing, Room identity, Today/Needs
projection, frozen Send bytes and replay key, exact source references, and
agent `launchId`/`turnId`/New-seen facts. Ask has no Keep or Bin: the durable
path is the saved thread and `Save as note`. Ordinary notes open in the active
`ThoughtWorkspaceWindow`, never the legacy `NoteEditor` route. See the
[application model](../APPLICATION-MODEL.md), [interaction
foundation](../INTERACTION-FOUNDATION.md), and the [synthesis corrections](../adversarial/SYNTHESIS.md#correct-the-map-before-building).

## J1 — Capture, develop, and reuse a thought

**Tuesday intent and fixture.** With synthetic `Thought AR-Review-01` (empty)
and prior Desk work `Repo holdspeak-demo`, capture “check the
API boundary before Friday”, develop it with keyboard and voice, save it, and
reuse the same thought as source. Start at Chair `Capture`; current resource is
the new Thought document, not a generic note form. The capture review warns
against legacy `NotePullout` as evidence ([capture review](../adversarial/capture_thought.md),
[notes review](../adversarial/notes_editor.md)).

**What the user sees and does.** (1) Press `New note` by pointer or Desk key;
the Thought window opens with title, body caret, `Talk` and `Done`. (2) Type,
or arm `Talk` with window/editor/selection and target generation captured,
speak once, and see text at that caret; `⌘Z` undoes it.
(3) Select a phrase, use IME if needed, correct it, and continue typing while
a transcript is pending. (4) Press `Done`; a durable Note id/revision returns
and the window closes to the prior Repo window. (5) Open `Thought AR-Review-01`
through the existing supported source handoff, add it to bounded Ask context,
and return with body and selection.

**Interruption and return.** A create refusal keeps the seed visible with
`Retry`; one retry uses one creation identity. Offline or
revision conflict keeps the draft and offers `Retry` or `Reload`; `Done` does
not close before an authoritative save. Close retains the document draft or completes its save; a failure leaves
the work available inline. Reload recovery must be backed by the existing
durable draft service before it is promised. Moving focus from editor A to B does not retarget speech. A late result
with stale editor/selection generation stays recoverable at its origin, never
in B or over newer input. Speech setup is an in-world
state, not a second page. At 393, title, body, `Talk`, and `Done` stack in one
scroll well; the caret remains the job and verbs stay 44px reachable.

**Coverage and proposed v1 choice.** `capture_thought`, `speech_dictation`,
`speech_learning`, `notes_editor`, `native_input`. Use the existing Thought/source-context handoff for the saved document
and selected passage, preserving its writer and source reference. Do not add
a parallel source picker.

## J2 — Record, import a meeting, and close its loops

**Tuesday intent and fixture.** Use synthetic `Meeting Architecture Review
2026-10-23`, with `review.vtt` and source-linked outcomes, to import or
record, inspect a result, make one decision, then move the commitment through
Today/Needs. Start at Meetings `Import` or `Record`; current resource is
`meeting:<id>` and its receipt. Intake, result, archive and
aftercare are separate authorities; [meeting](../adversarial/meeting_record.md),
[import](../adversarial/meeting_import.md), and [aftercare](../adversarial/meeting_aftercare.md)
reviews identify stopped/saved, provenance, and return boundaries.

**What the user sees and does.** (1) Choose `Import` and the known VTT fixture, or
press `Record`; the meeting id, source and actual route/egress are visible.
Import shows filename/format, import provenance and real versus synthetic
timestamp basis; its editable suggested date is distinguished from supplied
meeting time. A blank date follows the existing explicit backend fallback. (2)
Press `Stop` and see `Saved`, `Partial`, `Failed`, or `Stopped` with a receipt;
for import, genuine timing and speaker facts remain visible. An untimed
transcript offers source reading, without a fake timestamp seek. (3) Follow the existing intelligence policy: if import auto-queues under
the current setting/consent, show that run; otherwise press the existing
`Run summary`. Do not enqueue twice. The window shows the actual queued/run
identity and summary/source links separately from import completion. (4) Open one proposed decision, inspect its exact transcript segment,
and press `Confirm`; the decision keeps one durable ID, exact source segment/reference, owner,
due/review state where applicable and receipt. Meeting, Decisions and
Today/Needs project those canonical action/decision identities, so following
an action returns to that same reviewed source, not a separately created row. (5) Open Today
from the resulting action, choose `Done` or `Nudge`; `Nudge` enters the
frozen-byte Send well, where the owner reviews the frozen content and presses `Send`. Editing
happens before preparation; changing prepared content produces a replacement
prepared row with its own identity, not an in-place mutation of frozen bytes.
(6) Return to the meeting and see the decision/action lineage.

**Interruption and return.** Stop during recording must not claim a saved
meeting until durable persistence returns. Failed import retains source name/format/timing/date facts and its terminal
import receipt. `Re-import` reacquires the file and correlates the new attempt
to that accepted Meeting; it is not summary Retry. Temporary bytes need not
be retained. The bounded producer change must support that same-row attempt
before this recovery is declared delivered. Reopening uses the same meeting/run identity. After reload or restart,
read the durable job/result if supported; an interrupted or unknown run stays
truthful and offers only its supported recovery. A partial plugin result
names what is missing. A missed aftercare
signal is found through existing Meetings/Needs, not a new alert surface. A
prepared Nudge is not sent; a destination change requires a new preparation and source changes follow
the existing producer policy, including the deleted-source exception and
distinct Brief rule. Unknown Send outcome keeps the frozen bytes/replay key;
read back or replay that identity, then return to the same source/action. At 393, one meeting well stacks source, summary,
one outcome row and `Back`; the result never becomes a dashboard.

**Coverage and proposed v1 choice.** `meeting_record`, `meeting_import`,
`meeting_intelligence`, `meeting_aftercare`, `meeting_archive`, `decisions`,
`calendar_record`. The first calendar case uses one named event occurrence and retained
evidence snapshot. Recurrence keeps its existing scheduler semantics and is
a separate later case. Meeting, Today and Needs project canonical action IDs
through their existing adapters; they do not create duplicate commitments.

## J3 — Prepare a project review or 1:1

**Tuesday intent and fixture.** On synthetic `Project Atlas Review`, with
`Meeting Architecture Review` and `Note API boundary` filed, prepare a review
question and a 1:1 brief for synthetic report `Rina Patel`. Start from Project
Room or a People row; current resource is `project:<id>` or `people:<id>` and
the source set is explicit.

**What the user sees and does.** (1) Select the project and one source; the
Room shows identity, source rows and current selection. (2) Choose `Ask`; the
Ask window shows the selected source snapshot and a one-line question field.
(3) Press `Ask`; the answer shows named sources and its route/receipt,
then remains in the saved thread. (4) Press `Save as note` to create an
editable Thought note with exact source refs; there is no `Keep` or `Bin`. (5)
Open the saved Note's source and return to Ask without losing scope. (6) Choose
`Prepare` for Rina; review the brief and sources, then return to
Project Room or People row.

**Interruption and return.** A source that changes or disappears yields
`SOURCE GONE` and preserves the answer/draft; it never rereads a new source.
Recent thread A/B loads are fenced so A cannot paint into B. Closing Ask preserves the saved thread and current draft. Reopening binds
the same thread; any retained result is read by its actual request identity.
Reload must not silently resubmit. This design does not promise durable
background Ask where its producer has no persisted request/result authority;
interrupted requests keep recoverable input and a truthful retry action. A partial People
read is not an empty brief. At 393, Project/People identity remains above one
source list and composer; `Back` returns to the source row. The
[Ask](../adversarial/ask_whole_desk.md), [thread](../adversarial/threads.md),
[source](../adversarial/source_context.md), and [People prep](../adversarial/people_prep.md)
reviews support these boundaries.

**Coverage and proposed v1 choice.** `ask_whole_desk`, `threads`, `keep_answer`,
`source_context`, `people_prep`, `projects_room`. Keep the selected existing specialist/profile and its actual source scope;
switching profile does not relabel an older answer. People preparation stays
in the existing People/brief flow and returns to the originating person.
Project Room remains the return for project preparation; no prep wizard or
new Room for a person is introduced.

## J4 — Delegate work and inspect follow-through results

**Tuesday intent and fixture.** From `Project Atlas Review`, hand synthetic
item `Verify API boundary` to a configured agent, or run `Atlas weekly review`
with two selected sources; inspect the result and return to Project. Start at
Room or a selected Today/Needs row. Resources are `action:<id>`, `launch:<id>`,
`automation:<id>`, and project update.

**What the user sees and does.** (1) Select the item and press `Hand` or
`Run`; the face shows target, source refs, account/engine, and egress chip.
(2) Review the existing Hand preview and instruction. Use `Launch`, or
`Start when one is free` at the current launch limit; an already-running
agent uses its existing Hand path. Semantic Hand is object-to-agent delivery,
not file move and not a new generic Start confirmation. (3) Switch windows while it runs; the
view may close, but the id remains in Agents or Workbench. (4) Open the result:
`launchId`, `sessionKey`, `turnId`, branch/worktree, used/changed resources,
last words, review result and durable `New`/seen state are visible. `Answer`
answers that agent wait; Gate `Approve`/`Deny` uses its separate authority.
Stop/Resume acts on the exact supported session, not the result text. (5) Return to Project and
see the linked result or update. (6) For a commitment, Today or Needs offers
`Done`, `Later`, `Drop`, or `Nudge`; Send remains explicit egress.

**Interruption and return.** If note/file succeeds but Hand fails, retain the
note id and retry only Hand. A queued hand can be cancelled from Agents before launch. A launched
agent with an undelivered instruction retains its launch/target and existing
`Send again` recovery; it is not relaunched. Delivery and seen state remain
different facts; terminal-gone/unknown retains the result and named receipt. A stopped or late automation names its parent run and outcome. At the
producer commit boundary, Stop winning suppresses later delivery; a write
that already won remains a named retained result. The owner's newer draft
is never replaced by that result. An unknown outcome remains unknown until
read back; closing the view is not Stop. A lost Send response replays the same key
and reads one terminal receipt. Two launches never share a ResultBlock. At
393, the Project row, one active run/result row and one next verb stack; there
is no global task board or universal monitor. The [agent](../adversarial/agent_hand.md),
[result](../adversarial/agent_result.md), [automation](../adversarial/automation_build.md),
[schedule](../adversarial/automation_schedule.md), and [Today](../adversarial/today_followthrough.md)
reviews define these retained identities.

**Coverage and proposed v1 choice.** `project_update`, `agents_conductor`,
`agent_hand`, `agent_result`, `automation_build`, `automation_schedule`,
`mcp_tools`, `today_followthrough`, `send_prepare`, `send_commit`. The first return target is the originating Project Room update/result row,
linked by exact project/run identity; automation occurrence and agent turn
retain their existing separate results. Apply the Stop/commit distinction in
[D6](../DESIGN-PROPOSAL.md#d6-outcomes-survive-their-originating-view), not a
shared generic cancellation policy.

## J5 — Explore and organise resources

**Tuesday intent and fixture.** Use registered synthetic repository
`holdspeak-demo` with `docs/architecture/README.md`, `src/app.ts`, two branches,
and `Drawer Review sources`; inspect a file, file its source, and create a
project from selected references. This is a workload for existing
registered-repository APIs, not generic OS filesystem access. Start from Go, a
repository object, or a Drawer; resource is `repository:<id>` plus a view-local
path.

**What the user sees and does.** (1) Open two windows of the same repository:
A at `/docs`, B at `/src`; each keeps history, selection, focused row and
scroll. (2) Select a range with click/Shift/primary modifier, sort or change
view, and use the same command from menu, toolbar or key. (3) Press `Enter` or
double-click a supported file; read it in a bounded document view. (4) Use
`Back`/`Forward`, switch windows, and return to the file without cross-window
mutation. (5) File a reference in the Drawer or select sources for New Project;
source identity and egress remain visible.

Supported operation matrix: read registered tree/path/file/status and open a
file by default. Edit only after a conflict-aware provider write exists;
current `writeFile` has no expected revision, so the proposal is read-only for
editing. Git `checkout`, `stageFiles`, and `commit` are separate operations
with branch/index identity. Copy, move, delete, OS file-manager transfer and
fake success are out of scope. Semantic Hand and Ask attachment are distinct. The first Ask job uses a
supported Thought source. A repository/file cannot enter Ask unless its
provider declares the real ask/material capability; unsupported retains path
and selection with a typed refusal and return, never whole-Desk fallback. If a path vanishes, keep selection and show `NOT FOUND` with
`Retry`; reject stale folder responses. At 393, use list → detail stacking
with one `Back`, one selection anchor and an announced scroll well. The [explorer review](../adversarial/explorer_repo.md),
[drawers review](../adversarial/drawers.md), and [components review](../adversarial/components_reference.md)
set this boundary.

**Coverage and proposed v1 choice.** `explorer_repo`, `objects_pullouts`, `drawers`,
`knowledge_drawers`, `memory`, `new_project`. The first resource job exposes read/path/inspection and actual Git status.
Stage, Commit and Checkout need their producer-specific refusal/retry case
before delivery. Additional same-repository windows retain stable instance IDs
and their independent history across restoration, as proposed in
[D2](../DESIGN-PROPOSAL.md#d2-separate-application-window-resource-and-work-identity);
migration of older default resource-window keys is part of that package.

## J6 — Configure and restore readiness

**Tuesday intent and fixture.** On synthetic `Setup found: Local text engine`,
two connected accounts (`Acme GitHub`, `Acme Jira`) and destination
`Architecture Updates`, set one preference, adopt the text engine, choose a
per-job engine and verify a destination before the Atlas review. Start at the
actual Setup, Settings, Accounts or Engines door; current resource is a
configuration section and its operation receipt.

**What the user sees and does.** (1) Open Settings, change one value, and immediately see `Edited`, including the debounce interval,
then `Saving` and acknowledged `Saved`. Leave flushes or retains the newer
draft; return restores the field and its conflict/write state.
(2) Open Setup, inspect found rows and press `Use` for Local text; the receipt
says adopted, not “all jobs ready”. (3) Open Engines and assign
the engine for Ask or project update; Speech remains unassigned unless its
own readiness is proven. (4) In Accounts choose the explicit Acme identity,
check it, and return to the draft. (5) In Destinations check
`Architecture Updates`; its account/key and egress remain on that row. (6)
Return to the originating Atlas window with focus restored.

**Interruption and return.** A settings conflict keeps the later draft and
offers `Retry`. Account sign-in timeout or reload shows a named failure
and preserves the draft. Setup partial adoption retains per-row receipts and
does not repeat successful effects. Doctor is a separate readiness/repair
command, not a replacement wizard. At 393, one scrolling Settings or Setup
well shows section, rows and `Back`; no modal or hidden action is required. The [Setup review](../adversarial/setup.md),
[Engines review](../adversarial/engines_assignment.md), [Accounts review](../adversarial/accounts.md),
and [Settings review](../adversarial/settings.md) require these distinctions.

**Coverage and proposed v1 choice.** `engines_assignment`, `accounts`, `settings`,
`setup`. Setup `Use` returns the adopted profile reference; Engines selects that
actual profile in its existing assignment flow. Checking a destination reports
the supported validation outcome and does not send a sample delivery. A real
external Send retains its own prepared identity and receipt. Account
credentials, engine fit and destination keys remain separate objects.

## J7 — Operate and refine the desktop

**Tuesday intent and fixture.** Start with synthetic Desk state: Repo A, Ask
thread `T1`, Meeting `M1`, terminal readout, and a Components fixture adapter.
Arrange windows, operate through existing menus and keyboard, inspect a result,
report one issue with feedback, and return to work.
Start at Desk/Chair or Go; current resources are the distinct window instances
and their scoped documents/runs.

**What the user sees and does.** (1) Use Go, menu, Dock, palette or a
configured command to open or raise the named app/window/resource; one
compositor owns front state. (2) Drag, resize, minimise and restore Repo A;
scope, selection, scroll and focus return. (3) Use a view-local verb from
menu, toolbar or key; IME and undo keep priority. (4) Open the terminal to read
bounded output, follow or pause, and stop only a supported session; its receipt
stays with the session. (5) In the proposed Components reference, exercise the production pattern
with fixture data in loaded, empty, busy, failed and resumed states. The
first target is the real resource pattern; Settings follows. Until that seam
exists, the example is labelled `PROPOSED` / `LOCAL SPECIMEN` and cannot
claim shared production behavior. (6) At the operation, inspect its receipt/target and unknown/retry in the
existing ProcessCore projection; SendWell is the second outcome consumer.
Separately use per-window `Feedback` to capture window/element generation,
selected state, screenshot and audio. UiFeedbackHost retains a saved bundle
ID and transcription through the installed admitted speech route. Return to
Repo A; the report is independent of the operation receipt.

**Interruption and return.** A stale alias or missing scope says `NOT FOUND`
and keeps the prior window. A retained run completes while minimised and is
found on restore. A changed terminal generation rejects an old Stop. Report capture or mic-floor refusal keeps a local next action. Cancel
fences late capture/grants and returns to its origin. Once the bundle is
saved, transcription failure retains its bundle/path; `Retry transcription`
retries ASR only, without recapture/resave or replaying the domain operation.
Three sequential Settings reports in Firefox, including a cancelled capture
and failed transcription, are a named proposed acceptance case. No report
completion steals focus or changes the operation result. Presence is a review
boundary: the owner-disabled host stays off; no overlay or re-enable work.
At 393, Go and Dock remain the navigator; one window owns the work well, and
resize/minimise preserves the job, not a phone page. The
[windows](../adversarial/windows.md), [navigation](../adversarial/navigation_commands.md),
[terminal](../adversarial/terminals_processes.md), [feedback](../adversarial/feedback.md),
[activity](../adversarial/activity_context.md), and [presence](../adversarial/native_presence.md)
reviews support this boundary.

**Coverage and proposed v1 choice.** `desktop_workspace`, `windows`,
`navigation_commands`, `voice_commands`, `terminals_processes`,
`activity_context`, `feedback`, `components_reference`, `native_presence`.
Use existing Go/contextual application menu, Dock and front-window states
as the shell reference. Terminal actions bind the existing launch, session,
process and pane generation; following output is view state and Stop is a
domain operation. No global replacement session ID or approval UI is added.
Presence remains disabled until the owner changes it.

## Scope and remaining evidence

The coverage groups assign all 47 family IDs once; individual journeys also
use cross-cutting families from other groups. The [workflow map](WORKFLOW-MAP.md)
records those intersections and the primary delivery package. The proposed
v1 choices above resolve the initial consumer, resource restoration, calendar
scope, cross-app returns and late-operation policy. Concrete producer
revision/retry and Stop transaction designs must still be checked in their
bounded implementation package; current endpoint presence is not proof.

These are whole-job definitions, not executed workflows or owner acceptance.
Implementation later uses the existing compositor, commands, input/voice,
writers, receipts and Components fixture seam, then proves each named job at
1440 and 393. The draft remains **UNCHECKED — awaiting Muad'Dib** and starts
no product implementation.
