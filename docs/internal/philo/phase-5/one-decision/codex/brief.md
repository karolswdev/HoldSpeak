PHILO-5-01 Codex path proof. Use ONLY the MCP server named `holdspeak` for the HoldSpeak calls (no curl, no Python against the hub, no reading its database). Do these steps in order and report each result verbatim:

1. Call the MCP tool `desk.create` with arguments {"kind": "decisions", "data": {"title": "PHILO-5-01 Codex proof decision", "status": "accepted", "decision_markdown": "Decisions flow through one contract."}}. Report the returned id.
2. Call `desk.get` with {"kind": "decisions", "id": <that id>}. Report the title and status.
3. Restart the hub: run the shell command `touch /Users/karol/dev/tools/wt-philo-5-01/docs/internal/philo/phase-5/one-decision/codex/restart.request`, then poll every 2 seconds (at most 240 seconds) until the file `/Users/karol/dev/tools/wt-philo-5-01/docs/internal/philo/phase-5/one-decision/codex/restart.done` exists, and print its content.
4. Call `desk.get` again with the same id. Report the title and status.
5. Call `desk.list` with {"kind": "decisions"} and report the ids.

Finish with one JSON object: {"decision_id": ..., "read_before_restart": {...}, "restart": <the restart.done JSON>, "read_after_restart": {...}, "list_ids": [...], "mcp_errors": [every MCP error text you saw, or []]}.
