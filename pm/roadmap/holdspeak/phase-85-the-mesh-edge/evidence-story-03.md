# Evidence — HS-85-03 — `holdspeak mesh serve`, the edge worker

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-85-03-mesh-serve-worker` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/commands/mesh_serve.py` — new: `MeshServeWorker` (the loop
  factored into `claim_once` / `execute` / `poll_step` / `run_once` /
  `run_forever`), `urllib` transport (the house pattern), lazy-once engine
  via `build_configured_meeting_intel()` (THIS node's own resolution),
  exponential backoff (1s → 30s cap, reset on success), SIGINT/SIGTERM
  clean stop, one honest log line per claim/execute/outcome, token from
  `HOLDSPEAK_HUB_TOKEN` (env, never a flag).
- `holdspeak/main.py` — the nested `mesh` subcommand (`holdspeak mesh
  serve --hub --node --token-env --once`) + dispatch.
- `tests/unit/test_mesh_serve_worker.py` — new, 6 tests.

No route changes; `docs/api-surface.json` untouched by design.

## Verification artifacts

- `uv run pytest -q tests/unit/test_mesh_serve_worker.py` → **6 passed in
  1.15s** — end to end against an in-process hub app (the real mesh router
  over a real tmp DB): claim → injected-engine execute → the hub row
  completes with the result verbatim; a raising engine posts `fail`
  verbatim; the backoff sequence is exactly 1.0/2.0/4.0; an empty `--once`
  poll still stamps liveness (claim-as-heartbeat, the point); run-forever
  does the queued work exactly once and stops on `stop()`; the CLI parses
  (`python -m holdspeak.main mesh --help` exits 0).
- CLI/command neighbors: `uv run pytest -q tests/unit -k "main or cli or
  command"` → **192 passed**, unmodified.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3283 passed, 37 skipped, 2 warnings in 251.55s** (standing env-gated
  skips).

## Acceptance criteria — re-checked

- [x] Against a test hub: `--once` claims, executes via an injected
  engine, and the hub row completes verbatim —
  `test_once_claims_executes_and_completes_verbatim` (params
  system/user/temperature/max_tokens asserted verbatim on the engine).
- [x] A raising execution posts `fail` with the error verbatim —
  `test_engine_failure_posts_fail_verbatim` ("llama exploded: OOM" lands in
  the job row; `--once` exits 1).
- [x] Hub unreachable ⇒ backoff, no crash-loop; clean stop —
  `test_unreachable_hub_backs_off_without_crashing` (1/2/4 sequence),
  `test_run_forever_stops_on_stop_and_does_work`.
- [x] Claims stamp liveness end to end —
  `test_once_with_no_work_exits_clean` asserts `worker_last_seen` through
  the HS-85-01 helper after an EMPTY poll.
- [x] No config file changes — the command's arguments are its whole
  contract (`--hub`, `--node`, `--token-env`, `--once`).

## Deviations from plan

None of substance; three implementation notes recorded in the story
(urllib not requests; `--once` exit semantics distinguish silence from
outage; the engine builds lazily once and is reused across jobs). The
live proof against the real hub stays with HS-85-05 as planned — the
running hub predates the relay routes and restarts there anyway.

## Follow-ups

- HS-85-05's walk runs this worker as the real second process
  (`--node walk-edge`) and kills it for the offline beat.
