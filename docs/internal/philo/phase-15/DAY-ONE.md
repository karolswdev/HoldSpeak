# Day One — the runbook

**v2 · 2026-10-08.** What changed from v1: v1 was the script the rehearsals walked; v2 is the
runbook you follow on your own desk, rewritten from rehearsals 1a, 1b and 2 and lanes 01–21.
v1 is parked verbatim in `DAY-ONE-v1.md`.

This runbook is for your real desk. The rehearsals used an isolated HOME, separate agent
logins, a moved clock and a throwaway repository; you need none of these.

How to read a step:

- **Do**: one press or one check.
- **See**: the words on the face. Tokens are in `CODE`.
- **Else**: what to do if the face reads otherwise.
- **Paid**: the bounce id and the PR that made the step true. "(after #1012)" marks a step that
  is true only when PR #1012 is on main.

Widths: every step works at 1440 (a window) and at 393 (a phone). Where the gesture differs,
the step says so.

---

## 0. Before you start

0.1 **Check** the LAN engine box. Open `http://192.168.1.43:8080` in a browser.
- See: the llama.cpp page. The model is `qwen3.8-27b`. The key is `local`.
- Else: start the box first. HoldSpeak does not start it for you.

0.2 **Check** GitHub. Run `gh auth status` in a terminal.
- See: `Logged in to github.com account karolswdev`.
- Else: run `gh auth login`. HoldSpeak reads this sign-in; it has no sign-in of its own.

0.3 **Check** your coding agent. Run `codex --version` and `claude --version`.
- See: a version for each agent that you will use.
- Else: install the agent and sign in to it. Each agent uses its own sign-in.
- Note: the rehearsals launched Codex only. A launch of Claude Code was never pressed (no key on
  the rig). See §10.

0.4 **Know** where the hub writes. All of it is on this Mac.

| What | Where |
|---|---|
| Your desk (meetings, decisions, Projects, updates) | `~/.local/share/holdspeak/holdspeak.db` |
| Settings | `~/.config/holdspeak/config.json` |
| Project repositories and their clones | `~/.holdspeak/project_repositories.json`, `~/.holdspeak/repositories/` |
| Sent updates (the built-in folder) | `~/Documents/HoldSpeak/Sent/` |
| Agent hooks (after Install hooks) | your Claude Code settings and your Codex config |
| People keys | the macOS Keychain (the first Person you add asks for it) |

0.5 **Install** HoldSpeak (README, Quick start).
- Do: `git clone https://github.com/karolswdev/HoldSpeak.git`, then `uv venv && source .venv/bin/activate`, then `uv pip install -e .`
- See: the install ends with no error. The rehearsal `uv sync` took about 10 s.
- Else: you need Python 3.10+, uv, Node 22.12+ and a C++ compiler.

---

## 1. First run

1.1 **Run** `holdspeak doctor` before the first start.
- See: about 28 PASS and 4 WARN, then one last line `HUB · NOT RUNNING · start it with holdspeak`.
- Expected WARNs: `Where AI runs`, `Dictation AI model`, `Coding agents` (until 1.6). These are true before setup.
- Else: a FAIL names the missing file and its path. Fix that file first.
- Paid: B08 (#986).

1.2 **Run** `holdspeak`.
- See: the hub prints a URL with a token and opens your browser on the first-run page.
- The page is one scrolling page at both widths.

1.3 **Press** "Use a server on my network" on the Local AI card.
- See: the add-engine row with Server address and Key.
- Do: type `http://192.168.1.43:8080` and the key `local`.
- Do not press Set up local AI. It downloads 2.9 GB that a LAN desk does not need.
- Paid: B09 (#985).

1.4 **Press** Check.
- See: `READY · qwen3.8-27b` within about 4 s.
- Else: `UNREACHABLE` means the box is off (0.1). `KEY REQUIRED` or `KEY INVALID` means the key is wrong.
- Paid: B05 (#985), keys (#966).

1.5 **Press** "Use this for summaries".
- See: the receipt `USING · QWEN3.8-27B · SUMMARIES · DEFAULT SET` on the card. The menu-bar chip reads `→ LAN · 192.168.1.43`.
- Else: if any face says "No engine for summaries" after this, it is a defect. Note it.
- Paid: B10 (#985), B33 (#1001), the false blocker (#967).
- Speech stays on this Mac (Whisper). Set up speech · 144 MB appears beside the LAN row on a Mac without Whisper.

1.6 **Press** Install hooks on the Agents card.
- See: the card reads `2 AGENTS FOUND` and tmux as a `TOOL`. After the press: `CLAUDE CODE · HOOKS IN` and `CODEX · HOOKS IN`.
- Else: if a row has no Install hooks, that agent is not installed (0.3).
- Paid: B17 (#986), B34 B35 (#1001).

1.7 **Read** the Connections line on the same page.
- See: `SIGNED IN · KAROLSWDEV · FROM GH CONFIG`. This is gh's own config. No check ran yet.
- See also: the footer reads `NOT CHECKED` until a real check runs. This is true, not a failure.
- Paid: B31 (#1001).

1.8 **Type** your name and your aliases in the You card.
- Do: add "Karol" and, as an alias, any spelling Whisper uses for you ("Carol").
- See: `SET`. No Save button.
- Why: a meeting owner "Carol" then counts as you in Needs you and the Brief. See B78 in §10.
- Paid: B57 (#1001).

1.9 **Press** Continue later, or scroll to Ready.
- See: the Desk. The Dock has sprites for every place. The screen has five notes: Start here, About me, 1:1 prep, Current priorities, Weekly update.
- Paid: B19 (#989), B20 (#986).

---

## 2. The morning

2.1 **Open** the Brief. At 1440: Window ▸ Chair ▸ Brief. At 393: Go ▸ Brief.
- See: the window comes to the front, titled `Brief · Thursday 8 Oct 2026` (today's day and date).
- The Brief makes itself at 06:00. If the hub starts after 06:00, it makes it at once.
- No model runs and nothing leaves the Mac.
- Paid: B04 B16 (#980), B54 (#975), B59 (#1010).

2.2 **Read** the Brief rows.
- See, in this order, newest first in each kind: a merged PR, a sent (or published) update, an opened PR, a confirmed decision, a done action, an agent launch, then recorded and added things.
- Each row has its local time and opens its object. The Chair shows three rows; the window shows all.
- Else: a row in JSON, a hash or a UTC stamp is a defect.
- Paid: B58 B73 (#1010).

2.3 **Read** a `NOT READ` row if one is there.
- See: `NOT READ · People (locked) · Generate for the full brief`, and the receipt `GENERATED · PARTIAL`.
- Why: the 06:00 Brief does not unlock People.
- Do: press Generate. It makes today's Brief again with People read.
- Paid: B04 (#980), the key-free Brief (#975).

2.4 **Read** the one Needs number.
- See: the same number on the Needs drawer head, the Dock badge and the menu-bar bell.
- Every row says its kind: `ACTION`, `AGENT`, `HELD`, a decision, a source.
- Paid: B11 B12 (#980).

2.5 **Read** a `QUIET UNTIL` row before 08:00 (after #1012).
- See: a source row `QUIET UNTIL 08:00`. It is not counted in the one Needs number.
- Why: the Heartbeat sleeps 22:00–08:00. The first check after 08:00 runs at once.
- Else (before #1012): the same source reads `STALE` and is counted. Wait until 08:00, or press Retry (8.4; a GitHub Retry carries the `GITHUB.COM` badge).
- Paid: B60 (#1012).

2.6 **Open** The week. At 393: Go ▸ The week.
- See: this week's decisions and due items, or `NO CALENDAR · Connect`, or `NOTHING THIS WEEK`. Never an empty window.
- Paid: B07 (#980). The week was not rehearsed with a real calendar (§10).

---

## 3. A meeting

3.1 **Open** Meetings and **press** Import.
- See: the RECORD tab with a drop zone and a second Import.
- Do: drop the WAV file, or pick it and press Import. This is two presses (B84, §10).
- Paid: the final status (#968).

3.2 **Wait** for the row to finish.
- See: the title from the recording (not the file name), then `<N> WORDS · NOT RUN`.
- Import does not run the summary. `NOT RUN` is true.
- Else: `IMPORT DID NOT START` or `INTERRUPTED BY A RESTART` names the cause. Import the file again.
- Paid: B14 B30 (#985 #982), B01 (#982).

3.3 **Read** the transcript lamp.
- See: no lamp, or `WARN · <N> UNCLEAR SPAN`. Each unclear part is marked `[unclear m:ss–m:ss]` in the text.
- HoldSpeak never deletes the words it heard. A Whisper loop shows its words and the mark.
- Paid: B01 (#982).

3.4 **Press** Run summary on the meeting's row.
- See: `RAN · <n> S` (6 s to 22 s on the LAN box), the summary once, and the `MEETING READY` card in Capture.
- The card count is live. It leaves at zero.
- Paid: B13 B56 (#1001), the summary slab (#968).

3.5 **Open** the meeting's REVIEW tab.
- See: each decision and each action item with Confirm, Defer and Decline.
- Else: `DECISIONS · NOT EXTRACTED · <engine>` means the model sent no decisions. An empty list means it found none.
- Paid: B02 B03 (#983).

3.6 **Press** Confirm on each decision and action item that is true.
- See: the row reads confirmed. A confirmed action keeps its kind: the Room reads `Action:`.
- You can also Confirm from the Needs row.
- Known: an action may read `NO SOURCE · ⚠ UNSUPPORTED` when the transcript says it (B77). The owner may read "Carol" (B78).
- Paid: B02 B03 (#983).

3.7 **Press** "Add to Project ▸" on the open meeting, then the Project.
- See: `IN <Project>`.
- Do not drag the meeting onto the Project drawer. The drop does nothing (B76, §10).
- Paid: B37 (#1000).

---

## 4. A Project

4.1 **Press** New ▸ Project. At 1440: the Desk menu. At 393: Go ▸ New ▸ Project.
- See: the Door.
- Do: type the outcome. It becomes the Project's name.

4.2 **Press** "Choose a repository" on the GitHub row (after #1012).
- See: your repositories in about 4 s.
- Else (before #1012): the Door reads `NOT SET UP · Connect`. Open Settings › Connections › GitHub and press Recheck. The Door then offers "Choose a repository".
- Paid: B75 (#1012), B31 (#1001).

4.3 **Pick** the repository.
- See: the pick, `1 SOURCE`, its watches. No "0 open PRs".
- Paid: the Door (#1000).

4.4 **Press** CREATE.
- See: the Room opens. The receipt names the registered repository.
- An empty Project reads `NEW`.
- Paid: B25 (#989), B38 (#1000).

4.5 **Know** what the clone does.
- Nothing clones at CREATE. The first Hand to an agent clones the repository.
- The clone lives in `~/.holdspeak/repositories/<owner>/<name>/<name>` (the name twice; B86, §10).
- It is bound to github.com. A clone with another origin is parked beside it as `.not-github-<stamp>`.
- Get Info on the Project shows the clone's Folder.
- Else: `REPOSITORY · NOT READ` with Retry means the registrations file cannot be read. HoldSpeak does not overwrite it. Press Retry.
- Paid: B38 B39 (#1000).

---

## 5. Hand to an agent

5.1 **Open** the Project drawer and **select** the action item.

5.2 **Press** Hand to agent.
- See: the confirm line `→ <item> · CLAUDE CODE · YOLO · hs/<branch> · <egress chip>`, with Brief ▸, Cancel and Hand.
- The first agent is the first one with a known sign-in. `SIGN-IN UNKNOWN` on the line means HoldSpeak cannot see that agent's sign-in.
- Paid: B36 B39 (#1001 #1000).

5.3 **Press** the agent name on the line to flip it (Claude Code ↔ Codex).
- See: `CODEX · YOLO · …` and the chip `API.OPENAI.COM` for a Codex signed in to OpenAI.
- The Project remembers your choice.
- Paid: B39 (#1000).

5.4 **Press** Brief ▸ to read what the agent gets, then **press** Hand.
- See: the receipt `CLONED · KAROLSWDEV/<NAME> · hh:mm`, then the agent's lane.
- See on the lane: `SENT · hh:mm` when the brief is typed. Codex has no folder-trust stall.
- Paid: B41 B42 (#996).

5.5 **Know** what YOLO lets pass.
- Passes with no hold: reads of git config, `gh --version`, `gh auth status`, `gh pr view`, file writes in the agent's worktree (heredocs too), a script in its worktree, `echo "$?"`, the commit, the push of its own branch.
- Holds: a write outside the worktree, a git config write, a push to another branch, a pipe into an interpreter (`RUNS CODE · <name>`), a `cd` to a missing folder (`FOLDER NOT RESOLVED · <dir>`), a `$(…)` used as a path or a program.
- Paid: B43 (#998), B62 (#1011).

5.6 **Answer** a `HELD` row in Needs you.
- See: `HELD · <reason>` with the command, Deny and Approve. One press each.
- A hold expires after 4 minutes with no decision.
- Paid: B45 (#998).

5.7 **Open** a cut call in Raw.
- See on Needs: `CUT · APPROVE IN RAW`, with Deny and Open.
- Do: press Open, then Raw. Raw shows the whole command with Approve and Deny.
- See: `APPROVED · hh:mm` or `DENIED · hh:mm`. If someone decided first: `NOT DECIDED · hh:mm · ALREADY <state>`.
- Else: `HELD · <reason> · CUT · n OF m CHARS` with Deny only means the hub does not have the whole command. Deny it.
- Paid: B44 B63 (#1011).

5.8 **Press** Deny when a call must not run.
- See: the agent gets the reason, for example "denied from the desk: OUTSIDE THE WORKTREE · /tmp/pr_body.md … Do not try it again in a different form".
- Paid: B66 (#1011).

5.9 **Read** the lane's HELD station.
- See: `<n> HELD · <n> APPROVED · <n> DENIED · <n> EXPIRED`.
- See: `THE DESK ANSWERED` on a routine question the desk answered for you from the brief.
- A finished report reads DONE. It is not a Needs row.
- Paid: B45 B47 (#998), B48 (#996), B68 (#1011).

5.10 **Press** Re-brief to give the agent a new instruction.
- See: `QUEUED · AFTER THIS TURN` while the agent works, then `SENT · hh:mm`.
- Do: press Take back if you no longer need it.
- See: `TAKEN BACK`, or `NOT TAKEN BACK · ALREADY SENT`.
- Paid: B46 (#996), B67 (#1011).

---

## 6. The PR and the merge

6.1 **Wait** for the PR.
- See: the lane's PR station `#<n> <PR title>` within one 2-minute poll after the agent opens it. No press.
- Paid: B50 (#996), B65 (#1010).

6.2 **Merge** the PR on GitHub (your usual way).

6.3 **Read** the Room.
- See, within about 2 minutes and with no press: `DONE · <PR title> · PR #<n> MERGED · hh:mm`, with Open PR and the `GITHUB.COM` chip.
- See: the agent's worktree is removed and its session ends. The action is done.
- See (after #1012): the decision row reads `DONE · hh:mm`, not CONFIRMED.
- Paid: B51 (#1002), B70 (#1012).

---

## 7. The update

7.1 **Open** the Room › Updates and **press** Draft with model.
- See: the chip `UPDATE DRAFTS · <host>` before you press. The draft comes in about 30 s.
- Draft (with no model) is deterministic and takes under 1 s.
- Paid: B53 (#1002).

7.2 **Read** the claims in the editor.
- See: the label `MODEL · OPENAI COMPATIBLE`. Each claim has its chips. A model sentence reads `INFERENCE · UNREVIEWED`.
- See: one `Merged: <PR title> (PR #<n>) <link>` row for each merge in the period.
- See (after #1012): a model sentence that repeats a merged PR is dropped. The list chip reads `QWEN3.8-27B · 192.168.1.43:8080 · LAN`.
- Paid: B52 (#1002), B71 B72 (#1012).

7.3 **Press** Accept or Reject on each claim row, before Publish (after #1012).
- Do: press Accept on a sentence that is true. Press Reject on a sentence that is false.
- See: a row that will not be sent reads `OMITTED`. Every unreviewed model sentence starts as `OMITTED`.
- See: each press leaves `REVIEWED · hh:mm`. Accept removes `OMITTED`; Reject keeps it.
- See: a line that you type and save counts as your own reviewed claim.
- Else: `NOT REVIEWED · <reason>` with Retry means the review did not save. Press Retry.
- Else (before #1012): there is no Accept or Reject. An `[UNVERIFIED]` claim is left out; model sentences go out as they are.
- The sent file's last line counts what is left out: `<N> claims not checked, kept on the desk.` The stored update keeps every claim.
- Paid: B64 (#1012), B53 (#1002).

7.4 **Press** Publish.

7.5 **Press** Send in the Send well.
- See: the destination `HoldSpeak/Sent` (the path shows on hover), Check, the preview, then `✓ SAVED ~/Documents/HoldSpeak/Sent/<date>-<project>-rev-1-<id>.md`.
- Else: `✗ REFUSED · NOTHING VERIFIED · NOTHING SENT`. No claim in the update is verified. Do one of these, then Publish and Send again:
  - press Accept on one true sentence (7.3);
  - type one line of your own and save it (a fresh Project's empty update needs this);
  - wait for a merge: a verified `Merged:` row is enough to send.
- Paid: B23 (#989), NOTHING VERIFIED (#1002), B64 (#1012).

7.6 **Open** the sent file. Its shape:

```
# <Project> · Update · <date>

## Progress
- Merged: <PR title> (PR #<n>) <link>

## Decisions
## Risks & Blockers
## Dependencies
## Next Actions
## Source Coverage

<N> claims not checked, kept on the desk.
```

- A section with nothing in it reads `Not checked.` or "No … in this window." (B87, §10).
- Names, never ids. Paid: B53 (#1002).

---

## 8. The second morning

8.1 **Start** the hub after 08:00 if you can.
- Before 08:00 the Heartbeat sleeps. Sources read `QUIET UNTIL 08:00` (after #1012) or `STALE` (before #1012).

8.2 **Open** the Brief (2.1).
- See: yesterday's merged PR, sent update, opened PR, confirmed decision, done action and agent launch, each with its time.
- Limit: the Brief covers yesterday 17:00 until now (Monday: from Friday 17:00). Work done before 17:00 yesterday is in yesterday's Brief only, after a Generate (B90, §10).
- The open Brief window updates itself when the hub writes a new Brief, and when you come back to the page.
- Paid: B58 B59 (#1010).

8.3 **Read** the source rows in Needs you.
- See (after #1012): `GitHub · <owner>/<repo>`, `Meetings`, and times with their day: `yesterday 21:23`.
- Paid: B74 (#1012).

8.4 **Press** Retry on a source row.
- See: Retry on a GitHub source carries the `GITHUB.COM` badge (it calls GitHub).
- See (after #1012): `CHECKED · Meetings · hh:mm`, or `NOT CHECKED · <source> · <reason>`.
- Else: `NOT CHECKED · <source> · no answer` means the connector did not answer. The source stays as it was. Check gh (0.2), then press Retry again.
- Else (before #1012): Retry only reloads the list.
- Paid: B61 (#1012).

8.5 **Open** the Room.
- See (after #1012): one state per source: `STALE · CHECKED <n>H AGO` or `QUIET UNTIL 08:00`. The next check is never in the past.
- Paid: B69 (#1012).

8.6 **Search** with ⌘K for a word from yesterday's meeting.
- See: the meeting, the decision, the action (marked done) and the artifact.
- Known: a search for "PR #<n>" finds nothing (B79).

---

## 9. Doctor

9.1 **Run** `holdspeak doctor` with the hub running.
- See: the same list the Setup page runs (mic, hotkey, Coding agents, connectors), then the hub checks.
- See: `Coding agents` PASS after Install hooks.
- Known on a LAN-only desk: WARN `Where AI runs: This device · not set up yet` and WARN `Dictation AI model … not on this device yet`, although the LAN engine runs summaries (B81).
- Do: `holdspeak doctor --strict` makes a WARN fail. `--connectors` adds the connector checks.
- Paid: B08 (#986), one list (#966).

---

## 10. What is still open on day one

From rehearsal 2 (not paid):

- **B76** A meeting dropped on a Project drawer does nothing. Use "Add to Project ▸".
- **B77** An action the transcript says can read `NO SOURCE · ⚠ UNSUPPORTED`.
- **B78** "Carol" stays your name in the Room, the agent's brief and the update. Needs and the Brief treat it as yours.
- **B79** ⌘K does not find a PR by "PR #<n>".
- **B80** The 06:00 Brief's receipt says 0 items. The Brief itself is right.
- **B81** Doctor WARNs about this-device AI on a LAN-only desk; the event-log count is very high.
- **B82** The confirm line's chip for Codex reads `API.OPENAI.COM` even when Codex uses another provider.
- **B83** A `cd` through `/private/var` was held as outside the worktree. Probably the rig only; not verified on `/Users/karol`.
- **B84** Import is two presses.
- **B85** Hold labels can read snake_case (`NOT READ · shell_expansion`) or the wrong kind (`GITHUB ACTION FOR YOU` for `gh --version`).
- **B86** The clone folder repeats the repository name.
- **B87** The sent file keeps sections that read only "Not checked.".
- **B88** A Brief header count can differ from its body.
- **B89** The deterministic draft can say "All sources consulted successfully" while a source is stale.

From the lanes (not paid):

- **B32** Settings has no macOS calendar path (ICS only). Allow calendar access is on the first-run card only.
- **B49** Codex on the LAN model gets none of HoldSpeak's tools. On an OpenAI model: not verified.
- **No Send destination from a sign-in** (#974 #1001): a GitHub sign-in adds no GitHub Send destination. Only the folder is ready.
- **Folder chip** (#1002): the folder Send chip reads `THIS DEVICE`, not `FOLDER · <name>`.
- **Anthropic key** (#975): reads `NOT SUPPORTED YET`. Use OpenRouter or an OpenAI-compatible server.
- **Renamed branch** (#1010): if the agent renames its branch, the PR is not found.
- **Jira and Confluence** (#1001): read `NEVER CHECKED` until a check runs.
- **Credentials** (#1000): the agent's worktree uses your own credentials. It is not a sandbox.
- **Parked guard notes** (#986): no desk verb restores them.

From the runbook itself:

- **B90** (new, lane 22): the second-morning Brief starts at 17:00 the day before (Friday 17:00 on a Monday), so day-one work done before 17:00 is not in it.

Not rehearsed yet (the steps exist; no rehearsal pressed them):

- A Hand to Claude Code; email (Resend); live recording and First words; the real calendar; the Parked drawer; People beyond one added Person; the lane at 393.
