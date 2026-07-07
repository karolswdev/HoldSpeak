# Evidence — HS-85-05 — Docs + the live walk

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-85-05-docs-and-the-live-walk` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## The live walk (the phase's proof)

`scripts/walk_hs85_live.py` (the standing regression rig) against the REAL
hub on `127.0.0.1:8765`, with a REAL `holdspeak mesh serve` process as node
`walk-edge` carrying its own isolated HOME whose config points straight at
the `.43` llama.cpp — the hub knows the profile, only the NODE knows the
provider. All six beats asserted in one run:

```
beat 1: '[PASS] Mesh edges: walk-edge: live (0s ago)'
beat 2: profile authored in the editor → profile_ffdc41122782 (live (2s ago))
beat 3: agent badge = '⇄ mesh · walk-edge · Qwen3.5-9B-Q6_K-via-edge'
beat 4: reroute of fresh meeting 24edc825 executed THROUGH the edge;
        artifacts_saved=4 (worker completions 1→4)
beat 5: dictation dry-run THROUGH the edge (completions 4→5)
beat 6: offline refusal in 0.00s → "mesh node 'walk-edge' is offline
        (last seen 19s ago)"
HS-85-05 LIVE WALK: all six beats PROVEN — the request moved; the model
and the key never did
```

The worker's own log is the where-it-ran proof (one honest line per
claim/outcome; five claims — one agent turn, three reroute plugin calls,
one dictation rewrite — every one `COMPLETED on node walk-edge`):

```
job relay_af08a4adbfd0 CLAIMED for node walk-edge
job relay_af08a4adbfd0 COMPLETED on node walk-edge in 0.5s (167 chars)
job relay_2c1541c06d3e COMPLETED on node walk-edge in 0.5s (121 chars)
job relay_da098dd3952a COMPLETED on node walk-edge in 1.4s (443 chars)
job relay_115cd574b08e COMPLETED on node walk-edge in 2.1s (489 chars)
job relay_7886fd9a7b42 COMPLETED on node walk-edge in 0.4s (69 chars)
node walk-edge stopped serving the mesh
```

Screenshots (committed): `hs-85-05-walk-profile-live.png` (the editor-born
card reading "live (2s ago)"), `hs-85-05-walk-agent-mesh-badge.png` (the
desk conversation wearing `⇄ mesh · walk-edge`),
`hs-85-05-walk-rail-offline.png` (the models door dimming the dead edge).

The offline beat's pinned bound (< 5s): the refusal arrived in **0.00s**,
named (`mesh node 'walk-edge' is offline (last seen 19s ago)`) — the
HS-85-04 pre-queue 400, never a hang.

## What the walk caught (fixed here, each with a locking test)

Four stories of green unit suites, and the first END-TO-END run found three
shipping bugs — the story's whole reason to exist:

1. **The event-loop deadlock (the phase risk table's own prediction).**
   Every LLM-running route was `async def` calling the blocking engine
   inline; a mesh run WAITS on the relay queue while that same loop must
   serve the worker's claim polls. The job died at its deadline as "never
   claimed" — twice, identically, with the worker demonstrably polling.
   Fixed with `await asyncio.to_thread(...)` at all nine call sites
   (`ask.py`, `recipes.py` ×2, `chains.py`, `workflows.py` ×2,
   `dictation/pipeline.py` dry-run + remote, `cadence.py`), locked by
   `tests/unit/test_engine_off_the_loop.py` (5 tests: a spy engine asserts
   NO running loop is observable from its thread).
2. **The mesh-blind capability gate.** `resolve_llm_capability` judged only
   the endpoint shape (`base_url`), so a mesh-adopted config disabled the
   `llm` plugin capability and the reroute reported `executed: true` with
   every LLM plugin silently skipped. A named node now short-circuits to
   capable (liveness stays a run-time question with a named refusal) —
   `test_llm_capability_knows_the_mesh`.
3. **The de-facto second seam.** All 14 builtin meeting plugins (and the
   segment probe) call `MeetingIntel._chat_completion_text(messages, …)`
   directly — a chat surface the "tiny `run_prompt` seam" never covered, so
   plugin LLM calls failed softly on a mesh engine. `MeshRelayIntel` now
   adapts it by folding messages onto the one relay wire —
   `test_chat_seam_folds_messages_onto_the_relay`.

Also caught live, fixed in this branch:

- **v10→v11 upgrade dropped `profiles.node`** — a column ADDED to an
  existing table is invisible to `CREATE TABLE IF NOT EXISTS`; a v10
  database upgraded to a stamped v11 with the column silently missing.
  Explicit `ALTER TABLE ADD COLUMN` guard —
  `test_upgrade_adds_the_profiles_node_column`.
- **Worker recursion guard** — a serving node whose OWN engine resolves to
  a mesh profile would relay onward (or back to itself) instead of running
  anything; it now fails the job by name —
  `test_recursion_guard_refuses_a_mesh_engine`.
- **The editor's fresh card lied** — a just-authored mesh profile read
  "never served" until reload; the save now re-pulls the list so the card
  states the node's real state (`profiles-app.js`).
- The walk's worker runs `-v` (its honest log otherwise goes only to the
  temp HOME's log file) and imports a FRESH transcript per run (reroute
  dedup keys off the transcript hash, so a fixed meeting proves nothing on
  replay).

## Docs

- `docs/MODELS.md` — "The mesh edge: run on another node" under Runtime
  profiles: what serves (one command, running it is the consent), what
  moves (the request, hub ⇄ executing node only), what never moves (the
  model and the key), liveness honesty, the doctor line.
- `README.md` — the runtime-profiles bullet grows the one-sentence mesh
  edge (`holdspeak mesh serve` on another of your machines).
- `docs/SECURITY.md` — §4 egress table gains the **Mesh relay** row (what
  leaves, between whom, and the consent gate).
- Voice/drift guards: `uv run pytest -q tests/ -k "voice or drift or docs"`
  → **107 passed** with the new prose in place.

## Verification artifacts

- New/changed tests: `test_engine_off_the_loop.py` (5),
  `test_mesh_relay_provider.py` (+1 = 16),
  `test_intel_profile_resolution.py` (+1 = 20),
  `test_mesh_serve_worker.py` (+1 = 7),
  `test_db_schema_policy.py` (+1 = 8) — all green.
- `cd web && npm run build` → 17 pages; `npx vitest run` → **57 passed**.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  see the phase status line (run at close).

## Acceptance criteria — re-checked

- [x] The walk passes end to end, six beats asserted, worker log captured
  (above).
- [x] Offline refusal measured inside the pinned bound: 0.00s (< 5s),
  named, never a hang.
- [x] Docs guards green; touched guides read product-tense (107 passed).
- [x] BACKLOG row T, roadmap README, phase status, final-summary updated
  in the closing commit.
- [x] Full suite green (recorded in `current-phase-status.md`).

## Deviations from plan

- The walk grew beats the story sketch folded together: dictation got its
  own beat (the HS-85-02 owner call made DIR a first-class relay rider),
  and beat 4 imports a fresh throwaway meeting instead of rerouting a
  fixture (dedup honesty).
- Three of the fixes (deadlock, capability gate, chat seam) live in
  runtime code, not docs — the story absorbed them because the walk is
  precisely where they could be found (recorded per the phase's charter).

## Follow-ups

- The HSM follow-up (recorded in `final-summary.md`): the Apple worker +
  the per-device "serve my models to the mesh" consent toggle on this
  proven wire.
- Backlog candidate: the async routes still run LOCAL engine calls in the
  threadpool one at a time per request — fine today; revisit only if chat
  surfaces multiplex heavily.
