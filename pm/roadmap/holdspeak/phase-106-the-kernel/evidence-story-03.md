# Evidence - HS-106-03

- **Story:** HS-106-03 - The effect census, pinned as a test
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T22:18:14Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_effect_ledger_is_complete_and_current __________________

    def test_effect_ledger_is_complete_and_current() -> None:
        ledger = _load_ledger()
        entries = ledger["sites"]
        actual = _walk_effect_sites()
    
        ledger_by_key = {_ledger_key(entry): entry for entry in entries}
        actual_by_key = {site.key: site for site in actual}
        assert len(ledger_by_key) == len(entries), "effect ledger contains duplicate selectors"
        assert len(actual_by_key) == len(actual), "source walker produced duplicate selectors"
    
        unledgered = [actual_by_key[key] for key in actual_by_key.keys() - ledger_by_key.keys()]
        missing = [ledger_by_key[key] for key in ledger_by_key.keys() - actual_by_key.keys()]
        family_mismatches = [
            (ledger_by_key[key], actual_by_key[key])
            for key in ledger_by_key.keys() & actual_by_key.keys()
            if ledger_by_key[key]["family"] != actual_by_key[key].family
        ]
    
        failures = [
            f"UNLEDGERED effect site: {site.label} "
            f"scope={site.scope} target={site.target} ordinal={site.ordinal}"
            for site in sorted(unledgered, key=lambda item: (item.path, item.line))
        ]
        failures.extend(
            f"MISSING ledgered effect site: {entry['id']} "
            f"{entry['path']}:{entry['census_line']} [{entry['family']}] "
            f"selector={entry['selector']}"
            for entry in sorted(missing, key=lambda item: item["id"])
        )
        failures.extend(
            f"FAMILY CHANGED for {entry['id']}: ledger={entry['family']} "
            f"source={site.family} at {site.path}:{site.line}"
            for entry, site in family_mismatches
        )
>       assert not failures, "effect census drift:\n  " + "\n  ".join(failures)
E       AssertionError: effect census drift:
E           UNLEDGERED effect site: holdspeak/plugins/_effect_census_mutation.py:5 [subprocess] scope=mutate target=run ordinal=1
E       assert not ['UNLEDGERED effect site: holdspeak/plugins/_effect_census_mutation.py:5 [subprocess] scope=mutate target=run ordinal=1']

tests/unit/test_kernel_effect_fence.py:403: AssertionError
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current
1 failed, 2 warnings in 1.19s
```

### Captured run — 2026-07-26T22:18:31Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
.                                                                        [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 2 warnings in 1.72s
```

### Captured run — 2026-07-26T22:18:53Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_effect_ledger_is_complete_and_current __________________

    def test_effect_ledger_is_complete_and_current() -> None:
        ledger = _load_ledger()
        entries = ledger["sites"]
        actual = _walk_effect_sites()
    
        ledger_by_key = {_ledger_key(entry): entry for entry in entries}
        actual_by_key = {site.key: site for site in actual}
        assert len(ledger_by_key) == len(entries), "effect ledger contains duplicate selectors"
        assert len(actual_by_key) == len(actual), "source walker produced duplicate selectors"
    
        unledgered = [actual_by_key[key] for key in actual_by_key.keys() - ledger_by_key.keys()]
        missing = [ledger_by_key[key] for key in ledger_by_key.keys() - actual_by_key.keys()]
        family_mismatches = [
            (ledger_by_key[key], actual_by_key[key])
            for key in ledger_by_key.keys() & actual_by_key.keys()
            if ledger_by_key[key]["family"] != actual_by_key[key].family
        ]
    
        failures = [
            f"UNLEDGERED effect site: {site.label} "
            f"scope={site.scope} target={site.target} ordinal={site.ordinal}"
            for site in sorted(unledgered, key=lambda item: (item.path, item.line))
        ]
        failures.extend(
            f"MISSING ledgered effect site: {entry['id']} "
            f"{entry['path']}:{entry['census_line']} [{entry['family']}] "
            f"selector={entry['selector']}"
            for entry in sorted(missing, key=lambda item: item["id"])
        )
        failures.extend(
            f"FAMILY CHANGED for {entry['id']}: ledger={entry['family']} "
            f"source={site.family} at {site.path}:{site.line}"
            for entry, site in family_mismatches
        )
>       assert not failures, "effect census drift:\n  " + "\n  ".join(failures)
E       AssertionError: effect census drift:
E           MISSING ledgered effect site: C05 holdspeak/missioncontrol_bridge.py:38 [subprocess] selector={'scope': '_default_runner', 'target': 'run', 'ordinal': 1}
E       assert not ["MISSING ledgered effect site: C05 holdspeak/missioncontrol_bridge.py:38 [subprocess] selector={'scope': '_default_runner', 'target': 'run', 'ordinal': 1}"]

tests/unit/test_kernel_effect_fence.py:403: AssertionError
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current
1 failed, 2 warnings in 1.59s
```

### Captured run — 2026-07-26T22:19:10Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
.                                                                        [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 2 warnings in 1.16s
```

### Captured run — 2026-07-26T22:19:28Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_kernel_broker_modules_stay_within_line_budget ______________

    def test_kernel_broker_modules_stay_within_line_budget() -> None:
        offenders: list[str] = []
        for path in _broker_modules():
            budget = _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
            lines = _line_count(path)
            if lines > budget:
                offenders.append(
                    f"kernel broker module over {budget}-line budget: "
                    f"{path.relative_to(_REPO)}: {lines} lines"
                )
>       assert not offenders, (
            "broker density guard failed — carve a typed concern module; don't bump "
            "the budget:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: broker density guard failed — carve a typed concern module; don't bump the budget:
E           kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 301 lines
E       assert not ['kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 301 lines']

tests/unit/test_kernel_effect_fence.py:457: AssertionError
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
1 failed, 2 warnings in 0.31s
```

### Captured run — 2026-07-26T22:19:42Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
.                                                                        [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 2 warnings in 0.26s
```

### Captured run — 2026-07-26T22:19:55Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
F                                                                        [100%]
=================================== FAILURES ===================================
___________ test_kernel_broker_has_zero_driver_specific_conditionals ___________

    def test_kernel_broker_has_zero_driver_specific_conditionals() -> None:
        findings = [
            finding
            for path in _broker_modules()
            for finding in _driver_conditional_findings(path)
        ]
>       assert not findings, (
            "broker driver-conditional census expected zero; typed operation modules "
            "must own driver behavior:\n  " + "\n  ".join(findings)
        )
E       AssertionError: broker driver-conditional census expected zero; typed operation modules must own driver behavior:
E           driver-specific conditional in broker module: holdspeak/kernel/broker.py:2 (match dispatch)
E       assert not ['driver-specific conditional in broker module: holdspeak/kernel/broker.py:2 (match dispatch)']

tests/unit/test_kernel_effect_fence.py:528: AssertionError
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals
1 failed, 2 warnings in 0.28s
```

### Captured run — 2026-07-26T22:20:09Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
.                                                                        [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 2 warnings in 0.25s
```

### Captured run — 2026-07-26T23:00:06Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
......                                                                   [100%]
6 passed in 0.76s
```

### Captured run — 2026-07-26T23:03:06Z

- **Command:** `env NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost zsh -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/hs-106-03-captured-full-suite.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
.s...................................................................... [  5%]
.......................................................ss............... [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 55%]
..........s............................................................. [ 57%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 96%]
........................................................................ [ 97%]
........................................................................ [ 99%]
..................                                                       [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/.venv/lib/python3.14/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-8faa6792
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/core.py", line 1383, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1082, in _bootstrap_inner
      self._context.run(self.run)
      ~~~~~~~~~~~~~~~~~^^^^^^^^^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1024, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/meetings.py", line 440, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

tests/integration/test_web_transcript_import_api.py::test_garbage_transcript_marks_the_row_honestly_and_is_removable
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/.venv/lib/python3.14/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-5c3d0cd6
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/core.py", line 1383, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1082, in _bootstrap_inner
      self._context.run(self.run)
      ~~~~~~~~~~~~~~~~~^^^^^^^^^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1024, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/holdspeak/db/meetings.py", line 440, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_live_bus.py:24: needs Playwright + a browser
SKIPPED [1] tests/e2e/test_route_preflight.py:26: pre-flight needs Playwright + a browser
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ad8939833d1006d21/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
4230 passed, 41 skipped, 2 warnings in 806.97s (0:13:26)
```

### Captured run — 2026-07-26T23:17:05Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df6be66562be2cc682add6ba9706a17c381aed21

```text
......                                                                   [100%]
6 passed in 0.99s
```
