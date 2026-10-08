# Rehearsal 2, the second morning: bounces

PHILO Phase 15, lane 10. Walked 2026-10-07 21:06 to 22:05 MDT (real clock) on `main` c078a7938,
after all 18 Phase 15 lanes merged (worktree `wt-p15-r2`, branch `philo-15/rehearsal-2`). Day one
ran on the real clock; the second morning ran on a moved hub clock (07:05 and 08:10 on Thursday
8 Oct). Shots: `shots/NN-<face>-<width>.png` (78 files). No tests were run. Nothing tracked
outside this folder was changed.

## The rig, and where it differs from the owner's day

- One HOME (`mktemp -d -t hs-r2`), removed at the end. `CODEX_HOME`, `CLAUDE_CONFIG_DIR`,
  `TMUX_TMPDIR` and `HOLDSPEAK_PEOPLE_KEYSTORE_FILE` inside it. `GIT_CONFIG_NOSYSTEM=1`; the HOME's
  `.gitconfig` resets the helper list and allows only `!gh auth git-credential`. `GH_TOKEN` from
  `gh auth token`; a token-less `hosts.yml` (`user: karolswdev`). `OPENAI_API_KEY=local`. No
  `ANTHROPIC_API_KEY`, no `RESEND_API_KEY`. `HF_HOME` at the real Whisper cache, `HF_HUB_OFFLINE=1`.
  The hub log names its database inside the rig HOME. To my knowledge no Keychain item, no owner
  credential file and no real DB were read or written.
- Codex 0.159.0 ran on `qwen3.8-27b` at 192.168.1.43 through an isolated `CODEX_HOME/config.toml`
  (`wire_api = "responses"`). Claude Code was not launched (no key).
- The meeting: a 21 s WAV spoken by macOS `say` (decision: squash merges only; action for Karol:
  a CODEOWNERS file, due Friday). Whisper heard "Karol" as "Carol" and "karolswdev" as
  "Kiraal Swedeva".
- **The clock (rig only).** The hub has no fake clock. The second morning started the hub through
  `time-machine` (`travel(..., tick=True)`, installed into the worktree venv only, not into
  `pyproject.toml`): first at Thursday 07:05, then at 08:10. Real time between "yesterday" and
  "this morning" was a few minutes. Fresh browser pages got the same moved time
  (`page.clock.install` + `resume`); a page reload loses it. Clocks the hub does not own stayed real:
  GitHub stamps (the merge reads "21:40"), `gh`, Codex, SQLite `CURRENT_TIMESTAMP`. So a stamp
  written on the real clock after 08:10 can look "10 h old". I mark every row where that can matter.
- Headless Chromium over CDP (Playwright 1.57), one browser for both widths.
- Owner gestures by script, each on the face: a loop pressed Deny on Needs rows that read
  OUTSIDE THE WORKTREE or CUT, and Approve where an Approve existed (it approved
  `echo "canary-$(date +%s)"`, a probe the agent ran). One `PUT /api/updates/{id}` stands for the
  editor's Save, to make an update whose every claim is unverified (§ NOTHING VERIFIED).
- One shot is NOT committed: the Door's repository picker lists the owner's private repository
  names, and this repository is public.

## Timings

| What | Time |
|---|---|
| `holdspeak doctor`, before the first launch / second morning with the hub | 7.6 s / 2.7 s |
| First run: LAN server Check | READY within the 4 s wait |
| WAV import (21 s) to `55 WORDS · NOT RUN` | within 40 s (my wait loop did not time it closer) |
| Run summary on the LAN model | 6 s (face: RAN · 6 S) |
| Door: Create Project with the repository | 5 s |
| Hand to Codex → first command / → PR #4 | 21:18:09 → 21:18 / 21:30:07 (12 min, 11 holds: 3 approved, 7 denied, 1 expired) |
| PR #4 opened → the lane shows it | 21:30:07 → 21:38:15 (the Heartbeat sweep), 8 min |
| `gh pr merge 4 --squash` → launch closed → Room receipt | 21:40:54 → by 21:42:23 (first 2-min poll after the start) → read 21:43, no press |
| Hub start (07:05 hub time) → the scheduled Brief | 07:10:01, the first cadence tick (300 s) |
| Draft with model (first / second) | 28 s / 22 s |
| Publish / Send to the folder | under 4 s each |

## The three worst

1. **B58 LIES**: the second morning's Brief does not carry the day. It lists "Meeting recorded",
   "Project added", "Summary requested" and two stale sources. It has no decision, no agent, no
   PR #4, no merge, no sent update. The owner's Generate at 07:17 gives the same five rows.
2. **B62 + B63 STOP**: YOLO still holds the agent's normal reads (`git config user.name`,
   `gh --version`, `bash test.sh; echo "exit=$?"`). A cut hold says "CUT · APPROVE IN RAW", and Raw
   has no Approve and does not show the command. 11 holds in 12 minutes; one expired.
3. **B60 + B61 CONFUSE**: the first screen of the morning is "3 need you", and two of the three are
   STALE source rows ("github karolswdev/…", "meeting MEETINGS", "observed 21:23"). The 07:05 sweep
   was held by quiet hours (22:00–08:00). Retry on those rows only reloads the list.

## Bounces

Severity: P0 stops the day; P1 stops a step, or lies about the day's main facts; P2 confuses or
lies about a detail; P3 ugly or small.

| # | Sev | Face · width | What the owner saw | What he expected | Shot | Probable site |
|---|---|---|---|---|---|---|
| B58 | P1 | Brief · 1440 + 393 | The 07:10 scheduled Brief, "Brief · Thursday 8 Oct 2026": "2 sources not read, 3 things changed." Rows: Meeting recorded, Project added, Summary requested, and two "Not observed" sources. No decision (confirmed 21:14 yesterday, inside the period OCT 07-08), no agent launch, no PR #4, no merge, no sent update. The owner's Generate at 07:17 gives the same rows. | Yesterday's decision, the agent's PR and its merge, and the update he sent. | `52-morning-brief-393.png`, `53-morning-brief-reloaded-1440.png`, `68-morning-brief-generate-1440.png` | `holdspeak/services/monday_brief_service.py` (the "changed" collectors; no Conductor or update source) |
| B59 | P1 | Brief · 1440 | The Brief window opened at 07:11 (after the 07:10 brief was stored) shows "Brief · Wednesday 7 Oct 2026 · GENERATED 21:33". Only a page reload shows Thursday's. Also, a hub started at 07:05 shows yesterday's Brief until its first tick 5 minutes later. | This morning's Brief when he opens it. | `52-morning-brief-1440.png`, `53-morning-brief-reloaded-1440.png` | Brief load in `web/src/desk/chair/ChairHome.tsx` (no reload on the scheduled write; line not located); first tick waits `tick_interval_seconds`: `holdspeak/runtime/cadence.py:224-227` |
| B60 | P1 | Needs you · 1440 + 393 | At 07:05: "3 need you": "github karolswdev/holdspeak-dayone-rehearsal-1558 · not checked recently · observed 21:23 · STALE", "meeting MEETINGS · … STALE", and PR #4. The 07:05 Heartbeat sweep was held (`run_sweep {"held": true}`): quiet hours end at 08:00. The Brief repeats both as "Not observed". | No rows that HoldSpeak caused itself by sleeping. | `50-morning-arrival-1440.png`, `50-morning-arrival-393.png`, `55-morning-needs-1440.png` | `holdspeak/services/heartbeat_service.py:40` (`_DEFAULT_QUIET_END = 8`); the stale rule does not know the hold |
| B61 | P1 | Needs you · 1440 | Retry on a STALE source row changes nothing: no receipt, same row, same "observed 21:23". Retry only re-reads the Needs list. | Retry re-checks that source. | `56-morning-needs-retry-1440.png` | `web/src/desk/needs/NeedsDrawer.tsx:247` (`if (v.verb === "Retry") void refreshNeedsYou(true)`) |
| B62 | P1 | Needs you + lane · 1440 + 393 | YOLO held: `git config user.name; git config user.email` (SHARED GIT STATE), `command -v gh && gh --version` (GITHUB ACTION FOR YOU), `bash tests/codeowners_test.sh; echo "exit=$?"` (UNRESOLVED TARGET · $?), `git status --short && echo "HEAD=$(git rev-parse HEAD)" …`, and a combined identity read. 11 holds in 12 min. Heredoc writes and `git push` of its own branch now pass. | YOLO lets the agent read and run its own test in its worktree. | `37-needs-held-identity-1440.png`, `38-needs-two-held-reads-1440.png`, `39-needs-held-test-run-1440.png`, `43-lane-after-pr-1440.png` | `holdspeak/tool_gate_rules.py:1133-1134` (labels), `:1202-1213` (a `$` target is unresolved) |
| B63 | P1 | Needs you + lane · 1440 + 393 | A long held call reads "CUT · APPROVE IN RAW" with Deny + Open only. Raw shows the Codex pane ("Working · Running hooks"), not the command, and has no Approve. The first hold (a `cd` into the agent's own worktree) expired after 4 min. | Read the whole command and approve it somewhere. | `33-needs-held-393.png`, `35-lane-held-1440.png`, `36-lane-raw-1440.png` | `web/src/desk/needs/needsFace.ts:261`; the #998 ruling (B44 a design limit) promises Raw as the place |
| B64 | P1 | Room › Updates · 1440 | NOTHING VERIFIED reads only the model's own `[UNVERIFIED]` tag. The second model draft had no SUPPORTED claim (the face marks every claim INFERENCE · UNREVIEWED), and one is false: "Next Actions: Carol is to add a CODEOWNERS file … due Friday" for an action merged and done. Send was offered and saved it. (A body of only `[UNVERIFIED]` lines IS refused: "✗ REFUSED · NOTHING VERIFIED · NOTHING SENT", `64-…`, `67-…`.) | An update with nothing checked does not go out. | `61-draft2-model-1440.png`, `62-draft2-published-1440.png`, `63-draft2-send-1440.png` | `holdspeak/services/channel_contract.py:279-298` (`nothing_verified`) |
| B65 | P2 | Lane, drawer, Needs · 1440 | PR #4 opened 21:30:07. The lane's PR station read "—" until 21:38:15. The 2-min poll follows only PRs already known; a new PR is found by the 15-min Heartbeat sweep. | The lane shows the PR within a poll. | `42-lane-pr-1440.png`, `43-lane-after-pr-1440.png`, `47-lane-reopened-1440.png`, `48-lane-pr-known-1440.png` | `holdspeak/delivery/follow_through.py:181-231` (discovery in `_sweep`); `holdspeak/web_server.py:1988` (poll of known PRs) |
| B66 | P2 | Codex pane / lane rail | Every Deny reaches the agent as "denied from the desk", with no reason. The agent tried the `/tmp/pr_body.md` write three ways after three Denies. | The agent learns "outside the worktree" and stops. | `41-rebrief-sent-1440.png` | `holdspeak/coder_gate.py:626` |
| B67 | P2 | Lane · 1440 | A Re-brief sent mid-turn read "QUEUED · AFTER THIS TURN". It was typed at 21:30, after the PR was open and the work was done. The agent answered "Confirmed — already conforming …", which became an ASKS row. No verb cancels a queued Re-brief. | A Re-brief that is no longer needed is not typed, or he can take it back. | `41-rebrief-sent-1440.png`, `49-needs-asks-done-393.png` | `holdspeak/web_server.py` turn-end path (`flush_queued`, `holdspeak/services/launch_rebrief.py`) |
| B68 | P2 | Lane, Needs, Brief, Conductor · 1440 + 393 | The agent's finished report shows as a question: lane ASKS "now", Needs "ASKS · 8 MIN · Answer", Brief "TO ANSWER", Conductor icon "AGENT, ASKS". (B48 class, again.) | DONE is not a question. | `49-needs-asks-done-393.png`, `48-lane-pr-known-1440.png`, `45-brief-day1-generated-1440.png` | `turn_end` / `asks_a_question` (`holdspeak/agent_context/models.py`, mirrored in `needsYou.ts`); not re-read |
| B69 | P2 | Room · 1440 + 393 | At 07:06: "Clear here · ON TRACK · CHECKED 10H AGO", "Nothing open · next check 22:23" (a time in the past), while Needs shows the same source STALE. | One state for the source; a next check in the future. | `51-room-merge-receipt-1440.png`, `70-room-0810-1440.png` | `web/src/features/project-room/ProjectRoomCore.tsx:874` |
| B70 | P2 | Room · 1440 | After the merge closed the action (DB `status = done`), the Room's DECISIONS & COMMITMENTS row still reads "ACTION · OWNER CAROL · BY FRIDAY · CONFIRMED 21:14", with no DONE. The receipt line under it says DONE. | The row shows done. | `51-room-merge-receipt-1440.png` | Room decisions-and-commitments row (file not located) |
| B71 | P2 | Room › Updates · 1440 | The model draft repeats each merge: the `Merged: … (PR #1)` and `(PR #4)` rows, then the same two merges in prose. It also sends inferences that are wrong: "assigned Carol", "previously tracked as an open decision". The sent file carries all of it. | Each merge once; nothing false. | `58-draft-model-1440.png`, `60-sent-folder-1440.png` | model draft path in `holdspeak/services/project_update_service.py` (line not located) |
| B72 | P2 | Room › Updates list · 1440 | Each list row shows "MODEL IA_0488064EC64348AB8679B509E8952A60". (B53 is paid in the editor, not in the list.) | No raw ids. | `70-room-0810-1440.png` | updates list row (`web/src/features/project-room/update/`, line not located) |
| B73 | P2 | Brief · 1440 + 393 | "Summary requested: Repo hygiene sync" has the detail `{"meeting_id":"23c66417","expected_selection_hash":"sha256:3e52…"}`. Waiting rows read "Not observed: meeting MEETINGS · last seen 2026-10-08T03:23" (a UTC ISO stamp). | Plain words, local time. | `44-brief-day1-1440.png`, `53-morning-brief-reloaded-1440.png` | `holdspeak/services/monday_brief_service.py:25-35` (`_sanitize_detail` keeps the JSON), `:1434` |
| B74 | P2 | Needs you · 1440 + 393 | Source rows read "github karolswdev/…", "meeting MEETINGS", "observed 21:23" (no day on the next morning). | "GitHub · <repo>", "Meetings", "yesterday 21:23". | `50-morning-arrival-393.png` | Needs source rows (`web/src/desk/needs/needsFace.ts`, line not located) |
| B75 | P2 | First run → Door → Connections · 1440 | First run: GitHub "SIGNED IN · KAROLSWDEV · FROM GH CONFIG". The Door then: GitHub "NOT SET UP · Connect". Connect opens Settings › Connections: "GitHub NEVER CHECKED". Only Recheck made the Door offer "Choose a repository". (B31, again, on the Door.) | One sign-in truth; the Door offers his repositories at once. | `01-firstrun-1440.png`, `15-door-1440.png`, `16-door-github-1440.png`, `17-github-recheck-1440.png` | `holdspeak/services/connections_service.py:42`, `:169` (from B31); the Door's GitHub row |
| B76 | P2 | Desk · 1440 | Dragging the meeting onto the Project drawer draws the ghost and the dotted path; the drop does nothing and says nothing. "Add to Project ▸" on the opened meeting works (`IN …`, source `manual`). (B37's drag part.) | The drop files it, or says "not here". | `21-drag-meeting-over-project-1440.png`, `22-drop-meeting-on-project-1440.png`, `25-added-to-project-1440.png` | `web/src/desk/hand/drag.ts:5-6`, `web/src/desk/hand/begin.ts` (targets are agents only) |
| B77 | P2 | Meeting › Review · 1440 | The commitment "Add a CODEOWNERS file …" reads "NO SOURCE · ⚠ UNSUPPORTED", but transcript segment 3 says it. | "From the transcript, 0:08". | `12-proposals-1440.png` | meeting proposal support check (file not located) |
| B78 | P2 | Room, agent brief, update · 1440 | "Carol" stays his name everywhere but Needs and the Brief: the Room "OWNER CAROL", the brief typed to Codex "Owner: Carol", both updates "Carol was assigned / Carol is to add". Needs and the Brief treat the item as his ("YOURS"), as B57's fix intends. | Karol, or one "is this you?" fix that flows everywhere. | `51-room-merge-receipt-1440.png`, `58-draft-model-1440.png` | `holdspeak/services/agent_brief.py`; update drafter; Room row |
| B79 | P3 | Search ⌘K · 1440 | "squash" finds the decision, the artifact, the action and the meeting. "PR #4" finds nothing. (B55's PR part.) | The PR. | `66-search-PR4-1440.png`, `66-search-squash-1440.png` | search index (not located) |
| B80 | P3 | Receipt (no face) | The scheduled run's receipt says `brief.regenerated items=0`; the stored brief has 5 items. | The true count. | none (pipeline_events row) | `holdspeak/runtime/cadence.py:171`, `:180` (`getattr(brief, "item_count", 0) or len(getattr(brief, "items", []))` finds neither on the returned brief) |
| B81 | P3 | Doctor · terminal | Second morning: WARN "Where AI runs: This device · not set up yet" and WARN "Dictation AI model … not on this device yet" while the LAN default runs summaries; "Event log · 24h events: 66831" on a desk with one meeting (cause not verified). | Green for a LAN-only desk. | none (terminal) | `holdspeak/commands/doctor.py` |
| B82 | P3 | Hand confirm line · 1440 | Flipped to Codex, the egress chip reads "API.OPENAI.COM". In this rig Codex used the LAN box. On a Codex signed in to OpenAI the chip is right. | The host Codex will call. | `28-hand-confirm-codex-1440.png` | `web/src/desk/hand/HandConfirm.tsx` (does not read the Codex config) |
| B83 | P3 | Needs you · 393 | The agent's `cd /private/var/…/<its own worktree> && …` was held "OUTSIDE THE WORKTREE" and expired. Probably the rig: macOS `/var` → `/private/var`. The owner's `/Users/…` path probably does not hit it (not verified). | — | `33-needs-held-393.png` | worktree check in `holdspeak/tool_gate_rules.py` (path resolution) |
| B84 | P3 | Meetings · 1440 | Import is two presses: "Import" opens the RECORD tab with a drop zone and a second "Import". | One press, then the file. | `08-import-pressed-1440.png`, `09-import-picked-1440.png` | Meetings import panel |
| B85 | P3 | Needs you · 1440 | Hold labels: "NOT READ · shell_expansion" (snake_case), "GITHUB ACTION FOR YOU" for `gh --version`. | Plain words that match the command. | `38-needs-two-held-reads-1440.png` | `holdspeak/tool_gate_rules.py:1133`, `:1213` |
| B86 | P3 | Hand receipt · 1440 | The clone folder doubles its name: `~/.holdspeak/repositories/karolswdev/holdspeak-dayone-rehearsal-1558/holdspeak-dayone-rehearsal-1558`. | One level. | `29-handed-1440.png` | `holdspeak/services/agent_hand_service.py` clone path |
| B87 | P3 | Sent file | The sent update has four sections that read only "Not checked.", Source Coverage included. | Leave out a section with nothing in it. | `60-sent-folder-1440.png` | `holdspeak/services/channel_contract.py` (`_outbound`) |
| B88 | P3 | Brief + Needs · 1440 | Day one, 21:12 Brief: header "BRIEF · 1 THING WAITING" over a body that says "2 things waiting". Day one 21:24: "1 needs you" over a row that read "Codex · WORKING" (no shot; read from the page). | The header counts what the body lists. | `44-brief-day1-1440.png` | Brief header count; Needs count |
| B89 | P3 | Room › Updates · 1440 | At 08:11 the deterministic draft says "Source Coverage: All sources consulted successfully" while Needs shows two STALE sources. Clock caveat: after the 08:10 restart some observation stamps were written on the real clock, so the STALE rows at 08:11 may be the rig's. | One answer about the sources. | `71-draft-deterministic-0810-1440.png`, `69-needs-after-0800-1440.png` | deterministic coverage line in `holdspeak/services/project_update_service.py` |

Count: P0 0 · P1 7 · P2 14 · P3 11 (32).

## The sent update, verbatim

`~/Documents/HoldSpeak/Sent/2026-10-08-rehearsal-repo-hygiene-rev-1-e5de450a.md` (1119 bytes), model draft
rev 1, sent 07:12 hub time:

```
# Rehearsal repo hygiene · Update · 2026-10-08

## Progress

- Merged: Add CONTRIBUTING.md with the three pull request rules (PR #1) https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1
- Merged: Add CODEOWNERS naming Kiraal Swedeva as owner of every file (PR #4) https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/4
- A pull request adding a CONTRIBUTING.md file with three pull request rules was merged (PR #1).
- A pull request adding a CODEOWNERS file naming Kiraal Swedeva as owner of every file was merged (PR #4).
- The repo hygiene meeting established the use of Squash Merge exclusively on the rehearsal repository and assigned Carol to add the CODEOWNERS file by Friday.
- The CODEOWNERS action previously tracked as an open decision is now complete with the merge of PR #4.

## Decisions

- The team decided to use Squash Merge only on the rehearsal repository, starting today; the decision is active.

## Risks & Blockers

Not checked.

## Dependencies

Not checked.

## Next Actions

Not checked.

## Source Coverage

Not checked.

4 claims not checked, kept on the desk.
```

The four `[UNVERIFIED]` lines stayed on the desk, the merge row went once by its title with its
link, and the later drafts (model at 07:13, deterministic at 08:11) have no merge row. PR #1 is a
merge from rehearsal 1 in the same repository, inside the window.

## What now reads right (re-observed as fixed)

- **B08**: doctor before the first launch ends with one line: "HUB · NOT RUNNING · start it with `holdspeak`".
- **B09**: first run has "Use a server on my network": address, key, Check (READY · qwen3.8-27b), "Use this
  for summaries". No 2.9 GB download needed for a LAN desk (`02`–`04`).
- **B10**: that press leaves a receipt on the card: "USING · QWEN3.8-27B · SUMMARIES · DEFAULT SET" (`04`).
- **B35 / B36**: Install hooks on the first-run card leaves "CLAUDE CODE · HOOKS IN / CODEX · HOOKS IN";
  the confirm line says "CODEX · SIGN-IN UNKNOWN" (`05`, `28`).
- **B14**: an imported meeting reads "NOT RUN", not "OFF"; the title comes from the recording, not the file name
  (`10`; B30 too).
- **B02 / B03**: the 6 s LAN summary gives one decision and one commitment, each with Confirm, Defer, Decline;
  both confirmed (`12`, `13`).
- **B19 / B20**: the Dock has sprites for Intelligence, Desk memory, Delivery, Panes; the first screen has five
  notes and no guard notes (`06`).
- **B21**: at 393 Go is Needs you, Brief, The week, Capture, then Meetings, People, Conductor, Settings, the
  Project, New »; no keycaps (`31`).
- **B38 / B39**: the Project made in the Door with its repository registers it (receipt REPOSITORY.REGISTER);
  the hand clones it ("CLONED · KAROLSWDEV/… · 21:18"); a press on the agent name on the confirm line flips
  Claude Code to Codex (`20`, `27`–`29`).
- **B41 / B42**: Codex started in its worktree with no trust stall; the lane said "SENT · 21:18" (`35`).
- **B43** (in part): heredoc writes (`cat > CODEOWNERS <<'EOF'`), the commit and `git push -u origin <its branch>`
  passed under YOLO with no hold (B62 is the rest).
- **B45**: the HELD station counts: "11 HELD · 3 APPROVED · 7 DENIED · 1 EXPIRED" (`43`).
- **B46**: Re-brief was accepted ("QUEUED · AFTER THIS TURN", then "SENT · 21:30"); B67 is its timing.
- **B50**: the lane's PR card has the PR's own title "#4 Add CODEOWNERS naming …" (`48`).
- **B51**: the merge reached the launch at the first 2-minute poll after the hub start, about 90 s after
  `gh pr merge`, with no press; the Room receipt "DONE · ADD CODEOWNERS … · PR #4 MERGED · 21:40 · Open PR"
  (`51` at both widths). The worktree was removed, the session killed, the action set done.
- **B52 / B53**: the published update has the `Merged:` row once, with title, number and link; the sent file
  opens `# Rehearsal repo hygiene · Update · 2026-10-08`; unverified lines are omitted with
  "4 claims not checked, kept on the desk."; the editor's generator label reads "MODEL · OPENAI COMPATIBLE".
- **NOTHING VERIFIED**: an update with only `[UNVERIFIED]` lines is refused at the preview:
  "✗ REFUSED · NOTHING VERIFIED · NOTHING SENT", no Send verb (`64`, `67-update-refused-393.png`). B64 is the gap.
- **B54**: the Brief generated itself (07:10, key-free, no "No engine" row), titled "Brief · Thursday 8 Oct 2026",
  and it says what it could not read: "2 sources not read". B58 is what it misses.
- **B04**: day one's Generate made a new brief (21:12 → 21:33) with the new Project.
- **B11 / B12**: one number on the second morning: "2 need you" on the drawer head, the desk icon, the
  Intelligence and Desk memory badges and the menu-bar bell; rows say their kind (ACTION, AGENT) (`55`).
- **B57** (in part): Needs and the Brief treat the "Carol" action as his ("YOURS"); B78 is the rest.

Not observed, so not claimed: B47 (no YOLO responder answer was typed into the agent in this run; the only
wait was the B67 Re-brief answer, which stayed for the owner); B56 (the aftercare card was not watched).

## Not reached

- Live recording, First words, the calendar, People, Parked, The week, meaning search, Desk memory pages:
  not in this script or no time (headless, no microphone).
- Claude Code: no `ANTHROPIC_API_KEY`. Email: no `RESEND_API_KEY`.
- The lane at 393: not shot.
- The Concierge (Settings › Models): not opened; first run did the engine.
- Whether the STALE rows at 08:11 (B89) are the product or the rig's split clock.

## DAY-ONE v2 notes

- **§1.2** Doctor before the first launch: 28 PASS, 4 WARN (Where AI runs, Dictation AI model, Coding agents
  until hooks, People keystore in a rig), then `HUB · NOT RUNNING`. Say that these WARNs are expected.
- **§1.3–§1.5** One page now does the engine: first run › Local AI › "Use a server on my network" › address
  + key › Check › "Use this for summaries". The Concierge step (§1.5) becomes optional. Install hooks is on
  the same page (Agents card, with a receipt), so §5.1 folds into §1.3.
- **§2.3** The Brief makes itself at 06:00, or on the first tick (about 5 minutes) after a later start.
  Until B59 is paid: reload the page to see it. Generate makes it again.
- **§3.2** Import: Meetings › Import › drop or pick the file › Import (two presses). The title comes from
  the recording.
- **§3.3 / §3.5** Run summary is on the meeting's row; Confirm the decision and the commitment on the
  meeting's REVIEW tab (or the Needs row).
- **§4.2** Order changes: Settings › Connections › GitHub › Recheck BEFORE New Project (until B75 is
  paid), then Desk › New Project › name › Choose a repository › Create Project. Create opens the Room.
- **New §4.2b** Put the meeting in the Project: open the meeting › "Add to Project ▸" › the Project. Not a drag.
- **§5.2** Project drawer › select the action › Hand to agent › press the agent name on the line to
  change agent › Hand. The receipt says CLONED.
- **§5.3** Expect held calls in Needs you. Approve the short ones. A CUT one can only be denied or left to
  expire in 4 minutes (until B63 is paid). Re-brief waits for the end of the agent's turn.
- **§5.4** The PR shows on the lane at the next Heartbeat sweep (up to 15 minutes). After the merge on
  GitHub the Room receipt comes in about 2 minutes with no press; Rhythm › Run now is no longer needed.
- **§6** Room › Draft update › Draft with model (about 30 s) › Publish › Send (the folder). Read the claims
  first: inferences go out as facts (B64, B71).
- **§7.2 / the second morning** Start after 08:00, or expect STALE source rows before quiet hours end
  (B60). The morning Brief does not yet carry yesterday's decision, PR or merge (B58). ⌘K finds
  yesterday's words but not "PR #4".
