# HS-23-02 Evidence — Multi-Session Identity Model

**Date:** 2026-05-26.
**Story:** [story-02-multi-session-identity.md](./story-02-multi-session-identity.md).
**Result:** done.

## Identity Rules

HoldSpeak now builds one structured identity payload for the active waiting
agent session and exposes it through `/api/companion/status` under
`agent.identity`.

Compact display label:

```text
<Agent> | <Project> | <tmux-session>:<window>.<pane>
```

Examples:

```text
Codex | HoldSpeak | work:2.1
Claude | HoldSpeak | work:2.1
Codex | HoldSpeak | no tmux
```

Rules:

- `agent_label` is normalized to `Codex`, `Claude`, or `Agent`.
- `project_label` prefers hook-provided `project_name`, then repo root name,
  then cwd name.
- `tmux_label` prefers `tmux_session`, `tmux_window`, and `tmux_pane_index`;
  otherwise it falls back to the raw `tmux_pane`.
- Missing tmux metadata is displayed as `no tmux` in the compact label.
- `target_transport=tmux` and `target_confidence=high` when a tmux pane is
  available.
- `target_transport=text_injection` and `target_confidence=medium` when no tmux
  pane exists but runtime text injection is enabled.
- `target_transport=unavailable` or `unknown` and `target_confidence=low` when
  no reliable reply target is known.

## Implementation

- `holdspeak/agent_device.py` adds `build_agent_identity_payload(...)`.
- `holdspeak/web_server.py` includes the identity payload, target confidence,
  and target transport in `/api/companion/status`.
- `aipi-lite/bridge/companion_status.py` prefers the server-provided compact
  identity label before deriving a fallback from raw session fields.
- Tests cover high-confidence tmux identity, visible no-tmux degradation,
  server payload shape, and bridge consumption of the structured identity.

## Validation

```text
.venv/bin/python -m pytest tests/unit/test_agent_device.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
12 passed in 0.70s

aipi-lite/.venv/bin/python -m pytest aipi-lite/tests/test_companion_status.py -q
11 passed in 0.21s

scripts/aipi_test.sh -q
199 passed in 7.56s

.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_web_runtime.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
39 passed in 0.68s
```

Hardware dogfood was intentionally deferred because AI PI is offline for this
slice. HS-23-03 can use this data contract for browse/preview controls when
the device is back online.
