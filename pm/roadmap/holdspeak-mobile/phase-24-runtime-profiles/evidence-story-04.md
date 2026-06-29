# Evidence — HSM-24-04 (the desktop hub honors profiles)

**Date:** 2026-06-28
**Story:** [story-04-desktop-hub-honors-profiles.md](./story-04-desktop-hub-honors-profiles.md)
**Result:** DONE. The hub persists, syncs, manages, and RUNS on runtime profiles — with the API key
in the hub's secrets, never the payload. Full `uv run pytest` **3039 passed, 0 failed**.

## What shipped

**Data layer (PR #187):**
- Schema **v3 → v4** (`db/core.py`): `profiles` table (SHAPE only — no key column) + `agents.profile_id`;
  backup-then-apply migration + a guarded `ALTER TABLE agents ADD COLUMN profile_id` (re-applying
  SCHEMA_SQL adds tables, not columns); canonical snapshot regenerated.
- `ProfileRecord` + `ProfileRepository` (`db/models.py`, `db/primitives.py`); agents carry `profile_id`.
- Sync (`web/routes/sync.py`): `SyncKind` `profile`, a merge map + pull bucket, agent `profile_id` on
  the wire.

**CRUD + run (this commit):**
- Agents CRUD (`_agent_fields`) carry `profile_id`; **profiles CRUD routes** `GET/POST/PUT/DELETE
  /api/profiles` (shape only).
- **Agent-run resolution** (`/api/agents/{id}/run`): resolves the agent's `profile_id` →
  `build_meeting_intel_for_profile` — an `openAICompatible` profile runs on its endpoint with the key
  from the **hub's secrets** (`HOLDSPEAK_PROFILE_<ID>_KEY`, falling back to the default cloud key env),
  never the payload; an `onDevice`/absent profile falls back to the hub default (honest n/a). The run
  reports the resolved `profile_id`.

## Acceptance criteria → proof

- **A synced profile round-trips without a key; agent runs resolve to the right backend; absent →
  default; never-sync holds on the hub serializer.** `test_primitive_framework_sync` (profiles
  round-trip + the hostile-`api_key`-never-persisted/pulled assertion);
  `test_web_routes_primitives` (`test_profile_crud_roundtrip`,
  `test_run_agent_resolves_assigned_profile` — asserts the per-profile builder is used and the default
  is NOT, `test_run_agent_falls_back_when_profile_missing`). ✅
- **Key from the hub's secrets, never the payload.** `build_meeting_intel_for_profile` resolves the key
  from an env var by profile id; the profile shape (DB + wire + API) has no key field. ✅
- **No blast radius.** Full suite 3039 passed (the schema/run changes ripple through the whole DB +
  intel paths cleanly). ✅

## Also fixed (owner-requested)

`tests/e2e/test_route_preflight.py` was failing on clean `main` (the Cadence page `/cadence` was
served but missing from `PAGE_ROUTES`, so it was never swept). Added `/cadence` to `PAGE_ROUTES`; the
preflight now renders it too — green.

## Honest note

A live run against a real cloud endpoint (a real key in `HOLDSPEAK_PROFILE_<ID>_KEY`) is the hub
operator's walk; the resolution + custody are proven by the route tests with a fake intel.
