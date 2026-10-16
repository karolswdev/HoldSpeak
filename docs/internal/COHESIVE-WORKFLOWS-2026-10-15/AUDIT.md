# Bounded source audit — current main7f3345745

Three delegated read-only passes, no tests/browser/writes. Root inspected the
load-bearing source before settling this batch. These are source-confirmed
paths; runtime/appearance is not claimed until the live walk.

- WorkbenchWindow:660 cancels an unsaved450ms body timer on unmount;1296 Add
  lacks pending guard. TemplatePicker:102 treats loaded-empty as loading,
  hiding Blank.
- gate.ts:58 catches every decision error; ConductorWindow:398 only clears busy.
- CoderPullout:125 unconditionally clears newer reply text on successful Send.
- ConnectionsPane:509 drops selected subRef;api.ts:174 sends no ref though
  backend already supports it. Pane:462 allows stale reads to repaint rows.
- useRunsOn:237 cleans only timers;580 starts capture without owned cleanup.
- SettingsCore:2064 Save A closes the shared calendar well even after draft B.
- ThoughtContextPicker:118/133/146 sets pending then reads/writes sessionStorage
  outside try; cleanup can suppress accepted receipt. Current heading/search/
  text-only Button skins bypass shared interior primitives (visual concern).
- NotePullout:332 claims conflict/current for every review failure without read.
- PeopleCore:637 maps failed/pending calendar reads to empty;1325 invents cloud
  egress beside the action that merely creates a Workbench item.
- ProjectRoomCore:1378/1385/1392 silently catch merged-source mutation errors;
  Promise.all can reject before sibling outcomes settle and no reload follows.
- MeetingDetail:258 suppresses People read failure, leaving only Who?/Me.
- ZoneWindow:133 supplies a no-op empty action. InfoWindow:203 raw enabled
  lineage buttons silently do nothing for unresolved sources. Its long name and
  130px/1fr property layout need actual narrow check.
- DoorCore:474 raw New Project input has no associated label.
- SurfaceWindows:252 separate ellipsis loading face.
- DeskMenu:609 Left discards deeper hierarchy unlike Back634;686 focuses first
  trigger rather than opener.
- CapabilitySection:136, DeliveryBoard:90/445/473, WorkbenchResourceful:191
  raw custom action skins bypass library primary/busy treatment.
- Needs you needs.css:22/47 has nested scrolling topology. Poor handoff remains
  an unobserved hypothesis; observe before changing.

Audited entry points: DeskApp, applications, pullout registry and SurfaceWindows;
Workbench, Conductor, Note/context/send, People, Meetings, projects/Room,
Settings/accounts/engines/calendar, Runs on, Coder, Delivery, Zone/Get Info,
Needs you, menus. Existing Follow-through and Send share ledger/state/action
material; no equally concrete source defect was found in these bounded passes.
Coverage is a source census, not completed visual or end-to-end validation.
