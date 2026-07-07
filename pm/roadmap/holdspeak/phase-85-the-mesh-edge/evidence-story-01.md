# Evidence — HS-85-01 — The relay queue + the node wire

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-85-01-relay-queue-and-node-wire` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/db/core.py` — the `mesh_relay_jobs` (+ per-node/status index)
  and `mesh_workers` DDL; `SCHEMA_VERSION` 9 → 10 in the same edit (the v9
  lesson: additive-unbumped means old stamps never run the DDL); the
  `mesh_relay` repository wired on the `Database` container.
- `holdspeak/db/models.py` — `MeshRelayJob` record (hub-local; docstring
  pins the never-synced posture).
- `holdspeak/db/mesh_relay.py` — new repository: `enqueue` (120s default
  deadline), per-node oldest-first `claim_next` (every poll stamps
  `mesh_workers.last_seen`), `complete`/`fail` verbatim, `touch_worker` /
  `worker_last_seen` / `live_nodes(window)`, lazy `_expire_overdue` with
  named reasons for both abandonment shapes.
- `holdspeak/db/__init__.py` — repository export.
- `holdspeak/web/routes/mesh.py` — the node wire: `POST
  /api/mesh/relay/claim`, `POST /api/mesh/relay/{id}/complete`, `POST
  /api/mesh/relay/{id}/fail` (validation 400s; terminal/unknown outcomes
  refused 409 by name; enqueue deliberately has NO route).
- `tests/fixtures/db_schema_canonical.txt` — regenerated with the house
  no-op-regex recipe: +23 lines, purely additive.
- `docs/api-surface.json` + `docs/API_SURFACE.md` — regenerated (247
  routes; the three relay routes present).
- `tests/unit/test_mesh_relay_queue.py` — new, 12 tests.

## Verification artifacts

- `uv run pytest -q tests/unit/test_mesh_relay_queue.py` → **12 passed in
  0.95s** (one test fixed during authoring: wire tests must enqueue on the
  real clock or the fixed-timestamp deadline is honestly already expired —
  the queue caught its own test's mistake).
- Neighbors: `uv run pytest -q tests/unit/test_db.py
  tests/unit/test_db_schema_policy.py tests/unit/test_web_routes_sync.py
  tests/unit/test_api_surface.py` → **79 passed**, unmodified;
  `test_backend_density_guard.py` → **7 passed**.
- Schema guard: `uv run pytest -q tests/unit/test_db.py -k "schema or
  shape"` → **3 passed** after the snapshot regen.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3262 passed, 37 skipped, 1 warning in 262.96s** (standing env-gated
  skips).

## Acceptance criteria — re-checked

- [x] Enqueue → claim → complete round-trips verbatim; claim is per-node —
  `test_enqueue_claim_complete_round_trips_verbatim`,
  `test_claim_is_per_node`, `test_claim_orders_oldest_first`.
- [x] A claim poll stamps last-seen; `live_nodes(15)` reflects and ages out
  — `test_claim_poll_stamps_liveness_and_ages_out`,
  `test_worker_last_seen_reads_back` (injected clock).
- [x] Deadline expiry for both shapes, enforced on read, named reasons —
  `test_unclaimed_job_fails_at_deadline_with_a_named_reason`,
  `test_claimed_but_abandoned_job_fails_at_deadline`, plus
  `test_late_completion_is_refused`.
- [x] `fail` carries the node's error verbatim —
  `test_fail_carries_the_node_error_verbatim` (and over the wire in
  `test_wire_fail_and_validation`).
- [x] Never a synced kind — `test_relay_rows_never_ride_sync` pins
  `SYNC_KINDS` and `_MERGEABLE`; schema snapshot + api-surface regenerated
  in this commit.

## Deviations from plan

None of substance. Two implementation notes recorded in the story: enqueue
has no route by design (attack surface = claim/complete/fail only), and
late completions refuse with 409 so a slow worker can't silently "win"
after the user saw the timeout.

## Follow-ups

- HS-85-02 consumes `enqueue`/`get` and `live_nodes` for the relay
  provider's fast offline refusal.
- HS-85-03's worker speaks exactly these three routes.
