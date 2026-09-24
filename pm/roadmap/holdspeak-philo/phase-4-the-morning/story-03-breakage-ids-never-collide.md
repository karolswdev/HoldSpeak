# PHILO-4-03 - A failure never collides with the next brief

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** done
- **Depends on:** -
- **Unblocks:** the morning in one move
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Closure finding:** Phase 3 final-summary "What he still cannot do" #2

## Problem

Breakage items get a fixed id (`brief-break-pipeline-{event_id}`, `holdspeak/services/monday_brief_service.py:546`; connectors `:575`); the next day's brief inserts the same id again (`:305`) into a table-wide primary key (`holdspeak/db/schema.py:2441`) and answers 500 (`UNIQUE constraint failed: monday_brief_items.id`, run `20260924T012420Z`). The collision needs a failure already stored in an earlier brief to be selected again (selection keeps the latest failure per source over a window from the preceding business close, `:516`, `:145`): a Wednesday-evening failure selected Wednesday evening and again Thursday morning collides; a newly encountered failure need not (Astra, closure check).

## Scope

- **In:** the result below, its fence(s) red pre-fix, the rig case at 1440 and 393.
- **Out:** everything the phase status lists as out.

## Acceptance criteria

- [x] Fix shape settled (Astra's in-memory probe on the real table declarations): BRIEF-SCOPED ids for BOTH pipeline and connector items (`monday_brief_service.py:546,575`), retaining `source_ref` and the cause; NOT `INSERT OR IGNORE` (the new brief silently loses the row) and NOT `INSERT OR REPLACE` (the old brief loses its row and, with foreign keys on, its triage — `schema.py:2440`). No schema migration. — built: `brief-break-pipeline-{brief_id}-{event_id}` / `brief-break-connector-{brief_id}-{run_id}` (`monday_brief_service.py:558,587`), brief id minted before the collectors (`:268`), `source_ref` and cause unchanged, plain INSERT kept (`:309`), no schema change.
- [x] A lookback containing a breakage item already stored in an earlier brief generates the next brief with 200; BOTH briefs read back with their rows; the old brief's triage is preserved; same-day regeneration stays idempotent (same id). — `tests/unit/test_philo4_03_breakage_ids.py:93-137` (day two 200; both briefs read back; day-one Ack preserved `:135`; same-day same brief and ids `:109-112`).
- [x] The overlapping failure is minted through its REAL producer (a failed pipeline run selected into two briefs), never a hand-inserted row. — pipeline: a failing `MondayBriefService.shelve` on the hub through `@observe_service` + `SQLiteObserver` (`:145-160`, the observer's clock pinned to Wed 18:00); connector: `db.activity.record_connector_run` (`:173`).
- [x] Fence red pre-fix: two generations across a producer-day advance with one breakage in the lookback; today's code raises IntegrityError. — `docs/internal/philo/phase-4/ids/red-pre-fix.txt` (origin/main `1c39294c`: 2 failed, `sqlite3.IntegrityError: UNIQUE constraint failed: monday_brief_items.id`); green `green-post-fix.txt`.
- [x] Words unchanged by this story: breakage titles today carry service/method or connector ids (`:546`) and the Arrival renders `item.text` (`ChairHome.tsx:2000`); an id fix does not change the face. The Tenet 4 wording debt is ledgered in the phase status, not claimed here. — titles and details unchanged (`:164-165`, `:184-185` of the fence assert them); no web file changed.

## Effort (council-style estimate, not a promise)

0.5–1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-24 — built (Muad'Dib lane, Opus 5.5 worker): brief-scoped breakage ids; fence red pre-fix through the real producers; the rig is not run for this story (no face change).
- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
