# Agents: the code map (2026-10-17)

Read from `main` (`b746549b8`). Short paths: `desk/` is `web/src/desk/`,
`hs/` is `holdspeak/`. This map serves `DESIGN.md`; it is not a full audit.

## 1. What an agent is in data

There is no "agent" record. Four records describe one coding agent:

| Record | Where | What it holds | States |
|---|---|---|---|
| **Session** (from hooks) | `~/.config/holdspeak/agent_sessions.json`, key `agent:session_id`, at most 200 (`hs/agent_context/models.py:18`, `:32`) | cwd, tmux pane, last prompt, question, `wait_id`, last hook event | raw lifecycle `working · waiting · ended` (`models.py:46-49`); read-time decay to `idle` after 30 min and `ended` after 4 h (`models.py:51-53`, `sessions.py:171-195`) |
| **Launch** (Hand to agent) | `~/.holdspeak/agent_launches.json`, last 200 rows (`hs/delivery/factory_launch.py:63`, `:86`) | origin item, profile, worktree, branch, brief delivery, gate | `admitted … launched · registered · failed_to_register` (`factory_launch.py:774-1715`); brief `pending · sent · expired · session_gone …` (`hs/delivery/first_message.py:11-22`) |
| **Flight** (computed) | `hs/services/agent_flights.py` | the launch joined to its session and PR | `starting · working · waiting · pr_open · merged · ended · expired` (`agent_flights.py:15-24`) |
| **Auto-answer** | `~/.holdspeak/agent_answers.json` (`hs/services/agent_responder.py:50-92`) | the draft, its class (ROUTINE or REAL), the typed answer | `deciding · drafted · answered · escalated · superseded` |

Plus two unrelated things that also carry the word "agent":

- **Recipes** ("New Agent", saved personas): table `recipes`
  (`hs/db/schema.py:1414-1432`); the thread modes Chase, Desk, Draft,
  Interview and Plan are recipes too and show as `AGENT` in Search
  (`shots/48-search-agent-1440.png`).
- **Work attempts** of the Delivery board (`DeliveryBoard.tsx:62-65`).

## 2. Where state comes from

- **Hooks only.** The rider hook (`<prefix> agent-hook ingest --agent
  claude`) writes the session file under a lock; it makes no HTTP call
  (`hs/commands/agent_hook.py:55-79`). A hub loop checks the file every 2 s
  and broadcasts a `coder` frame on each change (`hs/web_server.py:143-171`,
  `:1924-1975`).
- **Event map** (`hs/agent_context/sessions.py:45-57`, `:115-122`): working
  = SessionStart, CwdChanged, UserPromptSubmit, Pre/PostToolUse, PreCompact,
  SubagentStop; waiting = Notification, Stop, PermissionRequest; ended =
  SessionEnd.
- **Blocked** (`models.py:258-275`): not ended and has a question; for
  Notification/PermissionRequest the subtype decides
  (`permission_prompt`, `idle_prompt`, `elicitation_dialog`,
  `models.py:233`). `wait_kind` is `approve` for a permission prompt, else
  `answer` (`models.py:364-371`).
- **The card text of a permission prompt is the hook's message**, "Claude
  needs your permission to use Bash". The command itself is not in the
  Notification payload, so the face cannot show it (`shots/16-*`).
- **Turn end** `asks · done · idle` (`models.py:352-361`). `done` only when
  the launch's PR is open (`agent_flights.py:92-95`). A flight whose
  session is not blocked reads **`working`** (`agent_flights.py:89`). This
  is why a finished agent with no PR says "Working" forever (`shots/23-*`).
- **No "seen" bit, no `unknown` state, no screen reading** as a state
  source. A stale session silently decays to idle (`models.py:51-53`).

## 3. The faces and their verbs

| Face | Opens from | Verbs | Notes |
|---|---|---|---|
| **Conductor** window | Dock, Go, ⌃3 (`desk/applications.ts:142-155`) | Answer / See the call (open the lane), Approve / Deny (gate proposals only, `desk/conductor/ConductorWindow.tsx:482-487`), Open, Get Info, Stop, Install hooks, Hide | Head text "No coder ready" / "N ready" (`ConductorWindow.tsx:226-228`); hooks line `:232`. `InstallHooksVerbs` is exported and never used (`:111`). |
| **Lane** window (one launch) | Conductor, Needs you, Room "Session" | Answer (AskWell), ARM, Use draft, Raw, Keys (INT ESC TAB ENTER arrows), Re-brief, Take back, Stop (inside Details), Open PR, Brief, Open terminal / Back to session | `desk/lane/LaneWindow.tsx`; only the lane's Answer sends `kind:"answer"` with `wait_id` (`desk/lane/laneStore.ts:257-260`). |
| **Session** window (a session with no launch) | Needs you "Open session", desk agent icon | ARM, keys, SPAWN, RENAME, KILL, Direct, SEND/ENTER, Speak, Keep as note, Flip, Pin | `desk/components/SessionPullout.tsx`. |
| **Coder card** | desk icon | Send reply, Speak to answer, Watch live | Bypasses the steer route: `/api/coders/select` + `/api/dictation/remote` (`desk/pullouts/CoderPullout.tsx:113`, `:134`). |
| **Needs you** rows | Needs you | Open session, Answer | `desk/needsYou.ts:376-436`; "CC" badge. The action row and its agent's row are separate. |
| **Hand sheet** | Object ▸ Hand to coder; Room/Door rows; drawer; drop | Launch, Cancel, Close, Send again | `desk/components/HandSheet.tsx:558-578`. The API takes `instruction`, the sheet never sends it (`HandSheet.tsx:329`, `:379`). |
| **Delivery board** | Search only (`desk/components/window/launcherRegistry.ts:17-21`) | Refresh, dossier, LAUNCH, Update source | A second launch path with no brief and no gate (`desk/deliveryFactory.ts:144-157`). Receipt key likely double-prefixed (`DeliveryBoard.tsx:157`). |
| **Terminals** | Search only | SPAWN | A raw tmux spawner (`shots/47b-*`). |
| **Mission Control** | a tab when repos have rails | pins, PROPOSE | `MissionControlConveyor.tsx:615`. |
| **New Agent** | Desk ▸ New Agent (`desk/verbRegistry.ts:224-233`) | Done, Continue in thread, Edit | Makes a recipe. Its Tools field is saved and never read (`hs/services/recipe_service.py:233-234`). |
| **Agents** app (old) | URL `/companion` only | Answer, Conductor, New agent | Parked, manifest row alive (`desk/applications.ts:156-175`). |

### Dead or duplicated

- **Answer lives in six places** (Conductor, lane, session window, coder
  card, Needs drawer `desk/needs/NeedsDrawer.tsx:138`, Today's "Speak
  answer" `desk/chair/ChairHome.tsx:2874`), with three different paths
  underneath; only one checks that the question is still current.
- **Stop lives in three places** (Conductor, lane, session window).
- **Four launch paths**: Hand (`/api/agent/hand`), Delivery board LAUNCH,
  SPAWN (`/api/coders/factory/spawn`), PR send-agent
  (`hs/web/routes/delivery_prs.py:158-198`).
- **One session, five faces**: Conductor, lane, session window, Needs you
  row, Mission Control pin; the Delivery board shows it a sixth time as a
  work attempt.
- **The hand verb needs a selected desk icon** (`verbRegistry.ts:514-516`:
  `selected(ctx)` else "Select an object"). A note open in front is not
  "selected" (`shots/07b-*`).
- **Today's Agents section is parked** (`ChairHome.tsx:1466-1469`).
- **The Dock tile shows no state** (`desk/components/window/Dock.tsx:479-486`);
  the count sits on the desk icon.

## 4. Answers and keys

- Live terminal: `GET /api/coders/{key}/peek?raw=1` polled every 1.5 s
  while a lane or session is open; the server runs `tmux capture-pane` and
  answers `not_modified` on an unchanged hash (`desk/steering.ts:75-76`,
  `hs/coder_steering.py:136-204`). The xterm is read-only
  (`desk/surface/XtermPane.tsx:106`).
- Text and keys go through `process.input`, literal text then Enter
  (`coder_steering.py:614-622`); keys are an allow-list (`:802-813`).
  `deliver` re-checks `wait_id` and refuses `wait_not_current` (`:769-776`).
- **ARM**: Secure and Normal need an arm grant first; YOLO with a known pane
  is direct (`coder_steering.py:562-603`). Arm refuses a paneless session
  with 409 (`hs/web/routes/system/coder_steering_routes.py:220-237`), and the face
  then still says "ARM FIRST" (`shots/39b-*`).
- **Auto-answers** (`hs/services/agent_responder.py:1-31`): Secure, no
  draft; Normal, a draft shown; YOLO, the question is held out of Needs
  you while the model drafts, a ROUTINE answer is typed with the prefix
  "The desk:", and nothing tells him. Observed: 44 s hold; it answered
  "Yes, …" to a "1 or 2" question (`shots/17-*`).
- Re-brief is typed now if the agent waits, else queued (at most 3, 2 h)
  (`hs/services/launch_rebrief.py:1-19`).

## 5. Hand to agent

- `POST /api/agent/hand {kind, id, instruction?, profile?, project_id?}`;
  preview at `/api/agent/hand/preview` (`hs/web/routes/agent_hand.py:88-165`).
  Kinds: action, decision, decision_record, project_item, note, meeting,
  artifact, issue.
- Needs a Project whose repository resolves to a Delivery Source
  (`hs/services/agent_hand_service.py:160-231`), makes worktree
  `hs-<kind>-<id>` on branch `hs/<kind>-<id>` (`:106-138`), and refuses
  past **3 live launches** (`MAX_LIVE_LAUNCHES = 3`, `:59`, `:373-377`). A
  finished agent with a live tmux session still counts.
- Gated spawn: Bash held to the new worktree (`:405-408`, `:551-570`); the
  brief waits for the rider to register (up to 30 min,
  `factory_launch.py:1429-1451`).
- Claude's argv gets `--settings`, `--mcp-config`, `--permission-mode
  acceptEdits` and `--allowedTools Bash mcp__holdspeak`
  (`factory_launch.py:1122-1136`, `hs/delivery/agent_mcp.py:114-161`).
- The executable is a bare name resolved by `$SHELL -c` inside tmux
  (`hs/coder_factory.py:185-193`); the credential arrives through a
  one-shot 0600 file read by `/bin/sh` before exec (`coder_factory.py:115-134`).

## 6. The desk's tools for agents (MCP)

- Each launch gets credential `agent:launch:<id>` with the **CONDUCTOR**
  palette: every WORK tool, People reads, decisions only as "proposed",
  and changes only to its own item or what it created
  (`hs/mcp/palettes.py:61-138`, `hs/services/conductor_launch.py:1-31`).
- `coder.list`, `coder.get`, `coder.audit` are reads; "steering verbs are
  out of scope" (`hs/mcp/families/coder.py:13-46`).
- `agent.hand` is **EGRESS** (`hs/mcp/tool_authority.py:289`) and not in the
  palette (`palettes.py:96-106`): an agent cannot start another agent.
- No `agent.prompt`, `agent.wait`, `agent.read`. No skill file.

## 7. What does not exist

- **Seen / unread** for a finished turn.
- **Resume** after the tmux session dies: nothing passes `--resume`,
  `resume` or `--session` (grep of `hs/`); the only "resume" re-sends a held
  brief (`agent_hand.py:277-297`).
- **Builder → reviewer pair**: PR send-agent starts one agent on a PR
  worktree (`delivery_prs.py:158-198`); nothing chains two.
- **An automation that starts an agent**: no caller of the hand service
  outside the routes, MCP and PR send-agent.
- **An agent's result in Today**: only a Needs you coder row
  (`ChairHome.tsx:1687`); the Room shows a merge receipt
  (`desk/agentFlights.ts:250-261`).
- **Screen detection, `unknown`, explain, agents he started by hand**
  outside hooks (`herdr/STUDY.md` §2).

## 8. Constraints a redesign keeps

- The credential bootstrap (one-shot file, never argv).
- The tool gate fails closed (`hs/coder_gate.py:502-516`), the Control modes
  Secure / Normal / YOLO (default YOLO, `hs/operation_policy.py:31-36`), and
  the owner's mapping in `docs/internal/CONDUCTOR.md`.
- Stop ends recorded process groups with generation checks
  (`coder_factory.py:298-378`).
- `deliver` re-checks the wait before typing.
- The stored names (`coder`, `launch`, `flight`, `agent_hand`, the MCP
  family `coder.*`) stay in code; only the face changes words.
- tmux is the runtime; no new binary for a first-time user (herdr study §4).
