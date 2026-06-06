# Evidence — HS-45-01: Dictation journal, the persistence spine

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## What shipped

The durable spine the rest of Phase 45 reads/writes: a `dictation_journal`
table + `DictationJournalRepository`, a side-channel `DictationJournalRecorder`
fed at the same post-run seam telemetry uses, a config toggle + retention cap,
and secret filtering — wired into **both** the live dictation path and the
dry-run path. Journal-disabled or unwired ⇒ dictation behavior byte-identical.

### Code

- **Table + schema** — `holdspeak/db/core.py`: `dictation_journal` added to
  `SCHEMA_SQL` (+ `idx_dictation_journal_recent`); `Database` constructs
  `self.dictation_journal`. Canonical snapshot regenerated in this commit
  (`tests/fixtures/db_schema_canonical.txt`, +20 lines, journal-only diff).
- **Repository** — `holdspeak/db/journal.py` (`DictationJournalRepository`):
  `record` (validates `source`, JSON-encodes `stage_ms`/`rewrite_pass_ms`/
  `warnings`, prunes to `retention` last-N on insert), `recent`
  (newest-first, `source`-filterable, limitable), `get`, `delete`, `clear`,
  `count`, and `mark_corrected` (the `corrected`/`correction_id` linkage
  HS-45-03 will call — column present, unset here).
- **Record model** — `holdspeak/db/models.py`: `DictationJournalRecord`.
- **Recorder bridge** — `holdspeak/plugins/dictation/journal.py`
  (`DictationJournalRecorder`): the `on_run`-sibling. Extracts per-stage
  timings exactly as `telemetry_store` does, **redacts** transcript + final
  text via the shared `looks_like_secret` check, and is **best-effort** — a
  no-op without a repository or with `enabled=False`, and it swallows every
  failure so a journal write can never break a dictation.
- **Config** — `holdspeak/config.py`: `DictationPipelineConfig.journal_enabled`
  (**default ON**, local) + `journal_retention` (default 500, validated `>= 1`).
- **Wiring** — `web_server.py` constructs the recorder (durable only when a repo
  is injected) and exposes it on `WebContext.journal`; `web_runtime.py` adds
  `_dictation_journal_repo()`, injects it, and records each live run
  (`source='dictation'`); the dry-run helper (`web/routes/dictation/_helpers.py`)
  records each dry-run (`source='dry_run'`), passed through from the route.

## Tests

### Unit — `tests/unit/test_db_dictation_journal.py` (13 tests)

Repository: full-field round-trip, unknown-source rejection, newest-first +
`source`-filter + limit, **retention prune to last-N on insert**, delete/clear,
`mark_corrected` flag + correction link. Recorder: stage-ms extraction mirrors
telemetry, persists a run with context, **disabled writes nothing**, **no
repository ⇒ no-op**, unknown source rejected, **secret redaction proven** (a
known `sk-…` value never lands in transcript *or* final text), and **repository
failure is swallowed** (no raise into the dictation path).

```
$ uv run pytest -q tests/unit/test_db_dictation_journal.py
13 passed in 0.39s
```

### Integration — `tests/integration/test_dictation_journal_wiring.py` (2 tests)

Drives the real dry-run executor (`_run_dictation_dry_run_text`) over a seeded
local project, offline (no endpoint — the kb-enricher runs without a runtime):

- a real run persists exactly **one** `source='dry_run'` row with the
  transcript, stage latency (`kb-enricher`), and matching `total_ms`/`final_text`;
- **`journal_enabled=False` ⇒ 0 rows AND byte-identical `final_text`** vs on.

```
$ uv run pytest -q tests/integration/test_dictation_journal_wiring.py
2 passed in 0.65s
```

### True end-to-end — real pipeline → real LLM → real DB row (no mic)

`scripts/journal_e2e_demo.py` + `tests/e2e/test_dictation_journal_e2e.py`
(opt-in, auto-skip without an endpoint — mirrors the HS-39 enrichment e2e). It
runs the **real** all-features pipeline (intent-router · kb-enricher ·
multi-pass project-rewriter) against the live `.43` llama.cpp, then journals the
resulting run through the **real** repository into a real on-disk SQLite DB and
reads the row back, asserting it faithfully captures the run.

Run live against `.43` (`Qwen3.5-9B-UD-Q6_K_XL.gguf`):

```
$ HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
  HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
  uv run pytest -s tests/e2e/test_dictation_journal_e2e.py
... 1 passed in 21.08s
```

The persisted afterlife it printed:

```
  ── persisted journal row ──────────────────────────────────
  id            1
  source        dictation
  intent        None  →  block agent_task_buildout  @ conf 0.85
  target        claude_code
  stage_ms      intent-router 3791ms  kb-enricher 0ms  project-rewriter 15825ms
  total_ms      19616
  rewrite_pass  5269ms + 5284ms
  corrected     False

  446 chars spoken → 1594 chars typed, durably journaled and reviewable.
```

A 446-char ramble routed to `agent_task_buildout` @ 0.85, targeted at
`claude_code`, rewritten over 2 real passes into a 1594-char grounded task — and
**every** field (source, transcript, routing, target, per-stage + total latency,
rewrite-pass timings, warnings, `corrected=False`) landed in a real DB row.

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2343 passed, 17 skipped in 58.90s
$ uv run ruff check holdspeak/db/ holdspeak/plugins/dictation/journal.py
All checks passed!
```

Up from the Phase-44 close (2328/16): **+15 tests** (13 unit + 2 integration)
and **+1 gated e2e skip**. No `holdspeak/static/_built/` tracked.

## Invariants held

- **Side-channel / behavior-preserving** — the recorder is a no-op without a
  repo or with `journal_enabled=False`; the integration test proves the typed
  `final_text` is byte-identical on vs off. The whole existing suite is green.
- **Local-first & private** — local SQLite only; transcript + final text
  redacted when they trip the shared secret check; retention-capped; per-entry
  delete + wipe at the repo layer.
- **Best-effort** — every recorder failure is swallowed; a journal error can
  never break a dictation.
- **Provable remotely (no mic)** — the dry-run integration test + the real `.43`
  e2e exercise the full spine without a microphone.
