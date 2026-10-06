# Agent hook install

Agent hooks let Claude Code and Codex report their own working directory,
session id, transcript path, tool activity and latest assistant question to
HoldSpeak. This is more reliable than asking the operating system which
terminal window is active.

Install the hooks once for each agent. They then work in every project.

## What hooks give you

- Project detection from the agent's real working directory.
- Target-aware dictation for Codex and Claude.
- Detection of a question that an assistant asks you, when capture is on.
- Live coder state on the Desk: working, waiting on you, idle or ended.
- The AIPI queries `agent_status` and `agent_question`.

## Install

1. Install HoldSpeak, and confirm that the agent can run it:

   ```bash
   which holdspeak
   holdspeak agent-hook latest
   ```

   The hook runs from the agent process. A shell alias does not work. If
   `which holdspeak` prints nothing, put HoldSpeak on a stable PATH.

2. Install the hooks:

   ```bash
   holdspeak agent-hook install
   ```

   This merges the HoldSpeak hooks into `~/.claude/settings.json` and
   `~/.codex/hooks.json`. It keeps your other hooks. A second run does not
   add duplicates.

3. Start a new Claude Code or Codex session. Hooks do not apply to a
   session that already runs.

Options for `install` and `uninstall`:

| Option | Effect |
|---|---|
| `--agent claude`, `--agent codex` | Change one agent. The default is `all`. |
| `--capture-messages` (`install` only) | Turn on capture mode. See below. |
| `--settings-path PATH` | Write to another settings file. Needs one `--agent`. |

To remove the hooks, run:

```bash
holdspeak agent-hook uninstall
```

Uninstall removes only the HoldSpeak entries. HoldSpeak never edits your
agent settings except when you run `install` or `uninstall`.

## Capture mode

Capture mode stores a short piece of the latest assistant message. It lets
HoldSpeak know when an agent waits for your reply. Add
`--capture-messages` to `install`.

- HoldSpeak keeps at most 4,096 characters of text.
- It stores the text in `~/.config/holdspeak/agent_sessions.json`.
- It marks the session `awaiting_response` only when the message looks like
  a question.
- The next prompt that you submit clears the text.
- `POST /api/dictation/agent-context/clear` also clears it.

Do not turn on capture mode on a shared machine unless every user accepts
this local storage.

## Install by hand

Print a template and paste it into the agent configuration:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

Omit `--capture-messages` for project and session detection only.

For Claude Code, paste the `hooks` object into the hooks section of
`~/.claude/settings.json`.

For Codex, write the `hooks` object to `~/.codex/hooks.json`.

### Hook events

| Agent | Events |
|---|---|
| Claude Code | `SessionStart`, `CwdChanged`, `UserPromptSubmit`, `Notification`, `PostToolUse` (matcher: Bash, Edit, Write, Task), `Stop`, `SessionEnd` |
| Codex | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse` (matcher: Bash, apply_patch, Edit, Write), `Notification`, `Stop`, `SessionEnd` |

`Stop` lets HoldSpeak capture the latest assistant question. `Notification`
carries a blocking ask, such as a permission prompt. `PostToolUse` is the
working signal. `SessionEnd` marks the session ended. A session that stops
reporting decays to idle after 30 minutes and to ended after 4 hours.

## Verify

Open a project in Claude Code or Codex and send a prompt. Then run:

```bash
holdspeak agent-hook latest
```

The output shows the latest session:

```json
{
  "agent": "codex",
  "cwd": "/path/to/project",
  "repo_root": "/path/to/project",
  "session_id": "...",
  "hook_event_name": "...",
  "awaiting_response": false
}
```

Use `--agent` to filter, `--all` to list every session, and
`--max-age-seconds` to change the age limit (default 1800).

With capture on, ask the agent a question. Run the command again. Look for
`"awaiting_response": true` and the text in `last_assistant_text`.

In the Speak window, **Automation hooks** shows which agents have hooks
set. The `GET /api/dictation/agent-hooks` route returns the same data.

The live sessions also appear at `GET /api/coders/sessions`.

## Check readiness for voice replies

Open `/api/coders/status` while HoldSpeak runs:

```json
{
  "ready_for_agent_reply": true,
  "blockers": [],
  "devices": {"count": 1, "query_names": ["agent_question", "agent_status"]},
  "agent": {"awaiting_response": true},
  "dictation": {"pipeline_enabled": true},
  "runtime": {"text_injection_enabled": true}
}
```

When `ready_for_agent_reply` is `false`, `blockers` names the missing
piece:

| Blocker | Fix |
|---|---|
| `no_device_connected` | Connect an AIPI-compatible device. |
| `no_agent_waiting` | Ask the agent a question with capture on. |
| `dictation_pipeline_disabled` | Turn on the dictation pipeline. |
| `text_injection_unavailable` | Fix text injection for your platform. |
| `text_injection_status_unknown` | Start the HoldSpeak runtime. |

## Reply from an AIPI device

A connected device can send these queries:

```json
{"type": "query", "name": "agent_status", "at": 1}
{"type": "query", "name": "agent_question", "at": 2}
```

When an agent waits, the reply is a status message:

```json
{
  "type": "status",
  "text": "Codex waiting in HoldSpeak: The tests pass. Should I run the full suite now?",
  "ttl_ms": 7000
}
```

When no fresh question exists, the text is `No agent waiting`. A question
is fresh for 120 seconds.

To rewrite a voice reply as a Codex or Claude request, turn on the
dictation pipeline:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["project-rewriter"],
      "target_profile_override": "auto"
    }
  }
}
```

While a fresh Codex question waits, device voice typing uses the
`codex_cli` target profile for that utterance. For Claude, it uses
`claude_code`. Your global target setting does not change. With the
pipeline off, voice typing inserts the raw transcript.

### tmux delivery

When the agent runs in tmux, the hook inherits `TMUX_PANE`, and HoldSpeak
records the pane on the session. A voice reply then goes to that pane
with `tmux send-keys`, so the agent does not need the focused window. If
no pane exists or tmux fails, HoldSpeak types the text instead. A voice
reply always needs an explicit action from you. To steer a pane from the
Desk, see [Coder integration](CODER_INTEGRATION.md).

For AIPI bridge work, run the web runtime on the port that the bridge
uses:

```bash
HOLDSPEAK_WEB_PORT=34999 holdspeak web --no-open
```

## Add project context

Project context is optional. HoldSpeak finds the project root from a
`.hs/` folder, a `.hs_context` file, `.git` or `.holdspeak`. In a repo,
create:

```text
.hs/
  instructions.md
  context.md
  memory.md
  workflows.md
  issues.md
  terms.md
  targets.md
  ignore
```

Each file is optional. A flat file such as `.hs_context` also works.

For example:

```md
# .hs/instructions.md
When dictating into Codex or Claude, rewrite rough speech into a concise
engineering request. Preserve filenames, commands, and test names.
```

Check what HoldSpeak reads:

```bash
holdspeak agent-hook context --project .
```

Add `--format json` for JSON output.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `holdspeak` not found from a hook | The hook PATH lacks HoldSpeak | Put HoldSpeak on a stable PATH, then run `install` again |
| `latest` shows no recent session | Hooks not installed, or the agent is not restarted | Run `install` and start a new session |
| `cwd` is wrong | The hook fired before the agent changed project | Send a new prompt in the target project |
| `awaiting_response` is always false | Capture is off, or the agent asked no question | Run `install --capture-messages`, then ask a direct question |
| AIPI shows `No agent waiting` | No captured question in the last 120 seconds | Ask a question and wait for the `Stop` event |
| Captured text is stale | No new prompt cleared it | Submit a new prompt, or clear it with the clear route |

## Safety

- Hooks are advisory. Dictation works without them.
- Capture mode stores bounded local text only.
- HoldSpeak uses captured text to shape dictation that you approve. It
  never sends a reply on its own.
- A hook that holds risky tool calls is a different feature. See
  [Gate](GATE.md).

## See also

- [Dictation pipeline setup](DICTATION_PIPELINE_GUIDE.md)
- [The Dictation Copilot](DICTATION_COPILOT.md)
- [Security and privacy](SECURITY.md)
