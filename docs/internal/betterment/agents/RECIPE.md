# Agents: the recipe

The slices that make `DESIGN.md` real. Each slice is one PR in the fast
cycle (`CLAUDE.md`): quick check, merge, the watcher runs the whole suite,
Astra reviews after. Short paths: `desk/` is `web/src/desk/`, `hs/` is
`holdspeak/`. Tests follow the test diet: T1 a hub test, T2 vitest (one
file per app: `desk/conductor/__tests__/agents.app.test.tsx`), T3 the desk
sweep, T4 a real browser only for keys, drag or touch.

**The rig for every slice.** `rig/fake_claude.py` is a fake Claude Code
that speaks the real hook protocol, asks, waits for an answer and for a
key, and says Done. Put it first on `PATH` as `claude` in an isolated hub
(`rig/start_hub.py`, ports 8821–8829) to walk a slice live, and to record
real hub answers for T2 doubles (`HOLDSPEAK_WIRE_WRITE`,
`web/src/test/recordedHub.ts`). Never start his real `claude`, `codex` or
`pi` in a test.

Order: truth first, then one press, then reach, then the new powers. Each
merge leaves the desk better and never half-broken.

---

## AG0. Tell the truth about state

- **Goal**: a finished agent says Done (New until opened), and an agent the
  restart killed says "Stopped by restart", never "Working" or "Asks you".
- **Files**: `hs/agent_context/models.py`, `hs/services/agent_flights.py`,
  `hs/web/routes/agent_hand.py`, `desk/agentFlights.ts`,
  `desk/conductor/ConductorWindow.tsx`.
- **Changes**:
  - `turn_end`: a Stop whose last message is not a question is `done`, with
    or without a PR (drop the PR-only rule at `agent_flights.py:92-95`). A
    flight that is not blocked and whose last event is a Stop reads `done`,
    not `working` (`agent_flights.py:89`).
  - A completion counts only when the turn had a UserPromptSubmit and work
    before the Stop (herdr's completion sequence); a SessionStart alone is
    never Done.
  - The seen bit: store `seen_wait_id` on the launch record;
    `POST /api/agent/launches/{id}/seen` sets it; opening the lane calls it.
    A done turn whose `wait_id` differs from `seen_wait_id` is **New**.
  - A live launch whose tmux session no longer exists (check with
    `tmux has-session` on hub start and on each heartbeat) is
    `stopped_by_restart`; its question is dropped from Needs you and the
    Conductor.
  - The lane's ARM refusal on a paneless session (409) shows "This agent's
    terminal is gone" in place of "ARM FIRST".
- **Done when**: with the fake agent, after its "Done" line the Conductor
  row reads **Done · New** within 3 s at 1440 and 393; opening it makes it
  Quiet; after `tmux kill-server` and a hub restart, both rows read
  "Stopped by restart" within one heartbeat, and Needs you drops them.
- **Tests**: T1 `tests/unit/test_agent_flights.py` (Stop without a question
  is done; seen makes it quiet; a missing tmux session is
  stopped_by_restart; a SessionStart alone is not done). T2 the agents app
  file with recorded answers for Done, New and Stopped.
- **Not in this slice**: the new words, Resume, Today, notifications.

## AG1. One name: Agents; park the other faces

- **Goal**: everything he sees about coding sessions says "agent", and the
  machine-word faces leave the way.
- **Files**: `desk/applications.ts`, `desk/conductor/ConductorWindow.tsx`,
  `desk/lane/LaneWindow.tsx`, `desk/components/HandSheet.tsx`,
  `desk/verbRegistry.ts`, `desk/components/window/launcherRegistry.ts`.
- **Changes**:
  - Title, Dock, Go, palette: **Agents** (keep the id `open-conductor` and
    ⌃3). Every face string from the words table in `DESIGN.md` §4: coder →
    agent, Hand to coder → Hand to agent, Install hooks → Connect Claude
    Code, Re-brief → Tell it, Raw → Terminal, ASKS YOU → Asks you, WANTS
    APPROVAL → Wants to run, `stopped_by_owner` → Stopped by you, the
    branch shown as a slug, no internal ids.
  - Remove **New Agent** from the Desk menu. Search labels recipes "Mode",
    not "AGENT".
  - Delivery board, Terminals (panes) and Mission Control move behind RAW.
    Unmap the `/companion` manifest row and route. Nothing is deleted.
  - Remove the unused `InstallHooksVerbs` export (`ConductorWindow.tsx:111`)
    from the face (park it).
- **Done when**: at 1440 and 393, no face string says coder, Conductor,
  rider, NODE, TARGET, INCOMPATIBLE or an internal id; Search "agent"
  shows Agents and Hand to agent, not five thread modes; Delivery board is
  reachable only with RAW.
- **Tests**: T3 the desk sweep (readable words; add the banned words to its
  word list); T2 the agents app file for the strings.
- **Not in this slice**: layout changes, new verbs.

## AG2. One press to answer and to allow

- **Goal**: he answers a question or allows a command from the Agents row
  in one press, and he sees the command first.
- **Files**: `hs/coder_steering.py`, `hs/web/routes/system/coder_steering_routes.py`,
  `desk/agents/AgentRow.tsx` (new), `desk/conductor/ConductorWindow.tsx`,
  `desk/lane/laneStore.ts`.
- **Changes**:
  - A steer with `kind:"answer"` and the current `wait_id` carries its own
    grant for that wait in every Control mode: the owner's press is the
    authority. `deliver` still re-checks the wait and the pane
    (`coder_steering.py:769-776`). The ARM chip leaves the face (it stays
    behind RAW with the keys).
  - `AgentRow`: one component for a row (title, agent, project, age; the
    question in full; choice buttons; the answer box with the mic; the
    draft with its source; Allow / Deny). The Conductor list uses it.
  - Choices: parse "Answer 1 for X, 2 for Y" in the question and the
    numbered menu (`❯ 1. Yes`, `2. No`) in the pane tail from the existing
    peek. One press sends the number.
  - **Wants to run**: the command is the lines above "Do you want to
    proceed?" in the pane tail (until AG7's rules replace this parse), or
    the gate proposal's `args_head`. Allow sends Enter on "Yes" (or the
    gate's approve), Deny sends Escape (or the gate's deny).
- **Done when**: with the fake agent in Normal mode, at 1440 and 393: the
  row shows the full question and `1 · config` / `2 · env`; one press
  reaches the agent (fake log) in under 2 s; the permission row shows
  `rm -rf build/ && make release`; Allow reaches the agent in one press.
- **Tests**: T1 `tests/unit/test_coder_steering_answer.py` (an answer with
  the current wait sends without an arm; a stale wait is refused). T2
  `AgentRow` with recorded peeks (choices parsed, one press posts the
  steer with `wait_id`; Allow posts Enter). T4 none (no real keys in the
  browser).
- **Not in this slice**: screen rules, Needs you and Today rows.

## AG3. The desk's own answers are visible and in the right form

- **Goal**: when the desk answers for him (YOLO), he sees what it said and
  why, and it answers a choice question with a choice.
- **Files**: `hs/services/agent_responder.py`, `hs/services/agent_flights.py`,
  `desk/agents/AgentRow.tsx`.
- **Changes**:
  - When the question offers choices (the AG2 parse, given to the drafter),
    a ROUTINE draft must be exactly one of them; anything else is REAL.
  - Record the draft's source (the decision or memory line it used) on the
    answer entry.
  - The row shows "The desk is drafting an answer" with **Answer it
    myself** during the hold, then "The desk answered: 1, from your
    decision '…'" as **New** until opened.
- **Done when**: in YOLO with the fake agent, the row shows the drafting
  line within 10 s of the ask, then "The desk answered: 1 …" (not
  "Yes, …"); the fake log shows `1`; at 1440 and 393.
- **Tests**: T1 `tests/unit/test_agent_responder.py` (a choice question
  with a non-choice draft is REAL; the source is stored), with a recorded
  LAN draft. T2 the row states.
- **Not in this slice**: changing which questions are ROUTINE.

## AG4. Hand to agent from where the work is

- **Goal**: he hands any work item from the window where he reads it, in
  two presses, and can add a sentence.
- **Files**: `desk/verbRegistry.ts`, `desk/agentHand.ts`,
  `desk/components/HandSheet.tsx`, `desk/needsYou.ts` (or its More menu),
  `desk/components/DeskToolShelf.tsx` (Search results).
- **Changes**:
  - The hand verb takes the front window's object when no desk icon is
    selected (today it needs `selected(ctx)`, `verbRegistry.ts:514-516`).
  - Needs you rows: More ▸ Hand to agent. Search: Hand to agent on an
    action, note, meeting or decision result; Enter on an action result
    opens it.
  - The sheet: an **Add a sentence** field (sent as `instruction`, which the
    API already takes, `HandSheet.tsx:329`, `:379`); *Where* as "Platform ·
    new branch draft-test-scaffolding"; Launch opens the agent's row in
    Agents and closes the sheet.
- **Done when**: with a note open in front at 1440, Object ▸ Hand to agent
  ▸ Launch starts the fake agent (2 presses); from Needs you, More ▸ Hand to
  agent works; the added sentence is in the fake log's first message; at
  393 the same from the note window.
- **Tests**: T2 the agents app file (verb enabled on the front window;
  instruction posted). T3 the sweep for the sheet at 393 (no clipped
  chips).
- **Not in this slice**: Review by (AG12), the queue (AG5).

## AG5. Working at once, and a queue

- **Goal**: he can run up to six agents by default, finished ones never
  block a new one, and at the limit a hand waits instead of failing.
- **Files**: `hs/services/agent_hand_service.py`, `hs/config/core.py`,
  `desk/components/HandSheet.tsx`, `desk/conductor/ConductorWindow.tsx`.
- **Changes**:
  - `MAX_LIVE_LAUNCHES` becomes the setting `agents.working_at_once`
    (default 6), shown in Settings ▸ Agents.
  - Count only launches that are Working or need him; Done, Quiet and
    Stopped do not count.
  - At the limit, Launch reads **Start when one is free**: the hand is
    stored as queued and started when a slot frees (the heartbeat checks).
    The row shows "Waits for a free agent".
- **Done when**: with three fake agents, two Done, a fourth hand starts at
  once; with six working, a seventh shows "Waits for a free agent" and
  starts within one heartbeat after one finishes; at 1440 and 393.
- **Tests**: T1 `tests/unit/test_agent_hand_cap.py` (done does not count;
  a queued hand starts when a slot frees).
- **Not in this slice**: helpers (AG11).

## AG6. Resume after a restart

- **Goal**: after a Mac restart, one press brings every stopped agent back
  to its conversation.
- **Files**: `hs/delivery/factory_launch.py`, `hs/services/agent_hand_service.py`,
  `hs/web/routes/agent_hand.py`, `desk/agents/AgentRow.tsx`.
- **Changes**:
  - On registration, store the agent's session id and its resume command
    on the launch: `claude --resume <id>`, `codex resume <id>`,
    `pi --session <path>` (herdr's table).
  - `POST /api/agent/launches/{id}/resume`: a new tmux session in the same
    worktree through the same credential start-up (`coder_factory.spawn`,
    a fresh launch credential), running the resume command. If the agent
    does not register within the usual window, open a shell in the
    worktree and mark the row "Could not resume · Hand again".
  - Rows: **Resume**; the Agents header: **Resume all** when two or more
    are stopped by restart.
- **Done when**: with the fake agent (taught to accept `--resume`), after
  `tmux kill-server` and a hub restart, Resume all brings both back in one
  press, and each row returns to its last state; at 1440 and 393.
- **Tests**: T1 `tests/integration/test_agent_resume.py` with the fake
  agent on `PATH` (resume argv built per agent; a stale id falls back).
- **Not in this slice**: resuming by itself (never).

## AG7. Screen rules (the herdr port)

- **Goal**: the desk knows an agent's state and its prompt from its screen
  when no hook speaks, and says why.
- **Files**: `hs/agent_context/screen_rules.py` (new, about 300 lines),
  `hs/agent_context/rules/*.toml` (vendored), `NOTICE`,
  `hs/web_server.py` (the watcher), `hs/mcp/families/coder.py`.
- **Changes**:
  - The rule engine in herdr's shape: regions (`bottom_non_empty_lines(n)`,
    `last_non_empty_above_prompt_box`, `osc_title` from `#{pane_title}`),
    `contains`, `regex`, `line_regex`, `not`, priority; a local override
    folder in `~/.config/holdspeak/agent-rules/`.
  - Vendor herdr's rule files for claude, codex, pi, gemini and opencode
    (Apache-2.0, v0.9.5 or newer, never the AGPL fork), with the license
    header and a NOTICE line naming herdr and our changes.
  - The watcher samples the bottom of each live agent's pane every 2 s and
    merges: hook first, then the rule, then "No signal" after 10 min.
    Rules also give the prompt's command and choices (replacing AG2's
    parse).
  - `coder.explain` (MCP) and "Why this state" behind RAW: the source, the
    rule id, the evidence lines, the age.
- **Done when**: with the fake agent's hooks turned off, its row still
  goes Working → Asks you → Done from the screen alone; "Why this state"
  names the rule; at 1440 and 393.
- **Tests**: T1 `tests/unit/test_screen_rules.py` on **recorded real
  screens** (captured once from real Claude Code and Codex sessions on the
  owner's desk with his consent, or herdr's own fixtures if its license
  covers them: unknown, check first). Never typed screens.
- **Not in this slice**: agents he started himself (AG15).

## AG8. The Agents list is the fleet

- **Goal**: one glance at Agents or the Dock tells him who needs him, who
  finished and who works.
- **Files**: `desk/conductor/ConductorWindow.tsx`, `desk/agents/AgentRow.tsx`,
  `desk/components/window/Dock.tsx`, `desk/screen/compose.ts`.
- **Changes**:
  - Sort: Needs you (oldest first), Done and New (newest first), Working,
    Quiet, Stopped (folded). Group lines by project when two or more
    projects have agents, each with its worst state.
  - The header counts only what is there; "On this Mac" shows only when
    something is missing.
  - **Start an agent** unfolds in place (what, project, agent): it files a
    note in the project and hands it.
  - The Dock tile: worst-state lamp, a dot for New, the count that needs
    him. The per-agent desk icons leave the floor; desk objects get an
    "Agent" line.
- **Done when**: with five fake agents in mixed states, the order and
  counts are right at 1440 and 393; Start an agent launches in 3 presses;
  the Dock tile shows the lamp and count.
- **Tests**: T2 the agents app file (sort, groups, counts, no zero
  counters) with recorded answers. T3 the sweep for Agents at both widths.
- **Not in this slice**: Today, Needs you, notifications.

## AG9. Agents in Today and Needs you; Done notifies

- **Goal**: Today tells him "2 agents need you · 1 finished", Needs you has
  one row per piece of work, and a finished agent notifies quietly.
- **Files**: `desk/chair/ChairHome.tsx`, `desk/needsYou.ts`,
  `hs/services/heartbeat_service.py`, `hs/desktop_notify.py`.
- **Changes**:
  - Today: an Agents line when there is something, and a Result card for
    each New done turn, with Open (replaces the parked section at
    `ChairHome.tsx:1466-1469`).
  - Needs you: while an agent works on an action, the agent's row replaces
    the action's row; the row uses `AgentRow` (inline Answer and Allow).
  - Notifications (decision 2): Done raises a quiet notification, never for
    the agent whose window is in front; Done stays out of Needs you.
- **Done when**: with the fake agent: after its Done, Today shows the card
  and the Agents line, the Needs you count does not change, and one quiet
  notification is recorded; at 1440 and 393.
- **Tests**: T1 `tests/unit/test_desk_agents.py` (Needs you projection:
  one row per item; notification rule). T2 Today's file for the card.
- **Not in this slice**: the Result's contents (AG10).

## AG10. The Result of a turn

- **Goal**: a Done agent shows what it did: its last words, what changed,
  what it read and wrote.
- **Files**: `hs/services/agent_flights.py`, `hs/web/routes/agent_hand.py`
  (the lane read), `desk/lane/LaneWindow.tsx`, `desk/agents/AgentRow.tsx`.
- **Changes**:
  - The lane read adds: files changed and the branch (`git diff --stat`
    of the worktree against its base), the PR, and **Looked at / Wrote /
    Prepared** from the hub's own log of the launch credential's MCP calls
    (`../mcp/DESIGN.md`), and the cost when the CLI reports it.
  - The agent's window: Story (default) and Terminal (opens at the bottom
    and follows the tail); the Result block leads the Story when Done.
- **Done when**: the fake agent, taught to edit a file, commit and call one
  MCP read, shows "1 file changed", its branch and "Looked at: Platform
  sync" in its Result; the Terminal opens at the prompt line; at 1440 and
  393.
- **Tests**: T1 the lane read (files changed, Looked at from a recorded
  call log). T2 the Result block.
- **Not in this slice**: review rounds (AG12).

## AG11. Agents that work together (MCP)

- **Goal**: a launched agent can prompt, wait for, read and answer an agent
  it started, and start one helper.
- **Files**: `hs/mcp/families/agent.py`, `hs/mcp/palettes.py`,
  `hs/mcp/tool_authority.py`, `hs/services/agent_hand_service.py`.
- **Changes**:
  - `agent.prompt` (with `wait`: one request), `agent.wait` (pinned to the
    session), `agent.read`, `agent.answer`, `agent.start_helper`, in the
    CONDUCTOR set, under herdr's contract: refuse a blocked agent
    (`agent_blocked`), report `agent_prompt_stalled` after 5 s, answer only
    its own helpers, never an approval prompt.
  - `agent.start_helper` is WORK under Normal and YOLO, asks under Secure
    (decision 3); one helper per launch, inside "working at once", its own
    worktree. A helper shows as an indented row.
- **Done when**: a fake builder agent that calls `agent.start_helper`,
  `agent.prompt --wait` and `agent.read` gets the fake helper's Done text
  back; the helper row shows under its parent; at 1440.
- **Tests**: T1 `tests/unit/test_mcp_agent_family.py` (each tool's rules;
  palette classes).
- **Not in this slice**: Review by (hub-run, AG12).

## AG12. Review by (builder and reviewer)

- **Goal**: he hands an item with "Review by Codex" and gets one result with
  the review rounds, without touching the reviewer.
- **Files**: `hs/services/agent_review.py` (new), `hs/services/agent_hand_service.py`,
  `desk/components/HandSheet.tsx`, `desk/agents/AgentRow.tsx`.
- **Changes**:
  - The sheet and Start an agent get **Review by** (none, Codex, Claude
    Code, pi).
  - The hub loop: on the builder's Done with a new commit, start the
    reviewer as a helper (its own worktree at that commit, read only, the
    review brief); on the reviewer's Done, prompt the builder with the
    MUST findings; at most two rounds; then the pair's Result (rounds,
    findings left). Findings left after two rounds is a Needs you row.
  - The row: "Claude Code builds · Codex reviews · round 1".
- **Done when**: with two fake agents (one taught to answer as a reviewer
  with one MUST, then none), the pair ends Done with "round 2, nothing
  left" in one result; at 1440 and 393.
- **Tests**: T1 `tests/unit/test_agent_review.py` (round limit, the hand-off
  text, findings left becomes Needs you).
- **Not in this slice**: review of PRs he did not hand (the automation
  starter in AG14).

## AG13. A HoldSpeak skill

- **Goal**: every agent knows how to work on his desk from its first turn.
- **Files**: `hs/cli_entry.py`, `hs/agent_skill/SKILL.md` (new),
  `hs/delivery/factory_launch.py`, `desk/conductor/ConductorWindow.tsx`
  (Connect).
- **Changes**: `holdspeak --skill` prints the skill of the installed
  version. Launches carry it with their settings; Connect installs it for
  his own Claude Code and Codex. Text per `DESIGN.md` (credential check
  first, read refs, say Done in one line, use a helper for review, never
  "Closes #N"). How Claude Code and Codex load a skill from a launch's
  settings folder: check the current CLI docs first (unknown).
- **Done when**: `holdspeak --skill` prints it; a launch's settings folder
  holds it; Connect writes it into the isolated `CLAUDE_CONFIG_DIR`.
- **Tests**: T1 the CLI output and the launch folder.
- **Not in this slice**: exporting Automations as skills.

## AG14. Automations that hand work to agents

- **Goal**: an automation hands items to agents on a schedule or an event,
  and their results land in Today.
- **Depends on**: Automations A-slices for *Do* kinds and *About*
  (`../workbench/RECIPE.md`), and Watches for Jira and GitHub events.
- **Files**: `hs/services/workbench_runner.py`, `hs/services/agent_hand_service.py`,
  the Automations window (its Do line), `hs/mcp/tools.py` (the `workbench.*` tools).
- **Changes**: *Do* kind **Hand to an agent** (agent, Review by); each run
  hands each new item once (skip items already handed), inside "working at
  once"; the run's result lists the agents started; each agent's Done is a
  New result in Today and on the automation. Starters shown only when
  their source works: Morning bug sweep, Review requests, Friday runbook.
  MCP: `automation.create` with `do: hand_to_agent`.
- **Done when**: a manual-run automation over two actions starts two fake
  agents; its result lists both; their Done results appear in Today; a
  second run starts none.
- **Tests**: T1 the runner (idempotent per item, inside the limit).
- **Not in this slice**: posting review findings anywhere (never; he sends).

## AG15. Agents he started himself (decision 1)

- **Goal**: his own Claude Code or Codex in his own tmux shows on the desk
  with its state, and he can answer it.
- **Files**: `hs/agent_context/screen_rules.py`, `hs/web_server.py`,
  `desk/conductor/ConductorWindow.tsx`.
- **Changes**: list the panes of his tmux server(s), find agent processes
  in each pane's process group, apply AG7's rules with the hook secret
  filter; show them in the folded "Agents you started yourself" with
  Answer and Allow (keys), no Stop, no brief. Nothing leaves the Mac. A
  switch for the rig (`HOLDSPEAK_OWN_AGENTS=off`, on by default in the
  product, off in every test rig, like the other isolation switches).
- **Done when**: in the rig, a fake agent started by hand in the rig's tmux
  (not by Hand to agent) shows in the section and answers reach it; at
  1440 and 393.
- **Tests**: T1 discovery on the rig's own tmux socket with the fake
  agent.
- **Not in this slice**: herdr's socket bridge (herdr study idea 9; only if
  he adopts herdr).
