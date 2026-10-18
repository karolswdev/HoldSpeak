# Parked: the second and third ways to automate (Betterment A8, 2026-10-18)

DECISIONS #2 (adopted 2026-10-17): one way to automate. The automation
sentence (When, Do, About, With, Put it in) replaces these on the face.
Nothing is deleted; their data and MCP tools stay.

- `newWorkflowVerb.ts`: the Desk menu's **New Workflow** (`desk.new-workflow`).
  Saved workflows still open, run and edit; MCP `workflow_run` stays.
- The old agent faces (the Agents list, New Agent) were parked by AG1:
  `../agents/README.md`.
- The queue view (`components/WorkbenchWindow.tsx`, with its event and idle
  starts, `WorkbenchAutomations.tsx` and `WorkbenchResourceful.tsx`) stays
  in place behind **RAW** in the automation window's title strip. RAW shows
  for an old queue automation, and for every automation while Settings ▸
  Builder tools is on.
