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

## Test plan

- `uv run pytest`: a synced profile round-trips without a key; an agent run resolves its profileId to
  the right backend; absent profile → default; the never-sync invariant holds on the hub serializer.

## Done when

The hub stores/serves profiles, resolves keys from its own secrets (never the payload), and runs an
agent on its assigned profile — tested.
