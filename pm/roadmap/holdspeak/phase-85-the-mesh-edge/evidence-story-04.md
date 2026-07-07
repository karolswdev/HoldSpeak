# Evidence — HS-85-04 — Liveness on every surface + the honest doctor

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-85-04-liveness-surfaces-and-doctor` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/web/routes/primitives/ask.py` — `_runnable_models` rows for
  meshNode profiles carry `node` + `live` + `last_seen_seconds`; the ask
  refuses an offline meshNode target with an immediate 400 naming the node
  and its last-seen age, placed BEFORE intel construction (an earlier draft
  landed it after the run — caught reviewing the diff), so NOTHING queues.
- `holdspeak/web/routes/primitives/profiles.py` — `GET /api/profiles`
  carries a `mesh_liveness` ENVELOPE sidecar; the synced profile shape
  stays pure (the integration shape guard pins its exact keys).
- `holdspeak/db/mesh_relay.py` — `list_workers()` (every node that ever
  served, with last-seen).
- `holdspeak/commands/doctor.py` — the informational **"Mesh edges"** check
  (registered in `collect_doctor_checks`, so the setup-status drift guard
  covers it); the Runtime-profiles line names the mesh node instead of a
  `None` endpoint.
- `web/src/pages/profiles.astro` + `web/src/scripts/profiles-app.js` — the
  editor's third kind (Mesh node + node field; a mesh profile is now
  authorable in the UI), the card's Node/Model/State block ("live (2s
  ago)" / "offline (180s ago)"), the `⇄ mesh · <node>` badge, save/edit
  round-trip of `node`.
- `web/src/scripts/settings-app.js` + `web/src/scripts/dictation/runtime.js`
  — picker labels (`name — mesh · node`) and badges (`⇄ mesh · <node>`).
- `web/src/desk/components/RecipeRail.tsx` + `web/src/desk/desk.css` — the
  models door names a mesh model's node in the title and dims it when
  offline.
- `scripts/screenshot_hs85_liveness.py` — the asserting rig (stays as the
  story's regression rig).
- `tests/unit/test_mesh_liveness_surfaces.py` — new, 8 tests.

No new routes; `docs/api-surface.json` untouched.

## Verification artifacts

- `uv run pytest -q tests/unit/test_mesh_liveness_surfaces.py` →
  **8 passed in 1.06s**.
- `uv run python scripts/screenshot_hs85_liveness.py` →
  **HS-85-04 SCREENSHOTS OK**, every claim asserted:
  `state='live (2s ago)'`, `badge='⇄ mesh · walk-edge'`,
  `state='offline (180s ago)'`,
  rail title `'qwen3.5-4b — mesh · walk-edge (offline)'`,
  settings `label='Pocket 4B — mesh · walk-edge'`,
  `chip='⇄ mesh · walk-edge'` — 4 committed PNGs, eyeballed.
- `cd web && npm run build` → 17 pages; `npx vitest run` → **57 passed**.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3291 passed, 37 skipped** (standing env-gated skips).

## Acceptance criteria — re-checked

- [x] `/api/models` rows carry `live` + last-seen; set-equality with the
  ask allow-list holds — `test_models_rows_carry_mesh_liveness`,
  `test_stale_worker_reads_offline_with_age`,
  `test_non_mesh_rows_are_untouched`; the existing set-equality pytest
  passed unmodified.
- [x] Offline mesh override ⇒ immediate 400 naming the node —
  `test_ask_against_offline_mesh_node_is_an_immediate_400` (both the
  never-polled and aged cases; asserts nothing queued), with the live-node
  path proven by `test_ask_against_live_mesh_node_proceeds` (200 + the
  mesh badge).
- [x] Pickers + rail render the state, screenshot-verified live AND
  offline — the rig output above; offline entries stay pickable
  (assignment is durable, liveness is momentary).
- [x] Doctor lists mesh workers with ages; the drift guard stays green —
  `test_doctor_mesh_edges_states`,
  `test_doctor_runtime_profiles_names_the_mesh_node`; `tests/ -k doctor`
  green in the full run.
- [x] Non-mesh behavior byte-identical — non-mesh rows carry no new keys
  (test), and the route/picker neighbors passed unmodified.

## Deviations from plan

- Liveness rides the profiles-list ENVELOPE rather than the profile rows —
  the pinned shape guard made the honest design obvious (recorded in the
  story Notes).
- The `/profiles` editor's Mesh kind was implicit in the phase but landed
  here — without it, HS-85-05's "authored once in the editor" beat would
  be impossible.

## Follow-ups

- HS-85-05: the walk uses the editor's new Mesh kind for its beat 2, and
  doctor's "Mesh edges" line is part of beat 1's capture.
