# Evidence — HS-73-08 — The cutover: one desk

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## The zero-loss verb inventory (the deletion gate)

Every distinct interactive verb in `desk-legacy.astro` + `desk-app.js`
(extracted by grep over `@click` handlers), and its fate:

| Legacy verb | Fate on the island |
|---|---|
| `refresh` / `tidyDesk` | chrome chips (HS-73-01/02) |
| `openCreate/closeCreate` (note, agent, kb, directory) | the create chips + in-world editor (HS-73-03) |
| `openCreate` (chain/workflow form: `addWorkflowStep`, `moveWorkflowStep`, `removeWorkflowStep`, `workflowForm.mode` prompt/graph) | **consciously dropped from the desk**: capability-graph authoring belongs to Workbench (the owner's Blueprints direction) — the drawer form was a thin duplicate; the workflow pull-out gains **Open full → /workbench** (this commit) so the authoring surface is one tap away |
| `openObject` (the bounce-out) | the pull-out (HS-73-04) — strictly better |
| `openFile/closeFile` ("Move to…") | the pull-out's Move-to (HS-73-04) |
| `toggleFile` (the toggle-OFF half) | **gap found by this inventory, closed this commit**: Move-to now marks the containing zone (✓) and clicking it REMOVES via the real membership DELETE |
| `openRun/submitRun/copyRun/closeRun` | the rail + the pull-out Run + Copy (HS-73-07) |
| `diveInto/surface` | zones (HS-73-05) |
| `answerCoder` | **gap found by this inventory, closed this commit**: the coder pull-out gains "Answer with voice" firing the same `POST /api/coders/select {agent, session_id}`; honest Retry state on failure |

## What was deleted

- `web/src/pages/desk-legacy.astro` (the whole Alpine page: create
  drawers, the run drawer, the file drawer, the "Browse as a list"
  appendix, the banned intro prose).
- `web/src/scripts/desk-app.js` (the eval'd Alpine factory).
- The `/desk-legacy` route + its pre-flight entry. **`/desk` → `/` stays**
  (link hygiene). `scripts/desk/sprites.js` **stays** — it is the shared
  picker the island imports (parity by construction).

## Verification artifacts

- `/desk-legacy` → **404** asserted; `/desk` still lands on `/`.
- **The toggle-off gap-closer proven**: a pre-filed note's Move-to showed
  its zone checked; clicking it tombstoned the membership row in the DB.
- The stop-signal greps clean **on the desk tree** (`web/src/desk`):
  zero `getUserMedia`, zero `aria-modal`, zero `role="dialog"`. (An
  earlier repo-wide sweep flagged `dictation/mic.js` — the dictation
  page's legitimate pre-existing browser recorder, out of the desk
  rule's scope; the honest scoping is recorded here.)
- Zero references to the deleted files in source (the two remaining grep
  hits are attribution comments in `api.ts`/`lineage.ts` naming the port
  source).
- Build: **17 pages** (the legacy page gone). vitest 9/9; pre-flight 2
  passed; manifest regenerated; full suite **3066 passed, 37 skipped, 0
  failures**.

## Acceptance criteria — re-checked

- [x] The verb inventory shipped BEFORE deletion; every verb mapped or
      consciously dropped with a line each.
- [x] Two real gaps the inventory caught (toggle-off, answerCoder) were
      closed on the island BEFORE the deletion landed.
- [x] The legacy page, factory, and route are gone; the shared sprite
      picker survives.
- [x] `/desk` keeps landing users on the desk.

## Deviations from plan

- The `.desk-next` CSS namespace stays (renaming it repo-wide is churn
  with zero user-facing value; recorded).

## Follow-ups

- HS-73-09: docs + the mechanical locks (including the scoped no-modal /
  no-prose greps as tests).
