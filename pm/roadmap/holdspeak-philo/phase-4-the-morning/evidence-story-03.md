# Evidence - PHILO-4-03

- **Story:** PHILO-4-03 - A failure never collides with the next brief
- **Status:** done
- **Date:** 2026-09-23

## Proof

### Captured run — 2026-09-24T05:25:18Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run --extra dev pytest -q tests/unit/test_monday_brief_service.py tests/unit/test_philo3_01_decision_route.py tests/unit/test_philo3_03_brief_clock.py tests/unit/test_philo3_install_contract.py tests/unit/test_philo3_summary_counts.py tests/unit/test_philo3_summary_detail.py tests/unit/test_philo3_summary_queue.py tests/unit/test_philo3_summary_rig.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_03_breakage_ids.py tests/unit/test_brief_collectors.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50efadaa83bd11187ff87d316005705e2bd02d0c

```text
........................................................................ [ 98%]
.                                                                        [100%]
73 passed in 12.51s
```

### The fence, red pre-fix and green post-fix

- **Fence:** `tests/unit/test_philo4_03_breakage_ids.py` (2 tests: pipeline, connector). Each mints one failure through its producer (pipeline: a failing `MondayBriefService.shelve` call on the hub, recorded by `@observe_service` into `pipeline_events` through the real `SQLiteObserver`, the observer's wall clock pinned to Wednesday 18:00; connector: `db.activity.record_connector_run`), generates day one (Wednesday 18:30) through `POST /api/brief/generate`, Acks the row, regenerates the same day, advances the producer clock one day, generates day two.
- **Red pre-fix** (`git archive origin/main` @ `1c39294c` + the fence overlaid): `docs/internal/philo/phase-4/ids/red-pre-fix.txt` — `2 failed`, both on `sqlite3.IntegrityError: UNIQUE constraint failed: monday_brief_items.id` at `holdspeak/services/monday_brief_service.py:305`.
- **Green post-fix:** `docs/internal/philo/phase-4/ids/green-post-fix.txt` — `2 passed`.
- **Rig:** not run. This story changes no face (ids only; the Arrival renders `item.text`); the closure-chain rig case belongs to the phase exit.
