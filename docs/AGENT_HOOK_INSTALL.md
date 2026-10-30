# Agent hook install

Agent hooks let Claude Code, Codex, and pi report their project, session,
work, wait, and end events to HoldSpeak. The records drive the Coder surface,
dictation targeting, and **Needs you** questions. Hooks are advisory. They do
not grant a coder access to Desk data or send a reply by themselves.

## What hooks give you

- the agent's real working directory and repository root;
- the session id, model, transcript path, and tmux pane when present;
- working, waiting, idle, or ended status;
- a bounded question when the agent asks for your input;
- optional project context from the repository's `.hs/` files.

Claude Code and Codex use their hook configuration files. pi has no separate
hook settings file. Its HoldSpeak extension rides each launched pi session.

## Install

1. Check that the HoldSpeak command the hook will run is available:

   ```sh
   which holdspeak
   holdspeak agent-hook latest
   ```

2. Install Claude Code and Codex hooks:

   ```sh
   holdspeak agent-hook install
   ```

   The command merges its entries into `~/.claude/settings.json` and
   `~/.codex/hooks.json`. It keeps foreign hooks and does not add duplicates.
   `CLAUDE_CONFIG_DIR` and `CODEX_HOME` change the resolved paths.

3. Start a new Claude Code or Codex session. Existing processes do not load a
   changed hook file.

The command also accepts `--agent claude` or `--agent codex`. `--settings-path`
needs one of those agents. `--agent pi` reports the extension state; it does
not write a settings file.

To remove only HoldSpeak's entries, run:

```sh
holdspeak agent-hook uninstall
```

## Capture mode

Capture mode is an explicit opt-in for the latest assistant text. Use it only
when local storage of that text is acceptable:

```sh
holdspeak agent-hook install --capture-messages
```

HoldSpeak stores bounded local session data in
`~/.config/holdspeak/agent_sessions.json`. The assistant text and prompt caps
are 4,096 characters. A question-shaped Stop, Notification, or Codex
PermissionRequest can set `awaiting_response`. The next prompt clears the
captured question. A pinned session is exempt from recent-age filtering.

Capture does not answer an agent. It only lets the Desk or an AIPI-compatible
device show the question so you can choose a reply.

## Install by hand

Print templates without changing an agent configuration:

```sh
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
holdspeak agent-hook templates --agent pi --capture-messages
```

Add the Claude `hooks` object to `~/.claude/settings.json`. Add the Codex
`hooks` object to `~/.codex/hooks.json`. pi uses the extension document that a
HoldSpeak coding launch supplies.

The rider events are:

| Agent | Events |
| --- | --- |
| Claude Code | `SessionStart`, `CwdChanged`, `UserPromptSubmit`, `Notification`, `PostToolUse`, `Stop`, `SessionEnd` |
| Codex | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `Stop`, `SessionEnd` |
| pi | Extension session start, prompt, tool result, agent end, and shutdown events |

Codex has no Claude-style `Notification` event. Its approval prompt is
`PermissionRequest`, and its end-of-turn `Stop` carries the last assistant
message. pi maps its extension events to the same session record.

## Verify

Open a project, start a new agent session, and send one prompt. Then run:

```sh
holdspeak agent-hook latest
holdspeak agent-hook latest --all
```

The JSON should include the agent, cwd, session id, hook event, lifecycle,
and repository when detected. With capture enabled, an agent question should
include `awaiting_response: true` and bounded `last_assistant_text`.

The Desk's **Automation hooks** view and `GET /api/dictation/agent-hooks`
report the hook templates and latest-session status. This is not the
voice-reply readiness contract. Read `GET /api/coders/status` for
`ready_for_agent_reply` and `blockers`. Live pane records appear in
`GET /api/coders/sessions`.

## Check readiness for voice replies

`GET /api/coders/status` reports whether a voice reply can reach a waiting
agent. Read `ready_for_agent_reply` and its `blockers` list. A ready status
requires a fresh waiting question, a connected AIPI-compatible device, an
enabled dictation pipeline, and text injection on the platform.

While a fresh Codex question waits, the dictation pipeline uses the
`codex_cli` target profile. For Claude it uses `claude_code`. The global target
setting does not change. With the pipeline off, voice typing inserts the raw
transcript.

Questions are fresh for 30 minutes unless the session is pinned. A voice
reply still needs your explicit send action.

## tmux delivery

Coder launches record `TMUX_PANE` when available. Desk steering then resolves
the pane identity and generation before it types. A missing or recycled pane
refuses delivery. See [Coder integration](CODER_INTEGRATION.md).

## Add project context

HoldSpeak reads optional project facts from `.hs/` in the repository, or from
the flat `.hs_context` file. Supported files include `instructions.md`,
`context.md`, `memory.md`, `workflows.md`, `issues.md`, `terms.md`,
`targets.md`, and `ignore`.

Example:

```md
# .hs/instructions.md
Rewrite rough dictation as a concise engineering request. Preserve filenames,
commands, and test names.
```

Inspect what the hook context loader sees:

```sh
holdspeak agent-hook context --project .
holdspeak agent-hook context --project . --format json
```

The context loader caps the complete rendered context at 64,000 bytes and one
file at 16,000 bytes. It redacts common secret patterns.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `holdspeak` is not found | Put the executable on a stable PATH, then install again. |
| No recent session | Install the hook and start a new agent session. |
| Wrong `cwd` | Send a prompt after the agent enters the intended project. |
| pi is missing hooks | Check the bundled HoldSpeak pi extension used by the launch. |
| `awaiting_response` is false | Enable capture for Claude or Codex, or check the agent's wait event. |
| AIPI says `No agent waiting` | Ask a new question and check it within the freshness window. |
| Captured text is stale | Submit a new prompt or clear the agent context route. |

## Safety

Capture stores bounded local text. Do not enable it on a shared machine unless
all users accept that local record. A hook never sends a reply by itself.

The Coder Gate is separate. It holds matched tool calls and can fail closed;
see [Gate](GATE.md).

## See also

- [Coder integration](CODER_INTEGRATION.md): launch, observe, and steer.
- [Dictation pipeline setup](DICTATION_PIPELINE_GUIDE.md): target routing.
- [The Dictation Copilot](DICTATION_COPILOT.md): voice context.
- [Security and privacy](SECURITY.md): local and provider boundaries.
