# HS-93-04 — Power lives on the Desk

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
  production Web evidence, and automated cross-client verification complete;
  owner/physical-device discovery evidence pending
- **Depends on:** HS-93-01, HS-93-02, HS-93-03
- **Unblocks:** HS-93-07, HS-93-08, HS-93-09
- **Owner:** unassigned

## Problem

Projects and Integrations are not first-class on the Web Desk, while Personas,
Workflows, Runs on, and advanced tools are exposed through several rails and
pages. These are the Desk's applications, tools, services, and processes. They
must live in the AI operating system without turning its resting surface into a
settings wall.

## Scope

- **In:** First-class Desk presence/action model for Project and Integration;
  shared tool-shelf/dock, selection/context, inspector/window, search/launcher,
  and live-status affordances for Persona, Workflow, Coder, Integration,
  models/destinations, devices, and background work; Runs-on summary beside
  imminent model work; capability readiness and effect preview; same semantic
  actions on Web and Swift; retained Artifact/Receipt return; simplify or remove
  redundant permanent rails/chips where the shared OS grammar supersedes them.
- **Out:** A universal command palette, graph-engine convergence, plugin
  marketplace, or permanent new top-level navigation.
- **Paths:** hub project/integration/capability/target routes, Web Desk world,
  pullouts, creation and action menus, Studio, Swift Desk primitive/tool dock,
  Workbench and connector sheets, and cross-client UAT.

## Acceptance criteria

- [x] A Project is discoverable from its related Desk material and supports
      assign/remove/open without becoming a Zone or Knowledge collection.
- [x] A configured Integration is discoverable from compatible selected
      material; setup is a focused room, and propose/approve/result returns to
      the source subject with a Receipt.
- [x] Personas, Workflows, Integrations, inference destinations, devices, Coder
      sessions, and background runs can be found through stable Desk tool,
      selection, search, inspector, and presence affordances without visiting
      Studio merely to launch or observe them.
- [x] Persona, Workflow, and Coder session actions appear only when their input,
      selection, readiness, and effect class make the action meaningful.
- [x] Runs on is visible before model-backed work and on its Receipt, but no
      placement decision is required for basic dictation or other safe defaults.
- [x] Web and Swift expose equivalent semantic actions over the shared wires
      (DeskIntegrationProposal source binding, contextual capability actions,
      Runs-on targets) while keeping native docks/sheets/motion — verified by
      the cross-client suites and the flagship simulator build; the owner
      "no permanent clutter" judgment on physical devices is candidate-Y scope.
- [x] Before/after evidence records fewer irrelevant controls at rest (the
      permanent Persona/model rail removed, the resting conveyor collapsed to
      one presence chip, five create chips folded into one Create entry) with
      task discovery preserved through the Tools shelf walks and the
      production evidence runners; the owner discovery-time measures are
      candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the owner discovery-time/clutter measures and the physical iPhone/iPad
inspector/connector/Coder/Runs-on/relaunch walks move verbatim to
[BACKLOG candidate Y](../BACKLOG.md) and are not claimed here.

## Test plan

- **Unit:** contextual-action eligibility, readiness, selection, destination,
  and result-return tests in Python, Vitest, and Swift.
- **Integration:** Project/Integration/capability routes and sync, proposal
  lifecycle, Workbench return, and artifact lineage tests.
- **Manual / device:** Select representative Meeting/Note/Artifact/Project
  material on Web, iPhone, and iPad; discover and complete each compatible act,
  then find the retained result after relaunch.

## Notes / open questions

An Integration may be a dock/tool-shelf presence rather than a freely positioned
content object. First-class means discoverable identity, readiness, action,
status, inspector, and receipt—not identical spatial rendering. Studio authors
and configures the tool; the Desk is where the tool lives and works.

Implementation and bounded evidence are recorded in
[progress-story-04.md](./progress-story-04.md). The unchecked criteria require
owner discovery/control-count observation and physical iPhone/iPad proof; a
simulator build and scripted production-Web path do not close them.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
