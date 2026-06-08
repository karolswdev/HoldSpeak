# Evidence — HS-53-01: the nudge engine + dismissal store

Write-once record of the brain that everything else in Phase 53 surfaces. A pure reader
over the existing activity ledger + the meeting window — no new watcher, no LLM, gated by
the activity privacy toggle, dismissals persisted.

## What shipped

- **New module `holdspeak/activity_nudges.py`** (~270 lines): `compute_nudges(db, *,
  project_id=None, now=None, limit=3) -> list[Nudge]`. Returns 1–3 source-cited nudges:
  - a **windowed summary** keyed `window:<since_iso>` ("you touched N things since your
    last meeting"), with `since_source` ∈ {`previous_meeting`, `recent_window`};
  - **per-record suggestions** keyed `record:<id>` ("you were looking at `github_issue
    owner/repo#123`"), each with one citation.
  Each `Nudge` carries `NudgeCitation`(s) — `record_id`, `source_browser`,
  `source_profile`, `entity_type`/`entity_id`, `domain`, `title`, `url`, `last_seen_at`,
  `visit_count` — so the UI can name where the nudge came from and a user can verify it
  on `/activity`.
- **Relevance is a deterministic heuristic** (recency buckets ≤1h/≤6h/≤24h/≤72h + entity
  bonus for `github_issue` / `github_pull_request` / `jira_issue` / `calendar_event` +
  project-match bonus + a small `visit_count ≥ 5` bump). A weak-signal record
  (`score < 1.0`) does not become a nudge. No LLM, no learned scorer, fully unit-testable.
- **Dismissal store** is a new tiny table `activity_nudge_dismissals (nudge_key TEXT
  PRIMARY KEY, dismissed_at TEXT NOT NULL)` declared in `holdspeak/db/core.py`'s canonical
  `SCHEMA_SQL`. Two methods on `ActivityRepository`:
  `list_dismissed_nudge_keys() -> set[str]` and `dismiss_nudge(nudge_key: str)` (upsert).
  Keys are deterministic so dismissals survive recomputation.
- **Off when activity is off.** `compute_nudges` reads
  `db.activity.get_activity_privacy_settings()["enabled"]` first and returns `[]`
  immediately when disabled — no records read, no work done.
- **Window resolution.** Prefer the previous `MeetingSummary.ended_at` (scans up to 5
  recent meetings, picks the first ended one ≤ `now`); fall back to `now - 24h` if none.
  `since_source` is recorded on the window nudge so the UI can phrase honestly
  ("since your last meeting" vs "recently").
- **Schema snapshot regenerated.** `tests/fixtures/db_schema_canonical.txt` now contains
  the new table; the snapshot test (`tests/unit/test_db.py:1619`) is green. Regenerated
  with the test's identical normalizer (`r'\\s+'` literal — a no-op that preserves
  newlines, per the memory note).

## Why this is honest

- **Read-only.** The engine never writes outside the dismissal table. It does not import
  history, scrape browsers, or call out.
- **Source-cited.** Every nudge carries `record_id` + `source_browser`/`source_profile` +
  `entity` + `last_seen_at`. No nudge has citations that are not derivable from a real
  `ActivityRecord` row.
- **Local-only.** Everything reads/writes the local SQLite DB through the existing
  `ActivityRepository`. No network.
- **Quiet beats noisy.** Window nudge requires `≥ 2` records in the window; per-record
  nudges require `score ≥ 1.0`. Records older than the window simply do not surface.

## Tests

`tests/unit/test_activity_nudges.py` — 10 tests, every acceptance bullet covered:

- `test_engine_returns_empty_when_activity_off` — the off-path (the consent gate).
- `test_engine_uses_previous_meeting_ended_at_as_window` — window key + `since_source` =
  `previous_meeting`; citations present.
- `test_engine_falls_back_to_recent_window_without_prior_meeting` — `since_source` =
  `recent_window`.
- `test_record_nudges_carry_source_citation` — the citation contract (browser/profile,
  entity, `last_seen_at`, `visit_count`, `record_id`).
- `test_dismissed_nudge_stays_dismissed` — dismissal filters; survives a fresh `Database`
  handle (persisted on disk, not in memory).
- `test_weak_signal_records_do_not_become_nudges` — stale-page suppression.
- `test_relevance_ordering_prefers_entity_typed_recent` — heuristic ordering
  (a `github_issue` 1h ago > a bare page 20h ago).
- `test_project_match_boosts_score` — project-id bonus.
- `test_limit_cap_is_respected` — 8 candidate records → exactly 3 nudges returned.
- `test_nudge_serialization_is_jsonable` — `.to_dict()` is JSON-safe (the API in HS-53-02
  will lean on this).

```
uv run pytest -q tests/unit/test_activity_nudges.py
-> 10 passed in 0.30s

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2509 passed, 17 skipped in 76.41s
   (was 2460 at the start of Phase 53; +10 is the new engine tests; the +39 between is
    test growth in earlier already-shipped commits.)
```

0 `_built/` tracked; no UI bundle touched (this is engine + DB only).

## Not done here (by design)

- **The HTTP surface** (`GET /api/activity/nudges` + `POST .../dismiss`) — HS-53-02.
- **Selected-record dictation context override** — HS-53-03.
- **The nudge card UI** (clone of `#kn-nudge`) — HS-53-04.
- **The user guide** — HS-53-05.
- **Dogfood + phase close** — HS-53-06.

## Files touched

- `holdspeak/activity_nudges.py` (new) — the engine.
- `holdspeak/db/core.py` — `activity_nudge_dismissals` table in `SCHEMA_SQL`.
- `holdspeak/db/activity.py` — `list_dismissed_nudge_keys` + `dismiss_nudge`.
- `tests/unit/test_activity_nudges.py` (new) — 10 tests.
- `tests/fixtures/db_schema_canonical.txt` — schema snapshot regenerated.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/story-01-nudge-engine.md` — status
  flipped to `done`.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/current-phase-status.md` — story
  table updated, "Where we are" updated.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
