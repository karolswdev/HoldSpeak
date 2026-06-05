# Evidence — HS-40-02 — Persistent correction memory

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## What shipped

The dictation `CorrectionStore` (HS-39-02) was in-process only — routing
learning died on restart. It is now **optionally DB-backed**: with a repository
injected it loads the recent set on construction and writes through on
`record`, so corrections survive a restart. With **no** repository it is the
Phase-39 in-process ring, byte-identical. The in-memory ring stays the fast
nudge path; the DB is durability, never a per-utterance read.

## Files touched

- `holdspeak/db/models.py` — new `DictationCorrectionRecord` dataclass
  (`id`/`kind`/`gist`/`value`/`created_at`).
- `holdspeak/db/corrections.py` (**new**) — `DictationCorrectionRepository`
  (mirrors `db/actuators.py`): `record_correction` (validates kind/gist/value),
  `recent_corrections(limit=)` (newest-first), `delete_correction`, `clear`.
- `holdspeak/db/core.py` — `dictation_corrections` table +
  `idx_dictation_corrections_recent` index in `SCHEMA_SQL`; repo registered on
  the `Database` container as `self.dictation_corrections`.
- `holdspeak/db/__init__.py` — exports `DictationCorrectionRepository`.
- `holdspeak/plugins/dictation/corrections.py` — `CorrectionStore(repository=…)`:
  `_load_from_repository` replays the recent set oldest-first (so `sequence`
  stays monotonic and the recency tie-break holds); `record` writes through
  after the in-memory append. Both DB calls are defensive — durability never
  blocks the live typing path.
- `holdspeak/web_server.py` — `MeetingWebServer(..., dictation_corrections_repository=None)`;
  the store is repo-backed only when one is injected.
- `holdspeak/web_runtime.py` — `_dictation_corrections_repo()` resolves
  `get_database().dictation_corrections` (defensive) and the live `run()`
  injects it into the server.
- `tests/fixtures/db_schema_canonical.txt` — **regenerated** (the trap): a
  fresh-build `sqlite_master` now includes the new table + index.
- Tests: `tests/unit/test_db_dictation_corrections.py` (**new**, 5 — repo
  round-trip / recency+limit / validation / delete+clear / fresh-container
  persistence); `tests/unit/test_dictation_correction_store.py` (+5 — write-
  through, secret-not-persisted, load-on-construct, survive-a-restart,
  cap-respected); `tests/integration/test_web_dictation_corrections_api.py`
  (+2 — GET reflects persisted, POST writes through).

## Why the repo is injected at `WebRuntime`, not `MeetingWebServer.__init__`

The story note suggested injecting at `MeetingWebServer` "(it has the
Database)". It does not — the server uses the `get_database()` **singleton**,
and eagerly opening it in `__init__` would make *every* server-constructing
test touch the real `~/.local/share/holdspeak/holdspeak.db`, break
`test_corrections_empty_by_default`, and write to real disk. Instead the store
takes an **optional** repository (bare server → in-memory, byte-identical), and
the **live runtime** injects the real repo. Web-level persistence is proven by
constructing a server with a temp-DB repo explicitly. Same outcome, test-safe.

## Verification artifacts

> `uv run` is broken on this machine (`platform.mac_ver()` empty); tests run via
> `.venv/bin/python -m pytest`.

- Schema snapshot: `.venv/bin/python -m pytest -q tests/unit/test_db.py -k canonical`
  → `1 passed` (fresh build matches the regenerated snapshot).
- Targeted: `.venv/bin/python -m pytest -q tests/unit/test_db_dictation_corrections.py tests/unit/test_dictation_correction_store.py tests/integration/test_web_dictation_corrections_api.py`
  → `26 passed`.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2210 passed, 16 skipped` (was 2198/16 at HS-40-01; +12).

## Acceptance criteria — re-checked

- [x] `dictation_corrections` table + `DictationCorrectionRepository` exist; the
      repo round-trips (record → fetch recent) — `test_record_and_recent_round_trip`.
- [x] Canonical schema snapshot regenerated; a fresh-build `sqlite_master`
      matches it — `test_fresh_schema_matches_canonical_snapshot` green.
- [x] `CorrectionStore` with a repo loads on construction + persists on record;
      survives a simulated restart — `test_store_loads_recent_on_construction`,
      `test_survives_a_simulated_restart`, `test_record_writes_through_to_repository`.
- [x] `CorrectionStore` with no repo is byte-identical — the unchanged
      `test_dictation_correction_store.py` Phase-39 cases pass.
- [x] Secrets/gist rules unchanged before persisting —
      `test_secret_and_invalid_are_not_persisted`.
- [x] `GET /api/dictation/corrections` reflects persisted corrections —
      `test_get_reflects_persisted_corrections`, `test_post_writes_through_to_db`.

## Deviations from plan

- Repo named `db.dictation_corrections` (not `db.corrections`) to be
  unambiguous against the unrelated meeting/activity domains.
- Repository placed in `holdspeak/db/corrections.py` as the story specified;
  the wiring lives in `WebRuntime` rather than `MeetingWebServer.__init__` (see
  "Why the repo is injected at `WebRuntime`" above).
- Off-by-default invariant: persistence is additive and independent of
  `corrections_enabled` (the flag still gates *consumption*/the routing nudge,
  which is byte-identical when off — all routing tests unchanged).
