# HS-40-02 — Persistent correction memory

- **Project:** holdspeak
- **Phase:** 40
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-40-04
- **Owner:** unassigned

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

- [ ] A `dictation_corrections` table + `DictationCorrectionRepository` exist;
      the repo round-trips a correction (record → fetch recent).
- [ ] The canonical schema snapshot is regenerated and a fresh-build
      `sqlite_master` matches it (the snapshot test passes).
- [ ] `CorrectionStore` with a repository **loads** recent corrections on
      construction and **persists** on `record`; survives a simulated restart
      (new store + same repo sees the prior corrections).
- [ ] `CorrectionStore` with **no** repository is byte-identical to pre-story
      (the existing `test_dictation_correction_store.py` passes unchanged).
- [ ] Secrets/gist rules unchanged (still gist-only + secret-rejected before
      persisting).
- [ ] `GET /api/dictation/corrections` reflects persisted corrections.

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
