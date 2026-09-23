# PHILO-2-03 — static pass, Astra

PASS: static

BRAIN: Astra; three completed Luna xhigh census/trace lanes; Astra reconciled the fragments and verified the execution owners.

SOURCE: `c42963bcd154b7d199de501370f1643e14a3921d`. Dirty at inspection: the supplied static-pass lane brief was untracked. The only tracked changes during this pass are its own roadmap/evidence records; no pre-existing tracked edits were found. Product source is unchanged from the atlas revision `1cd55bc829c1291cad661f93b2d90e61f001f179`. Input content hashes are sealed in the JSON. The supplied untracked lane brief is recorded as a dirty input and remains outside this commit; the graph-audit brief and all product evidence are tracked.

CONTRACT: `docs/internal/philo/briefs/static-pass-lane-brief.md`; `docs/internal/philo/briefs/graph-audit-brief.md` §§0–2, 6, 8, 9; graph schema v1; atlas v1 at the revision above; rig `scripts/graph_walk.py` v1.0.0 (inspected, not run). Phase 1 baseline: `675401a857b85336d4acaa8c65383dfc9636e4c8`.

RUNTIME: none. No frontend build, hub, database, engine call, device action, clock substitution or browser profile. No product process or e2e run.

JOBS: Expected results below preserve the story 01 selection. STATIC verdict describes the inspected wiring and branches. Observed execution: unverified for every job. Technical completion and owner usefulness are unverified; a wired verdict is not a live pass.

**J1 — Get past the gate. STATIC: broken.**
Expected: the desk; or the words kept with a receipt.
Source result: The normal Continue later, capture and Keep paths are source-wired. Named missing-model and rejected-token recovery instead opens New Project; it cannot repair the stated blocker. All 14 accepted failure categories were compared with the recovery map. No words or receipt were observed.
Evidence: web/src/desk/components/FirstWords.tsx:140; web/src/desk/components/FirstWords.tsx:473; web/src/lib/dictationRecovery.ts:69; holdspeak/db/onboarding.py:21.

**J2 — See what the desk asks of me. STATIC: wired.**
Expected: one SETUP row naming what is missing; the head counts what asks; an offer does not count.
Source result: The arrival reads assignments and renders a single setup demand with pending/failure branches. Head and offer branches are traced in ChairHome; the actual first screen and counts remain unobserved.
Evidence: web/src/desk/chair/ChairHome.tsx:487; web/src/desk/chair/ChairHome.tsx:2212; web/src/desk/chair/meetingPathBlocker.ts:83.

**J3 — Give the desk a summary engine. STATIC: wired.**
Expected: READY; the SETUP row gone ONLY because speech was already ready — with speech missing the row stays and says "No engine for speech" (`meetingPathBlocker.ts:83`), which is a second, separate case.
Source result: The selected LAN add/check/assign chain reaches the readiness and assignment owners. Speech remains a separate blocker. Cloud Check and preset Download alternatives have the failures below; they do not establish failure of the selected LAN path. No provider readiness is claimed.
Evidence: web/src/features/concierge/useConciergeController.ts:390; holdspeak/services/concierge_service.py:817; holdspeak/services/inference_assignment_service.py:1; web/src/desk/chair/meetingPathBlocker.ts:83.

**J4 — Have one meeting on the desk. STATIC: wired.**
Expected: a meeting row with its length; no summary yet; no error; import stops without an automatic summary.
Source result: Record/Stop reach MeetingService and the capture session. Import persists the normal meeting and explicitly leaves intelligence disabled without enqueueing it. The projected duration and row are source-backed; no recording, transcript or row was observed.
Evidence: holdspeak/web/routes/meetings/live.py:92; holdspeak/services/meeting_service.py:369; holdspeak/meeting_session/session.py:422; holdspeak/meeting_import.py:371.

**J5 — Know where the summary will run. STATIC: wired.**
Expected: the planned host, before the click.
Source result: The planned-route legs supply the host beside Run summary, before the click. Readiness gates the verb, and refusal has a named branch. This is source inspection, not a shot of the disclosure.
Evidence: web/src/pages/cores/history/CatalogRail.tsx:242; web/src/meetings/RouteDisclosure.tsx:52; web/src/meetings/summaryRoute.ts:74.

**J6 — Get the summary. STATIC: wired.**
Expected: the host that DID run it; the summary text; technical completion and usefulness reported separately.
Source result: The disclosed selection hash reaches admission and the queue; the owner-bound drainer reaches inference and persistence. The meeting summary slab renders intel.summary and attempt hosts from the run receipt. LAN availability, generated text and owner usefulness remain unverified separately.
Evidence: holdspeak/web/routes/meetings/intel.py:86; holdspeak/services/meeting_intel_service.py:138; holdspeak/intel_queue_conductor.py:227; web/src/meetings/MeetingSummarySlab.tsx:45; web/src/meetings/RouteDisclosure.tsx:97.

**J7 — Find it again after a restart. STATIC: unverifiable-statically.**
Expected: the same summary in two moves or less.
Source result: Durable summary/job reads and selection by meeting id are wired. The same-summary identity after an actual restart and the two-move bound require a live walk; they are not replaced here with the weaker claim that a DB reader exists.
Evidence: holdspeak/db/intel.py:495; web/src/pages/cores/HistoryCore.tsx:197; web/src/desk/chair/ChairHome.tsx:2037.

**J8 — Type by voice into another app. STATIC: unverifiable-statically.**
Expected: words at the cursor of the other app.
Source result: Hotkey admission, release and transcription kickoff have source owners. Native permission, focus, cursor target and delivery require the separately scoped owner sitting. The atlas already marks this case unreachable in the rig; absence of observation is not a product defect.
Evidence: holdspeak/runtime/dictation_capture.py:479; holdspeak/runtime/dictation_capture.py:589; web/src/pages/cores/dictation/hotkeyCustody.ts:121.

**J9 — Open what the desk remembered. STATIC: wired.**
Expected: the Rhythm face opens; a doorless receipt shows no Open.
Source result: The cadence receipt opens Rhythm and a doorless receipt has no Open. The deleted-meeting branch has a visible error path. Separate invocation/steering receipts pass the wrong source identity to the primitive opener, as the finding below records. The unscoped Desk memory window resolves to RecallFace; query, filter, source and owed-item controls are traced separately. Successful owed writes in its default recent view have a stale-result defect below.
Evidence: web/src/desk/components/SystemShade.tsx:192; web/src/desk/shell.ts:105; web/src/desk/store/compositorSlice.ts:137; web/src/features/project-room/ProjectRoomCore.tsx:1930.

**J10 — Get a brief, and another. STATIC: broken.**
Expected: the brief's own words stay on the face after the reload; after Generate again the RETURNED brief is the one DISPLAYED and it is RETAINED across another reload (not a stale face beside a new receipt); the same-day variant expects the producer to return the existing brief (`monday_brief_service.py:185`), the next-day variant must first PROVE the producer's date advanced (the clock mechanism named in the atlas) or is recorded blocked.
Source result: Generate assigns its returned brief and the latest read supports reload; same-day replay is explicit in the producer. Arrival hides a latest-load failure under No brief yet. Next-day production and retained returned text remain unobserved: no clock was advanced.
Evidence: web/src/desk/chair/ChairHome.tsx:466; web/src/desk/chair/ChairHome.tsx:556; web/src/desk/chair/ChairHome.tsx:1080; holdspeak/services/monday_brief_service.py:185.

**J11 — Develop a thought. STATIC: broken.**
Expected: a note, kept, with "Kept · time"; nothing hidden.
Source result: Typing reaches the debounced writer and working-note PATCH, but the footer reports filing state rather than a successful save and its time. Finish is a distinct lifecycle action. The preserved J11 recipe targets the wrong input and has an insufficient KEPT-only predicate; four J9 control recipes also use the wrong click target. No saved note was observed.
Evidence: web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:204; web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:484; web/src/desk/components/DeskEditor.tsx:224; docs/internal/philo/graph/atlas.json:4636.

GRAPH: [`static-astra.json`](static-astra.json). Interface and connection instances are scoped to each traced trigger so shared faces do not imply cross-action reachability. Nodes use the five schema kinds; links carry typed relations and source evidence. Atlas states are retained as the contract roster; an action-to-state link is kept only where its transition was separately established. A control displayed in a state does not prove that it produces that state. Atlas cases are copied verbatim; observations and council resolutions are empty. Exposure is encoded as `[exposure=…]` in labels because schema v1 has no exposure property. IDs identify declarations/gestures rather than evidence line numbers. Registry declarations and their caller gesture sites remain separate entry points.

COVERAGE:

- 4850 nodes; 713 typed links; 4184 trigger declarations. These are source declarations, not a count of usable controls.
- All 69 atlas cases copied verbatim; all 111 atlas state IDs retained; all 38 distinct atlas edge IDs have edge → interface → connection → action paths. The lane brief says 37 edges; the atlas contains 38. The atlas was not rewritten.
- {'applicable': 67, 'unreachable': 2} cases by atlas applicability. Exercised: 0. Unexercised: all 69, because the static lane forbids runtime walks. The atlas also excludes J8 native delivery and J10 next-day generation: the latter has no mechanism to advance the hub producer clock. Their cost is an unverified delivery job and unverified next-day brief behavior.
- 74 field-level claim reviews, by verdict: {'unresolved': 50, 'verified': 22, 'contradicted': 2}. A verified field does not certify the whole capability. Unresolved reviews identify the declarations/branches not established by the deep trace.
- 543 input files content-hashed. All 665 OpenAPI method/path operations have current source-census nodes; additional SPA/default-framework declarations are separate.
- Breadth includes individual JSX event and custom callback declaration sites (including parked sites), Button sites without a local event attribute, literal and generated Go verbs, application actions and aliases, keymap and browser listeners, startup/deep links, HTTP/WebSocket/MCP/CLI, runtime timers, connector inputs and engine response owners. The MCP finite helper/loop declarations were expanded without importing the product.
- Companion source declarations are included conditionally: SwiftUI callback sites under apple/App plus AIPI bridge, protocol and firmware callbacks. They are outside the selected deep jobs; no iPad/HSM/device work or observation was performed. Swift census is lexical: custom wrappers, target mounting and runtime-composed callbacks are not certified.
- Deep faces: FirstWords, Chair arrival/SETUP/Meetings/BRIEF, Concierge, meeting catalog/review/summary/recovery, Thought workspace/editor, SystemShade, unscoped Desk memory/RecallFace. A control can reach a local presentation action without a route or database table. Link absence in the breadth census is not an orphan verdict.

FINDINGS: ranked by cost to the owner. Product defects go to the council for a bounded Phase 3; tooling debt goes to shared live-pass preparation. No product or factual document correction was made in this lane.

1. **`fnd.astra.first_value_setup_wrong_owner` — product-defect.** High: a first-use speech or access failure sends the architect to create a Project, so the offered recovery cannot clear the named blocker. Tenets 2 and 3; Article VI.3.
   Expected: For missing_model or rejected_token, Setup reaches the engine/readiness or access owner that can resolve the named failure.
   Actual: Both categories enable Setup and disable retry. FirstWords routes every non-microphone Setup action to project-setup, which opens New Project. Microphone failures correctly use configure-setup; that separate branch does not repair these categories.
   Evidence: web/src/lib/dictationRecovery.ts:69; web/src/desk/components/FirstWords.tsx:473; web/src/desk/applications.ts:348.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

2. **`fnd.astra.thought_save_status_is_filing` — product-defect.** High: while writing a thought, the architect sees filing state rather than whether his newest words were kept. The selected first-use receipt is absent. Tenets 2, 3 and 7; Article VI.
   Expected: After typing, show the selected J11 save result Kept · time for the current note text, with a distinct pending or failure state.
   Actual: The writer schedules autosave, but the active Thought window foot reads KEPT or NOT IN A DRAWER from filing_status, and FINISHED from lifecycle. It does not bind the receipt to the last successful write or show its time. This is a presentation defect; source does not establish lost data.
   Evidence: web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:204; web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:484; pm/roadmap/holdspeak-philo/phase-2-the-graph/story-01-the-rulebook-and-the-state-atlas.md:75.
   Cases: case.j11.thought_keep.kept

3. **`fnd.astra.recall_recent_actions_lose_mode` — product-defect.** High for the architect with reports: after Done or saving an owner/date on the default Desk memory view, the row still shows the previous obligation and next action. Tenets 3 and 7; Article VI.3.
   Expected: After a successful owed-item write, the same Desk memory face displays the updated owner/date/completion or a named refresh failure. Retry on a failed recent read re-runs that recent read.
   Actual: The default no-query view loads recent results. Owed writes POST successfully and call refresh, but refresh is a no-op unless a nonempty search has run. The response is not merged into result; the row and its next-action verb remain stale until another read. This is a presentation-path defect, not a claim that the DB write failed. The same lost recent mode affects Retry: it calls search(), which invokes run with a blank query and no recent flag, so run returns immediately.
   Evidence: web/src/features/project-room/recall/RecallFace.tsx:196; web/src/features/project-room/recall/useRecallController.ts:143; web/src/features/project-room/recall/useRecallController.ts:159; web/src/features/project-room/recall/useRecallController.ts:193; holdspeak/web/routes/follow_through.py:111; holdspeak/services/follow_through_service.py:412; web/src/features/project-room/recall/useRecallController.ts:103; web/src/features/project-room/recall/RecallFace.tsx:375.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

4. **`finding.arrival_brief_load_error_swallowed` — product-defect.** High: a Tuesday brief load failure is shown as No brief yet, making persisted work look absent. Tenets 2, 3 and 7.
   Expected: Brief load failure is distinct from an actually absent latest brief.
   Actual: Arrival initializes brief=null, catches the latest-load error without setting a failure state, then clears loading and renders No brief yet.
   Evidence: web/src/desk/chair/ChairHome.tsx:466; web/src/desk/chair/ChairHome.tsx:1080.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

5. **`fnd.astra.shade_open_wrong_source_identity` — product-defect.** High within the broader Desk receipt loop: an invocation or steering receipt offers Open, closes the shade, and does not open its declared subject. Tenets 3 and 7; Article VI.3.
   Expected: Open follows the producer-declared invocation definition or coder-session target, or gives a visible refusal if it is missing.
   Actual: The invocation/steering producers use their own row id as source_id and a different target id in detail_url. The non-history/non-cadence Shade branch ignores detail_url and calls openPrimitive(source_id). An unknown source row id reaches console.warn and returns after the shade closes. The deleted-meeting history branch instead has a visible error path and is not this defect.
   Evidence: web/src/desk/components/SystemShade.tsx:180; web/src/desk/components/SystemShade.tsx:334; web/src/desk/shell.ts:105; web/src/desk/store/compositorSlice.ts:137; holdspeak/db/projections.py:408; holdspeak/db/projections.py:476; web/src/pages/cores/HistoryCore.tsx:151.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

6. **`finding.concierge_cloud_check_no_probe` — product-defect.** Medium: an alternative cloud setup Check never probes the configured provider. The selected LAN J3 path is separate. Tenets 2 and 3.
   Expected: Check reaches configured cloud destination and returns readiness evidence or failure.
   Actual: UI sends generate=true, route supplies no http_get, service returns NOT_SET without injected HTTP function.
   Evidence: web/src/features/concierge/useConciergeController.ts:498; holdspeak/web/routes/concierge.py:208; holdspeak/services/concierge_service.py:867.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

7. **`finding.concierge_download_no_completion_poll` — product-defect.** Medium: an optional model Download leaves the owner with zero progress and no terminal state in Concierge. Tenets 2 and 3.
   Expected: Download updates progress or reports completion/failure so the owner knows when the model is ready.
   Actual: Controller initializes received=0 and total, awaits the download request, and never updates or clears that progress; the source comment says polling is not implemented.
   Evidence: web/src/features/concierge/useConciergeController.ts:484; holdspeak/services/concierge_service.py:1779; web/src/features/concierge/useConciergeController.ts:363; web/src/features/concierge/ConciergeCore.tsx:120.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

8. **`fnd.astra.thread_keep_note_is_artifact` — product-defect.** Beyond the selected first-use jobs: the architect keeps useful thread text as a note but cannot find that result among Notes. Tenets 3 and 7; Article VI.3. Lower priority than losing first-use work.
   Expected: Keep as note creates a note from the selected assistant text, or returns a named refusal that says why it cannot.
   Actual: The active slash command sends as=note. The receiving service accepts as_kind but never branches on it; it always creates a plugin_output artifact and returns artifact_id. The callback chain is present, so the registry no-op is not the defect.
   Evidence: web/src/desk/components/ThreadComposer.tsx:609; web/src/desk/pullouts/ThreadPullout.tsx:1368; web/src/desk/threads.ts:461; holdspeak/web/routes/threads.py:298; holdspeak/services/thread_service.py:1755.
   Cases: No executable atlas case; the JSON position names the affected state or beyond-selection path.

9. **`fnd.astra.atlas_controls_not_bound_to_results` — tooling-debt.** High for audit confidence: J9 Open/Acknowledge/Dismiss and J11 editing can block before their intended controls fire; a loose KEPT check cannot prove the current words persisted. Tenets 2 and 3; Article IX.
   Expected: J9 triggers the named receipt control; J11 edits the active Note body. Result predicates bind the intended receipt/note and current content.
   Actual: Four J9 cases use click main.chair for Open/Acknowledge/Dismiss rather than the named controls. The normal Desk uses div.chair. J11 also fills .desk-window textarea although its editor is CodeMirror, then fills/clicks main.chair; its KEPT predicate is filing status rather than a bound note-content check. The rig directly uses these click/fill selectors. Reload actions ignore selector and are not part of this finding.
   Evidence: docs/internal/philo/graph/atlas.json:4636; web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:49; web/src/desk/components/DeskEditor.tsx:224; web/src/desk/chair/Chair.tsx:14; scripts/graph_walk.py:1768; scripts/graph_walk.py:579; docs/internal/philo/graph/atlas.json:3118; docs/internal/philo/graph/atlas.json:3253; docs/internal/philo/graph/atlas.json:3409; docs/internal/philo/graph/atlas.json:3587; scripts/graph_walk.py:1758.
   Cases: case.j9.shade_receipt_open.rhythm_face, case.j9.shade_open.door_stale, case.j9.shade_acknowledge.acknowledged, case.j9.shade_dismiss.dismissed, case.j11.thought_keep.kept

ORPHANS: derived from typed links and exposure; candidates are not automatic defects.

- The invocation/steering receipt door is a confirmed wrong-target chain at compositor resolution (finding above). The Thread Keep declaration is not a dead registry stub: its composer owns the action; the wrong persisted result type is the finding.
- Internal heartbeat/drainer, engine response and protocol nodes need no user Button. Parked scheduler and frontend sites are excluded from active-face claims. No historical exposure is invented for current code.
- The projection restore route/store has an internal consumer contract even without a SystemShade Restore button. No false documentation sentence was established; its lack of that button is not classified as doc drift.
- The census retains Button declarations without a local onX attribute as conditional candidates. Form submit, spread props and parent delegation can own them; they are not called dead without following that owner.
- Breadth-only nodes have no invented links. Their absence from the linked subgraph means not deep-traced, not unreachable. Dynamic loading, user connector packs and mount conditions require a runtime exposure census to close that limit.

UNKNOWN:

- No 1440/393 shot or on-glass claim: the specific static-lane prohibition on a product process supersedes the generic lane screenshot/full-suite rule. Only the schema unit fence and source validator ran in isolated HOME.
- No actual provider identity/result, persisted runtime row, terminal receipt, browser focus/geometry, native delivery, clock transition or useful architect output was observed. J7’s move bound and J8’s target remain unverified. First-use coverage does not establish 90% daily usability.
- Platform breadth establishes named source declarations. It cannot certify runtime-generated callbacks, plugin/user-pack contents, Swift custom-control expansion or every mounting configuration. No owner data/configuration was read to close these limits.
- Some Phase 1 field reviews remain unresolved, with source and reason in the JSON. Missing browser entries in a bounded inventory are extension candidates for story 07, not automatically contradictory claims. No unsupported doc-drift finding is emitted.
- Muad'Dib’s check is deliberately deferred by the lane sealing law until all four pass outputs are sealed. His output, branch and worktree were not read. Findings carry his position as pending; no agreement or council disposition is claimed.

PROOF: validator and additional source-contract checks are captured in `pm/roadmap/holdspeak-philo/phase-2-the-graph/evidence-story-03.md`. The focused schema test collected 17 tests and passed all 17. Full product suites, browser walks and screenshots are not applicable to this static-only deliverable.

AMENDMENTS: the story’s immediate other-brain-check clause is deferred to the four-pass council under the explicit sealing law; it is not silently certified. The atlas has 38 distinct edges rather than the brief’s stated 37. Cases and selected job contracts remain unchanged.

The Tuesday result remains unobserved. The source ledger identifies the recovery, save-status, receipt-target and brief-failure branches that can obstruct it.
