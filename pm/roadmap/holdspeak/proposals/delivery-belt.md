# Proposal — The Delivery Belt (the factory floor)

> Status: **draft proposal** (BACKLOG candidate U, expanded per owner
> direction 2026-07-07). Author-facing RFC, not yet a roadmap phase. Grounds
> in the desk primitive framework, the Workbench canvas (Phase 69) + the
> Blueprints vision, the actuator system (Phases 37/38/61), the
> coder-companion presence queue, the run-story frames (Phase 74), and the
> delivery-workbench (pmo-roadmap) package.

## 1. The pitch

Delivery-workbench has governed 110+ phases across two tracks, but its agent
integration is markdown-as-database and its human surface is files in a repo.
The owner's direction (verbatim): *"incredibly well integrated into the UI/UX
philosophy of Desk OS on iOS, and of course, its Web Equivalent… it's almost
like a conveyor belt builder with rich interaction affordances"* — and, on
expansion: an **app of DeskOS** where you can *start a repository scaffolded
with the delivery framework, have an AI agent scaffold it properly from your
input, treat these as desk primitives but also as separate entities, and
control a lot of those processes alongside*.

So: not a viewer — a **factory floor**.

- **Each project is a BELT.** Stories ride it as objects through STATIONS:
  candidate → scaffold → story → evidence → contract gate → PR → CI → close.
  The cadence already IS this pipeline; the belt makes it tangible.
- **"New Project" is a desk act.** Name it, speak the intent (voice on
  inputs), pick the agent — an agent (Claude Code, codex, any paired runner)
  creates the repo, installs delivery-workbench, runs the session intake, and
  scaffolds the roadmap from the user's words. The result lands on the desk
  as a new belt.
- **A project is a primitive AND an entity.** On the desk it files into
  zones, ropes to notes/meetings, opens into its belt (filed objects stay
  openable — the standing rule). Underneath it remains a real, separate repo
  with its own agents, PRs, and gates.
- **Agents are workers you place at stations.** Dispatching one at a story is
  visible (the presence/coder-queue lane already models a waiting/working
  agent); its run-story frames stream at the station; its result arrives as
  the station's receipt.
- **Portfolio control.** Many belts side by side; a glance says which are
  moving, which are stalled and WHY (the refusing station wears its reason).

## 2. The two non-negotiables

1. **Receipts, never a parallel truth.** The belt RENDERS from what already
   proves the work: git history, PR/CI conclusions, the phase files, evidence
   docs, the contract hook's output. No belt-side database of claimed
   progress. If the desk and the repo could ever disagree, the design is
   wrong.
2. **Every consequential act is an actuator.** Creating a repo, dispatching
   an agent, approving a gate, merging — propose → approve → execute, per
   action, off by default, audited (the Phase 37/38 grammar; Send-to-Slack's
   production posture). The Belt is the factory-shaped SURFACE of the
   actuator system, not a new privilege path.

## 3. Architecture sketch (what it lands on)

- **Substrate (pmo-roadmap repo):** a machine-readable state layer the
  markdown renders FROM — phase/story/status/evidence as structured data
  (front-matter or a generated `state.json` emitted by a `dw` CLI), plus
  `dw` verbs for the cadence (`story done`, `phase close`, `cadence check`
  linting the surfaces into agreement). The Belt is the flagship consumer
  that forces this substrate honest; agents get it as a by-product (the end
  of six-file prose surgery per shipping commit).
- **Hub (holdspeak):** a projects registry (path/remote per repo) + read
  routes that assemble a belt from receipts (`dw state` + `gh pr/checks` +
  the evidence tree); actuator routes for the gated acts (scaffold, dispatch,
  approve, merge). The agent-dispatch actuator drives the same seams the
  coder-companion already watches.
- **Web desk:** the Belt surface — nearest kin to the `/workbench` node
  canvas; a belt per project, stations as nodes, story objects moving, CI as
  station lights, hook refusals as in-world chips, evidence opening in place
  (no modals), the working agent rendered at its station from run frames.
- **DeskOS (HSM track):** the diorama Belt — the craft pass that sets the
  interaction bar (grab a story object, walk it to a station, the nod). The
  same contract shapes sync; layout stays local (the four-class taxonomy).

## 4. Slices (each its own phase; no mega-bundle)

- **B0 — The substrate** (pmo-roadmap): `dw state` + cadence verbs +
  `cadence check`, dogfooded on HoldSpeak's own roadmap. Exit: this repo's
  phase paperwork updates via verbs, and the linter catches a deliberately
  desynced surface.
- **B1 — One belt, read-only** (hub + web desk): render THIS repo's live
  phase from receipts — stations, lights, openable evidence, the agent lane.
  Exit: a live walk where a real story moves station-to-station during a
  real shipping commit, with zero belt-side writes.
- **B2 — The nod** (hub + web desk): the gated acts — approve/merge via
  `gh`, dispatch-an-agent as an actuator, stall chips from the hook/CI.
  Exit: one story shipped END TO END from the belt, every act audited.
  *Expanded by owner direction (2026-07-08) into the Steering Desk
  charter — [phase-87](../phase-87-steering-desk/AGENT-BRIEF.md):
  attach (a real live view into a real agent session), steer
  (voice-first, armed, pane-identity-verified, audited), classify
  (session exhaust → desk primitives + rails truth), and desk objects
  riding into steers as hydrated context. The Telegram interface's
  consent spine is the floor; contract-shaped wire types keep iPad/
  iPhone native (B4 inherits, never redesigns). Verbatim bar: "so
  robust, it will literally destroy our brains."*
- **B3 — The factory** (hub + web desk): "New Project" — repo + workbench
  install + agent-run intake from spoken input; belts as desk primitives in
  zones; the portfolio view. Exit: a new real repo born from the desk and
  its first story shipped from its belt.
- **B4 — The DeskOS belt** (HSM track): the diorama surface on the synced
  shapes; the couch walk.

## 5. Open questions (for graduation, not now)

- Where the projects registry lives (hub config vs. a synced primitive) and
  how a remote-only repo (no local checkout) degrades honestly.
- The agent-runner seam: the coder queue watches tmux sessions today —
  whether dispatch spawns tmux (observable, killable) or a headless runner
  with streamed frames.
- Whether `dw state` is generated-on-read (no new files in consumer repos)
  or committed (diffable receipts). Leaning generated-on-read + cached.
- Multi-machine: belts for repos that live on another mesh node — the relay
  precedent exists (Phase 85), deliberately out of scope until B3 is real.
