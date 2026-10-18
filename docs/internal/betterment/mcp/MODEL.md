# HoldSpeak MCP: the map for agent engines

Status: code map for the orchestrator, 2026-10-17. Read only: no product
code changed, no test run, no prompt sent to a model. Companions:
`../workbench/DESIGN.md` (Automations) and `../engines/DESIGN.md` (Engines).

**The idea this map serves.** When an automation's engine is an agent CLI
(Claude Code `claude -p`, Codex `codex exec`, pi `pi -p`), the agent gets
HoldSpeak's own MCP server. It then looks up meetings, people, projects,
decisions, Jira, memory and the rest itself, and the prompt does not have to
carry every source.

**The short answer.** Most of this exists already. The Conductor (the coding
agents HoldSpeak launches) gives each agent the HoldSpeak MCP over the hub's
HTTP route, with a credential bound to the launch and a hub-side tool set
named **CONDUCTOR**. That tool set is exactly "read, plus local desk writes;
no egress, no authority, no config, People read only". An automation can use
it as it is. What is missing is a launch path that does not need a tmux
pane, and the new automation fields on MCP.

The owner's rulings this map respects, and where the code quotes them:

- Agents read People over MCP; People writes stay with the owner
  (2026-10-06).[^people-ruling]
- MCP flows through the service layer: one composition root, thin
  transports (2026-09-23, HS-200-45).[^service-layer]
- A thread acting as the owner stops for his press on EGRESS, AUTHORITY and
  CONFIG; everything else is WORK and runs in its posture, YOLO included
  (2026-09-29, #694).[^thread-rule]

---

## 1. The server: where it lives, how it is served, who it runs as

### Where it lives

| Part | File |
|---|---|
| Tool catalogue and dispatch (main tools) | `holdspeak/mcp/tools.py` (257 tools in all, with the families) |
| 23 tool families | `holdspeak/mcp/families/*.py`, loaded in order by `families/__init__.py:30-54`; a broken family is recorded and skipped, never fatal (`:57-66`) |
| Authority table (WORK / EGRESS / AUTHORITY / CONFIG) | `holdspeak/mcp/tool_authority.py:38-298` |
| Named tool sets ("palettes") | `holdspeak/mcp/palettes.py` |
| Per-launch rules for a launched agent | `holdspeak/services/conductor_launch.py:290-386` |
| Resources (`holdspeak://…`) | `holdspeak/mcp/resources.py:133-262` |
| JSON-RPC handler | `holdspeak/mcp/server.py:277-347` (stdio) and `:361-478` (HTTP, with a principal and a palette) |

### Two transports, one writer

1. **The hub's HTTP route, `POST /api/mcp`.** This is the real server. The
   route hands each message to `handle_message_for_principal` with the
   principal the web-auth middleware derived.[^route] Tool calls never run on
   the event loop. Ordinary calls run one at a time on one MCP worker thread,
   first in, first out. Model, `gh` and `acli` tools ("long tools") run on
   the thread pool beside that queue. Every call first takes per-object locks
   (a `workbench_id`, a `project_id`, …).[^queue]
2. **The stdio sidecar, `uv run holdspeak-mcp`** (what `.mcp.json` starts).
   It composes nothing and never opens the database. For each message it
   finds the running hub through the owner lock beside the database file,
   and forwards the message verbatim to `POST http://127.0.0.1:<port>/api/mcp`
   with the **owner's** web token, which it reads from the config
   file.[^sidecar] With no hub, only `initialize` and `ping` answer; every
   tool call returns "No running HoldSpeak hub …; start `holdspeak web`".[^nohub]

Because both transports reach the same composed services, a desk write over
MCP puts the same `desk_changed` frame on `/ws` as the face does.[^service-layer]

### How a client authenticates, and the principal it runs as

| Caller | Credential | Principal | Tool set | With the Reach switch off |
|---|---|---|---|---|
| stdio sidecar (`.mcp.json`), or any loopback call with the owner token | owner web token | `OWNER` | **all 257 tools**, no palette | admitted (loopback owner) |
| Owner token from off-loopback | owner web token | — | — | refused 403 (`owner_refused_remote`) |
| An agent HoldSpeak launched | launch-bound agent credential (`launch_id` set) | `AGENT`, identity `agent:launch:<id>` | **CONDUCTOR**, re-resolved per request, plus a per-call gate on arguments | admitted from loopback |
| A credential the owner issued by hand (Reach) | agent credential | `AGENT` | PROJECT, SWEEP, DESK or ALL | needs Reach on |
| Nothing | — | `NONE` | — | 401 |

Sources: the gate and palette derivation are `mcp_http.py:139-232`; the
credential's fields are `principals.py:585-602`; `/api/mcp` takes the
`AGENT_SUBMIT` edge right so the route can admit agents (`principals.py:643-644`).
The sidecar's own `auth.py` always says `OWNER` (`mcp/auth.py:27-32`). A
credential is stored as a hash, lives 12 hours by default and at most 30 days
(`principals.py:377-407`, `:605-606`). A token in the query string is refused
(`mcp_http.py:182-187`).

**What this means for automations.** An automation agent must never get the
stdio sidecar. Through it, the agent would be the owner, with every tool
including `channel.send`. It must get the hub URL and a launch-bound
credential, which is what the Conductor already does (section 4).

---

## 2. Every tool family, classified

### The classes

The code has four classes (`tool_authority.py:32-35`). This map splits the
code's WORK into three, so you can see what an automation would do:

- **READ**: changes nothing. The tool's last word is a read verb
  (`tools.py:929-947`), or the launch rules call it a read.
- **DESK-WRITE**: WORK in code that changes only local state on this Mac
  (a note, a card, a draft, a window, a setup draft, a capture).
- **MODEL**: WORK in code that runs a model on the owner's assigned engines
  ("composer" in the launch rules, `conductor_launch.py:372-385`). Not
  offered to a launched agent: no model call inside a model call.
- **EGRESS**, **AUTHORITY**, **CONFIG**: as in code. Each one stops for the
  owner's press.

The last column counts the tools in the CONDUCTOR set, which is what a
launched agent can call (`palettes.py:96-106`).

### Counts per family

| Family | Tools | READ | DESK-WRITE | MODEL | EGRESS | AUTHORITY | CONFIG | Offered to a launched agent |
|---|---|---|---|---|---|---|---|---|
| desk (`desk.*`) | 8 | 4 | 4 | | | | | 8 |
| workbench | 10 | 3 | 6 | 1 | | | | 9 |
| meeting | 10 | 4 | 4 | 1 | | 1 | | 4 |
| recipe | 4 | 2 | | 2 | | | | 2 |
| zone, kb | 6 | 2 | 4 | | | | | 6 |
| proposal | 2 | | 2 | | | | | 0 |
| steward, nudge | 3 | 1 | 1 | | 1 | | | 1 |
| dictation | 2 | 2 | | | | | | 2 |
| settings (`settings.hub`, `settings.get/update`) | 3 | 2 | | | | | 1 | 2 |
| decision_record, decision | 6 | 3 | 3 | | | | | 4 |
| kernel, pipeline | 2 | 2 | | | | | | 2 |
| follow_through | 3 | 1 | 2 | | | | | 2 |
| monday_brief | 4 | 3 | | 1 | | | | 3 |
| scheduled_recording | 5 | 1 | 4 | | | | | 5 |
| ask | 4 | 1 | 2 | 1 | | | | 2 |
| coder | 3 | 3 | | | | | | 3 |
| cadence | 11 | 5 | 5 | 1 | | | | 5 |
| sequence, workflow | 4 | | 2 | 2 | | | | 0 |
| memory | 3 | 3 | | | | | | 3 |
| people | 18 | 5 | 10 | | | 2 | 1 | 5 |
| plugin_job | 4 | 2 | 2 | | | | | 2 |
| reactions, watch, event | 11 | 5 | 2 | | | | 4 | 5 |
| thought | 18 | 2 | 13 | 2 | | | 1 | 15 |
| inference, model_library | 8 | 1 | | | | | 7 | 1 |
| inference_assignment | 5 | 3 | | | | | 2 | 3 |
| concierge | 5 | 2 | 1 | | | | 2 | 2 |
| door, thread | 3 | 1 | 2 | | | | | 2 |
| project, provider, connection | 65 | 24 | 30 | 1 | 1 | 2 | 7 | 31 |
| channel | 9 | 4 | 1 | | 2 | 2 | | 5 |
| heartbeat | 4 | 1 | 2 | | | | 1 | 1 |
| interview | 4 | 1 | 2 | 1 | | | | 1 |
| practice_recipe | 3 | 2 | 1 | | | | | 2 |
| agent (`agent.hand`) | 1 | | | | 1 | | | 0 |
| desk_window | 6 | 1 | 5 | | | | | 6 |
| **All** | **257** | **96** | **110** | **13** | **5** | **7** | **26** | **144** (96 reads, 48 writes) |

The counts come from the live catalogue: `holdspeak.mcp.tools.TOOLS` joined
with `TOOL_AUTHORITY`, `is_read_tool`, `LAUNCH_RULES` and
`resolve_palette("CONDUCTOR")`, read on this tree with no family degraded.

### The 38 tools that stop for the owner's press

| Class | Tools | Source |
|---|---|---|
| EGRESS (5) | `nudge.send` (a GitHub comment as him), `channel.send`, `channel.discard`, `project.mark_update_delivered` (the delivery ledger), `agent.hand` (starts a cloud coding agent) | `tool_authority.py:78,228,275-276,289` |
| AUTHORITY (7) | `meeting.import` (reads a path on his disk), `people.owner_alias.link/unlink`, `project.archive`, `project.configure_steward`, `channel.save_destination/remove_destination` (the egress allow-list) | `:71,146-147,209,229,270-271` |
| CONFIG (26) | `settings.update`, `people.access.set`, `watch.create/set_enabled`, `reaction.create/set_enabled`, `thought.replace_default_context`, `inference.cancel_model_acquisition`, six `model_library.*` writes, `inference_assignment.set/clear`, `concierge.apply/download`, `project.setup.finalize`, `provider.jira_add_connection`, five `project.watch.*`/`add_suggested_source`, `heartbeat.set` | `:110,149,156-163,168,183-200,238,244,256-262,280` |

Four WORK tools are decided per call, on their arguments: `workbench.create`,
`workbench.update`, `scheduled_recording.create` and `scheduled_recording.update`
become AUTHORITY when the call turns on or changes a schedule
(`tool_authority.py:311-356`). The service also refuses a schedule enable
from a non-owner (`workbench_service.py:111-112`).

### Three corrections to the brief's sorting

- **`project.publish_update` is not egress in code.** It is WORK
  (`tool_authority.py:220`): it moves a draft to *published* inside the
  project, and nothing leaves the Mac (`families/project.py:332-333`). The
  delivery is `channel.send` or `project.mark_update_delivered`. It is still
  never offered to a launched agent (`conductor_launch.py:358`).
- **Deletes are WORK in code**, not AUTHORITY: `desk.delete`,
  `meeting.delete`, `workbench.delete`, `scheduled_recording.delete`
  (`tool_authority.py:43,53,69,103`). A launched agent can delete only what
  it made in the same launch, and never a meeting
  (`conductor_launch.py:290-325`).
- **People writes are WORK in the authority table** (`:136-145`). Agents
  are kept out of them by the CONDUCTOR set, which offers only the People
  reads (`palettes.py:69-81`, `families/people.py:227-233`). For the owner,
  People access defaults to *write* (`families/people.py:298-303`).

### What an automation will want, and whether it can have it

Every tool below is in the CONDUCTOR set unless marked.

| Need | Tools | Class |
|---|---|---|
| Meetings | `meeting.list` (query, dates, speaker, tag, open actions), `meeting.get`, `meeting.export` (Markdown or JSON), `meeting.proposals` | READ |
| Memory | `memory.search` (decisions, meetings, notes, threads, actions, milestones, risks, sends, updates, briefs, calendar events), `memory.page`, `memory.observations` | READ |
| People | `people.relationship.list/get`, `people.grounding.get`, `people.one_on_one.brief`, `people.readiness`. Shared intent only; leader-private prep never crosses MCP. Off when he sets People access to `off`. | READ |
| Projects | `project.list/get/get_room/get_delta`, `project.item.list`, `project.list_updates`, `project.resource.list`, `project.suggested_sources` | READ |
| Decisions | `decision_record.list/get/search` | READ |
| What waits for him | `desk.needs_you`, `follow_through.board`, `steward.nudges`, `cadence.loops/status` | READ |
| Jira | `provider.jira_search` (JQL), `provider.jira_discover`, `provider.jira_connections` | READ (network read through `acli`) |
| GitHub | `provider.github_connection`, `provider.github_discover` (repositories only), `provider.github_validate_repo` | READ (`gh`) |
| Desk | `desk.list/get/snapshot`, `zone.list_members`, `kb.list_members`, `dictation.list/get`, `event.list` | READ |
| Write a result locally | `desk.create` (a note; a decision only as *proposed*), `door.add_item` (a Follow-Through card), `thought.create`, `project.item.create` (launch's own project only), `channel.prepare` (prepares a send he presses) | DESK-WRITE |
| Not offered | `project.draft_update`, `monday_brief.generate`, `ask.run`, `workbench.run` and the other MODEL tools; every People write; `proposal.confirm`, `decision_record.create_*`, `project.accept_review` (his Confirm, `palettes.py:86-93`) | — |

**A gap:** there is no GitHub pull-request or issue read. "When GitHub asks
me to review, summarize the PR" cannot be done over MCP today. The watch
events arrive in `event.list`, but the PR body and diff do not.

---

## 3. The gating that exists, and the profile an automation needs

### What is enforced today

1. **The authority table** (`tool_authority.py`). One row for every tool; a
   fence test fails on a tool without a row (`:24-26`). Threads take only
   WORK rows (`THREAD_EXCLUDED`, `:301`; used by `services/thread_tools.py:340`).
2. **The palettes** (`palettes.py`). Named sets: PROJECT, SWEEP, DESK, ALL
   for credentials he issues (`:150-169`), and CONDUCTOR, which only a
   launch issues (`coder_factory.py:89-103`). A tool outside the palette is
   refused with `MCP-005` and is not in `tools/list` (`server.py:400-404,453-461`).
3. **CONDUCTOR's per-call gate** (`palettes.py:127-138`): the tool must be
   WORK on these arguments, not a People write, not his Confirm, not a
   NEVER or MODEL tool, and a desk decision must be *proposed*.
4. **Launch ownership** (`conductor_launch.py:1-31`): a launch edits,
   files and deletes only what it created; item tools touch only its origin
   item or items it made; project writes only add to its own project. This
   is held in the services and the kernel, not only on MCP.
5. **The kernel's desk delegation** (`kernel/desk.py:31-38`): filing,
   deciding, and zone and KB changes by an agent need a live grant. A launch
   gets one for `decision.create` only. Creating a note needs no grant.
6. **`tool_gate_rules.py` is not an MCP gate.** It reads one *Bash* or
   *Edit* call of a launched coding agent and says inside, outside or
   unparsed for its worktree (`tool_gate_rules.py:1-24`). An MCP tool keeps
   its own name and is not read there (`agent_context/hooks.py:290-291`). For
   an automation with built-in tools off, it does not apply.
7. **Control mode on the agent side.** In Normal and YOLO, the `holdspeak`
   tools are pre-approved in the agent; in Secure, each call asks in the
   pane (`delivery/agent_mcp.py:24-27,109-111`). The hub's palette decides
   in every mode.

### Does a "read + desk-write, no egress or config" profile exist?

**Yes. It is CONDUCTOR.** It is derived from the authority table, so a new
tool classifies itself (`palettes.py:45-59`). It holds 96 reads and 48 local
writes, and no EGRESS, AUTHORITY, CONFIG or MODEL tool (section 2).

What an unattended automation might still not want from it:

- the six `desk_window.*` tools (an overnight run should not rearrange his
  windows);
- `scheduled_recording.create/update/delete` and `workbench.create/update/delete`
  (they are limited to the launch's own records, so the harm is small).

**Recommendation (Tenet 1).** Use CONDUCTOR as it is for the first slice. If
the window tools prove a nuisance, an AUTOMATION palette is one more branch
in `resolve_palette` (`palettes.py:153-169`): CONDUCTOR minus
`desk_window.*`. That is about ten lines and reuses the same call gate. Do
not add a second allowlist in the agent's flags; the hub already refuses.

### A risk to know before building

A run started over MCP holds the lock for its `workbench_id` for the whole
run (`workbench.run` is a long tool keyed on `workbench_id`;
`long_tools.py:42-45,69-72`; locks taken in `mcp_http.py:256-267`). If the
agent inside that run calls `workbench.get` or `workbench.list_runs` on the
same automation, that call waits on the lock until the run ends or times
out. A run started from the face or the scheduler does not go through this
route. **Unverified live**; it is read from the code. The cheap fix: the
prompt already names the automation, so the agent does not need to read it,
or the run is started off the MCP route.

---

## 4. How agents get the HoldSpeak MCP today, and the one-shot form

### Today (the Conductor, tmux sessions)

`coder_factory.spawn` issues a credential with identity
`agent:launch:<launch_id>`, the CONDUCTOR palette and the launch id
(`coder_factory.py:89-103`). The token reaches the session from a one-shot
0600 file the session reads and deletes, never argv
(`coder_factory.py:115-124`); the hub URL rides `HOLDSPEAK_HUB_URL`
(`:130`). `delivery/agent_mcp.py` then gives each harness the server
`holdspeak`:

| Harness | How the server is attached | Source |
|---|---|---|
| Claude Code | `--mcp-config <0600 file>` with `{"type":"http","url":"${HOLDSPEAK_HUB_URL}/api/mcp","headers":{"Authorization":"Bearer ${HOLDSPEAK_AGENT_CREDENTIAL}"}}`; plus `--allowedTools mcp__holdspeak` when not Secure, and `--permission-mode acceptEdits` | `agent_mcp.py:53-63,114-125,146-161` |
| Codex | `-c mcp_servers.holdspeak.url="…/api/mcp"`, `-c mcp_servers.holdspeak.bearer_token_env_var="HOLDSPEAK_AGENT_CREDENTIAL"`, and `default_tools_approval_mode="approve"` when not Secure | `agent_mcp.py:128-138` |
| pi | `mcp.json` in the launch's own `PI_CODING_AGENT_DIR` (URL as text, bearer header from the variable); core tools direct, the rest found through `tool_search` | `pi_launch.py:59-68,171-186,232-240` |

The repository's `.mcp.json` is a different thing: it starts the stdio
sidecar as the owner, for an editor the owner runs. Codex hook trust
(`agent_context/codex_trust.py:1-23`) is about hooks, not MCP.

A one-shot CLI call already exists, without MCP: the summarizer runs
`claude -p --tools "" --no-session-persistence --output-format json
--max-budget-usd 0.10` and `codex exec --sandbox read-only --ephemeral -`
(`agent_summarizer.py:139-160`), and refuses the dangerous flags
(`:163-188`).

### The installed CLIs (this Mac, 2026-10-17)

- Claude Code **2.1.302**; Codex CLI **0.161.0**; pi **1.1.0**.
- At the M0 live check (2026-10-17, late): Codex CLI is **0.163.0**
  (`codex --version`); Claude Code and pi unchanged.

Flags confirmed in `--help` (no prompt sent):

| Need | Claude Code (`claude --help`) | Codex (`codex exec --help`, `codex mcp add --help`) | pi (`pi --help`) |
|---|---|---|---|
| One shot | `-p, --print` | `codex exec [PROMPT]`, `-` reads stdin | `-p, --print` |
| Add our server | `--mcp-config <configs...>` (files or JSON strings) | `-c mcp_servers.<name>.url=…`, `bearer_token_env_var` (named in `codex mcp add`) | `mcp.json` in `PI_CODING_AGENT_DIR` (as today) |
| Only our server | `--strict-mcp-config` | `--ignore-user-config` (also drops his model and provider settings; auth still uses `CODEX_HOME`) | `--no-mcp` turns all MCP off (not what we want) |
| Built-in tools off | `--tools ""` | `--sandbox read-only` (shell commands still run, read only) | `--no-tools` / `--no-builtin-tools`, `--tools`, `--exclude-tools` (applies to MCP tools too) |
| Allow / deny tools | `--allowedTools`, `--disallowedTools` | per-server `default_tools_approval_mode` (used by our code) | `--tools` keeps MCP tools unless an entry starts with `mcp__` |
| No prompts | `--permission-prompts none` (anything that would ask is denied) | non-interactive by design | non-interactive by design |
| No saved session | `--no-session-persistence` | `--ephemeral` | `--no-session` |
| Output | `--output-format json` | `--json` (JSONL events), `-o <file>` (last message) | `--mode json` |
| Model | `--model` | `-m, --model` | `--model` |
| Work folder | the process cwd | `-C, --cd`, `--skip-git-repo-check` | the process cwd |

Not in `claude --help` on this version: `--max-turns`.

### The one-shot commands this design needs

The prompt goes on stdin. The hub sets `HOLDSPEAK_HUB_URL` and
`HOLDSPEAK_AGENT_CREDENTIAL` in the child's environment only. The cwd is an
empty temporary folder.

Corrected by the M0 live check (2026-10-17; see Unknown):

```
claude -p --output-format json --no-session-persistence \
  --strict-mcp-config --mcp-config <0600 file from claude_mcp_document()> \
  --tools "" --allowedTools mcp__holdspeak --permission-prompts none \
  [--model M] [--max-budget-usd N]

codex exec --ephemeral --sandbox read-only --skip-git-repo-check -C <tmp> --json \
  -c features.apps=false -c web_search="disabled" \
  -c features.plugins=false -c features.multi_agent=false \
  -c features.image_generation=false -c features.browser_use=false \
  -c features.computer_use=false -c features.in_app_browser=false \
  -c features.tool_suggest=false -c features.skill_search=false \
  -c features.goals=false -c features.sleep_tool=false \
  -c features.view_image=false -c features.shell_tool=false \
  -c features.unified_exec=false \
  -c mcp_servers.<each name from `codex mcp list --json`>.enabled=false \
  -c mcp_servers.holdspeak.url="<hub>/api/mcp" \
  -c mcp_servers.holdspeak.bearer_token_env_var="HOLDSPEAK_AGENT_CREDENTIAL" \
  -c mcp_servers.holdspeak.default_tools_approval_mode="approve" \
  [-m M] -

PI_CODING_AGENT_DIR=<launch folder with models.json + mcp.json> \
PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 \
  pi -p --no-session --mode json --no-builtin-tools --model lan/<model>
```

- **Codex:** `features.apps=false` is required. Without it, the ChatGPT
  login's apps (`mcp__codex_apps__*`: GitHub writes up to
  `github_merge_pull_request`, Sites deploys, pets, parental controls)
  reach the agent. Do NOT set `features.code_mode_host=false`: MCP calls go
  through code mode, and with it off the MCP tool is not callable.
  `include_apply_patch_tool` is not a 0.163 key (Codex says "ignored").
- **pi:** the prompt goes on stdin, and stdin MUST be closed (EOF). With an
  open stdin and the prompt as an argument, pi waited and sent nothing for
  more than 300 s.

**What is new code** (small): a launch path that needs no tmux. Issue the
CONDUCTOR credential the same way `spawn` does (`agent_credentials.issue(...,
palette_name=CONDUCTOR, launch_id=...)`, `principals.py:377-387`), with a
time to live near the run's time limit; write the 0600 config; run the
process; revoke the credential and remove the config when it exits
(`agent_mcp.remove_mcp_config`, `agent_mcp.py:84-97`). A launch-bound
credential from loopback is admitted with Reach off (`mcp_http.py:159-176`),
so nothing else changes on the hub. The automation run happens inside the
hub, so the hub is always up.

**Things to know:**

- The owner's `~/.codex/config.toml` holds an `mcp_servers.pixellab`
  server. A plain `codex exec` loads it too. `-c
  mcp_servers.pixellab.enabled=false` keeps it out and keeps his model
  (`codex mcp list` shows `disabled`; resolved in M0).
- Claude Code tool names use underscores: `mcp__holdspeak__channel_send`
  for `channel.send` (`agent_context/hooks.py:290-291`).
- `--tools ""` removes the built-in set only; MCP tools from
  `--mcp-config` stay callable (resolved in M0, see Unknown).

---

## 5. Cost reporting

| Question | Answer | Evidence |
|---|---|---|
| Does `claude -p --output-format json` report the cost? | **Yes.** The result has `total_cost_usd`, `usage` (input, output, cache read, cache creation, thinking tokens), `modelUsage` per model (with `costUSD`), `num_turns`, `duration_ms`, `is_error`, `subtype`, and `permission_denials`. | A recorded result in the tree: `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/story-03-check-response-astra-invoked-claude.json:5-10` (2026-09-24, an older CLI version) |
| Is that the money he pays? | **Not always.** The same result says `"costBasis": "list"`: the figure is computed at list price. On a subscription login, it is an estimate, not a bill. | same file, `modelUsage` |
| Does `--max-budget-usd` exist? | **Yes**, in 2.1.302: "Maximum dollar amount to spend on API calls (only works with --print)". | `claude --help` |
| Does it apply to a subscription login? | **Yes** (M0, Max login). It stops on the list-price estimate. It is checked after a turn, so the run overshoots: cap $0.0001, spent $0.0045, one turn, the tool not called. Result: `subtype: "error_max_budget_usd"`, `is_error: true`, `terminal_reason: "budget_exhausted"`, `errors: ["Reached maximum budget ($0.0001)"]`, `result: null`, exit 1. | M0, Unknown below |
| Codex | No budget flag. `--json` (0.163) gives **tokens only, no dollars**: `turn.completed.usage` = `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens`. The model is not named in the events. | M0, Unknown below |
| pi | `--mode json`: each `turn_end.message` has `provider`, `model`, `usage` {`input`, `output`, `cacheRead`, `cacheWrite`, `reasoning`, `totalTokens`, `cost` {`input`, `output`, `cacheRead`, `cacheWrite`, `total`}}. On the LAN model every cost is 0. | M0, Unknown below |

For the Engines design (decision 3): show `total_cost_usd` on each Claude
Code result and label it "estimate" when the login is a subscription; pass
`--max-budget-usd` only when he sets a limit; say "Codex cannot limit
spend" on the Codex row.

---

## 6. MCP parity for the new designs

### What exists

| Area | Tools | Class |
|---|---|---|
| Automations (workbenches) | `workbench.list/get/list_runs` | READ |
| | `workbench.create/update` (fields: `id`, `name`, `recipe_id`, `schedule` (cron text), `schedule_enabled`, `schedule_revision`, `item_order`) | WORK; AUTHORITY when a schedule field is set |
| | `workbench.delete`, `add_item`, `update_item`, `delete_item` (parks) | WORK |
| | `workbench.run` | MODEL (long tool) |
| | Event starts: `reaction.create/set_enabled` (CONFIG) on a `watch.create` (CONFIG); `reaction.list`, `watch.list`, `event.list` (READ) | |
| Engines | `model_library.get` (READ); `connect_hosted_model` (families `openrouter`, `anthropic`), `define_endpoint` (`openai_compatible`, `private_endpoint`, `future_backend`), `connect_paired_device`, `download`, `add_to_library`, `use_model_file` (CONFIG) | |
| What runs where | `inference_assignment.summary/editor/preview_use_default` (READ); `set`, `clear` (CONFIG). Scope can be one subject: `subject_kind` in `thought`, `workbench`, `agent`, `recipe`, `project` | |
| Finding engines | `concierge.detect`, `concierge.probe` (READ); `propose` (WORK); `apply`, `download` (CONFIG) | |

Sources: `tools.py:153-174,229-262`; `families/reactions.py`;
`families/model_library.py:53-110`; `families/inference_assignments.py:49-54,73-109`;
`families/concierge.py`.

### What is missing, for the new shape

The new automation is one sentence: **When · Do · About · With · Put it in**
(`../workbench/DESIGN.md` §4).

| To do this | Missing on MCP | Its class when built |
|---|---|---|
| Write **Do** (the instruction on the automation) | No field. Today the instruction lives in the recipe (`recipe_id`), and there is no MCP tool to write a recipe's prompt. | WORK |
| Write **About** (named sources: meetings, drawers, projects, people) | No field. Sources live on each item (`grounding_json`). | WORK |
| Write **Put it in** (Inbox, Needs you, a file, a saved destination) | No field. Results go to a `pending-review` artifact. | WORK (a destination only *prepares* a send) |
| Set **When** in plain terms (day, time, "a meeting ends", "a note lands in…") | Only cron text, plus a reaction on a watch, which are two tools and two classes. No trigger for "a meeting ends" or "a note lands". | AUTHORITY (extend `_SCHEDULE_FIELDS`, `tool_authority.py:311-325`, with the trigger fields) |
| Set **With** | Works today: `inference_assignment.set` with subject `workbench:<id>`. | CONFIG |
| Run now and read the result | `workbench.run` works. No one call returns "the newest result, rendered". No per-run engine, cost or failure reason (the run record is wrong today; `../workbench/MODEL.md`). | READ (a `workbench.results` read) |
| Turn on or off | Only `schedule_enabled`. | AUTHORITY (as today) |
| Cancel a running run | No tool. | WORK |
| Connect a **CLI engine** (Claude Code, Codex, pi) | No engine kind. No `provider_family` for a CLI in any `model_library` draft. | CONFIG (one new `model_library.connect_cli_engine`, beside `connect_hosted_model`) |
| See CLIs **Found on this Mac** | `concierge.detect` does not list CLIs (`../engines/MODEL.md` §2). | READ |
| Remove an engine | No `model_library` remove tool. | CONFIG |
| Set a **spend limit** on an engine or an automation | No field. | CONFIG |
| Let the agent read a **repository folder** (Automations decision 3) | Not an MCP question: it is the agent's own read-only file tools in that folder. | — |
| Read a **GitHub PR** for a review starter | No tool (section 2). | READ |

Nothing on this list needs a new gate. Each new tool takes one row in
`TOOL_AUTHORITY`, and the CONDUCTOR set picks up the WORK rows by itself.

---

## Unknown

Resolved by the M0 live check, 2026-10-17 (the owner's OK: DECISIONS.md #4).
Each CLI ran in an empty temporary folder, with a stdio test server `ping`
(one tool; it returns `pong-<random hex>`) in place of the hub. The server
wrote a log of each request, so "called" below is the server's own record,
not the model's word.

- **RESOLVED: `claude -p --tools ""` keeps MCP tools.** Command:
  `claude -p --tools "" --strict-mcp-config --mcp-config <ping.json>
  --allowedTools mcp__ping --permission-prompts none --output-format json
  --no-session-persistence`, prompt "Call the ping tool and reply with its
  result only." Result: `"result": "pong-8b144bc3"`, `num_turns: 2`,
  `is_error: false`; the server log has `tools/call` → `pong-8b144bc3`.
  `--allowedTools mcp__<server>` allows every tool of that server.
- **RESOLVED: `--strict-mcp-config` drops the claude.ai connectors.** The
  same command with `--output-format stream-json --verbose`, prompt "List
  every tool name you can call, one per line." The `system/init` event:
  `tools: ['mcp__ping__ping']`, `mcp_servers: [{'name': 'ping', 'status':
  'connected', 'source': 'dynamic'}]`. No built-in tool, no
  `mcp__claude_ai_*`. Control run WITHOUT `--strict-mcp-config` (capped at
  $0.0001): `tools` also had 8 `mcp__claude_ai_Claude_Docs__*` tools, and
  `mcp_servers` listed `claude.ai Claude Docs` (connected), `claude.ai
  Google Drive`, `claude.ai Gmail` and `claude.ai Google Calendar` (all
  `needs-auth`, `source: claudeai`). The flag is load-bearing: M1 must
  always pass it.
- **RESOLVED: `--max-budget-usd` stops a run on a subscription login**
  (`claude auth status`: `authMethod: claude.ai`, `subscriptionType: max`).
  It overshoots by up to one turn (section 5). Cost of the check-1 run:
  `total_cost_usd: 0.0286682`; usage `input_tokens: 4`,
  `cache_creation_input_tokens: 3391`, `cache_read_input_tokens: 3321`,
  `output_tokens: 43`; `modelUsage.claude-opus-5-5.costBasis: "list"` (an
  estimate on this login, not a bill).
- **RESOLVED: Codex cost, and the read-only sandbox.** On 0.163.0 (ChatGPT
  login; the owner's model `gpt-6.1-sol` from his config), `--json` gives
  token counts only (section 5). The ping prompt gave
  `{"type":"item.completed","item":{"type":"mcp_tool_call","server":"ping",
  "tool":"ping","result":{"content":[{"type":"text","text":"pong-1ccc898e"}]},
  "status":"completed"}}` and usage `input_tokens: 46157,
  cached_input_tokens: 42624, output_tokens: 111`. `--sandbox read-only`
  does not block MCP calls.
- **RESOLVED, with a finding: Codex adds its own connectors.** With only
  `-c mcp_servers.pixellab.enabled=false` (the key exists: `codex mcp list`
  then shows pixellab `disabled`), the tool-list prompt named more than 190
  tools: `exec_command`, `apply_patch`, `web__run`, `image_gen__imagegen`,
  `collaboration.spawn_agent`, and about 170 `mcp__codex_apps__*` tools
  (GitHub `create_commit`, `merge_pull_request`, `update_file`; Sites
  `deploy_site_version`; parental controls). With the `features.*=false`
  and `web_search="disabled"` settings of section 4, the list fell to
  `apply_patch`, `clock__curr_time`, `collaboration.*` (6), `functions.exec`,
  `functions.wait`, `functions.request_user_input(_async)`,
  `list_mcp_resources`, `list_mcp_resource_templates`, `read_mcp_resource`
  and `mcp__ping__ping`, and ping was still called (`pong-69149f23`, server
  log). `features.code_mode_host=false` breaks MCP ("Code Mode is
  unavailable because code-mode host is disabled"; the reply was "Ping
  unavailable"). The Codex lists are the model's own report: Codex has no
  command that prints the tool set without a model call (`codex debug
  prompt-input` leaves the tools out).
- **RESOLVED: pi keeps MCP tools with `--no-builtin-tools`.** Command:
  `PI_CODING_AGENT_DIR=<tmp with models.json + mcp.json> PI_OFFLINE=1 pi -p
  --no-session --mode json --no-builtin-tools --model lan-qwen/qwen3.8-27b`.
  pi's configured default is `kimi-coding/k2p6`
  (`~/.pi/agent/settings.json`); the check used the owner's LAN model
  (`lan-qwen/qwen3.8-27b` at 192.168.1.43, the engine HoldSpeak gives pi),
  at zero cost. pi shows the model one tool, `codemode` (JavaScript that
  calls the other tools); MCP tools are reached in it as
  `tools.mcp__ping__ping(...)`. The run: `tool_execution_start` `codemode`
  → nested `tool_execution_start` `mcp__ping__ping` (with
  `parentToolCallId`) → result `pong-b30566e5`; final text
  `pong-b30566e5`. JSON shape: one event per line; types `session` (`id`,
  `cwd`, `version: 3`), `agent_start`, `turn_start`,
  `message_start/update/end`, `tool_execution_start/update/end`
  (`toolName`, `args`, `result`, `isError`, `durationMs`), `turn_end`
  (`message` with `provider`, `model`, `usage`, `stopReason`;
  `toolResults`), `agent_end` (`messages`), `agent_settled` (`aborted`).
  The tool-list prompt answered "codemode (directly), mcp__ping__ping (via
  codemode)".
- **Still unknown:** whether Codex `apply_patch` or `functions.exec` can
  write under `--sandbox read-only` (expected: no; not run); whether Codex
  `collaboration.spawn_agent` still works with `features.multi_agent=false`
  (the model still listed it); whether pi's `codemode` JavaScript can reach
  the file system or the network by itself (its prompt says it "calls other
  tools"; not run).
- The `workbench_id` lock risk in section 3: read from code, not run.

[^people-ruling]: `holdspeak/mcp/palettes.py:52-56`; `holdspeak/services/conductor_launch.py:7-9`.
[^service-layer]: `holdspeak/mcp/server.py:3-18`; `holdspeak/web/routes/mcp_http.py:12-21`.
[^thread-rule]: `holdspeak/mcp/tool_authority.py:3-22`.
[^route]: `holdspeak/web/routes/mcp_http.py:129-138,249-277`.
[^queue]: `holdspeak/web/routes/mcp_http.py:285-310`; `holdspeak/mcp/long_tools.py:42-66`.
[^sidecar]: `holdspeak/mcp/server.py:125-157` (discovery), `:160-178` (token), `:191-213` (forward).
[^nohub]: `holdspeak/mcp/server.py:107-110,216-226`.
