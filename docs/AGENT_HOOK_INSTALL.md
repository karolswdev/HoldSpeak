# Claude/Codex Agent Hook Install

Agent hooks let Claude Code and Codex report their own `cwd`, session id,
transcript path, model, tool activity, and latest assistant question to
HoldSpeak. This is more reliable than asking the operating system which
terminal window is active.

Install hooks once per agent environment. They then work across projects.
Per-project `.hs/` files are optional context that improve rewrites after
HoldSpeak knows which project the agent is using.

## What Hooks Enable

- Project detection from the agent's real working directory.
- Target-aware dictation for Codex and Claude.
- Assistant-question detection when message capture is enabled.
- AIPI companion queries:
  - `agent_status`
  - `agent_question`
- Better dry-run/readiness diagnostics in `/dictation`.

## Prerequisites

1. Install HoldSpeak.

   ```bash
   uv pip install -e .
   ```

2. Confirm the agent can run `holdspeak`.

   ```bash
   which holdspeak
   holdspeak agent-hook latest
   ```

If `which holdspeak` prints nothing, install HoldSpeak into a stable PATH
using your preferred tool, or create a stable symlink to this checkout's
entry point. Hooks run from the agent process, so shell aliases are not a
reliable install path.

## Choose Capture Mode

Use the non-capture template when you only want project/session detection:

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex
```

Use capture mode when you want HoldSpeak and AIPI to know when an agent is
waiting for your reply:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

Capture mode stores a bounded local snippet of the latest assistant message:

- max 4 KB;
- stored in `~/.config/holdspeak/agent_sessions.json`;
- marked `awaiting_response` only when the message looks like a question;
- cleared on the next submitted user prompt;
- manually clearable from `/dictation`.

Do not enable capture mode on shared machines unless everyone using the
machine understands the local storage behavior.

## Install For Claude Code

1. Generate the Claude template.

   ```bash
   holdspeak agent-hook templates --agent claude --capture-messages
   ```

2. Open Claude Code's hook/settings configuration.

3. Paste the generated `claude` object into the hooks section expected by
   Claude Code.

4. Restart or reload Claude Code if required by your Claude Code version.

The generated Claude hooks listen for:

- `SessionStart`
- `CwdChanged`
- `UserPromptSubmit`
- `Stop`

`Stop` is the event that lets HoldSpeak capture the latest assistant question
when `--capture-messages` is enabled.

## Install For Codex

1. Generate the Codex template.

   ```bash
   holdspeak agent-hook templates --agent codex --capture-messages
   ```

2. Open Codex's hook/settings configuration.

3. Paste the generated `codex` object into the hooks section expected by
   Codex.

4. Restart or reload Codex if required by your Codex version.

The generated Codex hooks listen for:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`

`Stop` is the event that lets HoldSpeak capture the latest assistant question
when `--capture-messages` is enabled.

## Verify Hook Ingestion

Open any project in Claude Code or Codex and send a prompt. Then run:

```bash
holdspeak agent-hook latest
```

Expected fields:

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

If you enabled capture mode, ask the agent a question or wait for the agent to
ask you one. Then run:

```bash
holdspeak agent-hook latest
```

Look for:

```json
{
  "awaiting_response": true,
  "last_assistant_text": "The tests pass. Should I run the full suite now?"
}
```

You can also open:

```text
/dictation -> Agent Hooks
```

The page shows recent hook status, registry path, and whether a captured
agent question is waiting.

## Verify From AIPI

With HoldSpeak running and an AIPI-compatible device connected, the device can
send:

```json
{"type": "query", "name": "agent_status", "at": 1}
```

Expected response when an agent is waiting:

```json
{
  "type": "status",
  "text": "Codex waiting in HoldSpeak: The tests pass. Should I run the full suite now?",
  "ttl_ms": 7000
}
```

Question-only variant:

```json
{"type": "query", "name": "agent_question", "at": 2}
```

Expected response when no fresh question is captured:

```json
{"type": "status", "text": "No agent waiting", "ttl_ms": 3000}
```

## Voice Reply Requirements

For AIPI voice replies to be rewritten as Codex/Claude responses, enable the
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

When a fresh captured Codex question is waiting, device-originated voice
typing forces the `codex_cli` target profile for that utterance. When a fresh
Claude question is waiting, it forces `claude_code`. This does not mutate your
global target override.

If the dictation pipeline is disabled or unavailable, AIPI voice typing still
uses the existing raw transcript insertion path.

## Add Project Context

Project context is optional but recommended. In each repo, create:

```text
.hs/
  instructions.md
  context.md
  workflows.md
  targets.md
  ignore
```

Minimal example:

```md
# .hs/instructions.md
When dictating into Codex or Claude, rewrite rough speech into a concise
engineering request. Preserve filenames, commands, and test names.
```

```md
# .hs/workflows.md
Run focused tests with `.venv/bin/pytest <path>`.
Run web builds with `cd web && npm run build`.
```

After adding `.hs/`, open:

```text
/dictation -> Project Context
```

Confirm HoldSpeak sees the expected project root and context files.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `holdspeak` not found from hook | Hook process PATH does not include HoldSpeak | Use an absolute executable path in the generated template or install HoldSpeak into a stable PATH |
| `holdspeak agent-hook latest` says no recent session | Hook not installed, not firing, or agent not reloaded | Regenerate template, re-paste config, restart the agent |
| `cwd` is wrong | Agent hook fired before changing project | Trigger a new prompt or cwd-change event inside the target project |
| `awaiting_response` is always false | Capture mode is not enabled or assistant did not ask a question | Regenerate with `--capture-messages` and test with a direct question |
| AIPI shows `No agent waiting` | No fresh captured question within HoldSpeak's recency window | Ask the agent a question and wait for a captured `Stop` event |
| Captured text is stale | Last user prompt did not clear the capture | Use **Clear** in `/dictation` or submit a new prompt through the agent |

## Safety Model

- Hooks are advisory context. Basic dictation still works without them.
- HoldSpeak does not silently edit Claude/Codex settings.
- Capture mode stores bounded local text only.
- Captured assistant text is used to shape user-approved dictation, not to
  send autonomous replies.
- AIPI can display/query waiting-agent state, but voice replies require an
  explicit user action.
