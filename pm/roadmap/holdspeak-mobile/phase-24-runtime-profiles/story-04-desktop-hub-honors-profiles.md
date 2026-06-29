# HSM-24-04 — The desktop hub honors profiles

**Status:** planned (after 24-01; parallel with the Apple stories).

## Problem

The desktop hub is the execution + persistence center (per Equilibrium). For profiles to be in
equilibrium, the hub must store/serve them and run an agent on its assigned profile — otherwise an
agent assigned to "Claude" on the iPad would silently fall back to the hub's default when run on the
hub.

## The design

- The hub persists `RuntimeProfile`s (shape only) alongside agents, and serves them on the sync
  routes the mesh already uses (`SyncKind.profile` rides the same `ChangeSet`).
- The hub's own key store is its existing secrets path (env / its keyring) — the synced shape never
  carries the key here either; the hub joins the key at request time, exactly like the Apple side.
- The hub's agent-run path resolves `agent.profileId` → the profile → the right backend
  (its local runtime for `.onDevice`, an OpenAI-compatible client for `.openAICompatible`). Unknown/
  absent profile → the hub's active default (graceful).
- Honest `n/a`: an `.onDevice` profile that names a GGUF the hub doesn't have is a rendered
  "unavailable here," not a crash.

## Scope

- Hub persistence + sync of `RuntimeProfile`.
- Hub-side key resolution (its secrets path; never from the synced payload).
- The agent-run path honors `agent.profileId`.

## Implementation notes (investigated 2026-06-28, before starting)

The hub is the persistence center — treat this as a careful, pytest-driven schema change:
- **Schema:** `holdspeak/db/core.py`, `SCHEMA_VERSION = 3`, agents table at ~739. The migration model
  (Phase 31, HS-31-04) is "re-apply `SCHEMA_SQL` (`CREATE TABLE IF NOT EXISTS`) + bump version, via
  `_ensure_schema`'s backup-then-apply." **Caveat that bites here:** re-applying `SCHEMA_SQL` adds new
  TABLES but NOT new COLUMNS to existing tables. A `profiles` table is free; **`agents.profile_id` needs
  a guarded `ALTER TABLE agents ADD COLUMN profile_id` in `_apply_schema`** (check `PRAGMA table_info`
  first; idempotent), OR model agent→profile as a join table to avoid the ALTER. Bump `SCHEMA_VERSION`
  → 4. **Regenerate `tests/fixtures/db_schema_canonical.txt`** (the `test_fresh_schema_matches_canonical_snapshot`
  guard, test_db.py:1619; query at :1632) — see [[reference_schema_snapshot_regen]].
- **Sync:** `holdspeak/web/routes/sync.py` — add `"profile"` to `SYNC_KINDS` (:42); add a `profiles`
  bucket to `_MERGEABLE` (:50) + `_BUCKET_KIND` (:75); add `"profile_id": "profile_id"` to the agents
  `_MERGEABLE` field map (:55); serve profiles in the pull route. NOTE: the Apple side does not yet PUSH
  profiles in its desk-sync ChangeSet — wire that too (it persists them locally only today).
- **CRUD + run:** `holdspeak/web/routes/primitives.py` — agents carry `profile_id` (:261 area + run at
  :334); add profiles CRUD; the run (`build_configured_meeting_intel`, intel/providers) currently uses
  the hub's SINGLE configured provider — resolve `agent.profile_id` → if `.openAICompatible`, build a
  provider for it with the key from the hub's SECRETS (env/keyring), never the payload; honest fallback
  to the default for on-device-GGUF profiles the hub can't host.
- **Key custody on the hub:** mirror the never-sync rule — the synced profile shape has no key; the hub
  joins its own secret at request time.

## Test plan

- `uv run pytest`: a synced profile round-trips without a key; an agent run resolves its profileId to
  the right backend; absent profile → default; the never-sync invariant holds on the hub serializer.

## Done when

The hub stores/serves profiles, resolves keys from its own secrets (never the payload), and runs an
agent on its assigned profile — tested.
