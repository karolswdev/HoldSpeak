# Project Rooms — Web power-user experience SRS

Document ID: `SRS-PRJ-WEB`
Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30

## 1. Experience objective

Ship a narrow real-work Web loop:

> Describe an outcome, install a real tested Watch through a guided interview, understand what changed, review/correct the resulting truth, generate an owner-ready update, and let a YOLO Steward complete one useful action while leaving a legible activity trail.

The Room is not a dashboard, generic graph, or project-management suite. It is a dense, quiet operating surface for understanding and moving consequential work.

## 2. Existing Web seams

The implementation MUST graduate the existing Web system:

- `DESK_APPLICATIONS` already lazy-declares Project Memory.
- `ProjectMemoryCore` already reads Projects, Meetings, Decisions, Artifacts, and “since last meeting.”
- Existing tests cover timeline composition, Project Ask, citations, Decision transitions, source opening, scoped restoration, and honest empty/error states.
- `DeskWindowFrame` owns window physics, focus, compact-sheet behavior, and head slots.
- `SurfaceWings`, `SurfaceSection`, `SurfaceRows`, `SurfaceLedger`, `SurfaceState`, `Material`, `CitationChips`, and `SurfaceFooter` define the Signal/Desk grammar.
- TanStack Query is the server-resource cache; Zustand owns workspace/UI state.
- Project is currently non-authorable in Web and opens a scoped singleton Project Memory surface.

Recommended feature boundary:

```text
web/src/features/project-room/
  api.ts
  model.ts
  commands.ts
  useProjectRoomController.ts
  ProjectRoomCore.tsx
  project-room.css
  components/
    ProjectSetupInterview.tsx
    ProjectSetupBrief.tsx
    ProjectWatchRecommendations.tsx
    ProjectProviderWizard.tsx
    ProjectWatchTest.tsx
    ProjectWatches.tsx
    ProjectOrientation.tsx
    ProjectFocusRail.tsx
    ProjectDeltaRiver.tsx
    ProjectReviewQueue.tsx
    ProjectEvidencePreview.tsx
    ProjectTimeline.tsx
    ProjectUpdateComposer.tsx
    ProjectStewardStrip.tsx
    ProjectStewardship.tsx
    ProjectInfo.tsx
```

`ProjectMemoryCore.tsx` MAY temporarily re-export `ProjectRoomCore` for route, action, and window compatibility.

## 3. Information architecture

### Immediate lenses

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-IA-001 | MUST | The window head MUST name the scoped Project, not “Project memory.” | T,D |
| WEB-IA-002 | MUST | The immediate lenses MUST be **Now**, **Timeline**, and **Updates**. | T,D |
| WEB-IA-003 | MUST | Review Changes MUST be a posture within Now, not a modal or separate application. | T,D |
| WEB-IA-004 | MUST | Evidence, Stewardship, Info, and Ask MUST remain reachable through the existing head-door/command grammar. | T,D |
| WEB-IA-005 | MUST | Steward state and pending review count MUST remain visible from Now. | T,D |
| WEB-IA-006 | SHOULD | A semantic Map/relationship outline SHOULD enter in V1; a graphical Map is later. | T,D |

### Window identity

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-IA-010 | MUST | V0 MUST preserve `open-project-memory` / `surface-project-memory` compatibility and its scoped opening behavior. | T |
| WEB-IA-011 | MUST | Reopening the currently scoped Project MUST focus the existing window. | T,D |
| WEB-IA-012 | SHOULD | After the normalized compositor supports dynamic subject windows, each Project SHOULD use `project-room:<projectId>` so Rooms can coexist. | T,D |
| WEB-IA-013 | MUST | Closing the Room MUST NOT archive the Project, stop its Steward, or discard its review state. | T |

## 4. Lifecycle and state distinctions

### Project lifecycle

```text
proposed → active ↔ paused → complete
                  ↘ cancelled
complete | cancelled → archived
```

Archive is a storage/presentation state, not a replacement for completion/cancellation.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-LC-001 | MUST | Project lifecycle, Project posture, source freshness, review attention, and Steward runtime MUST render as separate facts. | T,D |
| WEB-LC-002 | MUST | They MUST NOT collapse into one health score/color. | T,I |
| WEB-LC-003 | MUST | Pausing a Project MUST pause future scheduled Steward wakes by default but retain proposals, evidence, updates, and manual actions. | T,D |
| WEB-LC-004 | MUST | Archived Projects MUST open read-only by default with Restore in Info. | T,D |

### Room load state

```text
closed → loading → ready.current
                 → ready.partial
                 → ready.stale
                 → failed.empty
ready.* → refreshing → ready.*
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-LC-010 | MUST | A failed refresh with cached content MUST preserve content as partial/stale rather than replace it with a full-window error. | T,D |
| WEB-LC-011 | MUST | Every snapshot and mutation MUST carry Project revision. | T,I |
| WEB-LC-012 | MUST | A stale mutation MUST preserve the owner's edit and offer Refresh comparison; it MUST NOT overwrite silently. | T,D |

## 5. Creation and onboarding

The primary creation surface is a guided interview, not an unstructured chatbot or generic form. Its normative provider/Watch behavior is defined by `SRS_PROJECT_INTERVIEW_WATCHES.md`.

```text
new → interviewing → configuring_provider → ready_to_test
    → testing → test_passed | test_partial | test_failed
    → ready_to_activate → active
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-CR-001 | MUST | Project MUST become authorable through the shared creation/command grammar. | T,D |
| WEB-CR-002 | MUST | The first questions MUST be “What are you trying to accomplish?” and “What should HoldSpeak notice without being asked?” Name may be inferred and edited. | T,D |
| WEB-CR-003 | MUST | Within two questions, setup MUST show typed Watch candidates and a live brief of the durable configuration being assembled. | T,D,U |
| WEB-CR-004 | MUST | Each external candidate MUST enter a bounded Check connection → Discover → Clarify → Test flow and return without losing setup state. | T,D |
| WEB-CR-005 | MUST | Provider state MUST distinguish checking, ready, connection required, capability missing, partial, unavailable, and failed, with one exact next action. | T,D |
| WEB-CR-006 | MUST | Onboarding MUST NOT render six empty modules or require ontology configuration. | T,U |
| WEB-CR-007 | MUST | Dropping an object MUST expose the typed relationship verb before persistence. | T,D |
| WEB-CR-008 | SHOULD | V1 SHOULD add Transformation, Software/System, Research/Decision, Personal Build, and Blank template defaults. | T,D |
| WEB-CR-009 | MUST | Setup MUST autosave after accepted answers/selections and offer Continue setup after reload or close. | T,D |
| WEB-CR-010 | MUST | A live Watch test MUST show actual scope, observation time, entity count, up to five samples, present-state conditions, and partial/error state. | T,D |
| WEB-CR-011 | MUST | Activation review MUST show outcome, each precise Watch, cadence, action, YOLO, test result, and first-run behavior. | T,D |
| WEB-CR-012 | MUST | Successful activation MUST create one canonical Project/Desk object, open populated Now, and focus Run initial assessment. | T,D |
| WEB-CR-013 | MUST | Existing Projects without Watches MUST offer Set up Watches; Blank Projects MUST still offer link/drop material, add evidence/note, or speak a briefing. | T,D |
| WEB-CR-014 | MUST | Provider forms MUST remain fully usable when natural-language interpretation/model assistance is unavailable. | T,D |
| WEB-CR-015 | MUST | Info → Watches MUST reopen setup in edit mode with Edit, Test, Pause/Enable, and Retire per Watch. | T,D |

## 6. Now

Now renders three bands:

1. Orientation
2. Since last accepted review
3. Focus

At wide widths, Delta river and Focus rail may form a `3:2` split. At narrow widths, Focus precedes the river.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-NOW-001 | MUST | Orientation MUST show outcome/purpose, lifecycle, accepted posture when present, last review, source freshness, Steward state, and one primary verb. | T,D |
| WEB-NOW-002 | MUST | Primary verb order MUST be: Review changes; Resolve intervention; Continue/Set up Watches; Run initial assessment; otherwise Start work/Run Steward. | T,D |
| WEB-NOW-003 | MUST | Within 30 seconds, the owner MUST identify material changes, risks/blockers, pending decisions, stale/missing evidence, next checkpoint, and Steward state. | U |
| WEB-NOW-004 | MUST | Delta river MUST group by Decision, Risk, Dependency, Milestone, Signal, Commitment, Evidence, and Outcome gap—not source system. | T,D |
| WEB-NOW-005 | MUST | Each resting row MUST show kind, concise change, why it matters, observed time, source chip, and disposition. | T,D |
| WEB-NOW-006 | MUST | Focus MUST show at most five items by default, prioritizing judgment, worsening risk/dependency, stale commitment, checkpoint, stale evidence, and intervention. | T,D |
| WEB-NOW-007 | MUST | “Source unavailable,” “source stale,” “no detected change,” and “Project stable” MUST be distinct. | T,D |

## 7. Delta review

Required proposal view model:

```ts
interface ProjectProposal {
  id: string;
  projectId: string;
  projectRevision: number;
  kind: string;
  summary: string;
  whyItMatters: string;
  observedAt: string;
  sourceRefs: string[];
  sourceFreshness: "current" | "stale" | "unavailable" | "unknown";
  proposedPatch: unknown;
  comparedTruth?: unknown;
  disposition: "pending" | "accepted" | "deferred" | "dismissed";
}
```

### Review state machine

```text
idle → queue_ready → reviewing ↔ previewing
reviewing → editing → accepting → reviewing
reviewing → deferring → reviewing
reviewing → dismissing → reviewing
reviewing → conflict → refreshing_comparison → reviewing
reviewing → exhausted → checkpointed → drafting_update
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-DLT-001 | MUST | Wide review MUST show queue, selected proposal, source preview, current truth, proposed result, and verbs. | T,D |
| WEB-DLT-002 | MUST | Narrow review MUST show one proposal at a time with expandable comparison and persistent footer verbs. | T,D |
| WEB-DLT-003 | MUST | Verbs MUST be Accept, Edit & accept, Defer, and Dismiss. | T,D |
| WEB-DLT-004 | MUST | Edit & accept MUST edit the typed record, not generated narrative. | T,I |
| WEB-DLT-005 | MUST | Defer MUST support optional date/checkpoint and return only when due or materially changed. | T |
| WEB-DLT-006 | MUST | Dismiss in local YOLO MUST require no confirmation and MUST offer session-level Undo. | T,D |
| WEB-DLT-007 | MUST | Bulk Accept MUST be limited to compatible proposals of the same kind. | T,D |
| WEB-DLT-008 | MUST | Completion MUST summarize dispositions/conflicts and offer Finish review and Draft update. | T,D |
| WEB-DLT-009 | MUST | Every material claim/proposal MUST open its source through existing citation/source-opening behavior. | T,D |

## 8. Timeline

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-TIM-001 | MUST | Timeline MUST contain accepted reviews/updates, accepted Project truth changes, lifecycle/posture changes, Decision lineage, kept evidence observations, and consequential Steward results. | T,D |
| WEB-TIM-002 | MUST | Raw tool chatter MUST remain in Steward activity, not Timeline. | T,I |
| WEB-TIM-003 | MUST | Updates MUST form strong separators and open their frozen snapshot/evidence manifest. | T,D |
| WEB-TIM-004 | MUST | Truth changes MUST show prior/new value, actor, reason, time, and evidence refs. | T,D |
| WEB-TIM-005 | MUST | Existing tested Meeting/Decision/promoted-Artifact timeline behavior and source opening MUST survive via typed adapters. | T |
| WEB-TIM-006 | SHOULD | V1 SHOULD filter by semantic kind, actor, source, and time. | T,D |

## 9. Updates

### State

```text
generating → draft ↔ editing → saved → copied
draft | saved → superseded
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-UPD-001 | MUST | Drafting MUST be an editable document plane, never a chat transcript. | T,D |
| WEB-UPD-002 | MUST | Draft basis MUST show review/revision, accepted items used, excluded items, source coverage, and stale/unavailable sources. | T,D |
| WEB-UPD-003 | MUST | Editing prose MUST NOT alter underlying Project records. | T |
| WEB-UPD-004 | MUST | V0 verbs MUST be Save draft and Copy as Markdown using existing receipt/footer grammar. | T,D |
| WEB-UPD-005 | MUST | A new draft MUST NOT overwrite the last saved/accepted update. | T |
| WEB-UPD-006 | SHOULD | V1 SHOULD add Personal, Team, Leadership, Technical, and stakeholder presets. | T,D |

## 10. Stewardship and YOLO

### Runtime state

```text
off → ready → observing → comparing → acting → verifying → recording
recording → complete → sleeping → observing
active → pause_requested → paused → ready
active → stop_requested → stopped
active → failed | intervention_required
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-STW-001 | MUST | When active, Room MUST show restrained `YOLO ON · local owner`; broad authority MUST NOT use repeated warnings or danger styling. | T,D |
| WEB-STW-002 | MUST | V0 MUST provide Run Steward now and one successful observe→compare→act→verify→record loop. | T,D |
| WEB-STW-003 | MUST | Now MUST show compact state/current step/heartbeat/next wake/Pause-Resume/Stop/Open activity. | T,D |
| WEB-STW-004 | MUST | Pause MUST prevent future children/wakes and state what remains in flight. | T,D |
| WEB-STW-005 | MUST | Stop MUST be available without asking the model and prevent subsequent child work. | T,D |
| WEB-STW-006 | MUST | YOLO removes approvals, not failure truth. Failed action/verification MUST remain failed. | T,D |
| WEB-STW-007 | MUST | Material activity MUST show time, intent, action/tool, target, status, verification, resulting refs, and concise failure. | T,D |
| WEB-STW-008 | MUST | Repeated progress for one operation MUST update one row rather than append spam. | T |
| WEB-STW-009 | SHOULD | Scheduled wakes SHOULD be enabled after Run Now proves useful and MUST always show the next wake reason/time. | T,D |

## 11. Commands and keyboard

Semantic operations MUST use stable command IDs and the shared command vocabulary. Feature components MUST NOT add document-level keyboard listeners.

Required V0 command IDs:

```text
project.create
project.setup.answer
project.setup.accept-proposal
project.setup.continue
project.watch.test
project.watch.activate
project.watch.evaluate
project.watch.pause
project.open
project.add-material
project.refresh
project.review.open
project.review.next
project.review.previous
project.review.accept
project.review.edit
project.review.defer
project.review.dismiss
project.review.finish
project.update.draft
project.update.save
project.update.copy-markdown
project.steward.run
project.steward.pause
project.steward.resume
project.steward.stop
project.activity.open
project.ask
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-CMD-001 | MUST | Command deck in a frontmost Room MUST rank Project commands/scoped objects before global results. | T,D |
| WEB-CMD-002 | MUST | Review MUST support J/K or arrows, Space preview, A accept, E edit, L defer, X dismiss, command-Enter save, and layered Escape. | T,D |
| WEB-CMD-003 | MUST | Plain-letter commands MUST disable while text/select/contenteditable input owns focus. | T |
| WEB-CMD-004 | MUST | Delta, Timeline, and activity collections MUST use roving focus with one collection tab stop. | T,I |
| WEB-CMD-005 | MUST | Setup MUST use Enter to submit a one-line answer, Shift+Enter for newline, Cmd/Ctrl+Enter to accept/activate, layered Escape, arrows for lists, and Space to toggle a discovered scope. | T,D |
| WEB-CMD-006 | MUST | Voice MAY fill the current setup answer but MUST NOT submit, select a provider scope, or activate a Watch. | T,D |

## 12. Responsive Web

The Project window container—not browser viewport—is authoritative. The existing 560px surface breakpoint remains canonical.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-RSP-001 | MUST | At `>=560px`, Now uses river+focus, review uses queue+comparison, and update uses document+evidence rail. | T,D |
| WEB-RSP-002 | MUST | Below 560px, Focus precedes Delta, review becomes one card, evidence becomes expandable/switchable, and no primary workflow scrolls horizontally. | T,D |
| WEB-RSP-003 | MUST | Existing compact `DeskWindowFrame.is-sheet` behavior remains the phone-shaped Web authority. | T |
| WEB-RSP-004 | MUST | Coarse-pointer verbs remain visible and meet the existing minimum target; hover is not the only discovery. | T,I |
| WEB-RSP-005 | MUST | At `>=560px`, setup uses question plane plus live brief; below 560px the live brief follows the question plane in visual and DOM order. | T,D,I |

## 13. Empty, stale, error, and degraded states

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-STA-001 | MUST | Identity/orientation MUST render before independent Delta/Timeline/source/Steward resources finish. | T,D |
| WEB-STA-002 | MUST | One failed resource MUST NOT blank successful resources. | T,D |
| WEB-STA-003 | MUST | Empty copy: `No material yet.` Primary: Add first material. | T,D |
| WEB-STA-004 | MUST | No-Delta state MUST show last review and source coverage, with Add evidence, Ask, and Run Steward now. | T,D |
| WEB-STA-005 | MUST | Stale/unavailable sources MUST show last successful observation and retry/reconnect; cached claims retain observation time. | T,D |
| WEB-STA-006 | MUST | Evidence conflicts MUST show both claims/sources. | T,D |
| WEB-STA-007 | MUST | Model outage MUST preserve deterministic review, manual editing, evidence, saved updates, and activity. | T,D |
| WEB-STA-008 | MUST | Missing Project MUST show Project unavailable and recovery navigation. | T,D |
| WEB-STA-009 | MUST | Provider discovery/test failure MUST retain answer, interpreted Watch, discovered scopes, selections, and retry/continue-disabled paths. | T,D |
| WEB-STA-010 | MUST | Connection loss MUST preserve the exact active Watch and cached observation, mark attention, and offer reconnect/retest without deletion. | T,D |
| WEB-STA-011 | MUST | Error, degraded, and failure indicators MUST render in their own layout region and MUST NOT overlay or obscure functional UI elements. | T,D |

## 14. Accessibility and visual system

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-A11Y-001 | MUST | Every color-carried state MUST also use text/stable glyph. | T,I |
| WEB-A11Y-002 | MUST | Lifecycle, posture, freshness, attention, and Steward state MUST have distinct accessible names. | T,I |
| WEB-A11Y-003 | MUST | Review queue MUST announce position/total/kind/disposition. | T,I |
| WEB-A11Y-004 | MUST | Review and Steward verbs MUST name their target unambiguously. | T,I |
| WEB-A11Y-005 | MUST | Focus order MUST follow visible semantics and restore to source initiator. | T,D |
| WEB-A11Y-006 | MUST | At 200% zoom, essential labels/verbs MUST reflow rather than clip. | T,I |
| WEB-A11Y-007 | MUST | Reduced motion MUST remove spatial transitions without removing state/progress feedback. | T,I |
| WEB-A11Y-008 | MUST | (a) Setup MUST announce step, question, provider state, discovery count, selection count, and test result. (b) Suggestions MUST be labeled controls. (c) States MUST not rely on color. | T,I |
| WEB-A11Y-009 | MUST | Every text input in the Project Room MUST support voice entry through the existing OS mic affordance (Constitution Art IV.1). | T,D |
| WEB-VIS-001 | MUST | Use Signal tokens, Surface primitives, and feature-owned CSS; no raw colors/z-index. | I |
| WEB-VIS-002 | MUST | One window material; use type, hairlines, indentation, and depth—not nested dashboard cards. | I,D |
| WEB-VIS-003 | MUST | Updates read as filed dossier pages; evidence chips retain existing physical-reference language (design intent; verified by demonstration). | D |
| WEB-VIS-004 | MUST | Motion occurs only for refresh, disposition, Steward progress, and completed transitions; Room is quiet at rest. | I,D |
| WEB-VIS-005 | MUST | Every Watch evaluation, Steward step, provider call, and model invocation that crosses egress MUST display the compact egress badge (local / local+cloud / cloud, with target name) at its point of decision and in its activity/receipt row (Constitution Art III.2). | T,D |
| WEB-VIS-006 | SHOULD | Every accepted mutation, effect, and provider call SHOULD produce a visible receipt row in Stewardship activity or Timeline showing who, what, where, and outcome (Constitution Art V.2). | T,D |

## 15. Web read model and controller

Initial render SHOULD consume one coherent projection rather than an all-or-nothing browser `Promise.all` across raw authorities:

```ts
interface ProjectRoomSnapshot {
  projectId: string;
  revision: number;
  observedAt: string;
  project: ProjectOrientation;
  review: { lastAcceptedAt: string | null; pendingCount: number; proposals: ProjectProposal[] };
  focus: ProjectFocusItem[];
  sourceSummary: ProjectSourceSummary;
  lastUpdate: ProjectUpdateSummary | null;
  steward: ProjectStewardSummary;
}
```

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WEB-ARC-001 | MUST | `ProjectRoomCore` MUST compose; it MUST NOT own independent raw copies of every server collection. | I |
| WEB-ARC-002 | MUST | `useProjectRoomController(projectId)` MUST own lens/review selection, typed queries/mutations, conflicts, runtime reconciliation, command context, and focus restoration. | T,I |
| WEB-ARC-003 | MUST | Controller MUST expose discriminated state, not contradictory booleans. | T,I |
| WEB-ARC-004 | MUST | Domain clients MUST decode wire values; views MUST NOT consume `Record<string, unknown>` as their normal contract. | T,I |
| WEB-ARC-005 | MUST | Runtime events MUST patch/invalidate targeted query keys, not trigger whole-Desk refresh. | T,I |
| WEB-ARC-006 | MUST | Existing Project Memory tests for opening, timeline, citations, lifecycle, Ask, and empty search MUST remain or migrate to equivalent tests. | T |

## 16. Required Web scenarios

| ID | Scenario |
|---|---|
| WEB-SCN-001 | Outcome/watch interview discovers or validates a GitHub repo, live-tests a precise PR Watch, activates one canonical Project, and opens populated Now in under five prepared-fixture minutes. |
| WEB-SCN-002 | Meetings/Decisions succeed while a delivery source fails; useful content remains and source is unavailable, never “no change.” |
| WEB-SCN-003 | Five proposals can be previewed, accepted, edited, deferred, dismissed, and checkpointed without pointer or modal. |
| WEB-SCN-004 | Revision conflict preserves typed owner edit and refreshes comparison. |
| WEB-SCN-005 | Two disagreeing sources produce one conflict candidate with both sources. |
| WEB-SCN-006 | Draft update is evidence-linked and editable; prose edit leaves Project truth unchanged; copy emits activity/receipt. |
| WEB-SCN-007 | Run Steward now in YOLO performs and verifies one action without confirmation and updates Now/activity. |
| WEB-SCN-008 | Failed YOLO action remains failed/intervention-required and names exact operation. |
| WEB-SCN-009 | Pause prevents new child work; Resume continues; Stop prevents subsequent child work. |
| WEB-SCN-010 | At 390px container, review is one-card, no horizontal scroll, keyboard/screen-reader usable. |
| WEB-SCN-011 | With model unavailable, owner can inspect/link/review deterministic facts and save an update. |
| WEB-SCN-012 | Against one real EverDriven week, owner answers the operating questions in 30 seconds and edits rather than reconstructs the update. |
| WEB-SCN-013 | Missing GitHub auth preserves setup and offers provider recovery/Recheck; GitHub never appears active before a passing test. |
| WEB-SCN-014 | Connected-but-unmapped MCP/app appears partial/non-installable; no Watch semantics are invented. |
| WEB-SCN-015 | Editing an active Watch tests a new revision while the old one remains active and preserves all history. |

## 17. Implementation sequence

1. Extract typed API/model/controller from `ProjectMemoryCore` without changing behavior.
2. Add durable outcome/watch interview, native suggestions, and setup brief.
3. Add GitHub capability/discovery wizard, real Watch test, activation, and populated Now.
4. Broaden Delta and implement in-place review posture.
5. Extend Timeline and build Update document plane.
6. Add Steward strip, initial assessment/Run Now, activity, Pause, and Stop.
7. Add scheduled Watch actions, targeted RuntimeBus/query reconciliation, and degraded-state matrix.
8. Prove wide/narrow/keyboard/accessibility/real-dogfood scenarios; add real Jira parity if the proving Project requires it.
9. Add dynamic multi-Project windows and semantic/visual Map after V0 value is proven.
