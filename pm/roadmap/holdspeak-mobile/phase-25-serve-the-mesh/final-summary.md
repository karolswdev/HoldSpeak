# Phase 25 — Serve the Mesh: final summary

- **Phase opened:** 2026-07-07 (the recorded handoff from desktop
  phase-85, closed the same day)
- **Phase closed:** 2026-07-07 (scaffolded and shipped the same day)
- **Stories shipped:** 3/3

## Goal — was it met?

*"Flip one toggle on the phone, and a desk ask on the Mac executes on the
phone's own model — badged honestly, refused fast and by name the moment
the phone stops serving."* **Yes, proven live.** The walk's beat 3: an
ask against a meshNode profile naming `iPad` executed through the device
in 2.6s wearing egress `{scope: mesh, host: iPad}` — hub → relay queue →
the app's worker → the device's own provider → back. Beat 4: the app
killed, the node offline everywhere, a forced run refused in 0.00s naming
the node.

## What the phase shipped

- **HSM-25-01 — the Swift relay worker:** `MeshRelayJob` + claim/
  complete/fail on a new `HTTPDesktopClient+MeshServe` extension (Bearer
  discipline; a late completion is `.http(409)`, logged once, never
  retried); `MeshServeWorker` (an actor) — the Python reference worker
  translated: claim → execute on THIS device's own `ILLMProvider` →
  report verbatim; jittered ~3s cadence; 1s→30s backoff; cancellation
  honors the in-flight job; the recursion guard's named refusal; the
  empty-answer guard. 7 URLProtocol-stubbed tests.
- **HSM-25-02 — consent + the serving surface:** `meshServeOn` (default
  OFF — no node serves implicitly) drives `MeshServeStore`, the worker's
  lifecycle owner; serving follows the foreground (`scenePhase`); the
  Settings card wears the state as its subline (named refusal / "no hub
  paired" / "off" / "serving as iPad · N runs"). Sim-proven on the real
  hub (doctor: `iPad: live (2s ago)`).
- **HSM-25-03 — the live proof + docs:** the four-beat walk
  (`scripts/walk_hsm25_live.py`, the standing rig) + entry-point docs
  (apple/README "Serve the mesh", ARCHITECTURE's seam-in-reverse note,
  MODELS.md's phone-consent sentence).

## The finds of the phase

1. **The App target is a build gate nobody was running:** RunsOnPicker's
   `Kind` switch missed HS-85-02's `meshNode` case — the App had not
   compiled since the contract mirror landed, and `swift test` never
   builds it. The kind-add checklist gains: BUILD THE APP.
2. **The container-domain defaults trap (now twice-learned):** seeding an
   app's persisted UserDefaults from outside loses — user-level writes
   are shadowed by the container plist, and direct container-plist writes
   lose to cfprefsd. The house pattern is env-var seeds
   (`HS_WALK_SERVE_URL`, simulator-only, ephemeral).
3. **The @Published-init recursion SIGTRAP:** a SECOND assignment to a
   `@Published` property inside `init` goes through the setter and fires
   `didSet`; ours re-entered `InferenceConfigStore.shared` mid-
   `dispatch_once` via `MeshServeStore` and killed the app at launch.
   Seeds fold into the FIRST assignment (which fires no observer).
4. **Liveness surfaces differ by design:** the models door shows
   PROFILES (with liveness); a bare worker with no profile shows only in
   doctor's "Mesh edges". The rig polls the right surface per beat.

## Stories shipped

| ID | Title | PR |
|----|-------|----|
| HSM-25-01 | The Swift relay worker on the provider seam | #299 |
| HSM-25-02 | Consent + the serving surface | #299 |
| HSM-25-03 | The live proof + docs | the closing PR |

(The phase scaffold merged as #298. #299 also carried the api-surface
manifest regen — the relay routes gained their `ios` consumer.)

## Decisions

- Foreground-only serving in v1; background modes are a deliberate
  non-goal (a suspended worker must not look live). Recorded interest:
  BGProcessingTask / push-to-claim only on real owner want.
- The fold onto `complete(prompt:)` is the recorded seam limit —
  temperature/max_tokens ride the job and wait for the protocol to grow.
- The node name is `DeviceLabel.current` — the manifest's node string, so
  every hub surface names one thing.

## Numbers

Two PRs + the scaffold; 7 new Swift tests (`swift test` 500/0 at close);
five committed screenshots; one standing rig (`walk_hsm25_live.py`);
guards 107; the api-surface manifest +3 `ios` consumers.

## Handoff

- The wire now has TWO worker implementations (Python `mesh serve`,
  Swift `MeshServeWorker`) speaking the same three routes — any future
  transport change must move both (plus the walk rigs).
- A physical-device pass of the rig is a signing exercise, not a code
  one — run it whenever the phone is in hand (the sim exercised every
  code path against the real hub and the real `.43`).
- Ops notes: the sim build regenerates via `gen-meeting-capture.rb`
  before EVERY App edit; the walk needs the hub on
  `HOLDSPEAK_WEB_PORT=8765` and the app installed on the booted sim.
