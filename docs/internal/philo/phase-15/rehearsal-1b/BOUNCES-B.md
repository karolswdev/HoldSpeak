# Rehearsal 1, part B: bounces

PHILO Phase 15, lane 02, part B. Walked 2026-10-07 15:58 to 16:56 MDT on `origin/main` aa1a94e15
(worktree `wt-p15-rehearsal-b`, detached). Shots: `.tmp/day-one-shots/<step>-<width>.png` (108 files).
Evidence beside this file: `doctor-b.txt`, `pr1.json`, `sent-update.md`, `codex-pane.txt` (the last
screen of the agent), `hub-holdspeak.log`. Nothing tracked was changed. No tests were run.

## The rig, and where it differs from the owner's day

- One HOME (`mktemp -d`, `hs-dayone-b.*`), removed at the end. `HOLDSPEAK_PEOPLE_KEYSTORE_FILE`,
  `CLAUDE_CONFIG_DIR` and `CODEX_HOME` inside it. `HF_HOME=~/.cache/huggingface`, `HF_HUB_OFFLINE=1`.
- LAN engine `http://192.168.1.43:8080`, `qwen3.8-27b`, key `local`, added in the Concierge, then
  "Use this for summaries" and "Use these".
- Credentials: `ANTHROPIC_API_KEY` and `RESEND_API_KEY` are not exported. `OPENAI_API_KEY` is exported,
  but it is the 5-character LAN key (`local`), not an OpenAI key. So Codex ran with an isolated
  `CODEX_HOME/config.toml` that names the LAN box as its model provider (`wire_api = "responses"`),
  as R3 did. Claude Code had no credentials (NEEDS CREDENTIALS, below).
- GitHub: the throwaway repository `karolswdev/holdspeak-dayone-rehearsal-1558` (private, `--add-readme`),
  cloned into the HOME. The hub got `GH_TOKEN` from `gh auth token` and a token-less `hosts.yml`
  (`user: karolswdev`) in the HOME, so Connections reads him as signed in. Git used only
  `!gh auth git-credential` (`[credential] helper =` reset, `GIT_CONFIG_NOSYSTEM=1`).
- `TMUX_TMPDIR` inside the HOME. Without it, the hub's `tmux new-session` joins the owner's running
  tmux server, and the agent gets that server's environment (the real HOME, the real `~/.codex`),
  not the hub's (`holdspeak/coder_factory.py:123-131` passes only `HOLDSPEAK_HUB_URL` with `-e`). This
  matters for every isolated rehearsal; on the owner's own desk the two environments are the same.
- Headless Chromium (Playwright 1.57, `--use-angle=metal`), one persistent driver process for both
  widths. The driver did NOT run under `scripts/test_lock.py`: the lock waited up to 6.5 min per step,
  and a 1-second CDP attach is not a test run. The hub and the browser ran outside the lock too.
- `holdspeak web --no-open`. The hub printed no URL to a redirected stdout; the token came from the
  isolated `config.json`.
- Workarounds through HTTP routes, each also a bounce row: link the meeting to the Project (B37),
  register the local clone (B38), hand to Codex (B39). By hand in the agent's tmux pane, as the owner
  in a terminal would: Enter on Codex's folder-trust screen (B41), two typed steers (B46).

### Rig incident (disclose)

At 15:58 the first `git clone` of the throwaway repository ran with the Xcode system git config,
which sets `credential.helper=osxkeychain`. After `gh` gave the credential, git ran
`git credential-osxkeychain store` against the REAL login Keychain. It hung about 2 minutes (a
prompt, probably) and I killed it (pids 64707, 64710, signal 15). I did not read the Keychain, so
whether an item for github.com was written is UNKNOWN. The orchestrator or the owner can check
Keychain Access for a new `github.com` internet password dated 2026-10-07 15:58. From then on the
rig set `GIT_CONFIG_NOSYSTEM=1` and reset the helper list. The owner's `~/.claude/settings.json`
(Oct 6 21:59) and `~/.codex/config.toml` (Oct 4 12:37) were not touched.

## NEEDS CREDENTIALS

| Agent / service | Step it blocks |
|---|---|
| Claude Code (no `ANTHROPIC_API_KEY`) | §5.2 hand to Claude Code: the drag onto the Conductor at 1440 and the verb at 393 were walked to the confirm line (shots `5.2-confirm-line-with-repo-1440.png`, `5.2-verb-confirm-393.png`), and Hand was NOT pressed. The whole §5.3–§5.4 loop ran on Codex instead. |
| OpenAI (the exported key is the LAN key) | Codex ran on `qwen3.8-27b` through the LAN box, not on an OpenAI model. |
| Resend (no `RESEND_API_KEY`) | §6 email send. Only the Folder send was walked. |
| EventKit (headless, and no path, B32) | §4.3 the macOS calendar prompt (deny once, recover) was not reached. |

## Timings

| What | Time |
|---|---|
| `uv sync --python 3.13 --extra test --extra dev` / `npm ci` (web) / `npm run build` | 12.1 s / 4.6 s / 6.4 s |
| GitHub Recheck → CONNECTED · karolswdev | under 6 s |
| Door repository picker (30 repositories listed) | 4 s |
| WAV import, 26 s `say` meeting, to "63 WORDS" | 3.5 s |
| Run summary on the LAN model | 22.1 s (face: RAN · 21 S) |
| Install hooks, Codex / Claude Code (press to the verb going away) | 0.3 s / 0.12 s |
| `holdspeak doctor`, warm, hub running | 2.7 s; Coding agents PASS |
| Hand (route) → 202 launched | 0.8 s (16:26:48) |
| Launch → registration | about 2 min 54 s: Codex sat on its folder-trust screen until I pressed Enter at 16:29:42 (B41); the brief was sent at 16:29. Without the Enter: never. |
| Launch → PR #1 | 18 min 53 s (16:26:48 → 16:45:41), with 9 held calls (3 approved, 5 denied, 1 expired) and 2 steers typed in the pane |
| PR merge (`gh pr merge 1 --merge`) → Room receipt | 1 min 18 s (merged 16:48:40; Rhythm "Run now" pressed 16:49:30, the sweep took 1850 ms; receipt read 16:49:58). Unforced, the next sweep was 17:04 (Rhythm) and the Room said "NEXT CHECK 17:31". |
| Session and worktree cleanup after the merge | session gone 16:49:35 |
| Draft with model / deterministic Draft | 29.1 s / 0.5 s |
| Publish / Send to the Folder | under 3 s / 0.5 s (✓ SAVED) |

The Heartbeat sweep was forced with **Go ▸ Rhythm ▸ Run now** (`POST /api/settings/heartbeat/run-now`,
`web/src/pages/cores/CadenceCore.tsx:234`).

## The agent's PR, verbatim

`https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1`, branch
`hs/action-action_1ff5227ebc101ddbe1d827ba`, commit `aaceba6` "Add CONTRIBUTING.md with the three pull
request rules and its test", files `CONTRIBUTING.md`, `tests/contributing_test.sh`.

Title: `Add CONTRIBUTING.md with the three pull request rules`

Body:

> Adds CONTRIBUTING.md with the three pull request rules:
>
> 1. Branch from main.
> 2. One change per pull request.
> 3. Every pull request names its test.
>
> Includes tests/contributing_test.sh, which verifies the contributing file states all three rules (passing: PASS: CONTRIBUTING.md states all three rules).
>
> Item: action:action_1ff5227ebc101ddbe1d827ba
> Test: tests/contributing_test.sh

Read as a reviewer: the test script never fails. It prints FAIL lines but ends without `exit "$fail"`,
so it exits 0 when a rule is missing. That is the agent's work, not a HoldSpeak bounce, but nothing on
the desk would catch it.

## The weekly update, verbatim (sent to the Folder)

`~/Documents/HoldSpeak/Sent/2026-10-07-payments-ledger-cutover-rev-1-1d328e5f.md` (826 bytes), model draft
rev 1, published 16:50, sent 16:51:

```
## Progress

- A planning meeting was held for the payments ledger cut-over, during which the team decided to keep the old ledger read-only for 30 days post cut-over and assigned Carol to add a contributing file with three PR rules to the rehearsal repository by Friday.
- The contributing file with the three rules—branch from main, one change per pull request, and every pull request names its test—was merged into the rehearsal repository.

## Decisions

- The decision to keep the old ledger read-only for 30 days after the cut-over is active.

## Risks & Blockers

- **[UNVERIFIED]** No risks or blockers in this window.

## Dependencies

- **[UNVERIFIED]** No dependencies tracked.

## Next Actions

- **[UNVERIFIED]** No upcoming actions.

## Source Coverage

- **[UNVERIFIED]** All sources consulted successfully.
```

No `Merged:` row, no PR number, no link (B52). The deterministic draft made after it has no merge line at all.

## The LAN summary of the meeting, verbatim

Input: a 26 s meeting spoken by macOS `say` (script: decision "keep the old ledger read only for thirty
days after the cutover"; action for Karol "add a CONTRIBUTING file ... three rules ... Due Friday").

> Planning meeting for the payments ledger cut-over. Decided to keep the old ledger read-only for 30 days post cut-over. Carol to add a contributing file with three PR rules to the rehearsal repository by Friday.

Whisper heard "Karol" as "Carol", "sync" as "sink" and "read only" as "red only". The summary
corrected "red only" and kept "Carol". Proposals: "Confirm: Add a contributing file ... · by Friday"
and "Decide: Keep the old ledger read-only for 30 days after the cut-over", both with Confirm (#983 works).

## The five worst

1. **B41 STOPS**: Codex's first launch in a repository hangs on its folder-trust screen. The hub never answers it, because the screen has a "Note: You're in a subdirectory of a Git project ..." paragraph and the parser joins it into the path. Meanwhile the face says the agent is at work and the brief was delivered (B42).
2. **B43 STOPS**: YOLO holds every `cat > file <<'EOF'` and every `apply_patch` run in the shell, inside the agent's own worktree. A long held call has no Approve anywhere. That gave 9 holds in 19 minutes, and the agent began probing writes in `/tmp`.
3. **B38 STOPS**: a Project made through the Door with its GitHub repository cannot hand anything to an agent ("NO REPOSITORY"). No face registers or clones the repository.
4. **B47 LIES**: the YOLO responder talks to the agent in the owner's voice: 6 answers in 60 s ("Goodbye! 👋", "You're welcome! Glad I could help. 🚪"). One claims "I'll mark action:… as done on the desk". The last told the finished agent: "Hi! Go ahead and create the CONTRIBUTING.md …", which is an order to do the work again.
5. **B52 LIES**: the merge closed the item and the Room says "PR #1 MERGED". The weekly update has no `Merged:` row and no PR number or link. A deterministic draft made afterwards does not mention the merge at all.

## Bounces

| # | Step · width | What happened | What the owner would feel | Shot | Severity | Start from |
|---|---|---|---|---|---|---|
| B31 | §4.3 · 1440 | First run said "Connections ● SIGNED IN · 1 · GitHub gh · karolswdev · Use it". Settings › Connections then said "GitHub ○ NEVER CHECKED". A press on Recheck was needed to show "karolswdev ✓ CONNECTED · CHECKED NOW". DESTINATIONS stays 1 (the Folder): the sign-in adds no GitHub Send destination. | "It just said I'm signed in. Now it says never checked." | `4.3-firstrun-connections-1440.png`, `4.3-connections-1440.png`, `4.3-github-recheck-1440.png` | CONFUSES | `holdspeak/services/connections_service.py:42` (`DISPLAY_NEVER_CHECKED`), `:169` (no read until a check) |
| B32 | §4.3 · 1440 | After "Continue later" there is no way to give HoldSpeak the Mac calendar. Connections › Calendar "Set up" opens Settings › Meetings, which has only "Connect calendar" → "Paste an ICS URL or a file path". Needs you's "Connect calendar" opens the same page. "Allow calendar access" (EventKit) exists only on the first-run card. | "Where do I let it read my calendar?" | `4.3-calendar-setup-1440.png`, `4.3-calendar-connect-1440.png`, `4.3-needs-connect-calendar-1440.png` | STOPS | `web/src/pages/cores/connections/ConnectionsPane.tsx:645-648` (`onOpenModule("meetings")`); `web/src/pages/cores/SettingsCore.tsx:1938`; EventKit only at `web/src/desk/firstrun/CalendarCard.tsx:69` |
| B33 | §4.3 / §1.6 · 1440 | After "Use these" the summaries run on the LAN box. Doctor also says "Meeting summary: profile '192.168.1.43:8080'". But Settings says "No default model", "Assignments ⚠ NO DEFAULT", "Voice ⚠ NO ENGINE", "Meetings ⚠ SUMMARY · NO ENGINE"; Settings › Meetings says "Summary ⚠ NO MODEL · Choose model"; Connections says "Models · Unassigned · UNASSIGNED"; doctor's hub section says "SKIP inference · no targets configured". `/api/inference/assignments` has `meetings: no_assignment`. (Part A's B05, on four more faces.) | "Five faces say I have no model. Which one is true?" | `4.3-settings-open-1440.png`, `4.3-settings-meetings-1440.png`, `4.3-connections-1440.png`, `doctor-b.txt` | LIES | `holdspeak/services/connections_service.py:495` (counts only `status == "assigned"` rows); Settings hub headline (file not located) |
| B34 | §5.1 · 1440 | The Conductor drawer opens on two robots with orange squares and only "Get Info" in the footer. "Install hooks" shows only after you select an agent icon. Nothing says what the orange square means. | "Where is Install hooks? The doc says it is here." | `5.1-conductor-drawer-1440.png`, `5.1-codex-selected-1440.png` | CONFUSES | `web/src/desk/conductor/ConductorWindow.tsx:136-146` (the verb needs `member.detect`) |
| B35 | §5.1 · 1440 | Install hooks worked (Codex 0.3 s, Claude Code 0.12 s; hooks in the isolated `CODEX_HOME` with trust hashes and in `CLAUDE_CONFIG_DIR/settings.json`; doctor "Coding agents: Claude Code hooks installed; Codex hooks installed"). On the face the button and the orange square just go away. There is no receipt; only a failure gets one. | "Did it do anything?" | `5.1-codex-installed-1440.png`, `5.1-claude-getinfo-1440.png` | CONFUSES | `web/src/desk/conductor/ConductorWindow.tsx:57-84` (receipt only for fail/stop); `web/src/desk/conductor/store.ts:151-157` |
| B36 | §5.1 / §5.2 · 1440 | Claude Code has no credentials on this desk. Get Info reads "SIGN-IN UNKNOWN", and every Hand on the face defaults to Claude Code ("CLAUDE CODE · YOLO · API.ANTHROPIC.COM"). Nothing warns that the agent may not be signed in. A launch without a sign-in was not pressed (NEEDS CREDENTIALS), so what it does is unknown. | "Will it just hang at a login?" | `5.1-claude-getinfo-1440.png`, `5.2-confirm-line-with-repo-1440.png` | CONFUSES | `web/src/desk/agentHand.ts:40` (`DEFAULT_AGENT = "claude"`); sign-in read: `web/src/desk/firstrun/AgentsCard.tsx` |
| B37 | §4.2 / §5.2 · 1440 | No face puts a meeting into a Project. A meeting dragged onto the Project drawer draws the ghost and the dotted path, and on drop nothing happens, with no "not here". The record has no Project verb. The project detector did not file it. Workaround: `POST /api/projects/{id}/meetings/{mid}`. | "How do I put this meeting in my Project?" | `4.2-drag-meeting-over-project-1440.png`, `4.2-drop-meeting-on-project-1440.png` | STOPS | `web/src/desk/hand/drag.ts:5-6` ("A drop on anything that is not a target does nothing"); `web/src/desk/hand/begin.ts:60-65` (targets: Conductor and agents only); route with no face caller `holdspeak/web/routes/projects.py:402` |
| B38 | §5.2 · 1440 + 393 | The Project was made through the Door with `karolswdev/holdspeak-dayone-rehearsal-1558` (2 watches). Its confirm line reads "NO REPOSITORY" and Hand is disabled. No verb there or anywhere fixes it: nothing registers a local clone or clones the repository. `registerRepository` exists in the store, and no face calls it. Workaround: `POST /api/repositories {path}`, which also drops a new loose "holdspeak-dayone-rehearsal-1558" icon on the desk. | "It has my repo. Why no repository?" — he stops. | `5.2-dropped-confirm-line-1440.png` | STOPS | `holdspeak/services/agent_hand_service.py:271-275` (`no_repository`), `:143-203` (`resolve_project_repository`: needs a registered clone); `web/src/desk/store/dataSlice.ts:517` (no caller) |
| B39 | §5.2 · 1440 + 393 | In YOLO no face can hand to Codex. The drag onto the Conductor gives Claude Code; the drawer's "Hand to agent" gives Claude Code (both widths); the confirm line has no agent choice. A drag onto "Codex" inside the Conductor window does nothing: only a running `coder:` icon is a target. ⌘K "Hand to agent" reads "Select an object" with the item selected in the drawer, and Enter does nothing. Workaround: `POST /api/agent/hand` with `profile: codex-default`. | "I use Codex. How do I pick it?" | `5.2-drag-over-codex-1440.png`, `5.2-confirm-codex-1440.png`, `5.2-palette-hand-1440.png`, `5.2-verb-confirm-393.png` | STOPS | `web/src/desk/hand/HandConfirm.tsx:54-69` (agent fixed by the target); `web/src/desk/hand/begin.ts:60-65`; the sheet's picker is only in Secure/Normal: `web/src/desk/components/HandSheet.tsx:347` |
| B40 | §5.2 · 1440 | In the drawer's icon view a long object name is never cut: the action item and the PR icon each wrap to 14 lines. The Conductor window does the same for the agent ("Codex: contributing … its test"). | Windows 1.0. | `5.2-project-drawer-1440.png`, `5.3-conductor-during-trust-1440.png` | UGLY | drawer icon label (`web/src/desk/drawer/DrawerWindow.tsx`, label CSS not located) |
| B41 | §5.3 · tmux | Codex opened "Folder access … Note: You're in a subdirectory of a Git project. Trusting will apply to the repository root: …/holdspeak-dayone-rehearsal-1558 … Trust this folder? › 1. Trust and continue". The hub never pressed it: 3 minutes, `trust_state: not_seen`. The parser joins every non-blank row between the header and the question, the Note included, so the joined "path" never equals the worktree. (In the rig the screen also shows `/private/var/...` where the hub has `/var/...`; the owner's `/Users/karol` has no such symlink, but the Note rows break the match there too.) I pressed Enter in the pane at 16:29:42; the hub then typed the brief. | The agent never starts, and nothing on the desk says why. | `5.3-lane-during-trust-1440.png`, `5.3-lane-3min-1440.png` | STOPS | `holdspeak/delivery/first_message.py:147-176` (`parse_codex_trust_prompt`: `path_rows` = every row up to the question), `:179-184` |
| B42 | §5.3 · 1440 + 393 | During that stall the face lies. The Conductor says "1 AT WORK" with a blue working badge. The lane shows BRIEF lit "16:26 · 514 words", while the brief was not sent until 16:29 (`instruction_state: pending`). "Raw" makes no visible change. At 393 the Conductor list later read "AGENT · 1 MIN" for an agent that had run 19 minutes. | "It's working." It is not. | `5.3-conductor-during-trust-1440.png`, `5.3-lane-during-trust-1440.png`, `5.3-lane-raw-1440.png`, `5.3-conductor-393.png` | LIES | lane track BRIEF station: `web/src/desk/lane/LaneWindow.tsx` (track); Raw: `lane-raw` |
| B43 | §5.3 · 1440 + 393 | YOLO is meant to "pass every call in the worktree". It held `cat > CONTRIBUTING.md <<'EOF' …` (rule `here_document`, scope `unparsed`, `yolo_unparsed_command`). After that: `cat > tests/probe.txt <<'EOF'`, `probe2.md`, `probe3.md`, `apply_patch '*** Begin Patch …'` (twice), `git push -u origin HEAD`, and a probe `echo … > /tmp/hs_write_probe.txt`. In total 9 holds in 19 minutes. The agent said "The content triggers the denial, not the path. Bisecting which part" and tried writes in `/tmp`. | "YOLO? I approve every file it writes." | `5.3-needs-held-1440.png`, `5.3-held-heredoc-2-1440.png`, `5.3-held-applypatch-1440.png`, `5.3-needs-held-push-393.png` | STOPS | `holdspeak/tool_gate_rules.py:328-329` (any `<<` outside `$(cat <<'TAG' …)` is unparsed), `:361-365`; `holdspeak/operation_policy.py:414` |
| B44 | §5.3 · 1440 | A held call whose text is cut ("… +1075 CHARS") shows only "Deny · Open". "Open" opens the lane, which shows no held call and no Approve. Approve exists nowhere, so the owner can only deny or wait. One such hold expired after 4 minutes with no decision (`expires_at` = created + 240 s); the Needs row went away, and the agent said "A desk hold expired without a decision". | "Open shows nothing. How do I allow it?" | `5.3-held-open-1440.png`, `5.3-held-applypatch-1440.png` | CONFUSES | Needs held-call row (`web/src/desk/needs/needsFace.ts`, approve only on a whole command); CONDUCTOR.md R1 "Approve and Deny on the held-call row need a canvas" |
| B45 | §5.3 · 1440 + 393 | After 9 held calls (3 approved, 5 denied, 1 expired) the lane's HELD station still reads "—". The rail lists the runs that passed and no hold or denial. | "The lane says nothing was held." | `5.3-lane-after-answer-1440.png`, `5.3-answered-from-lane-1440.png` | LIES | `web/src/desk/lane/LaneWindow.tsx` (HELD station source) |
| B46 | §5.3 · 1440 | Re-brief (lane → Re-brief → text → Send) was refused: "NOT SENT · a current registered session and pane identity are required — nothing was typed". At that moment `/api/coders/sessions` listed the Codex session (PreToolUse 22:34:36Z), and the launch was `registered`. Answers typed through the Ask box did work later. I gave both steers by typing in the tmux pane. | "Re-brief is the one verb I need, and it refuses." | `5.3-rebrief-open-1440.png`, `5.3-rebrief-sent-1440.png` | STOPS | `holdspeak/coder_steering.py:577-588` (`registered_steering_destination_required`) |
| B47 | §5.3 · 1440 | When the PR was open, every Codex turn end became a wait, and the YOLO responder (Cadence draft on the LAN) answered six in 60 s, typed into the agent as the owner: "Confirmed — PR #1 is open … I'll mark action:… as done on the desk … You're clear." / "All good, thanks. You're clear." / "You're welcome — take care!" / "You're welcome! Glad I could help. 🚪" / "Goodbye! 👋" / "Hi! Go ahead and create the CONTRIBUTING.md in the rehearsal repository with the three rules …". The last one orders the finished agent to do the work again; the agent declined. The "I'll mark … done" claim was false until the merge. | "Who is talking in my name? It told the agent to start over." | `5.3-lane-chitchat-1440.png`, `5.3-lane-autoanswered-1440.png`, `codex-pane.txt` | LIES | `holdspeak/services/agent_responder.py:12-29` (ROUTINE rule; the 6-per-hour cap was reached in 60 s), `:129` (`answer_prompt`) |
| B48 | §5.3 · 1440 + 393 | Every Codex turn end shows as "CODEX ASKS" and a Needs row "ASKS · JUST NOW · Open · Answer", including "Understood — stopping here … Good luck with the merge!". The ASKS station stays "now" after the answer. | "It keeps asking me things that are not questions." | `5.3-needs-after-pr-393.png`, `5.3-lane-after-answer-1440.png` | CONFUSES | CONDUCTOR.md "Waits": a Codex `Stop` is a wait TO ANSWER; `web/src/desk/lane/LaneWindow.tsx:456` |
| B49 | §5.3 · tmux | The brief tells the agent "update the status of this item … file notes … with the holdspeak MCP tools". The agent reported: "the holdspeak MCP surfaced only read-only resources in this launch, so I couldn't file a note or flip the item status myself". Cause not verified (Codex MCP config, or the palette). | "The brief promises tools the agent does not get." | `5.3-lane-autoanswered-1440.png` (rail SAYS), `codex-pane.txt` | LIES | brief text: `holdspeak/services/agent_brief.py`; Codex MCP args: `-c mcp_servers.holdspeak.*` (CONDUCTOR.md K6) |
| B50 | §5.4 · 1440 | The lane's PR card and the PR icon in the drawer are titled "#1 Add a contributing file to the rehearsal repository …" (the item), not the PR's title "Add CONTRIBUTING.md with the three pull request rules". Open PR opened the right URL (`…/pull/1`); the headless browser has no GitHub sign-in, so GitHub showed "Page not found" for the private repository (rig only). | Small doubt: "is that my PR?" | `5.3-lane-chitchat-1440.png`, `5.4-room-after-sweep-1440.png` | LIES | lane PR card (`lane-pr`, `web/src/desk/lane/LaneWindow.tsx`); origin title from `web/src/desk/agentFlights.ts` |
| B51 | §5.4 · 1440 | After the merge on GitHub nothing changes: the lane still shows "MERGE yours" and the Room "NEXT CHECK 17:31" (43 minutes). The only way to close it now is Go ▸ Rhythm ▸ "Run now", a different window with no word about merges. After Run now the sweep receipt read "0 ROOMS · 1850 MS", but the Room receipt did land ("DONE · ADD A CONTRIBUTING FILE … · PR #1 MERGED · 16:48") and the item left follow-through. | "I merged it. Why does it still say mine?" | `5.4-room-right-after-merge-1440.png`, `5.4-rhythm-run-now-1440.png`, `5.4-room-after-sweep-1440.png` | CONFUSES | `holdspeak/services/heartbeat_service.py:38` (`_DEFAULT_SWEEP_EVERY = 15`); Room footer next check (file not located) |
| B52 | §6 · 1440 | The `Merged: <title> (PR #1)` row never appears. The model draft wrote "The contributing file … was merged into the rehearsal repository", with no PR number or link. Publishing it froze the PR into the update's manifest as reported. The deterministic draft made after that has no merge line at all. The `conductor.pr_merged` observation exists in `project_observations`. | "The one thing I did today is missing from the update." | `6-draft-model-1440.png`, `6-draft-deterministic-1440.png`, `sent-update.md` | LIES | `holdspeak/services/project_update_service.py:456-520` (`period_closures`: a key any published update froze is skipped); the model draft path drops the line (not located) |
| B53 | §6 · 1440 | The update's generator label reads "MODEL (IA_69187BBA560B4CE1B420B6C8E3DF865F)". "Draft with model" carries "LOCAL + CLOUD" for a LAN-only model. The model added "**[UNVERIFIED]**" to four empty sections, and those tags went out in the sent file. The sent file has no title, Project name, date or link. | Raw ids, a false cloud chip, and a file he cannot forward as it is. | `6-updates-open-1440.png`, `6-draft-model-1440.png`, `sent-update.md` | UGLY | `web/src/features/project-room/update/UpdatePosture.tsx` (`update-generator-label`, `update-draft-model-action`) |
| B54 | §7.2 · 1440 | At 16:53 the Brief is still the one generated at 16:06, before any engine: "No engine for summaries · Choose an engine", "PEOPLE · UNAVAILABLE", titled "Monday Brief" on a Wednesday. Rhythm ▸ Generate changed nothing. It knows nothing of the meeting, the decision, the agent, PR #1 or the merge. (Part A's B04, now also stating a false blocker.) | "The brief says I have no engine and nothing happened today." | `7.2-brief-open-1440.png`, `7.2-brief-regenerated-1440.png` | LIES | `holdspeak/services/monday_brief_service.py:420` (one brief per local date) |
| B55 | §7.2 · 1440 | ⌘K for the PR title, "CONTRIBUTING" or "PR #1" finds no PR. It finds the action (marked "done") and the same text as a DECISION (◈). The Room's standing page "What did we decide" lists the action item, not the decision ("Keep the old ledger read-only …"). | "Search does not know my PR, and it calls my task a decision." | `7.2-palette-add-1440.png`, `7.2-palette-pr-1440.png`, `5.4-room-right-after-merge-1440.png` | LIES | confirm writes a decision record for the action (`decision_id: dec-e6be9c3a373c4317` on the action); search index (not located) |
| B56 | §3.4 / §5.4 · 1440 | The "MEETING READY · Payments ledger sync · 2 to review · 1 open · Open proposals" card stays on the Meetings window, the Room and Rhythm long after both proposals were confirmed and the action was done (16:21 → 16:53). The meeting row read "RUNNING" while the card said READY. | "Still 2 to review?" | `3.5-confirmed-1440.png`, `5.4-room-after-sweep-1440.png`, `5.4-rhythm-run-now-1440.png` | LIES | `web/src/components/AmbientLayer.tsx:239-248` (part A's B13) |
| B57 | §3.5 · 1440 | Whisper heard "Karol" as "Carol". The confirmed action has owner "Carol", so it lands in follow-through WAITING (delegated), not in Needs you. The Room shows "ACTION · OWNER CAROL · BY FRIDAY", and the agent repeated "owner: Carol". Confirm has no "this is me" step. | "Who is Carol? That is me." | `3.3-record-open-1440.png`, `5.4-room-after-sweep-1440.png` | CONFUSES | proposal Confirm without an owner edit (`holdspeak/web/routes/proposals.py:100`) |

## Unknown (seen, cause not verified)

- Whether the 15:58 `git credential-osxkeychain store` wrote a github.com item into the real Keychain (rig incident above).
- Why Re-brief was refused while the session was registered (B46). It could be the rig's `TMUX_TMPDIR` (the steering grant may check the pane through a tmux call with another environment) or a real bug. `/api/coders/status` read `tmux_reply_available: false` and `sessions.count: 0` while `/api/coders/sessions` listed the session.
- What a Hand to Claude Code with no sign-in does (B36): not pressed.
- The agent said `rm -f` was "blocked". No such hold reached Needs you, and its cause was not read.
- Every ⌘K open logged `503 /api/people/relationships` (no People set up on this desk). The effect on the palette was not seen.
- The sweep receipt said "0 ROOMS" and still closed the origin; which part of the sweep did the K4 close was not read.

## What worked cleanly

- GitHub: Recheck → "karolswdev ✓ CONNECTED" in under 6 s. The Door's repository picker listed his 30 repositories in 4 s, and the pick showed "0 open PRs · CI —" and "1 SOURCE · 2 WATCHES". Create Project went straight to a Room that is on track and answers on the LAN.
- Meeting: WAV import 3.5 s with a good title ("Payments ledger sync", not the file name); LAN summary 22 s, short and correct. Confirm for both the action and the decision on the record (#983). The meeting, decision, action and summary artifact appear as objects in the Project drawer.
- Install hooks: one press per agent wrote only to the isolated `CODEX_HOME` / `CLAUDE_CONFIG_DIR` (with Codex trust hashes), and doctor's Coding agents row turned PASS.
- The confirm line at both widths: "→ item · CLAUDE CODE · YOLO · hs/action-… · API.ANTHROPIC.COM", Brief ▸ shows a readable brief with acceptance (7 checks).
- The lane, once running: the rail lists each RUN with its command, ANSWER rows, COMMIT `aaceba6`, "PR #1 opened · review none yet", FILES CHANGED 2, the GITHUB.COM egress chip on Open PR.
- Needs you held-call rows at both widths: the command in full when short, Deny one press, Approve one press (approved `git push -u origin HEAD` from the phone at 393).
- Answer from Needs you at 393 opens the lane's ask with the LAN draft ("Looks good — the acceptance criteria are met …") and the draft chip "192.168.1.43:8080 · LAN". Answer from the lane at 1440 sent at once with a "SENT" receipt.
- The agent followed the brief: worktree branch only, `main` untouched, item ref and test named in the PR body.
- Merge → Run now → the origin closed with the PR as evidence (follow-through empty, launch `complete`), the Room receipt "DONE · … · PR #1 MERGED · 16:48", and the tmux session and worktree were cleaned up 55 s after the merge.
- Draft with model 29 s, Publish, Send to the Folder 0.5 s with "✓ SAVED ~/Documents/HoldSpeak/Sent/2026-10-07-payments-ledger-cutover-rev-1-1d328e5f.md". The file opens and reads as markdown.
- ⌘K finds the meeting, the decision and the action by keywords, with the action marked "done".
