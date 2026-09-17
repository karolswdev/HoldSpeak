# HS-200-45: One composition root — MCP goes through the hub's services, like every other caller

- **Project:** holdspeak
- **Phase:** 200
- **Status:** in-progress
- **Depends on:** HS-200-02
- **Unblocks:** HS-200-28
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** the 2026-09-13 operational-surface audit §9-10 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`); the owner's ruling, 2026-09-13

## Problem

**MCP does not write raw SQL — it goes through the service layer. The defect is
that it builds its OWN copy of that layer.** There are two composition roots, and
every symptom below is downstream of that one fact.

`holdspeak/mcp/tools.py:640-651` calls `get_database()` and constructs
`PrimitiveService`, `WorkbenchService`, `MeetingService`, `RecipeService`,
`DictationService`, `EventQueryService`, `FollowThroughService`,
`MondayBriefService`, `DeskService`, `DecisionRecordService` — the same classes
the HTTP routes use, composed **bare**, with no `broadcast=`.

The hub's own routes compose with the live context
(`holdspeak/web_server.py:882,1047`: `broadcast=lambda message_type, data: ...`).

**And the in-hub MCP route holds the right root and drops it.**
`holdspeak/web/routes/mcp_http.py:47` takes `ctx: WebContext`. At `:149` it calls
`handle_message_for_principal(...)`, which lands in `tools.dispatch`, which
rebuilds everything from `get_database()`. The context is received and unused for
dispatch.

### What that one fact causes

1. **An MCP write never reaches the open browser.** No broadcast callback, so no
   `/ws` frame. The desk carries a manual "Refresh from hub" verb
   (`holdspeak/mcp/resources.py:75`) as the standing workaround. A remote write
   lands in the database and sits there.
2. **The out-of-process sidecar needs its own database handle**, which is how it
   walks around the owner lock. `holdspeak/runtime_lock.py:1-27` is an exclusive
   `flock` whose docstring says *"C10 forbids introducing a multi-writer SQLite
   arrangement at all."* `grep -rn "runtime_lock\|claim_runtime\|flock"
   holdspeak/mcp/` → **0 hits**. Only the hub claims it.
3. **Concurrent access is not made safe either.** `PRAGMA journal_mode` on a real
   database is **`delete`, not WAL**; `holdspeak/db/connection.py:3` claims "WAL
   pragmas" while `:25-27,41-43` set only `foreign_keys=ON`. No `busy_timeout`,
   no `isolation_level` anywhere in the package.
   `sqlite3.OperationalError: database is locked` already appears in E2E runs.
4. **Tools silently mean something different depending on where they run.**
   `meeting.start_capture` returns an error outside the hub because the callbacks
   live only in `holdspeak/web/routes/meetings/live.py:46-51`;
   `project.steward.trigger` returns `{"success": false, "code":
   "scheduler_not_wired"}` with **`isError: false`** — a soft refusal a caller
   reads as success. Model-invoking tools run in the sidecar's own process and
   compete with the hub for the same GPU with no coordination.

## Scope

Give the product one composition root and make MCP a caller of it, the way an
HTTP request is. Where a caller genuinely cannot be in-process, it becomes a
client of the hub rather than a second builder of the same services.

Implementation seams: `holdspeak/mcp/tools.py` dispatch composition;
`holdspeak/web/routes/mcp_http.py` (use the `WebContext` it already receives);
`holdspeak/mcp/server.py` startup; `holdspeak/db/connection.py` pragmas;
`holdspeak/runtime_lock.py`; `docs/MCP_SIDECAR.md`.

Out: changing what any MCP tool does. Out: the tool catalogue, the palettes, the
remote transport's auth model. Out: editing the owner's `.mcp.json`.

## Acceptance criteria

- [ ] **The in-hub MCP path uses the hub's own composed services.** An MCP write
      arriving at `/api/mcp` broadcasts exactly as the equivalent HTTP write
      does, and the open desk updates without a manual refresh. Proven by
      driving the real route against a real bus subscriber.
- [ ] **A caller that cannot be in-process is a CLIENT of the hub, not a second
      builder.** The stdio sidecar either proxies to a running hub or refuses
      with a sentence naming the owner and the remedy — never a silent second
      writer. The fork is argued in the evidence, with the rejected option and
      why.
- [ ] **Where concurrent access remains possible at all, it is actually safe:**
      `journal_mode` and `busy_timeout` match what `db/connection.py`'s own
      docstring claims, or the docstring is corrected. Code and comment agree.
- [ ] An existing database is migrated to the chosen journal mode without data
      loss, proven on a COPY of a real database, never on the owner's.
- [ ] **A tool that cannot do its job in the caller's context says so as an
      error, not as success.** `project.steward.trigger`'s soft refusal becomes
      an honest one; `meeting.start_capture`'s unavailability names why.
- [ ] A fence test reproduces the no-broadcast defect against the pre-fix tree —
      an MCP write, a subscribed bus, and no frame — and passes after.
- [ ] A fence test reproduces the contended-write failure pre-fix and passes
      after.
- [ ] `docs/MCP_SIDECAR.md` states the actual arrangement. Its current claim that
      the HTTP route composes "on the web runtime's LIVE services (never the
      sidecar's bare `serve()` instances)" (`mcp_http.py:3`) is **false today**
      and becomes true here, or is corrected.

## Test plan

Planned suite: `phase200_one_composition_root`. Drive the real `/api/mcp` route
through the real router with a real bus subscriber for the broadcast proof. Drive
a real hub and a real sidecar against one temporary database for the writer
proof. Never touch `~/.local/share/holdspeak/holdspeak.db`.

## Notes / open questions

**The owner's ruling, 2026-09-13**, on being shown the audit: *"wouldn't the MCP
need to go through some kind of common service layer? much like any http call?
why the fuck do those mcps even write directly to the db in the first place?"*
The layer exists and MCP uses it — but from a second root. This story closes that,
and the second-writer hazard closes with it rather than being patched separately.

This also unblocks HS-200-28: the Phase 200 baseline classifies the missing MCP
steering verbs as a defect to repair, and repairing them against a root with no
broadcast would ship steering that the desk cannot see.
