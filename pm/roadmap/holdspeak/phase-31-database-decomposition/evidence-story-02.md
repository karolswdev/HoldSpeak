# Evidence — HS-31-02 (`IntelRepository`)

**Shipped:** 2026-06-02. The deferred-intel jobs/attempts queue is extracted into
`IntelRepository`; `MeetingDatabase` no longer carries any intel-queue methods.

## What changed

- `holdspeak/db/intel.py` (new, 394 lines) — `IntelRepository(BaseRepository)`: the 11
  intel-queue methods moved **verbatim** —
  `enqueue_intel_job`, `claim_next_intel_job`, `retry_intel_job`, `complete_intel_job`,
  `list_intel_jobs`, `get_intel_queue_summary`, `record_intel_job_attempt`,
  `list_intel_job_attempts`, `fail_intel_job`, `requeue_intel_job`,
  `update_meeting_intel_status`.
- `core.py` — the 11 methods deleted (4311 → 3934 lines); `__init__` now constructs
  `self.intel = IntelRepository(self._connection, self)`.
- `base.py` — `BaseRepository.__init__` gained an optional `container` arg stored as
  `self._db`, the container back-reference for cross-domain calls (see Decisions).
- `__init__.py` — `IntelRepository` exported.

## Cross-domain call (the design crux)

`requeue_intel_job` reads a meeting (`get_meeting`) before enqueuing — a genuine
intel→meetings dependency. Rather than a one-off, established a scalable pattern:
repositories receive a back-reference to the container (`self._db`), so the call
became `self._db.meetings.get_meeting(...)`. The intra-repo `self.enqueue_intel_job`
call inside `requeue` is unchanged. This pattern is what HS-31-03 (projects →
action-items / artifacts) will reuse.

`intel_snapshots` stays with `MeetingRepository` (HS-31-01 decision) — this repo owns
the queue (`intel_jobs`, `intel_job_attempts`) and meeting intel-status updates only.

## Call sites updated

- **Production: 19** across 4 files (`intel_queue.py` ×10, `commands/intel.py` ×4,
  `web/routes/meetings.py` ×4, `meeting_session.py` ×1) → `db.intel.<method>(`.
- **Tests: 32** in `test_db.py` → `db.intel.<method>(`; **7 fake-db doubles** given
  `intel = property(lambda self: self)`.
- Zero bare `db.<intelmethod>` remain (grep-verified).

## Line counts

| File | Lines |
|---|---|
| core.py | 3934 (−377 this story; −1547 / −28% vs. original 5481) |
| meetings.py | 890 |
| intel.py | 394 |
| models.py | 345 |
| base.py | 49 |
| __init__.py | 17 |

## Tests ran

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2062 passed, 14 skipped**
  (== baseline). Green on the first run — the container back-ref path is exercised by
  the existing requeue tests.
- `uv run ruff check holdspeak/db/` → **All checks passed!**
- Smoke: `MeetingDatabase` exposes `.intel`; `get_intel_queue_summary()` round-trips;
  `hasattr(db, "enqueue_intel_job")` is `False`.

## Decisions

- **Container back-reference (`self._db`) for cross-domain repo calls** — chosen over
  threading specific sibling repos into each constructor, because more cross-domain
  calls land in HS-31-03. Repos are constructed `Repo(self._connection, self)`.
- **Out of scope / left as-is:** the pre-existing `F841` (`current_time`) in
  `meeting_session.py:1277` — present on HEAD, untouched.
