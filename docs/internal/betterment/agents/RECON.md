# Agents: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked the
job of an architect who hands work to coding agents and supervises them, on
a fresh desk, at 1440x900 and 393x852. I did not fix anything. All shots are
in `shots/` (85 files). The rig is in the footnote.[^rig]

The agent in this walk is a **fake Claude Code** (`rig/fake_claude.py`). It
is a small script named `claude` that speaks Claude Code's real hook protocol
(it runs the hook commands from the `--settings` file that the launch gives
it), prints work lines, asks one question, waits for the answer on its
terminal, then shows a Bash permission prompt, waits for a key, and finishes
with "Done". His real `claude`, `codex` and `pi` never ran. Every line the
fake read from its terminal is in its log, so "the answer reached the agent"
is a fact here, not a guess.

The job I walked: get ready, hand an item to an agent, see it start, see it
ask, answer it, approve a command, see that it finished, run three at once,
hit the limit, stop one, survive a restart, and find the related tools
(Delivery board, Terminals, New Agent).

## The headline

**The loop works under the face.** For the first time on record, the live
terminal and the answer delivery were observed end to end:

- The brief reached the agent 5 s after Launch (fake log, 19:28:00).
- The question showed in the Conductor within about 10 s (`15-conductor-asks-1440.png`).
- An answer typed in the lane reached the agent's terminal in about 1 s
  (fake log: `ANSWER RECEIVED: '1 - config/flags.yaml, shared with staging'`, 19:38:36).
- A key (Enter) pressed in the lane reached the agent's permission prompt
  (fake log: `PERMISSION KEY RECEIVED`, 19:31:54).
- The live terminal (Raw) streamed the pane: `RAW LINES 93 Δ 6s` (`18b-lane-raw-later-1440.png`).

**The face around it fails the architect.** He cannot find the verb, the
desk answers for him without telling him, a finished agent says "Working"
forever, a permission card does not say what the command is, answering
takes an "ARM" step, and after a restart dead agents keep asking.

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured system time.

| # | Step | What I pressed | What I saw (exact text) | What he expects | Where I got stuck | Presses | Wait | Shots |
|---|---|---|---|---|---|---|---|---|
| 0 | First open | Load the page | `Get ready` … `Optional setup` › `Agents · 3 AGENTS FOUND` · `Hooks tell HoldSpeak when Claude Code or Codex works, waits or stops.` · `SIGN-IN UNKNOWN` · `Install hooks` | Agents found and ready | "Sign-in unknown" on all three (a rig switch, fair), and "hooks" is a word he must learn | 2 | 3 s | `00-desk-first-open-*`, `01-first-run-optional-setup-1440.png` |
| 1 | Open the Conductor | Dock ▸ Conductor | `No coder ready · 3 CODERS · ON THIS MAC` · `Claude Code · No hooks · Install hooks` · `Hooks: see the coder's work, hand it work` | A place to start an agent | No verb to start one. Its word is "coder"; the Desk menu and Search say "Agent" for something else | 1 | 2.6 s | `03-conductor-empty-*` |
| 2 | Install hooks | `Install hooks` | `1 ready` · `Claude Code · Ready` · `HOOKS INSTALLED · CLAUDE CODE · 19:24` | – | Works in one press | 1 | 3 s | `04-conductor-after-install-hooks-1440.png` |
| 3 | Hand a note to an agent | Search "Rollback test" ▸ Enter (the note opens) ▸ click the note ▸ Object | `Hand to coder` is greyed; the menu foot says `Select an object` | The note in front is the object | The Object menu needs a selected desk icon, not the window in front. The note window's own foot has `Copy`, `Dictate about this`, `Develop this thought`: no hand verb | 4 | – / 60 s | `05-search-note-1440.png`, `06-note-open-1440.png`, `07b-object-menu-note-focused-1440.png` |
| 4 | Hand the meeting's action instead | Search "Draft test scaffolding" ▸ Enter | Nothing visible opened | The action opens | Enter on an ACTION result does nothing I can see | 2 | – / 20 s | `09-action-open-1440.png` |
| 5 | Find the action another way | Needs you ▸ the action's `More` | `Open · Defer · Decline` | `Hand to agent` here | Needs you lists the action but has no hand verb | 2 | – / 20 s | `10-needs-you-1440.png`, `11-needs-you-more-1440.png` |
| 6 | Open it | `More ▸ Open` | The **Platform** Room opens; the action row has `Hand to coder` and `Open` | – | Found it, in a third window | 1 | 2.5 s | `12-action-opened-1440.png` |
| 7 | Hand it | `Hand to coder` | Sheet: `CODER` (three cards, `SIGN-IN UNKNOWN`), `BRIEF · 3 SOURCES · 3.5 KB` (the action, `1:1 with Theo`, `Memory 8 LINES`), `ACCEPTANCE · 7 CHECKS`, `WHERE ~/REPOS/PLATFORM · NEW WORKTREE · HS/ACTION-ACTION_5F5EF5B8…`, `CONTROL · YOLO`, `API.ANTHROPIC.COM`, `Launch` | – | Good: the brief is grounded and the egress chip is honest. No place to add a sentence of my own. The branch name is an internal id | 1 | 3 s | `13-hand-sheet-1440.png` |
| 8 | Launch | `Launch` | `LAUNCHED · BRIEF PENDING` (4 s), then `LAUNCHED · BRIEF SENT`. A new desk icon `Claude Code: test s… agent` | The agent's window, or the Agents list | Nothing opens; the sheet stays with `Close` | 1 | brief in 5 s | `14-after-launch-t01s` … `t25s-1440.png` |
| 9 | See it ask | Dock ▸ Conductor | `1 asks · NEEDS YOU · ASKS YOU · ASKED 1 MIN AGO` · the full question · `Answer` | The ask in Needs you too | Needs you still said `7 need you`, all meeting items. Under YOLO the desk holds the question back while it drafts (by design, `agent_responder.py:10-17`). "1 min ago" ten seconds after the ask | 1 | ask shown ≈10 s | `15-conductor-asks-1440.png`, `15-conductor-asks-393.png` |
| 10 | Answer it (YOLO) | I was too slow | 44 s after the ask the desk typed `The desk: Yes, "The rollback flag moves into config/flags.yaml."` into the agent | To see that the desk answered, and why | The question offered "1 for config, 2 for env". The desk answered "Yes, …". The meeting's decision made the meaning right, but the form was wrong. The only trace is the lane foot `THE DESK ANSWERED · 19:28`. Nothing told me | 0 | 44 s | `17-see-the-call-1440.png` |
| 11 | Approve a command | Conductor ▸ `See the call` | Card `WANTS APPROVAL · Claude needs your permission to use Bash`; the lane opens `Claude Code wants approval` with `Raw` and `Re-brief`. No Allow, no Deny | The command, and Allow / Deny | The card does not say which command. To see it: `Raw` (the terminal shows the top of the pane, not the prompt), then `Keys`, then `ENTER`. The command `rm -rf build/ && make release` is in the terminal, below the fold | 4 | – / 90 s | `16-conductor-permission-1440.png`, `18b-lane-raw-later-1440.png`, `20-lane-keys-1440.png`, `20b-lane-terminal-bottom-1440.png` |
| 12 | Read the terminal | `Raw`, scroll | `RAW LINES 93 Δ 6s`, a FIND box, the brief text from the top | The live bottom of the screen | It streams, but opens at the top. With Keys open the terminal shrinks to one line | 2 | 1.5 s poll | `18b-lane-raw-later-1440.png`, `20b-lane-terminal-bottom-1440.png` |
| 13 | See it finish | Wait | The agent printed `Done. … Branch is ready for review; I did not open a PR.` The lane timeline shows it as `SAYS`. The lane title: `Claude Code is working`. Conductor: `1 at work · Working · 1 min ago`, and 8 minutes later `7 min ago · Working` | "Done", marked until I read it | A finished agent reads Working until it is stopped. It also holds one of the three launch slots | 0 | – | `21-after-enter-t12s-1440.png`, `22-lane-after-done-1440.png`, `23-conductor-after-done-1440.png`, `35-conductor-mixed-1440.png` |
| 14 | See it in Today | Dock ▸ Today | `TO DECIDE · The rollback flag moves into config/flags.yaml` … nothing about agents | "1 agent finished", "2 agents need you" | Today has no agent line at all (its Agents section is parked, `ChairHome.tsx:1466-1469`) | 1 | – | `24-today-after-agent-1440.png`, `33-today-with-agents-1440.png` |
| 15 | Run three at once (Normal mode) | Room ▸ `Hand to coder` ▸ `Launch`, twice | Two more launches; the desk shows one icon per agent | – | Works; 2 presses each, from the Room | 4 | 4 s each | `25-hand-sheet-*`, `27-launched-*` |
| 16 | Hand a fourth | Room ▸ `Hand to coder` | `CODER LIMIT REACHED`; `Launch` greyed | A way forward: stop one, or queue | The finished agent from step 13 fills a slot. No queue, no "stop the finished one" | 1 | – | `28-hand-sheet-at-cap-1440.png` |
| 17 | The fleet | Dock ▸ Conductor | Header `1 at work · 2 ASK · 3 OF 3 · 3 CODERS`; two `ASKS YOU` cards; `AT WORK` the finished one | The ones that need me first, the done one marked | The headline counts "at work" (the finished one) and puts the asks in a small chip. On the phone the questions are cut `…` and each Answer opens another window | 1 | – | `29-fleet-conductor-1440.png`, `29-fleet-conductor-393.png` |
| 18 | Answer it myself (Normal) | `Answer` ▸ type `1 - config…` ▸ `Answer` | The lane: full question, `Say or type the answer`, `NORMAL · ARM FIRST · ARM`. After a few seconds a draft: `DRAFT 1 — "Karol decided the flag moves to config/flags.yaml, owned by Theo due Friday." · Use draft · LAN QWEN 3.8 27B`. My Answer gave `ARM FIRST · 19:38` and sent nothing | Answer sends | "ARM" is an extra step that the face blames on me. After `ARM` and `Answer` it reached the agent in 1 s. The draft was right | 5 + typing | 1 s delivery | `30-answer-lane-open-1440.png`, `31-answer-typed-1440.png`, `31-after-answer-1440.png`, `32-armed-1440.png`, `32-after-armed-answer-1440.png` |
| 19 | Needs you with agents | Needs you | Two `CC` rows: `Claude Code: Write the on-call note … ASKS · 3 MIN · Open session · Answer` and `… TO APPROVE · JUST NOW`; below them the same two items as ACTION rows | One row per piece of work | The action and the agent working on it are two rows. "CC" is a code | 1 | – | `34-needs-you-with-agents-1440.png`, `34-needs-you-with-agents-393.png` |
| 20 | Stop the finished one | Conductor ▸ `Open` ▸ `Details` ▸ `Stop` ▸ `Stop · sure? (ends the coder's session)` | `ENDED · stopped_by_owner` · `STOPPED · 19:39 · BY YOU` | "Done ▸ Close" in one press | Stop hides in a fold; the end reason is a code | 4 | 3 s | `36-lane-details-1440.png`, `37-stop-pressed-1440.png`, `37b-after-stop-1440.png` |
| 21 | Restart the Mac (simulated) | Killed the rig's tmux and restarted the hub | Conductor: `2 ask · ASKS YOU · ASKED 4 MIN AGO`, both agents still asking. They were gone | "Stopped by restart · Resume" | Ghosts. `ARM` fails with HTTP 409 and the face still says `ARM FIRST`. The launch count says 0 live while the cards say 2 ask | 3 | – | `38-conductor-after-reboot-1440.png`, `39-ghost-lane-1440.png`, `39b-ghost-answer-1440.png`, `40-lane-ghost-393.png` |
| 22 | Delivery board | Search "Delivery" ▸ Enter | `PLATFORM · INCOMPATIBLE · INCOMPATIBLE · Update source` · `WORK 2 · WAITING · rider:claude · NODE local · BR hs/action-… · WT wt_b08e6 · TARGET TERM_237F2 · OFFLINE` · `Companion repo · owner/repo · ✕ NO LIVE SOURCE` | – | The same two agents again, in machine words. Only Search reaches it. On the phone it did not open | 2 | 4 s | `41-search-delivery-1440.png`, `42-delivery-board-1440.png`, `42-delivery-board-393.png` |
| 23 | Terminals | Search "Terminals" ▸ Enter | A dark pop-over: an empty field, `+ SPAWN`, `no tmux panes` | – | A raw tmux spawner. It does not see the two agents' panes | 2 | – | `47-search-terminals-1440.png`, `47b-terminals-open-1440.png` |
| 24 | New Agent | Desk ▸ `New Agent` | `Edit New Agent`: Name, Role, Instructions, Advanced, `Done`, with the same robot sprite as Claude Code | A coding agent | It is a saved prompt (a recipe). After `Done` it is gone from the desk; Search finds `Reviewer · AGENT`. Search "agent" lists `Chase, Desk, Draft, Interview, Plan · AGENT` (thread modes) | 4 | – | `43-desk-menu-1440.png`, `44-new-agent-1440.png`, `45-new-agent-saved-1440.png`, `46-search-reviewer-1440.png`, `48-search-agent-1440.png` |
| 25 | Phone | Room ▸ `Hand to coder` | The sheet fits; chips are cut (`SIGN-IN UNI`); `Launch · More` at the foot | – | Usable; Dock glyphs have no labels | 2 | – | `49-room-phone-393.png`, `50-hand-sheet-393.png`, `50-hand-sheet-full-393.png` |

Totals for the core job (hand one item, answer it, approve one command, know
it is done): **about 25 presses across five windows (Note, Needs you, Room,
sheet, Conductor, lane), 6 to 8 minutes**, and two parts never work: the
"done" signal and the restart.

## What worked

- Install hooks: one press.
- The hand sheet: a grounded brief (the action, its meeting, memory),
  acceptance checks, a new worktree and branch, the Control mode, and an
  honest egress chip (`API.ANTHROPIC.COM`).
- The launch: brief delivered in 5 s with the credential bootstrap, rider
  hooks and the desk's MCP server (`--mcp-config`) on the agent's command
  line (fake log).
- Hook state: the question reached the Conductor in about 10 s; the
  permission prompt reached Needs you at once.
- The drafted answer (Normal) was correct and named its source decision.
- Delivery of text and keys to the agent's terminal: about 1 s.
- The lane timeline (`BRIEF`, `RUN Read`, `SAYS`, `ANSWER`) is the best
  face in this cluster: it reads like a story of the session.
- The launch cap and Stop work as built.

## What I could not verify

- **The tool gate's held calls** (Approve / Deny on a gate proposal,
  `LaneWindow.tsx:366-377`). My fake shows Claude Code's own permission
  prompt, which is not a gate proposal, so the Approve / Deny path did not
  appear. Unknown.
- **The PR follow-through** (Heartbeat sees the PR, closes the action on
  merge). The rig refuses the real `gh`. Unknown.
- **Codex and pi launches.** Only the Claude path was walked; `codex` and
  `pi` were shadowed by stubs.
- **Desktop notifications.** The rig sets `HOLDSPEAK_DESKTOP_NOTIFY=0`.
- **"Speak answer"** from Today (`ChairHome.tsx:2874`): no agent row ever
  showed in Today, so the verb was not reachable.
- **Why "Hand to coder" needs a desk selection** and not the front window:
  observed, cause not read.
- **Why Enter on an ACTION search result showed nothing:** observed, cause
  not read.
- `27-launch-normal-mode-1440.png` records a rig mistake: my script pressed
  a desk icon whose accessible name also matched "Launch". It is not a
  product defect.

## Verdict

The Conductor does the hard part. A brief from his meeting reaches a real
terminal in seconds, an answer reaches the agent in one second, and the
lane tells the story of the session. The face fails the job of an architect
who runs several agents: the verb hides in a third window, the word is
"coder" here and "Agent" means a saved prompt elsewhere, the desk answers
for him in silence, a permission card hides the command, Answer needs an
ARM step, a finished agent says "Working" and blocks a slot, Today knows
nothing, and a restart leaves ghosts that keep asking. Two more faces (the
Delivery board and Terminals) show the same agents in machine words.

[^rig]: Isolated hub `scripts/graph_walk.py serve --scheduler` on port 8821
    (my range 8821–8829), started by `rig/start_hub.py` with
    `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, all isolation
    switches, `HOLDSPEAK_AGENT_STATE=off`, `TMUX_TMPDIR` inside the HOME,
    `CLAUDE_CONFIG_DIR`/`CODEX_HOME` inside the HOME), run from the code of
    the owner's desk worktree (`wt-daily-delight-delivery-20261017`,
    `217001b2e`; it differs from `main` only in
    `holdspeak/web/routes/setup.py`). `PATH` began with a folder holding the
    fake `claude` (`rig/fake_claude.py`) and two stubs for `codex` and `pi`,
    so none of his agent CLIs could start; `UV_NO_SYNC=1` so the hook
    command never re-synced his desk's virtual environment. A git fixture
    repository inside the HOME (`repos/platform`), registered as the
    Platform project's Delivery Source. Seed through the hub's own MCP and
    routes: People set up, Mira Chen, Theo Okafor, Jun Park; two meetings
    imported from transcripts (Platform sync, 1:1 with Theo), whose action
    items the real LAN engine extracted; two notes; the project Platform.
    Real LAN engine `qwen3.8-27b` at `192.168.1.43:8080` (meeting
    intelligence and the drafted answers); nothing faked but the agent CLI.
    Control mode YOLO for steps 0–14, then Normal (set in the isolated
    config file). The "restart" in step 21 is `tmux kill-server` on the
    rig's own socket plus a hub restart on the same HOME. Chromium headless
    via Playwright (`rig/walk.py`), 1440x900 and 393x852 (mobile, touch,
    scale 2). Afterwards the hub and the rig tmux were stopped and the
    scratch HOME removed; no fake process was left.
