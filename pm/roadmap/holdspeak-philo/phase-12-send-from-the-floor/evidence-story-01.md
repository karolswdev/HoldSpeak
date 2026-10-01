# Evidence - PHILO-12-01

- **Story:** PHILO-12-01 - The artifact source and the Floor binding
- **Status:** done
- **Date:** 2026-09-30

## Proof

### Captured run — 2026-10-01T02:42:44Z

- **Command:** `bash .tmp/philo-12-01/focused.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
238 tests collected in 1.21s
........................................................................ [ 30%]
........................................................................ [ 60%]
........................................................................ [ 90%]
......................                                                   [100%]
238 passed in 66.48s (0:01:06)
```

### Captured run — 2026-10-01T02:43:05Z

- **Command:** `bash .tmp/philo-12-01/web-checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
src/desk/floorSendBinding.test.ts > Floor send binding > exposes send only for the four primitive document kinds
src/desk/floorSendBinding.test.ts > Floor send binding > binds decision to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds artifact to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting summary to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting digest to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting followup to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds project latest published update to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > binds brief exact stored id to its exact document reference
src/desk/floorSendBinding.test.ts > Floor send binding > defaults a meeting to Summary
src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for meeting without a summary
src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for project without a published update
src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for parked destination
src/desk/floorSendBinding.test.ts > Floor send binding > keeps a unread fact pending instead of refusing
src/desk/floorSendBinding.test.ts > Floor send binding > keeps a loading fact pending instead of refusing
src/desk/floorSendBinding.test.ts > Floor send binding > keeps a failed fact pending instead of refusing
src/desk/floorSendBinding.test.ts > Floor send binding > keeps destination and brief as explicit nonprimitive projection data

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-12-01/web

 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > exposes send only for the four primitive document kinds 1ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds decision to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds artifact to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting summary to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting digest to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds meeting followup to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds project latest published update to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > binds brief exact stored id to its exact document reference 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > defaults a meeting to Summary 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for meeting without a summary 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for project without a published update 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > names the known absence for parked destination 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > keeps a unread fact pending instead of refusing 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > keeps a loading fact pending instead of refusing 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > keeps a failed fact pending instead of refusing 0ms
 ✓ src/desk/floorSendBinding.test.ts > Floor send binding > keeps destination and brief as explicit nonprimitive projection data 0ms

 Test Files  1 passed (1)
      Tests  16 passed (16)
   Start at  20:43:07
   Duration  492ms (transform 57ms, setup 74ms, import 45ms, tests 5ms, environment 263ms)


> holdspeak-web@0.0.1 typecheck
> tsc --noEmit

Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 3020 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-10-01T02:44:09Z

- **Command:** `bash .tmp/philo-12-01/full-suite.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
Python: Python 3.13.14
Isolated HOME and basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.TKUyajkb3u
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................................................................ [  1%]
........................................................................ [  2%]
........................................................................ [  2%]
........................................................................ [  3%]
..................................................F..................... [  3%]
........................................................................ [  4%]
........................sssssssssss.sssss.ssssss........................ [  4%]
........................................................................ [  5%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
........................................................................ [  7%]
........................................................................ [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 11%]
............F........................................................... [ 11%]
........................................................................ [ 12%]
..........................s........s.................................... [ 12%]
.................................ss........................ss........... [ 13%]
........................................................................ [ 13%]
........................................................................ [ 14%]
........................................................................ [ 14%]
.....s...........................................s.........s.ssss....... [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 18%]
........................................................................ [ 19%]
........................................................................ [ 19%]
...............................................ss....................... [ 20%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
.............s.........ss............................................... [ 23%]
........................................................................ [ 23%]
......................................ss................................ [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 25%]
........................................................................ [ 26%]
.................................................F...................... [ 26%]
........................................................................ [ 27%]
...........................................F............................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 28%]
........................................................................ [ 29%]
........................................................................ [ 29%]
..............s......................................................... [ 30%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 33%]
..................s..................................................... [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
..................F..................................................... [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
....................................................ss.................. [ 46%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
....................................................s................... [ 48%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
...........................F............................................ [ 50%]
........................................................................ [ 50%]
.............................................F.......................... [ 51%]
.................................ssss.ss................................ [ 51%]
........................................................................ [ 52%]
.....................................s.........sss...................... [ 53%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 55%]
........................................................................ [ 56%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 65%]
........................................................................ [ 66%]
x....................................................................... [ 66%]
........................................................................ [ 67%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 70%]
........................................................................ [ 71%]
.............F.......................................................... [ 71%]
...........................................s............................ [ 72%]
........................................................................ [ 72%]
........................................................................ [ 73%]
.........................................................s.............. [ 74%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
.s...................................................................... [ 76%]
........................................................................ [ 76%]
.........................................F...........s.................. [ 77%]
........................................................................ [ 77%]
.........................................................x.............. [ 78%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 89%]
........................................................................ [ 90%]
...........s............................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 92%]
..............................x......................................... [ 93%]
....................................................s................... [ 93%]
........................................................................ [ 94%]
..............................................x....................F.... [ 95%]
..............................................................ss.sssssss [ 95%]
sss.............sssssssss............................................... [ 96%]
.........ssss........ssssss...........................................ss [ 96%]
ssssssss.s.............................................................. [ 97%]
........................................................................ [ 97%]
........................................................................ [ 98%]
........................................................................ [ 98%]
..........................................................s............. [ 99%]
..sss................................................................... [ 99%]
...................................                                      [100%]
=================================== FAILURES ===================================
_________________ test_committed_manifest_matches_the_live_app _________________
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-12-01/.venv/bin/python

committed = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...web.routes.activity.enrichment', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': []}}
live = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...web.routes.activity.enrichment', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': []}}

    def test_committed_manifest_matches_the_live_app(committed, live) -> None:
>       assert committed["routes"] == live["routes"], (
            "the committed API-surface manifest drifted from the live app/call "
            "sites — regenerate: uv run python scripts/gen_api_surface.py"
        )
E       AssertionError: the committed API-surface manifest drifted from the live app/call sites — regenerate: uv run python scripts/gen_api_surface.py
E       assert [{'consumers'...ations'}, ...] == [{'consumers'...ations'}, ...]
E         
E         At index 80 diff: {'path': '/api/briefs/{brief_id}', 'methods': ['GET'], 'module': 'web.routes.project_briefs', 'consumers': ['web']} != {'path': '/api/brief/{brief_id}', 'methods': ['GET'], 'module': 'web.routes.monday_brief', 'consumers': ['web']}
E         Right contains one more item: {'consumers': ['web'], 'methods': ['WS'], 'module': 'web.routes.system.voice_stream', 'path': '/ws/dictation/stream'}
E         Use -v to get more diff

tests/unit/test_api_surface.py:52: AssertionError
__ test_promotion_cancellation_after_provider_return_never_publishes_artifact __
[gw11] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-12-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.TKUyajkb3u/pytest/popen-gw11/test_promotion_cancellation_af0')

    def test_promotion_cancellation_after_provider_return_never_publishes_artifact(tmp_path):
        db = Database(tmp_path / "promotion.db")
        _accepted_meeting_decision(db, "dec-fence")
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
        _profile(db, "promotion")
        InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
            "command_id": "assign-promotion", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
            "entries": [{"profile_id": "promotion", "profile_revision": 1}],
        })
        from holdspeak.kernel.runtime import _configure
        broker = _configure(db)
        owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    
        class CancellingIntel:
            def run_prompt(self, **_):
                with db._connection() as conn:
                    parent_id = conn.execute(
                        "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
                    ).fetchone()[0]
                # The durable parent cancellation lands while the provider call is
                # in flight, before the runner can elect a successful child receipt.
                broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
                return "late draft that must not publish"
    
        broker.inference_runner._engine_factory = lambda _revision, **_kw: CancellingIntel()
        service = DecisionLifecycleService(db, kernel=broker)
        # The child's provider work completed, so its receipt is EARNED
        # (succeeded); the cancellation election fences PUBLICATION instead —
        # the finalize discard refuses the artifact by name.
        with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
            asyncio.run(service.draft_promoted_with_model(owner, "dec-fence", "note", {}))
    
        with db._connection() as conn:
            parent_id = conn.execute(
                "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
            ).fetchone()[0]
            child_id = conn.execute(
                "SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?",
                (parent_id,),
      
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-10-01T03:56:54Z

- **Command:** `.venv/bin/python .tmp/philo-12-01/serial-failures.py 1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
ROUND 1 NODE 1: tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact
.                                                                        [100%]
1 passed in 0.76s
ROUND 1 NODE 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 9.49s
ROUND 1 NODE 3: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_speak_loop_393 ______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo12-serial-my0vzx9u/pytest/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10a81cd60>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:354: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:52348/'>, width = 393

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
>       assert landed == APPLIED_TEXT, landed
E       AssertionError: Ship the queue for platform on schedule
E       assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E         
E         - Ship the Q4 platform in October
E         + Ship the queue for platform on schedule

tests/e2e/test_hs176_loop_glass.py:276: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
1 failed in 7.22s
ROUND 1 NODE 4: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
.                                                                        [100%]
1 passed in 23.09s
ROUND 1 NODE 5: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
.                                                                        [100%]
1 passed in 18.57s
ROUND 1 NODE 6: tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
.                                                                        [100%]
1 passed in 6.31s
ROUND 1 NODE 7: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_create_keeps_an_unrelated_delete_failure[1440]
.                                                                        [100%]
1 passed in 28.22s
```

### Captured run — 2026-10-01T03:58:51Z

- **Command:** `.venv/bin/python .tmp/philo-12-01/serial-failures.py 2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
ROUND 2 NODE 1: tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact
.                                                                        [100%]
1 passed in 0.68s
ROUND 2 NODE 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 8.86s
ROUND 2 NODE 3: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
.                                                                        [100%]
1 passed in 8.90s
ROUND 2 NODE 4: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
.                                                                        [100%]
1 passed in 22.69s
ROUND 2 NODE 5: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
.                                                                        [100%]
1 passed in 22.17s
ROUND 2 NODE 6: tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
.                                                                        [100%]
1 passed in 6.34s
ROUND 2 NODE 7: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_create_keeps_an_unrelated_delete_failure[1440]
.                                                                        [100%]
1 passed in 28.40s
```

### Captured run — 2026-10-01T04:00:48Z

- **Command:** `.venv/bin/python .tmp/philo-12-01/base-speak.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
BASE 27d8bf1a RUN 1: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_speak_loop_393 ______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo12-base-speak-7jmk54ms/pytest/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10b26ad70>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:345: in _run
    _init_desk(page, url)
tests/e2e/test_hs176_loop_glass.py:119: in _init_desk
    _normal_chair(page)
tests/e2e/glass_infra.py:360: in _normal_chair
    chair.wait_for()
../../../.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x1115501a0>
cb = <function Channel.send.<locals>.<lambda> at 0x111557b00>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for locator(".chair") to be visible

../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
---------------------------- Captured stdout setup -----------------------------
[glass_infra] web bundle rebuilt in 6.8s
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
ERROR    holdspeak.web.routes.setup:runtime_support.py:71 Failed to build setup status: trust destination registry is not available
=========================== short test summary info ============================
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - playwright._...
1 failed in 40.70s
BASE 27d8bf1a RUN 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_speak_loop_393 ______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo12-base-speak-g8b_436y/pytest/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x108e40e90>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:345: in _run
    _init_desk(page, url)
tests/e2e/test_hs176_loop_glass.py:119: in _init_desk
    _normal_chair(page)
tests/e2e/glass_infra.py:360: in _normal_chair
    chair.wait_for()
../../../.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10efc4440>
cb = <function Channel.send.<locals>.<lambda> at 0x10f5582c0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for locator(".chair") to be visible

../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
ERROR    holdspeak.web.routes.setup:runtime_support.py:71 Failed to build setup status: trust destination registry is not available
=========================== short test summary info ============================
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - playwright._...
1 failed in 32.81s
BASE 27d8bf1a RUN 3: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_speak_loop_393 ______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo12-base-speak-dlvhtnbk/pytest/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10963ce90>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:345: in _run
    _init_desk(page, url)
tests/e2e/test_hs176_loop_glass.py:119: in _init_desk
    _normal_chair(page)
tests/e2e/glass_infra.py:360: in _normal_chair
    chair.wait_for()
../../../.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10f7c01a0>
cb = <function Channel.send.<locals>.<lambda> at 0x10fd57ec0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for locator(".chair") to be visible

../../../.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
ERROR    holdspeak.web.routes.setup:runtime_support.py:71 Failed to build setup status: trust destination registry is not available
=========================== short test summary info ============================
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - playwright._...
1 failed in 32.41s
```

### Captured run — 2026-10-01T04:03:16Z

- **Command:** `.venv/bin/python .tmp/philo-12-01/base-speak-v2.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
BASE 27d8bf1a RUN 1: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

.                                                                        [100%]
1 passed in 6.46s
BASE 27d8bf1a RUN 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

.                                                                        [100%]
1 passed in 6.45s
BASE 27d8bf1a RUN 3: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
3.13.14 (main, Jul 18 2026, 16:56:45) [Clang 22.1.3 ]
/Users/karol/dev/tools/wt-philo-12-01/.tmp/philo-12-01/base-27d8bf1a/holdspeak/__init__.py

.                                                                        [100%]
1 passed in 6.35s
```

### Captured run — 2026-10-01T04:04:01Z

- **Command:** `bash .tmp/philo-12-01/speak-confirm.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
.                                                                        [100%]
1 passed in 9.17s
```

### Captured run — 2026-10-01T04:04:33Z

- **Command:** `bash .tmp/philo-12-01/corrections.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
115 tests collected in 0.36s
........................................................................ [ 62%]
...........................................                              [100%]
115 passed in 4.70s
```

## Full-run tail and reading

The DW capture above reached its output limit. The complete, unedited output is [full-suite.log](assets/story-01-logs/full-suite.log). Its final lines are:

```text
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
FAILED tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 - AssertionEr...
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
FAILED tests/unit/test_philo10_atlas.py::test_the_counts_over_every_atlas_file
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
FAILED tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file
FAILED tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_create_keeps_an_unrelated_delete_failure[1440]
10 failed, 13592 passed, 117 skipped, 4 xfailed, 15 warnings in 4252.20s (1:10:52)
```

Every red is classified in [lane-01-astra.md](lane-01-astra.md), with exact node names and repeat logs. The three class-(a) inventory corrections pass 115 scoped tests. All seven class-(c) behavioral failures have two fresh serial passes; the extra 393 Speak failure and the three green base comparisons are retained and named. No claim that the full run was green.

## Source, binding and glass proof

[Raw source/lifecycle/brief/binding output](assets/story-01-logs/) includes collection, real-producer reds and greens, and the canonical-footer seam's separate red/green. [Actual atlas observations and shots](assets/story-01-walks/) retain artifact preview/prepare red and green runs, plus the existing project-update Send receipt at 1440 and 393. Astra inspected all four glass shots. The artifact face belongs to story 03. The lane record maps each acceptance criterion to its observed proof and names the rejected proof attempts.

All worker model records, scripts and verification limits are retained beside this evidence. DRAFT / UNCHECKED — awaiting Muad'Dib's counsel on built.

### Captured run — 2026-10-01T04:07:19Z

- **Command:** `bash .tmp/philo-12-01/generated-checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f20bdc5bbdc09c1f0b47e91d3f35183f5fe0d6cf

```text
OK docs/generated/operations.json
Architecture documentation checked (10 outputs).
OpenAPI: 582 paths
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
dw check: ok
```
