# Evidence — HS-22-05 tmux Agent Reply Transport

Date: 2026-05-24

## Scope Completed

- Extended `AgentSession` with optional tmux metadata:
  - `tmux_pane`
  - `tmux_session`
  - `tmux_window`
  - `tmux_pane_index`
  - `tmux_pane_current_path`
- Hook ingest captures `TMUX_PANE` from the hook process environment and
  preserves the previous pane across later events that lack tmux env.
- Added `holdspeak/tmux_transport.py` for literal tmux delivery:

```text
tmux send-keys -t <pane> -l <reply text>
tmux send-keys -t <pane> Enter
```

- Web runtime now prefers tmux delivery for device-originated agent replies when
  the waiting session has `tmux_pane`.
- Existing GUI `TextTyper` path remains the fallback.

## Validation

```text
.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_tmux_transport.py tests/unit/test_web_runtime.py tests/unit/test_typer.py -q
43 passed in 0.56s

git diff --check
passed
```

## Live Dogfood

Verified against Claude running inside tmux over the user's terminal workflow.

Hook state after launching Claude in tmux:

```text
agent: claude
session_id: dd4e9f15-4225-4e0e-810d-ad13186a0ac9
tmux_pane: %1
tmux_session: 1
tmux_window: 0
tmux_pane_index: 0
tmux_pane_current_path: /home/karol/dev/HoldSpeak
```

Bridge/runtime evidence:

```text
2026-05-25T05:16:09Z update_middle.ok "Claude waiting: Got it — no tool..."
2026-05-25T05:16:16Z device.voice_assistant.start
2026-05-25T05:16:17Z update_middle.ok "Replying to Claude"
2026-05-25T05:16:19Z ws.status.recv "I want to story me"

2026-05-25T05:17:16Z device.voice_assistant.start
2026-05-25T05:17:17Z update_middle.ok "Replying to Claude"
2026-05-25T05:17:22Z ws.status.recv "Sorry about cracking eggs."

2026-05-25T05:18:03Z device.voice_assistant.start
2026-05-25T05:18:07Z ws.status.recv "Do you speak any other languages?"
```

User confirmed the answer landed and submitted in Claude via tmux, including
over SSH, without needing GUI focus or X11 text injection.
