# Spike: pi as a third coding-agent harness (LAN model)

Date: 2026-10-08. Owner's request. Report only: this spike changes no product code.
Rig: one isolated HOME (`mktemp -d`), hub from the main checkout at
`d02d2dd8c` on port 8791, LAN model `qwen3.8-27b` at `http://192.168.1.43:8080/v1`
(llama.cpp, 49152-token context). The HOME was removed at the end. Raw logs are
in `docs/internal/spikes/pi-harness/`. The logs contained no credential and no
owner token (checked with grep before commit).

## Verdict

**YES, pi can be the third harness, with five gaps that HoldSpeak must close.**
On the LAN model, pi called `project.list` and `desk.needs_you` through its
built-in MCP client. A pi extension sent a pi `bash` call to the real
`holdspeak gate hook`. The hub held the call. The owner's deny blocked it, and
pi gave the deny reason to the model. pi took a multi-line brief as one
bracketed paste in tmux. A second extension reported each turn end with the
last assistant text. `holdspeak agent-hook ingest` accepted that report and
classified it. The gaps: (1) `pi` is not in `GATE_AGENTS` or in the `--agent`
choices, (2) there is no launch profile, (3) there is no adapter that writes
pi's per-launch config, (4) there is no maintained pi extension (gate + rider),
and (5) the gate names pi's tools `bash`/`edit`/`write`, but the gate rules know
only `Bash`/`Edit`/`Write`. pi does not use the Responses `namespace` tool type
that stopped Codex (B49). It sends MCP tools as plain chat-completions functions,
and llama.cpp accepts them.

## Install facts

| Fact | Value |
|---|---|
| Package | `@earendil-works/pi-coding-agent` (the old name `@mariozechner/pi-coding-agent` 0.73.1 is deprecated: "please use @earendil-works/pi-coding-agent instead going forward") |
| Version tested | 1.1.0 (published 2026-10-07) |
| License | MIT |
| Source | `github.com/earendil-works/pi` |
| Binary | `pi` (`dist/bundle/cli.js`) |
| Runtime | Node >= 22.19.0 (tested on Node 22.21.0) |
| Install (isolated) | `npm install --prefix $H/prefix @earendil-works/pi-coding-agent@1.1.0` (121 packages, 5 s) |

### Model providers

Built-in providers include Anthropic, OpenAI, Google Gemini, Mistral, Groq, xAI,
OpenRouter, DeepSeek, Bedrock, Azure OpenAI, Vertex, and others (`docs/providers.md`).
It also has a llama.cpp router integration (`/login llama.cpp`, `LLAMA_BASE_URL`).
The LAN box runs in single-model mode, not router mode. For that reason, we used
an OpenAI-compatible endpoint in `models.json` (`docs/models.md`, "Configure a
compatible endpoint"):

```json
{ "providers": { "lan": {
    "baseUrl": "http://192.168.1.43:8080/v1",
    "api": "openai-completions",
    "apiKey": "$OPENAI_API_KEY",
    "models": [ { "id": "qwen3.8-27b", "contextWindow": 49152 } ] } } }
```

`pi --list-models qwen` listed `lan  qwen3.8-27b  49.2K`. The launch flag is
`--model lan/qwen3.8-27b`.

### Per-launch configuration (isolation)

- `PI_CODING_AGENT_DIR=<dir>` replaces `~/.pi/agent` (`docs/environment-variables.md`).
  That folder holds `models.json`, `mcp.json`, `settings.json`, `auth.json`,
  `trust.json` and the default `sessions/`. One folder per launch gives each
  launch its own config. The owner's `~/.pi` was not changed (mtime 2026-04-28).
- `--session-dir <dir>` (or `PI_CODING_AGENT_SESSION_DIR`) sets the transcript folder.
- `-e <file>` loads one extension file. `--no-extensions` stops discovery but
  explicit `-e` still loads.
- `PI_OFFLINE=1`, `PI_SKIP_VERSION_CHECK=1`, `PI_TELEMETRY=0` stop pi's own network
  calls (catalog refresh, version check, telemetry).
- `--no-context-files` stops AGENTS.md/CLAUDE.md loading. A launch into a HoldSpeak
  worktree probably wants them on.
- Project `.pi/mcp.json` and `.pi/extensions` load only after project trust
  (`docs/security.md`). Thus HoldSpeak must put its wiring in the per-launch
  user folder or in `-e` flags, not in the worktree.

## Question 1: MCP tools: YES

pi 1.1.0 has a built-in MCP client (stdio and streamable HTTP; `docs/mcp.md`).
Config in `$PI_CODING_AGENT_DIR/mcp.json`
(`pi-harness/config/mcp.json`):

```json
{ "mcpServers": { "holdspeak": {
    "url": "http://127.0.0.1:8791/api/mcp",
    "headers": { "Authorization": "Bearer ${HOLDSPEAK_AGENT_CREDENTIAL}" },
    "exposure": "hidden",
    "toolExposure": { "project.list": "direct", "desk.needs_you": "direct" } } } }
```

The `headers` shape is the same as the Claude document HoldSpeak writes
(`holdspeak/delivery/agent_mcp.py:50-57`). One difference: pi expands `${VAR}` in
`headers` and `env`, but not in `url`. With `"url": "${HOLDSPEAK_MCP_URL}"`, pi
stopped with `url must be an http or https URL`. The adapter must write the URL
as text.

Connection check (agent credential `pi:spike`, Reach enabled, curl `tools/list`
returned 250 tools first):

```
$ pi mcp list
holdspeak: connected, 250 tools (hidden, global)
  http://127.0.0.1:8791/api/mcp
  tools: desk.list, ... desk.needs_you [direct], ... project.list [direct], ...
```

Tool names in the model become `mcp__holdspeak__project_list` and
`mcp__holdspeak__desk_needs_you` (pi changes `.` to `_`).

Run 1, direct exposure (`pi-harness/q1-direct-exposure.jsonl`, 4.4 s):

```
$ pi --model lan/qwen3.8-27b --mode json --no-context-files -p \
  "Call the tool mcp__holdspeak__project_list, then call the tool mcp__holdspeak__desk_needs_you. ..."
tool_execution_start  mcp__holdspeak__project_list   args {}
tool_execution_start  mcp__holdspeak__desk_needs_you args {}
tool_execution_end    mcp__holdspeak__project_list   {"projects": []}   isError false, 9 ms
tool_execution_end    mcp__holdspeak__desk_needs_you {"arming": [], "blockers": [], "complete": false,
   "count": 0, ... "sourceErrors": {"assignments": "Owner access is required", ...}}  isError false
final text: "project_list: Returned zero projects ... desk_needs_you: Nothing currently needs you ..."
```

The model sent both calls in one assistant message (`stopReason: toolUse`,
`rawStopReason: tool_calls`). The `api` field is `openai-completions`.

Run 2, discovery with no tool named (`exposure: "deferred"`, all 250 tools behind
pi's `tool_search`; `pi-harness/q1-deferred-exposure.jsonl`, 34 s). Prompt: "Using
the HoldSpeak server, list my projects and tell me what needs me on the desk."
The model ran `tool_search` four times. It then called `desk_snapshot`,
`settings_get`, `desk_list` x2, `project_list` and `follow_through_board`. It
found `project.list` without help. It did not find `desk.needs_you`. It used
`desk.snapshot` and `follow_through.board` in its place. Thus a launch should
give the core tools (`desk.needs_you`, `project.*`, `agent.*`) `direct`
exposure and keep the rest deferred. 250 direct tools would also fill much of a
49k context.

## Question 2: The gate: YES (proved with one held and denied `echo`)

pi API: the extension event `tool_call` (`docs/extensions.md`, "Events and
concurrency": "`tool_call` can mutate input or block execution"). A handler
returns `{ block: true, reason }`. pi gives `reason` to the model as an error
tool result. Handlers are `async` and pi awaits them. A handler that throws
blocks the call ("A `tool_call` handler failure blocks the tool as a
fail-safe", `docs/extensions.md`). That matches the gate's fail-closed rule.
MCP calls go through the same pipeline ("Every MCP call passes through Pi's tool
pipeline", `docs/mcp.md`, "Permissions"). Thus the gate can also hold MCP tools.

Bridge (`pi-harness/extensions/holdspeak-gate.ts`, 40 lines): on `tool_call`
with `toolName === "bash"`, it builds a Claude-shaped PreToolUse payload
(`hook_event_name`, `tool_name: "Bash"`, `tool_input.command`, `tool_use_id`,
`session_id`, `cwd`). It pipes the payload to
`uv run --project <checkout> holdspeak gate hook --agent claude`
(`holdspeak/commands/gate.py:142`). It reads
`hookSpecificOutput.permissionDecisionReason`
(`holdspeak/coder_gate.py:390-401`). Empty output allows the call. A deny returns
`{ block: true, reason }`.

Rig: `holdspeak gate arm`, then `holdspeak gate allow --repo $H/proj`. The hook
used the launch's `HOLDSPEAK_AGENT_CREDENTIAL` (`holdspeak/coder_gate.py:278`).
The hub thus recorded the hold under `session_key: "pi:spike"`.

Run A, owner deny (`pi-harness/q2-gate-owner-deny.*`):

```
held proposal: {"id":"Qihl6YyRmePrZC8sek3CpBZORPFJHaHi","session_key":"pi:spike","tool":"Bash",
                "args_head":"{\"command\":\"echo hello-from-pi\"}", ...}
POST /api/gate/proposals/Qihl.../decide {"decision":"denied","reason":"spike: owner denied the echo"}
[gate] BLOCK after 21.4s: denied from the desk: spike: owner denied the echo. The owner denied
       this call. Do not try it again in a different form.
tool_execution_end bash isError true  "denied from the desk: spike: owner denied the echo. ..."
final text: "The command was refused — the desk owner denied the echo call ..., so I did not retry."
```

The echo did not run. No `hello-from-pi` output is in the log.

Run B, no decision (`pi-harness/q2-gate-expiry.*`). pi waited for the full
hold and did not time out the handler:

```
[gate] BLOCK after 240.2s: the hold expired with no decision: expired: no decision arrived before the hold ran out
```

240 s is the gate TTL (`DEFAULT_TTL_SECONDS`, `holdspeak/coder_gate.py:55`).
The docs name no time limit for a `tool_call` handler, and 240 s passed. The
300 s Claude/Codex hook limit (`HOOK_TIMEOUT_SECONDS`, `coder_gate.py:56`) is
not needed in pi: the extension owns the wait.

Findings for the adapter:

- When pi is killed in a hold, the hook child stays alive until the hold ends.
  In Run A, the orphan hook of Run B wrote `BrokenPipeError` to stderr. The hub
  still showed the old hold. A launch stop must kill the process group.
- After the expiry deny in Run B, the model tried the same `echo` again (a
  second hold). The owner-deny text ("Do not try it again") stopped a retry in
  Run A. The expiry text does not have that sentence.
- pi's tool names are lower case: `bash`, `edit`, `write`, `read`. The gate
  rules know `Bash` and `EDIT_TOOLS = {"Edit", "Write", "MultiEdit",
  "NotebookEdit"}` (`holdspeak/tool_gate_rules.py:214`). The spike bridge mapped
  `bash` to `Bash`. Edit and write were not tested.

## Question 3: Brief in, turn end out: YES

Brief in. pi ran as a full-screen TUI in a tmux session (tmux 3.6b, socket
in `$H/tmux`). The spike used the same steps as `send_text_to_pane`
(`holdspeak/tmux_transport.py:58-98`): `tmux load-buffer`, then
`tmux paste-buffer -p -r -d`, then `send-keys -l $'\r'`. A three-line brief
arrived as one prompt, and pi ran it as one message
(`pi-harness/q3-tmux-pane.txt`). pi shows a warning at start: "tmux
extended-keys is off. Modified Enter keys may not work". Plain Enter worked.
pi's `docs/tmux.md` recommends `set -g extended-keys on` for the pane's
server.

Turn end out: three pi mechanisms. All three were seen or read:

1. **Extension event `agent_end`** (used in the spike;
   `pi-harness/extensions/turn-end.ts`). It fires when the agent stops and
   waits for input. `event.messages` holds the turn. `ctx.sessionManager`
   gives the session id and file. The spike wrote one Stop-shaped line per
   turn (`pi-harness/q3-turn-ends.jsonl`):

   ```
   {"hook_event_name":"Stop","session_id":"01a11d46-...","transcript_path":".../sessions/2026-10-08T20-48-24-771Z_01a11d46-....jsonl",
    "cwd":".../proj","stop_reason":"stop","last_assistant_message":"There are 0 projects. DONE"}
   {"hook_event_name":"Stop", ... "last_assistant_message":"Still 0 projects. What name should the new project have?\n</think>\n\nWhat should the new project be named?"}
   ```

   `turn_end` (each model reply) and `agent_before_settle` events also exist.
2. **Session transcript**: JSONL at
   `<session-dir>/<timestamp>_<session-id>.jsonl` (`docs/session-format.md`).
   Each entry is `{"type":"message", "message":{"role":"assistant", "content":[...],
   "stopReason":"stop"}}` (`pi-harness/q3-session-transcript.jsonl`). The format
   is pi's own, not Claude's.
3. **JSON and RPC modes**: `--mode json` streams `agent_start`, `turn_end`,
   `tool_execution_*` and `agent_end` events on stdout. `--mode rpc` is a
   long-lived JSONL command/event protocol (`docs/rpc.md`). These modes do not
   use the tmux pane.

Classification. The two turn ends went through HoldSpeak's own functions
(`holdspeak/agent_context/models.py:295`, `:338`):

```
'There are 0 projects. DONE'                     asks= False problem= False
'Still 0 projects. What name should the ...?'    asks= True  problem= False
```

The second line, piped to `holdspeak agent-hook ingest --agent claude
--print-summary`, gave `"lifecycle": "waiting"`, `"awaiting_response": true`,
`"question": "Still 0 projects. What name should ..."`. Thus the rider accepts
the payload as it is. `tmux_pane` was `null` because the ingest ran outside the
pane. Run from the extension inside the pane, it inherits `TMUX_PANE`. That was
not verified.

Model note (not a pi defect): Qwen on llama.cpp let one `</think>` into the
answer text. The classifier still read the question correctly.

## What HoldSpeak would need to add

| # | Piece | What | Beside |
|---|---|---|---|
| 1 | Agent name | Add `"pi"` to `GATE_AGENTS` and to the `--agent` choices of `gate hook` and `agent-hook ingest`. Sessions become `pi:<session_id>`. | `holdspeak/coder_gate.py:263`, `holdspeak/commands/gate.py:38`, `holdspeak/commands/agent_hook.py:200` |
| 2 | Launch profile | A `pi-default` profile (`executable: "pi"`, model slot `--model lan/qwen3.8-27b`), and `"pi"` in `KNOWN_EXECUTABLES`. | `holdspeak/delivery/factory_launch.py:66`, `:105-131` |
| 3 | Launch adapter | Per launch: make `PI_CODING_AGENT_DIR` with `models.json` (the placement's endpoint) and `mcp.json` (literal hub URL, `${HOLDSPEAK_AGENT_CREDENTIAL}` header, core tools `direct`). Set `--session-dir`, `PI_OFFLINE=1`, `PI_TELEMETRY=0`, and `-e <holdspeak-pi.ts>`. Kill the process group on stop (orphan hook finding). | `holdspeak/delivery/agent_mcp.py` (a `pi_mcp_document` beside `claude_mcp_document`, `:50`), `holdspeak/delivery/factory_launch.py` |
| 4 | Gate hook | One maintained extension, `holdspeak-pi.ts`. Its `tool_call` handler pipes a PreToolUse payload to `holdspeak gate hook --agent pi` and maps `bash` to `Bash`, `edit` to `Edit` and `write` to `Write`. A throw blocks the call. Ship it as a package file and pass its path with `-e`. | new `holdspeak/agent_context/pi_extension/holdspeak-pi.ts`; payload mapping beside `holdspeak/coder_gate.py:950` (`codex_spawn_hooks`) |
| 5 | Turn-end reader | In the same extension: `session_start`, `agent_end` (Stop with `last_assistant_message`), `tool_result` (PostToolUse heartbeat) and `session_shutdown`. Each pipes to `holdspeak agent-hook ingest --agent pi`. A pi entry beside the Claude and Codex templates. | `holdspeak/agent_context/hooks.py:238` (`codex_hook_template`) |
| 6 | Capture (optional) | `--capture-messages` reads a Claude transcript. pi's transcript format is different. A small pi reader, or `agent_end` text only. | `holdspeak/agent_context/` |

Items 4 and 5 are one file. pi also lets an extension register the MCP server
(`pi.registerMcpServer`, `docs/mcp.md`). Thus one extension can carry all of
items 3 to 5 if HoldSpeak prefers code to config files.

## Unknown (not verified)

- The edit and write tools through the gate. Only `bash` was tested.
- Rider ingest from inside the pi pane (`TMUX_PANE` pickup). The ingest was
  run by hand outside the pane.
- One `pi -p` run stopped with no output for 7 minutes. A retry with stdin
  from `/dev/null` finished in 34 s. The first `-p` run worked without
  `/dev/null`. The cause was not found. Print-mode launches should close stdin.
- Long coding work on `qwen3.8-27b` through pi (more than one or two tool
  turns). The spike tested the harness, not the model's coding quality.
- The old `pi-mcp-adapter` extension (5.1.0). It is not needed: the built-in
  client did the work.

## Raw logs

`docs/internal/spikes/pi-harness/`: `q1-direct-exposure.jsonl`,
`q1-deferred-exposure.jsonl`, `q2-gate-owner-deny.{jsonl,stderr.txt,decisions.txt}`,
`q2-gate-expiry.{jsonl,stderr.txt}`, `q3-tmux-pane.txt`, `q3-turn-ends.jsonl`,
`q3-session-transcript.jsonl`, `extensions/holdspeak-gate.ts`,
`extensions/turn-end.ts`, `config/models.json`, `config/mcp.json`. The JSON
event logs do not include the token-stream `message_update` events.
