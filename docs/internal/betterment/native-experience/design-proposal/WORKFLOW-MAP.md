# Proposed native-experience workflow map

**Design record — UNCHECKED by Muad'Dib.** Owner-authorized execution began
2026-10-23; that direction supersedes the original design-only/no-action hold.
[Delivery plan](../DELIVERY-PLAN.md) and [execution](../EXECUTION.md) record actual
slices. This preserves the original design trace without claiming ratification.
Date: 2026-10-23 · source packet: [47 adversarial reviews](../adversarial/README.md), [synthesis](../adversarial/SYNTHESIS.md), and [inventory](../USE-CASE-INVENTORY.json).

This is a design translation of the 47 audited family IDs into a coherent
React desktop experience. It is not a production-readiness verdict, an
acceptance report, an executed-task claim, or a new runtime registry. The
audits are cross-cutting evidence and enablers, not 47 user applications:
the map covers 13 public jobs and 47 traceable family units. The proposed
compositions are a small set of view families. They do not add runtime
enums, an application catalogue, a universal workflow engine, or a second
operation ledger.

The source corrections are applied here: normal notes use the active
`ThoughtWorkspaceWindow`, not the legacy note editor; projects use the active
Room, while the project drawer is retained only for restoration; Ask has
saved threads and **Save as note**, with no Keep/Bin answer path; Presence is
off; portable clients are separate; `explorer_repo` is a proposed resource
workload, not a shipped filesystem product. The review verdicts and “204
challenges” are not promoted as product facts or test results.

## Proposed v1 design frame

Keep React/TypeScript/DOM, the Desk compositor, existing public controls,
Zustand/RuntimeBus, FastAPI and native adapters. Keep application, window,
resource and operation identities distinct. A mounted view owns its local
history, selection, focused row and scroll. Existing document services own
draft and write authority; retained background work survives a mount and is
not owned by it. Commands are view-local, Desk-global, or explicitly
targeted. Configured voice macros remain distinct from contextual voice
proposals and their retained policy. Share public controls and material, but
compose them as resource-browser, collection/detail, document/editor,
conversation, preferences/inspector, live-capture, workflow-editor,
terminal/run-monitor, or shell/reference views. CodeMirror, terminal and
media controls remain specialized. This is a proposed composition map, not
a new set of runtime types.

Contract shorthand below is expanded so that a letter never stands alone:

| Code | Shared contract to reuse |
| --- | --- |
| W | application/window identity, lifecycle and restoration |
| F | focus and activation |
| S | selection, focused row, anchor and range |
| N | navigation, history and restore |
| C | command context and target scope |
| E | editing, IME, voice insertion and undo |
| V | collection/resource adapter, view modes and stable rows |
| T | transfer and cross-window handoff |
| X | panes, bounded scroll, follow/pause and resize |
| A | async snapshot, dirty state, retry and cancellation |
| O | operation, permission, egress, receipt and honest outcome |
| K | keyboard and accessibility behavior |
| P | native boundary, feedback and measured performance |

Journeys are the proof order, not a queue of 47 screens: **J1** capture,
develop and reuse a thought; **J2** record/import a meeting and close its
loops; **J3** prepare a project review or 1:1; **J4** delegate work and
inspect/follow through results; **J5** explore and organise resources;
**J6** configure and restore readiness; **J7** operate and refine the Desk.

The explicit cross-cutting/enabler families are `desktop_workspace`,
`windows`, `navigation_commands`, `native_input`, `feedback` and
`components_reference`: they provide shell, input, outcome and proof seams
for the public jobs, not new user apps. `native_presence` is a disabled
operational exception, and `explorer_repo` is a proposed acceptance workload
for the resource-browser contract. Neither is presented as a shipped product
surface.

## Matrix

| ID | User job → useful outcome | Proposed primary view / composition → transition | Shared contract codes (expanded above) | Convergence: first / second consumer, or retained exception | Journeys | Key state and recovery decision bound | Delivery package | Proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `capture_thought` | Get a thought down now and keep the saved note. | **Live-capture** Talk seed → **document/editor** Thought workspace. | W, F, E, A, O, P | `notes_editor` / `speech_dictation`; keep saved-note identity separate from meeting audio. | J1, J7 | Bind the Thought identity before capture; retain words if create/open fails; show write result; return to the originating Desk/window. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/capture_thought.md) |
| `speech_dictation` | Speak and see text land in the focused application. | **Live-capture** mic session → focused **document/editor** or field. | F, E, A, O, K, P | `native_input` / `notes_editor`; keep command dispatch and meeting lifecycle separate. | J1, J7 | Capture candidate target before mic focus, validate/bind generation at Talk release before async delivery; late result cannot land elsewhere; distinguish pending/refused/partial; retry once at the same target and restore focus. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/speech_dictation.md) |
| `speech_learning` | Correct a phrase and replay or learn it later. | **Live-capture** journal/correction → **preferences/inspector** learning state or replay. | W, V, O, P | `speech_dictation` / `capture_thought`; learning journal is not Memory search. | J1, J6, J7 | Keep journal/run, raw text, correction and learned outcome distinct; replay failure stays visible; return to the source phrase and do not claim applied learning. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/speech_learning.md) |
| `voice_commands` | Say a phrase and run one configured Desk action. | **shell/reference** Commands board → target view or returned app. | C, F, O, K, P | `navigation_commands` / `speech_dictation`; configured macros remain distinct from selection proposals. | J1, J7 | Resolve configured target and exact-once policy before fire; refusal/no-match is named; result receipt returns to the originating view without stealing unrelated focus. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/voice_commands.md) |
| `meeting_record` | Record a live meeting and stop cleanly. | **Live-capture** meeting session → **collection/detail** Meeting record and result. | W, F, A, O, P, X | `meeting_intelligence` / `meeting_archive`; keep capture, intelligence and scheduling authorities separate. | J2, J7 | Meeting identity exists before recording; Stop records stopped/saved/partial/failed truth; hardware refusal is named; reopen the same record and continue recovery without implying a saved result. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/meeting_record.md) |
| `meeting_import` | Import a recording or transcript as a normal Meeting. | **Resource-browser** intake/transfer → **collection/detail** Meeting. | V, T, O, P, A | `meeting_record` / `meeting_archive`; parsing success is separate from intelligence success. | J2, J5 | Retain filename/format/provenance, real/synthetic timing and suggested date; accepted import has terminal receipt; Re-import reacquires source separately from summary Run/Retry and preserves Meeting lineage/return. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/meeting_import.md) |
| `meeting_intelligence` | Run meeting intelligence and read a useful, sourced result. | **Workflow-editor** Run state → **collection/detail** Meeting result/source. | W, X, A, O, P, V | `meeting_record` / `meeting_archive`; do not create a generic intelligence screen. | J2, J3 | Retain `meeting_id`, run and route; mounted window may close while work continues; queued/running/failed/finished are distinct; reopen the result with source links and retry the right run. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/meeting_intelligence.md) |
| `meeting_aftercare` | Review meeting outcomes and follow through on actions. | **Collection/detail** meeting review → **workflow-editor** action/Send or Today row. | V, C, A, O, X | `meeting_intelligence` / `today_followthrough`; do not merge aftercare into Decisions or Today. | J2, J3, J4 | Use canonical proposal/action IDs; incomplete summary remains reviewable; approval/refusal and external send have separate receipts; return opens the same meeting/action. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/meeting_aftercare.md) |
| `meeting_archive` | Find the same meeting and result after restart. | **Collection/detail** history → meeting reader/result. | W, S, N, V, X, A, O | `meeting_record` / `meeting_intelligence`; keep transcript/history domain-specific, not Explorer. | J2, J5, J7 | Search older pages, preserve meeting/result identity and reading position; missing or unfinished result is not empty; restart restores the last valid detail or a named recovery path. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/meeting_archive.md) |
| `ask_whole_desk` | Ask about Desk work and get bounded, cited evidence. | **Conversation** Ask → source/context detail or saved thread/note. | W, F, E, V, X, A, O, K | `threads` / `source_context`; keep meeting runs, Memory and Send boundaries. | J1, J3, J5, J7 | Snapshot prompt/context and thread before run; old reading stays put while streaming; interrupted/refused/no-hit states retain draft and evidence boundary; return to exact source/thread. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/ask_whole_desk.md) |
| `threads` | Continue a saved specialist conversation with turns and tools. | **Conversation** saved thread → Ask turn/tool result/source. | W, F, E, V, X, A, O | `ask_whole_desk` / `source_context`; retain mode, branch and tool policy as thread-owned. | J3, J4, J5, J7 | Read one thread by stable identity; fence overlapping loads; preserve draft, held work and partial result through close/reopen; source-gone and refused tools explain the return. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/threads.md) |
| `keep_answer` | Save a useful answer as a Note with its source. | **Conversation** answer → **document/editor** Save as note; optional result inspection only where supported. | W, E, V, A, O | `ask_whole_desk` / `notes_editor`; no Keep/Bin path and no generic result store. | J1, J3, J5 | Preserve answer/thread/source lineage; create Note identity before write; save failure keeps answer and offers retry; return to the same Ask turn and note. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/keep_answer.md) |
| `source_context` | Choose a project, object or source before an operation. | **Resource-browser** scoped picker → **conversation** or operation host with About/source chip. | W, F, S, V, C, T, O | `ask_whole_desk` / `threads`; share qualified refs, not a universal picker. | J3, J5, J7 | Start with supported Thought, then Project/People; hand off ref, available revision/quote, provenance and opener. Repository/file needs declared ask capability; unsupported/missing/stale retains selection, never broadens scope; return restores origin. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/source_context.md) |
| `notes_editor` | Write, edit and develop a note without losing text. | **Document/editor** Thought workspace → saved Thought or sourced passage. | W, F, E, A, O, K, P | `native_input` / `capture_thought`; keep fast Capture entry and Ask request identity separate. | J1, J3, J7 | Thought/document identity and draft authority are stable; caret/IME/undo survive voice and close; conflict or save failure retains newer text; return to the exact caret/selection. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/notes_editor.md) |
| `knowledge_drawers` | Keep reference material in a named drawer and use it as context. | **Resource-browser** KB collection → source/context handoff or member editor. | W, S, V, T, N, O | `drawers` / `source_context`; KB membership is not directory or filesystem transfer. | J3, J5 | Membership/edge identity is authoritative; scoped selection survives refresh; filing failure keeps the ref and retries; Ask returns to the same drawer/member. | P02 [package](../DELIVERY-PLAN.md#p02-resources-and-collections) | [review](../adversarial/knowledge_drawers.md) |
| `people_prep` | Prepare for a 1:1 with one report. | **Collection/detail** People → meeting/Ask/action workflow. | W, F, S, V, C, O, X | `meeting_aftercare` / `today_followthrough`; keep private People data source-owned. | J3, J4, J5 | Bind `people:<id>` and source snapshot; missing provider data is distinct from empty agenda; meeting/action creation reports outcome; return to the person and prep state. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/people_prep.md) |
| `projects_room` | See where a project stands, what changed and what needs attention. | **Collection/detail** Projects → active Project Room/update/source. | W, F, S, V, X, A, O | `new_project` / `project_update`; Room is active, project drawer is retained restoration only. | J3, J4, J5 | Project identity and Room scope survive open/close; partial or failed reads are not empty; stale updates keep local work; return to the same project section. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/projects_room.md) |
| `new_project` | Create a project from a name and selected sources. | **Workflow-editor** one-screen Door → Project Room. | W, F, S, V, T, A, O, P | `projects_room` / `source_context`; no universal picker/wizard. | J3, J5, J6 | Validate selected source identity and egress before create; partial link results remain retryable; project ID is durable before Room handoff; return keeps the entered name and sources. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/new_project.md) |
| `project_update` | Draft a true project update without freezing the Desk. | **Workflow-editor** update draft → Room result, Send or saved document. | W, E, A, O, V, X | `projects_room` / `automation_schedule`; update is a derived snapshot, not a canonical meeting/decision. | J3, J4 | Keep project/update/run identities; close or reload does not cancel retained work; Stop versus late delivery is explicit; Save/Regenerate/Publish/Send each retain its own receipt and retry. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/project_update.md) |
| `decisions` | Record, review and supersede an architecture decision. | **Collection/detail** decision list → **document/editor** decision and successor. | W, E, V, A, O, K | `meeting_aftercare` / `projects_room`; successor lineage stays distinct from meeting actions. | J2, J3, J5 | Keep decision ID, source and draft revision; stale edit refuses without losing text; supersede creates named successor and receipt; return preserves list position and provenance. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/decisions.md) |
| `agents_conductor` | See agent sessions, state and work that needs an answer. | **Terminal/run-monitor** conductor → result, Hand or Needs action. | W, F, S, X, C, A, O, P | `agent_hand` / `agent_result`; keep owner-pane authority and terminal controls distinct. | J4, J7 | Join launch/queue/session/turn identities; partial start is visible; close/reopen restores row and focus; answer/Stop/Resume routes to the owning pane without duplicate work. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/agents_conductor.md) |
| `agent_hand` | Hand selected work to an agent and steer it with permission. | **Workflow-editor** Hand/target → **terminal/run-monitor** launch/result. | T, C, F, V, O, P | `agents_conductor` / `agent_result`; repository transfer and OS file drops remain separate. | J3, J4, J7 | Bind source/target before Hand preview; existing Launch/Start when one is free retains queue/launch receipt. Undelivered instruction uses Send again, not relaunch; return to source selection/session. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/agent_hand.md) |
| `agent_result` | Read an agent result, review it and answer or approve. | **Terminal/run-monitor** result block → answer/Gate or retained lane. | W, F, E, X, A, O, K | `agents_conductor` / `terminals_processes`; Gate, terminal and reviewer authority stay separate. | J4, J7 | Preserve launchId/sessionKey/turnId, origin, branch/worktree, used/last-word/review and New/seen state; bounded scroll does not lose answer; held/failed/late result is named; close/reopen returns to the same result and decision. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/agent_result.md) |
| `automation_build` | Create one automation with instruction, sources and one result. | **Workflow-editor** automation → run/result/Send or Today. | W, V, A, O, C, P | `automation_schedule` / `source_context`; do not merge into a universal wizard. | J3, J4, J7 | Persist workbench/item/parent-run identity; source and engine facts stay visible; stale or failed run preserves draft and retry; close/reopen returns to the named automation. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/automation_build.md) |
| `automation_schedule` | Schedule or trigger repeat work and recover its result. | **Workflow-editor** schedule → **terminal/run-monitor** occurrence/result. | W, N, A, O, P | `automation_build` / `feedback`; scheduler/provider authority remains separate from agent review and Send. | J4, J6, J7 | Distinguish trigger, occurrence, run and delivery; missed/failed delivery is durable and retryable; mounted window is not the work; return opens the occurrence and receipt. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/automation_schedule.md) |
| `mcp_tools` | Run, inspect and retain a Desk tool operation. | **Terminal/run-monitor** operation trace → parent Workbench/Thread/Gate result. | W, C, O, P, V | `automation_build` / `agent_result`; share trace/receipt projections, not Gate authority or a second registry. | J4, J5, J7 | Bind caller, tool, target, egress and child receipt; held Gate is not generic MCP; failed/unknown outcome remains inspectable; return to the parent job. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/mcp_tools.md) |
| `send_prepare` | Prepare exact content and destination before sending. | **Workflow-editor** Send preview → retained prepared row/owner commit. | W, V, E, O, T | `send_commit` / `project_update`; producers keep their own draft/source boundaries. | J2, J3, J4, J7 | Freeze bytes, source and destination before prepare; source changes follow producer policy, including the deleted-source prepared-Send exception and distinct Brief freshness rule; credential failure blocks with reason; Discard/Retry preserve lineage; return to producer and Needs row. | P09 [package](../DELIVERY-PLAN.md#p09-send) | [review](../adversarial/send_prepare.md) |
| `send_commit` | Send a stored document and retain the receipt. | **Workflow-editor** owner commit → **shell/reference** receipt/Needs return. | W, A, O, P, C | `send_prepare` / `accounts`; external effect remains owner-authorized and separate from Settings. | J2, J3, J4, J7 | Commit only the frozen prepared identity; unknown far-side result is not success; retry uses its command/receipt; return keeps source and destination visible in Needs/Delivery. | P09 [package](../DELIVERY-PLAN.md#p09-send) | [review](../adversarial/send_commit.md) |
| `engines_assignment` | Choose what runs where and verify engine readiness. | **Preferences/inspector** assignment → operation host with placement/egress fact. | W, V, O, A, P | `ask_whole_desk` / `meeting_intelligence`; configuration is not execution and not a universal monitor. | J2, J3, J4, J6 | Distinguish profile/config revision from route/run identity; readiness refusal names host; timeout/fallback/unknown stays visible; return to the originating job with actual placement. | P08 [package](../DELIVERY-PLAN.md#p08-readiness-and-preferences) | [review](../adversarial/engines_assignment.md) |
| `accounts` | Connect an account, check it and keep its boundary clear. | **Preferences/inspector** account row → producer/destination handoff. | W, F, V, A, O, P | `new_project` / `settings`; do not merge account, calendar source and destination secret identities. | J3, J4, J6 | Stable account/connection ref and permission state survive recheck; multiple accounts are explicit; sign-in failure retains the draft; return to the selected producer without hiding egress. | P08 [package](../DELIVERY-PLAN.md#p08-readiness-and-preferences) | [review](../adversarial/accounts.md) |
| `settings` | Edit preferences and keep unsaved work visible. | **Preferences/inspector** section → saved state or conflict retry. | W, F, E, A, O, K, P | `accounts` / `engines_assignment`; keep Settings one inspector, not the framework itself. | J6, J7 | Dirty/debounce/pending/rejected/saved states remain distinct; later edits survive leave/return and conflict; Retry writes the newer revision; focus returns to the edited field. | P08 [package](../DELIVERY-PLAN.md#p08-readiness-and-preferences) | [review](../adversarial/settings.md) |
| `setup` | Check device readiness and use what was found. | **Preferences/inspector** Setup/doctor → adopted resource or originating job. | W, F, V, A, O, P | `engines_assignment` / `accounts`; Setup owns found-resource adoption, not a second Engines registry. | J1, J2, J4, J6 | Readiness check, adoption and permission are separate outcomes; failed repair is named and retryable; adopted identity is durable; return preserves the job that requested readiness. | P08 [package](../DELIVERY-PLAN.md#p08-readiness-and-preferences) | [review](../adversarial/setup.md) |
| `native_presence` | Keep the bounded native presence option honest without stealing focus. | **Shell/reference** disabled/parked host status; portable clients remain external. | W, F, O, P | `desktop_workspace` / `feedback`; retain Presence off and do not re-enable a broken host. | J6, J7 | Disabled state is explicit; renderer/close/focus failure cannot masquerade as a live app; no local overlay claims portable-client identity; return is to Desk. | P10 [package](../DELIVERY-PLAN.md#p10-desktop-reference-feedback-and-native-boundary) | [review](../adversarial/native_presence.md) |
| `desktop_workspace` | Open the Desk and find the work surface. | **Shell/reference** Desk arrival → first task/window. | W, F, C, K, P | `windows` / `navigation_commands`; keep arrival separate from Explorer features. | J1, J3, J7 | Restore Desk/app/window identity before presenting a task; first-task route has a clear target; failed restore names the missing resource; return raises the originating window without focus theft. | P10 [package](../DELIVERY-PLAN.md#p10-desktop-reference-feedback-and-native-boundary) | [review](../adversarial/desktop_workspace.md) |
| `windows` | Open, focus, arrange, minimise, restore and close windows. | **Shell/reference** compositor/window frame → mounted view or retained work. | W, F, N, X, A, O, K, P | `desktop_workspace` / `explorer_repo`; shared lifecycle does not force every view into Explorer. | J1, J3, J4, J5, J6, J7 | Distinguish mounted view, dirty document and retained operation; close/minimise/reload each have a decision; restore validates identity and returns focus to the opener. | P01 [package](../DELIVERY-PLAN.md#p01-window-view-and-command-foundation) | [review](../adversarial/windows.md) |
| `navigation_commands` | Navigate by Go, Dock, palette and shared commands. | **Shell/reference** command projection → target application/view. | W, F, C, K, O, P | `desktop_workspace` / `voice_commands`; Go, Dock and palette remain distinct projections over one registry. | J1, J3, J4, J5, J6, J7 | Classify global, view-local and explicitly targeted scope; unavailable target explains why; same command keeps identity across menu/key/voice; return leaves front-window authority intact. | P01 [package](../DELIVERY-PLAN.md#p01-window-view-and-command-foundation) | [review](../adversarial/navigation_commands.md) |
| `explorer_repo` | Browse a registered repository in multiple windows and open a supported file. | **Resource-browser** two locations → **document/editor** supported file; proposed workload, not shipped filesystem scope. | W, F, S, N, V, T, E, A, O, K, X, P | `objects_pullouts` / `source_context`; provider owns repository operations; OS transfer remains distinct. | J3, J4, J5, J7 | Bind repo/window/resource IDs; preserve per-window history, focused row and selection; unsupported mutation or undeclared Ask capability refuses honestly; stale read keeps location and meaningful retry; return to the same file/selection. | P02 [package](../DELIVERY-PLAN.md#p02-resources-and-collections) | [review](../adversarial/explorer_repo.md) |
| `objects_pullouts` | Open an object, inspect it and run an available object verb. | **Collection/detail** object list → qualified pullout/detail. | W, F, C, V, O, K | `windows` / `explorer_repo`; domain hosts retain their own detail and operation semantics. | J3, J4, J5, J7 | Resolve kind and qualified identity before opening; front-window command target is explicit; unsupported verb is withheld; failed verb leaves receipt and returns to the same object/list. | P02 [package](../DELIVERY-PLAN.md#p02-resources-and-collections) | [review](../adversarial/objects_pullouts.md) |
| `drawers` | Create, browse and use a named collection drawer. | **Resource-browser** Directory/KB/Room collection → scoped member/context. | W, F, S, N, V, T, O | `knowledge_drawers` / `projects_room`; provider adapters remain separate from Git and semantic object collections. | J3, J5, J7 | Create/file/browse/use are separate identities; selection/history survive refresh; stale provider result is not empty; failed filing retries and returns to the same drawer. | P02 [package](../DELIVERY-PLAN.md#p02-resources-and-collections) | [review](../adversarial/drawers.md) |
| `terminals_processes` | Inspect a running process or terminal and stop it safely. | **Terminal/run-monitor** session/process → bounded stop/recovery result. | W, F, E, X, A, O, K, P | `agents_conductor` / `agent_result`; terminal input, session control and ledger remain separate. | J4, J6, J7 | Join launch/session/process identity and pane generation; follow/pause is view-local; Stop timeout/unknown is named; reopen shows old output versus new run and returns focus/receipt. | P07 [package](../DELIVERY-PLAN.md#p07-delegated-and-repeated-work) | [review](../adversarial/terminals_processes.md) |
| `activity_context` | Inspect device activity and always-on context. | **Collection/detail** activity/context records → scoped source or operation. | W, F, V, A, O, P | `source_context` / `feedback`; keep browser collection, singleton context and provider account health distinct. | J3, J5, J6, J7 | Identify collector and context revision; paused/unavailable is not empty; refresh conflict retains newer context; return to the requesting job with source scope intact. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/activity_context.md) |
| `memory` | Search Memory and inspect a sourced result. | **Collection/detail** Memory results → source detail/Ask handoff. | W, F, S, N, V, X, O, K | `source_context` / `ask_whole_desk`; use existing memory search, not a generic Explorer. | J1, J3, J5, J7 | Stable result/source ref, query, filter and scroll survive reopen; parked/deleted source says unavailable; display-only hit cannot fake an opener; retry returns to the same query. | P04 [package](../DELIVERY-PLAN.md#p04-sourced-conversations-and-retrieval) | [review](../adversarial/memory.md) |
| `native_input` | Edit text with keyboard, IME, voice and undo intact. | **Document/editor** shared input seam → active Thought, Ask or Settings consumer. | F, E, A, O, K, P | `notes_editor` / `speech_dictation`; Settings revision fields remain a separate contract. | J1, J3, J6, J7 | Bind input target and caret/range; composition and undo survive async voice; newer draft wins over stale result; refusal returns focus without replacing text. | P03 [package](../DELIVERY-PLAN.md#p03-authoring-input-and-voice) | [review](../adversarial/native_input.md) |
| `feedback` | Inspect an operation outcome; separately report a UI issue with its exact window state. | **Shell/reference** ProcessCore → SendWell outcome projection; UiFeedbackHost Settings → Ask issue capture and origin return. | C, O, P, K | `navigation_commands` / `send_commit`; ProcessCore first, SendWell second for outcomes; Settings then Ask for report capture; retain two authorities. | J1, J2, J3, J4, J6, J7 | Operation keeps target/egress/receipt and unknown/readback/replay. Report keeps window/element generation, state/screenshot/audio, saved bundle ID and configured ASR; cancel fences late work, ASR retry does not recapture/resave or affect the operation; return to origin. | P10 [package](../DELIVERY-PLAN.md#p10-desktop-reference-feedback-and-native-boundary) | [review](../adversarial/feedback.md) |
| `calendar_record` | Review calendar evidence and schedule a meeting recording. | **Workflow-editor** calendar evidence/schedule → **live-capture** Meeting and archive. | W, V, N, A, O, P | `meeting_record` / `meeting_archive`; snapshot review and live capture remain separate. | J2, J3, J6 | Event/occurrence/schedule/meeting IDs stay distinct; readiness or arming failure is visible; cancel/restart does not erase evidence; return opens the same event or Meeting. | P05 [package](../DELIVERY-PLAN.md#p05-meeting-lifecycle) | [review](../adversarial/calendar_record.md) |
| `components_reference` | Demonstrate the same application behavior with isolated fixture data. | **Shell/reference** production pattern specimen → fixture state, linked to real consumer. | W, F, S, C, E, V, K, P | `explorer_repo` / `settings`; later People and Meeting collection/detail; never a fake reference app. | J5, J6, J7 | Fixture adapter exercises real identity/selection/edit/outcome states; production provider remains authoritative; unsupported state is labelled; return links back to the consumer and evidence boundary. | P10 [package](../DELIVERY-PLAN.md#p10-desktop-reference-feedback-and-native-boundary) | [review](../adversarial/components_reference.md) |
| `today_followthrough` | See what needs attention today and keep commitments moving. | **Collection/detail** Today/Needs → action/Send/People/Meeting opener. | W, F, S, V, C, O, K | `meeting_aftercare` / `people_prep`; share IDs/openers/receipts, not a universal workflow ID; Today and Needs remain distinct. | J2, J3, J4, J7 | Action/decision/meeting/source identity and status are canonical; Done/Later/Drop/send outcomes are explicit; failure keeps the row; return opens the source and preserves queue position. | P06 [package](../DELIVERY-PLAN.md#p06-project-person-and-day) | [review](../adversarial/today_followthrough.md) |

## Convergence judgments and counterexamples

1. **Window/view identity converges first in `explorer_repo` and `settings`,
   then challenges `ThoughtWorkspaceWindow`.** Resource history and Settings
   dirty state are unlike consumers: if both preserve independent window
   state, the contract has earned a second consumer. A single global
   selection would be a counterexample; it would make Desk selection erase a
   repository range or a document caret.
2. **Collection/detail converges through `people_prep` and `meeting_archive`,
   then serves Memory and Projects.** Stable rows, focused item, bounded
   scroll and source failure are reusable. A meeting transcript is not a
   filesystem tree, so `meeting_archive` must not become an Explorer variant;
   its domain adapter owns result status and provenance.
3. **Retained work and outcomes converge through Meeting intelligence and
   Automation occurrences, then Agent results.** The shared fact is durable
   operation identity and receipt, not a universal status enum. A mounted
   window must not cancel work when it closes; terminal Stop, meeting Stop,
   and external Send each retain different authority and recovery.
4. **Input and conversation converge through Ask and the Thought editor,
   with Settings as the counterexample.** Draft preservation, target binding,
   IME and focus return are shared. CodeMirror remains CodeMirror; Settings
   field revisions and conflict policy must not be forced into a document
   editor, and voice macros must not become caret insertion.
5. **The reference follows production.** `components_reference` first consumes
   the repository/resource and Settings patterns with fixture adapters. A
   copied “reference app” or a 47-family component gallery would violate the
   first-use tenets: it demonstrates surfaces, not a useful owner job.

This trace is design coverage: it shows where each audited family has a
proposed entry, identity/target, useful outcome, interruption/recovery and
return. It is not an executed task, owner acceptance, performance result,
or live Desk walk. No tests, build, provider action or owner-state operation
was run for this artifact. The proposal, seven journeys and static canvases
now define the design; the next step after Muad'Dib's check is the bounded
package sequence in [DELIVERY-PLAN.md](../DELIVERY-PLAN.md), not another
definition or canvas phase.


## Execution reconciliation — 2026-10-23

The 47 rows above retain the original design trace and adversarial evidence.
Owner execution authorization supersedes the old check-before-start wording
in the original proposal close. Execution is active; no whole-family or
visual acceptance follows from design coverage. Actual package delivery and
the revised behavior/visual adoption sequence are in
[DELIVERY-PLAN](../DELIVERY-PLAN.md#execution-tracking); PRs and bounded proof
are in [EXECUTION](../EXECUTION.md).

Observed partial consumers are registered repositories/resources, Settings
You, active Thought voice/editing, and Note-sourced Ask/save/linked source and
Thread return. The first Project filed-Note source job is delivered with five passing
browser cases and final required quick green; full Project/People J3 remains
open. The shared
reference mirrors those real compositions with local IO; it is not another
production consumer. Meeting, People/Today, Agent/Automation, broader readiness,
Send and shell/feedback adoption remain incomplete. No row gains a completion
mark from the old recipe closeout or from a green component test.
