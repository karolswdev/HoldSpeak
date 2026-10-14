# Work — deep usability audit, 2026-10-14

DRAFT — HOLD FOR SHIP. Audit source baseline `eb9a3266e` (#1201). The audit
below was read-only. Root subsequently authorized the bounded implementation
recorded at the end. No staging or commit was performed.

Tuesday job: read a report's context, prepare the next discussion, close an
owed item, and correct project work without losing the correction.

## Findings by owner cost

### W1. A refused Room correction closes the editor, discards all edits, and hides the refusal

- **Steps:** open the populated Room; press the action proposal's title;
  change Text from `Write the rollback runbook` to `Write the release rollback
  runbook`, Owner from `Priya` to `Jordan`, and Due from `2026-10-20` to
  `2026-10-22`; press **Save & confirm**. Refuse that one isolated request with
  an HTTP 409 boundary fixture, then press the proposal's title again.
- **Actual:** the editor closes immediately. No failure or retry appears in
  the Room. Reopening shows the original text, owner, and date. The draft
  correction is lost. Both 1440 and 393 reproduce the same result.
- **Expected:** keep the entered correction in its well until the write
  succeeds. A refusal shows its plain reason beside that work and permits
  retry without retyping.
- **Cause:** `web/src/features/project-room/ProjectRoomCore.tsx:766` starts
  confirmation without awaiting it, then `:767` closes the editor. `:753`
  always reinitializes the editor from the saved proposal. The controller
  catches the refusal and sets `error` at
  `web/src/features/project-room/useProjectRoomController.ts:276`, but the
  live `ctrl.room` branch at `ProjectRoomCore.tsx:2931` does not render it;
  `:3041` shows that error only when no Room exists.
- **Evidence:** `.tmp/deep-usability/work-shots/room-proposal-edited-1440.png`,
  `room-proposal-refused-1440.png`, and
  `room-proposal-refused-reopened-1440.png`; the same three basenames with
  `-393.png` show the phone sequence.
  `.tmp/deep-usability/work-observations.json` records
  `refused_save_editor_open: 0` and the three restored original values.
- **Fails:** Tenets 2, 3, and 7; UX-CANON A.10; Constitution VI.1.
- **Smallest repair:** make confirmation report success/failure; close the
  existing editor only on success. Keep its draft through refusal and
  unrelated reads using the existing Desk draft mechanism. Render the plain
  write failure and **Try again** in the live Room or its existing row well.
  Use the existing Button, SurfaceWell, and failure grammar.
- **Limit:** HTTP 409 is deliberately injected at the browser boundary. It
  proves the real client's response to a refused write, not the incidence
  of conflicts on the owner's desk. Successful real confirmation follows
  the refusal in this walk.

### W2. Person Context loses an unsaved note when the owner checks Prep or History

- **Steps:** People → a seeded report → Context; type Topic and Note; press
  Prep; return to Context.
- **Actual:** both fields return empty. The walk typed `Release feedback
  draft` and `Priya can lead the release after the rollback review.`; the
  recorded values after return are `topic: ""`, `note: ""`.
- **Expected:** changing a lens preserves the unsent note for this person.
  A successful **Add note** clears the draft.
- **Cause:** Context stores Topic, Note, and Visibility in component-local
  state at `web/src/pages/cores/PeopleCore.tsx:1258`; switching lenses
  unmounts Context at `:659`. Prep already uses `useDeskDraft` at `:775`
  for adjacent unsent fields. Its contract explicitly covers close/reload
  and keys drafts by field and person at `web/src/desk/deskMemory.ts:1`.
- **Evidence:** `.tmp/deep-usability/work-shots/person-context-draft-1440.png`
  and `person-context-draft-lost-1440.png`, paired with
  `person-context-draft-393.png` and `person-context-draft-lost-393.png`;
  JSON `context_draft_after_tab_return` is empty at both widths.
- **Fails:** Tenets 2, 3, and 7; the daily journey direction to preserve
  work across reads and returns (`DESIGN-daily-journeys.md`, Outcomes →
  Confirm → Work) already establishes the adjacent correction grammar.
- **Smallest repair:** reuse `useDeskDraft` with person-specific keys for
  Topic, Note, and Visibility; clear only after a successful Add. No new
  draft store or close confirmation.

### W3. Context opens on four setup/creation areas before the report's saved context

- **Steps:** open a report with one saved note and a linked project; press
  Context to read the report's context before a discussion.
- **Actual:** the first view contains Calendar linking, an empty alias
  field, Project linking, and an empty Topic/Note editor. The saved `Career
  plan` note is below the visible desktop window. After Add note succeeds,
  scrolling reveals both the original and newly saved notes below the same
  form. At 393 the first viewport does not reach Notes at all. After
  scrolling to the saved note, its body is clipped in the only row that
  contains it; no row action can reveal the full text.
- **Expected:** Context starts with the saved context and linked work.
  Creation and link setup open when requested, in the same window.
- **Cause:** `web/src/pages/cores/PeopleCore.tsx:1265` renders Calendar first,
  `:1266` aliases second, `:1267` Project creation before linked projects,
  and `:1268` Note creation before saved notes. The forms mount on every
  Context visit. `CalendarLinkSection` and `OwnerAliasSection` likewise
  render their add controls by default. The saved note uses a generic short
  SurfaceRow at `:1268` without `onOpen`; its detail inherits hidden overflow
  and nowrap at `web/src/desk/surface/surface.css:207`, then becomes flex at
  `web/src/pages/cores/people.css:126`. The body is cut rather than wrapped.
- **Evidence:** `.tmp/deep-usability/work-shots/person-context-top-1440.png`
  and `person-context-note-added-1440.png`, paired with
  `person-context-top-393.png` and `person-context-note-added-393.png`.
  The added-note shot is a real UI Add
  followed by a read of the encrypted People record; it is not a seeded
  success screenshot.
- **Fails:** Tenets 2, 3, and 7; UX-CANON A.5.
- **Smallest composition:** keep the current Notes ledger first, with one
  **Add note** action unfolding the current fields in a SurfaceWell. Keep
  linked Project rows next, with **Link project** opening the current
  selector. Put Calendar and names in notes under the existing Disclosure
  grammar (`web/src/desk/surface/patterns/Disclosure.tsx:14`). Prep already
  carries the next 1:1/calendar job, so Context need not lead with its setup.
  Preserve all saved rows, visibility labels, and existing real actions.
  Use the existing wrapped ledger/Material grammar for saved context so the
  complete note is readable without adding a new object window.

## Other bounded observations

- The UI **Add note** writes the intended Topic/Note and clears its fields;
  **Add to agenda** writes the agenda; **Done** removes the owed item and
  History shows `satisfied` and `accepted` events. These are executed actions
  through the isolated real hub, not seeded outcomes.
- Saved Context notes have no row opener or correction action. The inspected
  saved note row has zero buttons (`PeopleCore.tsx:1268`). The backend's
  exposed note routes are GET and POST
  (`holdspeak/web/routes/people.py:207` and `:214`). A correction flow would
  need an admitted edit contract as well as a face, so this is a capability
  gap, not a recommendation to improvise a new editor in this repair.
- Project plan rows deliberately have no verbs (`ProjectRoomCore.tsx:1091`,
  `:1256`). This follows the earlier plan design. Rich item summaries and
  mitigation details exist in the producer; the current plan exposes title
  and selected facts. Do not treat the missing editor as a new regression or
  introduce a new project workflow from this audit alone.
- Confirmed action rows **inside Decisions and owed** are inert; confirmed
  decision rows expand Send, rather than their record
  (`ProjectRoomCore.tsx:1801`). This was actually pressed at both widths:
  the desktop shot shows the Add destination/Send area beginning below the
  row; phone shot catches the opening before the lazy well is painted. A
  subsequent DOM read at both widths contains the stored decision, Owner,
  Sources, destination, and Send. That is not proof of the full well's
  visual presentation, nor of a Send action.
- The same confirmed action later appears in **Open here** with **Open**
  and **Hand to coder**, visibly at both widths in
  `room-plan-after-press-{1440,393}.png`. The room snapshot provides its
  action item identity, and `ProjectRoomCore.tsx:1083` binds Open to the
  existing action-item opener. Those controls were not pressed. The Room's
  task workflow is therefore not generally blocked by its inert folded
  history row; no replacement task editor is justified by this evidence.
- History truncates a long commitment title at 393 and has no detail opener
  (`person-history-completed-393.png`, `PeopleCore.tsx:1304`). This is the
  same generic short-row composition as saved notes, with less immediate
  owner cost than the draft losses. Timeline words are the stored event
  tokens `satisfied` and `accepted`.

## Capture method and limits

The scratch runner is `.tmp/deep-usability/work_walk.py`. It uses the
existing `glass_infra._ensure_build`, `_boot`, `_api`, `_normal_chair`,
`_settle`, and `clear_hub_windows`, plus `room_seed_rig`. Each run passes
through `.tmp/deep-usability/locked.py` → `scripts/test_lock.py` with an
isolated HOME/DB and the existing warm Node 22/browser installation.

People setup, relationships, saved notes, accepted requests, project items,
and links are seeded through their actual HTTP producers. The existing Room
seed sets Room orientation fields through its DB adapter because that helper
has no corresponding HTTP mutation. A saved meeting and two pending
proposals are seeded through their existing DB producers. Seeded actions
are not counted as executed UI actions.

No inference, external sends, microphone, terminal, owner port 8765, owner DB,
or owner session is used. Discovery ran no test suite. A capture runner's zero exit
is not a validation verdict: individual state gaps are explicitly recorded.

Capture attempt 1 reached the desktop Context/Prep/History and refused /
successful Room correction states. Its phone setup reused the seed's fixed
project command ID; that idempotent reply has no `project.id`, so the helper
failed. The post-confirm decision selector also mistakenly searched for a
ledger line inside the ledger line. Both are scratch rig gaps. Attempt 2
uses per-width project command IDs and the actual row selector. No product
or shared helper was changed. Two setup attempts are the limit.

## Inner-state coverage

Attempt 2 completed all scoped capture steps at 1440×900 mouse and 393×852
emulated touch. Its observation file reports `gaps: []` for each width and
no setup error. All screenshots in the table were inspected; their presence
does not prove unexecuted actions. `S` below means
`.tmp/deep-usability/work-shots/` and `{w}` means the two exact suffixes
`1440` and `393`.

| Inner face/state | Executed action and durable result | Paired-width proof | UNKNOWN |
|---|---|---|---|
| People roster → report | Real roster row press opens the selected report, then Context | Subsequent report shots below; no repeat roster landing shot | Duplicate name, archive and protected locked states |
| Context · populated/top | Saved note and linked project are producer-seeded; no claim of UI creation | `S/person-context-top-{w}.png` | Calendar/alias/project link/unlink writes; calendar read refusal |
| Context · unsent/return | Typed Topic + Note → Prep → Context; both values lost | `S/person-context-draft-{w}.png`, `S/person-context-draft-lost-{w}.png`; JSON empty strings | Close/reload draft path was not executed; source predicts same loss |
| Context · saved | Real Add note; GET relationship contains the new note; fields clear | `S/person-context-note-added-{w}.png`; JSON `add_note` and zero saved-note row buttons | Correction is absent from current face/routes; no edit is claimed |
| Prep · unplanned/agenda | Real Add to agenda; GET relationship contains the session agenda; no recording or engine used | `S/person-prep-agenda-added-{w}.png`; JSON `agenda_added` | Planned linked 1:1, Record, failure/retry, accepted meeting joins and Prep source opens |
| History · populated | Real Done on the seeded accepted commitment; History shows accepted/satisfied | `S/person-history-completed-{w}.png`; JSON `history_text` | Reopen, delegation/execution evidence and meeting history are not covered |
| History · empty | Producer-created new report with no commitments; actual History tab press | `S/person-history-empty-{w}.png` | Info, archive, readiness and protected store failure |
| Room · pending correction | Real proposal title press and text/owner/date input | `S/room-proposal-edited-{w}.png` | Unrelated refresh while typing, empty-field clearing, explicit Cancel |
| Room · refused correction/return | One isolated HTTP409; editor closes; reopen loses correction | `S/room-proposal-refused-{w}.png`, `S/room-proposal-refused-reopened-{w}.png`; JSON original values | Frequency/causes of real owner conflicts; pending long request not timed |
| Room · confirmed work | Real corrected action Save & confirm, then real decision Confirm. Room read contains edited action, owner Jordan, due Oct22, commitment and action-item IDs | `S/room-confirmed-work-{w}.png`; JSON `room_snapshot_after_confirm` | Phone shot shows decision row and beginning of action row; complete action data is API proof, not full-row pixels |
| Room · decision row open | Actual row press expands Send; subsequent DOM read contains destination/decision/source/Send | `S/room-decision-open-{w}.png`, JSON `decision_after_open` | Full well layout is not proved by these partly visible shots; no send, destination creation, decision detail/editor/return |
| Room · plan risk | Actual press on Settlement latency risk leaves window list unchanged; row has no buttons | `S/room-plan-after-press-{w}.png`; JSON before/after windows equal | Deliberately read-only plan; no item edit/return contract assumed |
| Room · task handoff | Confirmed task visibly appears with Open + Hand to coder | `S/room-plan-after-press-{w}.png`; source `:1083` binds Open | Controls not executed: follow-through task detail, edit, completion and return remain unknown |

The `walk-gap-{w}.png` files are retained from attempt 1 and are not counted
as coverage. The successful final log is
`.tmp/deep-usability/work-capture-2.log`; the serialized action and durable
read observations are `.tmp/deep-usability/work-observations.json`.

Audit TUESDAY: a report's saved context is unnecessarily hard to reach, and two
ordinary correction/return paths lose unsent work. The existing components
already support the small repair needed here.

## Authorized repair and after proof

Root read the native `canvas/deep-work` Context 393, Add note 1440, and
Room refusal 393 poses and authorized BUILD against `IMPLEMENTATION.md`.
Canvas source is under `docs/internal/philo/phase-17/canvas/deep-work/`;
six rendered poses are in `.tmp/deep-usability/work-canvas-shots/`, with
zero page errors in `.tmp/deep-usability/work-canvas.log`. This is root's
direction read, not an owner acceptance or Muad'Dib check.

Changed product files:

- `web/src/pages/cores/PeopleCore.tsx`: saved Notes first, readable wrapped
  bodies, actual **Leader private** / **Shared** words; linked Projects next;
  Add note unfolds the existing gadgets in SurfaceWell; setup is under the
  existing Links Disclosure. Prep's calendar handoff opens the Links fold.
  Topic/body/visibility use existing per-relationship Desk drafts. Closing
  the well keeps the draft. Successful Add clears only the submitted
  snapshot; later typing remains intact.
- `web/src/pages/cores/people.css`: local note title/body roles and wrapping.
- `web/src/features/project-room/ProjectRoomCore.tsx`: confirmation waits
  for the accepted write; refused corrections retain their fields and well
  with a plain reason and **Try again**. Fields stay disabled while their
  submitted write is pending. A locally accepted row stays confirmed while
  the follow-up read recovers, without exposing another confirmation.
- `web/src/features/project-room/useProjectRoomController.ts`: returns the
  actual confirmation result; a read failure is distinct and visible in
  the existing Room with a read retry.

Focused check files were collected in
`.tmp/deep-usability/work-collect-final.log`, then run under the isolated
helper/lock with `--maxWorkers=2`. Final result:
**5 files passed, 75 tests passed**, in
`.tmp/deep-usability/work-tests-ship.log`.

The five files are `peopleCore.test.tsx`,
`peopleReopenLens.philo1306.test.tsx`, `ProjectRoomCore.test.tsx`,
`useProjectRoomController.test.tsx`, and the explicitly authorized integration
adaptation `web/src/desk/__tests__/philo13FacesDoNotLie.test.tsx` (one Add note
gesture; its store failure/read retry assertions remain). New focused checks
cover return/remount/person separation, private/shared authority, refusal /
retry, a new draft typed during an older write, pending Room correction,
and accepted write followed by failed read. No broad suite was run.

The fresh production after walk uses the same isolated glass helpers and
real producers. Final log:
`.tmp/deep-usability/work-after-capture-2.log`; structured observations:
`.tmp/deep-usability/work-after-observations.json`. Both widths report
`gaps: []`, with no setup error. All 22 final after screenshots were
inspected. `A` below means `.tmp/deep-usability/work-after-shots/`;
`{w}` again means exact `1440` and `393` suffixes.

| Repaired job | Actual after result | Paired-width proof |
|---|---|---|
| Read existing report context | Complete saved note is visible before all creation/setup fields; Note editor and Calendar control counts are both 0 on open | `A/context-read-{w}.png` |
| Close Add note well | Well closes, saved context stays, unsent Topic/Note/Shared stays in Desk drafts | `A/context-well-closed-{w}.png` |
| Prep → Context return | The same Topic, body and `shared_intent` return | `A/context-tab-return-{w}.png`; JSON `after_tab_return` |
| Browser reload | Topic/body/Shared remain exact | `A/context-reload-{w}.png`; JSON `after_reload` |
| Real chrome Close/Back → reopen People | Same selected report and full draft recover | `A/context-close-reopen-{w}.png`; JSON `after_close_reopen` |
| Failed note write → retry | HTTP503 People store outage shows the existing plain failure; fields/Shared stay exact. Removing the boundary fixture and pressing Add note writes a real Shared note | `A/context-refused-{w}.png`, `A/context-saved-{w}.png`; encrypted relationship read in JSON `saved_person` |
| Clear accepted note draft | Reopening Add note has empty Topic/body and default `leader_private`; no extra note is submitted | JSON `after_success_new_note` |
| Room correction → refused Save | HTTP409 keeps editor count 1 and all edited text/owner/date; named cause and Try again are visible | `A/room-correction-{w}.png`, `A/room-refused-kept-{w}.png`; JSON `room_refused` |
| Room retry accepted → follow-up read fails | Real confirmation succeeds; a separate injected Room HTTP503 shows read failure/retry. Corrected work stays Confirmed, editor count 0, write retry count 0 | `A/room-accepted-read-failed-{w}.png`; JSON `room_accepted_read_failed` and real `durable_room_after_accept` |
| Room read retry | Real reread removes the failure and presents the accepted task in Open here; durable record has corrected text, Jordan and Oct22 | `A/room-read-recovered-{w}.png`; JSON `room_after_read_retry.read_error_count: 0` |

After capture attempt 1 used a synthetic Notes HTTP409. Existing People
policy treats that status as a protected store failure and correctly took
the record off the face; the draft still survived reload/close before it.
That attempt is retained in `work-after-attempt1-observations.json` and
`work-after-capture.log`. The second and final attempt uses the real People
outage class (`503`, `people_store_unavailable`), which exercises its existing
keep-person/keep-draft policy. No protected-plane authority rule was changed.
Room's conflict fixture remains HTTP409. Fault incidence on the owner's desk
and the real hardware/egress tails remain unknown.

After TUESDAY: the isolated owner can read the report's saved context,
recover a draft after a normal return, and retry the corrected Room work
without retyping or mistaking a failed reread for a failed write.

SOURCE FROZEN — HOLD FOR SHIP. Root owns independent fresh review, combined
quick check, integration, status, PR, merge and owner desk deployment.
