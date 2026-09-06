# Phase 175 — Hygiene census

Census of THE-TUESDAY-ARC.md section 4 items against Phase 175's tree.

## Census table

| # | Item | Source | State in 175 tree | Resolution | Status |
|---|------|--------|--------------------|------------|--------|
| 1 | Per-source Adjust well | 169 ledger | Not referenced by any 175 tree file. The Adjust well is a Room face concept; 175's backend services (door_service, project_service, watch_sources) do not surface per-source parameter editing. | DEFER -- face-layer item; belongs to the phase that builds the Adjust disclosure (176+). | deferred |
| 2 | Steward settings under sources | 169 ledger | Not referenced. Steward configuration sits in project_steward_service.py (changed by 175 but not in the hygiene-scoped tree). | DEFER -- steward settings belong to the steward's own face phase (173 closed; future polish). | deferred |
| 3 | Park 167 wings' faces, setup/ and `configure-setup` manifest | 169 ledger | Zero hits for `configure-setup` or `setup/` in any 175 tree file. | DEFER -- a web-face parking task outside 175's tree. | deferred |
| 4 | Door window hugging its content | 169 ledger | A CSS/layout issue on the Door window. 175's door_service.py changes are data-layer (week_strip, event_project_index). The face files are owned by sibling lanes. | DEFER -- face-layer; the lane editing ChairHome owns this. | deferred |
| 5 | MCP twins for the door routes | 169 ledger | 175 adds `holdspeak/web/routes/calendar_events.py` (3 new routes). No MCP twins written for these routes. The MCP families changed by 175 (heartbeat, project, concierge, people) gained their own tools, but the calendar_events routes have no MCP twin. | DEFER -- MCP twins for calendar routes belong to the next MCP sweep. | deferred |
| 6 | Four legacy-wrapping writes in one transaction (158 S-1) | 158 N ledger | PAID in Phase 173. `project_service.py:7-9` documents "HS-173-08 / 158 S-1: the four legacy-wrapping methods folded from three separate transactions into one atomic transaction each." | ALREADY PAID | paid |
| 7 | Empty-patch revisions (158 N-1) | 158 N ledger | 175 does not introduce new revision-update patterns that would create empty patches. The existing revision fields in `scheduled_recordings.py:155-185` and `calendar_events.py:107` use upsert (ON CONFLICT UPDATE) which inherently avoids empty patches. | DEFER -- no new surface; pre-existing debt outside 175's scope. | deferred |
| 8 | Sidecar fetcher seam (165) | 165 ledger | PAID before 173. `door_service.py:139,331-332,366-367` references are documentation-only ("the Door never blocks on the sidecar"). The seam itself was fixed in the project MCP family. | ALREADY PAID | paid |
| 9 | Second acli account proof (166) | 166 ledger | `watch_sources.py:633` references acli confluence but no multi-account support. 175's watch_sources changes add `MeetingWatchSource` (local DB, zero acli). | DEFER -- acli multi-account is a connector-layer concern outside 175. | deferred |
| 10 | Nine tsc-erroring web files (150) | 150 ledger | `npx tsc --noEmit` on 175's five faces (ChairHome, MeetingsConfig, ProjectRoomCore, CadenceCore, BriefView, SystemShade) returns ZERO errors. The remaining six erroring files (ThoughtDocumentPane, ThoughtWorkspaceWindow, concierge/api, ConciergeCore, AssignmentEditor, ModelLibraryCore) are outside 175's tree. | NOT TOUCHED -- 175's faces are tsc-clean. | clean |
| 11 | Five conductor loops in parallel | Arc item | `calendar_ingest_conductor.py:163,719` still runs a single `_loop` thread. 175 adds event-Room matching inside the existing loop (line ~201) but does not parallelize the conductor loops. | DEFER -- conductor parallelism is an architecture item for a future phase. | deferred |

## New debt introduced by Phase 175

| # | Kind | Location | Detail | Severity |
|---|------|----------|--------|----------|
| N1 | `datetime.now()` without tz | `monday_brief_service.py:171` | `compute_lookahead` (NEW in HS-175-05): `period_start = now or datetime.datetime.now()` -- no timezone. Mirrors the inherited `compute_window` pattern at line 146 where callers pass tz-aware `now` in production. The risk is a bare call without `now=` which produces a naive datetime. | low -- production callers pass `now`; but the default is a silent footgun |
| N2 | Broad `except Exception` in new code | `calendar_ingest_conductor.py:201-203` | Event-Room matcher fault isolation: `except Exception as exc: log.error(...)`. Consistent with the existing conductor pattern (never let one step crash the loop). | accepted -- conductor fault isolation pattern |
| N3 | Broad `except Exception` in new code | `calendar_ingest_conductor.py:~249-253` | Watch-query loading inside the matcher: `except Exception: pass`. Swallows silently with no log. | low -- a failed watch query skip is reasonable but should log |
| N4 | Snapshot model can silently use cloud | `calendar_snapshot_service.py:576-595` | INHERITED: the direct dispatch path iterates ALL profiles without boundary filtering. A cloud `openAICompatible` profile with vision capability is selected without recording the host on the egress dict (line 631: scope only, no host). The routed path (line 516-537) DOES record the host. | medium -- the fence test (P2-2) is written as xfail(strict=True) to document this |

## Summary

- **PAY-NOW items**: none (no safe-to-edit files with payable debt).
- **PAY-AFTER-LANES items**: none identified.
- **DEFER items**: 7 (items 1-5, 7, 9, 11 -- all outside 175's tree or face-layer).
- **ALREADY PAID**: 2 (items 6, 8 -- paid in 173).
- **CLEAN**: 1 (item 10 -- 175's faces have zero tsc errors).
- **New debt**: 4 items documented (N1-N4), all low/accepted severity.
- **Positional INSERTs**: zero in the 175 tree. All INSERTs name their columns. Existing fence `tests/unit/test_no_positional_inserts.py` passes (3 passed).
- **TODO/FIXME/XXX**: zero in the 175 tree.
