# Surface census — 2026-10-14

Snapshot: main `6e86c666a` (#1199). The census follows the current application and content registries, plus the other window hosts mounted by DeskApp. Capture presence is evidence availability; it is not a design verdict or proof that an inner operation works. Lane reports state which captures were actually inspected.

## Declared applications

24 manifest rows: 21 unparked entries and 3 parked compatibility rows. The 18 entries with a core loader coexist with special Today, Ask and Conductor hosts. Duplicate compatibility rows are retained as declared; they are not extra independent apps.

| Entry | Window | Lane | Base capture 1440 / 393 | Note |
|---|---|---|---|---|
| Change places (`change-places`) | `surface-places` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Today (`open-intelligence`) | `intelligence:desk` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Speak (`dictate`) | `surface-dictation` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Ask AI (`ask`) | `ask:desk` | work | supplement or source only / supplement or source only | Check final lane coverage; some early shots show only loading. |
| Meetings (`review-meetings`) | `surface-meetings` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Conductor (`open-conductor`) | `conductor` | conductor | file / file | Check final lane coverage; some early shots show only loading. |
| Agents (`inspect-personas-and-coders`) | `surface-companion` | conductor | file / file | Check final lane coverage; some early shots show only loading. |
| Settings (`configure-settings`) | `surface-settings` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Live meeting (`record-live`) | `surface-live` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Rhythm (`configure-cadence`) | `surface-cadence` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Setup (`configure-setup`) | `surface-setup` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Context (`open-constitutional-context`) | `surface-constitutional-context` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Workbenches (`open-workbenches`) | `surface-workbenches` | conductor | file / file | Check final lane coverage; some early shots show only loading. |
| Components (`design-components`) | `surface-components` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Activity (`inspect-activity`) | `surface-activity` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Memory (`open-project-memory`) | `surface-project-memory` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Engines (`open-concierge`) | `surface-concierge` | tools | parent host | Parked → settings:models |
| New Project (`project-setup`) | `surface-project-setup` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Processes (`inspect-processes`) | `surface-processes` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| Commands (`configure-commands`) | `surface-commands` | tools | file / file | Check final lane coverage; some early shots show only loading. |
| People (`open-people`) | `surface-people` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Calendar snapshot (`review-calendar-snapshot`) | `surface-calendar-snapshot` | work | file / file | Check final lane coverage; some early shots show only loading. |
| Engines (`configure-runs-on`) | `surface-concierge` | tools | parent host | Parked → settings:models |
| Accounts (`configure-integrations`) | `surface-settings` | tools | parent host | Parked → settings:integrations |

## Object content registry

20 primitive kinds map to 13 specific content modules and 7 fallback mappings. A fallback mapping alone does not prove a reachable empty screen: some kinds open through a dedicated host first.

| Kind | Content | Audit evidence |
|---|---|---|
| `meeting` | `MeetingWindow` | work report: object captures / explicit state gaps |
| `artifact` | `ArtifactPullout` | root source inspection; not rendered in this audit |
| `note` | `NotePullout` | work report: object captures / explicit state gaps |
| `kb` | `KbPullout` | root source inspection; not rendered in this audit |
| `decision` | `DecisionPullout` | work report: object captures / explicit state gaps |
| `recipe` | `RecipePullout` | root source inspection; not rendered in this audit |
| `chain` | `ChainPullout` | root source inspection; not rendered in this audit |
| `workflow` | `WorkflowPullout` | root source inspection; not rendered in this audit |
| `coder` | `CoderPullout` | conductor report; legacy coder projection differs from SessionPullout |
| `directory` | `DirectoryPullout` | root source inspection; not rendered in this audit |
| `thread` | `ThreadPullout` | work report: object captures / explicit state gaps |
| `project` | `FallbackPullout` | project Room in work report; specific host overrides fallback |
| `repository` | `FallbackPullout` | root source inspection; not rendered in this audit |
| `roadmap` | `FallbackPullout` | root source inspection; not rendered in this audit |
| `story` | `FallbackPullout` | root source inspection; not rendered in this audit |
| `workbench` | `FallbackPullout` | specific host in conductor report; fallback not reached by this audit |
| `intelligence` | `IntelligencePullout` | work report: object captures / explicit state gaps |
| `people` | `PeoplePullout` | work report: object captures / explicit state gaps |
| `game` | `FallbackPullout` | root source inspection; not rendered in this audit |
| `layout` | `FallbackPullout` | root source inspection; not rendered in this audit |

## Hosts outside the application core list

These are live mounts in `web/src/desk/DeskApp.tsx:214-278`. They explain why a manifest-only sweep is insufficient.

| Host / operation | Audit ownership | Evidence / limit |
|---|---|---|
| AskPanel; HandSheet | work / conductor | Ask rendered; hand/launch behavior remains source only unless lane report says otherwise. |
| InlineEditor | root / work | 4 editors are registered (Note, Knowledge, Workflow, Recipe); only Note was visually inspected here. |
| InfoWindow; DeskToolInspector | conductor / root | Conductor Info captured; generic inspector not rendered. |
| MissionControlConveyor; DeliveryBoard; DeliveryDossierWindow; DeliveryTerminalWindow | conductor / root | Source census only; real delivery operations not exercised. |
| RoadmapWindow; RepoWindow | root | Mounted in source census; not rendered here. |
| WorkbenchWindow; NewWorkbenchChooser; ScheduleCreateWindow | conductor / root | Workbenches home captured; inner object/chooser capture blocked by fixture selector, so source only. |
| PanePicker; SessionPullout | conductor | Session captured at both widths through real Conductor Open; pane control actions not executed. |
| DrawerWindows; ConductorWindows; LaneWindow | work / conductor | Main drawer, Conductor, working lane and asking lane captured; report state limits separately. |

## Root source findings and unobserved tail

Sequence currently offers raw HTML Edit / Dictate controls in `web/src/desk/pullouts/ChainPullout.tsx:63`. Edit calls `openEditor`, but `chain` maps to `null` in `web/src/desk/pullouts/editors/registry.ts:46`; `InlineEditor.tsx:35` returns null without content. This is a concrete source-to-render gap (Tenets 3/5; UX A.1/A.11), not an executed click claim. Verify a live Sequence before fixing its exposed actions. Do not make a new editor framework to address it.

Artifact, Knowledge, Recipe, Sequence, Workflow and Directory object states, their edit states, generic Get Info, roadmap/repository details, delivery/factory flows, Workbench internals and schedule creation remain outside rendered coverage. They are named here instead of silently inheriting a green app-window verdict. Real inference, agent steering, terminal transport, account sign-in, notification delivery, live microphone, real touch and owner acceptance are unobserved.

## How captures were obtained

Existing `tests/e2e/test_desk_sweep.py` ran once under the machine lock and isolated HOME with `DESK_SWEEP_SHOTS=1`: 106 passed, 3 existing xfails, 109 PNGs. General captures are under `.tmp/evidence-shots/desk-sweep/`; lane scratch captures and observed protocol data remain under `.tmp/surface-audit/` or `.tmp/evidence-shots/surface-audit-conductor/`. The test seeds use real product producer/fixture helpers; external boundaries are isolated doubles. No owner hub, session, DB, keys, microphone or tmux was used.
