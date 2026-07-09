# The State-Recipe Worklist

The induced world-states the 255 capabilities need, ranked by how many
capabilities wait on each. A UAT scenario opens by applying a recipe and
asserting its verify probe; this is the build list for HSU-1-02 and the
Phase-3 packs. The rule: **each recipe carries its own verify probe and is
idempotent** — applied twice, the probe passes both times and no duplicate
state exists (read back through the product's own routes, never the DB).

## Ranked by demand (capabilities that need it)

| # needing | Recipe | What it induces / its verify probe |
|---|---|---|
| 125 | `seeded-desk` | Notes, KB, recipes injected through public `/api/desk/*`; probe: seeded primitives read back, indistinguishable from user-made. **The workhorse — most packs stage this once.** |
| 48 | `mesh-node-alive` | A real `holdspeak mesh serve` worker in its own process group, `.43`-wired HOME; probe: doctor "Mesh edges" reads live, `/api/models` shows the node. |
| 37 | `meeting-just-ended-open-actions` | Import a **fresh timestamped** transcript → run intel; probe: ≥1 open action via the aftercare/history route. Real pipeline output, not a DB fake. |
| 29 | `fresh-desk` | Boot `golden-local`, isolated HOME, no seeds; probe: `/api/desk` empty, doctor green. |
| 20 | `agent-pane-awaiting-input` | `tmux new-session -d` + arm a consent grant on the pinned `%N`; probe: peek shows the prompt, grant live. |
| 20 | `proposal-pending-approval` | Drive an actuator to a pending proposal (off-by-default flow turned on for the run); probe: the proposal is queued, unexecuted, egress-safe. |
| 14 | `intel-endpoint-dead` | Boot `bad-endpoint` (dead port); probe: doctor names the dead endpoint, a forced run refuses <5s, no hang. |
| 14 | `first-run-no-model` | Boot `no-model`; probe: `/welcome` fronts, first-dictation path honest, the milestone flips. |
| 8 | `agent-session-live` | A live agent process in a pane (running, not just idle); probe: peek shows live output. |
| 8 | `model-installed-on-device` | A GGUF present on the iPad/iPhone (Files sideload / HF download). **Device-local — partly manual (see gaps).** |
| 7 | `hub-reachable-on-lan` | The hub bound LAN-wide with a device paired (host+port+token); probe: the device lists the hub's models. |
| 5 | `dictation-pipeline-enabled` | Pipeline on with ≥1 block; probe: a dry-run shows a routed, transformed result. |
| 5 | `mesh-node-just-died` | Mid-run: SIGINT the worker's group, wait out liveness; probe: `/api/models` row `live==false`, ask refuses <5s by name. |
| 5 | `belt-with-registered-rails-repo` | A rails repo registered on the belt; probe: the conveyor renders its stations from receipts. |
| 5 | `recording-in-progress` | A live capture running (hub or device); probe: the recorder reports active, transcript growing. |
| 4 | `seeded-activity-ledger` | Activity records present (browser history + enrichment); probe: the ledger and pre-briefing nudges render, source-cited. |
| 4 | `agent-pane-armed` | `agent-pane-awaiting-input` + an arming grant held; probe: the armed ring shows, a steer would be accepted. |
| 3 | `presence-and-mascot-enabled` | Both `presence.enabled` and `presence.mascot` on; probe: the HUD/dock renders (device-local for native HUD). |

## The long tail (1–2 capabilities each)

Grouped by shape so HSU-1-02 can build families, not one-offs:

- **Content shapes:** `seeded-project-kb`, `seeded-hs-context-repo`,
  `seeded-symbol-dictionary`, `seeded-desk-many-meetings`,
  `imported-meeting-no-artifacts`, `meeting-with-ink-notes`,
  `two-speaker-recording`, `learned-correction-taught`, `saved-agent-exists`.
- **File-on-disk shapes:** `recording-file-on-disk`, `transcript-file-on-disk`,
  `model-file-in-files-app` (device-local).
- **Steering/tmux shapes:** `agent-runaway`, `agent-pane-recycled`,
  `hand-started-tmux-pane`, `agent-session-live`, `multiple-agents-awaiting`,
  `remote-steer-node-alive`, `remote-steer-node-offline`.
- **Config/enable shapes:** `wake-word-enabled`, `wake-result-pending-preview`,
  `slack-webhook-configured`, `token-guarded-hub`, `endpoint-reachable`,
  `dictation-pipeline-enabled`, `mic-permission-granted`.
- **Device/mesh shapes:** `two-devices-paired`, `airplane-mode-on`,
  `model-installed-on-device`, `non-english-speaker`, `focused-mac-app`,
  `linux-or-macos-desktop`.
- **Meeting-state shapes:** `meeting-open`, `recording-in-progress`.

## The device-local gap

Recipes marked **device-local** (`model-installed-on-device`, `airplane-mode-on`,
`mic-permission-granted`, `model-file-in-files-app`, the native HUD) cannot be
induced by inducing *hub* state — the conductor's reach stops at the LAN. These
stay **partly hand-staged** in a device sitting's pre-flight (the HSM-16-06
press-play block), and the harness's honest posture is to *check* the
precondition and refuse the beat if unmet, never to fake it. Named here so
Phase 3 budgets the manual pre-flight into any pack that needs them.

## The canonical five decks feed the recipes

`golden-local`, `golden-43`, `bad-endpoint`, `no-model`, `mesh-node` (HSU-1-02).
Most recipes are `golden-local` + seeds; the failure recipes ride `bad-endpoint`
/ `no-model`; the mesh and intel recipes ride `golden-43`. At least one fully
local path (the `no-model`/`first-run` legs) needs no `.43`, so the rig demos
without the LAN.
