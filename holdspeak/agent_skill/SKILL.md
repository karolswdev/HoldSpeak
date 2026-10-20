---
name: holdspeak
description: Use the HoldSpeak desk brief and review flow for this work.
---

# HoldSpeak

Before work:

1. Identify how this session started.
   - For a HoldSpeak-launched task, check `HOLDSPEAK_AGENT_CREDENTIAL` first. If it is absent or empty, stop and report that this launch has no desk credential. Do not use an owner-started path for that task.
   - For an owner-started Claude or Codex session, use the Setup-installed HoldSpeak MCP connection. If it is unavailable, report that HoldSpeak desk access is unavailable and stop before desk calls.
2. Read the brief references with `project.get` and `memory.search` before you edit.
3. Keep the change in the brief. Ask the desk when the brief is not clear.

For review, use `agent.start_helper` and give the reviewer the changed paths and the focused checks.

When the work is complete, say `Done — <what changed>.` on one line.

Never write `Closes #N`.
