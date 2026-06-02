# Evidence — HS-31-01 (Repository seam + `MeetingRepository`)

**Shipped:** 2026-06-02. The `holdspeak.db` monolith is now a package; the meetings
domain is extracted into `MeetingRepository`; the seam every later story copies is established.

## What changed

- `holdspeak/db.py` → `holdspeak/db/` package (via `git mv` to `core.py`, preserving history):
  - `holdspeak/db/__init__.py` — re-exports the full public surface (`from .models import *`,
    `from .core import *`, plus `BaseRepository`/`MeetingRepository`), so every existing
    `from holdspeak.db import X` import keeps working unchanged.
  - `holdspeak/db/models.py` — all 18 dataclasses + the 3 validation constants, extracted
    so repositories and the container share them with no import cycle.
  - `holdspeak/db/base.py` — `BaseRepository` (holds the container's connection factory +
    the shared `_json_*` helpers future repos need).
  - `holdspeak/db/meetings.py` — `MeetingRepository`: the meetings cluster (21 public
    methods + 9 private helpers) moved **verbatim**. Owns meetings, segments, speakers,
    topics, bookmarks, action items — and intel **snapshots** (`_save_intel`/`_load_latest_intel`),
    which are embedded in `MeetingState` save/load (see Decisions).
  - `holdspeak/db/core.py` — `MeetingDatabase` container: still owns the connection, schema,
    migrations, and the not-yet-migrated domains (intel queue, intent windows, plugins,
    artifacts, projects, activity). Now constructs `self.meetings = MeetingRepository(self._connection)`.

## Line counts (orig `db.py` = 5481)

| File | Lines |
|---|---|
| core.py (container, was the whole monolith) | 4311 (−1170 / −21%) |
| meetings.py (extracted domain) | 890 |
| models.py | 345 |
| base.py | 45 |
| __init__.py | 16 |
| **total** | 5607 |

Total grew ~126 lines (per-file headers/imports/class boilerplate) — the expected cost of
splitting one file into five. The win is separation: the meetings domain is now an isolated,
navigable module and the god-class shed a fifth of its bulk.

## Call sites updated (the move is API-changing by design — no compat facade)

- **Production:** 53 call sites across 11 files rewritten `db.<method>(` → `db.meetings.<method>(`
  (intel_queue, meeting_session, speaker_intel, plugins/queue, web/routes/meetings ×24,
  tui/services ×15, commands ×7). The 3 `hasattr(db, "get_action_item")` guards in
  web/routes/meetings.py were updated to `hasattr(db.meetings, ...)`.
- **One internal caller** (`requeue_intel_job` → `self.get_meeting`) rewritten to `self.meetings.get_meeting`.
- **One false positive deliberately left untouched:** `session.edit_action_item(...)` in
  web_runtime.py is a *session* method, not the db — a blind sed would have broken it.
- **Tests:** 112 call sites across 14 files rewritten (92 in test_db.py); 18 fake-db doubles
  given `meetings = property(lambda self: self)` so `db.meetings.X` resolves to the fake's `X`.
- `test_meeting_database_has_no_duplicate_method_definitions` upgraded to scan the whole
  `db/` package and assert no public method is defined in **both** the container and a
  repository — a refactor-aware guard for HS-31-02/03.

## Tests ran

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2062 passed, 14 skipped** —
  identical to the pre-refactor baseline. Behavior-preserving.
- `uv run ruff check holdspeak/db/` → **All checks passed!** (the package is ruff-clean).
- Smoke: a fresh `MeetingDatabase(tmp)` exposes `.meetings`, round-trips queries, and
  `hasattr(db, "get_meeting")` is `False` — the moved methods are gone from the god-class.

## Decisions / deviations

- **Package layout** (deferred decision, now made): `holdspeak/db/` package with a `Database`
  *container* — for HS-31-01 the container is still `MeetingDatabase` exposing `.meetings`;
  the rename to a thin `Database` + full call-site move completes in HS-31-03. The
  `from holdspeak.db import ...` path is unchanged.
- **`intel_snapshots` travels with `MeetingRepository`, not `IntelRepository`.** It is
  embedded in `MeetingState` (saved by `save_meeting`, loaded by `get_meeting`), so it is
  meeting state, not queue state. HS-31-02's `IntelRepository` therefore owns the intel
  *jobs/attempts queue* only; the status doc's scope note is refined accordingly.
- **`DEFAULT_DB_PATH` patch target moved.** `test_web_activity_api.py` monkeypatched
  `holdspeak.db.DEFAULT_DB_PATH`; after the split that name is read from `holdspeak.db.core`,
  so the fixture now patches `from holdspeak.db import core as db_module`. Only that one test
  file used the pattern.
- **Out of scope / left as-is:** a pre-existing `F841` (`current_time` unused) in
  `meeting_session.py:1277` — present on HEAD, untouched by this story.
