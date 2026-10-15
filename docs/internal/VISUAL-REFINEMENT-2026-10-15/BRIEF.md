# Continued visual refinement — 2026-10-15

Owner direction after the app-wide picker pass: continue finding ugly
windows and interfaces. The owner wants a deep pass, reusable components,
Workbench retained, useful jobs and real polish. Picker release1206 is
merged/deployed; base94551006a. One isolated worktree:
`/Users/karol/dev/tools/wt-visual-refinement-20261015`.

## Tuesday question

Can the architect open a work object, understand its state, make the next
edit or decision and recover from failure without parsing a configuration
dump or hunting a control? Tenets3/5/6/7 and ConstitutionVII/VIII apply.

## Audit before build

Two bounded read-only source lanes plus root production inspection.
Do not redesign or build during the audit. Source findings are candidates
until root opens the actual face. Pick concrete defects: raw controls,
type/material inconsistency, giant blank panels, duplicate hierarchy,
nested scroll, fields/actions detached from their data, phone clipping,
unexplained empty or failed states. Cover editor/open/action/error states
as well as arrivals. Rank by owner cost; don't invent an architecture.

- Editors lane: ScheduleCreateWindow, RecipeEditor, Thread elicitation,
  tool/destination configuration and their current nested controls.
- Work views lane: WorkbenchWindow, Knowledge, ProjectRoom, Conductor
  session detail. Inspect current source, not parked predecessors.
- Root: live isolated1440/393 captures, Calendar chooser known P2,
  synthesis and settled canvas, then bounded repair lanes, independent
  finished review, affected quick, one release and normal desk deployment.

Reports live here as AUDIT-EDITORS.md and AUDIT-WORK-VIEWS.md. Each finding
names path:line, the job and exact opening path, the visible defect and
current species to reuse; separate source inference from a live result.
Maximum six ranked findings per lane. Name existing good patterns and
remaining unknowns briefly. No screenshots or evidence artifacts tracked.

## Boundaries

Workers may author only their report during audit. No product/test edits,
tests, builds, browser, installs, staging or commits. Root will provide
specific settled designs/owned paths and focused test commands for build.
Anchors drift: verify against94551006a; other lanes are read-only now.
Never work in owner main checkout, stash/reset/restore/clean/switch,
delete, add-A, change owner HOME/DB or invoke hardware/external services.
HOLD FOR SHIP. Keep the audit bounded; source coverage is not runtime proof.
Fast-cycle CLAUDE.md governs delivery, no full/nightly or metal tests.
