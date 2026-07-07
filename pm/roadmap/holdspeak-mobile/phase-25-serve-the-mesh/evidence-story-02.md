# Evidence — HSM-25-02 — Consent + the serving surface

- **Shipped:** 2026-07-07
- **Commit:** branch `hsm-25-01-swift-relay-worker` (PR to `main`; stacked
  after HSM-25-01 on the same branch line)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `apple/App/MeetingCapture/MeshServeStore.swift` — new: the worker's
  lifecycle owner (start/stop the `MeshServeWorker` task + a 2s stats
  poll into `@Published` fields); the at-the-door recursion guard
  (`refusal` names the reason when the active profile is
  meshNode/desktop); the node name is `DeviceLabel.current` — the SAME
  string the device's model manifests push, so hub pickers/doctor/badges
  agree.
- `apple/App/MeetingCapture/SketchDiagram.swift`
  (`InferenceConfigStore`) — `meshServeOn` (UserDefaults
  `hs.inf.meshserve`, **default false**; didSet drives the store) +
  `makeMeshServeProvider()` (the Phase-24 resolution with the per-job
  recursion guard throwing `MeshServeRefusal`).
- `apple/App/MeetingCapture/AppSettings.swift` — the consent card in
  WHERE INTELLIGENCE RUNS (the `diarizeCard` pattern): "Serve my models
  to the mesh" + the honest subline (the guard's named reason /
  "no hub paired" / "off" / "serving as iPad · N runs"); the toggle
  disables when unarmable.
- `apple/App/MeetingCaptureApp.swift` — launch re-arm (consent flag
  survives relaunch) + the `scenePhase` observer: serving follows the
  foreground, so the hub's liveness never lies about a suspended phone.
- `apple/App/MeetingCapture/RunsOnPicker.swift` — **the latent HS-85-02
  App break, caught by this story's build**: the chip-symbol `switch`
  over `RuntimeProfile.Kind` didn't cover the new `meshNode` case, and
  `swift test` never compiles the App target — the app would not have
  built for anyone since the contract mirror landed. Fixed (the mesh
  antenna glyph).

## Verification artifacts

- Simulator (iPad Pro 13-inch, real hub on `127.0.0.1:8765`, peer paired
  via `HS_DESKTOP_*`, the `HS_CLASSIC_HOME=1 HS_DEMO_SETTINGS=1` route):
  - `hsm-25-02-settings-toggle-off.png` — the card under the egress row,
    subline **"off"**, toggle off (the default: no node serves
    implicitly).
  - `hsm-25-02-settings-serving.png` — consent on: subline
    **"serving as iPad · 0 runs"**, toggle on.
- **The wire is real, not seeded:** with the toggle on, the REAL hub's
  doctor read
  `[PASS] Mesh edges: iPad: live (2s ago); walk-edge: offline (3868s ago)`
  — the simulator's worker genuinely stamping liveness through
  `POST /api/mesh/relay/claim` on the desktop's own relay queue (the
  walk-edge row is Phase 85's retired walk worker, honestly offline).
- Build: `gen-meeting-capture.rb` → xcodebuild for the booted simulator →
  **BUILD SUCCEEDED** (the first build FAILED on the RunsOnPicker switch —
  the find above).
- Package tests unaffected (`swift test` target set excludes App); the
  worker itself remains covered by HSM-25-01's 7.

## Acceptance criteria — re-checked

- [x] The consent toggle (off by default) starts/stops the worker — the
  didSet → `MeshServeStore.apply`; persisted flag re-arms on launch.
- [x] App background/kill stops it — the `scenePhase` observer (leaving
  `.active` cancels; returning re-arms only if consented). Kill-proof:
  the hub's liveness window ages the node out with no cleanup call, by
  design (polling IS liveness).
- [x] The serving state renders on Settings — both screenshots.
- [x] The at-the-door guard refuses by name — `refusal` disables the
  toggle and wears the reason as the subline (same string the per-job
  guard posts).

## Deviations from plan

- The store polls the worker's stats every 2s instead of a callback —
  smaller seam, and the card only needs display freshness.
- The RunsOnPicker fix rode along (it blocked the App build entirely;
  recorded as a phase find — the kind-add checklist gains "build the
  App, not just swift test").

## Follow-ups

- HSM-25-03: the live walk (a desk ask on the Mac executing through the
  device's provider; kill → offline named refusal) + entry-point docs.
