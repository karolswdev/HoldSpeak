# HS-8-01 Evidence - Browser History Source Audit

## Shipped Result

HS-8-01 audits local browser-history sources for Phase 8 and defines the
safe ingestion contract before implementation.

No browsing URLs, titles, or page contents were dumped into this
evidence. The local commands inspected only file presence, SQLite schema,
journal mode, and row counts.

## Safari Findings

- Expected macOS path:
  `~/Library/Safari/History.db`
- Local status:
  - `History.db` exists.
  - `History.db-wal` and `History.db-shm` exist, so readers must treat
    Safari history as a WAL-mode SQLite database and copy companion files
    for a consistent snapshot.
- Relevant tables:
  - `history_items`
    - `id`
    - `url`
    - `domain_expansion`
    - `visit_count`
    - `status_code`
  - `history_visits`
    - `id`
    - `history_item`
    - `visit_time`
    - `title`
    - `load_successful`
    - redirect/origin/attribute fields
- Timestamp note:
  - Safari `history_visits.visit_time` is stored as a browser-specific
    real timestamp. HS-8-03 must normalize it to UTC datetimes in tests
    using fixture values.

## Firefox Findings

- Expected macOS profile root:
  `~/Library/Application Support/Firefox/Profiles/`
- Expected Linux profile root:
  `~/.mozilla/firefox/`
- Expected history database:
  `places.sqlite`
- Local status:
  - No Firefox profile/database was present in the standard macOS or
    Linux locations on this machine.
- Expected core tables from Mozilla Places documentation:
  - `moz_places` stores URL-level records and global statistics.
  - `moz_historyvisits` stores individual visits and references
    `moz_places`.
- HS-8-03 must confirm exact columns using fixture `places.sqlite`
  databases because no local Firefox database was available during this
  audit.

Reference: Mozilla Places database overview:
https://udn.realityripple.com/docs/Mozilla/Tech/Places/Database

## Safe Read Strategy

Browser databases must never be opened for write. The reader should:

1. Resolve candidate source database paths.
2. Create a temporary directory owned by HoldSpeak.
3. Copy the main SQLite file plus any `-wal` and `-shm` companions when
   present.
4. Open only the temporary copy.
5. Read only whitelisted metadata columns.
6. Delete the temporary copy after import.

For Safari, copying only `History.db` missed WAL-backed rows in the local
audit. Copying `History.db`, `History.db-wal`, and `History.db-shm`
produced the newer count snapshot.

## Minimum Ingestion Contract

HS-8-02 should persist normalized records with:

- `source_browser`
- `source_profile`
- `source_path_hash`
- `url`
- `title`
- `domain`
- `visit_count`
- `first_seen_at`
- `last_seen_at`
- `last_visit_raw`
- `entity_type`
- `entity_id`
- `project_id`
- `created_at`
- `updated_at`

Source readers should expose raw browser timestamps only as intermediate
values or explicit `last_visit_raw`; all user-facing times should be
normalized datetimes.

## Default-Enabled Behavior

Phase 8 is scoped as default-enabled for this personal local tool when
readable browser history sources exist. That default must still be
visible and reversible:

- UI/API reports active sources and last import time.
- Import can be paused.
- Imported records can be cleared.
- Domains can be excluded.
- No hidden remote telemetry or external network enrichment.

## Command Evidence

```text
$ ls -l "$HOME/Library/Safari"/History.db*
-rw-r--r--@ 1 karol  staff  544768 Apr 26 17:05 /Users/karol/Library/Safari/History.db
-rw-r--r--@ 1 karol  staff       0 Oct 21  2025 /Users/karol/Library/Safari/History.db-lock
-rw-r--r--@ 1 karol  staff   32768 Apr 21 08:20 /Users/karol/Library/Safari/History.db-shm
-rw-r--r--@ 1 karol  staff  613912 Apr 26 19:51 /Users/karol/Library/Safari/History.db-wal
```

```text
$ sqlite3 "$TMP_COPY/Safari-History.db" '.tables'
history_client_versions  history_items            history_tombstones
history_event_listeners  history_items_to_tags    history_visits
history_events           history_tags             metadata
```

```text
$ sqlite3 "$TMP_COPY/Safari-History.db" 'PRAGMA table_info(history_items);'
0|id|INTEGER|0||1
1|url|TEXT|1||0
2|domain_expansion|TEXT|0||0
3|visit_count|INTEGER|1||0
4|daily_visit_counts|BLOB|1||0
5|weekly_visit_counts|BLOB|0||0
6|autocomplete_triggers|BLOB|0||0
7|should_recompute_derived_visit_counts|INTEGER|1||0
8|visit_count_score|INTEGER|1||0
9|status_code|INTEGER|1|0|0
```

```text
$ sqlite3 "$TMP_COPY/Safari-History.db" 'PRAGMA table_info(history_visits);'
0|id|INTEGER|0||1
1|history_item|INTEGER|1||0
2|visit_time|REAL|1||0
3|title|TEXT|0||0
4|load_successful|BOOLEAN|1|1|0
5|http_non_get|BOOLEAN|1|0|0
6|synthesized|BOOLEAN|1|0|0
7|redirect_source|INTEGER|0||0
8|redirect_destination|INTEGER|0||0
9|origin|INTEGER|1|0|0
10|generation|INTEGER|1|0|0
11|attributes|INTEGER|1|0|0
12|score|INTEGER|1|0|0
```

```text
$ sqlite3 "$TMP_COPY_WITH_WAL/History.db" 'PRAGMA journal_mode; PRAGMA user_version;'
wal
16
```

```text
$ sqlite3 "$TMP_COPY_WITH_WAL/History.db" 'SELECT "history_items", COUNT(*) FROM history_items UNION ALL SELECT "history_visits", COUNT(*) FROM history_visits;'
history_items|322
history_visits|657
```

```text
$ find "$HOME/Library/Application Support/Firefox/Profiles" -maxdepth 2 \( -name places.sqlite -o -name profiles.ini \) -print
find: /Users/karol/Library/Application Support/Firefox/Profiles: No such file or directory

$ find "$HOME/.mozilla/firefox" -maxdepth 2 \( -name places.sqlite -o -name profiles.ini \) -print
find: /Users/karol/.mozilla/firefox: No such file or directory
```

## Verification

```text
git diff --check
```

```text
uv run pytest -q tests/unit/test_meeting_exports.py
6 passed in 0.29s
```
