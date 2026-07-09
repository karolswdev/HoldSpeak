# Evidence - HSU-1-01

- **Story:** HSU-1-01 - The conductor: hosted runs
- **Status:** done
- **Date:** 2026-07-09

## What shipped

`uat/conductor/` — a standalone FastAPI app (`uv run python -m uat.conductor`,
pinned port 8799) that holds HoldSpeak at arm's length:

- **Isolated runs** — each run gets a fresh HOME under `uat/_runs/<run_id>/home/`
  (the dogfood `_home` recipe ported to `home.py`: config/data/cache dirs, symlinked
  HF + Models caches so nothing re-downloads). Config is a sparse overlay the product's
  own `Config.load` merges over defaults — the conductor writes JSON, never imports `Config`.
- **Subprocess boot** — `holdspeak web --no-open` in its own process group with `HOME`,
  `HOLDSPEAK_WEB_PORT`, `HOLDSPEAK_WEB_HOST` pinned; health polled on the auth-exempt
  `/health` route; honest status `booting → up → down`, or `failed` with the log tail.
- **First-class verbs** — restart-with-a-different-overlay (old process torn down first),
  teardown by process-group (SIGTERM→SIGKILL, no orphans), per-run stdout/stderr capture
  tail-able over the API.
- **Device reachability** — a LAN-bound run mints its own web auth token (written into the
  run HOME's config before boot, riding the product's Phase-25 non-loopback guard) and
  reports pairing facts; loopback-only is the default.
- **Run DB** — sqlite at `uat/_runs/uat.db`, full schema landed (runs, scenario_executions,
  step_verdicts, findings); verdict writes arrive in HSU-1-04.
- **The subprocess boundary** — the conductor never imports the `holdspeak` package, enforced
  by an AST grep of `uat/conductor/` **and** a clean-subprocess import check.

## Proof

20 harness tests pass, including `test_run_lifecycle_real.py` which boots an **actual**
HoldSpeak under an isolated HOME, proves `/health` answers, restarts it under a different
overlay (asserting the old pid is dead — no orphan), and tears it down (asserting no live
process). The owner's command was also smoke-driven live: `python -m uat.conductor` served,
`POST /api/runs` booted a real product reporting `status=up` + pairing URL, `DELETE` tore it
down to `status=down`, and no `holdspeak`/conductor processes lingered.

### Captured run — 2026-07-09T06:38:53Z

- **Command:** `uv run pytest -q tests/uat/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 42d49a2870192e2fad6b9474660d5e01b7682c7e

```text
....................                                                     [100%]
20 passed in 4.44s
```
