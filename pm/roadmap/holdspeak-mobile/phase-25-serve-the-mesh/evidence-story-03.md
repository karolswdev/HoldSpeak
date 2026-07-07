# Evidence — HSM-25-03 — The live proof + docs

- **Shipped:** 2026-07-07
- **Commit:** branch `hsm-25-03-live-proof-and-docs` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## The live walk (the phase's proof)

`scripts/walk_hsm25_live.py` (the standing regression rig) against the
REAL hub on `127.0.0.1:8765`, with the REAL app on the iPad simulator
serving as node `iPad` — its own active profile pointing at the `.43`
llama.cpp (the hub knows only the node name; the DEVICE knows the
provider). All four beats asserted in one run:

```
beat 1: '[PASS] Mesh edges: iPad: live (1s ago); walk-edge: offline (5636s ago)'
beat 2: profile profile_f69a858bde7d card reads 'live (1s ago)'
beat 3: ask THROUGH the device in 2.6s — egress {'scope': 'mesh', 'host':
        'iPad'}; output 'This answer serves as a concise, self-referential…'
beat 4: app killed; offline refusal in 0.00s → "mesh node 'iPad' is
        offline (last seen 16s ago)"
HSM-25-03 LIVE WALK: all four beats PROVEN — the phone served; the model
and the key never moved
```

Screenshots (committed): `hsm-25-03-walk-device-serving.png` (the device
Settings card serving), `hsm-25-03-walk-hub-card-live.png` (the hub's
/profiles card for "Phone Edge" reading live),
`hsm-25-03-walk-hub-card-offline.png` (the same card offline after the
kill). The offline beat's pinned bound (< 5s): **0.00s**, named — the
HS-85-04 pre-queue 400.

## What the walk caught (the rig's finds, fixed here)

1. **The models door shows profiles, not workers** — beat 1's first cut
   polled `/api/models` for the node before any meshNode profile existed;
   the honest liveness surface for a bare worker is doctor's "Mesh edges"
   (the rig now polls doctor, and asserts the models row appears the
   moment the profile is authored).
2. **The container-domain defaults trap, again** (the standing sim
   lesson): seeding the app's persisted profile via
   `simctl spawn defaults write` loses to the app's container plist, and
   writing the container plist directly loses to cfprefsd — two runs
   served with the migrated on-device profile (`localEngineUnavailable`)
   while the seed sat on disk. The fix is the demo-env house pattern:
   `HS_WALK_SERVE_URL`/`HS_WALK_SERVE_MODEL` seed an EPHEMERAL endpoint
   profile in `InferenceConfigStore.init` (simulator-only).
3. **The @Published-init recursion trap**: the first cut of that seed
   assigned `meshServeOn = true` late in `init` — a second assignment to
   an already-initialized `@Published` property goes through the SETTER,
   its didSet re-entered `InferenceConfigStore.shared` mid-`dispatch_once`
   via `MeshServeStore.refusal`, and the app died SIGTRAP at launch
   (crash report read, frame-exact). The seed now folds into the FIRST
   assignment, which fires no observer.

## Docs (the entry points)

- `docs/MODELS.md` §"The mesh edge" — the phone's consent sentence (one
  switch, Settings → "Serve my models to the mesh").
- `apple/README.md` — the "Serve the mesh" section (what serves, what
  never leaves, the named refusals).
- `apple/ARCHITECTURE.md` — the seam-in-reverse note (`MeshServeWorker`
  under "Inference — one seam, three modes").
- Guards: `uv run pytest -q tests/ -k "voice or drift or docs"` →
  **107 passed**.

## Verification artifacts

- The walk output above (beats 1–4, one run, cleanup verified — the hub
  profile deleted, the env seed dies with the process).
- `swift test` → **500 tests, 0 failures, 9 standing skips**.
- The hub ran merged main (post-#299) — the walk exercised the SHIPPED
  wire end to end: web route → relay queue → the app's worker → the
  device's `OpenAIEndpointProvider` → `.43` → back.

## Acceptance criteria — re-checked

- [x] Toggle ON ⇒ doctor + models door live under the device's mesh name
  (beats 1–2).
- [x] A meshNode profile naming the device runs a desk ask executing on
  the device's provider, egress naming the node (beat 3: 2.6s,
  `{scope: mesh, host: iPad}`).
- [x] Kill ⇒ offline + fast named refusal (beat 4: 0.00s < 5s).
- [x] Docs at the entry points; guards green.

## Deviations from plan

- The proof ran on the simulator against the real hub and the real `.43`
  provider — the wire and every code path are the device's own; a
  physical-device pass changes signing, not code (the HSM proof pattern;
  the owner can re-run the rig with the phone in hand any time).
- The dictation/meeting-intel beats were not repeated here — Phase 85's
  walk proved those lanes ride the same relay, and this phase changed
  nothing hub-side.

## Follow-ups

- Recorded interest (BACKLOG posture): background serving
  (BGProcessingTask / push-to-claim) only if the owner wants the phone
  serving pocketed; the honest default stays foreground-only.
