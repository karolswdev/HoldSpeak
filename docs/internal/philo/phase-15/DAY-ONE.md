# Day One — the owner's first real day with HoldSpeak (v1, the rehearsal script)

Version 1, written 2026-10-07 by Muad'Dib from `DAY-ONE-INVENTORY.md` (main `b88fc3f7b`
plus lanes 01, 02 and 03 of Phase 15). This version is the script the rehearsal walks.
Version 2, after rehearsal 1 and the second morning, is the runbook the owner follows:
one screen per step, the shot beside it, ASD-STE100.

Each step names: the face; the gesture at 1440 and at 393; the proof that covers it today;
the state (WORKS / UNVERIFIED / KNOWN BROKEN / NEEDS REAL METAL); and, for the rehearsal,
what to look at. The states are the inventory's, updated for the lanes merged since.

## The rig for rehearsal 1

- A fresh isolated `HOME` (`mktemp -d`); `HF_HOME` at the real Whisper cache with
  `HF_HUB_OFFLINE=1` (the model is under the real HOME; nothing else is).
- Engines: the LAN model at `http://192.168.1.43:8080` (`qwen3.8-27b`, key `local`) set as
  the global default through the Concierge; Whisper `base` for speech; the local embedder for
  meaning search.
- Agents: a real Claude Code and a real Codex under an ISOLATED `CLAUDE_CONFIG_DIR` /
  `CODEX_HOME` login or API keys. Never the owner's keychain or `auth.json` (law from
  handover XXXIII; the R1 walk broke it and said so).
- Egress: a throwaway GitHub repository under the owner's account for the agent's PR; a
  Resend test key for email; the built-in Folder destination for the first send.
- Both widths for every face: 1440 and 393. One shot per step into
  `docs/internal/philo/phase-15/day-one-shots/<step>-<width>.png`.
- Every bounce becomes a row in `BOUNCES.md` (step, what happened, the shot, the lane that
  pays it) the same day.

## 1. Install and first launch

### 1.1 Install
- Face: a terminal. `git clone`, `uv venv && source .venv/bin/activate`, `uv pip install -e .`,
  `holdspeak` (README). Python 3.10+, uv, Node 22.12+, a C++ compiler. No PyPI or brew install.
- Gesture: CLI. `holdspeak` binds 127.0.0.1:8765 (or a free port), prints a token URL, opens
  the browser.
- Proof: `tests/unit/test_phase200_first_value.py`; the clean-venv install is `slow` (FULL only).
- State: UNVERIFIED on a clean Mac. Rehearsal: time the install; the llama-cpp build is the
  heaviest step.

### 1.2 `holdspeak doctor`
- Face: a terminal.
- Proof: `tests/unit/test_doctor_cli_one_list.py` (#966): the CLI runs the same list the
  Setup page runs (Coding agents, mic, hotkey, connectors), honours `--strict` and
  `--connectors`, then the 10 hub checks.
- State: WORKS (#966). Rehearsal: read every row; a WARN here is a first-day gap.

### 1.3 The first-value gate
- Face: `/` → `chair-first-value` → `firstrun`: Set up local AI, You (name, aliases), First
  words (dictate one sentence → Keep as note), Calendar, Connections, Agents (Install hooks,
  optional), Found engines, Ready. "Continue later" at the foot.
- Gesture: one scrolling page at both widths.
- Proof: `test_firstrun_one_screen_glass.py`, `test_firstrun_heard_glass.py`,
  `test_hs202_02_first_use_glass.py`, `tests/integration/test_setup_first_value_journey.py`;
  atlas `case.j1.*`.
- State: WORKS on glass (speech is a double). NEEDS REAL METAL: the physical mic, real
  inference. Rehearsal: dictate the real sentence; press Install hooks (no glass test presses
  it; no testid on the button).

### 1.4 Engines: the default
- Set up local AI downloads Whisper `base`, the embedder and the 4B starter model, assigns a
  responding LOOPBACK engine as the global default, turns meaning search on. A LAN or cloud
  engine is never auto-assigned; it is a proposal that needs "Use it".
- State: WORKS for the loopback default. The false "No engine for summaries" row after the
  default is assigned is FIXED in #967 (the blocker asks the route policy; an explicit OFF
  holds). Rehearsal: after the default is assigned, Needs you and the Brief show no engine
  row; turn summaries OFF in the Concierge and see OFF everywhere; turn them back on.

### 1.5 Engines: the LAN model and keys
- Face: Settings › Models = the Concierge (`/models`): Add an engine → Server address, Key
  (optional, #966), Check → READY / UNREACHABLE / KEY REQUIRED / KEY INVALID, Use this for
  summaries.
- Gesture: 1440 the window; 393 the stacked Concierge.
- Proof: `test_hs170_concierge_glass.py`, `test_concierge_key_boundary.py` (#966); atlas
  `case.j3.*` (the `assigned_ready` case blocks before the Concierge: old entry path, open).
- State: WORKS for the keyless .43 box (it takes any key); the keyed path is proven on a
  stub. KNOWN: an Anthropic key does nothing (no execution adapter); the 393 footer receipt
  overlaps Cancel. Rehearsal: add the .43 box with key `local`, Check, Use this for
  summaries; at 393 look at the footer.

### 1.6 Meaning search
- Face: the Concierge's Meaning search row (OFF / DOWNLOADING / INDEXING / ON).
- Proof: `test_meaning_search_row_glass.py`; the real-model case needs
  `HOLDSPEAK_MEMORY_EMBED_MODEL`.
- State: WORKS; real indexing NEEDS REAL METAL (new items take up to 120 s). Rehearsal: turn
  it on, time the first index.

## 2. The Morning

### 2.1 Arrival on the Chair screen
- Face: `chair-desk` with the screen: Project drawers, People, Conductor, Needs you, Parked,
  loose objects; TALK at the foot-left (1440). The Chair windows start closed.
- Gesture: 1440 Window ▸ Chair ▸ name or the icon; 393 Go ▸ Needs you / Brief / The week.
- Proof: `test_philo14_a1_fresh_arrival_glass.py` (waits for the sprites, #959),
  `test_philo13_11_chair_glass.py`, `test_philo13_17_phone_desk_glass.py`.
- State: WORKS. Open: the long desk scrolls uncapped; ~40 membership GETs on a 20-Project
  desk. Rehearsal: the first screen he sees; every icon readable at 393.

### 2.2 Needs you
- Face: the Needs drawer: one object one row; a row's Project button opens the drawer (#965);
  a proposal row opens the Room with that proposal selected; agent asks, held calls
  (Deny + Open; never Approve on a cut command), PRs, decisions, commitments, engine blockers,
  failed summaries, ARMED / NEXT, Connect calendar. Dock badge = count.
- Proof: `test_philo13_03_needs_you_glass.py`, `test_needs_you_means_you_glass.py`,
  `test_conductor_r1_gate_row_glass.py`, `test_philo14_a2_drawer_glass.py`,
  `test_philo14_a2b_paths_glass.py`.
- State: WORKS (#935, #965, #967). Open: at 393 the seventh row sits under the Dock (scroll
  reach unverified). Rehearsal: seven or more rows at 393; reach the last one.

### 2.3 The Brief
- Face: the `chair:brief` window; Generate; rows; handled; receipt; standing pages; "Add to
  1:1 agenda". One brief per local day, deterministic, no model.
- Proof: `test_philo11_05a_brief_decision_send_glass.py`, `test_hs175_rhythm_brief_glass.py`;
  atlas `case.j10.*` (the five empty-brief cases set up an engine first, #967).
- State: WORKS on a press. KNOWN: the Brief does not generate itself (the cadence loop is off
  by default; the Heartbeat holds 22:00–08:00). Rehearsal: the first morning starts with
  Generate; decide whether day one should find the brief already there.

### 2.4 The week
- Face: the `chair:week` window: the strip, this week, meetings, thoughts. Data from the Door.
- Proof: `test_hs175_arrival_glass.py`; atlas `p13.dock.needs_you_week`.
- State: WORKS with a seeded calendar; a real calendar NEEDS REAL METAL (EventKit prompt and
  read unverified). Rehearsal: connect the real calendar; see this week.

## 3. A meeting

### 3.1 Schedule and one-tap record
- Face: the Dock's Record orb; Capture's Record meeting / Schedule; Needs you's ARMED / NEXT
  with Cancel / Retry. Calendar auto-record is OFF by default.
- Proof: `test_hs144_door_glass.py` (schedule round trip), `test_philo13_16_capture_glass.py`;
  `test_hs147_one_tap_glass.py` is RETIRED.
- State: schedule / cancel WORKS; live recording UNVERIFIED (no browser-audio rig); the mic,
  BlackHole and permissions NEEDS REAL METAL. Rehearsal: record a real two-minute meeting from
  the orb at 1440 and from the Dock at 393.

### 3.2 Import a WAV
- Face: Meetings window → Import, or drop a file on the desk. 202, then "Transcribing — window
  N of M". Import does not auto-run the summary.
- Proof: `test_hs202_first_use_smoke.py` (re-anchored, strict mode green, #968),
  `tests/unit/test_philo15_03_import_final_status.py`, the real-hub import tests; atlas
  `case.j4.meetings_import.imported`, `case.j5.meeting_open.*`.
- State: WORKS (#968): an import always reaches a final status (failed with its cause, or
  complete), sync keeps it, an import interrupted by a restart is marked failed on the next
  start. Open: two j5 cases block at the old engine-setup step. Rehearsal: import a real WAV;
  kill the hub mid-import once and restart.

### 3.3 Transcription and summary
- Face: Run intelligence (`arrival-run-intel` / the record's button) → the summary slab (one
  render, #968), the balanced plugin profile + project detector.
- Proof: `test_hs201_summary_face_glass.py`, `test_hs201_summary_trust_glass.py`,
  `test_hs202_first_use_smoke.py`; atlas `case.j6.*`.
- State: WORKS with doubles; the LAN model's summary NEEDS REAL METAL (the first real-LAN
  closure s2 walk drew no summary in 300 s; the second passed). Rehearsal: the real summary
  on the real meeting; time it; read it as a Senior Architect would.

### 3.4 The aftercare card
- Face: MEETING READY in Capture's slot (Capture opens for it at both widths, #954); Open
  proposals, Dismiss.
- Proof: `test_philo14_a1c_aftercare_capture_glass.py`; atlas `philo603.toast.*`, `j6`, `s2`.
- State: WORKS. Open: two Floor toast cases block on setup. Rehearsal: let the card land
  while Capture is moved; while Meetings is in front.

### 3.5 Decisions and action items
- Face: proposals from the extractors; Confirm on the Needs row, the record, the Room; a
  proposal row opens the Room with the proposal selected (#965).
- Proof: `test_hs172_meeting_glass.py`, `test_hs200_meeting_outcomes_glass.py`,
  `test_philo13_08_decide_glass.py`, `test_philo14_a2b_paths_glass.py`.
- State: WORKS on fixtures; extraction quality on the LAN model NEEDS REAL METAL. Rehearsal:
  confirm one decision and one action item from the real summary.

## 4. People and Projects

### 4.1 Add a person
- Face: the People window; New relationship → Enter or Add; 1:1 prep lens.
- Gesture: 1440 the People drawer icon (opens People, lane 04); 393 the palette or menu verb.
- Proof: `test_hs172_people_glass.py`, `test_hs200_people_preparation_glass.py`,
  `test_philo13_09_prep_glass.py`.
- State: WORKS. Open: person memory pages do not exist. Rehearsal: add one real report.

### 4.2 Make a Project
- Face: New project → the Door (outcome, rows, connect) → Create → the DRAWER (icons or list,
  Get Info, Park, Hand, the Room one press away).
- Proof: `test_hs169_door_glass.py`, `test_philo14_a2_drawer_glass.py`,
  `test_philo14_a2b_paths_glass.py`, `test_hs169_room_glass.py`.
- State: WORKS. Open: the drawer's LIST view has no drag. Rehearsal: a real Project of his
  with its GitHub repo.

### 4.3 Connectors
- Face: Settings › Connections: GitHub (`gh`), Jira (`acli`, site + email), Confluence,
  Calendar (EventKit or ICS).
- Proof: `test_hs168_connections_glass.py`, `test_hs161_github_glass.py`,
  `test_hs166_jira_glass.py`, `test_hs146_calendar_snapshot_glass.py`; tests refuse the real
  CLIs.
- State: NEEDS REAL METAL (gh / acli auth, EventKit). KNOWN: a sign-in saves no Send
  destination; calendar denied had no way forward (lane 04 adds the System Settings verb); a
  GitHub Enterprise egress host reads github.com. Rehearsal: connect gh and the calendar for
  real; deny the calendar once and recover.

## 5. The Conductor

### 5.1 Install hooks
- Face: the first-run Agents card, or the Conductor drawer (Dock ⌘3): Copy install / Install
  hooks. CLI `holdspeak agent-hook install`.
- Proof: `tests/unit/test_onboarding_agents.py`, `test_conductor_r3_codex.py`; no glass test
  presses Install; no testid.
- State: UNVERIFIED on glass; NEEDS REAL METAL (Codex trust hash; live hook delivery never
  observed on a real desk). Rehearsal: press it; read the receipt; `holdspeak doctor` shows
  Coding agents green.

### 5.2 Hand to agent
- Face: drag an object from the screen or a drawer onto the Conductor or an agent icon (1440);
  the drawer's Hand verb; the Chair row's verb. YOLO = ConfirmLine (item → agent, CLAUDE CODE ·
  YOLO · hs/<branch>, egress chip, Brief ▸ / Cancel / Hand); Secure / Normal = HandSheet. 393:
  the verb opens the confirm line.
- Proof: `test_philo14_c3_drop_to_hand_glass.py`, `tests/unit/test_agent_hand*.py`.
- State: WORKS with doubles; a real launch NEEDS REAL METAL. Open: Door / Room row verbs and
  ⌘K open the sheet even in YOLO; the new agent icon can sit behind the open drawer; no issue
  object on the screen. Rehearsal: hand one real small action item from his Project to Claude
  Code in YOLO; then one to Codex.

### 5.3 The lane
- Face: the agent's window: the station track (BRIEF · WORK · COMMIT · PR · HELD · ASKS ·
  MERGE), the question with voice answer (`wait_id` must be current), Deny / Approve on a held
  call (a cut command: Deny + Raw only), Re-brief, Stop (two presses), Raw (the tmux pane).
  From Needs you: answer / approve / deny on the row.
- Proof: `test_philo14_c2_lane_glass.py`, `test_philo14_c2_lane_actions_glass.py`,
  `test_conductor_r1_gate_row_glass.py`, `tests/unit/test_philo14_c0_launch_lane.py`.
- State: WORKS with doubles. KNOWN: the draft chip reads NOT SET without a Cadence-drafts
  model, so YOLO answers nothing routine and every question reaches Needs you (the global
  default does not feed capability-only services); BRIEF shows a word count; Files changed
  shows names only. The real loop ran once (R1) with non-isolated credentials. Rehearsal:
  answer one real question from the lane and one from Needs you; deny one held call and
  approve one; assign the LAN model to Cadence drafts and watch a routine question get
  answered with a receipt.

### 5.4 The PR, the merge, the update row
- Face: the lane's PR card (Open PR → GITHUB.COM); the Room's merge receipt; the weekly
  update's `Merged: <title> (PR #n)` row (`report_merged_prs` on).
- Proof: vitest and unit only; NO glass test reads the merge receipt or the Merged row; no
  atlas Conductor case; merges proven with a fake gh.
- State: UNVERIFIED / NEEDS REAL METAL. Rehearsal: let the agent open the real PR on the
  throwaway repo; merge it on GitHub; watch the Heartbeat close the origin and the receipt
  land in the Room and in the update.

## 6. The weekly update and Send
- Face: the Room → Updates → Draft (deterministic or model) → the editor → Publish → the Send
  well (destination row, Check, preview, Sent). Destinations: Folder (built-in), GitHub
  comment, Jira comment, Confluence, Email (Resend default, lane 04), Slack webhook. "Send to
  ▸" on a window.
- Proof: `test_hs162_update_glass.py`, `test_hs173_update_glass.py`,
  `test_builtin_send_folder_glass.py`, `test_philo10_04_send_face_glass.py`,
  `test_philo13_15_send_to_glass.py`; atlas `p10.*`, `p11.*`.
- State: Folder send WORKS; gh / Jira / email / Slack and the model-drafted update NEEDS REAL
  METAL. KNOWN: `p11.meeting_summary.chair.sent` sends 200 but no sent row matches (unchecked).
  Rehearsal: draft with the LAN model, publish, send to the Folder and by Resend to himself.

## 7. The end of the day

### 7.1 Parked
- Face: the Parked drawer (lane 04: every parked object across kinds, Open and Restore);
  `meetings-parked`, the Workbench's parked, a Project's park receipt.
- Proof: `test_philo13_02_park_glass.py`; lane 04's glass.
- State: park / restore per kind WORKS; the one Parked place is lane 04. Rehearsal: park the
  test meeting and restore it from the drawer.

### 7.2 Memory, and the second morning
- What is remembered: the MemoryWorker sweeps every 120 s; the keyword index needs no model;
  vectors, facts, beliefs and pages each need an assigned engine. Where it shows: Desk memory
  (`/project-memory`), the Room's and the Brief's standing pages, ⌘K. Nothing memory-related is
  on the Chair screen. Overnight the Heartbeat holds 22:00–08:00; the Brief is not regenerated.
- Proof: `test_memory_faces_glass.py`, `test_hs526_desk_memory_glass.py`,
  `test_phase200_daily_loop.py` (day-2 recall across a restart).
- State: keyword recall WORKS; facts, beliefs and pages NEEDS REAL METAL (never run on the LAN
  model); the Desk memory face hides the four new kinds. Rehearsal 2: the next morning on the
  same HOME: the Brief carries yesterday's meeting, decision and the agent's merge; ⌘K finds
  yesterday's words; nothing doubles.

## Open before the rehearsal (from the inventory, ranked; the owners)

| # | Gap | Lane |
|---|---|---|
| 1 | LAN key on the Concierge | #966 merged |
| 2 | False "No engine for summaries"; OFF holds | #967 in review |
| 3 | WAV import final status | #968 in review |
| 4 | Summary slab consolidated; smoke re-anchored | #968 in review |
| 5 | Anthropic key has no execution adapter | queued (decide: adapter, or say OpenRouter / openai-compatible only on the face) |
| 6 | Needs-you paths | #965 merged |
| 7 | doctor runs the whole list | #966 merged |
| 8 | YOLO routine answers need a Cadence-drafts model | queued (the default should feed Cadence drafts; or the Concierge assigns it with summaries) |
| 9 | launch → PR → merge unproven on glass / atlas | rehearsal 1 is the proof; a Conductor atlas case after |
| 10 | The Brief does not generate itself | queued (ruling needed: cadence on by default for the brief only?) |
| 11 | Live recording has no browser-audio rig | rehearsal 1 records for real |
| 12 | Calendar denied: no way forward | lane 04 |
| 13 | Email default SendGrid → Resend | lane 04 |
| 14 | Parked icon opens Meetings only | lane 04 |
| 15 | 393 seventh Needs row under the Dock | rehearsal 1 looks |
| 16 | Memory invisible on the Chair; model kinds unrun | rehearsal 2 looks; a canvas if a face is needed |
| 17 | Install hooks has no glass or testid | rehearsal 1 presses; a fence after |
| 18 | People icon opens `/` | lane 04 |
