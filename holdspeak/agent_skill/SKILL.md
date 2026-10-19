---
name: holdspeak
description: Use the HoldSpeak desk brief and review flow for this work.
---

# HoldSpeak

Before work:

1. Check the launch credential first. If `HOLDSPEAK_AGENT_CREDENTIAL` is absent or empty, stop and report that this launch has no desk credential.
2. Read the brief references with `project.get` and `memory.search` before you edit.
3. Keep the change in the brief. Ask the desk when the brief is not clear.

For review, use `agent.start_helper` and give the reviewer the changed paths and the focused checks.

When the work is complete, say `Done — <what changed>.` on one line.

Never write `Closes #N`.
