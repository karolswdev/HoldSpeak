# HS-40-02 — Persistent correction memory

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done (2026-06-05)
- **Depends on:** none
- **Unblocks:** HS-40-04
- **Owner:** unassigned
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Problem

The dictation `CorrectionStore` (HS-39-02) is in-process only — "dies with the
process (no DB, no disk)". Once a user corrects routing, that learning is lost
on the next restart. Phase 40 makes corrections **persist across sessions** so
the copilot keeps what it learned, while keeping the in-memory ring as the fast
nudge path on the live typing.

## Scope

- In:
  - A `dictation_corrections` table in `holdspeak/db/core.py` `SCHEMA_SQL`
    (columns ~ `id`, `kind`, `key` (gist), `value`, `created_at`; an index for
    recency). **Regenerate + commit the canonical schema snapshot** (there is a
    snapshot test that proves a fresh build matches).
  - A `DictationCorrectionRepository` in `holdspeak/db/corrections.py`, mirroring
    `holdspeak/db/actuators.py` (`__init__(connection, container)`, `with
    self._connection()`, dataclass records); registered on the `Database`
    container (`db/core.py`) + exported in `db/__init__.py`.
  - `CorrectionStore` gains **optional persistence**: load recent corrections on
    construction, write-through on `record`. When no repository is injected it
    behaves exactly as today (the unit tests stay green). Keep the bounded
    in-memory ring as the nudge source so the live path never hits the DB.
  - Cross-session surfacing: `GET /api/dictation/corrections` reflects the
    persisted set (and/or a `?history` view).
- Out:
  - Persisting telemetry (stays in-memory).
  - A management UI (HS-40-04).
  - Cloud sync / multi-device.

## Acceptance criteria

- [x] A `dictation_corrections` table + `DictationCorrectionRepository` exist;
      the repo round-trips a correction (record → fetch recent).
- [x] The canonical schema snapshot is regenerated and a fresh-build
      `sqlite_master` matches it (the snapshot test passes).
- [x] `CorrectionStore` with a repository **loads** recent corrections on
      construction and **persists** on `record`; survives a simulated restart
      (new store + same repo sees the prior corrections).
- [x] `CorrectionStore` with **no** repository is byte-identical to pre-story
      (the existing `test_dictation_correction_store.py` passes unchanged).
- [x] Secrets/gist rules unchanged (still gist-only + secret-rejected before
      persisting).
- [x] `GET /api/dictation/corrections` reflects persisted corrections.

## Outcome

A `dictation_corrections` table + `DictationCorrectionRepository`
(`db.dictation_corrections`, mirroring `db/actuators.py`) + the canonical schema
snapshot regenerated. `CorrectionStore` gained optional persistence
(`repository=…`): load-recent-on-construct + write-through-on-record, the
in-memory ring still the nudge path. The repo is injected by the **live
`WebRuntime`** (not `MeetingWebServer.__init__`, which uses the `get_database()`
singleton and would force every server test onto the real DB); bare servers stay
in-memory + byte-identical. Suite 2210/16 (+12). See
[evidence-story-02.md](./evidence-story-02.md).

## Test plan

- Unit: new `tests/unit/test_db_dictation_corrections.py` (repo round-trip);
  extend `tests/unit/test_dictation_correction_store.py` (persistence load/save,
  no-repo unchanged).
- Schema: the canonical-snapshot test (find it — likely `tests/unit/test_db*`
  or a `schema` test) passes after regeneration.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- **Schema snapshot is the trap** — adding a table without regenerating the
  committed snapshot will fail the snapshot test. Regenerate via whatever
  command the snapshot test documents (grep the test for how it builds the
  reference).
- Wiring: the live `MeetingWebServer` owns the `CorrectionStore`
  (`server.dictation_corrections`); inject the repository there (it has the
  `Database`). The dry-run/test paths construct stores without a repo → stay
  in-memory.
- Decision (recorded in status): keep the in-memory ring for nudge-speed; the DB
  is durability + history, not the per-utterance read path.
