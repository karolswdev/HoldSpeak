# Evidence - HS-151-01

- **Story:** HS-151-01 - The thread ledger (schema + repository + import)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T21:23:57Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1d7c5de7-eeec-4b6e-927e-186a731078fc/scratchpad/home01 uv run pytest -q tests/unit/test_thread_repository.py tests/unit/test_db.py -k thread or schema or shape or reconcile`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fb418b506e0f5b90abb7a09c6060164b28c29257

```text
................................                                         [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout_method

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 67 deselected, 4 warnings in 6.50s
```

## Orchestrator triage (2026-08-29)

Read the output above: 32 passed (25 new `test_thread_repository.py`
+ the snapshot/shape/reconcile names). Schema block
`holdspeak/db/schema.py` L3404–3524; fixture 422→439 lines, diff is
exactly the block. Builder decisions accepted: REAL epoch timestamps,
content-synced FTS5 on implicit rowid with the four triggers (M3),
nullable `thread_refs.message_id` for thread-level refs (the
`import_hash` row), `soft_delete(thread)` cascading to messages so the
FTS triggers fire. Real-DB-copy reconcile proof is deferred to the
close sweep (story 08) — the fresh-DB twice proof is here.
