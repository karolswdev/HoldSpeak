# HS-85-01 — The relay queue + the node wire

- **Project:** holdspeak
- **Phase:** 85
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-85-02, HS-85-03
- **Owner:** unassigned

## Problem

Nothing can run "over there" until there is a place for work to wait and a
wire for a node to take it. The proven shape is the deferred-intel queue
(`intel_jobs`: claim → run → complete/fail, `retry_at` backoff —
`db/intel.py:65-107`); the relay needs its own hub-local table and three
node-facing routes, plus the one thing the mesh has never had: a liveness
record born from the worker's own polling.

## Scope

- In: the `mesh_relay_jobs` table + repository (id, `node`, `task_kind`
  ("llm" only for now), request payload (system/user prompt, temperature,
  max_tokens, model hint), status queued/running/completed/failed, result,
  error, `deadline_at`, created/claimed/completed timestamps). Hub-local:
  NOT a `SYNC_KINDS` member, schema-snapshot updated per the house recipe.
- In: node-facing routes — `POST /api/mesh/relay/claim` (body: node;
  returns the next queued job for that node or none; every call stamps the
  node's last-seen), `POST /api/mesh/relay/{job_id}/complete`,
  `POST /api/mesh/relay/{job_id}/fail`. Token-guarded like every paired
  call; `docs/api-surface.json` regenerated.
- In: worker liveness — a `mesh_workers` last-seen store (node → last poll
  timestamp) written on claim polls, readable by later stories
  (`live_nodes(window_seconds)` helper).
- In: lease hygiene — a claimed job whose deadline passes fails with a
  named reason ("node <n> claimed but never completed"); expiry enforced
  lazily on read (no new daemon).
- Out: the provider (HS-85-02), the worker (HS-85-03), any UI/doctor
  surface (HS-85-04), streaming, non-LLM task kinds (column exists, single
  value).

## Acceptance criteria

- [ ] Enqueue → claim → complete round-trips the payload and result
  verbatim; claim is per-node (node A never receives node B's job) (tests).
- [ ] A claim poll stamps last-seen; `live_nodes(15)` reflects it and ages
  out (tests, injected clock).
- [ ] Deadline expiry: unclaimed and claimed-but-abandoned jobs both fail
  at `deadline_at` with named reasons, enforced on read (tests).
- [ ] `fail` carries the node's error verbatim into the job row (test).
- [ ] The relay kinds never appear in `SYNC_KINDS` or `/api/sync/pull`
  (test), and the schema snapshot + api-surface manifest are regenerated.

## Test plan

- Unit: a new `tests/unit/test_mesh_relay_queue.py` (repo + routes via the
  primitives-test client pattern); `uv run pytest -q tests/unit -k relay`.
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a — HS-85-05 walks it live.

## Notes / open questions

- Schema bump: follow the Phase-50 policy (additive table ⇒ follow the
  house rule on `SCHEMA_VERSION`; the v9 model_manifests lesson says bump
  it, don't ship additively unbumped).
- Job rows hold prompt text like deferred-intel rows hold transcripts —
  same trust posture, documented in HS-85-05.
- **Implementation notes (recorded):** enqueue deliberately has NO route —
  only the hub's own relay provider (HS-85-02) writes jobs, so the wire's
  attack surface is claim/complete/fail only. A late `complete` (past the
  deadline) is refused with 409 naming the state, so a slow worker learns
  the truth instead of silently "winning" after the user already saw the
  timeout. Repository timestamps take an injected `now` for deterministic
  deadline tests.
