# Follow-ups found while building

Each item names the slice or recipe that takes it. Remove an item when the
PR that fixes it merges. The recovery reconciliation is retained in
`FOLLOWUPS-RESOLVED-2026-10-19.md`.

| Found in | Follow-up | Goes to |
|---|---|---|
| S4 delivery | The floor and meeting Keep behavior are verified. Mode recipes still enter Search as Agent rows; individual People need their Object-menu adapter because the world stores only the People singleton. Finish both seams in S5. S4 remains partial. | Shell S5 |
| Q0 (#1260) | Interview's answer-only pass puts a system message after the user message, which Qwen's template rejects. | Asking Q4, or a small fix |
| C2 (#1258) | Memory pages (what we decided, what is open) are not filtered by date, so a re-summary of an old meeting can still read later facts through a page. | Capture C6 |
| A0 (#1256) | Choosing Manual still pauses event starts and idle work; an existing test asserts it. The When editor replaces this control. | Automations A4 |
| S1 (#1259) | A person is not a desk object, so a person has no Object menu. | Shell S4 or Daily D6 |
| S1 (#1259) | The Builder tools switch is saved in the browser, not on the hub, so an agent cannot read or set it. | Shell S5 |
| S0 (#1257) | Search for "automation" still finds nothing. | Shell S5 (Automations A1 adds the alias) |
| ST0 (#1261) | ST1 #1347 delivered the one Rhythm quiet-hours store. Remaining ST0: Setup rows in words (the yellow Check chip), Other devices saved (`mcp_http.py:392-404` keeps it in memory only). | Setup ST1 |
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
| Process | The quick check runs only related tests; four reds reached main today unseen, and no main watcher was running. Current fast cycle: required quick check before merge; deploy after each merge; the full suite runs after merge at low priority and failures are fixed forward. The recovery tape is running; its current results are in STATUS. | Orchestrator |
| #1281 | `scripts/gen_docs.sh` stops at `generate_capability_docs.py`: `docs/internal/philo/data/desk.json` capability `tests[13]` names a TypeScript test title that no longer exists, so later generators do not run. | Small fix |
| A3 (#1293) | At 393 the NEW chip on the newest result is not visible (pushed off the meta line). | Automations A4 |
| E3 (#1294) | Job token budgets still cap the context: background 16,384, text/structured/tool 32,768 (`inference_capabilities.py:1235-1239`), so a 49,152 engine is capped where those apply. Budgets should follow the engine's real context. | Engines E5 |
| E3 (#1294) | MCP `model_library.define_endpoint` does not accept `context_tokens`; first-run LAN still auto-picks the first model; re-adding an existing engine keeps its first context. | Engines E4 / MCP M4 / Setup ST3 |
| AG1 (#1292) | The Automations window still says "No agents yet / New Agent" for saved personas; personas are retired as a face concept (DECISIONS #3). | Automations A4 |
| AG1 (#1292) | Branches named by the hub (`hs/<kind>-<id>`) show "new branch"; a slug from the item title needs a hub change. | Agents AG4 |
| AG2 (#1295) | At 393, Allow / Deny / Terminal stand with large gaps; the row is taller than needed. | Agents AG8 |
| AG2 (#1295) | The screen parse for questions is a stop-gap until the herdr-style rules (AG7); never read on a real Claude Code or Codex screen. | Agents AG7 |
| D2 (#1291) | The desk tool palette is at 27,679 of 27,680 bytes; the next MCP description change will break the guard. Trim descriptions or split the palette. | Watch / MCP M3 |
| D3 (#1296) | Promises from a plugin run that partly completes then fails stay pending (keep runs only on job completion). | Capture C5 |
| M2 (#1301) | Undo on "Wrote" shows only while the desk's delete-receipt bar is on screen. | Automations A6 |
| Q4 (#1302) | With the Thread window parked, interview, thread modes, slash commands and Thread tool holds have no face until Q7 (Ask my whole desk). A persona chat's follow-ups run as plain Asks. Q7 is now urgent. | Asking Q7 |
| Q4 (#1302) | Two browser files edited but not run (creation_glass New Thread step, desk_glass Thread rename step); the atlas `case.daily.thread.*` cases describe the parked face. | Next full run |
| Q4 (#1302) | The LAN chip shows twice (on the answer and in the footer); Send… under an answer is not built. | Asking Q5 |
| D4 (#1303) | On a fresh hub "No engine for summaries" counts 1 even with no meeting waiting; it should appear only when a meeting waits for a summary. | Daily D8 / Setup |
| D4 (#1303) | Browser files with edited selectors not yet run: today_glass, windows_glass, send_glass, chair_windows.py, windows_follow_the_bus (second half). | Next full run |
| D4 (#1303) | On a fresh hub "No engine for summaries" counts 1 even with no meeting waiting; it should appear only when a meeting waits for a summary. | Daily D8 / Setup |
| D4 (#1303) | Browser files with edited selectors not yet run: today_glass, windows_glass, send_glass, chair_windows.py, windows_follow_the_bus (second half). | Next full run |
| #1306 | `web/scripts/guard-architecture.mjs` is red on main with ~35 entries not in its baseline (not run by any suite). Trace and fix or re-baseline with reasons. | Small fix |
| S0/S1 | Something emptied a worktree's `web/node_modules` while its quick check waited for the lock. Cause unknown. | Watch |
| A7 (#1314) | Run now right after With ▸ Add, before the engine saves, is refused; the refusal still says "workbench" (`holdspeak/web/routes/primitives/workbenches.py:21`). | Small fix |
| A7 (#1314) | Meeting follow-ups cannot start "when a meeting ends": the hub has no meeting-ended event. It runs on Run now for now. | Automations A8 / Capture |
| E4 (#1311) | "Another HoldSpeak" tile has no add verb (no face creates a mesh destination). | Backlog |
| E4 (#1311) | No live OpenRouter / OpenAI / Anthropic / Gemini call made (stub only): Anthropic `/v1/models` auth, `response_format`, Gemini model ids unverified. | Next live walk |
| E5 (#1315) | Try it exists only for rows with a hub sample (not Automations, Live notes, Thoughts, Drafts, Speech). "Automations" maps to `workbench.item` (lane's choice). | Engines E6 |
| E5 (#1315) | Speech with no row now reads `no_assignment` (was `no_compatible_assignment`); faces that word it not all checked. | Setup ST1 |
| AG5 (#1308) | No cancel for a queued hand. | Agents AG8 |
| AG6 (#1310) | Hand again not built (`worktree_duplicate` refuses); a real `claude --resume <old id>` exit code not seen. | Agents AG7 |
| #1316 | If tmux restarts while the hub runs, the session watcher can mark a launch `complete` over `stopped_by_restart`, losing Resume. | Agents AG7 |
| D6 (#1312) | The intermittent People 503 cause is still unknown (D6 only logs it). Older Last-time fallback counts kept promises as decisions. | Daily D8 |
| M4 (#1321) | `model_library.remove` not built: a deleted profile can never be re-created, so removing `agent-claude` would break Add for good. RULING (orchestrator): Remove = retire (hide) + move its jobs to Everything else; never delete. | Engines / MCP |
| E7 (#1323) | Gemini CLI has no switch to turn web search and file reads off; accepted (the prompt already goes to Google). pi and Gemini get no desk tools yet. Sign-in for both reads "not known". | MCP M5 / Engines |
| A10 (#1324) | Folder mode unverified on the real CLIs (Codex shell to read; read-only sandbox refuses apply_patch; `--setting-sources user` keeps Claude sign-in). A folder must be a git worktree. Result card chip still says CLOUD. | Next live walk |
| A6 (#1322) | The phone Dock has no Automations tile; a NEW result shows in Today only. | Shell S3 |
| #1328 | Only the keyring stores are guarded; a `security` CLI call (e.g. acli) from a scratch HOME could still pop. | Watch |
| Sweep | `conductor at 393: still … moved 220 px` flakes in the desk sweep under load (seen in 3 lanes). | Small fix |
| M5 (#1330) | Not run on the real LAN box: the tool descriptions + task may overflow Qwen's 32k context, and the run then fails instead of retrying without tools. pi and Gemini still get no desk tools. | Next live walk |
| M6 (#1331) | `provider.github_pr_get` is not in the ASK palette; reviewers part unproven (the recorded PR had none). Other provider reads (Jira etc.) are probably refused for agent runs (owner-only). `_build_github_adapter` passes `db` positionally. | MCP / Projects |
| Q3 (#1332) | The touch fix in Search is unproven: the browser test passes on the old code too. | Watch |
| Q5 (#1335) | Ask about a person sends her name only (no grounding on her meetings and notes); Ask about this from Meetings has no test; Send… under an answer not tried on a real destination. | Ask Q8+ |
| AG3 (#1333) | "From your decision" proven only on recorded answers. "Asked 1 min ago" shows ~10 s after an ask. | Small fix |
| AG4 (#1334) | The desk sweep cannot open the hand sheet (no T3 check); the Where line not tested on a recorded answer. Dock drop is delivered with the S4 Floor change. | Agents |
| D8 (#1337) | Not built: a quiet notice + NEW line in Today when an automation finishes (needs a seen flag on `workbench_runs`). The morning notice cannot open Today (osascript). Fixtures send-hub, palette-enter, chair-brief, needs-you.gate still hold the old "No engine for summaries" row; re-record. | Daily D9 |
