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

```
claude -p --output-format json --no-session-persistence \
  --strict-mcp-config --mcp-config <0600 file from claude_mcp_document()> \
  --tools "" --allowedTools mcp__holdspeak --permission-prompts none \
  [--model M] [--max-budget-usd N]

codex exec --ephemeral --sandbox read-only --skip-git-repo-check -C <tmp> --json \
  -c mcp_servers.holdspeak.url="<hub>/api/mcp" \
  -c mcp_servers.holdspeak.bearer_token_env_var="HOLDSPEAK_AGENT_CREDENTIAL" \
  -c mcp_servers.holdspeak.default_tools_approval_mode="approve" \
  [-m M] -

PI_CODING_AGENT_DIR=<launch folder with mcp.json> \
  pi -p --no-session --mode json --no-builtin-tools --model lan/<model>
```

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
  server. A plain `codex exec` loads it too. `--ignore-user-config` drops it,
  but also drops his Codex model and provider choices.
- Claude Code tool names use underscores: `mcp__holdspeak__channel_send`
  for `channel.send` (`agent_context/hooks.py:290-291`).
- `--tools ""` is documented as "the built-in set". That the HoldSpeak MCP
  tools stay available with it is **unverified** (see Unknown).

---

## 5. Cost reporting

| Question | Answer | Evidence |
|---|---|---|
| Does `claude -p --output-format json` report the cost? | **Yes.** The result has `total_cost_usd`, `usage` (input, output, cache read, cache creation, thinking tokens), `modelUsage` per model (with `costUSD`), `num_turns`, `duration_ms`, `is_error`, `subtype`, and `permission_denials`. | A recorded result in the tree: `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/story-03-check-response-astra-invoked-claude.json:5-10` (2026-09-24, an older CLI version) |
| Is that the money he pays? | **Not always.** The same result says `"costBasis": "list"`: the figure is computed at list price. On a subscription login, it is an estimate, not a bill. | same file, `modelUsage` |
| Does `--max-budget-usd` exist? | **Yes**, in 2.1.302: "Maximum dollar amount to spend on API calls (only works with --print)". | `claude --help` |
| Does it apply to a subscription login? | **Unverified.** The help says "API calls". Most likely it stops on the same list-price estimate, whatever the login, but this was not run. | — |
| Codex | No budget flag in `codex exec --help`. `--json` prints events; whether a dollar cost or only token counts are in them is **unverified** on 0.161. | `codex exec --help` |
| pi | `--mode json` exists. Cost fields **unknown**. | `pi --help` |

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

- Whether `claude -p --tools ""` keeps the `mcp__holdspeak__*` tools. The
  help names only built-in tools. A one-prompt test settles it. If it does
  not, use `--disallowedTools` on the built-ins (Bash, Edit, Write, WebFetch,
  WebSearch) instead.
- Whether `--strict-mcp-config` also drops the claude.ai connectors tied to
  the login (Gmail, Drive, Calendar appear in this session). If it does not,
  an automation agent could reach Gmail. Check this before shipping.
- Whether `--max-budget-usd` stops a run on a subscription login.
- What `codex exec --json` reports about cost on 0.161, and whether
  `--sandbox read-only` affects the HTTP MCP server (most likely not; the
  sandbox is for shell commands).
- Whether pi's `--no-builtin-tools` keeps MCP tools, and what `--mode json`
  reports.
- The `workbench_id` lock risk in section 3: read from code, not run.

[^people-ruling]: `holdspeak/mcp/palettes.py:52-56`; `holdspeak/services/conductor_launch.py:7-9`.
[^service-layer]: `holdspeak/mcp/server.py:3-18`; `holdspeak/web/routes/mcp_http.py:12-21`.
[^thread-rule]: `holdspeak/mcp/tool_authority.py:3-22`.
[^route]: `holdspeak/web/routes/mcp_http.py:129-138,249-277`.
[^queue]: `holdspeak/web/routes/mcp_http.py:285-310`; `holdspeak/mcp/long_tools.py:42-66`.
[^sidecar]: `holdspeak/mcp/server.py:125-157` (discovery), `:160-178` (token), `:191-213` (forward).
[^nohub]: `holdspeak/mcp/server.py:107-110,216-226`.
