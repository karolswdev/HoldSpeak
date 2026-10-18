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
| E1 (#1273) | `CliEngine.cancel()` exists but nothing in the kernel calls it; an owner cancel waits for the timeout. | Engines E5 / Automations A3 (cancel) |
| E1 (#1273) | A timed-out CLI is retried once before the fallback (two killed attempts). Consider no retry on timeout for CLI engines. | Engines E5 |
| E1 (#1273) | Not confirmed on a real install that Codex accepts `-m` before the trailing `-`. | Engines E7 / M1 |
| C3 (#1271) | An import over MCP with no stated start still gets "now minus duration"; header dates are read on the face only. | Capture C7 |
| C4 (#1275) | Plugins skip as `no_assignment` when only "Meeting summaries" is assigned (no Meetings group or Default). Plugins should follow the summary's engine. | Engines E5 |
| C4 (#1275) | Plugin proposals reach review and Needs you again before C5 builds their face. Watch for noise on his desk. | Capture C5, Daily D3 |
| D1 (#1277) | An owner string the hub cannot tell is him counts as *theirs*. If his own name is not set, his items written as "Karol" drop out of the number. Setup must ask his name (ST5), and Needs you should show a setup row while it is unset. | Setup ST5 |
| D0 (#1264) | Old action rows on his desk keep their said-words dues; only new writes resolve dates. A one-time resolve on read, or a backfill, is needed. | Daily D2 |
| D1 (#1277) | Glass (browser) tests that count Needs-you rows may need the new count rule; the main watcher will show it. | Watch |
| A2 (#1280) | The old queue path for events is probably broken: `reaction_service.py` sets grounding to the event's refs, which `qualified_ref` refuses (watch: refs, URLs), so the run fails "Source unavailable". | Automations A4 / backlog |
| A2 (#1280) | The Inbox zone exists only on a seeded desk; on a fresh desk the result note is filed nowhere. | Automations A6 |
| A2 (#1280) | With auto-run off, an event's occurrence item waits until someone re-runs that item; Run now makes a fresh one instead. | Automations A4 |
| A2 (#1280) | Engine and gh replies in its tests use the real wire shape but were not recorded live. | Re-record on the next live walk |
| Process | The quick check runs only related tests; four reds reached main today unseen, and no main watcher was running. The orchestrator now runs the full suite after each batch of merges and redeploys the desk only when green. | Orchestrator |
| #1281 | `scripts/gen_docs.sh` stops at `generate_capability_docs.py`: `docs/internal/philo/data/desk.json` capability `tests[13]` names a TypeScript test title that no longer exists, so later generators do not run. | Small fix |
| S0/S1 | Something emptied a worktree's `web/node_modules` while its quick check waited for the lock. Cause unknown. | Watch |
