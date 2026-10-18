# herdr: a study, and what HoldSpeak should take from it

Status: study for the owner, 2026-10-17. No code changed. Inputs: the herdr
repository and docs (read with `gh api` and WebFetch on 2026-10-17), four
write-ups, and HoldSpeak's own agent side (cited as `file:line`).

## 0. Facts first: which herdr, which license

- **The repository in the brief is a fork.** `github.com/maxjendrall/herdr`
  is a fork of `herdrdev/herdr` (`"fork": true, "parent": "herdrdev/herdr"`).
  The fork has 0 stars, was last pushed 2026-04-01, and carries the old
  **AGPL-3.0** license. Do not use it.
- **The real project is `herdrdev/herdr`** (home page https://herdr.dev).
  - Version: **v0.9.5**, released 2026-10-14 (v0.9.4 the day before).
  - Stars: **44,517**; forks: 3,538 (GitHub API, 2026-10-17).
  - Language: Rust, one binary, a Ratatui TUI, Ghostty's VT parser
    (`crates/ghostty-vt`).
  - License: **Apache-2.0**. The changelog for 0.8.0 (2026-08-03) says:
    "Relicensed Herdr from AGPL-3.0-or-later to Apache-2.0."
- **What the license means for us.** Apache-2.0 is permissive. We may copy
  code or data if we keep the copyright notice and the license text, and say
  what we changed (a `NOTICE` entry). In practice we port **ideas** and, at
  most, **data** (the detection manifests, see 1.3). Their code is Rust and
  ours is Python and TypeScript, so a fresh write is the natural path anyway.
  Older copies (the fork, any pre-0.8.0 snapshot) are AGPL: never copy from
  those.

## 1. What herdr is and does

One line from its README: "the runtime your coding agents live on." herdr is
a terminal multiplexer (like tmux) that knows which panes hold coding agents
and what each agent is doing. It does not wrap the agents. It owns their
terminals.

### 1.1 Concepts

| Concept | What it is |
|---|---|
| **Workspace** | The top container: one per repo, task or investigation. Its sidebar state rolls up from the agents inside it. |
| **Tab** | A layout inside a workspace (`agents`, `logs`, `server`, `review`). |
| **Pane** | A real terminal (a PTY). Split right or down; read, send input, close. |
| **Agent** | A recognized agent process inside a pane. It has a kind (`claude`, `codex`, ...), an optional name (`reviewer`), and a state. |
| **Session** | A persistent server namespace with its own socket (`herdr session attach work`). |
| **Server and client** | The server owns panes and processes. Clients (the TUI, `herdr agent attach`, the CLI, scripts) attach and detach. Several clients can view one server. |
| **Machine** | A saved SSH host. Local and remote machines show in one window, with one combined agent list. |
| **Worktree** | A workspace with git checkout provenance: `herdr worktree create --branch X` makes the checkout, opens it as a workspace and groups it under the repo's workspace. |
| **Plugin** | A directory with `herdr-plugin.toml`: actions, event hooks, panes, keybindings, link handlers. "The entire Herdr CLI is the plugin API." |

Public IDs are short and stable: workspace `w1`, tab `w1:t1`, pane `w1:p1`.
Closed IDs are never reused. Every create command answers JSON with the new
IDs, so a script reads IDs and never guesses them.

### 1.2 Agent states

| State | Meaning |
|---|---|
| `working` | The agent is running a turn. |
| `blocked` | The agent shows an approval, a question or a permission UI. |
| `done` | The agent finished and **nobody has looked at it yet**. |
| `idle` | Finished or waiting, and seen. |
| `unknown` | An agent is there, but herdr cannot classify it. Not proof of success. |

Two details matter:

- **Done versus idle is a "seen" bit.** A finished turn stays `done` until a
  person focuses that pane. Each client tracks what it has seen. This is the
  "unread mail" model for agents.
- **`completion_seq`** marks an idle transition that followed real work, so
  startup, a restored session or a session switch is never counted as "the
  agent finished something".

**Rollups.** A blocked agent makes its pane, tab and workspace look blocked; a
working agent makes the workspace look active; a done agent stays visible until
viewed. The docs call this "the main Herdr workflow": start several agents,
then let the sidebar tell you which project needs a decision.

### 1.3 How it knows the state

Three sources, in order of authority:

1. **The agent reports its own state** (`pane report-agent --state working
   --seq N`). Some agents do this natively (Crush, Kiro, Command Code, Prime
   Agent, Muse Code); herdr's integrations for OpenCode, Pi, Kimi, Kilo, OMP
   and MastraCode report too. A report wins over the screen. `--seq` must
   rise, so a late report never overwrites a newer one.
2. **Screen manifests.** herdr finds the agent's process in the pane (the
   foreground process group), then reads **the live bottom of the screen and
   the OSC terminal title** (not the scrolled view). A per-agent TOML
   manifest of rules maps that text to a state. Example from
   `distribution/agent-detection/claude.toml` (v2026.10.11.1): a Braille or
   half-circle spinner in the OSC title means `working` (priority 1100);
   `esc to interrupt` in the last 12 lines means `working`; "showing detailed
   transcript" means `unknown` and skip the update. Rules have ids,
   priorities, regions (`bottom_non_empty_lines(12)`,
   `last_non_empty_above_prompt_box`, `osc_title`), `contains`, `regex`,
   `line_regex` and `not` guards.
3. **Fallback.** A known agent with no matching rule is `idle`, labelled
   `default_known_agent_idle_fallback`.

**Blocked is strict on purpose.** herdr marks `blocked` only when the screen
matches a known approval or question UI. The docs warn: "idle status is not
authorization to approve an action."

**Manifests update without a release.** herdr fetches newer per-agent rules
from herdr.dev and hot-reloads them; a local override in
`~/.config/herdr/agent-detection/<agent>.toml` always wins. When Claude Code
changes its spinner, herdr fixes detection in hours, not in a binary release.

**`herdr agent explain <target>`** shows why a pane has its state: the
manifest and version, the rule that matched, the evidence, or the fallback
reason. It also runs offline on a saved screen (`--file screen.txt`).

**Coverage.** 23 agents are detected (Claude Code, Codex, Copilot CLI,
Cursor, OpenCode, Pi, Gemini CLI, Amp, Droid, Devin, Kimi, Kilo, Qwen,
Grok, ...), plus any agent that reports itself.

### 1.4 The CLI and the socket API

The CLI is a thin wrapper over a **newline-delimited JSON socket**
(`~/.config/herdr/herdr.sock`; a named pipe on Windows). Request:
`{"id":"req_1","method":"ping","params":{}}`. `herdr api schema --json`
prints the full JSON Schema of every request, response and event.

| Area | Methods (selection) |
|---|---|
| Workspace, tab | `create`, `list`, `get`, `focus`, `rename`, `move`, `close`, `report_metadata` |
| Worktree | `list`, `create`, `open`, `remove` |
| Pane | `split`, `swap`, `move`, `zoom`, `layout`, `read`, `send_text`, `send_keys`, `wait_for_output`, `report_agent`, `report_agent_session`, `release_agent`, `close` |
| Agent | `list`, `get`, `read`, `explain`, `send_keys`, `prompt`, `wait`, `rename`, `focus`, `start` |
| Layout | `export`, `apply`, `set_split_ratio` |
| Events | `events.subscribe` (workspace, tab, pane, layout, worktree events; `pane.agent_status_changed` filtered by pane and state), `events.wait` |
| Other | `notification.show`, `session.snapshot`, `integration.install`, `plugin.*`, `server.stop`, `server.reload_config` |

Design points worth copying:

- **Agent verbs are separate from pane verbs.** `pane run` types into a
  terminal whatever runs there. `agent prompt` resolves the live agent first
  and refuses if that agent no longer owns the pane.
- **`agent prompt --wait` is one request.** It submits the prompt and starts
  the wait in one call, so no race exists between "send" and "wait".
- **It refuses to type into a blocked agent** (`agent_blocked`). A deliberate
  answer goes through `agent send-keys`.
- **`agent_prompt_stalled`**: after a prompt, herdr waits up to 5 s to see
  `working` or `blocked`; if nothing moves, it says so instead of waiting
  forever.
- **`agent.wait` pins the pane occupant**, so a replacement agent cannot
  satisfy the wait.
- **Long reads of full-screen agents.** For Claude Code and OpenCode, a read
  of more lines than the screen scrolls the agent's own transcript with mouse
  events, collects pages, and scrolls back. If even that fails, the docs say:
  ask the agent to write its answer as Markdown to a temp file and read the
  file.
- **Event streams fail loudly.** A slow subscriber gets `events_lost` and must
  re-read a snapshot; it never continues with a silent gap.

### 1.5 Agent-to-agent orchestration

Every process in a pane gets `HERDR_ENV=1`, `HERDR_PANE_ID`, `HERDR_BIN_PATH`
and `HERDR_SOCKET_PATH`. So an agent can drive herdr itself. The canonical
recipe (docs, "Agent automation"):

```bash
split=$(herdr pane split --current --direction right --no-focus)
review_pane=$(printf '%s\n' "$split" | jq -r '.result.pane.pane_id')
herdr agent start reviewer --kind codex --pane "$review_pane" -- -m gpt-5.4
herdr agent prompt reviewer "Review the current diff" --wait --timeout 120000
herdr agent read reviewer --source recent-unwrapped --lines 120
```

A builder agent spawns a reviewer, gives it work, waits until it settles,
and reads the result. `agent start` returns only when the new agent is
detected and ready. Write-ups call this part "more experimental" than the
state tracking (Better Stack); Flavio Copes runs "separate builder and
reviewer agents, with the human making the final decision", and a small
`spawn` script that makes a worktree and starts an agent per task.

### 1.6 Skills

- herdr ships **one skill**, `skills/herdr/SKILL.md` (214 lines). It teaches
  an agent to drive herdr from inside a pane: discover IDs, split with
  `--no-focus`, run and read, start helpers, wait.
- **`herdr --skill`** prints the copy bundled with the running binary, so the
  skill always matches the installed version. `npx skills add herdrdev/herdr
  --skill herdr -g` installs it for supported agents.
- **One guardrail**: if `HERDR_ENV` is not `1`, the agent stops and says so.
  An agent outside herdr never drives a session it does not own.
- **The trigger is narrow on purpose**: "Use only when the user explicitly
  mentions Herdr ... Do not use merely because a task could benefit from a
  background terminal."
- A second document, `herdr.dev/agent-guide.md`, is for an agent that
  **teaches a human** to set up herdr. Two audiences, two files.

### 1.7 Persistence

| Case | Processes live on | Layout returns | Screen returns | Conversation resumes |
|---|---|---|---|---|
| Detach and reattach | yes | yes | yes | yes |
| Server or machine restart | no | yes | only with opt-in pane history | yes, through native agent resume |
| `herdr update --handoff` | yes (best effort) | yes | yes | yes |

- **Native agent resume.** Each integration reports the agent's session id;
  after a restart herdr reopens the pane in the same folder and runs the
  agent's own resume command: `claude --resume <id>`, `codex resume <id>`,
  `pi --session <id>`, `opencode --session <id>` (18 agents). An agent can
  also report its own resume argv (`report-agent ... -- my-agent --resume
  $ID`), with limits: the first word is a bare command on PATH, at most 64
  arguments and 8 KiB.
- **Snapshots.** Up to 48 layout snapshots, at most one each 15 minutes, plus
  recovery copies of an unreadable `session.json`. Nothing restores itself;
  recovery is a documented copy.
- **Pane history is off by default** because terminal output holds secrets.

### 1.8 Notifications

- A toast when a **background** agent finishes or needs input. Delivery:
  in-app, the outer terminal (works over SSH), the OS, or off.
- **No toast for the tab you are looking at.**
- Sounds: one for "done", one for "needs input"; per-agent on/off.
- On Windows, a click on the OS notification selects the pane that raised it.
- `herdr notification show <title> --sound request` lets a script raise one.

### 1.9 UX details worth stealing

- **The sidebar is the product.** Spaces (workspaces) and an Agents list,
  each row with its state, sorted so the stuck one is visible. Copes: "Agent
  state is the killer feature ... I do not need to open six tabs every few
  minutes to see whether an agent stopped."
- **Done stays until seen** (1.2). Nothing is lost because you looked away.
- **Mouse and keyboard are both first class.** Right-click to split, drag
  borders, or `ctrl+b` prefixes.
- **Names for agents** (`reviewer`, `builder`) instead of pane numbers.
- **Custom status text**: an integration can set a `summary` token
  ("indexing") that shows in the agent row, separate from the state.
- **Phone over SSH**: the TUI adapts to narrow screens; no app needed.
- **One window, several machines**, with one agent list.
- **No telemetry, no account, no dashboard** (Copes).

Limits the write-ups name: detection is not perfect and `unknown` is not
success; a server restart ends processes (layout and conversations come back,
running jobs do not); no file isolation or shared memory between agents;
cross-machine CLI coordination is "planned, not built".

## 2. HoldSpeak today, feature by feature

HoldSpeak's agent side is **the Conductor** (`docs/internal/CONDUCTOR.md`): a
desk item is handed to Claude Code, Codex or pi, which runs in its own git
worktree in a detached tmux session, with a grounded brief, a tool gate by
Control mode, and follow-through to the merged PR. It is a different shape
from herdr: herdr is a terminal runtime with agent awareness; the Conductor is
a work pipeline with terminals underneath.

| Feature | HoldSpeak | Where |
|---|---|---|
| Agents run in persistent terminals | **Has it** (tmux, detached) | `holdspeak/coder_factory.py:125-133` (`tmux new-session -d`) |
| Live terminal view on the face | **Partly**: a read-only xterm.js viewer of polled `capture-pane` snapshots, behind Raw | `web/src/desk/surface/XtermPane.tsx:106` (`disableStdin`), `holdspeak/coder_steering.py:136` (`peek_pane`) |
| Type into an agent | **Partly**: only the armed steer composer and named keys, by law | `holdspeak/coder_steering.py:707` (`deliver`), `:861` (`deliver_keys`) |
| Workspaces, tabs, splits, layouts | **Missing** (one tmux session per launch; no layout model) | `holdspeak/coder_factory.py:49` |
| Agent state: working / waiting / ended | **Has it, by hooks only** | `holdspeak/agent_context/sessions.py:45-57`, `:115` |
| Blocked: approve versus answer | **Has it** (Notification subtype, PermissionRequest, Stop) | `holdspeak/agent_context/models.py:258` (`is_blocked`), `:364` (`wait_kind`) |
| Turn end: asks / idle / done | **Has it** (text reading of the last message) | `holdspeak/agent_context/models.py:352` (`turn_end`) |
| "Done, not yet seen" | **Missing** (no seen bit; DONE is a turn-end word, not unread) | `web/src/desk/agentFlights.ts:17` |
| `unknown` state, honestly shown | **Missing** (a stale session decays to idle after 30 min, ended after 4 h) | `holdspeak/agent_context/models.py:50-52`, `sessions.py:171` |
| Screen-based detection | **Missing as a state source**; one screen reading exists for Codex start-up only | `holdspeak/delivery/first_message.py:63`, `:74` |
| Agents covered | **Partly**: Claude Code, Codex, pi (hooks); every other agent is invisible | `docs/internal/CONDUCTOR.md:83` |
| Agents he starts by hand | **Partly**: seen when he installed the rider hooks (K1); not launched, so no lane | `holdspeak/agent_context/hooks.py:347` |
| Explain a state | **Missing** (`coder.audit` lists steering, not detection) | `holdspeak/mcp/families/coder.py:38` |
| State reaches the owner | **Has it**: Needs you coder rows, a WS `coder` frame on each transition, a desktop notification on the blocked edge | `web/src/desk/needsYou.ts:376`, `holdspeak/web_server.py:1935-1955`, `holdspeak/services/heartbeat_service.py:887` |
| Notification on done | **Partly**: DONE/IDLE are shown on the lane and lamp, with no notification by design ("Needs you is what needs him") | `docs/internal/CONDUCTOR.md:56` |
| Sound, "not for the window I am looking at" | **Missing** | `holdspeak/desktop_notify.py:271` |
| Fleet view | **Partly**: the Conductor drawer lists flights (`starting … merged`); one lane window per launch | `web/src/desk/applications.ts:138-150`, `web/src/desk/lane/LaneWindow.tsx:1-15` |
| Start an agent with a brief | **Has it, richer than herdr** (brief from meetings, decisions, memory; worktree; Control mode) | `holdspeak/mcp/families/agent.py:16`, `docs/internal/CONDUCTOR.md:5-12` |
| Tool gate by Control mode | **Has it; herdr has nothing like it** | `docs/internal/CONDUCTOR.md:55` |
| Auto-answer routine questions | **Has it** ("The desk: ..." under YOLO) | `holdspeak/services/agent_responder.py:112` |
| Follow through to the merged PR | **Has it; herdr has nothing like it** | `docs/internal/CONDUCTOR.md:115` |
| Desk tools inside the agent (MCP) | **Has it** (CONDUCTOR palette, launch credential) | `docs/internal/CONDUCTOR.md:39-40` |
| Coder sessions over MCP | **Partly**: `coder.list`, `coder.get`, `coder.audit` read only | `holdspeak/mcp/families/coder.py:13-50` |
| An agent starts another agent | **Missing**: `agent.hand` is EGRESS and not in the CONDUCTOR palette | `holdspeak/mcp/tool_authority.py:289` |
| Prompt an agent and wait for it | **Missing** (no `agent.prompt`, no `agent.wait`, no `agent.read` tool) | `holdspeak/mcp/families/coder.py:53-56` |
| `sequence.*` / `workflow.*` | **Not agents**: these are model chains on the inference path | `holdspeak/mcp/families/sequence.py:11-70` |
| Automations start coding agents | **Missing**: an automation run is one model call with no tools | `docs/internal/betterment/mcp/DESIGN.md` §2 |
| Limits | **Has it**: 3 live launches; 2 h quiet or 8 h running raises a Door item | `holdspeak/services/agent_hand_service.py:59`, `CONDUCTOR.md:57` |
| Hub restart | **Has it**: tmux keeps running; credentials, grants and ownership reload | `docs/internal/CONDUCTOR.md:94-103` |
| Machine reboot: resume the conversation | **Missing**: nothing runs `claude --resume` / `codex resume` | `grep --resume holdspeak/` finds no launch use |
| A brief that waits for a restart | **Has it** (pending first message survives) | `holdspeak/delivery/factory_launch.py:757`, `:1531` |
| Stop that really stops | **Has it, stronger than herdr** (process-group kill with generation checks) | `holdspeak/coder_factory.py:298`, `CONDUCTOR.md:88` |
| Skill file for agents | **Missing** (agents learn HoldSpeak only from MCP tool descriptions and the brief) | none |
| Several machines | **Missing** for agents (pi uses the LAN model, but runs here) | `holdspeak/delivery/pi_launch.py:96` |
| Plugins | **Different**: HoldSpeak has its own plugin host and recipes; no terminal plugin surface | n/a |

**Summary.** HoldSpeak is far ahead on the *work* around an agent: the brief,
the gate, the auto-answers, the PR follow-through, the desk's tools. herdr is
far ahead on the *runtime*: broad and honest state detection for any agent,
the seen bit, agent-to-agent primitives, resume after a reboot, and a sidebar
that makes ten agents easy to watch.

## 3. What to bring into HoldSpeak, ranked by value to the owner

Size: **S** = one fast-cycle PR; **M** = two to four PRs; **L** = a phase.
Every idea is **native** unless it says otherwise (section 4 says why).

### 1. Every agent on his Mac shows its state on the desk (screen detection beside hooks)

- **The idea.** Read the bottom of each tmux pane (we already `capture-pane`,
  `coder_steering.py:136`) and the pane title, and map it to
  `working / blocked / done / idle / unknown` with per-agent rule files in the
  herdr manifest shape. Hooks stay the first source; the screen fills in when
  no hook speaks, and covers agents with no hooks at all (Gemini CLI,
  OpenCode, Copilot, Cursor). Also detect agents in tmux sessions that
  HoldSpeak did not launch: his own `claude` in a terminal tab under tmux.
- **Why it matters for him.** Today an agent is visible only if it was
  launched by HoldSpeak or carries our hooks. A Senior Architect runs Claude
  Code and Codex by hand all day. "Claude Code is blocked, waiting for you"
  on the Dock and in Needs you, for *every* agent, is the single most useful
  thing herdr does, and the write-ups agree.
- **Where it lands.** `agent_context` (a second state source), the coder
  watcher (`web_server.py:1935`), Needs you R5 rows, the Dock badge, the
  Conductor drawer.
- **Size.** M. Slice 1: the rule engine plus Claude and Codex rules, state
  only. Slice 2: discover non-launched tmux panes. Slice 3: more agents.
- **Integrate or native.** Native. The manifests are Apache-2.0 data: we may
  vendor `distribution/agent-detection/*.toml` with a NOTICE line and keep a
  local override folder, or write our own rules in the same shape. Either
  way the engine is ours (~300 lines of Python).

### 2. Agents that wait on and hand off to each other

- **The idea.** Three MCP tools in the CONDUCTOR palette:
  `agent.prompt` (with an optional `wait`, one request, as herdr does),
  `agent.wait` (until `idle|done|blocked`, pinned to the session), and
  `agent.read` (the last N lines, or the last assistant message from the
  hook). Plus `agent.start_helper`: a launched agent may start **one helper
  in its own worktree** (a reviewer, a test runner), counted against the
  3-launch cap, under the same Control mode. Refuse to type into a blocked
  agent (`agent_blocked`), and report a stalled prompt after 5 s.
- **Why it matters for him.** This is how he already works: Muad'Dib builds,
  Astra reviews. Today that loop lives in our scripts. With these tools, a
  Claude Code builder hands its diff to a Codex reviewer, waits, reads the
  findings and fixes them, and he sees one item go from WORK to PR with a
  review attached. It turns three launches into one supervised pair.
- **Where it lands.** MCP (`mcp/families/agent.py`), `coder_steering.deliver`
  (the typing path exists), `tool_authority.py` (a helper inside the caller's
  own launch is WORK, not EGRESS, because no new item leaves the desk), the
  lane (a helper shows as a sub-lane).
- **Size.** M.
- **Integrate or native.** Native. We already own the session registry, the
  pane typing and the gate; herdr's value here is the *contract* (one-request
  prompt-and-wait, occupant pinning, `agent_blocked`, stalled detection),
  which we copy as rules.

### 3. Resume after a restart or a reboot

- **The idea.** The hooks already carry `session_id`. Store the agent's
  resume command with each launch (`claude --resume <id>`, `codex resume
  <id>`, `pi --session <path>`). When the hub starts and a live launch has no
  tmux session (the Mac rebooted), recreate the session in the same worktree
  through the same credential bootstrap, run the resume command, and mark the
  lane RESUMED. Fall back to a plain shell in the worktree when the id is
  stale, as herdr does.
- **Why it matters for him.** A reboot today strands every running agent:
  the worktree and the branch survive, the conversation does not, and he
  must hand the item again. With resume, a Monday-morning OS update costs
  nothing.
- **Where it lands.** Conductor (`factory_launch.py`, `coder_factory.spawn`),
  the R2 restart path (`CONDUCTOR.md:94`).
- **Size.** S to M.
- **Integrate or native.** Native. The credential bootstrap must stay ours.

### 4. The fleet view: one rail, every agent, the stuck one on top

- **The idea.** The Conductor drawer becomes herdr's sidebar on our desk:
  every agent (launched, helpers, hand-started), grouped by Project (herdr's
  workspace rollup), sorted **blocked, done-unseen, working, idle**, each row
  with its name, its one-line status (`summary`), its age and one verb
  (Answer, Approve, Open). The Dock glyph carries the worst state of the
  fleet. Add herdr's **seen bit**: a finished turn is DONE until he opens
  that lane, then idle. Notifications follow herdr's rule: done and blocked
  both notify, never for the lane he is looking at, with a distinct sound
  for each.
- **Why it matters for him.** He manages three people and will run several
  agents per person's work. One glance should answer "who needs me, who
  finished, who is still going". The seen bit stops a finished agent from
  vanishing into "idle".
- **Where it lands.** The desk: the Conductor window, the Dock, Needs you,
  `desktop_notify.py`. A face: drawn on the canvas first (UX-CANON).
- **Size.** M.
- **Integrate or native.** Native (our desk, our material).
- **Note.** "Done notifies" changes the A5 law ("Needs you is what needs
  him", `CONDUCTOR.md:56`). Decision 2 below.

### 5. Automations that start coding agents

- **The idea.** An Automation's Do line may be "Hand to an agent": on a
  schedule or an event, the automation picks items and hands each to Claude
  Code, Codex or pi through `agent.hand`, under the same cap and Control
  mode, and its result lists the launches with their lanes. Starters:
  "Every morning, take new Jira bugs labelled `agent-ok` and open draft PRs";
  "On a new PR in my repos, start a Codex reviewer and post its findings to
  the lane"; "Friday 16:00, ask an agent to update the runbook from this
  week's decisions".
- **Why it matters for him.** The Conductor waits for his press. Automations
  make it work while he is in meetings. This is the agentic-OS step: the
  desk starts the work, he only judges it.
- **Where it lands.** Automations (`betterment/workbench/DESIGN.md`), Engines
  (an "agent on this Mac" engine, `betterment/engines/DESIGN.md` §4), MCP
  (`automation.create` with `do: hand_to_agent`).
- **Size.** M, after the Automations and Engines slices land.
- **Integrate or native.** Native. Starting a launch is AUTHORITY at
  creation (he turns the schedule on once), then each run is the automation's
  own press, per the MCP design's rule.

### 6. A HoldSpeak skill, and skills as a shared format

- **The idea.** Ship `SKILL.md` for HoldSpeak, printed by `holdspeak --skill`
  so it always matches the installed version (herdr's best small idea). It
  teaches any agent: check `HOLDSPEAK_HUB_URL`/the launch credential first
  and stop if absent (herdr's guardrail); read the brief's refs with
  `project.get` and `memory.search`; report progress; hand to a helper; never
  write `Closes #N`. Install it into launched agents automatically, and into
  his own Claude Code and Codex with one press on the Agents card. Then go
  one step further: let the Practice recipes and Automations export as
  skills, so a recipe he made on the desk becomes a skill his hand-run Claude
  Code can use.
- **Why it matters for him.** Today an agent learns HoldSpeak only from 257
  tool descriptions. A skill makes every agent competent on his desk in its
  first turn, inside and outside the Conductor, and skills are the format
  Claude Code, Codex and pi already share.
- **Where it lands.** MCP, the Agents card, the launch spawn, Practice
  recipes.
- **Size.** S for the skill; M for recipe-to-skill export.
- **Integrate or native.** Native.

### 7. `explain` for agent state

- **The idea.** `coder.explain <session>`: which source decided the state
  (hook or screen rule), the rule id, the evidence lines, the age, and why a
  stale session decayed. Shown in the lane behind Raw.
- **Why it matters for him.** When a row says IDLE and the agent is clearly
  waiting, he (or we) can see why in one press instead of reading logs.
- **Where it lands.** MCP `coder.*`, the lane's Raw.
- **Size.** S (after idea 1).
- **Integrate or native.** Native.

### 8. A report-state protocol for any agent

- **The idea.** Copy herdr's "add support to your agent": every launched pane
  gets `HOLDSPEAK_PANE`, and `holdspeak agent report --state working --seq N
  [--summary TEXT] [-- resume argv]`. Agents that support herdr's protocol
  could be bridged too: if we export `HERDR_ENV`-shaped variables we must not
  pretend to be herdr, so we offer our own command with the same fields.
- **Why it matters for him.** New agents appear every month. A protocol lets
  a new agent join his desk without a HoldSpeak release.
- **Where it lands.** `agent_context` (a third state source), the CLI.
- **Size.** S.
- **Integrate or native.** Native.

### 9. Read herdr's agents when he runs herdr (optional bridge)

- **The idea.** If `~/.config/herdr/herdr.sock` exists, a read-only adapter
  calls `agent.list` and subscribes to `pane.agent_status_changed`, and the
  desk shows those agents as rows ("Codex in herdr w2:p1 is blocked"), with
  Open as "focus that pane" (`agent.focus`).
- **Why it matters for him.** Only if he adopts herdr as his terminal. Then
  his herdr fleet joins Needs you for free, with herdr's 23-agent coverage.
- **Where it lands.** A connector beside `agent_context`.
- **Size.** S.
- **Integrate or native.** **Integrate** (read-only, via the socket API). A
  missing socket means the connector is absent, not "zero agents".

### 10. Several machines

- **The idea.** Run launches on the LAN box or another Mac over SSH, with one
  fleet view. herdr does it with a remote server per machine.
- **Why it matters for him.** Low today: his agents run on this Mac, and pi
  already uses the LAN model remotely.
- **Size.** L. **Park it.**

### Not recommended

- **Workspaces, tabs and split layouts on the desk.** That is herdr's TUI,
  not our job. Our unit is the work item and its lane. Tenet 3 ("never a
  million interfaces").
- **Pane history persistence.** herdr keeps it off for secrets; we have no
  need.
- **A plugin marketplace for terminal plugins.** Our recipes and automations
  are the extension surface.

## 4. Recommendation: build native, borrow the contract and the rules

**Build it natively in HoldSpeak. Port herdr's ideas, and its detection
rules as data. Offer a read-only herdr bridge later, only if he uses herdr.**

Why:

1. **The Conductor's value sits on top of the terminal, and it depends on
   owning the spawn.** The launch credential travels through a one-shot 0600
   file read by a bootstrap before any shell runs (`CONDUCTOR.md:101`); the
   gate checks each call against the launch's worktree and tmux session
   (`CONDUCTOR.md:55`); Stop kills recorded process groups
   (`coder_factory.py:298`). If herdr owned the PTYs, each of these would
   need a herdr equivalent or a second supervisor. That is two moving parts
   where one works (Tenet 1, Tenet 3).
2. **His face is the web desk, not a TUI.** herdr's sidebar is a terminal
   UI. We would still need to rebuild it on the desk, so integrating herdr
   saves us only detection, and detection is the part we can port as data.
3. **The hard-won part of herdr is portable.** The state model (five states,
   the seen bit, `completion_seq`), the strict-blocked rule, the
   prompt-and-wait contract, the resume table and the manifests are ideas and
   Apache-2.0 data. Writing the engine is days, not weeks.
4. **No new install for a first-time user.** "Batteries included"
   (2026-10-05) means the fleet works with tmux, which the Conductor already
   requires. herdr would be one more binary to install and keep in step.
5. **The bridge keeps the door open.** If he likes herdr as his terminal,
   idea 9 reads its socket in one small PR, and his herdr agents join Needs
   you. We take its strengths without depending on it.

### Decisions for the owner

1. **Screen detection of agents HoldSpeak did not launch** (idea 1, slice 2):
   the hub reads the bottom lines of his own tmux panes, locally, to find
   agents. Recommended: yes, on by default, with the same secret filter the
   hook path uses (`sessions.py:158`). Nothing leaves the Mac.
2. **Done notifies** (idea 4): a finished agent raises a quiet notification
   (no sound by default) unless he is looking at its lane, and stays DONE
   until he opens it. This amends the A5 law, which keeps done out of
   notifications. Recommended: yes, with done kept out of Needs you.
3. **Helpers inside a launch are WORK** (idea 2): a launched agent may start
   one helper in its own worktree without his press, under the 3-launch cap.
   Recommended: yes under Normal and YOLO; Secure asks.

### Proposed order

1. Idea 3 (resume, S-M) and idea 6 (skill, S): small, independent, felt at
   once.
2. Idea 1 (detection, M), then idea 7 (explain, S).
3. Idea 4 (fleet view, M): a face, canvas first.
4. Idea 2 (agent-to-agent, M).
5. Idea 5 (automations start agents, M), after the Automations and Engines
   recipes.
6. Ideas 8 and 9 when a real need appears.

## Sources

- herdr repository: https://github.com/herdrdev/herdr (README, CHANGELOG,
  LICENSE, `skills/herdr/SKILL.md`, `distribution/agent-detection/claude.toml`,
  `docs/next/website/src/content/docs/*.mdx`: concepts, agents,
  agent-automation, agent-skill, add-herdr-support, integrations,
  session-state, socket-api, configuration, plugins, connecting-machines,
  how-to-work, cli-reference, marketplace).
- The fork named in the brief: https://github.com/maxjendrall/herdr (AGPL
  snapshot, 2026-04-01).
- https://herdr.dev/agent-guide.md
- https://flaviocopes.com/herdr/ and https://flaviocopes.com/herdr-skills.md
- https://betterstack.com/community/guides/ai/herdr-ai-agent/
- Not read: https://www.bitdoze.com/md/herdr-agent-multiplexer.md (the four
  sources above covered the same ground; nothing in this study depends on it).
