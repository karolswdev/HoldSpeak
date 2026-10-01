# PHILO-13-07 - B2 The Desk remembers

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** **PHILO-13-01 (B0) merged, its cases passing on main; this story's merge record cites B0's merged commit and evidence path (the gate)**; PHILO-13-05 (close means gone)
- **Unblocks:** D1 (out of this phase; the owner's "Later" waits on this story's return in real use)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** B2 (PROPOSAL §3, Wave B); fork 3, "Everything"
- **Closure finding:** `grounding/structure.md` F2 (`:285`), move 1 (`:300`); `grounding/faces-jobs.md` F5 (`:171`), move 2 (`:153`); `grounding/faces-surfaces.md` F13 (`:200`)
- **Canvas:** none (no new face; the return is the existing windows in their places)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Every open window, its place and any unsent draft survive a reload and a close, automatically (Workbench *Snapshot*; the owner's fork 3, "Everything").

## Problem

The workspace document `hs.desk.workspace.v1` keeps surface windows, rects, order, maximize and zones only (`web/src/desk/store/workspaceStorage.ts:8`, `:15-25`, `:132`). Pullouts and the Info, Roadmap, Repository and Workbench windows live in separate in-memory arrays (`web/src/desk/store/compositorSlice.ts:126`; `web/src/desk/store/windowFactory.ts:30`): after a reload they are gone (`grounding/structure.md:143`). Surface windows come back on their first screen. Drafts are lost: the J3 1:1 note was typed four times; the J4 update lost 111 typed characters (`grounding/faces-jobs.md:85-88`, `:101`). Minimized windows come back open and in front; one window's position was lost (`grounding/faces-surfaces.md:81`). Shots: `grounding/shots/jobs/J1-07-after-reload-1440.png`, `J2-05-came-back-1440.png`, `J2-06-after-reload-1440.png`, `J3-04-came-back-1440.png`, `J3-05-after-reload-1440.png`, `J4-05-came-back-1440.png`, `J5-04-after-reload-1440.png` (and `-393`).

## Scope

- **In:**
  - Extend the existing workspace contract (not a second store) to every window family below that **returns** (`web/src/desk/store/types.ts:26`; `workspaceStorage.ts:15`; `windowFactory.ts:30`), restored through its existing opener (`openPullout`, `compositorSlice.ts:137-152`, and each family's own store).
  - A per-window **place**: the selected meeting, the person + tab, the send pick and form, scroll where it carries the job.
  - **Unsent drafts** in the same document (the named fields below). A draft clears when its write lands; restore never saves or sends.
  - Minimized windows come back minimized; every saved position comes back.
  - Close keeps the place for the next open of the same object (fork 3).
- **Out:** saved window sets (D1, "Later"); a virtual-screen model; first-value recovery clearing the workspace (intentional, `grounding/structure.md:145`; unverified, not changed here).

### Every mounted window family and its disposition

From the Desk's mounts (`web/src/desk/DeskApp.tsx:249-305`; `web/src/desk/gl/WorldStage.tsx:270-277`). "Returns" = it reopens after a reload with its object and place; "exempt" = it does not, for the reason given from the source.

| Family | Mount | Open state today | Disposition |
|---|---|---|---|
| Surface windows (the 23 registry actions) | `SurfaceWindows`, `DeskApp.tsx:297` | `windowsById`, already persisted (`workspaceStorage.ts:15`) | **returns** (already); B2 adds the place |
| Pullouts (meeting, artifact, note, decision, kb, recipe, chain, workflow, coder, directory, intelligence, thread; the Thought workspace on the note) | `DeskApp.tsx:261`, `WorldStage.tsx:270` | `compositorSlice.ts:126` (in memory) | **returns** |
| Zone windows | `WorldStage.tsx:272-274` | `zoneWindows`, already persisted (`workspaceStorage.ts:23`) | **returns** (already) |
| Info windows | `WorldStage.tsx:275-277` | in memory (`windowFactory.ts:30`) | **returns** |
| Roadmap windows | `DeskApp.tsx:269-275` | `roadmapWindows` (in memory) | **returns** |
| Repository windows | `DeskApp.tsx:276-282` | `repositoryWindows` (in memory) | **returns** |
| Workbench windows | `DeskApp.tsx:283` | `workbenchWindows` (in memory) | **returns** |
| Delivery dossier | `DeskApp.tsx:267` | `useDeliveryDossier`, `web/src/desk/deliveryDossier.ts:182` | **returns** (Astra r1 finding 2) |
| Delivery terminal | `DeskApp.tsx:268` | `useDeliveryTerminal.openTarget`, `web/src/desk/deliveryTerminal.ts:221` | **returns** (the window and its target; the stream re-attaches) |
| Delivery board | `DeskApp.tsx:266` | local `useState`, `web/src/desk/components/DeliveryBoard.tsx:353` | **returns** |
| Mission Control conveyor | `DeskApp.tsx:265` | `useMissionControl.open`, `web/src/desk/missioncontrol.ts:333` | **returns** |
| Session pullout | `DeskApp.tsx:293` | `useSteering.openKey`, `web/src/desk/steering.ts:273` | **returns** |
| Tool inspector | `DeskApp.tsx:264` | `toolInspector`, `web/src/desk/store/types.ts:192` | **returns** (with its target) |
| Schedule recording | `DeskApp.tsx:291` | `scheduleCreateWindow`, `types.ts:206`; fields in local state, `ScheduleCreateWindow.tsx:70-80` | **returns**, with its field draft (it holds typed text) |
| Ask panel | `DeskApp.tsx:249` | `askOpen`, `types.ts:188` | **returns**, with its prompt draft |
| Inline editor | `DeskApp.tsx:250-257` | `editingId`, `types.ts:150` | **returns**, with its unsaved text |
| New Workbench chooser | `DeskApp.tsx:290` | `newWorkbenchChooser`, `types.ts:176` | **exempt**: it holds no typed text and no record; it exists only before a record does, and one pick makes the record (`NewWorkbenchChooser.tsx:1-8`). Reopening is the same one gesture. |
| Trust window | `DeskApp.tsx:301` | `useTrustWindow.open`, `TrustWindow.tsx:47-52` | **returns** (Astra charter r2 F3, the owner's "Everything"): its open state and rect return on reload; it holds no draft |
| Pane picker | `DeskApp.tsx:292` (a popover, defined in `SessionPullout.tsx`) | local | **exempt**: a popover, not a window (`grounding/faces-surfaces.md:145`) |
| Attention drawer / shade (the bell) | `DeskApp.tsx:294` | `AttentionDrawer.tsx:37`, `:68` | **exempt**: a transient shade over the Desk, closed by Escape; not a window |
| Exposé, Switcher, SnapGhost, the palette | `DeskApp.tsx:303-305`; `chromeState.ts:13` | transient | **exempt**: transient overlays (`grounding/structure.md:137`) |

### Every named draft field

| Draft field | Where | Grounding |
|---|---|---|
| the People 1:1 agenda item / note | `PeopleCore.tsx` 1:1s tab | J3-04, J3-05 (typed four times) |
| the People request / follow-up field | `PeopleCore.tsx` `Now` | J3-09 |
| the Room update draft body | the Room's Update posture | J4-05 (111 characters lost) |
| the Thought body before its first save | the Thought workspace | J5-04 |
| the meeting SEND well's form (Summary / Digest / Follow-up) and destination pick | `web/src/meetings/MeetingSendWell.tsx:28`, `:34`; `SendWell.tsx:64` | J2-05, J2-06 |
| the Decide inline title (after B3) | the meeting record | B3 |
| the Schedule recording title and time | `ScheduleCreateWindow.tsx:70-80` | this table |
| the Ask prompt | `AskPanel.tsx` | this table |
| the inline editor's unsaved text | the inline editor | this table |

## Acceptance criteria

- [ ] **Gate (review evidence):** PHILO-13-01 (B0) is merged on main and its cases pass there before this story merges; they pass again on this story's head. **This story's PR merge record cites B0's merged commit and its atlas evidence path (`evidence-story-01.md` and the run directories it names)**; without it the checker refuses the merge.
- [ ] Every family marked **returns** above comes back after a reload with its object and place, at 1440 and 393 (touch); one fence per family. Every family marked **exempt** keeps its reason in the source comment or the fence.
- [ ] Reload mid-job, for J1–J5 on the grounding week: 0 re-navigation gestures (from 2 in J2, 2 + retype in J3, 3 in J5).
- [ ] 0 lost drafts: **each** named draft field above, typed and not saved, survives a reload and a close; each clears after its save; none is saved or sent by restore. Red on main for the People note, the Room draft, the Thought body and the meeting form and pick.
- [ ] A minimized window comes back minimized; a moved window comes back where it was. Red on main (`grounding/faces-surfaces.md:81`).
- [ ] Closing one window closes only that one (`grounding/structure.md:300`).
- [ ] **Close → reopen keeps the place** (Astra charter r2 F2): for each returning family with a place (meeting pullout's selected form and pick, People's person + tab, the Room's project + update, Workbench, Repo, Roadmap, Delivery dossier/terminal, Trust's rect): move and resize it, set its place, close it, reopen the **same object** by its normal opener → the same rect and the same place. An actual atlas case per family in `atlas-phase13-muaddib.json` (open → move → set place → close → reopen → assert), at 1440 and with touch at 393; red on main where main loses it.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the workspace document (round trip per family; the place; drafts); `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the J1–J5 return legs of `grounding/faces-jobs.md` re-run at both widths (touch at 393), counting gestures.
- **Atlas:** one case per returning family (open → reload → same object and place) and one case per named draft field, at 1440 and 393, one case per `scripts/graph_walk.py run` invocation; B0's cases re-run on the head.
- **Shots:** each reload shot above, re-taken.

## Worker-brief scars

- **Doubles that lie:** a fence reads the real `localStorage` document the app writes, after a real reload; never a hand-built document the app never writes.
- **Never rewrite a guard to match a removal:** existing workspace fences gain families; none is loosened.
- **Drafts are not records:** a draft is never sent or saved by restore; restore fills the field, he presses Save or Send.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:153`; `grounding/structure.md:300`). PROVISIONAL.

## Notes

- 2026-10-01 — every file this story changes is the faces lane's (`web/src/desk/store/**`, `deliveryDossier.ts`, `deliveryTerminal.ts`, `PeopleCore.tsx`, the Room face, `AskPanel.tsx`, `ScheduleCreateWindow.tsx`, the pullouts).
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
