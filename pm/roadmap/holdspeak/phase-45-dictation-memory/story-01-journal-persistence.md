# HS-45-01 — Dictation journal: the persistence spine

- **Project:** holdspeak
- **Phase:** 45
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-45-02, HS-45-03, HS-45-04
- **Owner:** unassigned

## Problem
Dictation is ephemeral. Meetings persist (`db.meetings`, `/history`), but the
daily-driver dictation loop keeps no durable record of what was said, how it was
routed, what got typed, or how long it took — only a gist-only correction ring
(`plugins/dictation/corrections.py`) and an in-memory latency ring
(`plugins/dictation/telemetry_store.py`), both lost on restart. Without a journal
there is nothing to review, correct-after-the-fact, or replay. This story builds
the spine the rest of the phase reads and writes.

## Scope
- **In:**
  - A new `dictation_journal` table + `DictationJournalRepository` in
    `holdspeak/db/` (mirror the existing repo pattern: a module under `db/`,
    re-exported from `db/__init__.py`, reached as `db.dictation_journal.*` via
    the `Database` container). Suggested columns: `id`, `created_at`,
    `source` (`'dictation'` | `'dry_run'`), `project_root`, `transcript` (raw
    spoken/typed input), `intent` / `block_id`, `target_profile`, `final_text`,
    `stage_ms` (JSON per-stage), `total_ms`, `rewrite_pass_ms` (JSON list),
    `confidence`, `warnings` (JSON), `corrected` (bool / correction ref, set by
    HS-45-03).
  - **Secret-filtering on write** — reuse the same filter the correction store
    applies before persisting, so secrets never land in the journal.
  - **Retention cap** — prune on insert to a configurable bound (`config`
    `dictation.journal_retention`); start with a generous last-N.
  - **Toggle** — `config` `dictation.journal_enabled` (default **ON**, local;
    see the phase's locked decision); when off, no rows are written and behavior
    is byte-identical.
  - **Wipe API + per-entry delete** at the repo layer (the UI lands in HS-45-02).
  - Wire the write as a **side-channel over the existing pipeline `on_run` hook**
    (`plugins/dictation/pipeline.py` `on_run`, the same seam telemetry uses) so
    both **real dictation** (`web_runtime`) and **dry-run** persist a row, tagged
    by `source`. Best-effort: a journal write failure must never break a
    dictation.
  - Regenerate `tests/fixtures/db_schema_canonical.txt` in the same commit.
- **Out:** the review UI (HS-45-02); the in-moment correction surface + setting
  the `corrected` flag (HS-45-03); replay (HS-45-04). No change to routing /
  rewrite / typing output.

## Acceptance criteria
- [ ] `dictation_journal` table + `DictationJournalRepository` exist; a fresh DB
      builds the table and `TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot`
      passes with the regenerated snapshot in the same commit.
- [ ] A pipeline run (dictation **and** dry-run) persists exactly one journal row
      with transcript, routing, final text, per-stage + total latency, and
      `source` set correctly.
- [ ] Secrets in the input/output are filtered before persistence (same filter
      as the correction store) — a test proves a known secret never lands.
- [ ] Retention prunes to the configured bound on insert; `journal_enabled=false`
      ⇒ **no rows written** and the dictation/dry-run result is byte-identical.
- [ ] A journal write failure is swallowed (best-effort) and does not raise into
      the dictation path.
- [ ] Suite green; `db/` ruff-clean; **0** `_built/` tracked.

## Test plan
- Unit: a new `tests/unit/test_db_dictation_journal.py` — record/list/delete/wipe,
  retention prune, secret-filter, `source` tagging; extend the db-shape snapshot
  test. `uv run pytest -q tests/unit/test_db_dictation_journal.py` +
  `... -k "schema or shape"`.
- Integration: drive a **dry-run** through `/api/dictation/dry-run` (or the
  pipeline directly) and assert a journal row appears; assert `journal_enabled=false`
  writes none. `uv run pytest -q tests/integration -k journal`.
- Manual / device: n/a (no mic — the dry-run path is the equivalent and is
  covered above).

## Notes / open questions
- **Retention shape** (last-N vs N-days vs both) — start last-N, configurable;
  revisit if the dogfood wants time-based pruning.
- **`corrected` linkage** — leave the column/ref in place but unset here; HS-45-03
  owns setting it (and linking to the `dictation_corrections` row it creates).
- Greenfield posture: add the table to the canonical schema directly (no
  migration ceremony) per the repo's standing decision.
