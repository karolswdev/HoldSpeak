# Evidence - HS-200-42

- **Story:** HS-200-42 - Make a finished meeting actually produce intelligence
- **Status:** done
- **Date:** 2026-09-14

## Proof

### Captured run — 2026-09-15T03:59:46Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.I9mhsKdjvB uv run pytest -q -p no:randomly tests/unit/test_phase200_intel_drain.py tests/unit/test_intel_queue.py tests/unit/test_intel_command.py tests/unit/test_intel_process_aftercare_callback.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/unit/test_phase200_ci_isolation.py tests/unit/test_runtime_queue_frame.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1723abd09d5fb668fd9b0ba74d9300fc2c3a5330

```text
........................................................................ [ 58%]
....................................................                     [100%]
124 passed in 173.50s (0:02:53)
```

### Captured run — 2026-09-15T04:41:26Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.3u71rZ6O34 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:randomly tests/unit/test_doc_drift_guard.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase200_intel_drain.py tests/unit/test_runtime_queue_frame.py tests/e2e/test_hs170_meetings_glass.py tests/e2e/test_hs176_loop_glass.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 5ade218d0cba7fb80aa50d5d34ad4833ee11b25c

```text
.............................................................F           [100%]
=================================== FAILURES ===================================
_____________________________ test_speak_loop_393 ______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-7955/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x112c79860>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:374: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:356: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:50609/'>, width = 393

    def _loop(page: Any, width: int) -> None:
        _dry_run_on(page)
    
        # ── 1. land, judge, teach ──────────────────────────────────────
        result = _land(page, HEARD)
        result.get_by_role("button", name="Wrong").click()
        teach = page.locator(".speak-teach")
        teach.wait_for(timeout=8000)
        said = teach.get_by_role("textbox", name="What you said")
        assert said.input_value() == HEARD, said.input_value()
        said.fill(SAID)
        page.get_by_role("button", name="Teach correction").click()
        receipt = page.locator(".speak-receipt")
        receipt.wait_for(timeout=8000)
        assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()
    
        # ── 2. speak it again, in the SAME session: the rule fires ─────
        result = _land(page, AGAIN)
        landed = result.locator(".speak-result-text").inner_text()
        assert landed == APPLIED_TEXT, landed
        chip = result.get_by_role("button", name="Corrections applied")
        chip.wait_for(timeout=8000)
        assert chip.inner_text().strip() == "APPLIED"
        # ONE mic authority on this face (ruling R13): the well carries none
        assert page.locator(".speak-well .desk-mic").count() == 0
        _shot(page, "loop-speak", width)
    
        # ── 3. the Journal wing: both utterances, the two marks ────────
        _wing(page, "Journal")
        page.locator(".speak-journal").wait_for(timeout=10000)
        rows = page.locator(".speak-journal .surface-ledger-row")
        rows.first.wait_for(timeout=10000)
        _settle(page)
        assert rows.count() == 2, rows.count()
        # newest first: the second utterance wears APPLIED, the first TAUGHT
        assert "APPLIED" in rows.nth(0).locator(".journal-mark").inner_text()
        assert "TAUGHT" in rows.nth(1).locator(".journal-mark").inner_text()
    
        # ── 4. the Learned wing: the rule the desk now knows ───────────
        _wing(page, "Learned")
        page.locator(".speak-learned").wait_for(timeout=10000)
        page.locator(".speak-learned .surface-ledger-row").first.wait_for(timeout=10000)
        _settle(page)
        _assert_learned_board(page)
        _shot(page, "learned", width)
    
        # ── 5. Forget: the rule goes, the wing stands quiet ────────────
        row = page.locator(".speak-learned .surface-ledger-row").first
        forget = row.locator(".learned-forget .btn")
        forget.click()
        # one step, in-world: the verb arms itself, no modal (rule A.4)
        assert page.locator('[role="dialog"]').count() == 0
        assert forget.inner_text().strip() == "Forget?", forget.inner_text()
        forget.click()
        page.locator('.speak-learned .surface-state[data-kind="empty"]').wait_for(
            timeout=8000
        )
        _assert_learned_quiet(page)
        _shot(page, "learned-quiet", width)
        # the wire agrees: the store is empty
        assert _api(page, "GET", "/api/dictation/corrections", token=TOKEN)["items"] == []
    
        # ── 6. `Review` reviews: it crosses to the JOURNAL wing ────────
        page.get_by_role("button", name="Review").click()
        page.locator(".speak-journal").wait_for(timeout=8000)
>       assert (
            page.get_by_role("tab", name="Journal").get_attribute("aria-selected") == "true"
        )
E       AssertionError: assert 'false' == 'true'
E         
E         - true
E         + false

tests/e2e/test_hs176_loop_glass.py:324: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
1 failed, 61 passed in 45.83s
```

**Note on the 04:41:26Z capture above (exit 1):** the one failure was
`tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393`, a Phase 176 glass leg
this story does not touch in code. First read as branch-affected (main 6/6
legs, branch 3/6). Bisected: reverting each of this branch's web changes still
failed, and the pre-story base failed under the same load — the failure rate
tracked how busy the machine was, not what was in the tree. The cause is a
pre-existing paint race in the window-wings species (`web/src/desk/surface/
wings.tsx`): the wing strip lives in the window head and was bridged to the
body by a passive `useEffect`, so every wing change painted in two commits
and the head named the old wing over the new body for up to ~600 ms at 393.
Line 324 reads `aria-selected` on the Journal tab the instant the body
appears. Fixed at the source with `useLayoutEffect` (head and body land in
one paint, every window that uses wings); measured lag 0 ms; 6/6 serial runs
green after the fix (the last capture below). The failing capture is kept as
the honest record.

### Captured run — 2026-09-15T04:44:32Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.0kYDY8M7Am PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:randomly tests/unit/test_doc_drift_guard.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase200_intel_drain.py tests/unit/test_runtime_queue_frame.py tests/e2e/test_hs170_meetings_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5ade218d0cba7fb80aa50d5d34ad4833ee11b25c

```text
............................................................             [100%]
60 passed in 33.23s
```

### Captured run — 2026-09-15T05:12:41Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8Ls25hZsEt PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:randomly tests/e2e/test_hs176_loop_glass.py tests/e2e/test_hs168_window_wings_glass.py tests/e2e/test_hs176_journal_glass.py tests/e2e/test_hs170_meetings_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a6c1d9b0f687d4b60b64357e48e659ea4f6f5820

```text
.................                                                        [100%]
17 passed in 90.51s (0:01:30)
```
