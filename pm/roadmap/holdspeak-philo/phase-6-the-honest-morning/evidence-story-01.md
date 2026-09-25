# Evidence - PHILO-6-01

- **Story:** PHILO-6-01 - The honest import badge
- **Status:** done
- **Date:** 2026-09-24

## What was built

- One mapping line: `web/src/desk/chair/intelBadge.ts:26` maps `import_failed` to the existing FAILED idiom (the same word and species as the failed intel job at `web/src/desk/chair/ChairHome.tsx:265`). No new word, no adapter change, no transcription-field change (Astra's corrected diagnosis, `checks/charter-astra.md` finding 1).
- The producer states enumerated: the import path writes `importing` (`holdspeak/services/meeting_service.py:198,297`) and `import_failed` (`:315,:318`, via `_set_import_status` `:331-337`). `import_failed` is the only terminal failure state the import path writes. The other terminal failure write, `error` (`holdspeak/db/intel.py:1867` and others), was already FAILED.
- Rig case `case.philo601.import_failed.badge` (`docs/internal/philo/graph/atlas-phase3.json:6543`), written the way the Phase 5 cases are: the real empty-VTT fixture (`tests/fixtures/philo5_empty.vtt`, sha256 pinned) through `POST /api/meetings/import`, waiting for `/intel_status/state = import_failed`; the trigger reloads the Arrival; the predicate is `readable_text FAILED` on `[data-testid=arrival-meeting-badge]`. Schema-valid (`tests/unit/test_philo_graph_atlas.py`, 77 passed).
- `docs/generated/api-reference.json` regenerated (`scripts/philo_api_reference.py`): the new pytest names the import and meeting routes, so the ledger's test references grew (+27 lines). `--check` exit 0 after.

## The fence (producer -> wire adaptation -> rendered badge)

- **(1) Producer** `tests/unit/test_philo6_01_import_badge.py`: the real import route and worker with a header-only VTT; the detail and the list row both carry `intel_status` `import_failed`, no segments. The test keeps the vitest fixture `web/src/desk/chair/__tests__/fixtures/philo6/import-failed-meeting.json` equal to the real wire (ids, times and temp names normalised); a drift fails. The fixture was written by that test (`PHILO6_WRITE_FIXTURE=1`), never by hand. Characterisation: passes pre-fix.
- **(2) Wire adapter** `web/src/desk/chair/__tests__/importFailedBadge.philo601.test.tsx`: the real `fromWireMeeting` carries `import_failed` from both the list row and the detail. Passes pre-fix (Astra's retraction confirmed: the adapter was never the defect).
- **(3) Rendered**: the same file seeds the adapted list row and serves the real detail, renders `ChairHome`, and reads the row's badge. RED pre-fix (`Received: "SAVED"`), GREEN after (FAILED, `data-badge=failed`). A covered-states table names every state the badge maps (the producer's writes); it is red pre-fix on `import_failed`.

## Reds and greens (retained under `docs/internal/philo/phase-6/badge/`)

- `red.txt` — `git archive origin/main` (66205729) with the branch's tests and fixture overlaid: pytest `1 passed` (characterisation); vitest `Tests 2 failed | 1 passed (3)`: `the Arrival row of the producer's failed import shows the FAILED badge` — `Expected: "FAILED" Received: "SAVED"`; the covered-states table — `import_failed: expected 'SAVED' to be 'FAILED'`.
- `green.txt` — the branch: pytest `1 passed`; vitest `Tests 3 passed (3)`.

## Rig (at 1440 and 393)

Under `assets/story-01-shots/`, `HOLDSPEAK_EVIDENCE_WRITE=1`, each hub in a fresh mktemp HOME, engine none:

- `20260925T023753Z-case.philo601.import_failed.badge-muaddib-1440` — VERDICT pass, terminal settled; `'FAILED' is readable in viewport 1440x900 with rect x 1132 y 408 w 46 h 18`.
- `20260925T023803Z-case.philo601.import_failed.badge-muaddib-393` — VERDICT pass, terminal settled; `'FAILED' is readable in viewport 393x852 with rect x 18 y 543 w 46 h 18`.
- Glass reading (both `after.png` viewed): the row `Architecture boundary review — empty transcript` shows FAILED in the danger tone; no SAVED anywhere; no Open verb and no Run summary on the row. At 1440 the row's expanded well reads `SUMMARY` with the fact `FAILED` (the existing status-facts idiom, `ChairHome.tsx:2215-2228`). The headline reads `2 need you`: the failed import now counts as attention (`hasMeetingAttention`, `ChairHome.tsx:269-272`) beside the SETUP row, which is the existing law for every FAILED meeting (`ChairHome.tsx:811`).
- `attempts/` — three parked crashed runs (a `:has-text()` observe_at the rig refuses; one `--headless`), with a README. Not evidence.

## Not claimed

- `importing` (`meeting_service.py:198`), `refused` (`meeting_session/intel_admission.py:93`) and `live` (`meeting_session/live_readiness.py:82`) still fall to the SAVED fallback (`intelBadge.ts:31`). They are not terminal failure states of the import path; mapping them is a word decision outside this story. Listed for the orchestrator (BACKLOG candidate).
- The catalog (`web/src/pages/cores/history/helpers.ts:99`) says `IMPORT FAILED` for the same state; the Arrival says `FAILED` as the brief and the story rule (existing idiom, no new word).
- The `SUMMARY · FAILED` well on a failed import names the summary, but the import failed; this is the existing status-facts idiom, recorded for the owner's review, not changed.
- No full suite (the orchestrator's job). Rehearsed shots, not a sitting.

### Captured run — 2026-09-25T02:40:02Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_philo6_01_import_badge.py tests/unit/test_philo_graph_atlas.py && (cd web && npx vitest run src/desk/chair) && HOME=$(mktemp -d) uv run python scripts/philo_api_reference.py --check && HOME=$(mktemp -d) uv run python scripts/philo_graph_reference.py --check && HOME=$(mktemp -d) uv run python scripts/philo_boundary_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 1.70s

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-a/web


 Test Files  17 passed (17)
      Tests  96 passed (96)
   Start at  20:40:05
   Duration  3.50s (transform 3.63s, setup 1.82s, import 8.85s, tests 5.66s, environment 7.05s)

API reference checked
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
Boundary candidate census checked
```
