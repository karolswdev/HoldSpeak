# Audit B -- Front-Door Live Walk

Auditor: Claude (opus-4-6[1m])
Date: 2026-08-27
Branch: main @ ab79c702
Method: Real hub under isolated HOME, Playwright headless, 1440x900 + 393x852

---

## 1. LIVE WALK

### 1a. Fresh-open experience (first-ever boot)

A brand-new HOME triggers `arrival_required=true`. The entire viewport is
owned by **FirstWords** (Phase 140 first-value flow): a centred card titled
"VOICE TYPING / Dictate one sentence" with a Click-to-speak button, an
editable textarea, and three exit verbs: Copy, Keep as Note, Continue later.

**No DeskChrome, no Dock, no lanes are visible.** The chrome and all
desk-floor content are gated behind `!arrivalRequired` checks at
`web/src/desk/DeskApp.tsx:137-196`. Only `SurfaceWindows` renders in
`firstValueRecoveryOnly` mode (line 188-191), registering only the Setup
surface for recovery.

**Click-depth from first open to any pillar: unreachable.** The owner must
complete or dismiss the first-value flow before seeing any content.

Screenshots: `first-value-capture-1440.png`, `first-value-capture-393.png`

### 1b. Seeded Chair (after first-value dismissal)

After dismissing first-value (API: `POST /api/desk/seed` + `PUT
/api/setup/onboarding` with `disposition: dismissed`), the Chair renders.

**The Chair at 1440px shows (top to bottom):**

1. **Hero slot**: ThoughtEntry -- "Develop a thought" amber button +
   "More capture options" row.
2. **BRIEF lane** (2 rows): headline "2 things waiting", per-section
   counts (Changed 00, Broke 00, Waiting 02, Decisions 00), two items with
   Ack/Defer verbs.
3. **FOLLOW-THROUGH lane** (2 rows): "Land the write-receipt channel"
   (K, overdue 6d) and "Photograph the placement dial states" (K, 3d),
   each with check/dismiss verbs.
4. **MEETINGS lane** (1 row): "Phase 132 desk review" (AUG 25, 4 action,
   OFF badge). No scheduled-recording rows visible (the seeded hub had no
   enabled schedules).
5. **AGENTS lane** (1 row): "/Users/karol/dev/tools/HoldSpeak" with
   BLOCKED badge + Answer button.

**At 393px**, all four lanes render vertically in the same order. The
menubar collapses to "HoldSpeak" mark + egress badge + Search + clock;
the Go/Desk/Object/Window menus are NOT visible (hidden via CSS). The
Dock shows Intelligence (with badge "1"), Speak, and Meetings; remaining
entries scroll or are cut off.

Screenshots: `chair-home-1440.png`, `chair-home-393.png`,
`lane-brief-content-1440.png`, `lane-follow-through-content-1440.png`,
`lane-meetings-content-1440.png`, `lane-agents-content-1440.png`

### 1c. Navigation surfaces reachable from the opening surface

**DeskChrome menubar** (1440px only): HoldSpeak mark, Desk, Object, Go,
Window menus, hub-dot, egress badge, Search (Cmd+K), clock.

**HoldSpeak mark menu** entries: List view, Arrange desk (ghosted),
Refresh from hub, Speak (Cmd+1), Meetings (Cmd+2), Agents and coder
sessions (Cmd+3), Settings (Cmd+4).
Screenshot: `mark-menu-open-1440.png`

**Go menu**: rendered but 0 items captured by the walker's selector
(entries use the WorkMenu portal; visually present on the screenshot as
the Go button is highlighted). Items confirmed present via the Cmd+K
shelf below.

**Cmd+K shelf** (1440px): VERBS section (New Note, New Decision, New
Knowledge, New Agent, New Workflow, New Workbench), PROGRAMS section
(Speak Cmd+1, Ask AI Cmd+I, Meetings Cmd+2, Settings Cmd+4, Workbenches,
Agents and coder sessions Cmd+3, Runs on, Integrations, Commands,
Cadence, Context, Activity, Processes, Delivery [DRAWER], Panes
[DRAWER]), SETTINGS section (Voice, Sounds & Presence, Meetings, Rhythm,
Models, Assignments).
Screenshot: `shelf-open-1440.png`

**Dock** (bottom bar, 1440px): Intelligence (badge 1), Speak, Meetings,
Agents, Settings, Floor, Desk memory, Delivery, Panes, Record-a-meeting
orb (10 buttons total).
Screenshot: `dock-overview-1440.png`

### 1d. Pillar click-depths

| Pillar | Today's click-depth from Chair | Path |
|--------|-------------------------------|------|
| Task/commitment list (Follow-Through board) | **1 click** (lane header "02" badge) opens Intelligence pullout on FOLLOW-THROUGH tab | Chair lane header -> Intelligence |
| Brief / Monday Brief | **1 click** (lane header "02" badge) opens Intelligence pullout on BRIEF tab | Chair lane header -> Intelligence |
| Meetings list | **0 clicks** (visible on Chair as MEETINGS lane). Full surface = **1 click** via Dock "Meetings" or Cmd+2 | Chair -> Dock/Cmd+2 |
| Scheduled recordings | **1+ clicks**: appear as SCHEDULED-badged rows in the MEETINGS lane when enabled. Create = not reachable from Chair without opening Cadence surface (2 clicks: Dock or Cmd+K -> Cadence) | Dock/Cmd+K -> Cadence |
| Intelligence (all three wings) | **1 click** via Dock "Intelligence" button (badge shows overdue count) | Dock -> Intelligence |

Screenshots: `intelligence-brief-1440.png`, `intelligence-followthrough-1440.png`

### 1e. Intelligence pullout

Opens as a right-side drawer over the Chair (not a surface window). Three
tabs: BRIEF, FOLLOW-THROUGH, DECISIONS. The Brief tab shows
Changed/Broke/Waiting/Decisions with expandable sections and
Acknowledge/Defer/Speak footer verbs. The Follow-Through tab shows
NOW/WAITING/UNASSIGNED/OVERDUE lanes with owner initials and due dates.

### 1f. Settings / Models / Assignments (Phase 143 precedent)

Settings opens as a surface window showing 8 module tiles: Voice, Sounds
& Presence, Meetings, Rhythm, Models, Assignments, Integrations, System.
POSTURE toggle shows YOLO. The `/profiles` deep link resolves via
`SURFACE_ALIASES` at `SurfaceWindows.tsx:298` to
`configure-settings` scoped to `models`, which opens Settings focused on
the Model Library.

Screenshots: `settings-home-1440.png`, `settings-models-1440.png`

---

## 2. ROUTING CENSUS

### 2a. How top-level surfaces mount

**Three real routes** at `web/src/routes.tsx:20-29`:
- `/` -> `Desk` (DeskApp) -- immersive
- `/welcome` -> `Welcome` (WelcomePage) -- immersive
- `/presence` -> `Presence` (PresencePage) -- immersive

**Demoted routes** at `web/src/routes.tsx:41-76`: all other paths (16
total) redirect to `/` and queue a `SurfaceWindows` open via
`openSurfaceWhenReady()`.

**What `/` resolves to**: `DeskApp` (`web/src/desk/DeskApp.tsx:43`). At
line 76, `useChairState` picks `surface` (default: "chair" at
`chairState.ts:16`). If `arrivalRequired` is true, `ChairHome` renders
`FirstWords` (line 148-149 via `ChairHome.tsx:46-53`). Otherwise the
Chair renders the four-lane layout.

### 2b. Surface windows (the window registry)

`SurfaceWindows.tsx:37-238` defines the `SURFACES` array: 15 surface
windows, each with a key, id, title, glyph, eyebrow, minW, and a lazy
Core component. Adding a new surface = one row in this array.

Current surfaces (file:line for each entry):
| Key | Title | SurfaceWindows.tsx line |
|-----|-------|----------------------|
| `dictate` | Speak | 38-50 |
| `review-meetings` | Meetings | 51-63 |
| `record-live` | Live meeting | 64-76 |
| `configure-settings` | Settings | 77-90 |
| `configure-cadence` | Cadence | 91-103 |
| `configure-setup` | Setup | 104-116 |
| `open-constitutional-context` | Context | 117-130 |
| `open-workbenches` | Workbenches | 131-144 |
| `inspect-personas-and-coders` | Agents | 145-159 |
| `design-components` | Components | 160-172 |
| `inspect-activity` | Activity | 173-185 |
| `open-project-memory` | Project memory | 186-198 |
| `inspect-processes` | Processes | 199-211 |
| `configure-commands` | Commands | 212-224 |
| `open-people` | People | 225-237 |

**Surface aliases** at `SurfaceWindows.tsx:290-302`: `configure-integrations`
-> Settings (scoped to integration:destinations), `configure-integration`
-> Settings, `configure-runs-on` -> Settings (scoped to models),
`read-runtime-docs` -> Settings (scoped to guide).

### 2c. How Phase 143 added Models/Assignments as peers

Phase 143 did NOT add new surface windows. Instead it added two modules
inside the existing Settings surface:

1. `settingsPrefs.tsx:39` -- `{ id: "models", label: "Models", ... }`
2. `settingsPrefs.tsx:41` -- `{ id: "assignments", label: "Assignments", ... }`
3. `SettingsCore.tsx:899-905` -- `case "models"` renders `ModelsModule`;
   `case "assignments"` renders `CapabilityAssignmentsCore`.
4. `SurfaceWindows.tsx:298` -- alias `configure-runs-on` scopes Settings
   to "models".

The pattern for Phase 143: add a module tile to `PREF_MODULES`, a switch
case in `SettingsCore`, and optionally a `SURFACE_ALIASES` entry for deep
linking. This is the intra-window pattern. For a wholly new surface
window (like the Dashboard Door), the pattern is a `SURFACES` row +
optional `DEMOTED_ROUTES` entry.

### 2d. Chair lane registration

Lanes plug in at `web/src/desk/chair/lanes/index.ts:12-17`:
`LANE_COMPONENTS` maps lane IDs to components. The lane order is fixed at
`laneContract.ts:26-31`: brief -> follow-through -> meetings -> agents.
`ChairHome.tsx:28-36` builds the lanes map from `LANE_ORDER` and
`LANE_COMPONENTS`.

### 2e. Dock entries

The Dock renders two groups:
1. **DeskWindowFrame panels** -- any open desk window registers its
   minimize/restore chip on the Dock automatically.
2. **Launchers** -- `launcherRegistry.ts:17-21` seats: attention (0),
   delivery-board (1), panes (2). These are drawer-type surfaces.

The Dock's visual layout is: [launchers] + [open surface window chips] +
[RecordOrb]. Fixed launchers (Intelligence, Speak, Meetings, Agents,
Settings) are the `MARK_APPS` at `DeskChrome.tsx:28-33`.

### 2f. Where a new front-door surface mounts

A Dashboard Door has two viable mount points:

**Option A: New Chair lane.** Add an entry to `LANE_ORDER` at
`laneContract.ts:26` and a component to `LANE_COMPONENTS` at
`lanes/index.ts:12`. This is the lightest touch -- the Chair already
composes lanes generically. The new lane would render alongside Brief,
Follow-Through, Meetings, Agents.

**Option B: New surface window.** Add a row to `SURFACES` at
`SurfaceWindows.tsx:37`, a lazy Core under `pages/cores/`, optionally a
`DEMOTED_ROUTES` entry at `routes.tsx:41`, and a `DESK_TOOLS` entry at
`tools.ts:6`. This gives a full windowed surface reachable from Cmd+K,
the Go menu, and deep links.

**Option C: Replace or wrap ChairHome.** The Chair IS the `/` route. A
Dashboard Door that replaces the hero + lanes composition would modify
`ChairHome.tsx` directly or introduce a new default surface via
`chairState.ts`.

---

## 3. MEASURED OBSERVATIONS

### 3a. The MEETINGS lane shows no scheduled recordings

The seeded hub's `_populate()` creates a meeting but does not create
scheduled recordings. In the real owner's desk, scheduled recordings
(HS-136-03) appear as SCHEDULED-badged rows in the MEETINGS lane
(`MeetingsLane.tsx:101-111`) only when `s.enabled` is true. Creating a
schedule requires opening the Cadence surface -- there is no Chair-level
create affordance.

### 3b. Follow-Through items are visible but not actionable from Chair

The Chair's FOLLOW-THROUGH lane shows items with check/dismiss verbs,
but clicking a row opens the item in a pullout or Intelligence. The
"complete" and "dismiss" verbs fire `POST /api/follow-through/complete`
inline at `FollowThroughLane.tsx:103-118`.

### 3c. No TODO/kanban view exists today

There is no unified task kanban on the Chair. Obligations are split
across three surfaces: the Brief lane (changed/broke/waiting/decisions),
the Follow-Through lane (now/overdue/waiting/unassigned), and the
Intelligence pullout (three-tab full view). A Dashboard Door composing
these into one kanban would be a new surface.

### 3d. The Go menu at 393px is hidden

The `desk-verbbar` (Go/Desk/Object/Window menus) is not visible at
393px. Navigation at mobile width depends on the Dock buttons and the
mark menu (which shows 4 app shortcuts).

### 3e. Meetings surface window not opening via /meetings redirect

Navigating to `/meetings` redirects to `/` and calls
`openSurfaceWhenReady("review-meetings")` (`App.tsx:27-34`). In the
walk, the surface window did not appear -- the `SurfaceWindows` effect
at line 331 may not have completed registration before the redirect
queued the open. The meetings window IS reachable via Dock or Cmd+2.

---

## Screenshots index

| File | Width | Description |
|------|-------|-------------|
| `first-value-capture-1440.png` | 1440 | FirstWords first-value flow |
| `first-value-capture-393.png` | 393 | FirstWords mobile |
| `chair-home-1440.png` | 1440 | Chair with all 4 lanes |
| `chair-home-393.png` | 393 | Chair mobile, all lanes stacked |
| `lane-brief-content-1440.png` | 1440 | BRIEF lane detail |
| `lane-follow-through-content-1440.png` | 1440 | FOLLOW-THROUGH lane detail |
| `lane-meetings-content-1440.png` | 1440 | MEETINGS lane detail |
| `lane-agents-content-1440.png` | 1440 | AGENTS lane detail |
| `chrome-menubar-1440.png` | 1440 | DeskChrome menubar |
| `mark-menu-open-1440.png` | 1440 | HoldSpeak mark menu |
| `go-menu-open-1440.png` | 1440 | Go menu open |
| `dock-overview-1440.png` | 1440 | Bottom Dock |
| `shelf-open-1440.png` | 1440 | Cmd+K shelf |
| `intelligence-brief-1440.png` | 1440 | Intelligence pullout, BRIEF tab |
| `intelligence-followthrough-1440.png` | 1440 | Intelligence pullout, FOLLOW-THROUGH tab |
| `meetings-redirect-1440.png` | 1440 | After /meetings redirect |
| `settings-home-1440.png` | 1440 | Settings 8-tile home |
| `settings-models-1440.png` | 1440 | Settings -> Models (Model Library) |
| `cadence-surface-1440.png` | 1440 | Cadence surface window |
| `workbenches-surface-1440.png` | 1440 | Workbenches surface |
