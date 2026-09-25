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

## Round 2 (Astra's check on built: BOUNCE; `checks/lane-a-built-astra.md` finding 2)

- **The expanded row names the import.** `web/src/desk/chair/ChairHome.tsx:2176-2181,2237`: for `import_failed` (and no failed intel job) the status well head reads `IMPORT` and the cause line is the import worker's `intel_status_detail` (`LAST ERROR · No cues could be parsed from …`); every other failure keeps `SUMMARY`. The head carries `data-testid=arrival-status-well-head`.
- **Fence:** `web/src/desk/chair/__tests__/importFailedRow.philo601r2.test.tsx` — the complete row (the ledger line and its open well): badge FAILED, head IMPORT, the import's cause, no `SUMMARY`, no `SAVED`. Red on a `git archive f6c0c0d1` copy (`Received: "SEP 24Architecture boundary review — empty transcriptFAILEDSUMMARYFAILED"`), green on the branch: `docs/internal/philo/phase-6/badge/round-2/`.
- **Rig:** `case.philo601.import_failed.badge` now observes the well head (`readable_text IMPORT`); the badge FAILED is a setup check on the same evaluator. `20260925T035149Z-…-1440` VERDICT pass (`'IMPORT' is readable in viewport 1440x900 with rect x 306 y 450 w 40 h 13`); `20260925T035156Z-…-393` VERDICT pass (`x 22 y 307 w 40 h 13`). Glass (both after.png viewed): the row reads FAILED; the well reads IMPORT / FAILED / LAST ERROR with the import's cause; no SUMMARY, no SAVED. The trigger is the pointer on the well head: at 393 the open well sits below the sticky capture bar, the rig has no scroll verb and `End` did not scroll the Arrival; the head has no handler. Parked runs: `attempts/README.md`.
- **Narrowed:** the story no longer claims that no state falls to SAVED; `importing`/`refused`/`live` are BACKLOG "PHILO-6 follow-ups" row 1 (assigned).
- **Seen, not changed:** the import's cause names the worker's temporary file (`TMPLYES_VQF.VTT`), not the owner's file name; producer wording, outside this story.

## Round 3 (Astra's round-two check: BOUNCE; `checks/lane-a-built-astra.md` "Round two", finding 3)

- **The cause, at the producer.** `MeetingImportError` and `TranscriptParseError` carry a short `cause` (`holdspeak/meeting_import.py`, `holdspeak/transcript_parse.py`; 17 raises classed). The worker stores it as `intel_status_detail` and logs the full message (`holdspeak/services/meeting_service.py:318-326`). The face is unchanged: `LAST ERROR · <cause>` (`web/src/desk/chair/ChairHome.tsx:2181`).
- **Red on a `git archive 27ee9559` copy** (`docs/internal/philo/phase-6/brief/round-3/red.txt`): `AssertionError: No cues could be parsed from tmp9zn5e812.vtt. The file has a WEBVTT header but no readable cue blocks — nothing was imported.`; rendered, on the round-two fixture: `Received: "LAST ERROR · No cues could be parsed from upload.vtt. …"`. **Green** (`round-3/green.txt`): both pass; the fixture `import-failed-meeting.json` regenerated by its producer (`"detail": "NO TRANSCRIPT LINES"`).
- **Integration pins re-pointed:** `tests/integration/test_web_transcript_import_api.py` (`EMPTY OR BINARY FILE`, `NO TRANSCRIPT LINES`), `test_web_meeting_import_api.py` (`UNEXPECTED ERROR`).
- **Rig re-run** (`case.philo601.import_failed.badge`, `docs/internal/philo/graph/atlas-phase3.json:6539`; `words` now state the trigger is an inspection after scroll, not an owner-action transition): `20260925T043228Z-…-1440` VERDICT pass (`'IMPORT' is readable … x 306 y 450`), `20260925T043240Z-…-393` VERDICT pass (`x 22 y 364`). Both observations record `intel_status.detail = NO TRANSCRIPT LINES` in every API read; the temp name appears only in the hub log line (`hub_log[4]`), never on the wire or glass. Both after.png viewed: `IMPORT` / `FAILED  LAST ERROR · NO TRANSCRIPT LINES`.

- **The round-3 capture's script** (`r3-cmd.sh`, a scratch file; its full text here, since the capture header names only the path). It ran on the worktree holding BOTH round-3 stories (story 01's producer change was unstaged but present, and the atlas pin for `meeting_import.py` needs it):

```bash
set -o pipefail
H=$(mktemp -d)
HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_monday_brief*.py tests/unit/test_philo3_*.py tests/unit/test_philo4_*.py tests/unit/test_philo5_*.py tests/unit/test_philo6_*.py tests/unit/test_philo_graph_atlas.py tests/unit/test_brief_collectors.py tests/unit/test_hs171_aggregate_notify.py tests/unit/test_hs171_heartbeat_wire.py tests/unit/test_walk_monday_brief_126.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo_4_01_generate.py tests/unit/test_hs175_week_brief.py tests/unit/test_scheduled_recording_mcp.py tests/unit/test_hs202_desk_memory_recent.py tests/unit/test_thread_tool_gate.py tests/unit/test_brief_shelf.py tests/unit/test_event_linked_arm.py tests/unit/test_brief_mcp.py tests/unit/test_person_overlay.py tests/unit/test_people_brief.py tests/unit/test_hs175_cancel_owner.py tests/unit/test_graph_walk_calibration.py tests/unit/test_124_verify_round2.py tests/unit/test_124_verify_round3.py tests/unit/test_meeting_import*.py tests/unit/test_transcript_parse*.py tests/unit/test_hs201_import_no_auto_summary.py tests/unit/test_follow_through*.py tests/unit/test_decision_record_service.py tests/integration/test_phase200_attention_coverage.py tests/integration/test_web_meeting_import_api.py tests/integration/test_web_transcript_import_api.py tests/integration/test_web_history_import_ui.py \
 && (cd web && npx vitest run src/desk/chair src/desk/pullouts) \
 && HOME=$(mktemp -d) uv run python scripts/philo_api_reference.py --check \
 && HOME=$(mktemp -d) uv run python scripts/philo_graph_reference.py --check \
 && HOME=$(mktemp -d) uv run python scripts/philo_boundary_census.py --check \
 && HOME=$(mktemp -d) .githooks/dw check holdspeak-philo \
 && test -z "$(git status --short | grep '^ M' | grep pm/roadmap/holdspeak/)"
```

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

### Captured run — 2026-09-25T03:58:43Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_philo6_01_import_badge.py tests/unit/test_philo_graph_atlas.py && (cd web && npx vitest run src/desk/chair) && HOME=$(mktemp -d) uv run python scripts/philo_api_reference.py --check && HOME=$(mktemp -d) uv run python scripts/philo_graph_reference.py --check && HOME=$(mktemp -d) uv run python scripts/philo_boundary_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d164c58227ee48708df9c55ad0f76b618543412

```text
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 1.86s

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-a/web


 Test Files  20 passed (20)
      Tests  103 passed (103)
   Start at  21:58:46
   Duration  3.42s (transform 3.27s, setup 2.08s, import 9.41s, tests 5.69s, environment 8.28s)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
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

### Captured run — 2026-09-25T04:40:35Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/r3-cmd.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e35232e2dfbfa728cc6c98b27d37cbe20fc657e4

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 25%]
........................................................................ [ 33%]
........................................................................ [ 41%]
........................................................................ [ 50%]
........................................................................ [ 58%]
........................................................................ [ 66%]
........................................................................ [ 75%]
........................................................................ [ 83%]
........................................................................ [ 91%]
.......................................................................  [100%]
863 passed in 87.90s (0:01:27)

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-a/web


 Test Files  31 passed (31)
      Tests  181 passed (181)
   Start at  22:42:04
   Duration  3.81s (transform 4.36s, setup 3.12s, import 12.92s, tests 8.77s, environment 11.01s)

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
dw check: ok
```
