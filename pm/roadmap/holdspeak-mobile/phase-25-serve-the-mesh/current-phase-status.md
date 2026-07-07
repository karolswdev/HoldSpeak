# Phase 25 — Serve the Mesh (the phone becomes an edge)

**Status:** CLOSED (3/3, 2026-07-07 — scaffolded and shipped the same
day). See [final-summary.md](./final-summary.md).

**Last updated:** 2026-07-07 (HSM-25-03 done — the four-beat live walk on
the real hub: an ask THROUGH the device in 2.6s wearing egress
`{scope: mesh, host: iPad}`; kill → offline everywhere, refusal 0.00s
named. The rig's finds fixed: the models-door-vs-doctor liveness surface,
the container-domain defaults trap (the env-seed house pattern instead),
and a @Published-init recursion SIGTRAP (crash-report-diagnosed). Docs at
the entry points; guards 107; `swift test` 500/0.)

## Why this phase exists

Phase 85 shipped the generalization: a `meshNode` profile relays a run
through the hub to the node hosting the provider — the model and the key
never move; the request does. Any Mac/Linux box already serves with one
command. The devices the owner actually carries — the iPhone with its
on-device GGUF, the iPad — cannot serve yet, and they are the whole point
("use powerful models without any friction on synchronizing", the owner's
post-84 direction). The Swift side already has every seam: the
`ILLMProvider` protocol (`Providers.swift:22`), the `meshNode` contract
mirror (`Primitives.swift:257`, HS-85-02), the Bearer-token hub client
(`HTTPDesktopClient.swift:68`), and the foregrounded polling-loop
precedent (`QueuePresence.swift:104`). There is NO Swift worker today
(surveyed 2026-07-07) — a green field on proven seams.

**One thesis:** flip one toggle on the phone, and a desk ask on the Mac
executes on the phone's own model — badged honestly, refused fast and by
name the moment the phone stops serving.

## The design (pinned)

- **The HS-85 posture, verbatim.** Pull-only (the worker claims from the
  hub; nothing dials into the phone); polling IS liveness (the hub's
  15s window over the ~3s claim cadence); serving IS consent — the toggle
  is off by default, and stopping (toggle off, app backgrounded, app
  killed) reads offline hub-side within seconds, refusals named.
- **Foreground-only in v1.** The worker runs while the app is open —
  the `QueuePresence` task-loop pattern, cancelled on scenePhase leaving
  active. iOS background execution is a deliberate NON-goal (the honest
  posture: a phone that OS-suspends mid-job must not look live); the
  claim deadline (120s) already fails an interrupted job by name.
- **The device's OWN provider, resolved the Phase-24 way.** The worker
  executes through `InferenceConfigStore`'s active profile →
  `InferenceProviderFactory` → `ILLMProvider` — its model file, its
  Keychain key. No credential ever rides the relay (the HS-85 key rule).
- **The fold is explicit.** `ILLMProvider.complete(prompt:)` takes one
  string; the relay job carries system/user/temperature/max_tokens. The
  worker folds system + user deterministically (the mirror of the
  desktop's `_chat_completion_text` adapter) and ignores what the seam
  cannot express in v1 — recorded, not smuggled.
- **The recursion guard travels.** A device whose active profile is
  itself `meshNode` (or `desktop`) refuses to serve — by name, at
  toggle-time AND per-job, exactly like the Python worker's guard.
- **The node name is the device's mesh name** — the same name the
  device's model manifest pushes on sync, so pickers, doctor, and badges
  all agree on one string.
- **Serving is visible, not silent.** While the toggle is on, the
  Settings surface states it plainly: node name, live state, jobs served
  this session, last claim age. No prose beyond that (the no-prose rule).

## Exit criteria (evidence required)

- [x] `swift test` covers the worker loop against a stubbed hub
  (URLProtocol): claim→execute→complete verbatim; node-side failure →
  fail verbatim; hub outage → backoff without crash; cancel stops
  cleanly; the recursion guard refuses by name; the token rides as
  Bearer and never appears in any label —
  `MeshServeWorkerTests` 7/7 ([evidence-01](./evidence-story-01.md));
  full suite 500/0 at close.
- [x] The consent toggle (off by default) starts/stops the worker; app
  background/kill stops it; the serving state renders on Settings —
  [evidence-02](./evidence-story-02.md): two screenshots + the live
  doctor line; scenePhase observer for background; kill needs no cleanup
  by design (polling IS liveness), proven by the walk's beat 4.
- [x] The live proof on real metal: an ask against a meshNode profile
  naming the DEVICE executed on the device's own provider in 2.6s,
  egress `{scope: mesh, host: iPad}`; doctor listed the device live;
  kill → offline + 0.00s named refusal
  ([evidence-03](./evidence-story-03.md); three walk screenshots).
- [x] Docs teach it at the entry points (apple/README "Serve the mesh",
  the ARCHITECTURE seam-in-reverse note, MODELS.md's phone-consent
  sentence); guards **107 passed**.

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| HSM-25-01 | The Swift relay worker on the provider seam | **done** (2026-07-07 — worker + wire + 7 tests; `swift test` 500/0) | [story-01](./story-01-swift-relay-worker.md) |
| HSM-25-02 | Consent + the serving surface | **done** (2026-07-07 — toggle + state line, sim-proven on the real hub's doctor; the RunsOnPicker meshNode find) | [story-02](./story-02-consent-and-serving-surface.md) |
| HSM-25-03 | The live proof + docs | **done** (2026-07-07 — four beats live; 3 rig finds fixed; docs + guards 107) | [story-03](./story-03-live-proof-and-docs.md) |

## Where we are

**2026-07-07 — HSM-25-03 done: the phone served, live, and the phase is
CLOSED.** The four-beat walk (`scripts/walk_hsm25_live.py`, the standing
rig) ran the real app on the iPad simulator against the REAL hub: doctor
read `iPad: live (1s ago)`; the hub-side "Phone Edge" meshNode profile's
card read live; an ask against it executed THROUGH the device in **2.6s**
wearing egress `{scope: mesh, host: iPad}` (hub → relay queue → the app's
worker → the device's own endpoint provider → .43 → back); killing the
app read offline and a forced run refused in **0.00s**, named. Three rig
finds fixed along the way: beat 1 must poll doctor (the models door shows
PROFILES, not bare workers); seeding the app's persisted defaults from
outside loses to the container domain + cfprefsd — the env-seed house
pattern (`HS_WALK_SERVE_URL`, simulator-only, ephemeral) replaced it; and
the seed's first cut hit a @Published-init recursion SIGTRAP (a second
assignment in `init` goes through the setter — crash report read,
frame-exact; the seed folds into the FIRST assignment). Docs at the entry
points (apple/README, ARCHITECTURE, MODELS.md); guards 107; `swift test`
500/0. The phase is CLOSED 3/3 — see
[final-summary.md](./final-summary.md).

Earlier — **2026-07-07 — HSM-25-02 done: one switch, and the phone is an edge.**
`meshServeOn` (UserDefaults, default FALSE — no node serves implicitly)
drives `MeshServeStore`, the worker's lifecycle owner: toggle on →
`MeshServeWorker` serves as `DeviceLabel.current` (the SAME node string
the model manifests push, so every hub surface names one thing); toggle
off / scenePhase leaving `.active` / app death → the loop cancels and
the hub's liveness window ages the node out with NO cleanup call
(polling IS liveness). The Settings card wears the whole story as its
subline — the at-the-door guard's named refusal, "no hub paired", "off",
or "serving as iPad · N runs" — and the toggle disables when unarmable.
Sim-proven against the REAL hub: doctor read
`Mesh edges: iPad: live (2s ago)` while the card read `serving as iPad ·
0 runs` (two committed screenshots). The build caught a LATENT HS-85-02
break: RunsOnPicker's Kind switch missed `meshNode` — the App would not
have compiled for anyone since the mirror landed, and `swift test`
cannot see it (the kind-add checklist gains: BUILD THE APP). Next:
HSM-25-03 — the live walk (a desk ask executing through the device) +
docs.

Earlier — **2026-07-07 — HSM-25-01 done: the loop exists in Swift.**
`MeshRelayJob` + the three wire calls ride a new
`HTTPDesktopClient+MeshServe` extension (the conflict rule; Bearer
discipline identical to the rest of the client; a late completion is
`.http(409)` — logged once, never retried). `MeshServeWorker` (an actor)
translates the Python loop: claim → execute on THIS device's own provider
(built lazily from the injected factory) → report verbatim → claim again
immediately while work exists; idle sleeps jittered ~3s; outages back off
1s→30s; cancellation honored between polls so an in-flight job always
finishes. `MeshServeRefusal` carries the recursion guard's named reason
for the 25-02 factory; an EMPTY provider answer fails by name (found
writing the tests — the hub refuses empty results, so a blank answer
would otherwise dangle to its deadline). The fold onto
`complete(prompt:)` is the recorded v1 limit. 7 new tests
(request-scripted URLProtocol stub + a sleep recorder that cancels the
loop — deterministic, no waits); full `swift test` 500/0. Next:
HSM-25-02 — consent + the serving surface.

Earlier — **2026-07-07 — scaffolded.** The desktop wire closed the same
day (phase-85, PR #297) with the walk-find lessons recorded in its final
summary; the Swift seam survey (receipts above) confirmed a green field.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| iOS suspends the app mid-job and the hub waits the full deadline | medium | foreground-only posture + the 120s deadline fails the job by name; scenePhase cancel stamps nothing false | a hub-side job hanging past its deadline with the phone asleep |
| The on-device model is too slow for the 120s deadline on big prompts | medium | the deadline error is named and honest; the picker shows the device model's name so the caller chose it knowingly | walk runs that routinely expire |
| The fold loses sampling params silently | low | recorded v1 limit here + in the story; the job's temperature/max_tokens are honored where the provider grows them later | reviewer surprise at the fold |
| Serving drains battery unnoticed | low | the toggle is loud on Settings while on; foreground-only bounds it | owner complaint |

## Decisions made (this phase)

- 2026-07-07 — Foreground-only serving in v1; background modes are a
  deliberate non-goal. — honesty over reach: a suspended worker must not
  look live. Authority: the HS-85 liveness posture.
- 2026-07-07 — The worker folds system+user onto `complete(prompt:)`
  rather than growing the provider protocol in this phase. — smallest
  honest change; the protocol grows params when a real need lands.

## Decisions deferred

- **Background serving** (BGProcessingTask / push-to-claim). Trigger: the
  owner actually wanting the phone to serve pocketed. Default: no.
- **Serving the iPad and iPhone simultaneously under distinct node
  names.** Already works by construction (per-device names); a walk rider
  only if the owner asks.
