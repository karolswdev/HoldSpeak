# HS-8-03 Evidence - Safari and Firefox History Readers

## Shipped Result

HS-8-03 adds browser-history source readers that import local metadata
into the HS-8-02 activity ledger.

The implementation adds `holdspeak/activity_history.py` with:

- default-enabled Safari and Firefox source discovery
- source path hashing so the ledger does not store raw browser DB paths
- safe SQLite snapshot copying into a temp directory
- `-wal` and `-shm` companion copying when present
- read-only SQLite connections against the copied snapshot
- Safari `History.db` reader for `history_items` plus `history_visits`
- Firefox `places.sqlite` reader for `moz_places` plus
  `moz_historyvisits`
- browser timestamp normalization into UTC datetimes
- per-source checkpoint reads/writes
- incremental imports that skip already imported visit timestamps

## Safety Boundaries

The readers do not open live browser databases for write. Import uses a
temporary copy of the main SQLite file and any WAL/SHM companions, then
opens the copy with SQLite `mode=ro`.

The readers import only history metadata needed by the ledger:

- URL
- title
- domain
- visit count
- first/last visit timestamps
- raw last-visit timestamp for checkpoint/audit

They do not read cookies, cache, credentials, form data, private
browsing state, page content, or perform network enrichment.

## Fixture Coverage

`tests/unit/test_activity_history.py` creates temporary SQLite fixtures
for both browser schemas. The tests verify:

- discovered readable sources are enabled by default
- WAL/SHM companion files are copied with the main database
- Safari fixture visits import into `activity_records`
- Firefox fixture visits import into `activity_records`
- source checkpoints store the latest raw source timestamp
- repeated imports use checkpoints and do not churn duplicate records

## Verification

```text
uv run pytest -q tests/unit/test_activity_history.py tests/unit/test_db.py
56 passed in 1.54s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1120 passed, 13 skipped in 24.92s
```

```text
git diff --check
```
