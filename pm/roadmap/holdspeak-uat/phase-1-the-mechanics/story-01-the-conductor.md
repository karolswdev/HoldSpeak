# HSU-1-01 — The conductor: hosted runs

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** none
- **Owner:** unassigned

## Problem

Nothing today can hold HoldSpeak at arm's length: boot it with a
chosen configuration, watch its health, capture its logs, kill it, and
boot it again differently — all while an independent website stays up
to guide the human. The dogfood harness (Phase 67) proved the
substrate (isolated `_home`, `dogfood/setup.sh`, `dogfood/env.sh`) but
it is shell scripts a human drives by hand. The conductor is that
substrate turned into a process.

## Scope

- In:
  - `uat/conductor/` — a small FastAPI app, launched with
    `uv run python -m uat.conductor`, serving on a pinned local port
    (default `8799`, `UAT_PORT` to override), localhost only.
  - **Run lifecycle**: a *run* gets a fresh isolated HOME under
    `uat/_runs/<run_id>/home/` (the dogfood `_home` recipe: config
    dir, data dir, linked HF/model caches so nothing re-downloads),
    boots `holdspeak web --no-open` as a managed subprocess with
    `HOLDSPEAK_WEB_PORT` pinned (default `8788`) and `HOME` overridden,
    polls a health route until up, and tears down (SIGTERM, then kill)
    cleanly. Restart-with-a-different-deck is a first-class verb —
    scenarios depend on it.
  - **Run DB**: sqlite at `uat/_runs/uat.db` — runs, scenario
    executions, step verdicts (schema lands here; verdict *writes*
    land in HSU-1-04). `uat/_runs/` is gitignored.
  - **Log capture**: the product's stdout/stderr per run to
    `uat/_runs/<run_id>/logs/`, tail-able over the conductor's API
    (a failing scenario's first question is "what did the server say").
  - **Dogfood absorption, part 1**: the conductor reuses the dogfood
    sandbox-building logic (setup, cache links) — imported or ported,
    not duplicated. Physical file moves only where the conductor must
    own the code.
  - Conductor API: `POST /api/runs` (create + boot), `GET
    /api/runs/{id}` (status/health), `POST /api/runs/{id}/restart`
    (new deck), `DELETE /api/runs/{id}` (teardown), `GET
    /api/runs/{id}/logs`.
- Out: decks and seeding (HSU-1-02), scenarios (HSU-1-03), the site UI
  (HSU-1-04), any change under `holdspeak/`.

## Acceptance criteria

- [ ] `uv run python -m uat.conductor` serves; `POST /api/runs` boots
      an isolated HoldSpeak whose DB and config live under
      `uat/_runs/<run_id>/home/`, never the real `~`.
- [ ] Health is honest: a run reports `booting → up → down`, and a
      product that fails to boot reports `failed` with the log tail —
      never a hang.
- [ ] Restart-with-teardown works: two boots in one run, second under
      a different config file, no orphan processes (asserted by pid
      checks in tests).
- [ ] Product stdout/stderr captured per run and readable via the API.
- [ ] The conductor never imports the `holdspeak` package into its own
      process (subprocess boundary only) — enforced by a test grepping
      `uat/conductor/` imports.
- [ ] Unit/integration tests green under `uv run pytest -q tests/uat/`.

## Test plan

- Unit: run-ID/paths, HOME assembly, deck-file placement,
  process-state machine (fake subprocess).
- Integration: real `holdspeak web --no-open` boot on a free port,
  health poll, teardown, restart (marked, skipped where the package
  can't boot).
- Manual / device: n/a — covered in HSU-1-06.

## Notes / open questions

- Port pair convention: conductor `8799`, product-under-test `8788` —
  both distinct from the real hub's `8765` so a sitting can run beside
  the owner's live desk.
- The mesh hub auth token (`web_auth.py:ensure_web_token`) is per-HOME,
  so the isolated run gets its own token for free; the conductor reads
  it from the run HOME when it needs to call product APIs (seeding,
  HSU-1-02).
