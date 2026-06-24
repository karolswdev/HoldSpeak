# HSM-15-02 — The Workbench targets the mesh (RUNS ON: Your Mac + real connectors)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog
- **Depends on:** the Workbench canvas + `ModelPref`/`NodeKind` (Phase 14 / HSM-14-15);
  `HTTPDesktopClient` (the desktop's capabilities); HSM-15-04 (the runner dispatches per target).
- **Owner:** unassigned

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

- [ ] **RUNS ON: Your Mac** — `ModelPref.mesh` (peer-named) selectable in the node inspector; a
      mesh-targeted node's intelligence executes on the desktop server. LAN-proven.
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
