# Inventory A: every application and window, walked on the real product

Date: 2026-10-03. Base: `origin/main` @ `6ccfa4e0d` (worktree `wt-inv-a`, built bundle). Read-only: no tracked file changed.

**How.** One real hub (`scripts/graph_walk.py serve`) on a throwaway HOME (`/tmp/p13c1-inva-*`), seeded with the Phase 13 canvas seed (`story-11-canvas/harness/seed_db.py` + `rig.seed_hub`): 3 projects, 4 people, 4 meetings, decisions, notes, a brief, a workbench, one FILE destination. Playwright, a fresh browser per surface, at 1440×900 (mouse) and 393×852 (touch). Three passes: open-and-shoot (53 doors × 2 widths), main-job (48 jobs × 2 widths), a serial re-check of the doubtful ones. No engine, no microphone, no calendar, no GitHub/Jira. The owner's HOME and DB were not touched.

**Limits of this walk.** The rig hub has no recorder and no model. Jobs ran in parallel on one hub, so counts drift between shots (8 → 7 → 6 "need you"; two "Billing tracing pilot" projects are mine). Headless Chromium draws the 3D Floor in software: Floor speed and look are not judged.

Result classes: WORKS / PARTLY / BROKEN / EMPTY-ONLY (cannot judge without an engine, connector or device).
Shots are in `A-shots/`. Name = `<key>-<width>.jpg`.

## Table

| # | App / window | What it is for | Result | Defects seen | Needs | Tuesday value |
|---|---|---|---|---|---|---|
| 1 | **Chair** (Needs you, Brief, The week, Capture) | The morning screen: what needs him, the brief, the week's meetings | WORKS (Done 7→6, Ack 10→9) | "Name an owner" does nothing. SEND wells print the full folder path. "NEXT · CUTOVER DRY RUN · 15:32" for a 21:32 recording. At 393 only "Needs you" shows; Capture verbs are behind the window chip. | Engine for summaries | HIGH: his first screen |
| 2 | Intelligence | The brief, follow-through, decisions | PARTLY | Follow-through labels read "3 NOWS", "4 UNASSIGNEDS". Decisions row shows "F…" + raw id `D-19dbe10e895b`; 1 decision listed, 2 exist. Footer verbs sit under the Dock. Acknowledge/Defer/Speak ghosted. Second copy of the Chair brief. | none | MEDIUM: repeats the Chair |
| 3 | Speak | Dictate text into the focused app | EMPTY-ONLY | "DICTATION ⚠ NOT SET", "HOTKEY ⚠ UNKNOWN", "DRY RUN" on the daily face. Typed text gets no Keep/Copy verb. Journal works; rows show "820 MS". | Microphone, dictation engine, hotkey | HIGH: the core pulse |
| 4 | Ask AI | Ask a question over his data | EMPTY-ONLY | Ask is live with "No default model"; press gives HTTP 409 and "NOT ANSWERED · NO MODEL TO RUN IT". "CTX 0.0K/16.4K" twice. Field is prefilled with a prompt. | Engine | MEDIUM |
| 5 | Meetings | Find and review a meeting | WORKS (list, Open, summary, transcript, Send well, Decide) | Headline "All summaries done" over a footer "⚠ NO SUMMARY ROUTE · NO ASSIGNMENT". REVIEW and ARTIFACTS tabs show the same list as OUTCOMES. | Engine for new summaries | HIGH |
| 6 | People | His reports: what he owes, requests, 1:1s | WORKS (list → Avery → Now/Prep/1:1s tabs) | Add is ghost with no hint. | none | HIGH: three reports |
| 7 | Agents | Roster of agents and coder sessions | PARTLY | Roster shows only "New Agent OK" rows. The six agents on the Floor (Chase, Desk, Draft…) are absent. DELIVERY tab is blank. Header "CREW · SESSIONS · BLOCKED". | Coder sessions | LOW |
| 8 | Settings (front) | Menu of settings sections | WORKS | Posture row is cut by the footer. Footer "NOT SET" with no subject. "Meetings ○ SUMMARY SET ON" with no engine. "Voice ✓ LIVE" while Speak says NOT SET. | none | LOW: setup |
| 9 | Settings → Connections | GitHub, Jira, Confluence, calendar, destinations | EMPTY-ONLY | Raw folder path. "RAW 2". "NOT SET values stay on this hub" (lower case prose). | gh, acli, calendar | MEDIUM: once |
| 10 | Settings → Meetings (the only Calendar door) | Summary rule, capture, calendar, auto-record | EMPTY-ONLY | "ACTUATORS", "RAW 20". No Calendar app exists; "Connect calendar" lands here. | Calendar, engine | MEDIUM: once |
| 11 | Rhythm | How often the desk checks; the brief clock | WORKS (Run now ran) | Clock in UTC: "NEXT 03:21 · LAST 03:06 · WRITTEN 03:06" at 21:06 local. "0 ROOMS" with four rooms ticked. "122 MS". | none | LOW |
| 12 | Setup | Health checks | WORKS (Test runtime) | "NEEDS ATTENTION" over a column of PASS. Raw paths, `same_device`, eight clipped lines. | none | LOW |
| 13 | Context | Standing text every model call reads | **BROKEN** | Save → HTTP 500. The face prints `'DATABASE' OBJECT HAS NO ATTRIBUTE '_CONN'`. Cause: `holdspeak/constitutional_context.py:39,73,112` read `db._conn`; `Database` has `_connection` (`holdspeak/db/core.py:240`). "rev 0 ~0 tokens". | none | LOW today, but it cannot save at all |
| 14 | Workbenches + Workbench window | A list of work for an agent | **BROKEN** without an engine | Run is live with no model; press → "RUN FAILED · HTTP 500" (server body: "No model assignment can be frozen."). Agent picker squeezes the items to two rows. Raw path `~/.holdspeak/workbenches/workbench_…`. "Loading assignment". Title clipped by the tabs. | Engine | LOW |
| 15 | Activity | Record of activity | EMPTY-ONLY | "No activity yet" on a week with meetings and dictation. | unknown | LOW |
| 16 | Desk memory | Search everything remembered | WORKS (search "ledger" 38 → 11; Carry into brief → CARRIED) | "NO SOURCE" chip beside a live "SOURCE … Open source". | none | HIGH: find it later |
| 17 | Processes | Running and ended jobs | WORKS (read only) | Raw ids: `CHANNEL.SAVE_DESTINATION · desk:channel.save_destination · Node:hub-project-writer`. Time 10:31:22 matches no local time. "KERNEL · CURSOR 5". | none | LOW |
| 18 | Commands | Voice commands | EMPTY-ONLY (Add form opens) | "Add command" twice. "COMMANDS OFF". | Microphone | LOW |
| 19 | Models | Choose engines | EMPTY-ONLY | Seven rows "— ○ WAITING" with no next step. "Use these" ghost. | Engine | HIGH once: everything waits on it |
| 20 | Change places | Pick the wallpaper scene | WORKS | Prose descriptions. | none | LOW |
| 21 | New Project | Make a project Room | WORKS (name → Create → Room opens) | Three orange Connect verbs. Two projects may share one name. | Connectors optional | MEDIUM |
| 22 | Project Room | One project: state, people, decisions, update | WORKS (Draft update → Draft/Updates; decision row → Send; person Open → People) | "Clear here / Nothing open" while the project's meeting has an unowned action. Ask: Submit ghost, "MODEL · NOT SET", Submit label clipped. "next check 21:06" at 21:07. | Engine for Ask and model drafts | HIGH |
| 23 | Floor (3D) | All objects in space | PARTLY (not judged for look) | Labels overlap ("Ledger cutover sync" under "Reference"). Open took 8.8 s; a row double-click took ~80 s in the rig (software GL; unknown on his GPU). | GPU | MEDIUM |
| 24 | Floor list | All objects as a table | WORKS (rows open their windows) | **Get Info opens nothing.** Object menu stays all-ghost after a row is selected. Six notes all named "Thought". Thread named `th_884c5ef04396`. | none | MEDIUM |
| 25 | Delivery | Repos, sessions, terminals | EMPTY-ONLY | "NO LIVE SOURCE", `owner/repo` field. Session row opens a Terminal with raw glyphs ("░▒▓ … TERM_DBC58D7 RAW LINES 3 Δ 1S"). | Repo, GitHub, tmux | LOW |
| 26 | Panes | Pick a terminal pane | EMPTY-ONLY | "＋ SPAWN …" only. | tmux | LOW |
| 27 | Hide the menus | Focus mode | WORKS | Named as a removal. | none | LOW |
| 28 | Record orb / Live meeting | Record a meeting | EMPTY-ONLY | Rig: HTTP 501, "NOT RECORDING · NO RECORDER ON THIS HUB · OK". | Microphone, real hub | HIGH, not judged |
| 29 | Bell (Missed shade) | What he missed | WORKS | Artifacts "6h ago" beside meetings "6m ago", made in the same minute. Shade covers the Dock's Panes seat. | none | HIGH |
| 30 | Trust (Data boundaries) | What leaves the machine | WORKS (read) | "Enabled destinations None" with a saved destination. "Token: not set" while Connections says the pairing token is SET. A wall of label/value prose. | none | LOW |
| 31 | Thought window | Write and develop a thought | PARTLY | Opens 2–5 s after the press, partly behind "Needs you", title cut. Keys typed before it opens are lost. Every press makes a note named "Thought". "NO ENGINE YET". | Engine for the question | HIGH |
| 32 | Schedule recording | Set a recording for later | PARTLY | It saves, but the window stays open with a spinner. Chair shows the time 6 h early. Two mic buttons on Title. | Recorder | MEDIUM |
| 33 | Desk → New Note / Decision / Knowledge / Agent / Thread | Make an object | **BROKEN at the Chair** | Nothing opens and nothing changes on screen. Agent, Knowledge and Thread were made anyway (they show in the Floor list and the Agents roster). Note and Decision: no window; whether they were made was not checked. | none | MEDIUM |
| 34 | Desk → New Workflow / New Workbench | Make a workflow / workbench | WORKS (editor / template chooser open) | Chooser shows raw cron: "0 2 * * *", "0 7 * * 1-5". | Engine to run | LOW |
| 35 | Meeting window | One meeting | WORKS | "2h ago" for a meeting seeded minutes before (same clock defect, likely). | none | HIGH |
| 36 | Artifact window | One meeting artifact | PARTLY | "Meeting decisions" shows an empty DECISIONS section. | none | MEDIUM |
| 37 | Note window | One note | WORKS | Opens 77 px tall at 1440. | none | MEDIUM |
| 38 | Decision window | One decision; edit; send | WORKS (Edit → fields → Cancel/Done) | Full folder path in SEND. "↻karol". | none | HIGH |
| 39 | Agent window | One agent | EMPTY-ONLY | Ask ghost. "Assignment:recipe · Creates artifact". Two "No default model" blocks. | Engine | LOW |
| 40 | Knowledge window | A drawer of notes | WORKS | none seen | none | LOW |
| 41 | Palette (⌘K) | Find and open anything | WORKS ("ledger" → notes, meeting, project, verb, person) | Enter on the first row opened a Thought window, not the note (cause unknown). | none | HIGH |
| 42 | Mark menu, Go, Desk, Window menus | Doors | WORKS | 393: only Go. Go has no People, Intelligence, Live meeting. | none | MEDIUM |
| 43 | Dock | Doors and open windows | PARTLY | With five projects the Dock is wider than 1440: Places and the Record orb fall off the right edge; window chips are cut. At 393: four icons a page, no labels, three project icons look the same. | none | HIGH |
| 44 | Components (`/design/components`) | Developer catalogue | not judged | Blank for 4 s, then a "Components" window on the desk. | none | LOW |

## Counts

44 rows.

- WORKS: 22 (rows 1, 5, 6, 8, 11, 12, 16, 17, 20, 21, 22, 24, 27, 29, 30, 34, 35, 37, 38, 40, 41, 42). Most carry defects.
- PARTLY: 7 (rows 2, 7, 23, 31, 32, 36, 43).
- BROKEN: 3 (row 13 Context save; row 14 Workbench Run; row 33 Desk → New … at the Chair).
- EMPTY-ONLY: 11 (rows 3, 4, 9, 10, 15, 18, 19, 25, 26, 28, 39).
- Not judged: 1 (row 44).

## Ranked defects

1. **Context cannot save.** HTTP 500; raw Python error on the face. `holdspeak/constitutional_context.py:39,73,112` use `db._conn`, which does not exist. Shot: `A-shots/J10-context-1440.jpg`.
2. **Desk → New Note / Decision / Knowledge / Agent / Thread at the Chair opens nothing.** Objects pile up unseen. Shots: `A-shots/34-new-note-1440.jpg`, `A-shots/47-obj-workbench-1440.jpg` (the list behind shows "New Agent" ×2, "New Knowledge" ×2, "New workflow" ×2, a raw thread id).
3. **Times are wrong by the UTC offset in four places.** Scheduled 21:32 shows "15:32" on the Chair; artifacts made minutes ago read "6h ago"; Rhythm prints UTC ("LAST 03:06"); Processes prints 10:31:22. One cause is likely (naive local time read as UTC); not verified. Shots: `A-shots/J31-schedule-1440.jpg`, `A-shots/J30-thought-1440.jpg`, `A-shots/27-bell-1440.jpg`, `A-shots/J08-rhythm-1440.jpg`.
4. **Workbench Run fails with "RUN FAILED · HTTP 500".** The verb is live with no model; the real reason stays on the server. Shot: `A-shots/J11-workbench-1440.jpg`.
5. **"Name an owner" on the Chair does nothing** (four of the seven things that need him). Shot: `A-shots/J00c-chair-owner-1440.jpg`.
6. **Thought window opens late and half hidden; each press makes a note called "Thought".** Six "Thought" notes after this walk. Shots: `A-shots/J00c-chair-owner-1440.jpg` (window behind Needs you), `A-shots/J21b-get-info-1440.jpg` (the list).
7. **The Dock overflows at 1440 with five projects.** Places and the Record orb leave the screen. Shot: `A-shots/J30-thought-1440.jpg`. At 393 the Dock has no labels: `A-shots/26-dock-more-393.jpg`.
8. **Get Info opens nothing; the Object menu is all ghost with a row selected.** Shot: `A-shots/J21b-get-info-1440.jpg`.
9. **Agents shows the wrong crew.** Only "New Agent OK" rows; the real agents are missing; DELIVERY tab blank. Shot: `A-shots/J06-agents-1440.jpg`.
10. **Faces contradict each other on state.** Meetings: "All summaries done" + "NO SUMMARY ROUTE". Room: "Clear here" with an unowned action. Settings: "SUMMARY SET ON", "Voice LIVE" with nothing set. Trust: "Enabled destinations None". Desk memory: "NO SOURCE" beside a source. Shots: `A-shots/04-meetings-1440.jpg`, `A-shots/20-room-1440.jpg`, `A-shots/07-settings-1440.jpg`, `A-shots/28-trust-1440.jpg`, `A-shots/13-desk-memory-1440.jpg`.
11. Intelligence: "3 NOWS", "4 UNASSIGNEDS"; decision title cut to "F…" beside its raw id; footer under the Dock. Shots: `A-shots/J01-intelligence-1440.jpg`, `A-shots/01-intelligence-1440.jpg`.
12. Raw technical text: folder paths in every SEND well, Setup paths, Processes ids, workbench path, cron strings, "RAW 20", "KERNEL · CURSOR 5", "820 MS". Shots: `A-shots/00-chair-1440.jpg`, `A-shots/09-setup-1440.jpg`, `A-shots/14-processes-1440.jpg`, `A-shots/39-new-workbench-1440.jpg`.
13. Schedule recording stays open with a spinner after it saved. Shot: `A-shots/J31-schedule-1440.jpg`.
14. Meetings tabs REVIEW and ARTIFACTS look the same as OUTCOMES. Shot: `A-shots/J04b-meetings-tabs-1440.jpg`.
15. Artifact "Meeting decisions" has an empty DECISIONS section. Shot: `A-shots/42-obj-artifact-1440.jpg`.
16. Settings: the Posture row is cut by the footer. Shot: `A-shots/07-settings-1440.jpg`.
17. Workbench window: the agent picker leaves two item rows. Shot: `A-shots/47-obj-workbench-1440.jpg`.
18. Ask AI and Speak keep live verbs with nothing set. Shots: `A-shots/J03-ask-1440.jpg`, `A-shots/02-speak-1440.jpg`.

## Not covered

- Anything that needs an engine, a microphone, a calendar, GitHub/Jira or tmux: real dictation, TALK, a live recording, a model answer, a model-drafted update, a real send. All marked EMPTY-ONLY.
- Roadmap, Repository, Delivery Dossier: no door without a repository.
- Mission Control, Info window, Zone window, Chain and Coder pullouts, Calendar snapshot, Interview panel: not reached.
- Settings sections Assignments, Voice, Sounds & Presence, Wallpaper, System, Posture: not opened one by one (Models, Connections, Meetings were).
- Window chrome (drag, resize, snap, Overview, switcher, reload memory): Overview was opened, nothing was measured.
- 393: every door was opened and shot, but only the Chair, Meetings, Room, Speak and Dock shots were read. The Chair's Brief, The week and Capture windows at 393 were not reached.
- The 3D Floor's look and speed (software GL in the rig).
- One event to know: the rig's Delivery board listed tmux sessions that look like the machine's real ones ("ccgram %0", "hs10605_kill_62847"). I opened one Terminal view to shoot it and sent no keys. Whether the rig's tmux isolation leaks is unknown.
