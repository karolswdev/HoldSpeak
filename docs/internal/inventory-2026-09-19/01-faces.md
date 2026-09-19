# 01 — FACES: the honest map of what a HoldSpeak user can see and do

Repo: `/Users/karol/dev/tools/HoldSpeak`, branch `main`. Read-only inventory.
Scope: the React+Vite web desk under `web/`. **There is no Astro document
shell any more** — no `astro.config.*` exists anywhere outside
`node_modules`, and `web/package.json` has no astro dependency. One SPA,
one tree.

Everything below is derived from the router (`web/src/routes.tsx`,
`web/src/App.tsx`), the application manifest
(`web/src/desk/applications.ts`), the verb registry
(`web/src/desk/verbRegistry.ts`) and the nav components — not from docs.

---

## 0. The architecture you must understand before the table makes sense

HoldSpeak is **not** a routed web app. It is a fake desktop OS in one page.

| Layer | File | What it is |
|---|---|---|
| Real routes | `web/src/routes.tsx:21-29` | **Three.** `/` (Desk), `/welcome`, `/presence`. That's it. |
| Demoted routes | `web/src/routes.tsx:42-75` | 15 legacy paths that *redirect to `/`* and stage a window open (`web/src/App.tsx:19-44`). They are deep links, not pages. |
| Catch-all | `web/src/App.tsx:71` | `path="*"` → `<Navigate to="/" replace />`. **Any unknown URL silently lands on the Desk with no message.** |
| Application manifest | `web/src/desk/applications.ts:46-425` | 22 "applications". 19 carry a `surface` (a lazily-loaded core hosted in a window); 3 are pointers/aliases. |
| Window host | `web/src/desk/components/SurfaceWindows.tsx:44-53` | Turns manifest rows into registered surface keys. |
| Dispatcher | `web/src/desk/shell.ts:71-100` | `openSurface(key)` → **returns false silently if the key was never registered**; `openSurfaceOr(key, href)` then navigates to `href`. |
| Verb registry | `web/src/desk/verbRegistry.ts:136-780` | ~67 verbs. The menu bar, the mark menu, the floor right-click menu and ⌘K are all projections of it. |

### The five ways a user can reach anything

| # | Entry | File | What it exposes |
|---|---|---|---|
| 1 | **Dock** (bottom, always visible) | `web/src/desk/components/window/Dock.tsx:110`, `applications.ts:441` | Exactly **5** apps: Intelligence, Speak, Meetings, Agents, Settings. Plus a centre Record orb and launcher chips for Desk memory / Delivery / Panes when announced. |
| 2 | **Menu bar** (top-left) | `web/src/desk/components/DeskMenuBar.tsx:24-29` | Four menus: **Desk · Object · Go · Window**. `Go` is the full application list. |
| 3 | **HoldSpeak mark menu** | `web/src/desk/components/DeskChrome.tsx:30`, `applications.ts:449` | 3 view verbs + the 6 `mark: true` applications. |
| 4 | **⌘K command deck** | `web/src/desk/components/DeskToolShelf.tsx:39-46` | Sections PROJECTS / VERBS / PROGRAMS / OBJECTS / SETTINGS / MEETINGS. **The single most complete index in the product, and it is behind an invisible keystroke.** |
| 5 | **Floor right-click** | `web/src/desk/floorMenu.ts:33-56` | `New ▸` / `Launch ▸` + floor verbs. Only exists in *spatial view*, which is not the default (`web/src/desk/chairState.ts` defaults to `chair`). |

There is **no persistent sidebar, no visible nav list, no breadcrumb**. If
a face is not one of the five dock apps, the user must know a menu name, a
keystroke, or the URL.

---

## 1. Every route / screen / face

### 1a. Real routes

| Path | Name on screen | What it is for | How reached | Primary verbs |
|---|---|---|---|---|
| `/` | (no title — the Desk) | The whole product. Renders either **ChairHome** (arrival, the default) or the **spatial Floor**. | Default | see 1c/1d |
| `/welcome` | "◍ HoldSpeak" + first-value card | Compatibility arrival for old bookmarks; renders the same `FirstWords` as the cold Desk. `web/src/pages/WelcomePage.tsx:1-16` | URL only. **Nothing links to it.** | Click to speak · Copy · Keep as Note · Continue later |
| `/presence` | a single status lamp | A one-lamp runtime status page ("Ready"/"Connecting"). `web/src/pages/PresencePage.tsx:11-28` | URL only. **Nothing links to it.** | `← Desk` link |

### 1b. Demoted routes (URL → `/` + window open)

All 15 from `web/src/routes.tsx:42-75`. None is linked from any nav; they
exist for bookmarks and for `openSurfaceOr` fallbacks.

| Path | Opens surface | Note |
|---|---|---|
| `/setup` | `project-setup` (the Door) | |
| `/dictation` | `dictate` (Speak) | |
| `/live` | `record-live` | |
| `/history`, `/meetings` | `review-meetings`, scope `meeting:<id>` | two paths, one face |
| `/settings` | `configure-settings` | |
| `/activity` | `inspect-activity` | |
| `/commands` | `configure-commands` | |
| `/cadence` | `configure-cadence` (shown as **Rhythm**) | |
| `/workbenches` | `open-workbenches` | |
| `/profiles` | `configure-runs-on` → Concierge | path name matches nothing on screen |
| `/studio` | `configure-settings` | tombstone: "Studio died" (`routes.tsx:71`) |
| `/companion` | `inspect-personas-and-coders` (shown as **Agents**) | path name matches nothing on screen |
| `/docs/dictation-runtime` | `read-runtime-docs` → Settings/guide | |
| `/design/components` | `design-components` | developer catalog, shipped to users |

**Paths that look real and are not:** `/projects`, `/models`, `/ask`,
`/context`, `/project-memory`, `/calendar-snapshot`, `/components`. They
are `href` values in the manifest (`applications.ts:98, 209, 236, 287, 327`)
but **not routes** — they hit the `*` catch-all and dump the user on `/`
with no error. See §2 DEAD LINKS.

### 1c. Hosted surfaces (the 19 windows)

Reach key: **DOCK** = bottom dock · **GO** = menu bar Go / ⌘K PROGRAMS
(requires `group: "app"|"tool"`, `desk/tools.ts:4-7`) · **MARK** = HoldSpeak
menu · **URL** = demoted route only · **CODE** = only from another face.

| Surface key | Name on screen | One sentence | Reach | Primary verbs |
|---|---|---|---|---|
| `open-intelligence` | **Intelligence** | Three tabbed views over desk-wide work: Brief, Follow-through, Decisions. `desk/pullouts/IntelligencePullout.tsx:13-17` | DOCK · MARK | Brief / Follow-through / Decisions segments; per-card complete/snooze/delegate |
| `dictate` | **Speak** | Voice typing: talk, watch it land in another app, teach corrections. `pages/cores/dictation/SpeakFace.tsx` | DOCK (⌘1) · GO · MARK | Talk · Open · Teach · Choose (model) · Re-check · Review · Export |
| `review-meetings` | **Meetings** | The recorded-meeting ledger and the typed record of each. `pages/cores/HistoryCore.tsx` | DOCK (⌘2) · GO · MARK · `/history`,`/meetings` | Search · HAS OPEN ACTIONS filter · Open · Delete · Export |
| `inspect-personas-and-coders` | **Agents** (tool label "Agents and coder sessions") | Saved agent behaviours + live coder sessions. `pages/cores/CompanionCore.tsx` | DOCK (⌘3) · GO · MARK · `/companion` | (inspection only; no create verb on the face) |
| `configure-settings` | **Settings** | Nine preference modules. `pages/cores/SettingsCore.tsx`, modules at `pages/cores/settingsPrefs.tsx:40-60` | DOCK (⌘4) · GO · MARK · `/settings` | Open (per module) · Save · module-specific |
| `open-people` | **People** | Relationships, commitments, 1:1 prep. `pages/cores/PeopleCore.tsx` | **MARK only** + `desk.open-people` verb | New relationship · Add · Link calendar event · Link project · Add note · Send to Workbench · Mark satisfied |
| `open-project-memory` | **Desk memory** | *Actually the Project Room.* Re-export: `pages/cores/ProjectMemoryCore.tsx:5-9` → `features/project-room/ProjectRoomCore.tsx`. Six different faces behind one name (see §2). | GO · ⌘K | scope-dependent — see below |
| `open-concierge` | **Models** | Engines found → the proposed set → "Use these". `features/concierge/ConciergeCore.tsx` | **No group ⇒ not in Go/⌘K.** Reached only via the `configure-runs-on` alias (`applications.ts:311`) or `openSurface("open-concierge")` from Settings/Speak | Check · Download · Add · Adjust · Cancel · **Use these** |
| `configure-runs-on` | **Models** (again) | Manifest pointer at `applications.ts:414-422` whose `windowId` is the Concierge. | GO · ⌘K · `/profiles` | — |
| `configure-integrations` | **Connections** | Pointer into Settings scoped to `integration:destinations` (`applications.ts:423-431`). | GO · ⌘K | — |
| `project-setup` | **New Project** (the Door) | Create a Project in one screen. `features/project-room/door/DoorCore.tsx:383` | `desk.new-project` verb (Desk menu, **floor-scoped**) · `/setup` · FirstWords | Cancel · **Create Project** · Connect (per source) · Adjust |
| `record-live` | **Live meeting** | The live recording room. `pages/cores/LiveCore.tsx` | **No group ⇒ not in Go/⌘K.** Record orb, Chair "Record meeting", `/live` | Preview route · Save |
| `configure-cadence` | **Rhythm** | Sweep interval, brief generation, notification cadence, open loops. `pages/cores/CadenceCore.tsx` | GO · ⌘K · `/cadence` | Sweep interval · Runner host · Notification mode/content · Mark done · Kill loop |
| `open-workbenches` | **Workbenches** | Mission control for agent workbenches. `pages/cores/WorkbenchesHomeCore.tsx` | GO · ⌘K · `/workbenches` | **+ Create** |
| `inspect-activity` | **Activity** | This-device work context, meeting candidates, connectors. `pages/cores/ActivityCore.tsx` | GO · ⌘K · `/activity` | Watching toggle · Filter · Delete · Clear records |
| `open-constitutional-context` | **Context** | The always-on briefing every agent receives. `pages/cores/ConstitutionalContextCore.tsx` | GO · ⌘K **only** | Edit · Cancel |
| `inspect-processes` | **Processes** | What the kernel is running. `pages/cores/ProcessCore.tsx` | GO · ⌘K **only** | — |
| `configure-commands` | **Commands** | Map spoken phrases to registered actions. `pages/cores/CommandsCore.tsx` | GO · ⌘K · `/commands` | Save command |
| `change-places` | **Change places** | Environments, favourites, atmosphere, wallpaper, room sound. `pages/cores/ChangePlacesCore.tsx` | GO · ⌘K (⌘⇧P) | pick a place |
| `review-calendar-snapshot` | **Calendar snapshot** | Review calendar evidence before it enters the Desk. | **CODE only** — drag-drop (`desk/components/GlassDropLayer.tsx:68`) or Settings→Meetings (`SettingsCore.tsx:1631`). No route, no menu entry. | accept/reject the snapshot |
| `design-components` | **Components** | The Signal component catalog — a developer artefact. | `/design/components` **URL only** | — |

**The six faces inside "Desk memory".** `ProjectRoomCore.tsx:1869-1965`
routes on scope + server state, in this order:

| Condition | Face | Sections/verbs |
|---|---|---|
| no scope | **Recall** (`recall/RecallFace.tsx`) | Search the Desk · CURRENT / SUPERSEDED / DISPUTED / OWED / MEETINGS / BRIEFS / ALSO |
| scope `q:<sentence>` | Recall, pre-searched | same |
| review pending | **Review posture** (`review/ReviewPosture.tsx`) | Edit · Confirm · Defer · Undo · Close |
| update drafting | **Update posture** (`update/UpdatePosture.tsx`) | Close (draft/publish inside) |
| steward running | **Steward posture** (`steward/StewardPosture.tsx`) | CIRCUITS · Retry · Close |
| prepare active | **Prepare posture** (`prepare/PreparePosture.tsx`) | Purpose · Result · SOURCES · CARRIED FORWARD · CLAIMS · NOT READ · MANIFEST |
| otherwise | **The Room** (`ProjectRoomCore.tsx:774+`) | ROOM/HISTORY wings; NEEDS YOU · SOURCES · RECEIPTS · DECISIONS & COMMITMENTS · UNFINISHED · BRIEFS; Pause/Resume a Watch; Ask this project |

### 1d. Windows mounted directly by the Desk (not in the manifest)

All from `web/src/desk/DeskApp.tsx:216-262`.

| Component | Name on screen | Purpose | Reach |
|---|---|---|---|
| `AttentionDrawer` → `SystemShade` | **"Desk memory"** (bell tooltip, `DeskChrome.tsx:44-47`); panel aria-label **"Missed"** | What happened while you were away: Projects · Coverage · Needs you · Finished · Learned | Bell in the top-right chrome |
| `DeliveryBoard` | **Delivery** | Delivery attempts / PR receipts board | Dock launcher chip, announced at `DeliveryBoard.tsx:384-392` |
| `DeliveryDossierWindow` / `DeliveryTerminalWindow` | dossier / terminal | Drill-down from the board | CODE only |
| `MissionControlConveyor` | **RAILS** | Roadmap/repo/gate rails panel | A floating `RAILS` tab that **only appears if the desk has repos** (`MissionControlConveyor.tsx:598`) |
| `RoadmapWindow` / `RepoWindow` | roadmap / repository | Rails drill-down | CODE only, from the conveyor |
| `WorkbenchWindow` | a workbench | AGENT · RUNS ON · RESOLVES WITH · STARTS WHEN + items/runs/automations | CODE only, from Workbenches home / a pullout |
| `NewWorkbenchChooser` | new-workbench template picker | | `desk.new-workbench` verb |
| `ScheduleCreateWindow` | **Schedule recording** | Arm a scheduled recording | Chair footer "Schedule" (`ChairHome.tsx:2087-2093`) |
| `ThoughtWorkspaceWindow` | **Thought** | Note + Interview panes, AI context attach | "Develop a thought" → Speak, or a thought row |
| `TrustWindow` | **Data boundaries** | Where data goes | The egress chip in the chrome (`DeskChrome.tsx:239`) |
| `SessionPullout` / `PanePicker` | **Panes** | Terminal/coder panes | Dock launcher chip |
| `DeskToolInspector`, `InfoWindow`, `ZoneWindow`, `InlineEditor`, `GlassDropLayer` | — | object inspectors / editors | CODE only |
| `AskPanel` | **Ask AI** | Ask across the work on the desk | `⌘I`, Go menu, `object.ask` |

### 1e. Pullouts — the detail face for a desk object

`web/src/desk/pullouts/registry.ts:28-49`. Opened by `object.open` /
clicking an object / `?open=<ref>`.

| Kind | Content | Note |
|---|---|---|
| meeting | `MeetingPullout` | |
| artifact, note, kb, decision, recipe, chain, workflow, coder, directory, thread, people | dedicated pullouts | |
| intelligence | `IntelligencePullout` | the Intelligence app is a *pullout*, not a window |
| **project, repository, roadmap, story, workbench, game, layout** | `FallbackPullout` | **7 of 20 primitive kinds have no detail face.** Clicking a Project object gives you the fallback. |

### 1f. Chrome transients

| Element | File | What it does |
|---|---|---|
| Hub dot | `DeskChrome.tsx:227` | live / connecting / degraded |
| Egress chip | `DeskChrome.tsx:239-247` | "EXTERNAL REACH ENABLED" etc. → Trust window |
| Mic lamp | `DeskChrome.tsx:72-83` | Mic idle/open/speech/held |
| Attention bell | `DeskChrome.tsx:36-56` | badge = needs-you + held gate items |
| Clock | `DeskChrome.tsx:88-108` | |
| Write receipt | `DeskChrome.tsx:250` | refused floor writes |
| Shortcut sheet | `verbRegistry.ts:684` (⌘/) | |

---

## 2. Reachability: dead ends, orphans, broken links

### 2a. BROKEN — verbs that go nowhere (highest severity)

**The single worst defect in the product's navigation.** The surface key
`"project-room"` **is never registered**. It does not appear in
`DESK_APPLICATIONS` (`applications.ts:46-433`) nor in
`DESK_APPLICATION_ALIASES` (`applications.ts:455-464`). Its fallback href
`/projects` is **not a route** (`routes.tsx`, `App.tsx:42-75`), so
`App.tsx:71`'s `*` catch-all navigates to `/` — where the user already is.
Result: **a click that does absolutely nothing, with no error.**

| Call site | Verb on screen | Outcome |
|---|---|---|
| `web/src/desk/chair/ChairHome.tsx:542` | opening a Project from a Needs-You row | silent no-op |
| `web/src/desk/chair/ChairHome.tsx:555` | Coverage "repair" → the owning Project | silent no-op |
| `web/src/desk/chair/ChairHome.tsx:1323` | "Open" on a proposal | silent no-op |
| `web/src/desk/chair/ChairHome.tsx:1460-1466` | proposal "MORE ▸ Open" | silent no-op |
| `web/src/desk/components/SystemShade.tsx:450` | shade Coverage row → Project | silent no-op |
| `web/src/desk/components/SystemShade.tsx:586` | **shade PROJECTS section → open the Room** | silent no-op |
| `web/src/features/project-room/recall/RecallFace.tsx:84` | a decision card → its Project | silent no-op |
| `web/src/pages/cores/history/MeetingReview.tsx:272` | a meeting → its Project | silent no-op |

The working key is `open-project-memory` with scope `project:<id>` — used
correctly by only three call sites: `DeskToolShelf.tsx:253` (⌘K),
`PeopleCore.tsx:605`, `useDoorController.ts` (after Create Project).

**So: the Project Room — the centrepiece of phases 157-176 — is reachable
from exactly one discoverable place: pressing ⌘K and typing the project
name.** Every on-face route to it is broken.

Existing tests do not catch it because they assert the *call*, not the
result: `features/project-room/recall/__tests__/RecallFace.test.tsx:168`
asserts `openSurfaceOr` was called with `"project-room"`.

**Second scope-grammar break.** `ChairHome.tsx:1743` and `:1751` call
`openSurfaceOr("review-meetings", "/meetings", m.id)` — a bare id.
`HistoryCore.tsx:40` only accepts `scope.startsWith("meeting:")`. So
"Open" on a meeting from the arrival opens the Meetings window **with
nothing selected**. `desk/surface/citations.tsx:27` does it correctly, which
proves the grammar exists and was simply not followed.

### 2b. DEAD LINKS — manifest `href`s that resolve to nothing

`applications.ts` declares these hrefs; none is a route, all hit `*` → `/`:
`/ask` (`:98`), `/context` (`:209`), `/models` (`:287`, `:419`),
`/project-memory` (`:236` — note `PeopleCore.tsx:605` uses it as a
fallback), `/calendar-snapshot` (`:327`), `/components` (`:225`),
`/#processes` (`:341`), `/projects`. They are harmless only because
`openSurface` usually succeeds first — except where it doesn't (§2a).

### 2c. ORPHANS — faces nothing links to

| Face | File | Status |
|---|---|---|
| `/welcome` | `pages/WelcomePage.tsx` | no link anywhere; pure bookmark compatibility |
| `/presence` | `pages/PresencePage.tsx` | no link anywhere |
| **Components catalog** | `pages/cores/ComponentsCore.tsx` | no `group`, so absent from Go/⌘K; only `/design/components` |
| **Calendar snapshot review** | `pages/cores/CalendarSnapshotReviewCore.tsx` | no group, no route; only via drag-drop or one Settings button |
| **Context** | `ConstitutionalContextCore.tsx` | no caller anywhere except the Go menu |
| **Processes** | `ProcessCore.tsx` | no caller anywhere except the Go menu |
| **`SetupCore`** | `pages/cores/SetupCore.tsx` | **dead code** — referenced only by the `_parked` setup tree |
| **`ModelLibraryCore` + `CapabilityAssignmentsCore`** | `pages/cores/` | reachable only through Settings→Models→`FrontDoorView` "Advanced" toggle (`pages/cores/frontDoor.tsx:501-510`, `:581-590`); their manifest rows are commented out at `applications.ts:157-158` |
| **The whole parked setup Interview** | `features/project-room/_parked/setup/` (9 components incl. `JiraWizard`, `SuggestionCards`, `SetupInterview`) | superseded by the Door; still in the tree |
| **Parked chair lanes** | `desk/chair/_parked/` (`DoorBoardLane`, `AgentsLane`, `ThoughtEntry`) | dead |

### 2d. DEAD ENDS — faces with no way onward

| Face | Why it dead-ends |
|---|---|
| **The cold arrival** | On a fresh desk `ChairHome.tsx:855-1010` renders every section conditionally on `length > 0`. The face is a headline, "No brief yet / Generate", and a capture bar. No New Project verb, no "what next". |
| **Recall / Desk memory** | Its only onward verb (open the Project) is the broken `project-room` key. `RecallFace.tsx:84`. |
| **Presence page** | Only a `← Desk` anchor. |
| **Components catalog** | No verbs at all. |
| **`FallbackPullout`** for project/workbench/roadmap/repository/story | A detail panel with no detail and no verbs. |
| **Concierge with zero engines** | "No engine yet", `7 GROUPS · 7 WAITINGS`, `Use these` disabled. The only forward move is a 507 MB download. |

### 2e. MCP-only — capability with no face at all

The MCP sidecar exposes ~222 tools; several whole subsystems have **no
screen**:

| Subsystem | MCP tools | Face? |
|---|---|---|
| **Heartbeat** | `heartbeat_set`, `heartbeat_status`, `heartbeat_run_now`, `heartbeat_notify_test` | **None.** Grepping `web/src` for "heartbeat" finds only the audio-lease heartbeat in `lib/audioFloor.ts`. |
| **Watches, desk-level** | `watch_create`, `watch_list`, `watch_preview`, `watch_refresh`, `watch_set_enabled` | Only inside a Project Room ("SOURCES"/"CIRCUITS", `StewardPosture.tsx:369-401`), which is itself only ⌘K-reachable. The word "Watch" surfaces only in history labels (`ProjectRoomCore.tsx:230-233`). |
| **Practice recipes** | `practice_recipe_list/get/compile` | None. |
| **Zones** | `zone_file`, `zone_unfile`, `zone_list_members` | `ZoneWindow.tsx` + the floor zone right-click — spatial view only. |
| **Scheduled recording** | `scheduled_recording_*` | Create only (`ScheduleCreateWindow.tsx`); list/update/delete have no face. |
| **Monday brief** | `monday_brief_generate/get` | One "Generate" button on the arrival (`ChairHome.tsx:918`) and the Intelligence Brief view. |
| **Cadence run-now** | `cadence_run_now` | Per `docs/internal/OPERATIONAL-SURFACE-AUDIT.md:115`: "no face calls run-now". |

### 2f. Reconciliation with the HS-200 "dead-end" material

There is **no `docs/internal` document named for dead-end faces**. I
grepped `docs/` and `pm/roadmap/holdspeak/` for `dead.end`, `orphan face`,
`unreachable face`, `no way onward`. What exists:

1. **`pm/roadmap/holdspeak/phase-168-the-connections-door/assets/audit-today.md`**
   — a *click-path* dead-end audit (columns `Clicks · Seconds · Dead end?`)
   from Phase 168, pre-Door. Its headline finding (`:117-119`): *"The cold
   dead end is SILENT. The user answers both questions, sees 3 native cards
   with no GitHub or Jira option, and has no path forward to connect."*
   **Status: still true in shape.** The Door now shows `Connect` buttons
   (`DoorCore.tsx:87-118`) so it is no longer silent — but `Connect` leaves
   the Door for Settings (`useDoorController.ts:231`), which tells the user
   to run `gh auth login` in a terminal.
2. **`docs/internal/OPERATIONAL-SURFACE-AUDIT.md:100-120`** — the HS-200
   flow inventory. It names flow 7 (`Claim review on an update`)
   **UNREACHABLE — no route, tool or face** and flow 15
   (working-context promotion) *"fences live, verb unreachable"*.
   **Both confirmed.** It does **not** list the `project-room` break in
   §2a; that appears to be new and unrecorded.
3. `pm/roadmap/holdspeak/phase-200-the-working-practice/assets/settled-design-daily-workflow.md:975`
   — a single design note ("`Write it myself` must not be a dead end").

**Net: the audit trail covers click-paths and backend flows. Nobody has
audited the *surface-key graph*, which is where the worst break lives.**

---

## 3. Terminology the user meets on screen

Paths below are relative to `/Users/karol/dev/tools/HoldSpeak/web/src/`.
"Defined on screen?" means: could a newcomer work out the meaning from the
face alone, without docs.

### 3a. The nouns

| Noun | Representative on-screen citation | Meaning as the product uses it | Defined on screen? | Ambiguous |
|---|---|---|---|---|
| **Desk** | `desk/components/AttentionDrawer.tsx:95` | The whole operating surface; also a search scope; also a sync boundary | No | **YES ×3** — the app, the scope (`desk/applications.ts:286`), the device ("SAVED ON ANOTHER DESK", `desk/surface/patterns/TaskResume.tsx:194`) |
| **Floor** | `desk/components/window/Dock.tsx:191` | The spatial view where records are 3D objects | No | mild (also "Floor atmosphere", `desk/DeskApp.tsx:178`) |
| **Chair** | `desk/components/window/Dock.tsx:184` | The home/arrival view; a bare dock toggle opposite Floor | No | mild |
| **Arrival** | never rendered (classNames/testids only, `desk/chair/ChairHome.tsx:743`) | the home screen | **never on screen** | n/a |
| **Places / Atmosphere** | `desk/applications.ts:52-53`; `desk/gl/atmosphereRegistry.ts:20` | Ambient scene picker for the Floor | partly | **YES** — vs "room sound" (`pages/cores/settingsWallpaper.tsx:135`) and "Room" |
| **Room** | `features/project-room/useProjectRoomController.ts:21` | The home wing of a Project Room | No | **YES ×4** — wing "Room" / "Meeting room" (`desk/applications.ts:182`) / "ROOM NAMES" (`pages/cores/CadenceCore.tsx:105`) / "ARM ROOM MEETINGS ONLY" (`pages/cores/SettingsCore.tsx:1657`) |
| **Door** | `desk/chair/ChairHome.tsx:225` (emblem "DOOR") | The source-watch intake; also the New Project screen | **No — and the screen is titled "New Project"** (`desk/applications.ts:327-336`) | **YES** — the word only reaches the user as an unexplained emblem |
| **Watch** | `features/project-room/door/DoorCore.tsx:400` ("N WATCHES") | A Project-scoped source observer | No | **YES** — the *same records* render as "CIRCUITS"/"SOURCE" under Steward (`features/project-room/steward/StewardPosture.tsx:397-399`); plus the verb-state "Watching" in `pages/cores/ActivityCore.tsx:98`, `pages/cores/ProcessCore.tsx:138` |
| **Circuit** | `features/project-room/steward/StewardPosture.tsx:395` | Breaker state of a repeatedly failing Watch | No | **YES** — renames Watch mid-product |
| **Steward** | `features/project-room/steward/StewardPosture.tsx:441` | The Project component that evaluates work under policy | No | No |
| **Nudge** | `StewardPosture.tsx:539` | The message a Steward emits | No | **YES** — vs "Activity nudges" in dictation (`pages/cores/dictation/DictationSections.tsx:130`), unrelated |
| **Proposal / Review** | `features/project-room/review/ReviewPosture.tsx:633` | A candidate action awaiting judgment | No | **YES** — also the Concierge "proposed set" (`desk/applications.ts:305`), also "MeetingReview", also "Accept review" on Thoughts |
| **Project** | `lib/primitives.ts:490` | A body of work with meetings, decisions, memory | **blurb exists at `:493` and is never rendered** | No |
| **Update / Delta** | `features/project-room/update/UpdatePosture.tsx:426` | A published Project status post | No | **YES** — vs "Update context" verb (`desk/pullouts/NotePullout.tsx:382`). "Delta" is **never on screen** (only the emblem "D", `ChairHome.tsx:213`) |
| **Meeting / Aftercare / Transcript** | `desk/applications.ts:108`; `desk/components/AttentionDrawer.tsx:147` | Captured conversation; post-meeting follow-up | No | "Aftercare" is undefined jargon |
| **Note / Thought / Thread** | `lib/primitives.ts:445, 623`; `desk/thought-workspace/ThoughtWorkspaceWindow.tsx:470` | Text you write; a Note under development; a persistent chat | blurbs never rendered | **YES** — "Note" vs "Grounding note" vs "Satisfaction note" (`pages/cores/PeopleCore.tsx:606, 717`) |
| **Decision / Receipt** | `desk/pullouts/DecisionPullout.tsx:96-97`; `desk/components/ReceiptLine.tsx:24` | A recorded decision; a durable record of what ran | No | **YES** — the Intelligence segment labelled **"Decisions" renders receipts** (`desk/pullouts/IntelligencePullout.tsx:16`: `{ id: "receipts", label: "Decisions" }`) |
| **Intelligence** | `desk/applications.ts:68` | The desk-wide brief/follow-through/receipts view | description at `:69` | **YES** — also a per-meeting post-processing run ("Auto-run intelligence", `pages/cores/SettingsCore.tsx:1472`) |
| **Brief** | `desk/pullouts/IntelligencePullout.tsx:14`; `ChairHome.tsx:915` | The generated daily digest | No | **YES ×4** — arrival brief / Rhythm brief (`applications.ts:194`) / "Preparation brief" (`features/project-room/prepare/PreparePosture.tsx:62`) / "Draft the brief" (`:682`) |
| **Follow-through** | `desk/pullouts/IntelligencePullout.tsx:15` | Board of what you owe and are owed | No | **YES** — used as the eyebrow for *both* Rhythm (`applications.ts:199`) and People (`:384`) |
| **Commitment** | `pages/cores/PeopleCore.tsx:697` ("You owe") | A promise tracked against a person | No | mild |
| **Assignment** | `desk/components/WorkbenchWindow.tsx:395` vs `features/project-room/RoomPeopleSection.tsx:125-126` | Which model runs a capability — **or** a task a person owes | No | **YES, worst class** — two unrelated meanings, both visible |
| **Runs on / Model / Engine / Capability** | `WorkbenchWindow.tsx:393`; `desk/applications.ts:304`; `DeskToolInspector.tsx:318`; `lib/primitives.ts:697` | Four names for "where inference happens" | No | **YES** — "Engine" is never distinguished from "Model" on screen |
| **Models** | `desk/applications.ts:304`, `:412`; `pages/cores/settingsPrefs.tsx:54`; `pages/cores/ModelLibraryCore.tsx:423` | **Three different screens carry this name** | partly | **YES, worst class** |
| **Concierge** | — | the model setup flow | **never on screen** (the window is titled "Models") | n/a |
| **Provider / Connection / Integration** | `ModelLibraryCore.tsx:323`; `desk/applications.ts:421`; `DeskToolInspector.tsx:246` | One idea, three words | partly | **YES** — and `docs/product-language.json` canonicalizes `connector → integration`, which the screen never says |
| **Hub / Egress** | `desk/components/DeliveryBoard.tsx:414`; `pages/cores/TopologyMapView.tsx:453` | The runtime host; data leaving the device | Egress: yes, via chip title | mild |
| **Grounding** | `desk/components/AskPanel.tsx:492` vs `pages/cores/PeopleCore.tsx:606` | Source records fed as context — **or** free text about a person | No | **YES** |
| **Knowledge / Zone** | `desk/verbRegistry.ts:161, 205` | A grounding collection; a findable Desk placement | No | mild ("No Knowledge" as a null option reads as a judgment, `desk/pullouts/editors/RecipeEditor.tsx:94`) |
| **Agent / Recipe / Persona / Mode** | `desk/applications.ts:128`; `desk/tools.ts:44` (`recipe → "Agent"`); `desk/pullouts/RecipePullout.tsx:2` ("Recipe (Persona)"); `desk/components/ModeTabs.tsx` | **One object, four names.** A thread's "mode" *is* a recipe id (`desk/pullouts/ThreadPullout.tsx:1778-1780`) | description at `:130` | **YES** — and "Agents" the app lists both personas and live sessions |
| **Workflow / Sequence / Chain** | `desk/verbRegistry.ts:183`; `lib/primitives.ts:521`; `desk/pullouts/ChainPullout.tsx:46` ("Edit chain") | Saved multi-step behaviour | No | **YES** — `docs/product-language.json` maps `chain → sequence` and `lib/productLanguage.ts:47` enforces it, yet `ChainPullout.tsx:46` still ships "Edit chain"; `desk/tools.ts:45-47` maps *both* `chain` and `workflow` to the label "Workflow" |
| **Workbench** | `desk/applications.ts:234` | Scheduled agent work unit | description at `:235` | **YES** — "Send to Workbench" as a People delegation target (`PeopleCore.tsx:717`), and the unrelated external "Delivery Workbench" naming in `lib/primitives.ts:571` |
| **Automation** | `desk/components/WorkbenchAutomations.tsx:195` vs `pages/cores/dictation/DictationSections.tsx:66` | Trigger-started work — **or** dictation hooks | No | **YES**, unrelated |
| **Cadence / Rhythm / Sweep / Loop** | `pages/cores/SettingsCore.tsx:1764`; `desk/applications.ts:193`; `pages/cores/CadenceCore.tsx:100, 609` | The unresolved-work review system | No | **YES, worst class** — "Cadence" is both the system and a plain frequency (`StewardPosture.tsx:490`, `PeopleCore.tsx:739`); Rhythm's own description is *"Sweep, brief, and notification **cadence**"*; "Loop" appears for the first and only time on a destructive verb, "Kill loop" |
| **Heartbeat** | — | the unattended sweep | **never on screen** | n/a |
| **Speak / Dictation / Journal / Blocks / Learned / Utterance** | `desk/applications.ts:78`; `pages/cores/DictationCore.tsx:40-43`; `pages/cores/dictation/SpeakFace.tsx:320` | The voice-typing app and its four wings | No | **YES** — the app is "Speak" but every internal label says "Dictation"; **"Blocks" is a bare wing label with zero explanation**; "Utterance" is a bare field label next to placeholder "Talk, or type here" |
| **Ask / Lens** | `desk/applications.ts:99`; `desk/components/AskPanel.tsx:463` | Cross-desk question surface; its scoping selector | description at `:100`; **Lens: none** | **YES** — "Ask AI" app vs "ASK" button vs "Ask this project" (`ProjectRoomCore.tsx:1662`). **"Lens" is a one-word label with no definition anywhere in the product** |
| **Context / Constitutional context** | `desk/applications.ts:217`; `desk/pullouts/NotePullout.tsx:372`; `pages/cores/ConstitutionalContextCore.tsx:171` | The always-on agent briefing | description at `:218` | **YES, worst class — five senses**: the Context app, "AI context" on a Note, "Constitutional context", "Decision context" (`DecisionPullout.tsx:96`), "Role context" (`PeopleCore.tsx:739`). `docs/product-language.json` lists `Context` as a **guarded term** |
| **Memory / Desk memory** | `desk/applications.ts:285`; `desk/components/DeskChrome.tsx:49` | Search over connected evidence | description at `:286` | **YES — two different faces share the name.** The bell/shade is titled "Desk memory" (`DeskChrome.tsx:44-49`) *and* the `open-project-memory` window is titled "Desk memory" (`applications.ts:285`). Plus "Meeting memory" (`:117`), "Long memory" (`:291`), a Workbench "Memory" tab (`WorkbenchWindow.tsx:1433`), "Filter the memory" (`RecallFace.tsx:413`) |
| **Interview** | `desk/components/InterviewPanel.tsx:52`; `ThoughtWorkspaceWindow.tsx:414` | Question-driven context extraction | No | **YES** — a Thread mode and a Thought-Workbench pane, plus a third parked one |
| **Coverage** | `ChairHome.tsx:831`, `:293` ("Coverage incomplete") | How much of your sources the arrival could actually read | **No — a bare section token** | **YES** — and it is the *headline* of the arrival when incomplete |
| **Manifest** | `PreparePosture.tsx:549, 651, 683` | The frozen source list bound to a brief | No | **YES** — "MANIFEST MISMATCH" is a failure state the user cannot interpret |
| **Posture** | `pages/cores/settingsPrefs.tsx:564-566` | Authority preset (Secure/Normal/YOLO) | No | **YES** — glossary calls it "Control mode" |
| **Dossier / Conveyor / Mission control** | `DeliveryBoard.tsx:442`; `MissionControlConveyor.tsx`; `applications.ts:235` | Delivery-pipeline furniture | No | "Dossier" is only ever lowercase inside a tooltip; "Conveyor" and "Mission control" **never appear as a title** |
| **Roadmap / Story / Repository** | `lib/primitives.ts:568, 579, 501`; group "Delivery" `:700` | Delivery Workbench objects leaking into the product | No | **YES** — "Story" shares nothing with the rest of the vocabulary |
| **Companion** | `desk/applications.ts:138` (eyebrow over the Agents window) | — | **No** | **YES** — a one-off word for the Agents app |
| **Kernel** | `desk/applications.ts:345` | what runs processes | No | introduced once, used nowhere else |

### 3b. Glossary reconciliation

**On screen, absent from `docs/GLOSSARY.md`:** Circuit · Nudge · Aftercare ·
Coverage · Manifest · Lens · Blocks · Utterance · Companion · Dossier ·
Posture · Story/Roadmap/Delivery · Mission control · Assignments ·
Provider · Connections · Runs on · Follow-through · Needs you · Update ·
Evidence · Constitutional context · Kernel · "Meeting memory" · "Long memory".

**In the glossary, never on screen:** arrival · **Concierge** ·
**Heartbeat** · Reach · Resourceful · Everyday context · Project Room (the
screen says only "Room") · Control mode · sidecar · MCP · Project facts ·
Project context.

**Direct contradictions (glossary/`product-language.json` vs the code):**

| # | Canon says | Screen says | Cite |
|---|---|---|---|
| 1 | "Concierge — the model setup window" | **"Models"**, and two other screens are also "Models" | `desk/applications.ts:304, 411-413`, `settingsPrefs.tsx:54` |
| 2 | "Everyday context" | "Constitutional context" / app titled "Context" | `ConstitutionalContextCore.tsx:171`, `applications.ts:217` |
| 3 | "Control mode" | "Control posture" / "Posture" | `settingsPrefs.tsx:564-566` |
| 4 | `connector → integration` | "Connections" and "Provider" | `applications.ts:421`, `ModelLibraryCore.tsx:323` |
| 5 | `chain → sequence` (enforced by `lib/productLanguage.ts:47`) | **"Edit chain"** — a live violation of the app's own registry | `desk/pullouts/ChainPullout.tsx:46` |
| 6 | "Watch — a Project-scoped source observer" | "CIRCUITS" / "SOURCE" | `StewardPosture.tsx:397-399` |
| 7 | "Receipt — an execution record" | tab labelled **"Decisions"** | `IntelligencePullout.tsx:16` |
| 8 | "Project Room" | "Room", colliding with three other Rooms | `useProjectRoomController.ts:21` |
| 9 | `Context` is a **guarded term** | shipped as an app label + four compounds | `applications.ts:217` |
| 10 | Every primitive in `lib/primitives.ts` carries a `blurb` — the only place any object kind is *defined* | **no `.tsx` file reads `blurb`.** Every definition in that table is dead copy | `lib/primitives.ts` |

---

## 4. Onboarding: what a brand-new user sees

### 4a. The gate

`holdspeak/setup_status.py:291` — `"arrival_required": first_run and
onboarding["disposition"] is None`. When true, `DeskApp.tsx:123` unmounts
**almost the entire product**: menu bar (`:185`), Ask panel (`:204`),
inline editor (`:209`), pullouts (`:215`), tool inspector, Mission Control,
Delivery board, roadmap/repo/workbench windows, pane picker, session
pullout, attention drawer, Trust window, **the Dock (`:257`)**, snap ghost,
Exposé, Switcher. Only `SurfaceWindows` survives, in
`firstValueRecoveryOnly` mode (`:252-255`).

`ChairHome.tsx:369-378` then short-circuits to a bare page containing one
component: `FirstWords`.

### 4b. Minute by minute

| Time | What happens | File |
|---|---|---|
| 0:00 | Whole product unmounted; one card renders | `DeskApp.tsx:185-260` |
| 0:05 | **"Dictate one sentence"** / "Tap to speak, edit here, then use" / one button **"Click to speak"** / textarea / greyed Copy · Keep as Note · Continue later | `FirstWords.tsx:353-396, 438-477` |
| 0:20 | Speak or type → Copy/Keep light up from text alone | `firstValueCold.test.tsx:104-113` |
| 0:40 | **Keep as Note** → note "First dictation" created; **`POST /api/desk/seed` fires unconditionally** (21 objects appear, unasked); `PUT /api/setup/onboarding` retires arrival forever | `FirstWords.tsx:205-241, 280-323` |
| 1:00 | Arrival appears: headline **"Nothing needs you"**, `BRIEF / No brief yet / [Generate]`, capture bar, ~550px of empty black | `ChairHome.tsx:744, 911-928, 2055-2095` |
| 1:30 | They press **Generate** — the only non-capture verb — against an empty DB with no model | `ChairHome.tsx:918-926` |
| 2:30 | They press **Develop a thought** → Thought Workbench → **"AI needs a model / Set up AI"** | `ThoughtWorkspaceWindow.tsx:418` |
| 3:30 | Concierge: **"No engine yet"**, `7 GROUPS · 7 WAITINGS`, seven empty dropdowns, `Use these` disabled, one 507 MB download offered | shot `phase-170.../story-03-shots/build-cold-1440.png` |
| 6:00 | Hunting for the product. **New Project is not on the arrival** — `desk.new-project` is `scope: "floor"` (`verbRegistry.ts:231-241`), so it lives in the menu-bar Desk menu only |
| 7:00 | The Door: one field "What are you delivering?", `SOURCES` = `GitHub ⚠ SIGN IN [Connect]`, `Jira ⚠ SIGN IN [Connect]`, footer `NO SOURCES · BLANK PROJECT`, greyed `Create Project` | `DoorCore.tsx:383-466`; shot `phase-169.../story-02-shots/door-cold-1440.png` |
| 7:30 | **Connect** abandons the Door for Settings→Connections, which shows a terminal command box reading **`gh auth login`** | `useDoorController.ts:231, 491-496`; shot `phase-168.../story-01-shots/ConnectionsCold.png` |
| 9:00 | They create a blank Project. The Room opens: **"Nothing needs you"** in the headline *and* in the NEEDS YOU section, no sources, composer carrying **`MODEL · NOT SET`** | `ProjectRoomCore.tsx:1690`; shot `phase-169.../story-03-shots/room-quiet-1440.png` |
| 10:00 | Net: one note, a seeded desk they never asked for, an empty Project, two unfinished setup errands neither of which was named on the arrival | |

### 4c. What "first value" means in code

Purely instrumentation, not product state. `desk/firstValue.ts:4-13`
defines nine events posted to `/api/setup/first-value/*`. `finish("success")`
fires **only when a real transcript came back from the mic**
(`FirstWords.tsx:277, 301-304`). A user who **types** their sentence gets
the note, gets the message *"Kept as a note. Continue later when you are
ready for your Desk."*, and is never counted a success — even though
`firstValueCold.test.tsx:137-149` deliberately supports the no-mic path.

### 4d. The Interview — three different things, one name

| Thing | File | Status |
|---|---|---|
| **Thread Interview** | `desk/components/InterviewPanel.tsx`, rendered at `ThreadPullout.tsx:1771-1773` | live, but only when the server hands back `thread.interview`. The panel asks nothing itself: it is a Section `<Select>`, a `Context · N ideas` toggle, `Explore`, and suggestion cards (`Try draft` / `Keep idea` / `Later` / `Dismiss`). The questions live server-side. |
| **Project-setup Interview** | `features/project-room/_parked/setup/SetupInterview.tsx` | **PARKED**, replaced by the Door (`applications.ts:299`) |
| **Thought Workbench Interview** | `desk/thought-workspace/ThoughtWorkspaceWindow.tsx:404-420` | live; hard-gated on a model |

`docs/INTERVIEW.md` documents nine sections (Goals, Projects, What matters,
Cadences, People, Decision log, Delegation, Sources & models) and opens
with *"Configure a suitable model through Settings > Models."* — i.e. the
documented onboarding path is unreachable on a fresh install.

### 4e. Shots viewed

| Shot | What it shows |
|---|---|
| `pm/roadmap/holdspeak/phase-169-the-streamlined-door/assets/story-02-shots/door-cold-1440.png` | the Door, cold |
| `pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-15-shots/quiet-all-clear-1440.png` | the arrival, quiet — 550px of black |
| `pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-16-shots/day1-attention-1440.png` | the arrival working, with real data |
| `pm/roadmap/holdspeak/phase-169-the-streamlined-door/assets/story-03-shots/room-quiet-1440.png` | a Project Room, fresh |
| `pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-05-shots/walk-settings-hub-1440.png` | Settings hub |
| `pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-01-shots/ConnectionsCold.png` | Settings → Connections, cold |
| `pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-03-shots/build-cold-1440.png` | Concierge/Models, cold |
| `pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-04-shots/build-speak-unset-1440.png` | Speak, dictation unset |
| `pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-41-shots/composer-send-refused-1440.png` | thread mode tabs incl. INTERVIEW |
| `pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/desk-1440.png` | the desk census face |

---

## 5. Usability verdict — why a capable newcomer cannot run this

Ranked by how much each one blocks understanding. Every item is a specific
file, not an impression.

---

**1. Every on-face route into the Project Room is broken.**
`"project-room"` is not a registered surface and `/projects` is not a
route, so eight call sites are silent no-ops:
`desk/chair/ChairHome.tsx:542, 555, 1323, 1460`,
`desk/components/SystemShade.tsx:450, 586`,
`features/project-room/recall/RecallFace.tsx:84`,
`pages/cores/history/MeetingReview.tsx:272`. The Project Room — the
centrepiece of ten phases — is reachable from **exactly one discoverable
place**: press ⌘K and type the project name
(`desk/components/DeskToolShelf.tsx:253`). A user who clicks "Open" on
their own project and sees nothing happen concludes the product is broken,
and they are right.

**2. There is no navigation.** Five dock icons
(`desk/components/window/Dock.tsx:110`) plus four menu-bar words
(`desk/components/DeskMenuBar.tsx:24-29`). The only complete index of the
22 applications is the **⌘K command deck**
(`desk/components/DeskToolShelf.tsx:39-46`) — an invisible keystroke with
no on-screen affordance except a small "Search ⌘K" chip. Nine surfaces
(People, Context, Processes, Calendar snapshot, Components, Live meeting,
Concierge, Change places, New Project) are not on the dock at all.

**3. "Models" names three different screens, and "Model / Engine / Runs on
/ Assignment / Capability" name one decision.** The Concierge window
(`desk/applications.ts:411-413`), the Settings Models module
(`pages/cores/settingsPrefs.tsx:54` → `settingsModels.tsx:8` →
`frontDoor.tsx` → `ModelLibraryCore` + `CapabilityAssignmentsCore`), and
the Model Library screen itself (`pages/cores/ModelLibraryCore.tsx:423`).
A user who gets "MODEL · NOT SET" (`ProjectRoomCore.tsx:1690`) and goes to
"Models" may land on any of the three depending on which door they used.

**4. The cold arrival is a dead end that names nothing the product does.**
`desk/chair/ChairHome.tsx:855-1010` — every section is
`length > 0 ? … : null`. On a fresh desk the entire face is a headline, a
"No brief yet / Generate" row, and four capture verbs, over ~550px of
empty black (shot: `phase-200.../story-15-shots/quiet-all-clear-1440.png`).
No Project, no Watch, no Room, no next step. The one prominent verb —
**Generate** (`ChairHome.tsx:918-926`) — runs a brief against an empty
database with no model and no readiness check.

**5. "New Project" is floor-scoped, so it is invisible from the home
screen.** `desk/verbRegistry.ts:231-241` declares `desk.new-project` with
`scope: "floor"`; `desk/components/DeskCreateMenu.tsx:36` filters on that
scope; `DeskStartActions` is mounted only by `EmptyDesk.tsx`, which
`DeskApp.tsx:186` renders only when `showFloor`. The default surface is
the Chair (`desk/chairState.ts`). **The verb that creates the product's
central object cannot be seen from the product's default screen.**

**6. The model prerequisite is discovered four separate times, never
announced once.** `ThoughtWorkspaceWindow.tsx:418` ("AI needs a model"),
`ProjectRoomCore.tsx:1690` (`MODEL · NOT SET`), `ThreadPullout.tsx:21`
(`NO MODEL`), `desk/pullouts/shared/CapabilitySection.tsx:76` ("No model
configured"). Nothing on the arrival says "you have no model". When the
user finally reaches the Concierge they get `7 GROUPS · 7 WAITINGS`,
seven empty dropdowns and a disabled `Use these` (shot:
`phase-170.../story-03-shots/build-cold-1440.png`).

**7. First launch seeds 21 objects into the user's database without
asking, and the deliberate Seed verb is unreachable.**
`desk/components/FirstWords.tsx:212` posts `/api/desk/seed`
**unconditionally** on every exit — including "Continue later" with an
empty textarea. The explicit `▤ Seed the desk` button that should own this
act (`desk/components/EmptyDesk.tsx:48-62`) only renders on the Floor,
which `DeskApp.tsx:129` forces off during arrival. The user never sees a
prompt, a receipt, or an undo.

**8. "Context" has five meanings and "Cadence" has two, on screens the
same user visits in one session.** Context: the app
(`desk/applications.ts:217`), "AI context" on a Note
(`NotePullout.tsx:372`), "Constitutional context"
(`ConstitutionalContextCore.tsx:171`), "Decision context"
(`DecisionPullout.tsx:96`), "Role context" (`PeopleCore.tsx:739`) —
and `docs/product-language.json` already flags `Context` as a guarded
term. Cadence: the review system (`SettingsCore.tsx:1764`) and a plain
frequency (`StewardPosture.tsx:490`), while the Settings module named
**Rhythm** defines itself as *"Sweep, brief, and notification cadence"*
(`desk/applications.ts:194`).

**9. One window, "Desk memory", is six different faces — and the name is
already taken by the notification bell.**
`pages/cores/ProjectMemoryCore.tsx:5-9` re-exports `ProjectRoomCore`;
`ProjectRoomCore.tsx:1869-1965` then routes to Recall / Review / Update /
Steward / Prepare / Room depending on scope and server state, with a
runtime title override (`:1899`). Meanwhile the attention bell is *also*
labelled "Desk memory" (`DeskChrome.tsx:44-49`). A user clicking the same
menu entry twice can get two structurally different screens and never
know why.

**10. Whole subsystems have MCP tools and no face at all.** Heartbeat
(`heartbeat_set/status/run_now` — zero occurrences in `web/src` outside an
unrelated audio lease in `lib/audioFloor.ts`). Desk-level watches
(`watch_create/list/preview/refresh` — the only Watch UI is inside a
Project Room, itself ⌘K-only). Practice recipes. Scheduled-recording
list/update/delete (only create has a face,
`desk/components/ScheduleCreateWindow.tsx`).
`docs/internal/OPERATIONAL-SURFACE-AUDIT.md:115` states plainly that no
face calls cadence `run-now`, and `:107, :110, :118` that claim review and
working-context promotion are unreachable. The product's own audit says
6 of 15 core flows are driveable without a browser — which means the
browser is not where the product lives, but it is the only place the user
is.

---

### Honourable mentions (11-15)

11. **Seven of twenty primitive kinds fall through to `FallbackPullout`**
    (`desk/pullouts/registry.ts:43-48`) — project, repository, roadmap,
    story, workbench, game, layout. Clicking a Project object gives you a
    panel with no content and no verbs.
12. **`lib/primitives.ts` carries a `blurb` for every object kind — the
    only place in the product where any noun is defined — and no `.tsx`
    file reads it.** The definitions exist and are dead.
13. **Typing is second-class.** `FirstWords.tsx:277, 301-304` — a
    first-value attempt only `finish("success")`es if a real mic
    transcript arrived, even though `firstValueCold.test.tsx:137-149`
    deliberately supports the typed path. The success metric
    under-reports.
14. **`Connect` abandons the Door.** `useDoorController.ts:231, 491-496`
    opens Settings on `integrations`, where the instruction is to run
    **`gh auth login` in a terminal** (shot:
    `phase-168.../story-01-shots/ConnectionsCold.png`). A shell
    round-trip inside a first-run flow.
15. **Dev surfaces ship to users.** `/design/components` renders the
    Signal catalog with internal section titles ("Wings and the fold",
    "The ledger walks" — `pages/cores/ComponentsCore.tsx:206, 238`), and
    `RAILS` / Delivery / Roadmap / Story are Delivery-Workbench objects
    from a different product living in the same desk
    (`lib/primitives.ts:568-579`).

---

### The one-line diagnosis

The owner's sentence — *"we've added a shit-ton of things but I still fail
to understand most of it from a usability perspective"* — is not a
perception problem. **The product has 22 applications and 5 nav entries;
its central object is reachable only by an invisible keystroke because
every visible route to it is a no-op; its central prerequisite (a model)
is announced by four different faces and never by the home screen; and the
same word names three different screens in the place where you go to fix
that prerequisite.** None of that is discoverable from the faces, because
it is not *there*.

