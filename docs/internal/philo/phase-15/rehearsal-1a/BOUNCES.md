# Rehearsal 1, part A: bounces

PHILO Phase 15, lane 02, part A. Walked 2026-10-07 10:28 to 11:10 MDT on `origin/main` 859e71dd6
(worktree `wt-p15-rehearsal`, detached). Shots: `.tmp/day-one-shots/<step>-<width>.png` (76 files).
Nothing tracked was changed. No tests were run.

## The rig, and where it differs from the owner's day

- HOME A (1440 walk, then the 393 Chair pass on the same desk) and HOME B (393 first run and
  Concierge), each `mktemp -d`. Both removed at the end.
- `HF_HOME=~/.cache/huggingface`, `HF_HUB_OFFLINE=1`. Whisper `base` (MLX) came from that cache.
- LAN engine `http://192.168.1.43:8080`, `qwen3.8-27b`, key `local`. No other egress.
- Differences, so a reader does not count them as bounces:
  - `holdspeak web --no-open`, not bare `holdspeak`: bare `holdspeak` opens the owner's real browser.
  - `HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$HOME/people.key`: without it, adding a person writes the real
    macOS Keychain (`holdspeak/people/store.py:486-492`). This causes doctor's People keystore WARN.
  - The meaning-search model (`nomic-embed-text-v1.5.Q8_0.gguf`, 146 MB) was copied from the real
    `~/.cache/holdspeak-models/embed/` into the isolated HOME, so it was not downloaded. No download
    time was measured.
  - gh / acli "NO SIGN-IN" and the agents' "SIGN-IN UNKNOWN" come from the isolated HOME.
  - Headless Chromium over CDP, driven by the main checkout's venv (Playwright is a dev extra, so the
    worktree's `uv sync` does not install it). No microphone, so First words was skipped.
- Not walked in part A: Install hooks (no agents in part A); the §1.4 OFF/ON check; killing the hub
  in the middle of an import; the §3.4 variants with Capture moved. Set up local AI was NOT pressed:
  it downloads 2.9 GB.

## Timings

| What | Time |
|---|---|
| `uv sync` in the fresh worktree | 9.4 s |
| `uv run holdspeak doctor`, cold, no hub | 10.7 s |
| `uv run holdspeak doctor`, warm, hub running | 1.9 s |
| Concierge Check of the .43 box | 0.5 s (READY, qwen3.8-27b) |
| Meaning search, first index (10 items, local embedder) | 17 s, INDEXING 0 OF 10 to ON |
| WAV import, 35 s fixture, to final state | about 5 s (Whisper: 10:52:03 to 10:52:06, two 30 s windows) |
| Run summary on the LAN model | 8 s (face: RAN · 8 S); 9.6 s from the press to MEETING READY |

## The LAN summary, verbatim

Input: `tests/fixtures/philo3_architect_meeting.wav` (35 s, synthetic; script in
`tests/fixtures/philo3_architect_meeting.txt`: three decisions, three action items).

> Synthetic architect meeting covering three decisions: adopting SQ-like for the local meeting ledger (Mayyachan to write migration plan by Friday), keeping summary retrieval on the local desk after a hub restart (Leo Martinez to test on Tuesday), and using a recorded provider reply for isolated rig tests (Priya Shah). A named failure offense marker was noted before ship.

Topics: Local meeting ledger · Summary retrieval after hub restart · Recorded provider reply for
isolated rig tests · Named failure offense before ship.

Read as a Senior Architect: short and in a neutral voice, and it does not invent facts. It is only
as good as the transcript. It repeats the ASR errors ("SQ-like" for SQLite, "Mayyachan" for Maya
Chen, "named failure offense" for "named failure fence") and does not mark them as uncertain. Priya
Shah's action ("add the named failure fence before ship") is gone, because the transcript lost it
(B01). It says "three decisions", but the product records no decision (B02).

## The five worst

1. **B01 LIES**: the transcript has "finally" about 250 times and lost an action item. The face says "299 WORDS" and gives no warning.
2. **B02 LIES**: a meeting never yields a decision proposal on day one. The summary says "three decisions"; Decisions is empty; Review says "Not run".
3. **B03 STOPS**: there is no Confirm for a meeting's action item when the meeting is not in a Project. Review opens a panel with only glyph buttons and no Confirm.
4. **B04 LIES**: the Brief says "No changes" after a full day. A second Generate returns the 10:50 brief again. It is titled "Monday Brief" on a Wednesday.
5. **B05 LIES**: the Concierge proposes the LAN box as READY for seven groups. After "Use these", the same screen marks four of those groups "TOOL INCOMPATIBLE". Settings says "No default model".

## Bounces

| # | Step · width | What happened | What the owner would feel | Shot | Severity | Start from |
|---|---|---|---|---|---|---|
| B01 | §3.2 · 1440 | Import cuts the audio into hard 30 s windows. Whisper base looped at the end of window 1: "Owner, Priya Shah. Action. finally finally …" (about 250 times). The third action item and its due date are lost. The meeting row says "299 WORDS" (the script is about 100 words). No warning. The transcript wall is shown in full on the record. | "It made up garbage and called it my meeting." He stops trusting transcripts. | `3.3-meeting-open-1440.png`, `3.5-decide-pressed-1440.png` | LIES | `holdspeak/meeting_import.py:60` (`DEFAULT_WINDOW_SECONDS = 30.0`), `:352` (hard slices); `holdspeak/transcribe.py:457` (mlx transcribe with default decode options, no repetition guard) |
| B02 | §3.3 / §3.5 · 1440 | No decision proposal. The summary schema has `topics`, `action_items`, `summary` only. The `decision_capture` plugin chain is off by default, and `plugin_runs` has 0 rows. The summary text says "three decisions". The Intelligence DECISIONS tab says "No decisions match this search". The meeting's REVIEW tab says "Not run · PROPOSALS · NOT RUN" under a header that says "RAN · 8 S". | "It heard three decisions and kept none." | `3.5-intel-decisions-1440.png`, `3.5-meetings-review-tab-1440.png` | LIES | `holdspeak/intel/parsing.py:20-55`; `holdspeak/config/meeting.py:95` (`intent_router_enabled: bool = False`); `web/src/pages/cores/history/reviewModel.ts:278` |
| B03 | §3.5 · 1440 | No Confirm for an action item from a meeting that is not in a Project. The Needs row shows "TO REVIEW · Review". Review opens a small Intelligence window on FOLLOW-THROUGH, with "NOW · NO ITEMS" first. On the selected row there are only 16 px glyphs (✓ Mark done, ↷ Dismiss, ◷ Snooze, ⇢ Delegate, ↺ Reopen) and "SOURCE MOMENT UNAVAILABLE", although the transcript exists. Confirm exists only for Project proposals. Not done: no action item was confirmed. | "Where is Confirm? What do these symbols do?" He gives up on the step. | `3.5-review-1-1440.png`, `3.5-row-selected-1440.png` | STOPS | `web/src/desk/needs/needsFace.ts:294-312` (confirm only with `proposalId`), `:322-328` (`_toReview` → review); `web/src/desk/pullouts/views/FollowThroughView.tsx:303-307` |
| B04 | §2.3 · 1440 + 393 | The day-one Brief says "No changes". At 11:08, after a meeting, a decision, three actions, a person and a Project, Generate returned the same 10:50 brief. It is titled "Monday Brief" on a Wednesday. The header says "OCT 05 – 07"; the body says "Period: 2026-10-06 – 2026-10-07". | "The brief is blind and stale. Generate does nothing." | `2.3-brief-generated-1440.png`, `2.3-brief-regenerated-393.png` | LIES | `holdspeak/services/monday_brief_service.py:420` ("Generate or return the existing brief for the current local date"); `holdspeak/services/document_sources.py:331` |
| B05 | §1.5 / §1.6 · 1440 | After "Use this for summaries", the Set proposes Qwen3.8 27B (READY) for six groups. After "Use these" (200), a "TO REPAIR 1" block says: 192.168.1.43:8080 for THOUGHTS & NOTES, WRITING & DICTATION, AGENTS & TOOLS, BACKGROUND, "TOOL INCOMPATIBLE · This engine cannot give a structured result". The Set below still shows those groups READY. The check reads manifest claims; it does not probe the server. Settings (Dock) says "No default model", "Assignments NO DEFAULT", "Voice NO ENGINE". | "Is my engine set up or not? Two screens disagree." | `1.6-use-these-1440.png`, `1.6-settings-1440.png` | LIES | `holdspeak/services/inference_assignment_service.py:1866-1868`; `holdspeak/services/concierge_service.py:1021`; Settings headline: file not located |
| B06 | §1.5 · 1440 + 393 | The Concierge proposes "Quick local Qwen" (a 2.6 GB chat LLM that is not downloaded, WAITING) for **Speech recognition**. Whisper base is on this device: first run shows Speech "ON DEVICE". | "A chat model for speech? Is speech broken?" | `1.5-concierge-open-1440.png`, `1.6-models-after-assign-1440.png` | LIES | `holdspeak/services/concierge_service.py:762-781` (no `best_whisper` → falls back to the chat preset) |
| B07 | §2.4 · 1440 | The week, opened from Window ▸ Chair on a fresh desk with no calendar and no meetings, is an empty window. `chair-window-body-week` has no children. There is no empty state and no "Connect calendar". At 393, after the import, it does show the meeting. | "Broken window." | `2.4-the-week-1440.png`, `2.4-the-week-5s-1440.png` | CONFUSES | `web/src/desk/chair/ChairHome.tsx:1331-1385` (every section is conditional) |
| B08 | §1.2 · terminal | Before the first launch: "Summary: 28 passed, 4 warnings, 0 failed", then "Running hub … 4 FAIL [Errno 61] Connection refused" with no "start holdspeak first" line. LLM runtime WARN: the missing file is `Qwen3.5-4B-Q4_K_M.gguf`, but the fix tells him to download `bartowski/Qwen3.5-4B-Instruct-GGUF Qwen3.5-4B-Instruct-Q4_K_M.gguf` by hand with `huggingface-cli` (a different file; the product has Set up local AI). With the hub running: `runtime-preflight FAIL Model not found` for a model he did not choose. Rows in developer words: MIR routing, MIR telemetry, Structured-output compilation, LLM runtime counters, Mesh edges, Project context "+ KB", "Runs on destinations: This device: this device". | "Did install fail? Which file do I need?" | `.tmp/day-one/doctor-nohub.txt`, `doctor-hub.txt` | CONFUSES | `holdspeak/plugins/dictation/guidance.py:60-61`; `holdspeak/doctor.py:409` (hub section); `holdspeak/commands/doctor.py:913-924` (MIR rows) |
| B09 | §1.3 / §1.4 · 1440 + 393 | Set up local AI is one 2.9 GB button: Whisper (on device), meaning search 146 MB, and the 2.7 GB chat model. He cannot take meaning search alone here. First run cannot add his LAN box: the engine scan covers loopback only, and there is no "Add an engine" on this page. He must press "Continue later" and find Settings ▸ Models (or the Needs row) himself. | "I have a 27B box on my network. Why download 2.7 GB?" | `1.3-firstrun-full-1440.png`, `1.3-firstrun-full-393.png` | CONFUSES | `web/src/desk/firstrun/FirstRun.tsx:160-163`; `holdspeak/services/inference_default_service.py:8-9` (loopback only) |
| B10 | §1.5 · 1440 | After "Use this for summaries", the Models window closes itself and shows no receipt. The menu-bar chip changes to "→ EXTERNAL REACH ENABLED" for a box on his own LAN (later "→ 192.168.1.43:8080"). | "Did it take? What reach did I just enable?" | `1.5-after-use-1440.png` | CONFUSES | `web/src/desk/setup.ts:122-126` |
| B11 | §2.2 · 1440 + 393 | The headline count does not match the rows: "1 need you" over 2 rows; "Nothing needs you" over a Calendar row; "3 need you" over 4; "4 need you" over 5. Grammar: "1 need you". | "Which number is true?" | `2.2-needs-you-1440.png`, `1.5-after-use-1440.png`, `2.2-needs-you-393.png` | CONFUSES | `web/src/desk/needs/needsFace.ts:507-511` |
| B12 | §2.2 · 393 | The decision he typed by hand ("Use SQLite for the local meeting ledger") appears in Needs you as "TO REVIEW · Review". The rows do not say decision or action: every proposal row is "TO REVIEW · Review". | "I just decided that. Why review it?" | `2.2-needs-you-393.png` | CONFUSES | `web/src/desk/needs/needsFace.ts:289-292` |
| B13 | §3.4 · 1440 | The aftercare card says "3 open · Open proposals". The press removes the card and the window stays on OUTCOMES. The target (REVIEW) says "Not run". The three "open" items are summary action items, not proposals. | "It said 3 open proposals, then showed me nothing." | `3.4-aftercare-1440.png`, `3.5-proposals-1440.png` | LIES | `web/src/components/AmbientLayer.tsx:239-248` |
| B14 | §3.2 · 1440 | Import: at 1.5 s, before transcription, the window flashes "All summaries done · SAVED". Then the row says "OFF" for a summary that has not run, while Settings says "SUMMARY SET ON · AFTER EVERY MEETING". Import does not run the summary; the API says so, the face says "OFF". | "Summaries are on, so why OFF?" | `3.2-import-done-1440.png`, `1.6-settings-1440.png` | CONFUSES | `web/src/pages/cores/history/helpers.ts:281`; `web/src/pages/cores/history/CatalogRail.tsx:160` |
| B15 | §3.3 · 1440 | The record footer keeps "QUEUED 10:59" after the summary RAN. | Small doubt. | `3.3-run-end-1440.png` | LIES | Meetings window footer (file not located) |
| B16 | §2.3 · 1440 | Window ▸ Chair ▸ Brief opens the Brief BEHIND the Models and Settings windows, not in front. | "Nothing happened." | `2.3-brief-open-1440.png` | CONFUSES | window manager raise-on-open (file not located) |
| B17 | §1.3 · 1440 + 393 | Agents card: "2 FOUND" over three rows (Claude Code, Codex, tmux). | Small doubt. | `1.3-firstrun-full-1440.png` | CONFUSES | `web/src/desk/firstrun/AgentsCard.tsx:126` |
| B18 | §1.3 / §1.5 | Sizes disagree between faces: Chat 2.7 GB (first run) vs 2.6 GB (Concierge); meaning search 146 MB vs 139 MB. | Small doubt. | `1.3-firstrun-top-1440.png`, `1.5-concierge-open-1440.png` | LIES | decimal vs binary units: `FirstRun.tsx:162` `formatBytes` vs the Concierge size label |
| B19 | §2.1 · 1440 + 393 | Four Dock items have no sprite, only a text glyph: Intelligence ◆, Desk memory ◎, Delivery ▤, Panes ⧉ (393: ◆). A hidden Dock button is labelled "More AppIcons". | Windows 1.0 next to the pixel sprites. | `2.1-chair-arrival-1440.png`, `2.1-chair-393.png` | UGLY | Dock items with `img=NONE` (Dock.tsx; sprite map not located) |
| B20 | §2.1 · 1440 + 393 | The first screen has ten seed notes, including "Effect guard" and "Egress guard". | "What are guards? Do I need to read ten notes?" | `2.1-chair-arrival-1440.png` | CONFUSES | `holdspeak/services/thread_modes.py:365,383` |
| B21 | §2.1 / §2.2 · 393 | The Go menu has 22 entries (Processes, Commands, Workbenches, Context, Activity, Setup, Rhythm …), with ⌘ keycaps on a phone. The Desk menu has nine "New" kinds (Knowledge, Workflow, Workbench, Thread …). | Tenet 3: "a million interfaces". | `2.2-go-menu-393.png`, `4.2-desk-menu-1440.png` | CONFUSES | `web/src/desk/DeskMenuBar.tsx:43-65` (Go) |
| B22 | §3.3 · 1440 | The record opens in a narrow right column of the Meetings window, and the summary is cut. Zoomed, the left list is a 400 px empty black column. | Cramped, then empty. | `3.3-meeting-open-1440.png`, `3.5-decide-pressed-1440.png` | UGLY | `web/src/pages/cores/history/` layout |
| B23 | §3.3 / §2.3 | The Send well is open by default on the record and the Brief. It prints the raw `/private/var/folders/…/Documents/HoldSpeak/Sent` path under "~/Documents/HoldSpeak/Sent". The preview renders the filename's underscores as italics: "philo3*architect*meeting". | Noise; it looks broken. | `3.5-needs-after-summary-1440.png`, `2.3-brief-generated-1440.png` | UGLY | channel preview markdown (file not located) |
| B24 | §3.5 · 1440 | The Intelligence window opens at about 390×300 px. Its tab list (BACK / BRIEF / FOLLOW-THROUGH / DECISIONS) fills most of the window, and the items are below the fold. | He must find Zoom first. | `3.5-review-1-1440.png` | UGLY | Intelligence window default size (file not located) |
| B25 | §4.2 · 1440 | Create opens the Room, not the drawer the script names. An empty new Project says "Clear here · ON TRACK". The receipt reads "CREATE FROM SETUP". The "Steward" button has no explanation. | "On track with what?" | `4.2-project-created-1440.png` | CONFUSES | Room headline for a Project with no sources (file not located) |
| B26 | §7.1 · 1440 | The Parked icon opens Meetings, not a Parked drawer (gap #14; lane 04 is not on main). After Park, Meetings says "No meetings yet" next to a "PARKED 1" chip. Restore is reached only through that chip. | "Where did my meeting go?" | `7.1-parked-1440.png`, `7.1-parked-drawer-1440.png` | CONFUSES | DAY-ONE gap #14 (lane 04) |
| B27 | §1.5 · 393 | The Concierge footer receipt "7 GROUPS · 1 ENGINE · 7 WAITING" runs into Cancel ("7 WAITCancel"): receipt x 8..253, Cancel x 221. | Broken-looking footer. | `1.5-add-checked-393.png` | UGLY | known (DAY-ONE §1.5); Concierge footer CSS |
| B28 | §2.4 · 393 | In The week, the topic chips ("…ISOLATED RIG TES") and the Open button are cut at the right edge. | Sloppy. | `2.4-the-week-393.png` | UGLY | `ChairHome.tsx` MeetingsSection at 393 |
| B29 | §1.3 · 1440 + 393 | Connections line: "GH · NO SIGN-IN ACLI · NO SIGN-IN". The two tokens run together, so it reads "NO SIGN-IN ACLI". | Small. | `1.3-firstrun-top-1440.png` | UGLY | `web/src/desk/firstrun/ConnectionsCard.tsx:111-112` |
| B30 | §2.1 · 393 | A desk label breaks inside a word: "philo3_arc / hitect_me…". The meeting title is the raw filename with underscores; the attendee is "Recording". | Small. | `2.1-chair-393.png` | UGLY | import title from the filename (`holdspeak/meeting_import.py`) |

## Unknown (seen, cause not verified)

- After Meaning search reached ON, one page screenshot took 6.5 minutes (10:37:50 to 10:44:23). The next calls took 0.1 s. The hub log has nothing at that time. Cause unverified: a headless renderer stall, or a blocked page main thread.
- B05's effect: whether "TOOL INCOMPATIBLE" stops memory facts, Cadence drafts or Thought interviews in practice. Not exercised in part A.
- "Use these" returned 200 although Speech recognition was WAITING, and the service refuses a WAITING group with 409 (`holdspeak/services/concierge_service.py:1558-1570`). What the face sent for that group is not verified.
- The first press on the Models window close box did not close it; the second press did. Not verified whether the first press only focused the window.
- 393 "seventh Needs row under the Dock": this desk had five rows. The fifth row ended at y=792, above the Dock at y=796. Seven rows not tested.
- First words / the real microphone: not exercised (headless).
- The hub polls loopback engine discovery every 30 s and logs four "Connection refused" lines each time, also after an engine is chosen (log noise, not on a face).

## What worked cleanly

- `uv sync` in 9.4 s. `holdspeak doctor` runs the whole list (mic, hotkey, BlackHole, Coding agents, connectors) and then the hub checks (#966).
- First run at both widths: one scrolling page with no side scroll at 393. You saves the name and aliases ("SET") with no Save button. Continue later goes to the desk.
- Needs you on a fresh desk shows exactly the two true rows (Calendar, No engine for summaries). After "Use this for summaries" the engine row goes, as #967 intends.
- The Concierge's Add an engine has a Key field (#966). Check said READY · qwen3.8-27b in 0.5 s.
- Meaning search: Turn on → INDEXING 0 OF 10 → ON in 17 s, on this device.
- WAV import reaches a final state in about 5 s and keeps it (#968). The 393 Chair screen then shows the meeting.
- Run summary on the LAN model: 8 s, one summary slab, MEETING READY card, Needs you updates to the three action items.
- Manual decision: Decide → title → Save → `POST /api/decisions 201`. It shows on the desk as a decision object.
- People: Set up People, type "Priya Nair", Add (201). Her card opens, and she is on the desk as an icon.
- Project through the Door: type the outcome, Create Project, in one press with no connectors. The Project drawer is on the desk; the Room answers on the LAN model.
- Park and Restore round trip (`DELETE` then `POST …/restore`, both 200). The Needs count follows (4 → 1 → 4).
- 393: every desk sprite loaded; Go ▸ Needs you / Brief / The week work; the last Needs row is reachable above the Dock.
- Window ▸ Chair ▸ submenu works with the mouse.
