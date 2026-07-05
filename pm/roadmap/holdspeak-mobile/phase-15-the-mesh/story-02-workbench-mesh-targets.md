# HSM-15-02 — The Workbench targets the mesh (RUNS ON: Your Mac + real connectors)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** in-progress (2026-07-05 — **survey-corrected**; see "The 2026-07-05 rescope"
  below. Much of the original design shipped elsewhere; the genuinely-open heart — the
  per-step dispatch — is the active build.)
- **Depends on:** the Workbench canvas + `ModelPref`/`NodeKind` (Phase 14 / HSM-14-15);
  `HTTPDesktopClient` (the desktop's capabilities); HSM-15-04 (the runner dispatches per target).
- **Owner:** agent (Fable)

## The 2026-07-05 rescope (the resume survey, code-read)

Pre-paid while the phase slept:

- **The graph travels and runs on the hub whole** — Phase 22: `lowerToBlueprint()` →
  `graph_json` sync → the hub's `workflow_graph.py` linearizer runs it (22-04 proved the
  iPad-authored graph on the hub with real `.43` intel).
- **Per-node `runs_on` + `failure_policy` ride the wire** — 22-01 (`BPRunsOn`, the exact
  raw strings the hub's `_RUN_TARGETS` accepts; unset stays byte-identical "auto").
- **The run-target pick is informed, not blind** — 16-08: the model MANIFEST syncs and the
  "where should it run?" sheet names the hub's actual model.
- **Device-initiated proposals through the desktop connectors** — the desk actuator relay
  (`api/desk/actuators/*`, Phase 38/72): the iPad proposes, the hub's one 5-gate executor
  acts after approval.
- **The generic "run a capability on your Mac" RPC this story's grounding asked for now
  exists** — `POST /api/ask` (HSM-16-04): prompt + optional context in, output + honest
  per-run egress out, persists nothing. The dispatch seam consumes it as-is.

Genuinely open (the story's remaining substance):

1. **Per-STEP dispatch — DONE 2026-07-05 (the heart).** "Your Mac" joined the node
   inspector's RUNS ON (`ModelPref.desktop`, glyph + honest hint) and `BPRunsOn.desktop`
   joined the wire (the hub's `_RUN_TARGETS` recognises it and preserves the pin in the
   run trail; an OLDER hub folds it to "auto" — same semantics, wire-safe by
   construction). The runner dispatches a pinned step to the paired peer over
   `POST /api/ask` under the SAME retry loop + IF-UNREACHABLE policy, `StepOutcome.ranOn`
   is honest (a fallback reports on-device), and the HUD job label states the pin and
   settles to where it actually ran. Proven end to end: the Simulator's pinned step
   landed on a REAL local hub (prompt receipts) — see `evidence-story-04.md` (the runner
   story closed with this slice) + `screenshots/hsm-15-02-mesh-run.png` /
   `hsm-15-02-runson-inspector.png`. Suites: Swift 476/9/0, hub unit green.
2. **Connector sinks from a canvas run** — a Slack/GitHub sink node still never routes
   through the desktop's propose→approve→execute from a run (reachable → propose via the
   desk relay; air-gapped → honest local draft + badge).
3. **Mesh source** — a desktop meeting selectable as a workflow source.
4. **Workflow-level default target + failure policy** (nodes inherit/override).

## Grounding (2026-06-22)

The desktop already runs the intelligence (`intel/engine.py` `MeetingIntel`; the dictation runtime;
the actuators) and already has the **one approval/egress contract** (`ActuatorProposal` +
`ActuatorExecutor`, Slack/GitHub/webhook connectors via `web/routes/meetings.py`). What is **missing**
is a generic **"run a capability on your Mac and return the result" RPC** — capabilities are reachable
only through their specific domain routes (meetings / dictation / actuators), not a uniform
node-execution endpoint. So the new desktop work for this story is that small RPC (HSM-15-04 consumes
it); the connector-sink routing **reuses** the existing actuator path, it does not rebuild it.

## Vision

"RUNS ON" today means *where the model runs* (Auto / On-device / Endpoint). In the mesh it means
*where in your mesh a step runs* — and **"Your Mac" is a capability target**, not just an
inference URL. The desktop hub has things the iPad alone does not: the big models, and the real
**propose→approve→execute connectors** (Slack, GitHub, webhook). Targeting the Mac unlocks steps
the iPad cannot do on its own. The visual language becomes a **mesh program**.

## The design

- **A third RUNS-ON target: "Your Mac."** `ModelPref` gains `.mesh` (label: the paired peer's
  name). A node set to Your Mac runs its intelligence on the desktop server (its model, its
  context, your paid-for memory) over the existing seam.
- **Sink nodes route through the desktop's real connectors.** A `Slack` (or `GitHub`) output node,
  when the workflow can reach the Mac, **does not** draft-only — it rides the desktop's
  `propose→approve→execute` actuator path (the repo's production connector), with the egress badge
  and an explicit approval. On-device-only (air-gapped) → it degrades honestly to a local draft +
  the egress badge, never a silent send.
- **Mesh-aware sources.** A workflow source can be a **desktop meeting** (the hub's library), not
  only an on-device one — so a graph wired on the iPad can run over work captured on the Mac.
- **Per-workflow defaults (owner's call).** The failure policy + default target are a **workflow**
  setting (a node inherits or overrides) — see HSM-15-04. The Workbench-settings surface owns the
  workflow default; the node inspector shows "Inherit from workflow" as the default node state.

## Acceptance criteria

- [x] **RUNS ON: Your Mac** — selectable in the node inspector (`ModelPref.desktop`; the HUD
      label names the paired peer); a mesh-targeted node's intelligence executes on the
      desktop server (proven against a real local hub; the cabled-iPad LAN beat joins the
      phase's owner queue).
- [ ] **Connector sinks** — a Slack/GitHub sink routes through the desktop's real
      propose→approve→execute path when the Mac is reachable; air-gapped → honest local draft +
      egress badge. LAN-proven + Simulator-shot.
- [ ] **Mesh source** — a desktop meeting is selectable as a workflow source.
- [ ] **Workflow-level policy** — the default target + failure policy live at the workflow; nodes
      inherit/override; the inspector reflects it.

## Build plan

1. `ModelPref.mesh` + peer-named label; node inspector option.
2. Workflow-level default target + failure policy (the Workbench-settings surface); node "Inherit".
3. Sink-node routing: reachable Mac → desktop connector (approval + egress); air-gapped → draft.
4. Mesh source (desktop meeting) selection.
5. Simulator shots + a LAN proof (a mesh-targeted node runs on the Mac; a sink proposes through the
   real connector).

## Test plan

- Host: `ModelPref` resolution + workflow→node policy inheritance unit-tested; sink routing decision
  (reachable → connector, air-gapped → draft) unit-tested with a fake `DesktopClient`.
- LAN: a node set to Your Mac executes on the desktop; a Slack sink proposes through the real path.
- Simulator: the inspector showing Your Mac + the connector-sink approval.

## Notes

- This is where the runner (HSM-15-04) earns its "one runner for the mesh" framing: dispatch is a
  per-node target decision, not a separate code path.
- Egress honesty is load-bearing: a sink that *could* send must always show the badge and require
  the nod — air-gapped runs degrade to a draft, never a silent no-op-that-looks-sent.
