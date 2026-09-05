# Phase 173 hygiene record

THE-TUESDAY-ARC.md section 4 items audited against the Phase 173 tree
(project_service.py, project_steward_service.py, project_update_service.py,
room_health_service.py, watch_sources.py, db/steward.py, db/updates.py,
db/schema.py, web/routes/steward.py, web/routes/project_updates.py,
mcp/tools.py, web/src/features/project-room/{model.ts, api.ts,
steward/**, update/**}).

## Paid

### 158 S-1: the four legacy-wrapping writes in one transaction

**File:** holdspeak/services/project_service.py

Four methods (`add_resource`, `remove_resource`, `associate_meeting`,
`disassociate_meeting`) each used three separate transactions (revision
bump, legacy repo layer write, change row + event + command). All four
folded into one atomic `with self._db._connection() as conn:` block each.
The repo layer's SQL is inlined; validation preserved (relationship
vocabulary check hoisted before the transaction in `add_resource`).

Lines changed: ~2402-2490 (add_resource), ~2498-2575 (remove_resource),
~2588-2690 (associate_meeting), ~2695-2790 (disassociate_meeting), plus
docstring update at line 8.

**Tests:** 102 passed (test_project_revision_law.py 67,
test_project_service_characterization.py 35); density guard 8 passed;
positional inserts guard 2 passed. Total: 112 passed, 0 failed.

## Already clear (no action needed)

### tsc-erroring web files in the steward/update UI area

**Verdict:** zero tsc errors in `web/src/features/project-room/steward/`
or `web/src/features/project-room/update/`. The remaining 8 tsc errors
are all outside the 173 tree (thought-workspace x2, concierge x2,
AssignmentEditor x1, ModelLibraryCore x1, ProjectRoomCore.tsx x1 [locked]).

### 165: the sidecar fetcher seam

**Verdict:** already fixed in `holdspeak/mcp/families/project.py:944-951`.
The `_watch_service()` helper composes with `default_snapshot_fetcher` (the
166-03 rider-a shape). The one remaining unfixed instance is in
`holdspeak/mcp/families/heartbeat.py:88` (`WatchService(db, observer=obs)`
without a fetcher), but that file is Phase 171's tree, not 173's.

## Deferred (tree intersects but not a named candidate)

### 158 N-1: empty-patch revisions

**File:** holdspeak/services/project_service.py `update_project` (line ~1910)

`update_project({})` still bumps the revision. The tree intersects
(project_service.py), but the item is not a named candidate in the
story, and changing the behavior (skip revision bump when `fields` is
empty) requires broader caller analysis. Deferred to a future phase whose
tree specifically touches `update_project`.

## Out of tree (not touched by Phase 173)

- per-source Adjust well
- steward settings under sources
- park the 167 wings' faces, setup/ and the configure-setup manifest entry
- the door window hugging its content
- MCP twins for the door routes
- the second acli account proof (166)
- the nine tsc-erroring web files outside steward/update (150)
- the five conductor loops in parallel
