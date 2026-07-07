# Phase 85 — The Mesh Edge (run where the node is)

**Status:** OPEN (2/5).

**Last updated:** 2026-07-07 (HS-85-02 done — the meshNode profile kind
(contract mirrored schema/Python/Swift, `profiles.node` @ v11) +
`MeshRelayIntel` (immediate named refusal offline; bounded wait; queue
errors verbatim); DICTATION ADOPTS TOO (owner call, reversing the first
cut): `MeshRelayRuntime` rides the endpoint leg's advisory-constrained
posture over the relay; egress scope `mesh` end to end incl. both web
badge renderers).

## Why this phase exists

Owner direction (2026-07-07, the post-84 conversation): *"if a provider is
available on a mesh device, why can't we ask for the request to go through
that mesh edge? That way we use powerful models without any friction on
synchronizing."*

Phase 84 finished the profile layer: where intelligence runs is a named,
picked thing. But a profile still only works where its host can run it — an
`onDevice` profile is honest-n/a everywhere but its device, and an endpoint
profile needs each surface to hold its own key and reachability. The mesh
already knows *what* each node can run (`ModelManifestRecord`,
`holdspeak/db/models.py:528` — availability-only rows the devices push on
sync), and one relay direction already shipped (HSM-15-13: the iPad chats
with the desktop's model by sending the turn to the hub). This phase ships
the generalization: **a run goes to the node that hosts the provider. The
model and the key never move; the request does.**

The 2026-07-07 transport survey pinned the ground truth the design must
respect (receipts in the story files):

- Devices are mesh **clients**: sync is client-driven polling
  (`/api/sync/pull`/`push`, `web/routes/sync.py:392-488`); the only hub
  WebSocket is the page runtime bus. There is **no heartbeat, no last-seen,
  no paired-devices table** — today nothing knows whether a node is
  reachable.
- The pull-queue pattern is proven: `intel_jobs` with claim → run →
  complete/fail and `retry_at` exponential backoff
  (`db/intel.py:65-107`, `intel_queue.py:56-118`).
- The provider seam is tiny: a relay provider implements
  `run_prompt(system_prompt=, user_prompt=, temperature=, max_tokens=) ->
  str` and raises `MeetingIntelError` on failure (`intel/engine.py:306`,
  consumed at `web/routes/primitives/ask.py:380`).
- Phase 84's seams take the branch cleanly: `_apply_runtime_profile` (one
  adoption rule), `endpoint_egress` (one badge constructor), the "Runtime
  profiles" doctor check, `_runnable_models` (the models front door).

**One thesis:** a profile can name a NODE, and a run against it executes on
that node's own provider — relayed through the hub, refused fast when the
node is not there, and badged as exactly what happened.

## The design (pinned here so the stories don't fossilize five accidents)

- **Relay-through-hub, pull-only.** Mesh devices sleep, background, and sit
  behind NAT; nothing dials INTO a node. The hub owns a relay queue; a
  node's worker polls to claim, executes locally, posts the result back.
  The topology is the coder-queue/deferred-intel shape, not a new one.
- **Liveness is born from the worker's own polling.** A node is *live* iff
  its worker claimed-or-polled within the liveness window (pinned default:
  workers poll every ~3s; live = seen within 15s). Pickers and the models
  door show liveness, not existence; a run against a non-live node refuses
  fast and by name — never hangs.
- **Fail fast, never dangle.** Relay runs carry a deadline (pinned default:
  120s). Expired or unclaimed-past-deadline ⇒ the provider raises
  `MeetingIntelError` naming the node and why. The `retry_at` backoff
  pattern is for the queue's hygiene, not for silently retrying a user-felt
  run.
- **Relay jobs are hub-local rows, never a synced kind.** Prompts ride the
  relay wire between hub and the executing node only; `SYNC_KINDS` does not
  grow. (Deferred intel already stores transcripts in hub rows; same
  posture.)
- **The key rule gets stronger.** The executing node resolves the run
  through its OWN effective resolver (its engine, its profiles, its
  `HOLDSPEAK_PROFILE_<ID>_KEY` env) — no credential ever transits the mesh.
- **Egress says what actually happened.** A relayed run is neither `local`
  nor `cloud`: the wire badge is `{scope: "mesh", host: <node>}` via
  `endpoint_egress`, rendered "Mesh · <node>" on the web; the Swift mirror
  maps it onto the existing `EgressScope.mixed(node)`. Badges stay
  REPORTED, never inferred.
- **Serving is consent.** No node serves the mesh implicitly. The reference
  worker is an explicit command (`holdspeak mesh serve` — running it IS the
  consent, the Phase-52 macro posture); the Apple devices' worker + toggle
  is the HSM track's follow-up on this proven wire (the Phase-84 split,
  repeated deliberately).
- **v1 is request/response.** `run_prompt` is a blocking string call;
  streaming relay is a future contract change, not a rider.
- **Contract changes are mirrored or they don't ship.** The profile shape
  grows `node` (+ the `meshNode` kind): `profile.schema.json`, the Python
  record/repo/sync row, and the Swift `Contracts` mirror move together,
  pinned by the primitive-contract test.

## Exit criteria (evidence required)

- [ ] A live walk on the real hub: a mesh-node profile whose provider
  exists ONLY on the worker node runs an agent chat and a meeting-intel
  run from the hub's surfaces, badges reading `Mesh · <node>`, with the
  worker's log proving execution happened there
  (`scripts/walk_hs85_live.py` output + screenshots in evidence).
- [ ] The same walk kills the worker and proves fast, named refusal:
  the picker shows the node offline; a forced run fails inside the
  deadline with the node named — no hang.
- [ ] `holdspeak doctor` reports mesh workers (node, last-seen age) and
  the "Runtime profiles" check names a mesh-node resolution (tests +
  captured live).
- [ ] Contract mirrored three ways (JSON schema, Python, Swift) with the
  primitive-contract test green; `docs/api-surface.json` regenerated for
  the new relay routes.
- [ ] Every new queue/provider/CLI path unit-tested (claim/complete/fail,
  deadline expiry, liveness window, offline refusal); full suite green
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).
- [ ] Docs teach the feature honestly (what serves, what moves, what
  never moves); voice/drift guards green; BACKLOG row T updated.

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| HS-85-01 | The relay queue + the node wire | **done** (2026-07-07 — `mesh_relay_jobs`+`mesh_workers` @ schema v10; claim/complete/fail routes; 12 new tests, 79+7 neighbors/guards green) | [story-01](./story-01-relay-queue-and-node-wire.md) |
| HS-85-02 | The mesh profile kind + the relay provider | **done** (2026-07-07 — meshNode + `node` mirrored 3 ways @ v11; `MeshRelayIntel` + `MeshRelayRuntime` (DIR adopts, owner call); mesh egress to both web badges; 16 new tests) | [story-02](./story-02-mesh-profile-and-relay-provider.md) |
| HS-85-03 | `holdspeak mesh serve` — the edge worker | backlog | [story-03](./story-03-mesh-serve-worker.md) |
| HS-85-04 | Liveness on every surface + the honest doctor | backlog | [story-04](./story-04-liveness-surfaces-and-doctor.md) |
| HS-85-05 | Docs + the live walk | backlog | [story-05](./story-05-docs-and-the-live-walk.md) |

## Where we are

**2026-07-07 — HS-85-02 done: a node is pickable, and picking it relays.**
The contract moved as one: `kind: meshNode` + `node: string` on
`profile.schema.json`, `ProfileRecord`/repository/sync row/routes on the
hub (`profiles.node` column ⇒ schema v11, snapshot regenerated, +1 line),
and the Swift `RuntimeProfile` mirror — where the pre-edit read caught a
load-bearing detail: the `Kind` enum decode THROWS on unknown cases, so
without `case meshNode` a synced profile would have broken iPad sync.
`MeshRelayIntel` (`intel/mesh_relay.py`) speaks the standard
`run_prompt` interface: a node not seen within the liveness window refuses
IMMEDIATELY naming the node and its last-seen age (and enqueues NOTHING);
otherwise it enqueues on the HS-85-01 queue and waits bounded — node-side
failures and deadline expiries surface the queue's own named errors
verbatim. Adoption: `_apply_runtime_profile` resolves meshNode to a
node-shaped `EffectiveEndpoint`; both meeting-intel builders return the
relay provider; DICTATION refuses meshNode honestly (named fallback — the
DIR runtime speaks grammar-constrained calls, recorded scope decision).
Egress end to end: `endpoint_egress(node=)` ⇒ `{scope: "mesh", host}`,
`_run_egress` reports it for per-run AND config-adopted mesh runs, and both
web badge renderers (PersonaChat, AskPanel) wear `⇄ mesh · <node> ·
<model>`. MID-STORY OWNER CALL: the first cut had dictation refuse meshNode;
the owner overruled ("DIR could also be routed") and the code agreed — the
endpoint leg is already advisory-constrained, so `MeshRelayRuntime`
(`plugins/dictation/runtime_mesh_relay.py`) reuses its message/validation
helpers with the transport swapped to the relay queue; assembly builds it in
the same counting/cold-start delegate; the setup probe reports node
liveness; doctor names the node; latency degrades under the pipeline's
existing budget machinery, exactly like a slow endpoint. 16 new tests
(`test_mesh_relay_provider.py`); contract + queue + profile-resolution +
route + dictation neighbors green (three pre-existing stubs grew the `node`
kwarg); vitest 57; bundle rebuilt. Next: HS-85-03 — `holdspeak mesh serve`.
DICTATION runs mesh now, so the resolution matrix treats meshNode
identically across both pipelines.

Earlier — **2026-07-07 — HS-85-01 done: the spine exists.** `mesh_relay_jobs` +
`mesh_workers` land at schema v10 (bumped WITH the DDL — the v9 lesson;
snapshot regenerated with the house no-op-regex recipe, +23 additive lines
only). The repository (`db/mesh_relay.py`) carries the pinned lifecycle:
enqueue (120s default deadline) → per-node oldest-first claim (every poll
stamps `mesh_workers.last_seen` — the mesh's only heartbeat) →
complete/fail verbatim; deadlines enforce lazily on ANY read, and both
abandonment shapes fail with named reasons ("never claimed" /
"claimed but never completed"). A late completion is refused (409) so a
slow worker learns the truth. The wire is three token-guarded routes on the
mesh router (claim / complete / fail; enqueue deliberately has no route —
only the HS-85-02 provider writes jobs); api-surface at 247 routes. 12 new
tests (`test_mesh_relay_queue.py`: lifecycle, per-node isolation, ordering,
both deadline shapes, late-completion refusal, liveness aging, wire
validation, never-a-synced-kind); db/schema-policy/sync/api-surface
neighbors 79 + density guard 7, unmodified. Next: HS-85-02 — the meshNode
profile kind + the relay provider.

Earlier — **2026-07-07 — scaffolded.** Candidate T graduated same-day from
the post-84 conversation; the transport survey grounded the five stories in
the real seams (no device WS, no heartbeat — the worker's polling becomes
the liveness signal; the intel-jobs queue shape is the precedent;
`run_prompt` is the whole provider interface).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A relay run hangs a user surface when the node dies mid-run | high without care | deadline on every job; claim leases (a claimed-but-never-completed job fails at deadline, not never) | any test where a dead worker leaves a run pending past its deadline |
| Liveness flaps (a worker between polls reads as offline) | medium | liveness window ≥ 5× poll interval; pickers label "last seen Xs ago", never binary flicker | UI showing offline for a worker that completes a run seconds later |
| The relay provider blocks the ask route's event loop while polling | medium | the wait is bounded + coarse (0.5s steps) and runs where the engine already runs (threadpool via the existing seam) | route latency for NON-mesh runs regressing |
| Contract drift across the three mirrors | medium | one story owns the contract change; the primitive-contract test pins all three | schema/Swift/Python disagreeing in review |
| Scope creep into the Apple worker | medium | pinned split: Apple serving is the HSM follow-up on this proven wire | Swift files beyond the Contracts mirror in any diff |

## Decisions made (this phase)

- 2026-07-07 — Relay-through-hub with a pull worker; no inbound
  connections to nodes ever. — the transport survey: devices are clients,
  NAT/sleep is reality. Authority: owner's direction + the survey.
- 2026-07-07 — The reference worker is `holdspeak mesh serve` (any
  machine), and the Apple device worker is the HSM track's follow-up. —
  proves the wire live without Swift risk; repeats the Phase-84 split that
  worked.
- 2026-07-07 — Relay jobs are hub-local, never synced; prompts move only
  hub ⇄ executing node. — least data movement, matches deferred-intel
  posture.

## Decisions deferred

- **Streaming relay** (token-by-token over the wire). Trigger: chat
  surfaces feeling the blocking wait on big prompts. Default: bounded
  request/response.
- **Multi-hop / worker-to-worker relay** (node A asks node B without the
  hub). Not on the table; the hub is the one spine (Phase 72 canon).
- **Relay for transcription/whisper work** (only LLM `run_prompt` rides in
  v1). Trigger: a real need; the queue schema should not preclude it (a
  `task_kind` column from day one, single value for now).
