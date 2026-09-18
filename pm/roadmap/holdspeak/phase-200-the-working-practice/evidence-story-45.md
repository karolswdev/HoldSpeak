# Evidence - HS-200-45

- **Story:** HS-200-45 - One composition root — MCP goes through the hub's services
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-17T23:55:46Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.IcPO9vDuPQ uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_one_composition_root.py tests/integration/test_phase200_one_composition_root_processes.py tests/unit/test_backup_restore_cli.py tests/critical/test_journey_backup_restore.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9e9a569a495160b549eb847717a10caa342071f9

```text
...................................                                      [100%]
35 passed in 11.12s
```

### Captured run — 2026-09-17T23:55:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.f5Cy7xKLEY uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_doc_claims.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9e9a569a495160b549eb847717a10caa342071f9

```text
...........................................................              [100%]
59 passed in 2.94s
```

## The one fact, and what it caused

MCP never wrote raw SQL. It composed the SAME service classes the HTTP routes use, from a SECOND root: `tools.dispatch` and 19 families rebuilt everything from `get_database()` with no `broadcast=` and none of the hub's wiring; `mcp_http.py` received the hub's `WebContext` and dropped it; the stdio sidecar opened the owner's live database as a second process that never touched the owner lock. One fact, four symptoms: an MCP write never reached the open desk, the sidecar walked around the lock, concurrent access ran on `journal_mode=delete`, and tools meant different things depending on where they ran.

## What is true now

- **One composition root.** `holdspeak/runtime/composition.py`: `RuntimeServices` (52 fields: db, observer, broadcast, and every live service the hub composes) installed by `_create_app`; `tools.dispatch`, `resources.py`, `refinement_runtime.py` and all 19 families resolve db/observer/services through it (`db_or`/`observer_or`/`runtime_service`). `service()` raises on a name the root does not carry. An AST fence fails on any bare `get_database()`/`get_observer()` call under `holdspeak/mcp/**`; a second fence drives the real `_create_app` on an isolated HOME and asserts every name any family asks for is a field and non-None. That fence found `confluence_provider` declared on `WebContext` and never constructed (HS-174-07); it is constructed now.
- **The sidecar is a client of the running hub.** `holdspeak-mcp` discovers the hub per message from the owner lock body (pid alive, port, host), forwards JSON-RPC verbatim to `POST /api/mcp` with the hub's own token read from the config file (never `Config.load`, which would mint one), and returns the hub's answer. No hub: a JSON-RPC error names the database, the remedy (`start holdspeak web, then retry`) and the diagnosis hatch; the database is never opened and no file is created under HOME. `HOLDSPEAK_MCP_STANDALONE=1` runs bare and CLAIMS the owner lock with label `holdspeak-mcp pid N`, so a later hub refuses loudly. The rejected option, a read-only second builder, is argued in `runtime_lock.py`'s C10 paragraph and `docs/MCP_SIDECAR.md`.
- **A loopback OWNER is admitted on `/api/mcp` with the remote flag off.** The flag governs the remote listener. A notification returns a real 204 (the old `JSONResponse(None, 204)` raised `Response content longer than Content-Length` inside the hub on every handshake).
- **One frame for a changed desk object.** `PrimitiveService` and `WorkbenchService` take `on_changed`; the hub binds it to `broadcast("desk_changed", {kind, id, op, origin})`; the desk subscribes once (`useDeskChangedRefresh`) and refreshes debounced. Also emitting: the reaction and resourceful projections, coder notes, the rails journal note, guardrail seeds. Meetings, rooms, thoughts and sync emit nothing, and the docs say so.
- **WAL, busy_timeout, foreign_keys, all three set by `_apply_pragmas`.** `journal_mode=WAL` is a persistent file property; setting it on open costs 0.18 ms median (0.0008 ms warm). Proven on a `cp` of the owner's real database (the original never opened, the copy deleted): 243 tables / 143,228 rows before, `wal` after `Database(path)`, no table lost rows, `integrity_check: ok`, `foreign_key_check: 0`. `backup_database` checkpoints first; `restore_database` refuses under a live owner AND under any open connection (SQLite's own exclusivity via `PRAGMA journal_mode=DELETE` on a timeout-0 connection), then removes stale `-wal`/`-shm` after the copy. Every database-file copy site was checked (table in the worker report, reproduced below).
- **Honest errors.** `project.steward.trigger`'s `{"success": false, "code": "scheduler_not_wired"}` is a `ServiceError` (isError true); `recipe.chat`'s retirement is a `ToolError`; `meeting.start_capture`/`stop_capture` outside a hub name the hub instead of blaming the input. Left as domain answers, with reasons: `desk.verb` `ui_only`, `people.readiness` `access: disabled`, `project.accept_suggested_source`'s `accepted_no_watch`.

## The fences and their pre-fix failures (captured on the pre-fix tip b391632f)

(a) no broadcast: `AssertionError: expected ONE desk_changed frame, saw []`. (b) contended access: the brief expected `database is locked` from a missing `busy_timeout`; Python's `sqlite3.connect` already applies `timeout=5.0`, so that premise was wrong and is corrected here. The real hazard was `journal_mode=delete`: a writer behind a held READ failed with `sqlite3.OperationalError: database is locked`; the docstring fence failed `assert 'delete' == 'wal'`. (c) sidecar with no hub: `the sidecar CREATED a database with no hub: ['.../.local/share/holdspeak/holdspeak.db']`. (d) sidecar with a hub: a real hub on an isolated HOME, the real `holdspeak-mcp` subprocess, `desk.create` over stdio, read back over `GET /api/notes`, one database, one lock, one frame at the broadcast seam (no harness opens a `/ws` socket and a sidecar together; stated in the test). (e) loopback owner with the flag off: `{"error":"streamable_http_not_enabled"} assert 404 == 200`.

## Counsel-on-built: BOUNCE, then paid

P0: `holdspeak restore` while the hub ran bricked a WAL database (`disk I/O error` for every fresh reader and the next hub) because restore unlinked `-wal`/`-shm` under live connections and nothing enforced offline. Paid by the two refusal gates above, fenced (a live owner refuses with bytes unchanged; an unlocked open connection refuses; the CLI exits 1; offline restore works), and `docs/RELEASING.md`'s "a restore can never be the step that loses data" corrected. P1: the 204 traceback on every handshake; the sidecar minted `config.json` via `Config.load`; `ask_service`/`plugin_job_service` were asked for and not carried (built bare in the hub while a comment claimed the hub instance); the "any caller" frame claim was true only for the primitive routes and MCP. All paid as listed above. P2 paid: ownership label passthrough, the off-loopback bound-host remedy, the bare-accessor AST fence, the WAL/synced-folder sentence, the hs165 walk's transcript write made explicit. Skipped by ruling: two hubs in one test process; a fuller iCloud treatise.

## Ruling corrections recorded

R5 as briefed ("remove stale sidecars on restore") was only safe offline and nothing enforced offline; the ruling was incomplete and the P0 followed from it. R7(b) named the wrong hazard (busy_timeout); the worker measured the default and corrected the premise rather than writing a fence that passed pre-fix. R1 as briefed (`current().db` everywhere) would have broken ~40 tests that monkeypatch `<module>.get_database`; the `db_or` fallback is bare-root only and the AST fence keeps it honest.

## Doc-claims registry

Two `known_false` rows flipped to `holds` in this commit because their sentences became true (`mcp_http.py:3`, `connection.py:3`), each with a predicate over the real code; the SECURITY.md tailnet-bind row stays `known_false` and unowned (the remote auth model was out of scope here; parked). Ratchet 7 → 5.

## Not done here, deliberately

- `holdspeak/doctor.py:251` still builds a bare `PrimitiveService(get_database())`: a CLI path with no hub to borrow from.
- The four real-DB schema tests skip under an isolated HOME, so their backup-API patch is unexecuted; the same change in `test_phase200_runtime_identity.py` ran and caught the WAL bug.
- `bind_host` is still applied by nothing (BACKLOG).

## Counsel re-read: RATIFY-WITH-CONDITIONS, both paid

Every original finding verified PAID with evidence (probe outputs after: the restore refuses with `DatabaseInUse`, the notification returns a real 204 with no hub-side traceback, no config file is minted, `ask_service` in the hub carries the bus). New hunt: the exclusivity probe leaves the file in `delete` mode with rows intact if the copy fails before touching the destination, and `Database(p)` reopens it as `wal`; a torn copy is covered by the pre-copy safety backup as before. Condition A: on a write-protected file the journal switch was a silent no-op, so the refusal never fired and the run died later with a misleading error. Paid: the OS is asked first (`os.access` on file and directory) and the exclusivity connection opens with `mode=rw`; proven with a 0444 file in a 0555 directory: `... or its directory is not writable; restore needs a writable database file and directory. Nothing was changed.` Condition B: a comment on the hs165 walk's gated transcript write, noting the determinism assertions run unconditionally.

## The full suite (orchestrator, isolated HOME, xdist): 6 failed / 10386 passed, all six branch-new, all paid

`desk_changed` registered in `holdspeak/realtime_frames.py` and mirrored in `web/src/runtime/frames.ts`; the sidecar's loopback `urlopen` classified in the effect fence's `_EXCLUDED_CALLS` (the ledger is a tombstone; a call to the owner's own hub is not egress); the two Phase 143 censuses re-anchored to the moved lines, and one of them taught to see through `runtime_service(name, builder)`, because it had gone blind to the ask family's factory the moment it was wrapped; the inference-setup "reads do not mutate" test now compares logical state (`data_version`, `schema_version`, row counts) because a WAL read legitimately touches `-shm`; one new palette test pinned its precondition against xdist neighbours. Second full pass recorded in the commit message.

Second full pass: 1 failed / 10391 passed. The one, `test_scheduled_recording_conductor.py::test_one_shot_disables_after_cancelled` (`assert 'arming' == 'cancelled'`), passed in the first full pass and passes 3/3 serially: a scheduling-order flake under xdist load in a Phase 136 test this story does not touch.
