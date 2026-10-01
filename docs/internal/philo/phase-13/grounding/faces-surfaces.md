# PHILO Phase 13 grounding: faces, every surface (items 1, 2, 3, 3b)

**UNCHECKED — awaiting Astra.**

**Date:** 2026-10-01. **Base:** `89f69e346` on `docs/philo-13-ground` (main `4c49651e` + the plan). **Lane:** Fedaykin (Opus 5.5) for Muad'Dib. Docs only; no product code.
**Sibling files:** W2 owns `faces-jobs.md` (3c the Tuesday spine, 4 the fold, 5 ambition). Astra owns `structure.md` and `inventory.md`.

**Isolation.** Two real hubs (`scripts/graph_walk.py serve`, the rig's own hub process) ran on two throwaway HOMEs made by `mktemp -d` under `$TMPDIR`. Both DB paths were under those HOMEs (`probes/faces-surfaces-hubs.out.txt`). Both HOMEs were removed after the run. No real HOME, no owner DB, no send of any kind. Intelligence and dictation cleanup were off (no engine assigned; the `.43` engine is down).

- **COLD:** a fresh empty HOME. The first screen he would see.
- **POPULATED:** a week for a Senior Architect with three reports, seeded through the real producers before boot (`probes/faces-surfaces-seed.py.txt`, the `scripts/philo11_send_job.py` `mint` pattern) and through real routes after boot (`probes/faces-surfaces-seed_api.py.txt`): 3 projects, 1 published update + 1 draft, 4 people (3 `direct_report` with 1:1s, requests, notes, linked to the ledger project; 1 peer), 4 meetings with summaries, action items and decision artifacts, 2 desk decisions, 1 decision record, 3 notes, 8 meeting artifacts, 3 dictation journal rows, 1 brief, 1 Workbench with 3 items, 1 saved FILE destination inside the HOME.

**Method.** Playwright against the hub, one fresh browser context per surface (no window memory carried between surfaces), at 1440×900 (mouse) and 393×852 (`has_touch`, `is_mobile`, every press a `tap()`, drags as CDP touch events). Per surface: the shot, the opener used, ms from the press to the first verb or 60 chars of text in the window ("first useful pixel"), visible text nodes in view (the noun count proxy), verbs in view, ghosts, sub-12 px text, zero counters, dialogs, and hit ownership by `elementFromPoint` at each plated verb's centre (clip-aware: a verb scrolled out of its well is not counted). Scripts: `probes/faces-surfaces-*.py.txt`; raw records: `probes/faces-surfaces-*.json` and `*.out.txt`. The static canon scan (`scripts/ux_canon_scan.py`, read-only run, nothing written to the tree) is in `probes/faces-surfaces-canon-scan-*.out.txt`.

**Not `scripts/graph_walk.py run`.** The plan names the rig's "Walk a case" procedure. I used the rig's hub (`serve`) but not its `run` mode: `run` takes one atlas case per invocation, and an atlas case per surface (≈50 surfaces × 2 widths × 2 states) was not mintable in this lane. Every observation here is a direct Playwright observation on a rig hub, not an atlas observation. This is a method gap; Astra may hold it.

## Summary table

Job: J1 morning brief · J2 meeting→decision→update · J3 1:1 with a report · J4 project Room→update · J5 voice capture and find later · NONE. "Tuesday?" = would he open it on a Tuesday. Nodes = visible text nodes at first sight, 1440 populated. Shots under `shots/surfaces/`.

| # | Surface | Job | Tuesday? | Nodes | Worst finding | Shot (1440 / 393) |
|---|---|---|---|---|---|---|
| 1 | Chair (the arrival home) | J1 | yes | 60+ | five different "needs you" numbers on one screen and its neighbours; TALK dock covers content at 393 | `01-chair-pop-1440` / `01-chair-pop-393` |
| 2 | Arrival (First Words) | J5 | once | 9 | blank screen for ~1.9 s before the first verb | `00-arrival-cold-1440` / `00-arrival-cold-393` |
| 3 | Intelligence | J1 | yes | 35 | second copy of the Chair brief; three ghost verbs on an empty brief | `10-intelligence-pop-1440` / `-393` |
| 4 | Speak | J5 | yes | 31 | "LANDS IN Claude Code", "DICTATION NOT SET", "HOTKEY UNKNOWN": three setup states on the daily face | `11-speak-pop-1440` / `-393` |
| 5 | Ask AI | J2/J4 | sometimes | 21 | with "No default model" shown, ASK still runs and fails with a raw model path | `120-engine-off-ask-pop-1440` / `-393` |
| 6 | Meetings | J2 | yes | 48 | "Nothing needs you" while the Chair says 7–8 need him; G5 footer overlap | `13-meetings-pop-1440` / `-393` |
| 7 | Agents | NONE | no | 11 | "No agents" while the Floor lists six AGENT objects | `14-agents-pop-1440` / `-393` |
| 8 | Settings | NONE (setup) | no | 41 | "Meetings ✓ SUMMARY ON" with no summary engine | `15-settings-pop-1440` / `-393` |
| 9 | Live meeting | J2 | yes | 9 | no Go, no palette row: door is the Record verbs only | `16-live-pop-1440` / `-393` |
| 10 | Rhythm | J1 | no | 26 | footer `NOT SET` with no subject | `17-rhythm-pop-1440` / `-393` |
| 11 | Setup | NONE | no | 54 | "NEEDS ATTENTION" over a column of PASS rows; raw paths; 32 text nodes under 12 px | `18-setup-pop-1440` / `-393` |
| 12 | Context | NONE | no | 10 | `rev 0 ~0 tokens` (zero counters) | `19-context-pop-1440` / `-393` |
| 13 | Workbenches | NONE | no | 6 | a raw card button (`WorkbenchesHomeCore.tsx:92`) | `20-workbenches-pop-1440` / `-393` |
| 14 | Components | NONE (dev) | no | 54 | a developer catalogue reachable by the product; ~10 s to first useful pixel by its route | `21-components-pop-1440` / `-393` |
| 15 | Activity | NONE | no | 10 | "No activity yet" on a week with meetings and dictation | `22-activity-pop-1440` / `-393` |
| 16 | Desk memory | J5/J4 | yes | 58 | opens scrolled 172 px: its search and filters are hidden; `NO SOURCE` beside `Open source` | `23-desk-memory-pop-1440` / `-393` |
| 17 | Models (`open-concierge`) | NONE (setup) | no | 49 | 7 × "WAITING" with no next step on the row; pickers do not own 44 px at 393 | `24-models-pop-1440` / `-393` |
| 18 | New Project | J4 | rarely | 21 | sound face; three orange Connect verbs compete with the name field | `25-new-project-pop-1440` / `-393` |
| 19 | Processes | NONE | no | 14 | raw operation ids (`CHANNEL.SAVE_DESTINATION`, `Node:hub-project-writer`) | `26-processes-pop-1440` / `-393` |
| 20 | Commands | NONE | no | 8 | two "Add command" verbs on one empty face | `27-commands-pop-1440` / `-393` |
| 21 | People | J3 | yes | 16 | at 393 the first palette match for "People" is a note, not the app | `28-people-pop-1440` / `110-palette-people-pop-393` |
| 22 | Calendar snapshot | J1 | — | — | not walked: no door without a calendar screenshot drop | — |
| 23 | Models (`configure-runs-on` alias) | NONE | no | 49 | the same window as #17 under a second registry row | `30-models-runs-on-pop-1440` / `-393` |
| 24 | Connections (alias) | NONE (setup) | no | 77 | the same Settings window; destination row prints the raw folder path | `31-connections-pop-1440` / `-393` |
| 25 | Change places | NONE | no | 19 | 28 text nodes at 9–11 px; prose descriptions | `32-change-places-pop-1440` / `-393` |
| 26 | Room (project) | J4 | yes | ~40 | 4.5 s to open; "Nothing needs you" over open actions; G1 no route | `64-room-pop-1440`, `66-room-decision-unfolded-pop-1440` |
| 27 | Workbench window | NONE | no | ~60 | raw hex colour codes drawn over agent names; items read NEEDS REVIEW before any run | `70-workbench-window-pop-1440` |
| 28 | Delivery board | NONE | no | 8 | "NO LIVE SOURCE" and an owner/repo field; Dossier/Terminal/Roadmap/Repo need a repo (not walked) | `100-objwin-delivery-pop-1440` / `-393` |
| 29 | Schedule recording | J2 | sometimes | 20 | two mic buttons on the Title field | `102-objwin-schedule-pop-1440` / `-393` |
| 30 | Trust (Data boundaries) | NONE | no | 30 | "Enabled destinations None" with a saved destination; "MEETING SUMMARY ● OFF" (green dot) | `103-objwin-this-device-chip-pop-1440` / `-393` |
| 31 | Pane picker | NONE | no | 3 | "no tmux panes" (prose, lower case) | `101-objwin-panes-pop-1440` |
| 32 | Missed shade (bell) | J1 | yes | 40 | artifacts minted minutes ago read "7h ago" beside "38m ago" | `131-frame2-bell-pop-1440` / `-393` |
| 33 | Thought window (Write a thought) | J5 | yes | 12 | sound; "NO ENGINE YET · Choose an engine" is honest | `133-frame2-write-thought-pop-1440` / `-393` |
| 34–40 | Pullouts: Meeting, Artifact, Note, Decision, Persona, Knowledge, Thread | J2/J5 | mixed | 28–46 | Artifact "Meeting decisions" renders an empty DECISIONS section; Thread title is a raw id | `80…85-pullout-*-pop-1440` / `-393`, `91-pullout-new-thread-pop-1440` |
| 41 | Frame: menu bar, Dock, Expose, Switcher, SnapGhost, palette, Get Info, mark menu, Hide the menus | all | — | — | the Dock overflows 1440 with one long window chip; at 393 chrome takes ~25 % of the height | `41…53-frame-*-pop-1440`, `41…47-frame-*-pop-393`, `130-frame2-mark-menu-*` |

Counts: **walked 21 of 23 registry rows** (two rows are aliases of a walked window: #23 and #24 were opened and shot; #22 Calendar snapshot was not reachable), **3 of 7 direct object windows** (Workbench, ScheduleCreate, Trust; Delivery board as the door to DeliveryDossier/Terminal), **7 of 13 dedicated pullouts** (Meeting, Artifact, Note, Decision, Persona/Recipe, Knowledge, Thread) plus Workflow's editor (New Workflow), and the frame. Not walked: Chain, Coder, Directory/ZoneWindow, Intelligence pullout as a Floor object, People pullout, Roadmap, Repository, DeliveryDossier, DeliveryTerminal, Calendar snapshot (see UNKNOWN).

## 1. The frame

Evidence: `probes/faces-surfaces-frame-pop-1440.json`, `faces-surfaces-frame-pop-393.out.txt`, `faces-surfaces-frame2.json`, `faces-surfaces-misc.json`, `faces-surfaces-room-1440.json`.

**Arrival.** Cold: First Words, "Dictate one sentence" (`00-arrival-cold-1440.png`). The page is blank for about 1.9 s before the first verb (`arrive_ms` 1891–1912 in every walk record; the first exploratory shot at ~1.2 s was an empty dark screen). "Continue later" opens the Chair: `1 need you`, `NO CALENDAR Connect calendar`, SETUP `No engine for summaries`, BRIEF `THIS DEVICE` `Generate` `No brief yet`, and the TALK dock (`01-chair-cold-1440.png`). Populated: `8 need you`, six filter tokens, NEEDS YOU 5 OF 7, BRIEF · 9 THINGS WAITING, SEND, MEETINGS 3 (4 meetings exist), and one SEND well per meeting, each printing the full destination path (`01-chair-pop-1440.png`, `102-objwin-schedule-pop-1440.png`).

**Menu bar.** 1440: `HoldSpeak` mark · Desk · Object · Go · Window · `■ ⌂ THIS DEVICE` · bell count · Search ⌘K · date · clock. 393: **only Go** (Desk, Object and Window are absent), and the clock wraps under the bar (`menubar.scrollWidth` 396 > 393; `faces-surfaces-frame-pop-393.out.txt`). At 393 the mark menu carries Open Intelligence and Open People (`130-frame2-mark-menu-pop-393.png`), so those two stay reachable.

**Menus.** Desk: New Note/Decision/Knowledge/Agent/Workflow/Workbench/Thread/Project, Hide the menus, List view, Open Intelligence, Open People. Go: 16 programs (Live meeting, Components, People, Intelligence, Calendar snapshot are not on Go). Window: 8 rows, all ghost with no window open. **Object: all ten rows stay ghost after a list row is selected**, while the same row's right-click menu has Open, Get Info, Continue in thread, Duplicate, Move to Zone, Delete live (`111-object-menu-decision-pop-1440.png`, `111b-row-context-menu-decision-pop-1440.png`). That right-click menu ghosts `Edit · Not editable` on a decision whose own window has a live **Edit** verb (`112-get-info-decision-pop-1440.png`).

**Get Info** from the list opens the object's ordinary window, not an Info card (`112-get-info-decision-pop-1440.png`). Astra's inventory places `InfoWindow` under WorldStage only (`WorldStage.tsx:275-277`), so on the List (which the phone always shows) Get Info is a second Open.

**Palette (⌘K).** Opens a shelf of VERBS, PROGRAMS, DRAWERS, SETTINGS. "Live meeting", "Components" and "Calendar snapshot" give "No matching tools or Desk items." "Send" gives `Slack NOT CONFIGURED`, `Telegram control NOT CONFIGURED` and unrelated programs; no document can be sent from the palette. "People" at 393 lists the **note** "People & vocabulary" first and `Open People` second, so Enter opens the note (`28-people-pop-393.png`, `110-palette-people-pop-393.png`). At 393 one Escape does not close the shelf; two do (`shelf_open_after_one_escape: true` in `faces-surfaces-misc.json`).

**Dock.** 1440: Intelligence (•), Speak, Meetings, Agents, Settings, Floor/Chair toggle, Desk memory (badge), Delivery, Panes, **Hide the menus**, Places, the record orb, then one chip per open window, Overview, Reset. With one window whose title is long, **the Dock is 1510 px wide on a 1440 viewport: left −35, right 1475** (`dock_geometry` in `faces-surfaces-room-1440.json`; `64-room-pop-1440.png` shows "Intelligence" cut at the left edge; `70-workbench-window-pop-1440.png` shows "ence"). 393: three rows (seats; Delivery/Panes/Hide the menus/Places/orb; window chips + Overview + Reset). Dock 125 px + window-chip row ≈ 170 px, menu bar 48 px: **about 25 % of the 852 px height is chrome**; a window gets 631 px (`meetings_open_rect [0, 48, 393, 631]`).

**Windows at 1440.** Open from Go: front at (24,72) 640×619. Title drag moves it; the grip resizes it; a second window comes in front; a click on a visible part of the back window raises it; maximize fills the work area (10,54, 1420×794) and restores; minimize removes the window and leaves no distinct Dock sign (only the same underline an open window has, `46-frame-minimized-pop-1440.png`). Expose (⌃↑) tiles both windows with titles (`48-frame-expose-pop-1440.png`). Switcher (⌃`) lists them (`49-frame-switcher-pop-1440.png`). **SnapGhost lies about the result:** the ghost was 705 px wide, the snapped window 820 px (`snapghost` vs `snapped_rect` in `faces-surfaces-frame-pop-1440.json`; `50-frame-snap-ghost-pop-1440.png`). Two windows carried `is-front` at once (`windows_after_second`); the real front is the higher z-index (unknown whether this is a defect or a class meaning "front layer").

**Windows at 393.** Every window is full width at y=48. A touch drag on the title does not move it, there is no resize grip and no maximize light (`moved false`, `no grip found`; `41-` and `42-frame-*-pop-393.png` are byte-identical, the expected tell of a drag that changed nothing). A second window covers the first completely; the first has no visible point to tap (`meetings_visible_point null`). The only ways back are the window chip row and Overview.

**Memory across reload.** Positions of the windows that were open come back, but **a minimized window comes back open and in front**, and one window's position did not survive (Settings at (10,54) returned at (24,72)) (`memory_before_reload` / `memory_after_reload`, both widths).

**Hide the menus** (a Dock seat) replaces the menu bar with `⌂ THIS DEVICE` and the Dock with `Back to Desk · Places · Meeting recorder idle` (`51-frame-menus-hidden-pop-1440.png`). It is a focus mode named as a removal.

**The bell (Missed shade).** BRIEF Weekly brief `10 THINGS`; NEEDS YOU · 5 (four "Artifact needs review"); FINISHED · 4 ("Meeting saved"). **Artifacts minted at 14:41 local read "7h ago" at 15:19, while meetings minted the same second read "38m ago"** (`131-frame2-bell-pop-1440.png`; DB rows store naive local time, `artifacts.created_at = 2026-10-01T14:41:28` with the desk at MDT). Likely a naive timestamp read as UTC (cause not verified).

## 2. Every application (per surface)

Times are press → first useful pixel at 1440 / 393 and include a 250 ms menu settle. "Live" means it read the populated week; "stale" means it did not.

**Intelligence** (Dock seat 0; Desk menu; mark). J1. Tuesday: yes, but it is the second copy of the brief that the Chair already shows (BRIEF, FOLLOW-THROUGH, DECISIONS wings; the brief items repeat the Chair's BRIEF rows). 166–454 ms. Live. Cold: "No brief generated." + Generate, with **Acknowledge, Defer, Speak ghosted in the footer** on an empty brief (`10-intelligence-cold-1440.png`; A.11 says withhold). 15 text nodes at 11 px (wing labels, section captions). Brief kind chip `MTG` sits on its own row under the item.

**Speak** (Dock seat 1, ⌘1). J5. Yes. ~650 ms. Live (`3 TODAY`). The daily face carries three setup states: `LANDS IN · Claude Code` with `FOCUSED APP` and `DRY RUN` chips, `DICTATION · ⚠ NOT SET Choose`, `HOTKEY · ⌥R ⚠ UNKNOWN Re-check`. At 393 the `▸ Details` disclosure is covered by the transport (`speak-transport` owns its centre; `walk-pop-393.json`). TALK with no microphone gives an honest line: "THE BROWSER GAVE NO MICROPHONE. YOUR DRAFT REMAINS EDITABLE. CHECK THE MICROPHONE, THEN RETRY." (`121-engine-off-talk-pop-1440.png`). Text at 9–11 px: LEVEL, LANDS IN, DICTATION, HOTKEY, 3 TODAY.

**Ask AI** (Go, ⌘I; a panel, no SurfaceWindows row). J2/J4 when an engine exists. ~340 ms. The prompt field is prefilled with prose ("Summarize the following in 3–4 tight sentences. Be concrete."). The face says `Ask · No default model · Choose default`, yet **ASK stays live; pressing it fails with `HUB> model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf`**, repeated upper-case in the footer (`120-engine-off-ask-pop-1440.png`, `-393.png`). Engine-off excuses the failed answer, not a raw path as the failure face or a verb that cannot run. `CTX 0.0K/16.4K` appears twice. A yellow left rail marks the assignment block (DS6 is a hard zero; not verified whether this rail is the counted pattern).

**Meetings** (Dock seat 2, ⌘2). J2. Yes. ~640 ms. Live: four rows (three after the delete proof). Headline **"Nothing needs you"** while the Chair says 7–8 need him and two of these meetings own unassigned action items (`13-meetings-pop-1440.png`; `meetingsHeadline` counts only summaries and failures, `web/src/pages/cores/history/helpers.ts:216-233`). Every row wears a green `SAVED` chip. Row meta (`OCT 01 · 30 MIN · 4 WORDS`) is 10 px. Footer `NO SUMMARY ROUTE · NO ASSIGNMENT` is green (a success colour on a missing route). At 393 the list shows one and a half meetings above the footer.

**Agents** (Dock seat 3, ⌘3). NONE. No. ~640 ms. **"No agents" and "No sessions"** while the Floor list has six AGENT objects (Chase, Desk, Draft, Interview, Plan, Project) (`14-agents-pop-1440.png`, `03-floor-list-pop-1440.png`). Header `CREW · SESSIONS · BLOCKED` with no counts. The face reads `recipeRows` (`web/src/pages/cores/CompanionCore.tsx:134-175`); why it is empty while the Floor shows six personas is unknown.

**Settings** (Dock seat 4, ⌘4). Setup. No. ~640 ms. `No default model` (display), then nine rows each with `Open`: a menu of menus. **`Meetings ✓ SUMMARY ON · AFTER ROOM MEETINGS`** is green although no summary engine exists (the chip reads the config switch `hub.meetings.intelligence`, `web/src/pages/cores/settingsPrefs.tsx:515-517`); the Chair says "No engine for summaries" and Trust says "MEETING SUMMARY OFF". `Voice ✓ LIVE` while Speak says `DICTATION NOT SET`. Footer `NOT SET · WRITTEN 14:41`. A wider window shows a `Posture · YOLO` row that the default width hides (`51-frame-menus-hidden-pop-1440.png`).

**Live meeting** (no Go, no palette row; Record orb, Chair Record meeting, `/live`). J2. Yes. 1.5–1.8 s via route. "Ready to record · Start meeting · Link · connected · TRANSCRIPT · Start a meeting to begin · READY". Not walked further (the rig forbids the microphone).

**Rhythm** (Go). J1 (brief cadence). No. ~645 ms. `Every 15 min` display; Sweep, Runs on, Monday brief `DAILY 08:00 ✓ LAST OCT 01` + `1 WATCH ITEM`, Notify. Footer `NOT SET` with no subject.

**Setup** (Go). NONE. No. ~640 ms. `■ NEEDS ATTENTION` over a column of `PASS` rows (none fails); detail lines print raw paths (`Loaded /var/folders/…`, `Schema OK at /var/…`); 32 text nodes at 10 px (every PASS). Next step "Run one dictation to verify" + `Continue arrival` + `Runs on`.

**Context** (Go). NONE. No. `STATUS rev 0 ~0 tokens 0/32,768 CHARS` (A.8: two zero counters), `Save` ghost, one textarea.

**Workbenches** (Go). NONE. No. One card `Ledger cutover bench · 3 PENDING · Choose default · Manual` rendered as a raw button (`WorkbenchesHomeCore.tsx:92`).

**Components** (`/design/components` only). NONE: a developer catalogue. ~10 s to first useful pixel by its route (`first_useful_ms` 10197). 26 text nodes under 12 px; `Download weights` clipped; A1 at `ComponentsCore.tsx:402`.

**Activity** (Go). NONE. "No activity yet" with `Refresh now`, `☑ WATCHING`, `Clear records` on a week with meetings and dictation. Not his job.

**Desk memory** (Go; Dock seat with badge). J5/J4. Yes, if it opened at the top. **It opens with its body scrolled 172 px (1440) / 269 px (393): the search field and the All/Decisions/Commitments/Briefs/Meetings filters are above the fold** (`scrolled: desk-surface-body:172` in `walk-pop-1440.json`; `23-desk-memory-pop-1440.png`). CURRENT 1 shows `Freeze the old ledger on Nov 5` with chips `DEC 10-01 · DECISION · NO SOURCE · ACCEPTED` and, on the next line, `SOURCE MTG 10-01 · 12:41 · Open source`: a "no source" chip beside a live source link. MEETINGS 4, BRIEFS 10. Live.

**Models** (`open-concierge`; Go via the alias row; `24-models-pop-393.png` and `30-models-runs-on-pop-393.png` are byte-identical because both rows open one window; Chair "Choose an engine"). Setup. No. ~635 ms. `No engine yet · THIS MAC · M-SERIES · CHECKED 2:45 PM`, `Add an engine`, THE SET: seven groups each `— ⌄ ○ WAITING`, PROBE `Test`, footer `7 GROUPS · 7 WAITING`, `Cancel`, `Use these` (ghost). "Engine off" excuses no engine; it does not excuse seven WAITING rows that do not say what they wait for. At 393 the `—` pickers own their centre but not the 44 px band (`faces-surfaces-hit44-393.json`).

**New Project** (Desk menu; palette at 393). J4. Rarely. Sound and short: name field with mic, three sources each `○ NOT SET UP Connect` (orange), footer `NO SOURCES · BLANK PROJECT · Cancel · Create Project` (ghost until named).

**Processes** (Go). NONE. `WATCHING RUNS 1`, empty NEEDS YOU / RUNNING / WAITING / UNKNOWN headings, one row `10:28:07 CHANNEL.SAVE_DESTINATION · … Owner-session · Node:hub-project-writer SUCCEEDED` (raw ids; `10:28:07` matches neither the local time of the save, 14:41, nor its UTC time, 20:41). Footer `KERNEL · CURSOR 5 · RUNS 1`.

**Commands** (Go). NONE. "No voice commands" with `Add command` twice (head and empty state) and `COMMANDS OFF · Enable in Settings`.

**People** (Desk menu `Open People`, mark menu; no Go row; palette second row). J3. Yes. ~640 ms. Cold: `Set up People` + one prose line. Populated: `Encrypted · Local storage · Notes only`, `New relationship`, a Name field + `↻ DIRECT REPORT` + `Add`, then Avery Chen, Jordan Patel, Morgan Lee (Peer), Sam Rivera. The 1:1s, requests and notes seeded for each report are one press away (J3 is W2's spine).

**Calendar snapshot.** Not walked. Its only doors are a Glass Drop of a calendar screenshot and a Settings import (`GlassDropLayer.tsx:68`, `SettingsCore.tsx:2115`); no menu, palette or route reaches it.

**Connections** (Go; alias of Settings with scope). Setup. Opens the Settings window scrolled to CONNECTIONS: `TOOLS 5` (GitHub NEVER CHECKED, Jira form with site/email + Add, Confluence, Calendar NOT SET UP, Models Unassigned), `DESTINATIONS 1 ▸ Team updates folder FILE /private/var/folders/q7/…/Updates-out THIS DEVICE`, `Add destination`. Two registry rows ("Settings", "Connections") open one window.

**Change places** (Go, ⌘⇧P, Dock Places). NONE. Four 3-D scenes with prose descriptions at 9–11 px (28 nodes). A pleasure, not a job.

**Room** (Floor list → project; Desk memory scoped). J4. Yes. **4.5–4.8 s from the double-click to the window** (`open_ms` 4484 in `faces-surfaces-room-1440.json`). `Nothing needs you · ● ON TRACK · Draft update`, NEEDS YOU "Nothing needs you" (the project's meeting owns the unassigned "Write the rollback runbook"), SOURCES `Steward`, PEOPLE 3 with Open each, SINCE YOU LOOKED, DECISIONS & COMMITMENTS 1, a sticky `Ask this project…` well with `MODEL · NOT SET Choose`. The published update is not on the first screen. Unfolding the decision row shows a SEND well only; **the sticky Ask well covers the SEND well's lower half** (`66-room-decision-unfolded-pop-1440.png`).

**Workbench window** (from Workbenches or the Floor). NONE today. Opens in ~460 ms. **Agent rows draw the raw colour code over the name** ("#25Chase", "#6BDesk", `70-workbench-window-pop-1440.png`). Items read `NEEDS REVIEW` before any run; `Run · Bind an agent first`; `Starts only when you press Run.` (prose); raw path `~/.holdspeak/workbenches/workbench_7f0804c026b5/`. Static scan: 23 raw `<button>`s (`WorkbenchWindow.tsx:178`, `:319`, `:422`, `:431`, …).

**Delivery board** (Dock Delivery). NONE. `INTEGRATION Companion repo owner/repo [field] ✕ NO LIVE SOURCE`, footer `SOURCES · WORK · READ 15:09:55`. Dossier, Terminal, Roadmap and Repo need a repository; not walked.

**Schedule recording** (Chair Schedule). J2. `RECORDING STARTS ON ITS OWN AT THE SET TIME`, Title (**two mic buttons**: one inside the field, one beside it), Mode ONCE, When, Duration 60 MIN, Cancel, Schedule (`102-objwin-schedule-pop-1440.png`).

**Trust / Data boundaries** (menu bar `THIS DEVICE`). NONE. "All data stays on this device"; **`Enabled destinations · None` while a FILE destination is saved and listed in Connections** (`103-objwin-this-device-chip-pop-1440.png`; the count reads `/api/setup/status` `trust.destinations` filtered by `enabled`, `TrustWindow.tsx:62-68,107-110`); `MEETING SUMMARY ● OFF` with a green dot; eight label/value rows of prose ("Only runs for an explicit summary request", "Change the summary assignment").

**Pane picker** (Dock Panes). NONE. A popover: field + mic + `+ SPAWN` + "no tmux panes".

**Pullouts** (`probes/faces-surfaces-pullouts-pop-{1440,393}.json`). Opening from the list takes ~2.0–2.3 s by double-click at 1440 and ~1.2–1.4 s by tap at 393.
- *Meeting:* `Review meeting` in the head; quote of the summary; SEND with a form CycleGadget and the folder (raw path); ACTION ITEMS; ARTIFACTS; `Dictate about this`, `Record follow-up`.
- *Artifact "Meeting decisions":* **heading DECISIONS and nothing under it**, though the artifact holds `structured_json.decisions` (`81-pullout-artifact-pop-1440.png`); two artifacts share the name "Meeting decisions" in the list; every artifact row reads `ATTN 1`. Raw buttons `ArtifactPullout.tsx:38`, `:57`, `:64`.
- *Note, Knowledge:* sound.
- *Decision:* `accepted ↻ karol` (lower-case status token and the owner's login), CONTEXT/DECISION/CONSEQUENCES, SEND, `Copy · Dictate about this · Edit`.
- *Persona (Chase):* **the display line is `#2563EB`**, the persona's colour code, above its name (`84-pullout-recipe-agent-pop-1440.png`); `Ask` ghost; two yellow-railed "assignment · No default model · Choose default" blocks.
- *Thread (New Thread):* **title and head are the raw id `th_09c37ed817eb`** (`91-pullout-new-thread-pop-1440.png`); `Send` ghost; static A1 at `ThreadPullout.tsx:110`, `:122`, `:1671`.
- *New Workflow:* step chips are raw buttons (`WorkflowEditor.tsx:94`, `:107`, `:121`). *New Decision* creates and persists an untitled "New decision" at once.

## 3. The carried ledger (handover XXXII §Open 3)

| Item | Reproduced? | Evidence |
|---|---|---|
| Chair TALK dock over the meeting preview at 393 | **Yes.** The `arrival-capture-bar` (y 573–711) owns the hit points of the preview's `THIS DEVICE` chip, `▸ TRANSCRIPT · 4 WORDS` and the next meeting's title. Not at 1440. | `60-ledger-chair-meeting-preview-pop-393.png`; `covered` list in `faces-surfaces-ledger-chair-preview.json` |
| "No meetings yet" beside an open record | **Not reproduced** with four meetings: with a record open (from the list and from the Chair) the headline reads "Nothing needs you" and the list keeps its rows. The defect needs an empty list (the one-record case of `BACKLOG.md:25`); I did not seed that case. | `61-ledger-meeting-record-pop-1440.png`, `63-ledger-chair-open-meeting-pop-*.png`, `faces-surfaces-ledger-meetings.json` |
| G1, the dead Room Open | **The dead verb is gone; the route is still missing.** The Room decision row has no Open; it unfolds to a SEND well only. There is no way from the Room to the record in Intelligence DECISIONS. | `65-room-decisions-pop-1440.png`, `66-room-decision-unfolded-pop-1440.png`; `decision_row.buttons: []` |
| G5, Meetings footer at 393 | **Yes.** With a record open, `NO SUMMARY ROUTE · NO ASSIGNMENT` (9–288, y 613–631) runs under `MD` (211–255) and `SRT` (259–303); the text reads "NO ASSI[MD]NMEN[SRT]". The buttons still own their hit points, so the press works; the chip is unreadable. | `63-ledger-chair-open-meeting-pop-393.png`; `overlaps` in `faces-surfaces-ledger-meetings.json` |
| The lone THIS DEVICE chip | **Yes**, on the Chair BRIEF head at both states (`BRIEF · 9 THINGS WAITING   [THIS DEVICE]   Generate`), and the same lone chip closes every SEND well, the Desk memory footer and the menu bar. | `01-chair-pop-1440.png`, `01-chair-cold-1440.png`, `23-desk-memory-pop-1440.png` |
| **Meetings hard-delete** | **Yes.** Meeting → record → `Delete` → `Delete?` → gone. No undo; the footer says `DELETED 14:59`. DB on the throwaway HOME: before `meetings m-hiring` 1 row, `segments` 2, `intel_snapshots` 1, `artifacts` 2; after: 0, 0, 0, 0. | `67/68/69-ledger-delete-meeting-*-pop-1440.png`; `faces-surfaces-ledger-delete-meeting.json`; `holdspeak/db/meetings.py:1061-1065` |
| **Workbench items hard-delete** | **Yes, after an 8 s client undo.** Remove → toast `Removed Draft rollback runbook · Undo · 08s`; DB at 1 s: row present; at 12 s: row gone, face "Removal committed". The table has no tombstone column (`pragma table_info(workbench_items)`). | `71b-workbench-item-confirm-pop-1440.png`, `72-workbench-item-deleted-pop-1440.png`; `db_at_1s` / `db_at_12s` in `faces-surfaces-workbench-1440-delete.json`; `holdspeak/db/workbenches.py:295-301` |

## 3b. The face canon audit

Static scan (read-only `scripts/ux_canon_scan.py`, base tree): A1 raw `<button>` 102, A3-prose 43, B raw control 30, emoji 24, A8 zero counters 23, raw-ids 17, C type collapse 4, A3-sentence 2 (`probes/faces-surfaces-canon-scan-totals.out.txt`; per face with file:line in `faces-surfaces-canon-scan-by-face.out.txt`).

| Rule | What the walk saw | Evidence |
|---|---|---|
| **Plain language / no prose** (A.3, Tenet 4) | Prose on faces: Ask's prefilled prompt; Trust's eight value sentences; Change places descriptions; Setup detail lines with paths; Workbench "Starts only when you press Run."; People cold "Encrypted, local-only relationship context". Raw machine words: `th_09c37ed817eb`, `#2563EB`, `CHANNEL.SAVE_DESTINATION`, `Node:hub-project-writer`, `accepted`, `karol`, full `/private/var/…` paths in every SEND well and in Connections. | shots above; static raw-ids 17 (`PeopleCore.tsx:267`, …) |
| **Every verb the library Button** (A.1) | Live raw buttons on walked faces: Artifact (`ArtifactPullout.tsx:38/57/64`), Thread (`ThreadPullout.tsx:110/122/1671`), Workflow editor (`WorkflowEditor.tsx:94/107/121`), Workbench window (23), Workbenches card (`WorkbenchesHomeCore.tsx:92`), Persona capability chips (`CapabilitySection.tsx:136/187/204`), Delivery board (`DeliveryBoard.tsx:89/439/467`). Note: many non-`btn` elements the DOM audit flagged are library species (`surface-ledger-line`, `gadget-transport-key`) and are not findings. | `faces-surfaces-canon-scan-by-face.out.txt`; `audit.buttons` in walk JSON |
| **Voice mic on every text input** | Met on almost every field walked (search, names, prompts, Context, New Project, Jira site/email). Exceptions: Speak's draft has no mic (allowed: Talk is the face's mic authority, UX-CANON D); Schedule's Title has **two** mics. Static B (raw control) 30, e.g. `DoorCore.tsx:408`, `ScheduleCreateWindow.tsx:160`. | `inputsNoMic` in walk JSON; `102-objwin-schedule-pop-1440.png` |
| **12 px floor** | **Broken on 25 of the faces walked.** Captions and meta at 10–11 px nearly everywhere; 9 px in Speak, Ask, Components, Change places. 157 hard-coded `font-size` declarations of 9–11 px under `web/src/desk` (e.g. `web/src/desk/chair/chair.css:126`, `:167`, `:178`). | `audit.small` per surface in `walk-*.json`, `pullouts-*.json` |
| **No counters of zero** (A.8) | Context `rev 0 ~0 tokens`; Agents header `CREW · SESSIONS · BLOCKED` (the counts are dropped but the words stay); static A8 23 (`SettingsCore.tsx:1570`, `ConciergeCore.tsx:485`, `LiveCore.tsx:683`, …). | `19-context-pop-1440.png` |
| **No modals** (A.4) | **Met.** No `dialog`, `role=dialog` or `aria-modal` on any walked face; deletes confirm in place (`Delete?`, Undo toast). | `audit.dialogs` empty in every record |
| **A verb that does nothing** (A.11) | Ghost-but-shown: Intelligence Acknowledge/Defer/Speak on an empty brief; Object menu all ghost with a selection; Window menu all ghost. Live-but-failing: Ask `ASK` with no model. | §1, §2 |
| **Hit ownership at 393 by hit test** | Clip-aware centre test: one loss, Speak `▸ Details` under `speak-transport`. Chair: the TALK dock owns the preview's points (ledger row 1). 44 px band (`elementFromPoint` at centre ±20 px): Chair 11/14 own it, Meetings 3/5, Settings 5/8, Models 4/8 (the `—` pickers own only their 27 px). Chrome-strip rows (Dock, menus) not measured. | `walk-pop-393.json`; `faces-surfaces-hit44-393.json` |
| **Honest states** (A.10) | Dishonest greens: Settings `SUMMARY ON`, Meetings footer green `NO SUMMARY ROUTE`, Trust green dot on `OFF`, every meeting `SAVED`. Contradictions across faces: see F1–F3 below. | §2 |

## FINDINGS, ranked by owner cost

Each is tagged with the job it breaks. "Engine off" is excused only where named.

1. **F1 (J1, J2, J4): "Needs you" is five different numbers.** Chair `8 need you` / `7 need you`, Chair NEEDS YOU `5 OF 7`, bell `7`/`5`, shade `NEEDS YOU · 5`, Dock Desk memory badge `7`/`5`, Meetings `Nothing needs you`, Room `Nothing needs you`, all on the same data at the same moment. He cannot trust the one number the Desk is built around. `01-chair-pop-1440.png`, `13-meetings-pop-1440.png`, `64-room-pop-1440.png`, `131-frame2-bell-pop-1440.png`; `helpers.ts:216-233`.
2. **F2 (J2, J4): status faces contradict each other.** Settings `SUMMARY ON` vs Chair `No engine for summaries` vs Trust `MEETING SUMMARY OFF`; Settings `Voice LIVE` vs Speak `DICTATION NOT SET`; Trust `Enabled destinations None` vs a saved destination; Agents `No agents` vs six AGENTs on the Floor; Desk memory `NO SOURCE` beside `Open source`. `settingsPrefs.tsx:515-517`, `TrustWindow.tsx:62-68,107-110`, `CompanionCore.tsx:134-175`.
3. **F3 (J2): a deleted meeting is gone for good, and a Workbench item after 8 s.** Meeting, segments, summary and artifacts all leave the DB with no undo. `faces-surfaces-ledger-delete-meeting.json`, `faces-surfaces-workbench-1440-delete.json`; `meetings.py:1061-1065`, `workbenches.py:295-301`.
4. **F4 (all jobs at 393): the phone Desk is a third chrome.** Menu bar 48 px with only Go, Dock two to three rows (125–170 px), the TALK dock floating over content; ~25 % of the height is frame, windows cannot move or resize, a second window hides the first completely. `41-frame-meetings-open-pop-393.png`, `10-intelligence-pop-393.png`, `60-ledger-chair-meeting-preview-pop-393.png`, `faces-surfaces-frame-pop-393.out.txt`.
5. **F5 (J2, J4): failure faces that lie or dead-end.** Ask runs with "No default model" and fails with `model file not found: ~/Models/gguf/…`; Intelligence shows Acknowledge/Defer/Speak on no brief; the Object menu stays all ghost when a row is selected. `120-engine-off-ask-pop-*.png`, `10-intelligence-cold-1440.png`, `111-object-menu-decision-pop-1440.png`.
6. **F6 (J2): the meeting's decisions are not readable in their artifact.** "Meeting decisions" opens to an empty DECISIONS heading; two artifacts share the name; every artifact says `ATTN 1`; the shade calls them "Artifact needs review · 7h ago" minutes after they were made. `81-pullout-artifact-pop-1440.png`, `131-frame2-bell-pop-1440.png`.
7. **F7 (J4): the Room is slow and quiet about what changed.** 4.5 s to open; "Nothing needs you" over an unassigned action from the project's own meeting; the published update is not on the first screen; the Ask well covers the decision's SEND well; G1's route to the record is still missing. `faces-surfaces-room-1440.json`, `64/65/66-room-*.png`.
8. **F8 (J1, J5): Desk memory opens with its search hidden.** The body is scrolled 172–269 px on open; the one field he came for is above the fold. `23-desk-memory-pop-1440.png`, `scrolled` in `walk-pop-*.json`.
9. **F9 (all): the 12 px floor is not met on 25 faces**, and 157 CSS declarations set 9–11 px under `web/src/desk`. The 2026-09-21 ruling is unpaid across the Desk. `audit.small` in the walk JSON; `chair.css:126`.
10. **F10 (J2, G5): the Meetings footer chip runs under MD/SRT at 393** and is green for a missing route. `63-ledger-chair-open-meeting-pop-393.png`.
11. **F11 (J1): time is wrong on the shade.** Artifacts from 14:41 read "7h ago" at 15:19; same-second meetings read "38m ago"; Processes prints `10:28:07` for a save made at 14:41 local / 20:41 UTC. Cause not verified (naive local timestamps read as UTC is the likely one). `131-frame2-bell-pop-1440.png`, `26-processes-pop-1440.png`.
12. **F12 (frame): the Dock overflows 1440** as soon as one window has a long title (1510 px wide, −35 to 1475). `faces-surfaces-room-1440.json`, `64-room-pop-1440.png`.
13. **F13 (frame): the window manager forgets and fibs.** Minimized windows return open after reload; one window's position was lost; the snap ghost (705 px) differs from the snap (820 px); a minimized window has no Dock sign. `faces-surfaces-frame-pop-1440.json`, `46/50-frame-*-pop-1440.png`.
14. **F14 (J3 at 393): People's first palette match is a note**; the app is the second row and the mark menu's last row; Desk menu is absent at 393. `110-palette-people-pop-393.png`, `130-frame2-mark-menu-pop-393.png`.
15. **F15 (all): raw machine text on faces.** Thread `th_09c37ed817eb`, persona display `#2563EB`, Workbench `#25Chase` overlap, `CHANNEL.SAVE_DESTINATION`, `accepted ↻ karol`, full temp paths in every SEND well. `91-pullout-new-thread-pop-1440.png`, `84-pullout-recipe-agent-pop-1440.png`, `70-workbench-window-pop-1440.png`.
16. **F16 (Tenet 3): a dozen windows he would not open on a Tuesday.** Agents, Setup, Context, Workbenches, Components, Activity, Processes, Commands, Change places, Pane picker, Delivery board, Models ×2 rows, Connections as a second Settings door. Two registry rows open Models, two open Settings. Candidates for merge or park (Astra's consolidation map owns the decision).
17. **F17 (J1): cold arrival is blank for ~1.9 s**, then First Words. `arrive_ms` in every walk record.
18. **F18 (J1): the brief exists twice** (Chair BRIEF and Intelligence → BRIEF) with different verbs (Ack/Defer vs Acknowledge/Defer/Speak). `01-chair-pop-1440.png`, `10-intelligence-pop-1440.png`.

## Reconciliation with Astra's S0 inventory (`origin/docs/philo-13-ground-astra:…/inventory.md`)

Read after the walk. Same 23 manifest rows, same 7 direct windows, same 14 pullout components.

- **Astra lists, I did not walk:** DeskToolInspector, MissionControlConveyor, NewWorkbenchChooser, SessionPullout, the compact receipt row, Glass Drop layer, ZoneWindow, InfoWindow (spatial), ThoughtWorkspaceWindow as a Note route, InlineEditor, Chain/Coder/Directory pullouts, Roadmap/Repo/Dossier/Terminal windows, Calendar snapshot.
- **I walked, Astra lists differently or not at all:** the Missed shade (Astra: AttentionDrawer/SystemShade; it is the bell in the menu bar), the mark menu as the only 393 door to People/Intelligence, the Thought window from the Chair's `Write a thought`, the Pane picker as a popover (not a window), the Room as the Project redirect (Astra: Project → `open-project-memory` scoped; the face is the Room).
- **Agreements the walk confirms:** Live meeting, Components and Calendar snapshot have no Go or palette door; Connections and the second Models row open existing windows; Ask has no SurfaceWindows row.
- **One divergence to check:** Astra places Get Info's `InfoWindow` under WorldStage only. On the List (the phone's default), Get Info opened the ordinary object window (`112-get-info-decision-pop-1440.png`). Both are consistent; the face consequence is that Get Info ≡ Open off the spatial Floor.
- **Astra claim not walked:** the Brief "Open person" handoff uses an unresolved key `people` (`BriefView.tsx:484-492`). I did not press it.

## UNKNOWN (not verified here)

- Calendar snapshot, Roadmap, Repository, DeliveryDossier, DeliveryTerminal, Chain, Coder, Directory/ZoneWindow, InfoWindow (spatial), the spatial Floor itself (WebGL drew no objects in 1.5 s headless; the Floor is out of scope).
- "No meetings yet" beside an open record: needs the one-meeting seed; not run.
- Why Agents shows no agents while the Floor lists six; why two windows carry `is-front`; the cause of "7h ago".
- Real touch hardware: 393 presses were Playwright touch emulation and CDP touch events, not a phone.
- Engine-on behaviour of every surface; the Room's update posture and send (W2's J4).
- First-useful-pixel numbers are rough: they include a 250 ms menu settle and a headless browser on a shared machine.

## Hub boot used

```sh
H=$(mktemp -d -t fs13pop)                       # and fs13cold for the cold hub
HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/people.key PYTHONPATH=. .venv/bin/python <seed.py>   # populated only, before boot
HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/people.key .venv/bin/python scripts/graph_walk.py serve --port <free> --token fs13
```

Both hubs reported `DB_PATH` under their own `$H` (`probes/faces-surfaces-hubs.out.txt`). Both hubs were stopped and both HOMEs removed at the end of the lane.
