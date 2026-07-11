# HS-92-06 — Capabilities make findable results

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress
- **Depends on:** HS-92-01, HS-92-05
- **Unblocks:** HS-92-07, HS-92-09
- **Owner:** unassigned

## Problem

Saved Personas, Recipes, Agents, Chains, Workflows, Blueprints, plugins, and live
Coders all appear runnable, but their lifecycle and result behavior differ. A
generic `Run` can yield transient text, an Artifact, a proposal, a queue row, or
a warning. A person should be able to choose material, choose understandable
behavior, run it, and find the result without learning implementation taxonomy.

## Scope

- **In:** Persona and Workflow definitions as Desk capabilities; Sequence/Chain
  compatibility; Coder session distinction; additive Invocation/Attempt/result
  envelope and QualifiedRefs; Workbench support negotiation; contextual run
  labels; Artifact materialization/lineage; entry to and return from Workbench;
  failure retention and retry.
- **Out:** Forcing dictation/plugin/connector pipelines onto one graph engine;
  syncing transient Persona chat threads; calling a live Coder a Persona.
- **Paths:** `holdspeak/db/primitives.py`,
  `holdspeak/web/routes/primitives/recipes.py`,
  `holdspeak/web/routes/primitives/chains.py`,
  `holdspeak/web/routes/primitives/workflows.py`,
  `holdspeak/web/routes/workflow_graph.py`, `holdspeak/plugins/host.py`,
  `web/src/desk/components/Pullout.tsx`,
  `web/src/desk/components/PersonaChat.tsx`, `web/src/pages/WorkbenchPage.tsx`,
  `apple/Sources/RuntimeCore/Workbench/`,
  `apple/App/MeetingCapture/WorkbenchUI.swift`, and run/lineage/UAT tests.

## Acceptance criteria

- [ ] A saved behavior is labeled Persona on both clients and a live Claude/Codex
      process is labeled Coder session; no primary Desk view calls both Agent.
- [ ] Persona, Workflow, and advanced Sequence each expose input schema/help,
      supported placement, effect classes, readiness, and a contextual action
      such as `Ask Scout` or `Run Release workflow on 3 items`.
- [ ] Every run receives one invocation/correlation ID, definition ref,
      initiator, grounding refs, requested placement, attempts, and terminal
      result/ref without replacing existing optimized job tables.
- [ ] Workbench opens from a Workflow object with that exact definition loaded;
      Save/Run returns to the same object and a kept Artifact materializes beside
      the source with definition/input/attempt lineage.
- [ ] A graph unsupported by a host is marked unavailable or partially supported
      before Run and never silently lowered to a prompt; Sequence remains an
      explicitly linear compatibility form.
- [ ] Empty output, unavailable capability, failed attempt, cancelled run, and
      retry retain input/grounding and create an honest receipt or actionable
      failure state.
- [ ] Existing grounded Ask, Persona conversation, Keep/Bin, voice input, and
      Coder steering delight remain intact.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_run_frames.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_web_routes_ask.py tests/unit/test_plugin_host_idempotency.py tests/unit/test_primitive_contract.py`; Web Desk run/Workbench tests; Swift Workbench/contract tests.
- **Integration:** `uv run pytest -q tests/integration/test_artifact_synthesis_pipeline.py tests/integration/test_primitive_framework_sync.py tests/integration/test_web_built_mount.py`; UAT `pack-desk/06`, `pack-desk/13`, `pack-desk/17`, and `pack-b-steering/08`.
- **Manual / device:** Create a Persona and Workflow, run each on selected
  material, enter/exit Workbench, Keep/Bin, induce unsupported graph and offline
  target failures, and find the Artifact/receipt after relaunch on Web and Swift.

## Notes / open questions

Plugin and Integration SDK docs keep precise packaging terms. The product Desk
shows the capability or Integration, not the packaging mechanism.

## Automated evidence — 2026-07-11

- Schema v17 adds additive `capability_invocations` and
  `capability_attempts` receipts with retained input/grounding, requested
  placement, terminal state, and Artifact result refs; domain job tables stay.
- Persona, Sequence, and Workflow responses expose input help/schema,
  placement, effect class, readiness, host support, and contextual actions.
- Unsupported Workflow graphs return an unavailable receipt before engine
  construction and are never lowered to their prompt; Sequence declares its
  linear compatibility form.
- Web loads the exact Workflow selected from the Desk, saves/runs it, returns
  to that Workflow or kept Artifact, places results beside positioned sources,
  retains failed input, and shows the receipt.
- Swift contracts/providers decode the same invocation/attempt/result envelope;
  hub-born cards retain the invocation source through sync.
- Focused Python route/schema/receipt suites, Web typecheck plus 102 Desk tests,
  and 48 focused Swift provider/contract/Desk-record tests pass. Native
  selected-Workflow Workbench entry, active cancellation, and physical
  Web/native relaunch walks remain open, so this story is not closed.
