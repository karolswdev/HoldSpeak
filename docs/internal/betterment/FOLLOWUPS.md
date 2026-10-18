# Follow-ups found while building

Each item names the slice or recipe that takes it. Remove an item when the
PR that fixes it merges.

| Found in | Follow-up | Goes to |
|---|---|---|
| Q0 (#1260) | An engine added through the Model Library gets a 16,384-token context by default (`model_library_service.py:526`), although the LAN engine serves 49,152. The route also counts one token per byte (`inference_adoption_service.py:148-157`). Tools barely fit. Read the engine's real context size when Check runs, and count tokens properly. | Engines E3 |
| Q0 (#1260) | Interview's answer-only pass puts a system message after the user message, which Qwen's template rejects. | Asking Q4, or a small fix |
| Q0 (#1260) | "Engine not reachable" is shown as "No engine for answers" (`ask_service.py` reason mapping). | Asking Q1 |
| C2 (#1258) | Memory pages (what we decided, what is open) are not filtered by date, so a re-summary of an old meeting can still read later facts through a page. | Capture C6 |
| A0 (#1256) | Choosing Manual still pauses event starts and idle work; an existing test asserts it. The When editor replaces this control. | Automations A4 |
| S1 (#1259) | A person is not a desk object, so a person has no Object menu. | Shell S4 or Daily D6 |
| S1 (#1259) | The Builder tools switch is saved in the browser, not on the hub, so an agent cannot read or set it. | Shell S5 |
| S0 (#1257) | Search for "automation" still finds nothing. | Shell S5 (Automations A1 adds the alias) |
| ST0 (#1261) | Rest of ST0 not built: one Rhythm quiet-hours store (do it once, in ST1), Setup rows in words (the yellow Check chip), Other devices saved (`mcp_http.py:392-404` keeps it in memory only). | Setup ST1 |
| ST0 (#1261) | The fix is in the Engines summary only. The runtime speech route still falls back to the default last; on a desk without speech's own capability row, a route plan could still reach the chat server. Check it. | Setup ST1 / Engines E5 |
| S0/S1 | Something emptied a worktree's `web/node_modules` while its quick check waited for the lock. Cause unknown. | Watch |
