# Evidence — HS-85-02 — The mesh profile kind + the relay provider

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-85-02-mesh-profile-and-relay-provider` (PR to `main`)
- **Owner:** Claude (Fable 5 session); mid-story scope call by the owner

## Files touched

- **The contract, moved as one:**
  `pm/roadmap/holdspeak-mobile/contracts/schemas/profile.schema.json`
  (`kind` enum + `meshNode`; `node` property);
  `holdspeak/db/models.py` (`ProfileRecord.node`), `db/primitives.py`
  (upsert/row), `db/core.py` (`profiles.node` column ⇒ **schema v11**),
  `web/routes/sync.py` (sync field set), `web/routes/primitives/profiles.py`
  (CRUD field); `apple/Sources/Contracts/Primitives.swift`
  (`Kind.meshNode` + `node` + tolerant decode — the pre-edit read caught
  that the Kind decode THROWS on unknown cases, so the missing case would
  have broken iPad sync);
  `tests/integration/test_primitive_framework_sync.py`
  (`_PROFILE_SHAPE_KEYS` — the fourth mirror — grew `node`).
- `holdspeak/intel/mesh_relay.py` — `MeshRelayIntel`: the standard
  `run_prompt` interface over the HS-85-01 queue; a node outside the
  liveness window refuses IMMEDIATELY by name and enqueues NOTHING;
  node-side failures and deadline expiries surface the queue's named errors
  verbatim.
- `holdspeak/intel/providers.py` — `_apply_runtime_profile` meshNode branch
  (node-shaped `EffectiveEndpoint`); both meeting-intel builders return the
  relay provider; `endpoint_egress(node=)` ⇒ `{scope: "mesh", host}`.
- `holdspeak/plugins/dictation/runtime_mesh_relay.py` — **the owner's
  mid-story call** (*"DIR could also be routed"*): `MeshRelayRuntime`
  reuses the endpoint backend's message/validation helpers (imported, not
  copied) with the transport swapped to the relay; `assembly.py` builds it
  inside the same counting/cold-start delegate; `setup_runtime.py` probes
  node liveness; `commands/doctor.py` names the node.
- `web/routes/primitives/ask.py` + `recipes.py` — call sites pass `node`;
  `_run_egress` reports mesh for per-run AND config-adopted runs.
- `web/src/desk/components/PersonaChat.tsx` + `AskPanel.tsx` — the badge
  renderers wear `⇄ mesh · <node> · <model>`.
- `tests/unit/test_mesh_relay_provider.py` — new, 16 tests;
  `tests/fixtures/db_schema_canonical.txt` regenerated (+1 line).

## Verification artifacts

- `uv run pytest -q tests/unit/test_mesh_relay_provider.py ...` (the mesh +
  dictation cluster) → **67 passed**.
- Contract + queue + resolution + route neighbors → **182 passed** after
  three pre-existing stubs of `build_meeting_intel_for_profile` grew the
  `node=""` kwarg (signature growth, recorded).
- `cd web && npm run build` → 17 pages; `npx vitest run` → **57 passed**;
  source-only commit.
- Full suite, first run: **1 failed, 3276 passed** — the failure was
  `test_profile_never_sync_holds_across_every_read_surface` pinning the
  exact profile field set (the guard doing its job on a contract change);
  the shape set grew `node` and the re-run is green:
  **3277 passed, 37 skipped**.

## Acceptance criteria — re-checked

- [x] Contract mirrored three ways + pinned — schema, Python, Swift moved
  in this commit; `test_primitive_contract.py` green (8), and the
  integration shape guard (the strictest mirror) updated + green (13).
- [x] `MeshRelayIntel.run_prompt` round-trips against the queue —
  `test_run_round_trips_through_the_queue` (payload verbatim both ways).
- [x] Non-live node ⇒ immediate named error (and NOTHING enqueued);
  expired ⇒ the deadline reason —
  `test_offline_node_refuses_immediately_by_name`,
  `test_deadline_expiry_surfaces_the_queue_reason`,
  `test_node_side_failure_surfaces_verbatim`.
- [x] The resolution matrix grew meshNode rows; every existing case passes
  unmodified — `test_effective_intel_adopts_mesh_node`,
  `test_mesh_profile_without_node_falls_back_with_reason`,
  `test_dictation_adopts_mesh_nodes_too`, plus the untouched HS-84 files.
- [x] `endpoint_egress(mesh)` shape pinned; existing badge wire shapes
  unchanged — `test_endpoint_egress_mesh_shape`,
  `test_run_egress_reports_mesh_for_profile_and_default`; route neighbors
  verbatim.

## Deviations from plan

- **The owner reversed the story's dictation scope mid-story** ("DIR could
  also be routed") and the code sided with him: DIR's endpoint leg was
  already advisory-constrained, so the relay rides the identical posture.
  Shipped in this story rather than deferred: `MeshRelayRuntime` + assembly
  + probe + doctor + tests. Latency needs no new machinery — the pipeline's
  budget rules and the DIR-R-003 cold-start cap govern a far edge exactly
  like a slow endpoint.
- The phase carries TWO schema bumps (v10 queue, v11 `profiles.node`),
  each with its DDL.
- Web badge renderers rode along (the story's egress bullet implied it);
  vitest + rebuild verified.

## Follow-ups

- HS-85-04 adds liveness to the pickers/models door and can now show the
  dictation Runtime tab's mesh state via the probe that already reports it.
- The HSM follow-up (Apple worker) should note the phone can now serve
  BOTH chat/intel and dictation rewrites.
