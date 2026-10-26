# Egress labels — the inventory (2026-10-25)

Owner, 2026-10-25, on a Today shot with `KAROLSANEAPPLE.ATLASSIAN.NET` chips on
every Jira row: "I'm also pissed off at the ever-present 'labels' (the LAN, the
192.168.1.36, the jira label as visible on that screen) ... It feels like an
ancient relic now..."

The rule (UX-CANON A.9, amended the same day): no host, IP address or scope word
on the rows, toolbars or status bars of a working window. Name an engine by its
name. The address stays where the choice or the act is made.

Fences: `tests/unit/test_egress_labels_canon.py` (source) and the desk sweep's
`labels` fence (`tests/e2e/test_desk_sweep.py`, rendered).

## Removed (working windows)

| Window | Site (web/src) | Was | Now names the destination at |
|---|---|---|---|
| Today, Needs you | `desk/needs/NeedsDrawer.tsx` pr row | `github.com` chip | Open PR hover title (the URL) |
| Today, Needs you | `desk/needs/NeedsDrawer.tsx` repair row | Jira / GitHub host chip beside Retry | Retry hover title `Checks <host> again` |
| Today, Needs you | `desk/needs/NeedsDrawer.tsx` send row | destination chip | the row fact (`DOCUMENT → <destination>`), Look (the Send preview), Send hover title |
| Today, Meetings | `meetings/RouteDisclosure.tsx` (`today-route`, `row-route`, `detail-route`, `recovery-route`) | route host chips and `+ FALLBACK <host>` | summary verb hover title (`routeTitle`): Make the summary, Run summary, Retry |
| Today, Meetings | `meetings/RouteDisclosure.tsx` `RunAttempts` | every contacted host | a failed attempt only, as its outcome; the host in its hover title |
| Today, Room | `desk/standingPages.tsx` | `Written by qwen3.8-27b · LAN` | `Written by qwen3.8-27b` |
| Ask | `desk/components/AskPanel.tsx` status bar | route lamp `LAN` / `CLOUD` / `LOCAL` | none; the engine by name |
| Ask, Room | `desk/hooks/useEngine.ts`, `surface/EngineLine.tsx`, `surface/RunLine.tsx` | `qwen · LAN`, `Working · qwen · CLOUD` | the engine name only |
| Speak | `pages/cores/dictation/SpeakFace.tsx` engine row, status bar; `DictationCore.tsx` footer | host / `CLOUD` / `· LAN` chip; `whisper on this Mac` | the engine name only |
| Agents | `desk/conductor/ConductorWindow.tsx` status bar | `API.ANTHROPIC.COM` chip | none (the Hand confirm names it before a start) |
| Agents | `desk/lane/LaneWindow.tsx` footer, draft row | `GITHUB.COM`, draft model host | Open PR hover title; none on the draft |
| Agents, Today, Room | `desk/components/AgentFlight.tsx` | `GITHUB.COM` chip | Open PR hover title |
| Meetings | `pages/cores/HistoryCore.tsx`, `history/MeetingRecord.tsx` status bars; `history/MeetingHeader.tsx` strip | summary host chip | summary verb hover title |
| Meetings (Live) | `pages/cores/LiveCore.tsx` status bar | intel egress chip | Live's configure face (kept) |
| Room Now | `features/project-room/ProjectRoomCore.tsx` proposal rows, source rows | model / source host chips | none |
| Room Now | `ProjectRoomCore.tsx` ask well | `MODEL · <host>` chip | the engine name |
| Room History | `ProjectRoomCore.tsx` receipts | `REMOTE · <ip>` chip | none |
| Room Now | `features/project-room/NudgeCard.tsx` SENT and UNKNOWN rows | `GITHUB.COM` chip | the open nudge card (kept, below) |
| Room Prepare | `prepare/PreparePosture.tsx` route, progress, footer; `prepare/model.ts` | host chips; `SENT · 127.0.0.1 · …` | the model name: `SENT · QWEN3 35B · …` |
| Room Update | `update/UpdatePosture.tsx` footer, provenance | host chip; `QWEN · 192.168.1.43:8080 · LAN` | the model name |
| Drawers | `desk/drawer/DrawerWindow.tsx`, `InfoWindow.tsx` status bars | link host chip | Open hover title (the URL) |
| Activity | `pages/cores/ActivityFinishedReceipts.tsx` | `REMOTE · <ip>`, host chips, `N remote` | Who: `You` / `Another device` |
| Automations | `desk/components/automation/AutomationWindow.tsx` status bar | `engine · where` chip | the With slot names the engine |
| Automations | `automation/ResultCard.tsx` | `CLOUD` / `LAN` chip | the model by name |
| Voice | `desk/voice/ProposalStrip.tsx` | scope chip after the act | none |
| Components | `design-reference/WindowReference.tsx` reader, `ConversationReference.tsx` | `studio.local · LAN`, `LAN` lamp, `Private network` | none (the reference follows the rule) |
| Workbench | `desk/components/WorkbenchWindow.tsx` item result | `⌂ LOCAL` / `LAN` / `CLOUD` chip | none |
| Workbench | `desk/components/workbench/WorkbenchRunsWing.tsx` run rows, run facts | `· LAN ·` in the row, `egress` fact | the model by name |
| Workbench | `desk/components/WorkbenchAutomations.tsx` automation head | `GITHUB` / `JIRA` egress badge | the source by name, quiet (`GitHub`, `Jira`) |
| Delivery | `desk/components/DeliveryBoard.tsx` toolbar | `Hub` chip | none |
| Delivery | `desk/components/DeliveryDossierWindow.tsx` asset rows | `↗ Download` drawn as an egress chip | a quiet `Download ↗` cell |
| Rhythm | `pages/cores/CadenceCore.tsx` runs-on facts, status bar | `REMOTE · <host>` chip; empty footer chip | none; the Where it runs picker (kept) |
| Tool inspector | `desk/components/DeskToolInspector.tsx` status bar | route host chip | the propose and approve verbs' hover title `Goes to <host>` |

Count: 26 working-window site groups removed in #1481 (34 web source files, tests excluded), and 7 more in the left-overs slice (7 files). 12 kept groups below.

## Kept (the choice or the act)

| Window | Site | Why |
|---|---|---|
| Send preview, confirm | `desk/surface/send/SendWell.tsx` | the channel destination before the press |
| Settings ▸ Destinations, Connections | `pages/cores/connections/*` | where the choice is made |
| Settings ▸ Engines, What runs where | `features/runson/*`, `pages/cores/AssignmentEditor.tsx`, `AssignmentModelChooser.tsx`, `ModelLibraryCore.tsx`, `TopologyMapView.tsx`, `settingsTts.tsx`, `SettingsCore.tsx` | where the choice is made |
| Hand confirm | `desk/hand/HandConfirm.tsx`, `desk/components/HandSheet.tsx` | the confirm before an agent run |
| Setup, the Door | `desk/firstrun/*`, `features/concierge/*`, `features/project-room/door/DoorCore.tsx` | setup |
| Room nudge card | `features/project-room/NudgeCard.tsx` (open card) | the preview before Send to GitHub |
| Room Steward policy | `features/project-room/steward/StewardPosture.tsx` | configuration |
| Automations With / Put choosers | `automation/WithEditor.tsx`, `PutEditor.tsx` | where the choice is made |
| Speak configure, Live configure | `dictation/Readiness.tsx`, `LiveCore.tsx` configure face | configuration |
| Feedback recorder | `desk/feedback/UiFeedbackHost.tsx` | the act (speech route while recording) |
| Menu bar trust badge | `desk/components/DeskChrome.tsx` | opens Privacy and trust; says `→ Your network`, no address |
| Components specimens | `ControlsGallery.tsx`, `ObjectSpeciesGallery.tsx`, `WindowReference.tsx` Engines | the species reference |

## Left for a later slice

- Agents' status bar says `N on this Mac` (the coders installed here, not egress).
- The dead code #1481 kept for tests is gone: `useDraftEgress` (parked at
  `desk/lane/_parked/useDraftEgress.tsx`, its test at `desk/lane/__tests__/_parked/`),
  `isLanHost` (parked with its test at `pages/cores/dictation/__tests__/_parked/`), and the
  `saidOnFace` pass-through (removed; no caller set it).
- Not in the ruling's list and still wearing an egress badge: `desk/components/PrReceiptsSection.tsx`
  (`GitHub` badge in the head and on a proposal).
