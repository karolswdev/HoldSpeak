# HSU-2-04 — Inventory sweep: the desk, the mesh, the agents

- **Project:** holdspeak-uat
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HSU-2-01
- **Owner:** unassigned

## Problem

The newest and fastest-moving territory: the desk as the front door,
the mesh as where intelligence runs, the steering/factory spine as
first-class agent manipulation — plus how work *hands off between
mesh participants* (a run relayed to the node that hosts the
provider, a device serving its models, the desk steering a session on
another machine, knowledge grounding a run anywhere). This is the
material the owner called out by name, and the least-inventoried.

## Scope

- In: the domain inventoried into `uat/features.yaml` — at minimum
  the territory of: desk primitives + zones + edit-in-place +
  filing/diving, the workbench/blueprints (authored on any surface,
  run on the hub), ask/grounding/threads (desk objects + rails as
  receipts), the conveyor and mission control, runtime profiles ("one
  runtime": where intelligence runs, per run, honestly badged), the
  mesh edge (relay queue, pull workers, node liveness, honest offline
  refusal), device-as-edge (the iPad/iPhone serving models to the
  mesh, per-device consent), **handoff across mesh participants**
  (the cross-surface arcs: author here, run there, result everywhere
  — enumerate each arc as its own row), the knowledge base / `.hs`
  context and its grounding reach, steering (peek → arm → steer →
  keys → panes → cross-machine relay), the factory (spawn/rename/
  kill), the delivery belt + rails grounding + the rails observer,
  presence/Qlippy, and the sync spine + contracts that hold the
  parity set together. Row format, method, and verification
  discipline identical to HSU-2-02.
- Out: ranking (HSU-2-05), scenario authoring (Phase 3), building
  recipes (steering/factory scenarios will need tmux-shaped recipes —
  worklist rows, not builds), fixing anything found, remote-machine
  nodes (deferred-decision default stands).

## Acceptance criteria

- [ ] Every HS/HSM phase whose subject is in this domain is mapped to
      ≥1 ledger row or explicitly marked internal — checked by a
      domain phase-list in the story evidence.
- [ ] Zero `unknown` surface cells remain in this domain; contested
      cells carry verification notes/screenshots.
- [ ] The handoff arcs are enumerated as explicit rows (each names
      its from-surface, via, and to-surface), not folded into
      component rows.
- [ ] Consent-spine capabilities (steering, factory kill, actuators,
      device serve) carry their gate into the scenario hints — the
      recipe induces the *armed* state through the real consent flow,
      never around it.
- [ ] Every row names its required state recipe(s); the tmux/agent-
      session-shaped recipe needs are in the worklist.
- [ ] Ledger validation green.

## Test plan

- Unit: ledger validation suite green on the grown file.
- Integration: n/a.
- Manual / device: the surface-verification pass, incl. at least one
  real handoff arc walked live (e.g. authored on the iPad, run on the
  hub, result read on the web desk).

## Notes / open questions

- **Starting map:** [`directory/30-desk-mesh-agents.md`](./directory/30-desk-mesh-agents.md)
  — 113 capabilities pre-seeded by the sweep (the largest domain), with
  the handoff arcs already enumerated as their own rows
  (`mesh.handoff.*`, `steering.cross_machine`, `sync.*`,
  `agents.*` companion). This story verifies the map on device — the
  cross-machine and two-device arcs need a real second machine and a
  paired phone — and reconciles it into the ledger.
- This domain moves weekly (Phases 86–90 were one week); the sweep
  records the *current* truth and the ledger's phase column is the
  audit trail for what arrived after.
