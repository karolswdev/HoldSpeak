# HS-23-05 Evidence — Reply Target Readiness Guard

**Date:** 2026-05-26.
**Story:** [story-05-reply-target-readiness-guard.md](./story-05-reply-target-readiness-guard.md).

## Live Finding

During hardware dogfood, AI PI allowed right-button reply capture while the
selected target was `Codex | holdspeak | no tmux` and GUI text injection was
unavailable. The device displayed a reply flow, but the answer had no delivery
path.

## Implementation Evidence

- `holdspeak/web_runtime.py` now checks selected agent deliverability before
  starting device voice capture.
- Tmux-backed targets remain deliverable even when GUI text insertion is
  unavailable.
- No-tmux targets are rejected when `TextTyper` is unavailable.
- Rejected targets send a short device status: `No reply target`.

## Validation

- `.venv/bin/python -m pytest tests/unit/test_web_runtime.py tests/unit/test_agent_context.py tests/unit/test_agent_device.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q`
- `scripts/aipi_test.sh -q`
- `git diff --check`

## Result

HS-23-05 closes the main confidence contradiction from live dogfood: AI PI no
longer invites the user to answer a target that HoldSpeak cannot write back to.
