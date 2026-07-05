# HSM-16-08 — Capability objects: workflows + models, combinable + runnable across the mesh

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** done (2026-07-04 — the genuinely-open half built: **the model manifest is the sync
  wire's eleventh kind**, published/stored/served on both sides, and the run-target sheet consumes
  it (the "On your desktop" row NAMES the model it would run). Survey truth-ups recorded honestly:
  (1) workflow/model desk kinds + combine-to-run (drop a workflow/recipe/chain on an input →
  offerRunTarget → run) and the cross-node hub run were **pre-paid** by the desk era + Phase 22;
  (2) "drop a model onto a workflow node sets RUNS-ON" was **superseded** by Phase 24 runtime
  profiles + `BPNode.runsOn` (the owner-ratified "where intelligence runs" shape) — building a
  second gesture for the same decision would be drift, not value; (3) the acceptance's "target
  resolved from the synced manifest" ships as the manifest **informing the user's choice** in the
  run-target sheet, not silent auto-routing — auto-resolving egress without the human would
  violate the one approval+egress contract (Phase 15/21). The no-binary invariant is asserted on
  every layer: schema negative (validate.py), Swift wire test, hub route test. The live
  cross-device run rides 16-06 per this story's own test plan. Suites: Swift 467/9/0, hub 2474
  unit green, validator ALL PASS, sim shot committed.)
- **Depends on:** HSM-16-02 (workflow + modelManifest sync), HSM-16-03 (hub), HSM-16-05 (organization
  flows — the same transport carries capability), the Workbench (HSM-14-15/16, `Workflow.swift`,
  `generate(workflowTypes:)`), Phase-15 fluid compute (RUNS-ON / RuntimeMode A/B/C).
- **Unblocks:** HSM-16-06 (the proof can include a cross-mesh run).
- **Owner:** unassigned

## Problem

Workflows (the Workbench's visual-programming AI programs) and models are the **executable** layer, but
today a workflow is trapped where it was authored and runs only via a detail-screen button. For a mesh,
a workflow authored on the iPad should **run on the Mac's big model**, and on the desk a workflow should
be a first-class object you **drop onto an input to run it immediately**. Models likewise should be
first-class objects whose *availability* the mesh understands without shipping the binary.

## Scope

- **In (design-first; build where it's the cheapest path to the proof):**
  - **Workflows + models as first-class DeskObject kinds** (extends [[story-20-the-desk-object-model]]):
    a `workflow` object (material: the Workbench crystal/graph) and a `model` object (the cartridge),
    each with the standard facets — and a new **combine/run** interaction.
  - **Combine = run.** Dropping a `workflow` object onto an **input** object (a meeting, a KB, a
    lasso selection, an output) **executes** the workflow against that input and blooms the result as
    **Content** (artifacts) on the desk — the spatial form of `generate(workflowTypes:)`. Dropping a
    `model` onto a workflow node sets that node's RUNS-ON target.
  - **Target resolution across the mesh.** The run's compute target resolves via Phase-15 fluid compute
    against the **model manifest** (16-02): on-device if capable, else the Mac hub, else an endpoint —
    honoring the one approval + egress contract (Phase 15). A workflow authored on the iPad can run on
    the Mac because the manifest told it the Mac has the model.
  - **Definitions flow** (via 16-02/16-05): a workflow saved on one surface appears and runs on the
    others; the model manifest advertises each node's models.
- **Out:** authoring the Workbench graph itself (already HSM-14-15/16); shipping model binaries over the
  mesh (never — only the manifest). The web Workbench editor is its own follow-up; this story is the
  capability **objects + combine-to-run + mesh target resolution**.

## Acceptance criteria

- [ ] `workflow` and `model` are first-class DeskObject kinds (registered in the convention + the
      `DeskObjectKind` dispatch), with materials and the combine/run interaction.
- [ ] Dropping a workflow object onto a meeting (or KB / selection) runs it and produces real artifacts
      on the desk; dropping a model onto a workflow node sets that node's RUNS-ON.
- [ ] A workflow authored on one surface runs on another node of the mesh, the target resolved from the
      synced model manifest under the Phase-15 approval+egress contract.
- [ ] No model binary ever crosses the mesh; only the manifest does (asserted in tests).

## Test plan

- Unit/host: a combine-to-run resolves the correct target from a manifest fixture (on-device vs Mac vs
  endpoint) and emits artifacts; an air-gapped manifest with no capable model refuses cleanly.
- On device (folded into HSM-16-06): author a workflow on the iPad, run it against a meeting with the
  target resolved to the Mac hub, watch the artifacts bloom — real metal.
