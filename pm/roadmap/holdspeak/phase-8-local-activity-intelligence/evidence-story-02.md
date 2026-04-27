# HS-8-02 Evidence - Activity Ledger Persistence

## Shipped Result

HS-8-02 adds the local persistence foundation for Phase 8's Local
Attention Ledger.

The implementation adds:

- `activity_records` table for normalized browser-history metadata.
- `activity_import_checkpoints` table keyed by source browser, profile,
  and source path hash.
- Typed DB dataclasses for activity records and import checkpoints.
- `upsert_activity_record()` for local persistence and deduplication.
- `list_activity_records()` for recent-context surfaces.
- `delete_activity_records()` for clear and retention controls.
- `set_activity_import_checkpoint()` and
  `get_activity_import_checkpoint()` for incremental source readers.

## Data Contract

The ledger persists the HS-8-01 minimum contract:

- source browser/profile/path hash
- URL and normalized URL
- title and domain
- visit count
- normalized first/last seen datetimes
- raw source timestamp (`last_visit_raw`)
- entity type/id
- optional project link
- created/updated timestamps

Raw browser timestamps are retained only as source audit data. The
primary user-facing times are normalized datetimes.

## Deduplication

Duplicate imports merge into one record when they share:

- source browser + source profile + normalized URL, or
- source browser + source profile + extracted entity type/id.

Merges preserve earliest first-seen time, latest last-seen time, latest
raw source timestamp, and the highest observed visit count. This keeps
incremental readers from double-counting repeated imports while still
updating newer metadata.

## Retention and Deletion

`delete_activity_records()` supports broad clear operations and filtered
retention/deletion by:

- source browser
- source profile
- project ID
- domain
- `older_than` last-seen timestamp

This gives HS-8-06 a concrete primitive for visible privacy controls.

## Verification

```text
uv run pytest -q tests/unit/test_db.py
51 passed in 2.20s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1115 passed, 13 skipped in 25.48s
```

```text
git diff --check
```
