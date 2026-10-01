# PHILO-13 S0 — shared surface inventory

**Status:** CHECKED — Muad'Dib RATIFY, 2026-10-01 (`checks/structure-muaddib.md` on `docs/philo-13-ground`; PR #722 comment).
**Base:** `4c49651e1` (the pinned audit base; anchors below were read from this worktree)
**Scope:** read-only source census for Astra’s grounding lane. This file records
what can open what, where it is mounted, and what is reachable from the Desk
grammar. It does not make a product or design decision. No test, hub, database,
visual walk, or screenshot was run for this census.

## Census at a glance

| Evidence | Count | Source anchor |
|---|---:|---|
| Manifest actions | 23 | `web/src/desk/applications.ts:48-451` |
| Primitive kinds | 20 | `web/src/lib/primitives.ts:449-674` |
| Distinct pullout content components | 14 (13 dedicated + `FallbackPullout`) | `web/src/desk/pullouts/registry.ts:6-19,26-47` |
| Registry fallback/redirect entries | 7 | `web/src/desk/pullouts/registry.ts:38-46` |
| Manifest Dock seats | 5 | `web/src/desk/applications.ts:72,83,113,134,154` |
| Menu IDs | 4 | `web/src/desk/components/DeskMenuBar.tsx:28-33` |
| Transient top-level overlays | 3 | `web/src/desk/DeskApp.tsx:303-305` |

The 20 primitive kinds and the 14 distinct pullout components are different
counts: 13 kinds have named dedicated content and seven registry rows reuse
`FallbackPullout`; Intelligence and People account for the remaining named
content rows. A
primitive may redirect to a surface or a generated window, and the registry
contains fallback rows for several such kinds. `openPullout` resolves the
primitive descriptor before it decides whether to mount a pullout, window,
surface, or nothing (`web/src/desk/store/compositorSlice.ts:137-175`).

Reachability in the application table uses these words literally:

* **Go** means the manifest row is a `group: "app"` or `group: "tool"` row,
  so `web/src/desk/tools.ts:1-21` puts it in `DESK_TOOLS` and
  `web/src/desk/verbRegistry.ts:606-633` exposes `go.<action>`.
* **Palette** means the action is available through the `⌘K` palette when its
  verb is offered. The palette is opened by `web/src/desk/components/DeskToolShelf.tsx:557-611` and
  runs the selected row at `web/src/desk/components/DeskToolShelf.tsx:616-708`.
* **Dock** means one of the five manifest Dock seats. A running seat restores
  or focuses its window; a cold seat calls `openSurfaceOr` at
  `web/src/desk/components/window/Dock.tsx:143-177`.
* **Mark** means a HoldSpeak mark-menu command generated at
  `web/src/desk/applications.ts:469-475` and rendered by
  `web/src/desk/components/DeskChrome.tsx:29-32`.
* **Route** means a demoted deep link. Only `/`, `/welcome`, and `/presence`
  are real product routes (`web/src/routes.tsx:1-29`); the rest of the listed
  paths hand the intent to a surface (`web/src/routes.tsx:31-76`).
* **Code** means a source handoff identified in the handoff index below.

**Anchors:** source references use repository-relative paths. Line ranges identify the inspected branch; they are not runtime observations.

## S0 application inventory — all 23 manifest rows

The component anchor is the manifest’s lazy core or the direct host identity.
The reachability column records source reachability; it is not a claim that a
person saw or successfully used the face.

| # | Action / label | Component or host anchor | Reachability and handoffs |
|---:|---|---|---|
| 1 | `change-places` — Change places | `web/src/desk/applications.ts:50-63` → `ChangePlacesCore` | Go, Palette, `⌘⇧P` (`web/src/desk/applications.ts:56-57`); Chair/Floor Places button calls it (`web/src/desk/components/window/RoomActions.tsx:25-49`). |
| 2 | `open-intelligence` — Intelligence | `web/src/desk/applications.ts:66-74`; no surface core; pullout content is `IntelligencePullout` (`web/src/desk/pullouts/registry.ts:43`) | Dock seat 0, Mark (`desk.open-intelligence`), Palette through the mark verb; attention and system-shade code can call `openIntelligence` (`web/src/desk/components/AttentionDrawer.tsx:16,150-173`; `web/src/desk/components/SystemShade.tsx:197,455,807`). It is a pullout route, not a SurfaceWindows row. |
| 3 | `dictate` — Speak | `web/src/desk/applications.ts:76-94` → `DictationCore` | Dock seat 1, Go, Palette, `⌘1`, Route `/dictation`, Mark (`web/src/desk/applications.ts:76-94`; `web/src/routes.tsx:42-44`). First Words and start actions also open it (`web/src/desk/components/FirstWords.tsx:360-481`; `web/src/desk/components/DeskStartActions.tsx:17-45`). |
| 4 | `ask` — Ask AI | `web/src/desk/applications.ts:97-104` (Go group at line 103); direct `AskPanel` host at `web/src/desk/DeskApp.tsx:247-249`, frame at `web/src/desk/components/AskPanel.tsx:271-548` | Explicit Go door and `⌘I` use the generated handler (`web/src/desk/verbRegistry.ts:606-631`, with Ask’s `openAsk` branch at `web/src/desk/verbRegistry.ts:623-627`); Object Ask menu and Palette object verb are `web/src/desk/verbRegistry.ts:445-461`; `askOpen` mounts the Chair panel. It has no Dock seat and no SurfaceWindows row. |
| 5 | `review-meetings` — Meetings | `web/src/desk/applications.ts:106-123` → `HistoryCore` | Dock seat 2, Go, Palette, `⌘2`, Routes `/history` and `/meetings`, Mark (`web/src/desk/applications.ts:106-123`; `web/src/routes.tsx:45-56`). Meeting pullouts use it with a meeting scope (`web/src/desk/components/Pullout.tsx:76-85`). |
| 6 | `inspect-personas-and-coders` — Agents | `web/src/desk/applications.ts:126-144` → `CompanionCore` | Dock seat 3, Go, Palette, `⌘3`, Route `/companion`, Mark (`web/src/desk/applications.ts:126-144`; `web/src/routes.tsx:73`). |
| 7 | `configure-settings` — Settings | `web/src/desk/applications.ts:147-172` → `SettingsCore` | Dock seat 4, Go, Palette, `⌘4`, Routes `/settings` and `/studio`, Mark (`web/src/desk/applications.ts:147-172`; `web/src/routes.tsx:58-60,70-73`). Registry aliases include `configure-integrations`, `configure-integration`, and `read-runtime-docs` (`web/src/desk/applications.ts:157-163`). |
| 8 | `record-live` — Live meeting | `web/src/desk/applications.ts:175-188` → `LiveCore` | Code from Record Orb, CaptureBar, and start actions; Route `/live` (`web/src/routes.tsx:42-45`). It has no Go group and no Dock seat. `RecordOrb` calls it after recording starts or stops (`web/src/desk/components/RecordOrb.tsx:59-75`). |
| 9 | `configure-cadence` — Rhythm | `web/src/desk/applications.ts:191-206` → `CadenceCore` | Go, Palette, Route `/cadence` (`web/src/routes.tsx:62-65`); attention source rows open it with a subject ref (`web/src/desk/components/AttentionDrawer.tsx:56-63`). |
| 10 | `configure-setup` — Setup | `web/src/desk/applications.ts:217-235` → `SetupCore` | Go, Palette, first-value microphone recovery, and setup handoffs; no Dock seat. It is admitted in the first-value recovery registry alongside `project-setup` (`web/src/desk/components/SurfaceWindows.tsx:61-70`). Its `href` is `/`, and there is no `/configure-setup` route. |
| 11 | `open-constitutional-context` — Context | `web/src/desk/applications.ts:238-252` → `ConstitutionalContextCore` | Go and Palette. Manifest `href` is `/context` (`web/src/desk/applications.ts:243`), but that path is not a demoted row in `web/src/routes.tsx:41-76`; runtime fallback behavior is therefore not claimed here. |
| 12 | `open-workbenches` — Workbenches | `web/src/desk/applications.ts:255-269` → `WorkbenchesHomeCore` | Go, Palette, Route `/workbenches`; Workflow pullouts hand off to it with a resource scope (`web/src/desk/components/Pullout.tsx:87-96`). |
| 13 | `design-components` — Components | `web/src/desk/applications.ts:272-285` → `ComponentsCore` | Route `/design/components` (`web/src/routes.tsx:74-75`). The manifest has no group, Dock, or Mark field; no Go/Palette claim is made from this row. |
| 14 | `inspect-activity` — Activity | `web/src/desk/applications.ts:288-303` → `ActivityCore` | Go, Palette, Route `/activity` (`web/src/routes.tsx:62`). |
| 15 | `open-project-memory` — Desk memory | `web/src/desk/applications.ts:306-320` → `ProjectMemoryCore` | Go, Palette, and code from the Desk memory launcher/SystemShade (`web/src/desk/components/AttentionDrawer.tsx:74-95`). Projects resolve to this surface with `project:<id>` scope (`web/src/lib/primitives.ts:518-528`; `web/src/desk/shell.ts:103-113`). |
| 16 | `open-concierge` — Models | `web/src/desk/applications.ts:325-345` → `ConciergeCore` | Code from Chair setup blocker, Settings, Speak, Thought, and related capability views; aliases `configure-runs-on` (`web/src/desk/applications.ts:331-345`). No Go group on this row; the duplicate Go row is #22. Chair setup opens this surface at `web/src/desk/chair/ChairHome.tsx:1181-1209`. |
| 17 | `project-setup` — New Project | `web/src/desk/applications.ts:348-362` → `DoorCore` | Desk New Project verb and Palette New group (`web/src/desk/verbRegistry.ts:248-259`), first-value recovery, Route `/setup` (`web/src/routes.tsx:41-43`). No Dock seat. |
| 18 | `inspect-processes` — Processes | `web/src/desk/applications.ts:365-379` → `ProcessCore` | Go and Palette. Manifest fallback `/#processes` (`web/src/desk/applications.ts:365-371`) is not a demoted route row. |
| 19 | `configure-commands` — Commands | `web/src/desk/applications.ts:382-396` → `CommandsCore` | Go, Palette, Route `/commands` (`web/src/routes.tsx:62-64`). |
| 20 | `open-people` — People | `web/src/desk/applications.ts:399-413` → `PeopleCore` | Mark (`desk.open-people`), Palette through that mark verb, and People/Follow-through code. Primitive `people` redirects to this surface (`web/src/lib/primitives.ts:640-650`). The Brief “Open person” handoff uses the unresolved key `people` and fallback `/people`; it has no matching alias or demoted route (`web/src/desk/pullouts/views/BriefView.tsx:484-492`; `web/src/App.tsx:60-68`). |
| 21 | `review-calendar-snapshot` — Calendar snapshot | `web/src/desk/applications.ts:416-429` → `CalendarSnapshotReviewCore` | Code from the Glass Drop screenshot/import flow and Settings (`web/src/desk/components/GlassDropLayer.tsx:65-69,82-95,137-158`; `web/src/pages/cores/SettingsCore.tsx:2115`). No group, Dock, Mark, or demoted route row. |
| 22 | `configure-runs-on` — Models (alias action) | `web/src/desk/applications.ts:431-440`, same `windowId: "surface-concierge"` | Go and Palette; `/profiles` is a demoted route to this action (`web/src/routes.tsx:69`). SurfaceWindows opens the hosted Concierge via the alias target (`web/src/desk/components/SurfaceWindows.tsx:104-109`; `web/src/desk/applications.ts:325-336`). This row is a registry redirect distinction, not another window. |
| 23 | `configure-integrations` — Connections | `web/src/desk/applications.ts:442-450`, same `windowId: "surface-settings"` | Go and Palette; Settings alias/module scope `integration:destinations` (`web/src/desk/applications.ts:157-159,442-450`). It does not create a second Settings window. Settings and the Inspector hand off to this scoped surface (`web/src/pages/cores/SettingsCore.tsx:1969,2290-2295`; `web/src/desk/components/DeskToolInspector.tsx:519-524`). |

`SURFACE_APPLICATIONS` is the manifest projection used by the window registry
(`web/src/desk/applications.ts:453-458`). `DOCK_APPLICATIONS` is the five-seat projection
(`web/src/desk/applications.ts:460-467`). `MARK_APPLICATION_COMMANDS` has the special
`desk.` prefix only for Intelligence and People; all other marked rows use
`go.` (`web/src/desk/applications.ts:469-475`).

## DeskApp mounted surfaces, overlays, and reachability

`DeskApp` places the delete host above both setup branches
(`web/src/desk/DeskApp.tsx:82-93`). After arrival, the normal branch mounts the
following groups. The `SurfaceWindows` row is the registry and is called out
separately; all other rows are non-registry direct mounts or direct overlay
mounts. Conditional mounts can be absent even when their source is present.

| Mounted group | Direct source anchor | Reachability / condition |
|---|---|---|
| Delete host | `web/src/desk/DeskApp.tsx:86-92` → `DeskDeleteHost` | Always above setup pending/failure and normal branches; delete receipt/listener host. |
| Atmosphere | `web/src/desk/DeskApp.tsx:219-225`; lazy import `web/src/desk/DeskApp.tsx:50-52` | Floor only (`showFloor`); atmosphere is not a window frame. |
| Glass Drop layer | `web/src/desk/DeskApp.tsx:226`; `web/src/desk/components/GlassDropLayer.tsx:65-158` | Floor only; screenshot/import path can open Calendar snapshot and Meetings. |
| Desk chrome | `web/src/desk/DeskApp.tsx:227`; `web/src/desk/components/DeskChrome.tsx:29-32,111-280` | Normal arrival only; contains mark menu, attention bell, clock, runtime lamp, and egress chip. |
| Compact receipt row | `web/src/desk/DeskApp.tsx:228-230`; `web/src/desk/components/DeskReceiptRow.tsx:13` | Normal compact view only. |
| Floor/Chair face | `web/src/desk/DeskApp.tsx:231-246` | Floor branch uses Empty Desk, List, or lazy WorldStage; Chair branch uses `ChairHome`. Arrival uses ChairHome’s First Words path (`web/src/desk/chair/ChairHome.tsx:467-484`). |
| WorldStage | lazy import `web/src/desk/DeskApp.tsx:53-55`; mount `web/src/desk/DeskApp.tsx:238-243` | Floor spatial view only; WorldStage also mounts Zone and Info windows and pullouts (`web/src/desk/gl/WorldStage.tsx:266-277`). |
| Desk list | `web/src/desk/DeskApp.tsx:234-237` → `DeskListView` | Floor list view only; rows open pullouts (`web/src/desk/components/DeskListView.tsx:366`). |
| ChairHome | `web/src/desk/DeskApp.tsx:245`; arrival split `web/src/desk/chair/ChairHome.tsx:467-484` | Normal Chair or first-value First Words; CaptureBar is inside ChairHome (`web/src/desk/chair/ChairHome.tsx:2747-2791`). |
| Ask panel | `web/src/desk/DeskApp.tsx:247-249`; frame `web/src/desk/components/AskPanel.tsx:271-548` | Chair only in the direct mount, when `askOpen`; Floor/List owns its own Ask mount. Object Ask sets the store (`web/src/desk/verbRegistry.ts:445-461`). |
| Inline editor | `web/src/desk/DeskApp.tsx:250-257`; frame `web/src/desk/components/InlineEditor.tsx:38-71` | Chair only in direct mount when `editingId`; Floor/List/WorldStage own their own editor mount. |
| Chair pullout cards | `web/src/desk/DeskApp.tsx:258-262`; shell `web/src/desk/components/Pullout.tsx:21-105` | Chair only, after item resolution; note rows can route to ThoughtWorkspaceWindow (`web/src/desk/components/Pullout.tsx:108-129`). |
| Desk Tool Inspector | `web/src/desk/DeskApp.tsx:264`; frame `web/src/desk/components/DeskToolInspector.tsx:241-537` | Normal arrival only; launcher is registered by the component and can be invoked from object/capability flows. |
| Mission Control conveyor | `web/src/desk/DeskApp.tsx:265`; `web/src/desk/components/MissionControlConveyor.tsx:560-615` | Normal arrival only; RAILS/conveyor conditional on available repository/session state. |
| Delivery Board | `web/src/desk/DeskApp.tsx:266`; frame `web/src/desk/components/DeliveryBoard.tsx:349-423,399-564` | Normal arrival only; registers a launcher and opens dossier/terminal handoffs. |
| Delivery dossier | `web/src/desk/DeskApp.tsx:267`; frame `web/src/desk/components/DeliveryDossierWindow.tsx:58-96` | Normal arrival only; conditional open state. |
| Delivery terminal | `web/src/desk/DeskApp.tsx:268`; frame `web/src/desk/components/DeliveryTerminalWindow.tsx:160-236` | Normal arrival only; conditional terminal state. |
| Roadmap windows | `web/src/desk/DeskApp.tsx:269-275`; lazy import `web/src/desk/DeskApp.tsx:56-60`; frame `web/src/desk/components/RoadmapWindow.tsx:72-119` | Normal arrival only; one per `roadmapWindows` state row. Primitive `roadmap` redirects here (`web/src/lib/primitives.ts:596-606`). |
| Repository windows | `web/src/desk/DeskApp.tsx:276-282`; lazy import `web/src/desk/DeskApp.tsx:61-65`; frame `web/src/desk/components/RepoWindow.tsx:176-271` | Normal arrival only; one per `repositoryWindows` state row. Primitive `repository` redirects here (`web/src/lib/primitives.ts:529-539`). |
| Workbench windows | `web/src/desk/DeskApp.tsx:283-289`; lazy import `web/src/desk/DeskApp.tsx:66-70`; frame `web/src/desk/components/WorkbenchWindow.tsx:1467-1928` | Normal arrival only; one per `workbenchWindows` state row. Primitive `workbench` redirects here (`web/src/lib/primitives.ts:618-628`). |
| New Workbench chooser | `web/src/desk/DeskApp.tsx:290`; frame `web/src/desk/components/NewWorkbenchChooser.tsx:13-34` | Normal arrival only; state is set by `openNewWorkbenchChooser`, and templates hand off to a Workbench window (`web/src/desk/components/WorkbenchTemplatePicker.tsx:54,74`). |
| Schedule create window | `web/src/desk/DeskApp.tsx:291`; frame `web/src/desk/components/ScheduleCreateWindow.tsx:123-215` | Normal arrival only; conditional schedule-create state, opened by CaptureBar (`web/src/desk/chair/ChairHome.tsx:2783-2789`). |
| Pane picker | `web/src/desk/DeskApp.tsx:292`; `web/src/desk/components/SessionPullout.tsx:236-330` | Normal arrival only; launcher/pane selection can open a session (`web/src/desk/components/SessionPullout.tsx:254-318`). |
| Session pullout/window | `web/src/desk/DeskApp.tsx:293`; frame `web/src/desk/components/SessionPullout.tsx:653-781` | Normal arrival only; conditional steering session state. |
| Attention drawer and SystemShade | `web/src/desk/DeskApp.tsx:294`; drawer frame `web/src/desk/components/AttentionDrawer.tsx:89-105,324`; shade mount `web/src/desk/components/AttentionDrawer.tsx:89-95` | Normal arrival only; attention launcher is registered in the Dock and SystemShade can open memory/Intelligence/Meetings/Rhythm/Settings/People (`web/src/desk/components/AttentionDrawer.tsx:74-95,150-173`; `web/src/desk/components/SystemShade.tsx:197,199,455,651,807`). |
| Trust window | `web/src/desk/DeskApp.tsx:301`; frame `web/src/desk/components/TrustWindow.tsx:56-172` | Normal arrival only; egress chip opens it (`web/src/desk/components/DeskChrome.tsx:259-266`), and it can return to Settings (`web/src/desk/components/TrustWindow.tsx:159-168`). |
| Dock and Record Orb | `web/src/desk/DeskApp.tsx:302`; Dock `web/src/desk/components/window/Dock.tsx:36-356`; Record Orb `web/src/desk/components/RecordOrb.tsx:17-89` | Normal arrival only. The five app seats and runtime launchers are Dock children; Record Orb is the center capture control. |
| Snap Ghost | `web/src/desk/DeskApp.tsx:303`; `web/src/desk/components/window/SnapGhost.tsx:26-41` | Normal arrival only; visible only while a drag publishes a snap rect. |
| Expose | `web/src/desk/DeskApp.tsx:304`; `web/src/desk/components/window/Expose.tsx:26-150` | Normal arrival only; transient overview of registered windows, toggled by `desk.overview` and Dock Overview. |
| Switcher | `web/src/desk/DeskApp.tsx:305`; `web/src/desk/components/window/Switcher.tsx:34-55` | Normal arrival only; transient MRU strip during window cycling, fed by `flashSwitcher` (`web/src/desk/components/window/Switcher.tsx:14-28`). |

The setup-pending/failure return at `web/src/desk/DeskApp.tsx:195-213` has only the
loading/error surface and Retry. During first-value arrival, `arrivalRequired`
also suppresses DeskChrome, Floor, Ask, editors, pullouts, all direct windows,
Dock, and transient overlays (`web/src/desk/DeskApp.tsx:143-149,216-305`). The root delete
host remains mounted. `SurfaceWindows` is still mounted in recovery-only mode,
but its rows are only `project-setup` and `configure-setup`
(`web/src/desk/components/SurfaceWindows.tsx:61-70,86-109`); First Words is the arrival face
(`web/src/desk/chair/ChairHome.tsx:467-484`, `web/src/desk/components/FirstWords.tsx:360-481`).

### Nested non-registry frame census

The direct `DeskApp` table above is not the complete frame set. These frames
are mounted by direct faces or by the pullout/WorldStage branches and are not
rows in `SurfaceWindows`:

| Frame | Mount / frame anchor | Opens from |
|---|---|---|
| `ZoneWindow` | `web/src/desk/gl/WorldStage.tsx:272-274`; frame `web/src/desk/components/ZoneWindow.tsx:106-194` | Object Open on a directory (`web/src/desk/verbRegistry.ts:399-411`), Floor spatial zone actions, and Info Filed links (`web/src/desk/components/InfoWindow.tsx:173-186`). |
| `InfoWindow` / Get Info | `web/src/desk/gl/WorldStage.tsx:275-277`; frame `web/src/desk/components/InfoWindow.tsx:85-140,257`; menu verb `web/src/desk/verbRegistry.ts:414-423` | Object → Get Info. Its Filed links open Zone windows; lineage links open pullouts (`web/src/desk/components/InfoWindow.tsx:173-205`). Summary-specific actions come from `infoContract`; this inventory does not infer uninspected contract branches. |
| `ThoughtWorkspaceWindow` | `web/src/desk/components/Pullout.tsx:108-129` routes owned notes; frame `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:505-547` | A Note pullout whose `thoughtForNote` result says `ownership: "thought"`; this is the atlas write-a-thought window path. It keeps the same `pullout:<id>` compositor identity and returns through the supplied close handler. |
| `PulloutFrame` | `web/src/desk/components/Pullout.tsx:21-105`; outer selection `web/src/desk/components/Pullout.tsx:128-129` | All dedicated pullout kinds after compositor resolution. Note rows route through the NoteWindowRouter first. |
| `InlineEditor` on Floor/List | `web/src/desk/gl/WorldStage.tsx:266-268`; List/Face equivalents are owned by those components | Object Edit/New flows; Chair’s direct editor is separately listed above. |
| `SystemShade` | `web/src/desk/components/AttentionDrawer.tsx:89-95`; implementation `web/src/desk/components/SystemShade.tsx` | Attention Dock launcher; its source buttons hand to Desk memory, Meetings, Rhythm, Settings, Intelligence, and People. |

## Pullouts by name and registry distinctions

`PULLOUT_CONTENT` maps 14 distinct components: 13 named dedicated pullout
components plus the single `FallbackPullout` reused by seven rows
(`web/src/desk/pullouts/registry.ts:6-19,26-47`). Those seven rows are fallback
declarations or redirect cases.
The runtime distinction is made by the primitive descriptor before the registry
is rendered (`web/src/desk/store/compositorSlice.ts:137-175`).

### Dedicated pullout contents (14)

| Primitive / pullout name | Content component | Registry anchor | Notable handoffs |
|---|---|---|---|
| Meeting | `MeetingPullout` | `web/src/desk/pullouts/registry.ts:27` | Artifact opens from `web/src/desk/pullouts/MeetingPullout.tsx:67`; Speak and Live actions are at `web/src/desk/pullouts/MeetingPullout.tsx:190-198`; shell Review meeting action is `web/src/desk/components/Pullout.tsx:76-85`. |
| Artifact | `ArtifactPullout` | `web/src/desk/pullouts/registry.ts:28` | Speak handoff `web/src/desk/pullouts/ArtifactPullout.tsx:68`. |
| Note | `NotePullout` | `web/src/desk/pullouts/registry.ts:29` | Note is routed through `NoteWindowRouter` (`web/src/desk/components/Pullout.tsx:108-129`); ordinary Note uses `web/src/desk/pullouts/NotePullout.tsx:478`, owned Thought uses `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:505-547`; Speak/edit paths are in `web/src/desk/pullouts/NotePullout.tsx:478` and its editor calls. |
| Knowledge | `KbPullout` | `web/src/desk/pullouts/registry.ts:30` | Member open and Speak at `web/src/desk/pullouts/KbPullout.tsx:62,95`; edit at `web/src/desk/pullouts/KbPullout.tsx:103`. |
| Decision | `DecisionPullout` | `web/src/desk/pullouts/registry.ts:31` | Speak at `web/src/desk/pullouts/DecisionPullout.tsx:170`; related decision links at `web/src/desk/pullouts/DecisionPullout.tsx:138-143`. |
| Persona | `RecipePullout` | `web/src/desk/pullouts/registry.ts:32` | New Thread pullout at `web/src/desk/pullouts/RecipePullout.tsx:36`; Speak at `web/src/desk/pullouts/RecipePullout.tsx:97`. |
| Sequence | `ChainPullout` | `web/src/desk/pullouts/registry.ts:33` | Speak/edit at `web/src/desk/pullouts/ChainPullout.tsx:67,75`. |
| Workflow | `WorkflowPullout` | `web/src/desk/pullouts/registry.ts:34` | Speak at `web/src/desk/pullouts/WorkflowPullout.tsx:56`; shell Edit Workflow action opens Workbenches (`web/src/desk/components/Pullout.tsx:87-96`). |
| Coder session | `CoderPullout` | `web/src/desk/pullouts/registry.ts:35` | Speak at `web/src/desk/pullouts/CoderPullout.tsx:169`; session controls continue at `web/src/desk/pullouts/CoderPullout.tsx:180` and following code. |
| Directory | `DirectoryPullout` | `web/src/desk/pullouts/registry.ts:36` | Member open at `web/src/desk/pullouts/DirectoryPullout.tsx:56`; Speak at `web/src/desk/pullouts/DirectoryPullout.tsx:79`. Object Open on a directory is intercepted to `ZoneWindow` before this content (`web/src/desk/verbRegistry.ts:399-411`). |
| Thread | `ThreadPullout` | `web/src/desk/pullouts/registry.ts:37` | New thread at `web/src/desk/pullouts/ThreadPullout.tsx:1401`; object Continue in Thread creates and opens one (`web/src/desk/verbRegistry.ts:464-484`). |
| Fallback (seven names) | `FallbackPullout` | `web/src/desk/pullouts/registry.ts:17,38-42,45-46` | Shared fallback component for Project, Repository, Roadmap, Story, Workbench, Game, and Layout declarations. `openPullout` redirects or no-ops these before the component is normally rendered; see the distinction table below. |
| Intelligence | `IntelligencePullout` | `web/src/desk/pullouts/registry.ts:43` | Opened by Intelligence mark/Dock/attention paths; no hosted SurfaceWindows row. |
| People | `PeoplePullout` | `web/src/desk/pullouts/registry.ts:44` | Primitive `people` redirects to People surface before registry (`web/src/lib/primitives.ts:640-650`); People pullout remains the registry content for direct `people:<id>` content resolution if reached. |

The table has 13 named dedicated components plus the shared FallbackPullout.
The registry’s seven fallback names are listed in the next table and must not
be counted as seven additional components.

### Fallback, redirect, and no-op distinctions (7 registry rows)

| Registry name | Descriptor / compositor result | Actual destination |
|---|---|---|
| Project | `surface: { type: "surface", surfaceKey: "open-project-memory" }` at `web/src/lib/primitives.ts:518-528`; compositor branch `web/src/desk/store/compositorSlice.ts:158-169` | SurfaceWindows Project Memory, scoped `project:<id>` through `web/src/desk/shell.ts:103-113`. Registry fallback row is not mounted. |
| Repository | `surface: { type: "window", windowKey: "RepositoryWindow" }` at `web/src/lib/primitives.ts:529-539`; compositor branch `web/src/desk/store/compositorSlice.ts:153-157` | `RepoWindow`, one of the direct `DeskApp` mapped windows. |
| Roadmap | `web/src/lib/primitives.ts:596-606`; compositor window branch `web/src/desk/store/compositorSlice.ts:153-157` | `RoadmapWindow`, one of the direct `DeskApp` mapped windows. |
| Story | `surface: { type: "none" }` at `web/src/lib/primitives.ts:607-617` | No pullout/window/surface action in `openPullout`; source census records no-op. |
| Workbench | `web/src/lib/primitives.ts:618-628`; compositor window branch `web/src/desk/store/compositorSlice.ts:153-157` | `WorkbenchWindow`, one of the direct `DeskApp` mapped windows. |
| Game | `surface: { type: "none" }` at `web/src/lib/primitives.ts:585-595` | No pullout/window/surface action in `openPullout`; source census records no-op. |
| Layout | `surface: { type: "none" }` at `web/src/lib/primitives.ts:663-674` | No pullout/window/surface action in `openPullout`; source census records no-op. |

Directory is a special distinction: its descriptor says pullout
(`web/src/lib/primitives.ts:495-506`), but Object Open chooses `openZoneWindow` for a
directory at `web/src/desk/verbRegistry.ts:399-411`. People is a surface redirect in the
descriptor, even though `web/src/desk/pullouts/registry.ts:44` contains a People pullout component.
`openPullout` is therefore the authority for the actual destination, not the
presence of a name in the registry table.

## Frame, Dock, Expose, Switcher, Snap Ghost, palette, Get Info, Chair dock, and arrival

### Frame and window controls

Every `DeskWindowFrame` supplies drag, resize, persistence, focus, minimize,
maximize, phone-sheet behavior, and close lifecycle from
`web/src/desk/components/DeskWindow.tsx:1-9,539-755`. Its visible head and
actions are at `web/src/desk/components/DeskWindow.tsx:757-882`: close, minimize, maximize, double-click
maximize, Escape close, and the head context menu. Window-facing verbs are
registered in `web/src/desk/verbRegistry.ts:634-699` (close, minimize, cycle, snap, maximize),
and `DeskWindow` maintains the compositor/window registry used by Dock, Expose,
and Switcher.

### Dock

The OS Dock is mounted at `web/src/desk/DeskApp.tsx:302` and implemented at
`web/src/desk/components/window/Dock.tsx:36-356`.

* Five manifest application seats are emitted at `web/src/desk/components/window/Dock.tsx:143-207` and are
  Change places only through separate RoomActions; the actual five seats are
  Intelligence, Speak, Meetings, Agents, and Settings from the manifest
  declarations at `web/src/desk/applications.ts:66-74,76-94,106-123,126-144,147-172`.
* Chair/Floor toggle and runtime launchers are emitted at `web/src/desk/components/window/Dock.tsx:208-259`.
  RoomActions provides the Places action at `web/src/desk/components/window/RoomActions.tsx:25-49`.
* Non-primary running windows receive focus/restore/close chips at
  `web/src/desk/components/window/Dock.tsx:260-312`; Overview and Reset layout appear when windows exist at
  `web/src/desk/components/window/Dock.tsx:313-334`.
* A Dock click focuses/restores a running seat or calls `openSurfaceOr` for a
  cold hosted seat (`web/src/desk/components/window/Dock.tsx:143-177`). Intelligence calls
  `openIntelligence` because it is not a hosted surface.

There is no source component named `ChairDock`. The source has a Chair-local
CaptureBar (`web/src/desk/chair/ChairHome.tsx:2747-2791`) and the OS Dock
(`web/src/desk/DeskApp.tsx:302`). This inventory maps “Chair dock” to those two source
surfaces and does not claim a visual equivalence.

### Expose, Switcher, and Snap Ghost

* **Expose** is a transient region, not a dialog. It reads the window registry,
  displays open windows, and restores/focuses the selected entry at
  `web/src/desk/components/window/Expose.tsx:55-61,110-150`. Escape closes it
  (`web/src/desk/components/window/Expose.tsx:42-53`); `desk.overview` and Dock Overview are its source triggers
  (`web/src/desk/verbRegistry.ts:302-311`; `web/src/desk/components/window/Dock.tsx:313-323`).
* **Switcher** is a 900 ms MRU strip published by window cycling
  (`web/src/desk/components/window/Switcher.tsx:14-28,31-55`). It does not add
  a window to the compositor.
* **Snap Ghost** is an aria-hidden translucent tile while a drag publishes a
  landing rectangle (`web/src/desk/components/window/SnapGhost.tsx:1-41`). It
  is mounted in the normal Desk branch at `web/src/desk/DeskApp.tsx:303`.

### Palette and menus

The menu bar has Desk, Object, Go, and Window IDs at
`web/src/desk/components/DeskMenuBar.tsx:28-33`. At compact width only Go is
rendered; the other menu verbs are appended to Go at `web/src/desk/components/DeskMenuBar.tsx:97-109`.
The verb registry builds Go rows from `DESK_TOOLS` at
`web/src/desk/verbRegistry.ts:606-633`. This is why the 23 manifest rows do not
all have the same Go reach: only grouped app/tool rows enter the Go projection,
while mark, Dock, direct object, or route paths can still reach other actions.

The `⌘K` palette is opened by the system search verb and mounted by
`web/src/desk/components/DeskToolShelf.tsx:557-611`; its portal rows are grouped at
`web/src/desk/components/DeskToolShelf.tsx:345-495`, and selection runs at `web/src/desk/components/DeskToolShelf.tsx:616-708`.
Its program rows include Go verbs plus the launcher registry
(`web/src/desk/components/DeskToolShelf.tsx:398-423`). This is the source basis for the Palette claims
in the application table.

### Get Info

Object → Get Info is `web/src/desk/verbRegistry.ts:414-423`; selected object identity is
rendered by `web/src/desk/components/InfoWindow.tsx:85-140`. Filed links open Zone windows and lineage
links open a resolved pullout (`web/src/desk/components/InfoWindow.tsx:173-205`). The Info window is
mounted through WorldStage’s `infoWindows` map at `web/src/desk/gl/WorldStage.tsx:275-277`, so
it is a nested non-registry frame and not a SurfaceWindows application.

### Arrival and first value

`web/src/desk/DeskApp.tsx:195-213` waits for the combined refresh/setup result. On a normal
arrival, `ChairHome` chooses First Words when `arrivalRequired` and otherwise
renders Chair plus Arrival (`web/src/desk/chair/ChairHome.tsx:467-484`). First Words provides the
dictation first-use face and its recovery actions; setup recovery calls
`configure-setup` and project setup calls `project-setup`
(`web/src/desk/components/FirstWords.tsx:360-481`). During this branch, SurfaceWindows is mounted in
recovery-only mode and registers only the two Setup keys
(`web/src/desk/components/SurfaceWindows.tsx:61-70,86-109`). A staged deep link is consumed only by the
normal registry after all rows register (`web/src/desk/components/SurfaceWindows.tsx:98-119`), while
`openPrimitive` walks home through `/?open=<ref>` and refreshes before opening a
pullout (`web/src/desk/shell.ts:115-130`).

## Handoff index — what opens what

These are the concrete cross-face handoffs found in the source census. They are
grouped so the exact source path and line is retained for later Tuesday probes.

| Source action / face | Opens | Evidence |
|---|---|---|
| Chair setup blocker | Concierge / Models, scoped `models` | `web/src/desk/chair/ChairHome.tsx:1181-1209` |
| First Words microphone recovery | Setup surface | `web/src/desk/components/FirstWords.tsx:360-481`; registry recovery `web/src/desk/components/SurfaceWindows.tsx:61-109` |
| First Words project recovery | New Project / Door | `web/src/desk/components/FirstWords.tsx:360-481`; action manifest `web/src/desk/applications.ts:348-362` |
| Chair CaptureBar — microphone | Starts dictation/capture path | `web/src/desk/chair/ChairHome.tsx:2757-2765` |
| Chair CaptureBar — Write a thought | Creates/open Note pullout | `web/src/desk/chair/ChairHome.tsx:2769-2775`; note creation `web/src/desk/newThought.ts:57` |
| Chair CaptureBar — Record meeting | Starts recording and opens Live | `web/src/desk/chair/ChairHome.tsx:2776-2782`; `web/src/desk/components/RecordOrb.tsx:59-75` |
| Chair CaptureBar — Schedule | Schedule create window | `web/src/desk/chair/ChairHome.tsx:2783-2789`; `web/src/desk/DeskApp.tsx:291` |
| Record Orb | Live meeting surface | `web/src/desk/components/RecordOrb.tsx:59-75`; manifest `web/src/desk/applications.ts:175-188` |
| Meeting pullout “Review meeting” | Meetings surface with meeting scope | `web/src/desk/components/Pullout.tsx:76-85` |
| Workflow pullout “Edit Workflow” | Workbenches surface with workflow scope | `web/src/desk/components/Pullout.tsx:87-96` |
| Pullout content Speak actions | Speak / Dictation surface, generally with resource ref | `web/src/desk/pullouts/ArtifactPullout.tsx:68`; `web/src/desk/pullouts/ChainPullout.tsx:67`; `web/src/desk/pullouts/CoderPullout.tsx:169`; `web/src/desk/pullouts/DecisionPullout.tsx:170`; `web/src/desk/pullouts/DirectoryPullout.tsx:79`; `web/src/desk/pullouts/KbPullout.tsx:95`; `web/src/desk/pullouts/MeetingPullout.tsx:190`; `web/src/desk/pullouts/NotePullout.tsx:478`; `web/src/desk/pullouts/RecipePullout.tsx:97`; `web/src/desk/pullouts/WorkflowPullout.tsx:56` |
| Settings model/assignments | Concierge / Models | `web/src/pages/cores/SettingsCore.tsx:2290-2295`; manifest alias `web/src/desk/applications.ts:325-345` |
| Settings calendar snapshot | Calendar Snapshot review surface | `web/src/pages/cores/SettingsCore.tsx:2115`; manifest `web/src/desk/applications.ts:416-429` |
| Settings integration module | Settings scoped `integration:destinations` | `web/src/pages/cores/SettingsCore.tsx:1969`; `web/src/desk/applications.ts:157-159,442-450` |
| Speak runtime model section | Concierge / Models with remembered task focus | `web/src/pages/cores/dictation/DictationSections.tsx:27-40`; `web/src/pages/cores/dictation/SpeakFace.tsx:651-657` |
| Thought workspace “Choose an engine” | Concierge / Models, scope `models`, preserving task focus | `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:328-333` |
| Thought note ownership | ThoughtWorkspaceWindow replaces ordinary Note pullout | `web/src/desk/components/Pullout.tsx:108-129`; `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:505-547` |
| Object Open on directory | Zone window | `web/src/desk/verbRegistry.ts:399-411`; frame `web/src/desk/components/ZoneWindow.tsx:106-194` |
| Object Open on other primitive | Primitive-dependent pullout/window/surface/no-op | `web/src/desk/verbRegistry.ts:399-411`; `web/src/desk/store/compositorSlice.ts:137-175` |
| Object Get Info Filed link | Zone window | `web/src/desk/components/InfoWindow.tsx:173-186` |
| Object Get Info lineage link | Pullout | `web/src/desk/components/InfoWindow.tsx:190-205` |
| Project object | Desk memory, scoped `project:<id>` | `web/src/lib/primitives.ts:518-528`; `web/src/desk/shell.ts:103-113` |
| People primitive | People surface | `web/src/lib/primitives.ts:640-650`; manifest `web/src/desk/applications.ts:399-413` |
| Repository / Roadmap / Workbench primitive | Corresponding generated window | `web/src/lib/primitives.ts:529-539,596-606,618-628`; compositor `web/src/desk/store/compositorSlice.ts:153-157` |
| Attention source history | Meetings, with source scope | `web/src/desk/components/AttentionDrawer.tsx:56-63` |
| Attention source cadence | Rhythm, with source scope | `web/src/desk/components/AttentionDrawer.tsx:56-63` |
| Attention other source | Primitive open; home walk if needed | `web/src/desk/components/AttentionDrawer.tsx:56-63`; `web/src/desk/shell.ts:115-130` |
| Attention Desk memory launcher | Project memory surface | `web/src/desk/components/AttentionDrawer.tsx:74-95` |
| System Shade actions | Desk memory, Meetings, Rhythm, Settings, Intelligence, People | `web/src/desk/components/SystemShade.tsx:197,199,455,651,807` |
| Glass Drop screenshot/import | Calendar Snapshot or Meetings | `web/src/desk/components/GlassDropLayer.tsx:65-69,82-95,137-158` |
| Trust egress window | Settings after trust view | `web/src/desk/components/TrustWindow.tsx:159-168`; source chip `web/src/desk/components/DeskChrome.tsx:259-266` |
| Desk Tool Inspector project/thread/capability/integration | Project memory, thread pullout, Concierge, Settings scoped integration | `web/src/desk/components/DeskToolInspector.tsx:297,333,341,506,519-524` |
| Desk Tool Shelf project/object/settings/model | Project memory, pullout, Inspector, Settings, thread | `web/src/desk/components/DeskToolShelf.tsx:341-375,445-494` |
| Workbench recipe | Recipe pullout | `web/src/desk/components/WorkbenchWindow.tsx:543` |
| Decisions/brief/follow-through views | Meeting, Workbench, People-intended, Speak | `web/src/desk/pullouts/views/DecisionsView.tsx:137,152`; `web/src/desk/pullouts/views/BriefView.tsx:490,502`; `web/src/desk/pullouts/views/FollowThroughView.tsx:165-178`. Brief “Open person” calls `openSurfaceOr("people", "/people", relationship_id)`; source has no `people` alias or `/people` route, so this particular handoff falls back to the wildcard `/` path in `web/src/App.tsx:60-68`. |
| Repository / roadmaps / workbench templates | Corresponding generated windows | `web/src/desk/components/WorkbenchTemplatePicker.tsx:54,74`; direct maps `web/src/desk/DeskApp.tsx:269-289` |
| Pane picker | Coder session | `web/src/desk/components/SessionPullout.tsx:254-318` |
| Delivery board | Dossier and Delivery terminal | `web/src/desk/components/DeliveryBoard.tsx:380-423,443-475,519-521` |

## Tuesday lens (J1–J5)

This is a source reachability lens for the five Tuesday jobs in the settled
grounding plan. It records the route and handoff evidence to probe; it does not
assert that the job was visually verified.

| Tuesday job | Source path through the Desk | Evidence and open boundary |
|---|---|---|
| J1 — the morning: arrive → read the brief → open what needs him today | Arrival/normal Desk → Intelligence Dock/mark → Brief view → THIS WEEK and open source actions | `web/src/desk/pullouts/IntelligencePullout.tsx:13-17,78-85,135-163`; `web/src/desk/pullouts/views/BriefView.tsx:158-208,337-376`; arrival gate `web/src/desk/DeskApp.tsx:115-187,195-213`. Server setup state and brief data were not loaded. |
| J2 — a meeting: start → live → summary → decision → send the update | CaptureBar/Record Orb → Live → Meeting pullout summary → Decisions view/source → one Meeting Send well (Summary, Digest, or Follow-up) | `web/src/desk/chair/ChairHome.tsx:2747-2791`; `web/src/desk/components/RecordOrb.tsx:59-75`; `web/src/desk/pullouts/MeetingPullout.tsx:120-156`; `web/src/pages/cores/history/MeetingDetail.tsx:167-176`; `web/src/desk/pullouts/views/DecisionsView.tsx:135-153`; `web/src/meetings/MeetingSendWell.tsx:1-47`. No meeting data or visual state was loaded. |
| J3 — a 1:1 with one of his three reports: prep → notes → follow-ups | People mark/surface → Prep lens → Grounding notes / 1:1 agenda → Follow-through/commitment actions | `web/src/pages/cores/PeopleCore.tsx:29-36,304-309,349-474` (Prep); `web/src/pages/cores/PeopleCore.tsx:590-607` (notes); `web/src/pages/cores/PeopleCore.tsx:702-734` (commitments and 1:1 agenda); `web/src/desk/pullouts/views/FollowThroughView.tsx:142-180`. No person records were opened. |
| J4 — a project: open the Room → what changed → publish an update | Project object/Desk memory → scoped Project Room → changed/history sections → Draft update posture | `web/src/desk/shell.ts:103-113`; `web/src/features/project-room/ProjectRoomCore.tsx:1-2,2094-2124`; Room head and Draft update `web/src/features/project-room/ProjectRoomCore.tsx:307-357`; update posture `web/src/features/project-room/ProjectRoomCore.tsx:2157-2171`. No project rows or persisted windows were inspected at runtime. |
| J5 — capture a thought by voice and find it again later | CaptureBar Write a thought → Note pullout / ThoughtWorkspaceWindow when owned → later Note open via Desk primitive route | `web/src/desk/chair/ChairHome.tsx:2769-2775`; `web/src/desk/components/Pullout.tsx:108-129`; `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:505-547`; home walk `web/src/desk/shell.ts:115-130`. No live hub row or shot was captured. |

## Unknowns and limits

1. **No visual verification.** This inventory has no 1440 or 393 shot, no hit
   target/overflow observation, and no claim that a face is visually usable.
2. **No live walk or hub state.** Conditional rows (arrival, empty Desk,
   meetings, people, sessions, repositories, delivery state, thought
   ownership) are source-reachable only. Their current data, network result,
   and open-window instance set are unknown.
3. **Chair dock naming.** No `ChairDock` symbol exists in the source census;
   “Chair dock” is mapped to CaptureBar plus the OS Dock. Whether the intended
   atlas case means one or both needs Muad’Dib’s check.
4. **Info summaries.** `InfoWindow` delegates summary actions through
   `infoContract`; this inventory anchors the frame, Filed, and lineage paths
   but does not infer every summary action (`web/src/desk/components/InfoWindow.tsx:228-257`).
5. **Demoted fallback behavior.** `openSurfaceOr` falls back to the supplied
   href if a surface is not registered (`web/src/desk/shell.ts:93-101`). This
   inventory records source hrefs and route rows; it did not run cold-start
   timing or a browser route.
6. **Registry fallback declarations.** The seven names in
   `web/src/desk/pullouts/registry.ts:38-46` are counted as declarations, but descriptor/compositor
   routing means several never reach a fallback component. Their actual
   destinations are recorded above; no “fallback visible” claim is made.
7. **Redirect duplication.** `configure-runs-on` and
   `configure-integrations` are manifest actions with shared Settings or
   Concierge identities/aliases. The rows are intentionally kept separate so
   their action reachability and scopes remain auditable; they do not imply
   extra windows.
8. **Receipt and transition states.** Source transition hooks and receipts are
   anchored where found, but no receipt row, producer state, branch transition,
   or “real producer” output was observed. These are evidence questions for the
   later probes.

This closes the source census only. It does not close a face, a walk, a story,
or a visual verification claim.
