# Parked: the second and third ways to automate (Betterment A8, 2026-10-18)

DECISIONS #2 (adopted 2026-10-17): one way to automate. The automation
sentence (When, Do, About, With, Put it in) replaces these on the face.
Nothing is deleted; their data and MCP tools stay.

- `newWorkflowVerb.ts`: the Desk menu's **New Workflow** (`desk.new-workflow`).
  Saved workflows still open, run and edit; MCP `workflow_run` stays.
- The old agent faces (the Agents list, New Agent) were parked by AG1:
  `../agents/README.md`.
- The queue view is parked here (2026-11-08, every automation run is a
  Program, #2032/#2033): `WorkbenchWindow_20261108.tsx` with its event and
  idle starts (`WorkbenchAutomations_20261108.tsx`,
  `WorkbenchResourceful_20261108.tsx`), its runs wing, its inlet
  autocomplete, its voice grammar, its styles
  (`workbench-config_20261108.css`), its tests (`__tests__/`) and its web
  callers (`workbenchQueueViewApi_20261108.ts`). RAW is gone from the
  automation window. The hub routes only it called are parked in
  `holdspeak/web/routes/_parked/workbench_queue_view_routes_20261108.py`.
