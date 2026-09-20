# Evidence - HS-201-08

- **Story:** HS-201-08 - Main is green
- **Status:** done
- **Date:** 2026-09-20

## Final verification — 2026-09-20 UTC

The quiet-tree full run completed at 100%, exit 0. Capture **2026-09-20T07:18:40Z**, isolated HOME, four xdist workers with work stealing, only `tests/e2e/test_metal.py` ignored:

```text
========== 11264 passed, 116 skipped, 4 xfailed in 1508.86s (0:25:08) ==========
```

All original six, the notification family and all 12 named failures in the historical charter audit pass in this run. The normalized skip summary is identical to the first complete run's 116. The same four strict proposal-chain xfails remain; no new skip, xfail or serial mark. Raw log SHA256: `f1c2047d3aeef8a5e0a96ce9f0f65d41be6517f96814eeb1918a1344c111f6e3`.

Final web check: **274 files / 2,601 tests passed**, architecture/type/build/bundle checks passed; inherited-baseline check reports zero branch-new. All **eleven documentation CI commands** passed under Python 3.12 at **07:17:48Z**, input tree **6c8c47bdfeeae64d3246cd592aa309a3a0e9f645**. OpenAPI/API tests pass in the full Python 3.13 runtime suite. Earlier 2,599-test web and earlier input-tree captures below are historical, superseded by these final checks.

Day 2 continuity is proven from a seeded day-1 state. The current first-use summary path does not create the decision or commitment that day 2 carries. No current owner creation path is proven by this rig. The historical fixture uses actual plugin structured output; artifact type, title, status, confidence and sources are fixture envelope values, with no plugin-run row or `synthesize_meeting_artifacts` chain. This limit also applies to day-2 faces that read those envelope fields.

Astra viewed all 18 story shots and re-viewed the original eight after the final run: before, Allow is primary while Deny has focus; after, Deny is primary and focused, including reload at 1440/393; the restarted Ask reads SAVED HERE at both widths. The reload still loses the reason row (BACKLOG). The 393 day-2 preparation shot shows the top only; the carried rows are proven by DOM assertions. All shots are isolated rigs, not the owner's desk.

After this run, 444 unrelated tracked rig artifacts were restored byte-for-byte with `git show HEAD:path`; nine new artifacts were parked under `.tmp/hs201-green/parked-rig-churn/after-final-full`. The preceding restore had handled 470 tracked and 11 new artifacts. Only 18 story-08 PNGs ship. No source, test, generator or metadata input changes after the final docs input tree are permitted; the final staged delta proof follows below.

Built counsel is in `checks/story-08-late-built-muaddib.md`; the D5 original and correction remain beside it. The seven repair groups and the first complete run's six failures remain visible. Story 07 and the owner sitting stay open. This record proves local verification; the gated commit and exact-title PR supply delivery records. No merge is authorized.

CI-only unknowns at local closure: the three original Ubuntu unit failures, generated/OpenAPI equality under CI's Python 3.12 environment, and serial macOS E2E ordering. The high-descriptor condition is proven by the local 1,050-descriptor probe, not exercised by CI. A failed branch check reopens verification.

## Classification and scope

Doctrine: (a) stale test posture or invalid platform/setup precondition, with still-valid states pinned; (b) a real defect, repaired at its code source without weakening the invariant; (c) an unrelated flake, requiring two serial-green runs and a named source. No unresolved (c) claim is used to close this story.

| Failure family | Class | Cause and repair | Proof |
|---|---|---|---|
| CI isolation guard | b — CI harness | Unit CI ran at the account HOME. The observer fallback creates a real installation marker during the suite. The invariant is valid; isolate HOME before collection. | Original Ubuntu failure and local fake-runner pair red; isolated pair/file green. |
| Custody database recreation | a | Unlink/copy allows inode reuse. Create a sibling replacement while the old inode exists, then replace. Custody continues to use the persisted desk identity. | Original Ubuntu assertion red; deterministic replacement test and different/unknown-desk states retained. |
| Warm transcriber reuse | a | The test assumed auto means MLX on every host. Pin actual resolver preconditions for MLX/Mac and faster-whisper/Linux; keep distinct backend/model/language states. | Linux-like resolver probe red, then green with the pinned tests. |
| Guardrail decision | b — product | The server broadcast the decision without persisting it; hydration discarded the live value. Persist before broadcast and hydrate the valid decision, retaining a live decision only for held calls without metadata. | Original glass red; backend/store regressions; actual pending frame, reload, primary/focus assertions and shots at both widths. |
| Both restart glass tests | b — product | First POST failed before saving/restarting. start() returned after lifespan but before the listener bound. Wait for Uvicorn listener readiness and fail on startup exit. | Original macOS CI failures; real event-gated Uvicorn red; startup and restart tests after repair. |
| Completed-project roadmap list / ten glass failures | b — product | Explicit null from DW reached .get on None and broke the entire list. Preserve the valid no-next-story state. | Six route tests: two red, four existing forms green; mixed active/completed list pinned. |
| Philo references / OpenAPI | a | Current source outgrew generated references and four authored anchors. Refresh outputs with accurate baseline/current-source labels; keep checks intact. | Per-check reds captured; reviewed output deltas and final docs/API checks. |
| Eight notification transitions | a | Ambient UTC time fell in the test's 02:00–03:00 quiet window. Pin the implicit clock; retain explicit quiet-hour cases. | Exactly eight failures at injected 02:30 UTC, then 38 passed with the same ambient clock and under -n 4. |
| Weekly brief timestamp | a | A face-wide zero regex rejects valid 00:33 and 08:00. Check actual counter labels and require the face; keep real component zero/positive states. | Scoped glass red then three passed; actual glass assertion rejects rendered zero counters and accepts both timestamps; both shots viewed. |
| Interrupted-send wait | a | A valid pipe descriptor can exceed select’s fixed limit. Use DefaultSelector for the same readiness wait. | Same 1,050-descriptor probe red then green; both real-send tests pass; SIGKILL/reconciliation assertions unchanged. |
| Remote credential glass | c | The real runner-loopback tests leave credentials in a process-global store; page-wide first Revoke hits the wrong row. Give the glass fixture a private store and teardown, and target its row. | Root serial greens twice; named producer sequence 2 failed/6 passed before and 8 passed after. Other credential remains usable. |
| Two-day continuity | a | Analysis-only summary deliberately produces no proposals. Pin that current law, then use a labelled historical fixture for the still-live continuity chain. | Both full-run widths red at proposal wait; both repaired widths pass (71.37s), actual empty-state canaries reject forced work, NOT RUN and day-2 shots viewed. |

The initial CI-isolation worker called its family (a); Astra classifies the missing CI HOME boundary as (b), a harness defect, because the assertion remains correct and unchanged. No product custody or transcriber defect is claimed.

The prior xdist-pollution diagnosis is withdrawn after Muad'Dib's clock falsifier. Story AC5 and the phase decision record carry the amendment, not a serial mark or a generic singleton reset. The two serial-green captures remain below and show why that evidence alone could not diagnose a clock defect.

### Evidence limits and ledger

- The completed original main CI run is 35478778899 at 675401a8. The 321247d2 main run was queued at the initial inspection; the later Unit/docs failures are recorded below. The local baseline at 321247d2 reproduced Guardrail Allow; the other five named tests passed before changes.
- The initial broad diagnostic capture (05:16:13Z, exit 2) was intentionally interrupted after the clock falsifier resolved its purpose. Its output is truncated and it is **not** full-suite proof. Final verification uses a quiet tree and saves a complete raw log before recording its tail.
- The default-path writer is tests/unit/test_124_verify_round3.py::test_pipeline_events_without_filters_returns_recent_events: the MCP database substitution does not substitute observer_or()'s fallback. get_observer() opens the default database. The new CI HOME boundary contains that test state; no owner HOME is used.
- database_identity() still uses file identity and may miss replacement when an inode is reused. This is separate from desk custody; follow-up home remains Phase 200 runtime-identity ownership, not this first-use repair.
- Existing Delivery Workbench bookkeeping errors remain in phase 101 (evidence/status mismatch) and phases 152/153/154/156/200 (missing final summaries). They predate this story and are recorded in the phase's existing ledger.
- Tests use temporary HOME, fake engines where required, and Chromium. They do not observe the owner's microphone or close the Phase 201 sitting.

## Diagnostic accounting and accepted follow-ups

The interrupted run reported eleven failures, listed below. The first ten are class (b), each with the /api/roadmaps NoneType traceback in the complete raw log. The last is class (a), stale OpenAPI. This does not establish that no other failures exist; the final complete run is required.

- FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]
- FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[393]
- FAILED tests/e2e/test_hs144_door_glass.py::test_hs144_door_cold_open_keeps_first_sentence_one_job
- FAILED tests/e2e/test_hs144_door_glass.py::test_hs144_door_populated_glass_action_refusal_and_shots
- FAILED tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_real_hub_states_and_dimensions
- FAILED tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
- FAILED tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393 - As...
- FAILED tests/e2e/test_hs144_door_glass.py::test_meetings_settings_calendar_glass_and_egress_fact
- FAILED tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15
- FAILED tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state
- FAILED tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app

The completed 675401a8 CI run predates Philo and those ten glass tests passed there. The roadmap crash was reproduced locally on 321247d2. At that diagnostic stage, 321247d2 CI was queued. The later Unit/docs failures are recorded below; no roadmap CI failure is inferred from them.

Docs red was three generator drifts plus one invalid metadata anchor cascading into capability/coverage refusals; OpenAPI drift surfaced separately in pytest. Three doctor anchors and the lane-induced redactor shift are repaired. Other silent anchors are follow-up work.

Astra independently recomputed the boundary comparison from the full worktree: 898 candidates before and after, three removed and three added (ignoring line movement). All semantic changes already exist on 321247d2, with no lane edit to those source files.

| Removed inherited candidate | Current source / added candidate |
|---|---|
| doctor.py:663 OpenAI models-compatibility fix text | Named Cloud intel check says live analysis is off for Record, per the accepted Phase 201 change. |
| intel_admission.py:469 auto-title comment | Current displaced_work_for_stop call centralizes the speech-only stop rule. |
| model_library_service.py:379 old Anthropic custody comment | Rewritten comment at :555 remains a candidate. |
| — | model_library_service.py:376 comment naming the existing OpenAI-compatible execution adapter. |
| — | CatalogRail.tsx:254 comment naming onSelect and ZERO requests. |

Worker correction: an incomplete temporary copy omitted extensions/ and falsely reported removal of Firefox's fetch. Astra compared the full worktree and confirmed it remains. The worker also cited line 377 prose; the actual lexical hit is line 376 above. Historical commit attribution is not needed: all three removals are confirmed on lane base 321247d2. API roster grows 693→694 with summary-selection; doctor function keys remain 41→41.

Counsel correction: the old guardrail shot had Allow filled and Deny focused. No Enter gesture was observed. Current Deny is filled and focused. Its persisted reason row still does not hydrate; that species is parked in BACKLOG. CI HOME isolation contains the observer fallback writer; it does not repair the writer.

## Generated-output review

Astra reviewed the refreshed diff: API entries 693→694 and OpenAPI paths 568→569 add only POST /api/concierge/summary-selection; no path or schema was removed or narrowed. The schema uses raw Request, so OpenAPI does not invent its body contract. The supplementary row retains source, consumers, candidate tests and explicit uncertified contract fields, but handler_evidence is empty: nested router-path extraction remains a known gap. Source inspection at holdspeak/web/routes/concierge.py:269–316 confirms the owner check, exact four request keys, and assign_summary with the request principal. This review does not certify downstream egress from OpenAPI.

Doctor function keys stay 41. Five function source bodies reflect inherited Phase 201 edits; three retired live-analysis checks now have one off-state outcome, replacing 3/3/14 legacy outcomes. That change records the existing Record decision, not a new behavior or removed function. Capability/component/trust-boundary IDs stay 77/19/17. The three corresponding YAML outputs change only the four reviewed anchors. Boundary output is the accepted 898→898 delta above. Generator edits change provenance strings only; the immutable snapshot and census are unchanged.

The eleven docs commands use Python 3.12. OpenAPI generation and API surface pytest use the uv Python 3.13 environment with the assembled app dependencies. CI's Python 3.12 Unit job remains required to verify that environment's schema output.

## Web verification

Recorded output from npm --prefix web run check (already executed; not a rerun).
Exit file: 0
Full raw log SHA256: 21ad715be73b28044656cbabc895e8d875cb676f4af88f6e983c5a13b60d46ab
React architecture guard passed (785 source files; zero framework residue).
 Test Files  274 passed (274)
      Tests  2599 passed (2599)
bundle gate passed (Desk JS 1312518 B; Desk CSS 319765 B; source maps 0)

Recorded output from uv run python scripts/check_web_baseline.py --run:
Suite totals: 2599 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new

Captured text below has trailing whitespace trimmed for the commit; commands, results and substantive output are unchanged.

## Proof

### Captured run — 2026-09-20T05:14:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.uV4zVzRY5k PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated tests/unit/test_phase200_task_resume.py::test_custody_survives_the_database_file_being_recreated tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
...F..                                                                   [100%]
=================================== FAILURES ===================================
_________________ test_guardrail_row_renders_and_deny_focused __________________

guardrail_hub = {'broker': <holdspeak.kernel.broker.Broker object at 0x10ec53620>, 'db': <holdspeak.db.core.Database object at 0x10e9f...s._ToolCallEngine object at 0x110f64590>, 'server': <holdspeak.web_server.MeetingWebServer object at 0x10e08ecf0>, ...}

    def test_guardrail_row_renders_and_deny_focused(guardrail_hub: dict) -> None:
        """Guardrail row visible, decision box Deny primary/focused, no overflow."""
        from playwright.sync_api import sync_playwright

        url = guardrail_hub["url"]

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            for width in (1440, 393):
                # Fresh thread + engine state per width
                guardrail_hub["engine"]._pass = 0
                r = _api_direct(url, "POST", "/api/threads",
                                {"title": f"Guardrail glass {width}",
                                 "recipe_id": "hs-seed-mode-chase"})
                assert r["status"] == 201, f"Failed to create thread: {r}"
                thread_id = r["payload"]["id"]

                page = browser.new_page(viewport={"width": width, "height": 900})
                _open_thread(page, url, thread_id)

                composer = page.locator("[data-testid='composer-input']")
                composer.wait_for(state="visible", timeout=10000)

                def _type(text: str) -> None:
                    page.evaluate("""([s,v])=>{const e=document.querySelector(s);if(!e)return;
                        Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,v);
                        e.dispatchEvent(new Event('input',{bubbles:true}));
                        e.dispatchEvent(new Event('change',{bubbles:true}));
                        e.selectionStart=e.selectionEnd=v.length}""",
                        ["[data-testid='composer-input']", text])

                _type("Transition commitment to done")
                page.wait_for_timeout(500)
                send_btn = page.locator("[data-testid='send-button']")
                if send_btn.count() > 0:
                    send_btn.click()
                else:
                    composer.press("Enter")
                page.wait_for_timeout(8000)

                _save_shot(page, "guardrail-row", width, shots_dir=SHOTS_03)

                guardrail_row = page.locator("[data-testid='guardrail-row']")
                if guardrail_row.count() > 0:
                    assert guardrail_row.is_visible(), f"Guardrail row not visible at {width}"
                    violation = page.locator("[data-testid='guardrail-violation']")
                    if violation.count() > 0:
                        vtext = violation.first.inner_text().lower()
                        assert "source" in vtext or "people" in vtext, (
                            f"Violation text unexpected at {width}: {vtext}")

                decision_box = page.locator("[data-testid='decision-box']")
                if decision_box.count() > 0:
                    _save_shot(page, "guardrail-decision-box", width, shots_dir=SHOTS_03)
                    dd = decision_box.first.get_attribute("data-default-decision")
>                   assert dd == "deny", f"Expected deny, got '{dd}' at {width}"
E                   AssertionError: Expected deny, got 'allow' at 1440
E                   assert 'allow' == 'deny'
E
E                     - deny
E                     + allow

tests/e2e/test_hs153_practice_glass.py:578: AssertionError
---------------------------- Captured stdout setup -----------------------------
[glass_infra] web bundle rebuilt in 5.6s
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
------------------------------ Captured log call -------------------------------
ERROR    uvicorn.error:httptools_impl.py:421 Exception in ASGI application
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/httptools_impl.py", line 416, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1135, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 191, in __call__
    with recv_stream, send_stream, collapse_excgroups():
                                   ~~~~~~~~~~~~~~~~~~^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    raise exc
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/holdspeak/web_server.py", line 608, in _web_auth_gate
    return await call_next(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 115, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 101, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 355, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 243, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-201-a/holdspeak/web/routes/roadmaps.py", line 185, in api_roadmaps
    return JSONResponse({"roadmaps": await asyncio.to_thread(read)})
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/Users/karol/dev/tools/wt-201-a/holdspeak/web/routes/roadmaps.py", line 180, in read
    project = _project(root, directory.name, include_phases=False)
  File "/Users/karol/dev/tools/wt-201-a/holdspeak/web/routes/roadmaps.py", line 147, in _project
    next_story = next_data.get("story_id") or next_data.get("id") or next_data.get("next_story", {}).get("story_id")
                                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get'
=========================== short test summary info ============================
FAILED tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused
1 failed, 5 passed in 28.85s
```

### Captured run — 2026-09-20T05:15:13Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.23SYQg0LB2 uv run pytest -q tests/unit/test_phase200_attention.py::TestNotificationTransitions`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.............                                                            [100%]
13 passed in 1.90s
```

### Captured run — 2026-09-20T05:15:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.c35OvhlKLq uv run pytest -q tests/unit/test_phase200_attention.py::TestNotificationTransitions`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.............                                                            [100%]
13 passed in 1.83s
```

### Captured run — 2026-09-20T05:15:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ONjIZsjnDG uv run pytest -q -n 4 tests/unit/test_phase200_attention.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
bringing up nodes...
bringing up nodes...

......................................                                   [100%]
38 passed in 1.47s
```

### Captured run — 2026-09-20T05:16:13Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.YtP8Gg6eqa PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 4 --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
...............ssssssssssssssssssssssssssss............................. [  1%]
........................................................................ [  2%]
........................................................................ [  3%]
........................................................................ [  3%]
............................................F........................... [  4%]
........................................................................ [  5%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
....................................................................F... [  7%]
................................F....................................... [  8%]
..............F......................................................... [  8%]
........................................................................ [  9%]
........................................................................ [ 10%]
..F................................................................F.... [ 10%]
................................F.....................F................. [ 11%]
....................................Fs.................................. [ 12%]
........................................................................ [ 12%]
....F.................................................s................. [ 13%]
........................................................................ [ 13%]
.....................................................ss................. [ 14%]
..........s...............................................ss............ [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
...........s............................................................ [ 19%]
........................................................................ [ 19%]
........................................................................ [ 20%]
............................s............ss....ss.....ss................ [ 20%]
................................s.........sssss......................... [ 21%]
................................................ss...........s.......... [ 22%]
...............s........................................................ [ 22%]
........................................................................ [ 23%]
........................................s............................... [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 29%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
................................F....................................... [ 36%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 46%]
........................................................................ [ 47%]
.....................................................................F.. [ 48%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 50%]
..........................................................
=================================== FAILURES ===================================
___________________ test_thought_workbench_real_glass[1440] ____________________
[gw0] darwin -- Python 3.13.11 /Users/karol/dev/tools/wt-201-a/.venv/bin/python3

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9083/popen-gw0/test_thought_workbench_real_gl0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x11796ec90>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_thought_workbench_real_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
        from playwright.sync_api import sync_playwright
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database
        from holdspeak.kernel.runtime import _configure
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        home = tmp_path / "home"
        home.mkdir()
        model = tmp_path / "deterministic-this-machine.gguf"
        model.touch()
        browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        provider = {"path": str(model)}
        monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: provider["path"])
        reset_database()
        database = db_core.get_database()
        engine = _InterviewEngine()
        broker = _configure(database)
        monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
        callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
        server = MeetingWebServer(callbacks, auth_token=TOKEN)
        url = server.start()
        errors: list[str] = []
        console_errors: list[str] = []
        requests: list[str] = []
        responses: list[tuple[str, int]] = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on("request", lambda request: requests.append(request.url) if "/api/thoughts/" in request.url else None)
                page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
                created = _api(page, "POST", "/api/thoughts", {
                    "request_id": str(uuid.uuid4()),
                    "raw_text": "RAW CUSTODY PHRASE — launch ownership first capture.",
                    "source": {"kind": "typed"},
                    "initial_note": {
                        "title": "Launch ownership",
                        "body_markdown": "Launch ownership needs one accountable person.",
                        "tags": ["launch"],
                    },
                })
                thought = created["thought"]
                page.evaluate(
                    "([id, receipt]) => sessionStorage.setItem(`hs.thought.default-context-receipt.${id}`, JSON.stringify(receipt))",
                    [thought["id"], created["default_context_receipt"]],
                )
                page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

                workspace = page.get_by_role("region", name="Thought", exact=True)
                try:
                    workspace.wait_for(timeout=10000)
                except Exception:
                    page.screenshot(path=f"/tmp/holdspeak-thought-workbench-open-failure-{width}.png", full_page=False)
                    raise AssertionError({"body": page.locator("body").inner_text(), "errors": errors,
                                          "console": console_errors, "requests": requests})
                page.get_by_role("region", name="Note", exact=True).wait_for()
                primary = workspace.locator(".thought-state-primary")
                primary.wait_for()
                assert primary.inner_text() == "Ask AI"
                idle_box = primary.bounding_box()
                assert idle_box
                assert workspace.locator(".btn--primary:visible").count() == 1
                assert page.get_by_text("Good enough").count() == 0
                assert page.get_by_text("Keep refining").count() == 0
                assert page.get_by_text("Finish instead").count() == 0
                formatting = workspace.get_by_role("toolbar", name="Markdown formatting")
                formatting.wait_for()
                for control in ["Bold", "Italic", "Underline"]:
                    assert formatting.get_by_role("button", name=control).is_visible()
                assert formatting.get_by_role("button", name="H1").is_visible()
                assert formatting.get_by_role("button", name="List").is_visible()

                window_box = workspace.bounding_box()
                assert window_box and window_box["y"] >= 48
                assert window_box["y"] + window_box["height"] <= 900
                note_box = page.get_by_role("region", name="Note", exact=True).bounding_box()
                if width == 1440:
                    interview_box = page.get_by_role("region", name="Interview", exact=True).bounding_box()
                    assert window_box["width"] >= 1000, workspace.evaluate("el => ({style: el.getAttribute('style'), width: getComputedStyle(el).width, minWidth: getComputedStyle(el).minWidth, classes: el.className})")
                    assert note_box and interview_box
                    assert note_box["width"] >= 650 and note_box["height"] >= 360
                    assert 300 <= interview_box["width"] <= 380 and interview_box["height"] >= 360
                    assert note_box["x"] + note_box["width"] <= interview_box["x"] + 1
                    assert note_box["y"] == pytest.approx(interview_box["y"], abs=1)
                else:
                    hidden_interview = workspace.locator(".thought-interview")
                    assert hidden_interview.get_attribute("aria-hidden") == "true"
                    assert hidden_interview.get_attribute("inert") is not None
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert page.evaluate("document.body.scrollWidth <= innerWidth")
                page.screenshot(path=f"/tmp/holdspeak-thought-workbench-idle-{width}.png", full_page=False)

                # A real durable Note edit while ASKING must suppress the frozen
                # result. The stale question never reaches owner-visible state.
                engine.block_next = True
                primary.click()
                if width == 1440:
                    page.get_by_text("Finding one useful question…", exact=True).wait_for(timeout=10000)
                else:
                    page.wait_for_function(
                        "el => el?.textContent?.trim() === 'Stop'",
                        arg=primary.element_handle(),
                        timeout=10000,
                    )
                assert engine.started.wait(5)
                note_editor = page.get_by_role("textbox", name="Note body")
                assert note_editor.get_attribute("contenteditable") == "true"
                note_editor.click()
                page.keyboard.press("Meta+ArrowDown")
                page.keyboard.press("Enter")
                page.keyboard.insert_text("Edited while asking.")
                assert "Edited while asking." in note_editor.inner_text()
                page.keyboard.press("Control+s")
                deadline = time.time() + 5
                edited = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
                while "Edited while asking." not in edited["working_note"]["body_markdown"] and time.time() < deadline:
                    time.sleep(0.05)
                    edited = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
                assert "Edited while asking." in edited["working_note"]["body_markdown"]
                working_statuses = [status for path, status in responses if path.endswith(f"/api/thoughts/{thought['id']}/working")]
                assert working_statuses[-2:] == [409, 200], working_statuses
                engine.release.set()
                page.wait_for_function("el => el?.textContent?.trim() === 'Ask AI'", arg=primary.element_handle(), timeout=20000)
                assert page.get_by_text("STALE QUESTION MUST NOT APPEAR", exact=True).count() == 0

                primary.click()
                if width == 393:
                    page.wait_for_function("el => el?.textContent?.trim() === 'Answer question'", arg=primary.element_handle(), timeout=20000)
                    assert primary.inner_text() == "Answer question"
                    primary.click()
                page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=20000)
                answer = page.get_by_role("textbox", name="Your answer")
                answer.fill("Mina owns the launch.")
                page.screenshot(path=f"/tmp/holdspeak-thought-workbench-question-{width}.png", full_page=False)
                assert primary.inner_text() == "Add & ask next"
                question_box = primary.bounding_box()
                assert question_box and idle_box
                assert question_box["x"] == pytest.approx(idle_box["x"], abs=1)
                assert question_box["y"] == pytest.approx(idle_box["y"], abs=1)
                assert question_box["width"] == pytest.approx(idle_box["width"], abs=1)
                assert workspace.locator(".btn--primary:visible").count() == 1

                # Admission is re-evaluated under the write fence. Remove the only
                # target after the question: answer/focus/key survive the refusal.
                provider["path"] = None
                primary.click()
                page.get_by_text("Couldn't start the next turn. Your answer is still here. Add it to the Note.", exact=True).wait_for(timeout=10000)
                assert answer.input_value() == "Mina owns the launch."
                assert answer.evaluate("el => el === document.activeElement")
                assert engine.calls == 2

                # The refusal did not mutate the review. Restore readiness and
                # reopen its fresh reducer, then exercise the atomic composite.
                provider["path"] = str(model)
                page.reload(wait_until="load")
                workspace = page.get_by_role("region", name="Thought", exact=True)
                workspace.wait_for(timeout=10000)
                primary = workspace.locator(".thought-state-primary")
                if width == 393:
                    workspace.get_by_role("button", name="Interview 1", exact=True).click()
                page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=10000)
                answer = page.get_by_role("textbox", name="Your answer")
                answer.fill("Mina owns the launch.")
                with page.expect_response(
                    lambda response: response.url.endswith("/answer-and-continue"),
                    timeout=10000,
                ) as composite_response:
                    primary.click()
                composite = composite_response.value
                composite_body = composite.json()
                assert composite.status == 202, composite_body
                marker_name = "Added to Note · View" if width == 393 else "Added to Note"
                marker = workspace.get_by_role("button", name=marker_name, exact=True)
                try:
                    marker.wait_for(timeout=10000)
                except Exception:
                    raise AssertionError({
                        "composite": composite_body,
                        "workspace": workspace.inner_text(),
                        "errors": errors,
                        "console": console_errors,
                    })
                if width == 393:
                    marker.click()
                page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for()
                assert workspace.locator(".thought-document-body .cm-scroller").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
                deadline = time.time() + 10
                while engine.calls < 3 and time.time() < deadline:
                    time.sleep(0.05)
                assert engine.calls == 3
                time.sleep(0.35)
                assert engine.calls == 3, "composite child
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-20T05:24:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.pCua2wjFBe PYTHONPATH=/Users/karol/dev/tools/wt-201-a/.tmp/hs201-green:/Users/karol/dev/tools/wt-201-a uv run pytest -q -p attention_wallclock_red_plugin tests/unit/test_phase200_attention.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.......................F..FFFF...FFF..                                   [100%]
=================================== FAILURES ===================================
_ TestNotificationTransitions.test_a_changed_item_with_the_same_count_notifies _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c2ab890>
db = <holdspeak.db.core.Database object at 0x10c34bb60>

    def test_a_changed_item_with_the_same_count_notifies(self, db: Database) -> None:
        """The audit's defect: 3 -> 3 with one item swapped was silent."""
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        first = _sweep(svc, _agg([_row("a"), _row("b"), _row("c")]))
>       assert first["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:508: AssertionError
_ TestNotificationTransitions.test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c381940>
db = <holdspeak.db.core.Database object at 0x10d4e4690>

    def test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a", "p1"), _row("x", "p2")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:556: AssertionError
_________ TestNotificationTransitions.test_restart_renotifies_nothing __________

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c3d6b10>
db = <holdspeak.db.core.Database object at 0x10d4e5590>

    def test_restart_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc1 = _service(db, calls)
        items = _agg([_row("a"), _row("b"), _row("c")])
>       assert _sweep(svc1, items)["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:575: AssertionError
_ TestNotificationTransitions.test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c343130>
db = <holdspeak.db.core.Database object at 0x10d4e5d10>

    def test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a", "p1"), _row("b", "p1")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:590: AssertionError
_ TestNotificationTransitions.test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c343240>
db = <holdspeak.db.core.Database object at 0x10d4e5f90>

    def test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a"), _row("b")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:620: AssertionError
_ TestNotificationTransitions.test_escalation_fires_through_the_sweep_and_says_so _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c30b4d0>
db = <holdspeak.db.core.Database object at 0x10d4e4410>

    def test_escalation_fires_through_the_sweep_and_says_so(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        today = {**_row("k"), "why": "DUE TODAY", "rankClass": "due_today"}
>       assert _sweep(svc, _agg([today, _row("b")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:677: AssertionError
_ TestNotificationTransitions.test_counsel_probe_2b_archived_project_ids_leave_the_settings _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c3e1b70>
db = <holdspeak.db.core.Database object at 0x10d4e5e50>

    def test_counsel_probe_2b_archived_project_ids_leave_the_settings(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a", "p1"), _row("z", "p9")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:694: AssertionError
_ TestNotificationTransitions.test_the_policy_row_is_written_only_when_the_set_or_outcome_changed _

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x10c3e1ef0>
db = <holdspeak.db.core.Database object at 0x10d4e5810>

    def test_the_policy_row_is_written_only_when_the_set_or_outcome_changed(self, db: Database) -> None:
        """Counsel P1-5."""
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        items = _agg([_row("a"), _row("b")])
        writes: list[int] = []
        original = svc._persist_edge

        def counting(*args, **kwargs):
            writes.append(1)
            return original(*args, **kwargs)

        with patch.object(svc, "_persist_edge", side_effect=counting):
>           assert _sweep(svc, items)["outcome"] == "sent"
E           AssertionError: assert 'held_quiet_hours' == 'sent'
E
E             - sent
E             + held_quiet_hours

tests/unit/test_phase200_attention.py:728: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_changed_item_with_the_same_count_notifies
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_restart_renotifies_nothing
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_escalation_fires_through_the_sweep_and_says_so
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_2b_archived_project_ids_leave_the_settings
FAILED tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_the_policy_row_is_written_only_when_the_set_or_outcome_changed
8 failed, 30 passed in 1.88s
```

### Captured run — 2026-09-20T05:25:00Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Xix2BCgCLb PYTHONPATH=/Users/karol/dev/tools/wt-201-a/.tmp/hs201-green:/Users/karol/dev/tools/wt-201-a uv run pytest -q -p linux_backend_plugin tests/unit/test_transcriber_init_race.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.F.                                                                      [100%]
=================================== FAILURES ===================================
________________ test_boot_warm_is_reused_by_a_legacy_dictation ________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10e7e9350>

    def test_boot_warm_is_reused_by_a_legacy_dictation(monkeypatch):
        """HS-200-05: the crash's actual trigger, in two calls.

        The boot warm is ROUTED and passes the resolved engine name it read from the
        speech material (`"mlx"`). A legacy dictation — the owner's desk, which lacks
        the `thoughts-writing-route-assignments` migration and so has no frozen route
        bundle — passes nothing and falls back to `config.model.backend` (`"auto"`).
        Those name the same engine. Before this fix the reuse check compared the
        stored, RESOLVED "mlx" against the requested, RAW "auto", never matched, and
        built a second `_MlxTranscriber` on a second pinned thread FOR EVERY
        UTTERANCE. Its "load" was a process-level mlx_whisper cache hit, so it
        inherited lazy arrays owned by the first thread's stream, and the first eval
        killed the hub with an uncatchable C++ throw.
        """
        built = []
        rt = _runtime(monkeypatch, built, backend="auto")

        warm = rt._ensure_transcriber_loaded(
            model_name="base", backend="mlx", language="auto"
        )
        dictation = rt._ensure_transcriber_loaded()

>       assert len(built) == 1, (
            f"{len(built)} transcribers built for one engine — a second instance in "
            "one process is a process-fatal MLX cross-thread crash in production"
        )
E       AssertionError: 2 transcribers built for one engine — a second instance in one process is a process-fatal MLX cross-thread crash in production
E       assert 2 == 1
E        +  where 2 = len([<tests.unit.test_transcriber_init_race.SlowFakeTranscriber object at 0x10e9e8b90>, <tests.unit.test_transcriber_init_race.SlowFakeTranscriber object at 0x10e9e8cd0>])

tests/unit/test_transcriber_init_race.py:127: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation
1 failed, 2 passed in 1.97s
```

### Captured run — 2026-09-20T05:26:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.mNHbmMs0Eo uv run pytest -q .tmp/hs201-green/test_web_server_startup_probe.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
___________ test_start_does_not_return_before_uvicorn_listener_ready ___________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9093/test_start_does_not_return_bef0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1093d6060>

    def test_start_does_not_return_before_uvicorn_listener_ready(tmp_path, monkeypatch) -> None:
        """Red: lifespan's ``_started`` event precedes Uvicorn listener readiness."""
        import holdspeak.web_server as web_server

        lifespan_done = threading.Event()
        listener_ready = threading.Event()
        returned = threading.Event()
        outcome: dict[str, Any] = {}
        owner: dict[str, Any] = {}

        class FakeUvicornServer:
            def __init__(self, config: Any) -> None:
                self.config = config
                self.started = False
                self.should_exit = False
                owner["uvicorn"] = self

            def run(self) -> None:
                owner["meeting"]._started.set()
                lifespan_done.set()
                listener_ready.wait(timeout=5)
                self.started = True

        monkeypatch.setattr(web_server.uvicorn, "Server", FakeUvicornServer)
        server = _new_server(tmp_path, monkeypatch)
        owner["meeting"] = server

        def start() -> None:
            try:
                outcome["url"] = server.start()
            except BaseException as exc:  # pragma: no cover - red probe capture
                outcome["error"] = exc
            finally:
                returned.set()

        thread = threading.Thread(target=start, daemon=True)
        thread.start()
        try:
            assert lifespan_done.wait(timeout=5), "fake lifespan did not complete"
            # Current code returns as soon as _started is set. The desired code
            # remains blocked until FakeUvicornServer.started becomes true.
>           assert not returned.wait(timeout=1), (
                "MeetingWebServer.start() returned before the Uvicorn listener was ready"
            )
E           AssertionError: MeetingWebServer.start() returned before the Uvicorn listener was ready
E           assert not True
E            +  where True = wait(timeout=1)
E            +    where wait = <threading.Event at 0x1094231d0: set>.wait

.tmp/hs201-green/test_web_server_startup_probe.py:84: AssertionError
_____________ test_start_raises_when_uvicorn_exits_during_startup ______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9093/test_start_raises_when_uvicorn0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1093d5a70>

    def test_start_raises_when_uvicorn_exits_during_startup(tmp_path, monkeypatch) -> None:
        """Red: a failed Uvicorn run must not publish a dead URL."""
        import holdspeak.web_server as web_server

        startup_failed = threading.Event()
        returned = threading.Event()
        outcome: dict[str, Any] = {}
        owner: dict[str, Any] = {}

        class FakeUvicornServer:
            def __init__(self, config: Any) -> None:
                self.config = config
                self.started = False
                self.should_exit = False
                owner["uvicorn"] = self

            def run(self) -> None:
                owner["meeting"]._started.set()
                self.should_exit = True
                startup_failed.set()

        monkeypatch.setattr(web_server.uvicorn, "Server", FakeUvicornServer)
        server = _new_server(tmp_path, monkeypatch)
        owner["meeting"] = server

        def start() -> None:
            try:
                outcome["url"] = server.start()
            except BaseException as exc:
                outcome["error"] = exc
            finally:
                returned.set()

        thread = threading.Thread(target=start, daemon=True)
        thread.start()
        try:
            assert startup_failed.wait(timeout=5), "fake startup failure did not occur"
            assert returned.wait(timeout=5), "start() did not finish after server failure"
        finally:
            server.stop()
            thread.join(timeout=5)

        assert not thread.is_alive(), "startup failure probe thread did not finish"
>       assert "url" not in outcome, outcome
E       AssertionError: {'url': 'http://127.0.0.1:57163'}
E       assert 'url' not in {'url': 'http://127.0.0.1:57163'}

.tmp/hs201-green/test_web_server_startup_probe.py:140: AssertionError
=========================== short test summary info ============================
FAILED .tmp/hs201-green/test_web_server_startup_probe.py::test_start_does_not_return_before_uvicorn_listener_ready
FAILED .tmp/hs201-green/test_web_server_startup_probe.py::test_start_raises_when_uvicorn_exits_during_startup
2 failed in 2.08s
```

### Captured run — 2026-09-20T05:27:15Z

- **Command:** `python3 .tmp/hs201-green/ci_summary.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
REMOTE BASELINE; fetched logs, not a local rerun
{"conclusion": "failure", "headSha": "675401a857b85336d4acaa8c65383dfc9636e4c8", "name": "Tests", "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/35478778899"}
E2E Tests (macOS)	UNKNOWN STEP	2026-09-20T01:09:01.8406400Z FAILED tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused - AssertionError: Expected deny, got 'allow' at 1440
E2E Tests (macOS)	UNKNOWN STEP	2026-09-20T01:09:01.8408440Z FAILED tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart - urllib.error.URLError: <urlopen error [Errno 61] Connection refused>
E2E Tests (macOS)	UNKNOWN STEP	2026-09-20T01:09:01.8409610Z FAILED tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440 - urllib.error.URLError: <urlopen error [Errno 61] Connection refused>
Unit Tests	UNKNOWN STEP	2026-09-20T01:28:50.9494426Z FAILED tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated - AssertionError: assert 'refusing to ...deliberately.' == ''
Unit Tests	UNKNOWN STEP	2026-09-20T01:28:50.9499740Z FAILED tests/unit/test_phase200_task_resume.py::test_custody_survives_the_database_file_being_recreated - AssertionError: assert '770dfca6cafd2ea2' != '770dfca6cafd2ea2'
Unit Tests	UNKNOWN STEP	2026-09-20T01:28:50.9504154Z FAILED tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation - AssertionError: 2 transcribers built for one engine — a second instance in one process is a process-fatal MLX cross-thread crash in production
```

### Captured run — 2026-09-20T05:29:00Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.zIOp3BMouj uv run pytest -q tests/unit/test_web_server_startup.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_____________ test_start_waits_for_listener_after_lifespan_startup _____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9100/test_start_waits_for_listener_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10a0f2d70>

    @pytest.mark.timeout(30)
    def test_start_waits_for_listener_after_lifespan_startup(tmp_path, monkeypatch) -> None:
        """A post-lifespan gate must keep start blocked until Uvicorn binds."""
        server = _server(tmp_path, monkeypatch)
        entered = threading.Event()
        release = threading.Event()
        returned = threading.Event()
        outcome: dict[str, Any] = {}

        async def hold_before_listener() -> None:
            entered.set()
            await asyncio.to_thread(release.wait)

        # MeetingWebServer's own startup handler is registered first and sets its
        # internal event before Uvicorn creates its listener. This handler makes
        # that ordering deterministic without adding a test sleep.
        server.app.router.on_startup.append(hold_before_listener)

        def start() -> None:
            try:
                outcome["url"] = server.start()
            except BaseException as exc:  # pragma: no cover - assertion context
                outcome["error"] = exc
            finally:
                returned.set()

        thread = threading.Thread(target=start, daemon=True)
        thread.start()
        try:
            assert entered.wait(timeout=10), "post-lifespan startup gate did not run"
>           assert not returned.wait(timeout=1), (
                "start() returned before the Uvicorn listener was ready"
            )
E           AssertionError: start() returned before the Uvicorn listener was ready
E           assert not True
E            +  where True = wait(timeout=1)
E            +    where wait = <threading.Event at 0x110d016a0: set>.wait

tests/unit/test_web_server_startup.py:72: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
ERROR    uvicorn.error:on.py:134 Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/starlette/routing.py", line 701, in lifespan
    await receive()
  File "/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/uvicorn/lifespan/on.py", line 137, in receive
    return await self.receive_queue.get()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/asyncio/queues.py", line 186, in get
    await getter
asyncio.exceptions.CancelledError
_____________ test_start_raises_when_uvicorn_exits_during_startup ______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9100/test_start_raises_when_uvicorn0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10a0f2520>

    @pytest.mark.timeout(30)
    def test_start_raises_when_uvicorn_exits_during_startup(tmp_path, monkeypatch) -> None:
        """A failed server must not publish a URL for a dead listener."""
        import holdspeak.web_server as web_server

        startup_failed = threading.Event()
        returned = threading.Event()
        outcome: dict[str, Any] = {}
        owner: dict[str, Any] = {}

        class FailedUvicornServer:
            def __init__(self, config: Any) -> None:
                self.config = config
                self.started = False
                self.should_exit = False
                owner["uvicorn"] = self

            def run(self) -> None:
                # This models Uvicorn completing lifespan and then aborting before
                # it can create a listener. A real started server would remain
                # alive until should_exit; this one never reaches started=True.
                owner["meeting"]._started.set()
                self.should_exit = True
                startup_failed.set()

        monkeypatch.setattr(web_server.uvicorn, "Server", FailedUvicornServer)
        server = _server(tmp_path, monkeypatch)
        owner["meeting"] = server

        def start() -> None:
            try:
                outcome["url"] = server.start()
            except BaseException as exc:
                outcome["error"] = exc
            finally:
                returned.set()

        thread = threading.Thread(target=start, daemon=True)
        thread.start()
        try:
            assert startup_failed.wait(timeout=10), "fake startup failure did not occur"
            assert returned.wait(timeout=10), "start() did not finish after server failure"
        finally:
            server.stop()
            thread.join(timeout=10)

        assert not thread.is_alive(), "startup failure thread did not finish"
>       assert "url" not in outcome, outcome
E       AssertionError: {'url': 'http://127.0.0.1:57417'}
E       assert 'url' not in {'url': 'http://127.0.0.1:57417'}

tests/unit/test_web_server_startup.py:137: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_web_server_startup.py::test_start_waits_for_listener_after_lifespan_startup
FAILED tests/unit/test_web_server_startup.py::test_start_raises_when_uvicorn_exits_during_startup
2 failed in 2.14s
```

### Captured run — 2026-09-20T05:30:52Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.h4zYiqhinZ uv run python .tmp/hs201-green/fake_runner_pytest.py -q tests/unit/test_124_verify_round3.py::test_pipeline_events_without_filters_returns_recent_events tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.F                                                                       [100%]
=================================== FAILURES ===================================
__________________ test_the_running_suite_is_itself_isolated ___________________

    def test_the_running_suite_is_itself_isolated() -> None:
        """The guard, applied to this very run.

        `pytest_configure` already refused if this were a real installation; this
        states the invariant where a reader will see it.
        """
        import os
        import pwd

        home = os.environ.get("HOME") or str(Path.home())
        passwd_home = pwd.getpwuid(os.getuid()).pw_dir
>       assert (
            real_home_violation(
                home, passwd_home, opt_in=os.environ.get(REAL_HOME_OPT_IN, "")
            )
            == ""
        )
E       AssertionError: assert 'refusing to ...deliberately.' == ''
E
E         + refusing to run the product suite against a real HoldSpeak installation: HOME=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.h4zYiqhinZ holds /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.h4zYiqhinZ/.local/share/holdspeak. Run with an isolated HOME instead:
E         +   HOME=$(mktemp -d) uv run pytest ...
E         + An attended live walk sets HOLDSPEAK_ALLOW_REAL_HOME=<walk name> to accept this deliberately.

tests/unit/test_phase200_ci_isolation.py:92: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated
1 failed, 1 passed in 1.09s
```

### Captured run — 2026-09-20T05:30:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.RIdsQ7nl8u uv run pytest -q tests/unit/test_124_verify_round3.py::test_pipeline_events_without_filters_returns_recent_events tests/unit/test_phase200_ci_isolation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
....................                                                     [100%]
20 passed in 1.23s
```

### Captured run — 2026-09-20T05:32:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ndfLUpyQs2 PYTHONPATH=/Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes:/Users/karol/dev/tools/wt-201-a uv run pytest -q -p attention_wallclock tests/unit/test_phase200_attention.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
......................................                                   [100%]
38 passed in 1.84s
```

### Captured run — 2026-09-20T05:32:19Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.gfb63XcB7e uv run pytest -q -n 4 tests/unit/test_phase200_attention.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
bringing up nodes...
bringing up nodes...

......................................                                   [100%]
38 passed in 1.49s
```

### Captured run — 2026-09-20T05:36:33Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.WTf8GbDrty uv run pytest --collect-only -q tests/unit/test_phase200_ci_isolation.py tests/unit/test_phase200_task_resume.py tests/unit/test_transcriber_init_race.py tests/unit/test_phase200_attention.py tests/unit/test_thread_guardrail.py tests/unit/test_web_server_startup.py tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
tests/unit/test_phase200_ci_isolation.py::test_a_real_installation_under_the_account_home_is_refused
tests/unit/test_phase200_ci_isolation.py::test_an_isolated_home_is_lawful
tests/unit/test_phase200_ci_isolation.py::test_a_bare_runner_home_is_lawful
tests/unit/test_phase200_ci_isolation.py::test_the_opt_in_waives_the_refusal_and_is_named
tests/unit/test_phase200_ci_isolation.py::test_a_missing_passwd_entry_does_not_refuse
tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated
tests/unit/test_phase200_ci_isolation.py::test_every_probe_answers_a_string[missing_local_model_reason]
tests/unit/test_phase200_ci_isolation.py::test_every_probe_answers_a_string[missing_mlx_whisper_reason]
tests/unit/test_phase200_ci_isolation.py::test_every_probe_answers_a_string[missing_local_dictation_route_reason]
tests/unit/test_phase200_ci_isolation.py::test_the_local_model_probe_reports_the_absent_path
tests/unit/test_phase200_ci_isolation.py::test_the_local_model_probe_is_silent_when_present
tests/unit/test_phase200_ci_isolation.py::test_the_dictation_route_probe_names_the_missing_package
tests/unit/test_phase200_ci_isolation.py::test_both_readiness_paths_go_through_one_predicate
tests/unit/test_phase200_ci_isolation.py::test_the_predicate_answers_false_for_an_unset_path
tests/unit/test_phase200_ci_isolation.py::test_the_predicate_answers_true_for_a_real_file
tests/unit/test_phase200_ci_isolation.py::test_every_critical_journey_carries_the_marker
tests/unit/test_phase200_ci_isolation.py::test_the_database_singleton_is_built_once_under_concurrency
tests/unit/test_phase200_ci_isolation.py::test_a_reset_cannot_be_undone_by_a_construction_already_in_flight
tests/unit/test_phase200_ci_isolation.py::test_the_shutdown_handler_stops_every_conductor_it_started
tests/unit/test_phase200_task_resume.py::test_a_saved_ask_keeps_the_ratified_elements
tests/unit/test_phase200_task_resume.py::test_the_pinned_identity_is_one_askservice_would_accept
tests/unit/test_phase200_task_resume.py::test_a_purpose_is_required
tests/unit/test_phase200_task_resume.py::test_saving_against_an_unknown_project_is_a_not_found
tests/unit/test_phase200_task_resume.py::test_an_ask_cannot_be_saved_into_a_state_it_cannot_reach
tests/unit/test_phase200_task_resume.py::test_the_stopped_reason_is_stored_verbatim
tests/unit/test_phase200_task_resume.py::test_discard_is_a_state_and_leaves_the_projection
tests/unit/test_phase200_task_resume.py::test_an_accepted_ask_leaves_the_projection_too
tests/unit/test_phase200_task_resume.py::test_a_failed_ask_stays_in_the_projection
tests/unit/test_phase200_task_resume.py::test_an_absent_recipe_draws_no_key_at_all
tests/unit/test_phase200_task_resume.py::test_custody_survives_a_restart_and_never_leaks_an_id
tests/unit/test_phase200_task_resume.py::test_the_custody_identity_is_stable_within_the_machine
tests/unit/test_phase200_task_resume.py::test_the_projection_can_be_scoped_to_one_project
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[0]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[-1]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[51]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[1000]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[20]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[2.5]
tests/unit/test_phase200_task_resume.py::test_the_limit_is_bounded_one_to_fifty[True]
tests/unit/test_phase200_task_resume.py::test_the_page_is_newest_first_and_keyset_paged
tests/unit/test_phase200_task_resume.py::test_a_row_saved_mid_page_never_shifts_the_page_under_the_reader
tests/unit/test_phase200_task_resume.py::test_a_forged_cursor_is_refused
tests/unit/test_phase200_task_resume.py::test_resume_without_a_transport_dispatches_nothing_and_hands_back_the_material
tests/unit/test_phase200_task_resume.py::test_resuming_a_discarded_ask_is_a_conflict
tests/unit/test_phase200_task_resume.py::test_resuming_an_unknown_ask_is_a_not_found
tests/unit/test_phase200_task_resume.py::test_a_second_resume_cannot_take_a_lease_the_first_still_holds
tests/unit/test_phase200_task_resume.py::test_an_orphaned_lease_settles_to_failed_with_a_named_reason
tests/unit/test_phase200_task_resume.py::test_a_live_lease_is_not_abandonment
tests/unit/test_phase200_task_resume.py::test_recovery_leaves_settled_rows_alone
tests/unit/test_phase200_task_resume.py::test_the_invocation_identity_is_unique
tests/unit/test_phase200_task_resume.py::test_an_invalid_state_is_refused_by_the_check
tests/unit/test_phase200_task_resume.py::test_the_rows_go_with_their_project
tests/unit/test_phase200_task_resume.py::test_reconcile_adds_the_table_to_a_pre_200_database
tests/unit/test_phase200_task_resume.py::test_a_browser_observed_refusal_records_the_targets_own_words
tests/unit/test_phase200_task_resume.py::test_a_stopped_ask_is_still_resumable
tests/unit/test_phase200_task_resume.py::test_an_unrecognised_code_stores_the_code_and_no_reason
tests/unit/test_phase200_task_resume.py::test_a_code_the_hub_has_never_heard_of_quotes_nothing
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[]
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[   ]
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[192.168.1.43 is unreachable]
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[Destination 'LAN box' is unavailable]
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[Inference_Target_Unavailable]
tests/unit/test_phase200_task_resume.py::test_a_sentence_can_never_get_in_through_the_code[aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
tests/unit/test_phase200_task_resume.py::test_recording_the_same_stop_twice_changes_nothing
tests/unit/test_phase200_task_resume.py::test_the_route_will_not_move_a_row_it_does_not_own[accepted]
tests/unit/test_phase200_task_resume.py::test_the_route_will_not_move_a_row_it_does_not_own[discarded]
tests/unit/test_phase200_task_resume.py::test_stopping_an_unknown_ask_is_a_not_found
tests/unit/test_phase200_task_resume.py::test_the_machine_identity_is_minted_once_and_persisted
tests/unit/test_phase200_task_resume.py::test_an_existing_machine_identity_is_never_rewritten
tests/unit/test_phase200_task_resume.py::test_a_settings_save_round_trips_the_machine_identity
tests/unit/test_phase200_task_resume.py::test_a_config_that_cannot_be_written_yields_no_identity
tests/unit/test_phase200_task_resume.py::test_custody_survives_the_database_file_being_recreated
tests/unit/test_phase200_task_resume.py::test_a_different_machine_reads_elsewhere
tests/unit/test_phase200_task_resume.py::test_an_unknown_desk_draws_no_custody_at_all
tests/unit/test_transcriber_init_race.py::test_concurrent_ensure_builds_exactly_one_transcriber
tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation[mac-mlx]
tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation[linux-faster-whisper]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-backend-mac-mlx]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-backend-linux-faster-whisper]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-model-mac-mlx]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-model-linux-faster-whisper]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-language-mac-mlx]
tests/unit/test_transcriber_init_race.py::test_different_transcriber_identity_rebuilds[different-language-linux-faster-whisper]
tests/unit/test_transcriber_init_race.py::test_every_mlx_transcriber_shares_one_pinned_thread
tests/unit/test_phase200_attention.py::TestRanking::test_the_five_classes_in_the_ratified_order
tests/unit/test_phase200_attention.py::TestRanking::test_classes_rank_overdue_then_due_today_then_not_run_then_no_due_then_waiting
tests/unit/test_phase200_attention.py::TestRanking::test_a_due_date_decides_before_the_reason_token
tests/unit/test_phase200_attention.py::TestRanking::test_within_class_orders_are_the_ratified_ones
tests/unit/test_phase200_attention.py::TestRanking::test_severity_is_not_a_sort_key
tests/unit/test_phase200_attention.py::TestRanking::test_tie_break_is_the_stable_id_and_the_order_is_deterministic
tests/unit/test_phase200_attention.py::TestRanking::test_an_unknown_time_sorts_last_in_its_class
tests/unit/test_phase200_attention.py::TestRanking::test_rank_items_does_not_mutate_its_input
tests/unit/test_phase200_attention.py::TestRanking::test_sort_key_is_the_complete_key
tests/unit/test_phase200_attention.py::TestDedup::test_three_projections_of_one_obligation_are_one_row
tests/unit/test_phase200_attention.py::TestDedup::test_the_same_title_in_two_projects_is_two_obligations
tests/unit/test_phase200_attention.py::TestDedup::test_a_projection_without_a_project_joins_the_one_project_that_names_it
tests/unit/test_phase200_attention.py::TestDedup::test_a_projection_without_a_project_stands_alone_when_several_projects_name_it
tests/unit/test_phase200_attention.py::TestDedup::test_normalisation_strips_a_leading_ref_case_and_spacing
tests/unit/test_phase200_attention.py::TestDedup::test_counsel_probe_1_distinct_obligations_never_merge
tests/unit/test_phase200_attention.py::TestDedup::test_the_true_cross_source_case_is_one_row_with_two_openable_sources
tests/unit/test_phase200_attention.py::TestDedup::test_same_ref_across_sources_merges_and_different_refs_do_not
tests/unit/test_phase200_attention.py::TestDedup::test_the_shared_fixture_ranks_and_groups_as_the_browser_does
tests/unit/test_phase200_attention.py::TestDedup::test_a_merged_row_is_remembered_only_when_every_projection_is
tests/unit/test_phase200_attention.py::TestDedup::test_every_row_carries_its_sources_even_when_alone
tests/unit/test_phase200_attention.py::TestAggregateWiring::test_items_come_back_ranked_with_class_sources_and_facts
tests/unit/test_phase200_attention.py::TestAggregateWiring::test_two_projections_of_one_obligation_collapse_on_the_wire
tests/unit/test_phase200_attention.py::TestAggregateWiring::test_a_carried_row_from_a_failed_source_keeps_its_place_in_the_ranking
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_changed_item_with_the_same_count_notifies
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_quiet_hours_hold_then_deliver_once
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_quiet_hours_hold_even_a_same_count_change_and_deliver_it_once
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_restart_renotifies_nothing
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_the_set_edge_is_a_pure_object
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_2_pruning_drops_archived_projects_and_resolved_door_cards
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_3_escalation_of_a_known_id_notifies
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_escalation_fires_through_the_sweep_and_says_so
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_2b_archived_project_ids_leave_the_settings
tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_the_policy_row_is_written_only_when_the_set_or_outcome_changed
tests/unit/test_phase200_attention.py::TestNoFalseAllClear::test_a_failed_source_keeps_its_last_known_items_stamped_with_their_observation
tests/unit/test_phase200_attention.py::TestNoFalseAllClear::test_an_empty_partial_result_is_not_complete
tests/unit/test_thread_guardrail.py::TestGuardrailMatches::test_exact_match
tests/unit/test_thread_guardrail.py::TestGuardrailMatches::test_wildcard_match
tests/unit/test_thread_guardrail.py::TestGuardrailMatches::test_wildcard_no_match
tests/unit/test_thread_guardrail.py::TestGuardrailMatches::test_no_patterns
tests/unit/test_thread_guardrail.py::TestGuardrailMatches::test_multiple_patterns
tests/unit/test_thread_guardrail.py::TestGuardrailSeeds::test_seed_guardrails_creates_two
tests/unit/test_thread_guardrail.py::TestGuardrailSeeds::test_seed_guardrails_idempotent
tests/unit/test_thread_guardrail.py::TestGuardrailSeeds::test_seed_guardrails_parse
tests/unit/test_thread_guardrail.py::TestModeGuardrails::test_chase_has_both_guardrails
tests/unit/test_thread_guardrail.py::TestModeGuardrails::test_desk_has_egress_guard_only
tests/unit/test_thread_guardrail.py::TestModeGuardrails::test_draft_has_no_guardrails
tests/unit/test_thread_guardrail.py::TestModeGuardrails::test_plan_has_no_guardrails
tests/unit/test_thread_guardrail.py::TestGuardrailsForThread::test_no_mode_returns_empty
tests/unit/test_thread_guardrail.py::TestGuardrailsForThread::test_chase_mode_returns_both_guardrails
tests/unit/test_thread_guardrail.py::TestGuardrailsForThread::test_draft_mode_returns_no_guardrails
tests/unit/test_thread_guardrail.py::TestToggleGuardrail::test_toggle_on
tests/unit/test_thread_guardrail.py::TestToggleGuardrail::test_toggle_off
tests/unit/test_thread_guardrail.py::TestToggleGuardrail::test_toggle_on_preserves_tools
tests/unit/test_thread_guardrail.py::TestRealCoordinatorGuardrail::test_chase_yolo_guardrail_violation_call_still_executes
tests/unit/test_thread_guardrail.py::TestRealCoordinatorGuardrail::test_chase_safe_violation_pending_carries_deny
tests/unit/test_thread_guardrail.py::TestRealCoordinatorGuardrail::test_guardrail_disabled_per_mode_zero_invocations
tests/unit/test_thread_guardrail.py::TestRealRunnerGuardrailCloudRedaction::test_cloud_route_withholds_sensitive_texts
tests/unit/test_thread_guardrail.py::TestRealRunnerGuardrailCloudRedaction::test_local_route_guardrail_through_real_runner
tests/unit/test_thread_guardrail.py::TestGuardrailRunsOncePerPass::test_three_calls_one_guardrail_invocation
tests/unit/test_thread_guardrail.py::TestGuardrailTimeoutContinues::test_timeout_produces_warning_row
tests/unit/test_thread_guardrail.py::TestGuardrailExceptionContinues::test_exception_produces_warning_row
tests/unit/test_thread_guardrail.py::TestReconcileThreadMessagePartsKindDrift::test_old_db_rejects_guardrail_kind
tests/unit/test_thread_guardrail.py::TestReconcileThreadMessagePartsKindDrift::test_reconcile_widens_check_and_preserves_rows
tests/unit/test_thread_guardrail.py::TestReconcileThreadMessagePartsKindDrift::test_rebuild_is_noop_when_already_widened
tests/unit/test_thread_guardrail.py::TestGuardrailM1CapabilityBoundary::test_cloud_guardrail_withholds_sensitive_texts
tests/unit/test_thread_guardrail.py::TestGuardrailM1CapabilityBoundary::test_local_guardrail_preserves_sensitive_texts
tests/unit/test_thread_guardrail.py::TestS1PerCallViolationMapping::test_specific_violation_maps_only_to_named_tool
tests/unit/test_thread_guardrail.py::TestS1PerCallViolationMapping::test_generic_violation_maps_to_all_matching_tools
tests/unit/test_thread_guardrail.py::TestS1PerCallViolationMapping::test_mixed_violations
tests/unit/test_web_server_startup.py::test_start_waits_for_listener_after_lifespan_startup
tests/unit/test_web_server_startup.py::test_start_raises_when_uvicorn_exits_during_startup
tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused
tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart
tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440[1440]
tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440[393]

162 tests collected in 0.86s
```

### Captured run — 2026-09-20T05:36:51Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.hbDn0Wbqp1 uv run pytest -q tests/unit/test_phase200_ci_isolation.py tests/unit/test_phase200_task_resume.py tests/unit/test_transcriber_init_race.py tests/unit/test_phase200_attention.py tests/unit/test_thread_guardrail.py tests/unit/test_web_server_startup.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
........................................................................ [ 45%]
........................................................................ [ 91%]
..............                                                           [100%]
158 passed in 33.02s
```

### Captured run — 2026-09-20T05:37:26Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.oZUsjyoaTt PYTHONPATH=/Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes:/Users/karol/dev/tools/wt-201-a uv run pytest -q -p linux_backend tests/unit/test_transcriber_init_race.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
..........                                                               [100%]
10 passed in 1.44s
```

### Captured run — 2026-09-20T05:37:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.2fDXUZySBd PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
....                                                                     [100%]
4 passed in 31.38s
```

### Interrupted diagnostic — NOT full-suite proof

Interrupted at about 95%, exit 2. Tests not run: unknown set. One SIGINT was sent to the verified owned controller; its workers and Playwright processes exited. Default load left three workers idle. Peer accepted work stealing for the final complete run; no assertion or selection changes.

### Captured run — 2026-09-20T05:38:32Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 4 --ignore=tests/e2e/test_metal.py 2>&1 | tee .tmp/hs201-green/full-final.log | tail -100`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
        live = gen.build_reference_app().openapi()
        # Export provenance is documentation metadata, not a server schema field.
        declared["info"].pop("x-philo-note")
        declared["info"].pop("x-source-snapshot")
>       assert declared == live, "OpenAPI drift: run scripts/philo_openapi_reference.py with isolated HOME"
E       AssertionError: OpenAPI drift: run scripts/philo_openapi_reference.py with isolated HOME
E       assert {'components'...ions'}}, ...}} == {'components'...ions'}}, ...}}
E
E         Omitting 3 identical items, use -vv to show
E         Differing items:
E         {'paths': {'/api/action-items/{item_id}': {'patch': {'operationId': 'api_update_action_item_api_action_items__item_id_...Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, 'summary': 'Annotations'}}, ...}} != {'paths': {'/api/action-items/{item_id}': {'patch': {'operationId': 'api_update_action_item_api_action_items__item_id_...Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, 'summary': 'Annotations'}}, ...}}
E         Use -v to get more diff

tests/unit/test_api_surface.py:108: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:17: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:160: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.OqhjAn2F8n/xdist-gw1/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.OqhjAn2F8n/xdist-gw1/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:552: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:618: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:171: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:232: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:281: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:149: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:396: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:461: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:554: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:270: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:521: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:673: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:921: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1090: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:327: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:281: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:367: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]
FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[393]
FAILED tests/e2e/test_hs144_door_glass.py::test_hs144_door_cold_open_keeps_first_sentence_one_job
FAILED tests/e2e/test_hs144_door_glass.py::test_hs144_door_populated_glass_action_refusal_and_shots
FAILED tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_real_hub_states_and_dimensions
FAILED tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
FAILED tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393 - As...
FAILED tests/e2e/test_hs144_door_glass.py::test_meetings_settings_calendar_glass_and_egress_fact
FAILED tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15
FAILED tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state
FAILED tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py:363: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
11 failed, 10813 passed, 101 skipped in 1658.34s (0:27:38)
```

### Captured run — 2026-09-20T06:08:01Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpieh6qeoq uv run pytest -q tests/unit/test_roadmaps_api.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
....FF                                                                   [100%]
=================================== FAILURES ===================================
_ test_project_reads_dw_next_json_variants_exactly[explicit-null-next-story-{"next_story": null}-None-2] _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9195/test_project_reads_dw_next_jso4')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10c603bd0>
name = 'explicit-null-next-story', payload = '{"next_story": null}'
expected = None, next_exit = 2

    @pytest.mark.parametrize(
        ("name", "payload", "expected", "next_exit"),
        [
            ("explicit-story-id", '{"story_id": "HS-201-08"}', "HS-201-08", 0),
            ("explicit-id", '{"id": "HS-201-08"}', "HS-201-08", 0),
            ("nested-story-id", '{"next_story": {"story_id": "HS-201-08"}}', "HS-201-08", 0),
            ("absent-next-story", "{}", None, 2),
            ("explicit-null-next-story", '{"next_story": null}', None, 2),
        ],
    )
    def test_project_reads_dw_next_json_variants_exactly(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        name: str,
        payload: str,
        expected: str | None,
        next_exit: int,
    ) -> None:
        _write_project(
            tmp_path,
            name,
            phase=1,
            phase_slug="active",
            story_id="HS-201-08",
            status="ready",
        )
        fake_run, calls = _run_for_payload(name, payload, next_exit=next_exit)
        monkeypatch.setattr(roadmaps, "_run", fake_run)

>       result = roadmaps._project(tmp_path, name, include_phases=False)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_roadmaps_api.py:89:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

repo_root = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9195/test_project_reads_dw_next_jso4')
slug = 'explicit-null-next-story', include_phases = False

    def _project(repo_root: Path, slug: str, include_phases: bool = True) -> dict[str, Any] | None:
        root = _project_path(repo_root, slug)
        if root is None:
            return None
        readme = root / "README.md"
        phases = [p for d in root.iterdir() if d.is_dir() if (p := _phase(d)) is not None]
        phases.sort(key=lambda phase: phase["number"], reverse=True)
        readme_text = _safe_text(readme)
        name_match = _H1.search(readme_text)
        current_match = _CURRENT.search(readme_text) or _ANY_PHASE.search(readme_text)
        current_number = int(current_match.group(1)) if current_match else (phases[0]["number"] if phases else 0)
        current = next((phase for phase in phases if phase["number"] == current_number), phases[0] if phases else None)
        exit_code, check_output = _run(repo_root, "check", slug)
        issues = _issues(check_output)
        health = "green" if exit_code == 0 else ("warn" if exit_code == 1 else "red")
        _, next_output = _run(repo_root, "next", slug, "--json")
        try:
            next_data = json.loads(next_output)
        except (TypeError, json.JSONDecodeError):
            next_data = {}
>       next_story = next_data.get("story_id") or next_data.get("id") or next_data.get("next_story", {}).get("story_id")
                                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'NoneType' object has no attribute 'get'

holdspeak/web/routes/roadmaps.py:147: AttributeError
_ test_roadmaps_list_keeps_active_project_when_completed_project_has_null_next_story _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9195/test_roadmaps_list_keeps_activ0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10c6b5250>

    def test_roadmaps_list_keeps_active_project_when_completed_project_has_null_next_story(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _write_project(
            tmp_path,
            "active",
            phase=1,
            phase_slug="active",
            story_id="HS-201-08",
            status="ready",
        )
        _write_project(
            tmp_path,
            "completed",
            phase=1,
            phase_slug="closed",
            story_id="HP-1-01",
            status="done",
            closed=True,
        )

        calls: list[tuple[Path, tuple[str, ...]]] = []

        def fake_run(repo_root: Path, *args: str) -> tuple[int, str]:
            calls.append((repo_root, args))
            if args[0] == "check":
                return 0, "dw check: ok"
            if args == ("next", "active", "--json"):
                return 0, '{"story_id": "HS-201-08"}'
            if args == ("next", "completed", "--json"):
                return 2, '{"next_story": null}'
            raise AssertionError(args)

        monkeypatch.setattr(roadmaps, "_run", fake_run)
        app = FastAPI()
        app.include_router(
            roadmaps.build_roadmaps_router(
                WebContext(get_state=lambda: {}),
                repo_root=tmp_path,
            )
        )

        response = TestClient(app, raise_server_exceptions=False).get("/api/roadmaps")

>       assert response.status_code == 200, response.text
E       AssertionError: Internal Server Error
E       assert 500 == 200
E        +  where 500 = <Response [500 Internal Server Error]>.status_code

tests/unit/test_roadmaps_api.py:144: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_roadmaps_api.py::test_project_reads_dw_next_json_variants_exactly[explicit-null-next-story-{"next_story": null}-None-2]
FAILED tests/unit/test_roadmaps_api.py::test_roadmaps_list_keeps_active_project_when_completed_project_has_null_next_story
2 failed, 4 passed in 0.88s
```

### Captured run — 2026-09-20T06:08:03Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmps8xl8iub uv run pytest -q tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
F                                                                        [100%]
=================================== FAILURES ===================================
_________________ test_committed_openapi_matches_reference_app _________________

    def test_committed_openapi_matches_reference_app() -> None:
        """Declared schemas remain real; raw Request semantics remain outside them."""
        declared = json.loads((REPO / "docs/generated/openapi.json").read_text())
        live = gen.build_reference_app().openapi()
        # Export provenance is documentation metadata, not a server schema field.
        declared["info"].pop("x-philo-note")
        declared["info"].pop("x-source-snapshot")
>       assert declared == live, "OpenAPI drift: run scripts/philo_openapi_reference.py with isolated HOME"
E       AssertionError: OpenAPI drift: run scripts/philo_openapi_reference.py with isolated HOME
E       assert {'components'...ions'}}, ...}} == {'components'...ions'}}, ...}}
E
E         Omitting 3 identical items, use -vv to show
E         Differing items:
E         {'paths': {'/api/action-items/{item_id}': {'patch': {'operationId': 'api_update_action_item_api_action_items__item_id_...Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, 'summary': 'Annotations'}}, ...}} != {'paths': {'/api/action-items/{item_id}': {'patch': {'operationId': 'api_update_action_item_api_action_items__item_id_...Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, 'summary': 'Annotations'}}, ...}}
E         Use -v to get more diff

tests/unit/test_api_surface.py:108: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app
1 failed in 1.55s
```

### Captured run — 2026-09-20T06:08:05Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpzqllvc7h /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_api_reference.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
API reference drift: docs/generated/api-reference.json, docs/API_REFERENCE.md
```

### Captured run — 2026-09-20T06:08:09Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp5t55h1j8 /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_boundary_census.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
boundary census drift
```

### Captured run — 2026-09-20T06:08:12Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpcfp9uq9s /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_doctor_reference.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
doctor reference drift
```

### Captured run — 2026-09-20T06:08:12Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpaj4ll9qm /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/validate_architecture.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
Architecture metadata: 4 shard(s), 147 record(s)
ERROR docs/internal/philo/data/runtime.json.capabilities[7].sources[1].line: source line 1454 is outside holdspeak/commands/doctor.py
Architecture metadata validation failed: 1 error(s), 0 warning(s).
```

### Captured run — 2026-09-20T06:08:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpewdfysa2 /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/generate_capability_docs.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
architecture metadata is invalid; run scripts/validate_architecture.py for diagnostics
```

### Captured run — 2026-09-20T06:08:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp1fmaww6q /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_doc_coverage.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
architecture metadata is invalid; run scripts/validate_architecture.py for diagnostics
```

### Captured run — 2026-09-20T06:12:13Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp628ahkgz PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 4 --dist=worksteal tests/unit/test_roadmaps_api.py tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440] tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[393] tests/e2e/test_hs144_door_glass.py::test_hs144_door_cold_open_keeps_first_sentence_one_job tests/e2e/test_hs144_door_glass.py::test_hs144_door_populated_glass_action_refusal_and_shots tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_real_hub_states_and_dimensions tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393 tests/e2e/test_hs144_door_glass.py::test_meetings_settings_calendar_glass_and_egress_fact tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15 tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
bringing up nodes...
bringing up nodes...

................                                                         [100%]
16 passed in 43.63s
```

### Captured run — 2026-09-20T06:16:51Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.K7mKV0CxAG uv run pytest -q tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
......                                                                   [100%]
6 passed in 2.86s
```

### Captured run — 2026-09-20T06:17:24Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7wTTOouJhs /opt/homebrew/opt/python@3.12/bin/python3.12 pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/docs_ci.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e24262b977f47dd3dabf99c1944fa3979eaf1024

```text
Python: 3.12.12 (main, Oct  9 2025, 11:07:00) [Clang 17.0.0 (clang-1700.3.19.1)]
T1: e24262b977f47dd3dabf99c1944fa3979eaf1024
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/SRS.md docs/internal/philo/initial-findings.md docs/internal/philo/source-checklist.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_api_reference.py --check
API reference checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_boundary_census.py --check
Boundary candidate census checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_config_reference.py --check
Configuration declaration reference is current
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_doc_coverage.py --check
Documentation coverage checked.
All eleven documentation CI commands passed.
```

### Captured run — 2026-09-20T06:17:57Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.JeABlgjSSj /opt/homebrew/opt/python@3.12/bin/python3.12 pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/docs_ci.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 249b8364bfa178c5cd2d22bdb1c81e0c35bc7027

```text
Python: 3.12.12 (main, Oct  9 2025, 11:07:00) [Clang 17.0.0 (clang-1700.3.19.1)]
T1: 249b8364bfa178c5cd2d22bdb1c81e0c35bc7027
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/SRS.md docs/internal/philo/initial-findings.md docs/internal/philo/source-checklist.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_api_reference.py --check
API reference checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_boundary_census.py --check
Boundary candidate census checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_config_reference.py --check
Configuration declaration reference is current
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_doc_coverage.py --check
Documentation coverage checked.
All eleven documentation CI commands passed.
```

### Captured run — 2026-09-20T06:18:26Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 4 --dist=worksteal --ignore=tests/e2e/test_metal.py 2>&1 | tee .tmp/hs201-green/full-worksteal.log | tail -100`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
DEBUG    holdspeak.web_server:web_server.py:580 Broadcasting runtime_queue to WebSocket clients
DEBUG    holdspeak.web_server:web_server.py:580 Broadcasting runtime_queue to WebSocket clients
DEBUG    holdspeak.intel_queue:intel_queue.py:379 HS-172-03: dirty marker set after intel complete for 1a9868b9
INFO     holdspeak.intel_queue:intel_queue.py:988 Processed 1 deferred intel job(s)
INFO     holdspeak.web_server:web_server.py:485 Stopping meeting web server
INFO     holdspeak.calendar_ingest_conductor:calendar_ingest_conductor.py:234 Calendar ingest conductor stopped
INFO     holdspeak.workbench_conductor:workbench_conductor.py:523 Workbench conductor stopped
INFO     holdspeak.scheduled_recording_conductor:scheduled_recording_conductor.py:143 Scheduled recording conductor stopped
INFO     holdspeak.intel_queue_conductor:intel_queue_conductor.py:176 Stopping the intel drainer; waiting up to 60s for an in-flight model call to finish.
DEBUG    holdspeak.web_server:web_server.py:1416 Meeting web server shutdown complete
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:17: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:160: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.51CcokFHgR/xdist-gw3/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.51CcokFHgR/xdist-gw3/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.51CcokFHgR/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:552: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:618: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:171: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:232: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:281: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:149: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:396: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:461: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:554: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:270: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:521: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:673: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:921: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1090: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:327: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:281: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:367: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-201-a/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
FAILED tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id
FAILED tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section
FAILED tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[1440]
FAILED tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[1440]
FAILED tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[393]
FAILED tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[393]
6 failed, 11258 passed, 116 skipped, 4 xfailed in 1516.98s (0:25:16)
```

## Complete worksteal run — still red

Capture 2026-09-20T06:18:26Z reached 100%: **6 failed, 11258 passed, 116 skipped, 4 xfailed in 1516.98s**. This is a complete diagnostic, not a passing closure. No new skip or xfail was added. The four strict xfails are the explicitly parked Phase 200 proposal chain. The 15 additional skips versus the interrupted run are tests that the interrupted run had not completed; final closure will compare exact skip locations. All original six and the notification family passed. Six remaining nodes are listed in the captured tail. The canon no-write node passed; its conditional isolation proposal was not acted on.

### Captured run — 2026-09-20T06:48:08Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section 2>&1 | tee .tmp/hs201-green/weekly-before.log | tail -65`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
F                                                                        [100%]
=================================== FAILURES ===================================
______________ TestRhythmWeeklyBrief.test_brief_this_week_section ______________

self = <tests.e2e.test_hs175_rhythm_brief_glass.TestRhythmWeeklyBrief object at 0x109fdb610>
glass_with_calendar = (<Page url='http://127.0.0.1:57433/'>, [], 'http://127.0.0.1:57433')

    def test_brief_this_week_section(self, glass_with_calendar):
        """The brief face: period as the ONE display fact, no headline
        sentence, THIS WEEK composed rows, flat SINCE FRIDAY, no '00'."""
        page, errors, _ = glass_with_calendar

        _open_intelligence(page)
        _settle(page)
        page.wait_for_timeout(1000)

        # Check the brief data via API
        brief_data = _api(page, "GET", "/api/brief/latest", token=TOKEN)
        tw_items = brief_data.get("sections", {}).get("this_week", [])
        assert len(tw_items) > 0, (
            f"Brief API has no this_week items: {list(brief_data.get('sections', {}).keys())}"
        )

        # Wait for the intelligence pullout to appear
        pullout = page.locator(".intelligence-pullout, .intelligence-brief")
        try:
            pullout.first.wait_for(timeout=3000)
        except Exception:
            pass

        pullout_visible = pullout.first.count() > 0 and pullout.first.is_visible()

        if pullout_visible:
            # ── (1) Exactly ONE display-step element (the period label) ──
            brief_el = page.locator(".intelligence-brief")
            display_els = brief_el.locator(".intelligence-brief-period")
            assert display_els.count() == 1, (
                f"Expected exactly 1 display-step element, got {display_els.count()}"
            )
            # No headline sentence on this face
            headline = brief_el.locator(".intelligence-brief-headline")
            assert headline.count() == 0, (
                "Headline sentence must not appear on the brief face (canon C + A.3)"
            )

            # ── (2) No text matching /\b00\b/ (counters of zero = A.8 bounce) ──
            body_text = brief_el.text_content() or ""
            import re
>           assert not re.search(r'\b00\b', body_text), (
                f"Found '00' counter of zero on the brief face: ...{body_text[:200]}..."
            )
E           AssertionError: Found '00' counter of zero on the brief face: ...SEP 14-20GENERATED SEP 20 00:48THIS WEEK2 MEETINGSNEXT SPRINT PLANNING 01:481 ARMED1 DUEAnia owns the API specSUNSINCE FRIDAYREVIEW DECISIONAnia owns the API spec○PEOPLE · UNAVAILABLE...
E           assert not <re.Match object; span=(26, 28), match='00'>
E            +  where <re.Match object; span=(26, 28), match='00'> = <function search at 0x1032ca8e0>('\\b00\\b', 'SEP 14-20GENERATED SEP 20 00:48THIS WEEK2 MEETINGSNEXT SPRINT PLANNING 01:481 ARMED1 DUEAnia owns the API specSUNSINCE FRIDAYREVIEW DECISIONAnia owns the API spec○PEOPLE · UNAVAILABLE')
E            +    where <function search at 0x1032ca8e0> = <module 're' from '/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/re/__init__.py'>.search

tests/e2e/test_hs175_rhythm_brief_glass.py:416: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section
1 failed in 13.80s
```

The skip comparison, after normalizing only isolated HOME paths, adds exactly: one dictation llama.cpp model prerequisite; three grounding-rails project-map prerequisites; ten missing mock-meeting WAV fixtures; one unavailable Mermaid renderer. No previous skip disappears. These 15 existing prerequisite skips explain 101 → 116; no skip policy changed.

### Main 321247d2 CI observation

Read-only GitHub job logs, not branch verification: Unit job [106025713237](https://github.com/karolswdev/HoldSpeak/actions/runs/35490970756/job/106025713237) completed **4 failed, 9538 passed, 26 skipped**. Nodes: API surface reference drift plus the named CI HOME, custody replacement and warm transcriber tests. Documentation job [106025713310](https://github.com/karolswdev/HoldSpeak/actions/runs/35490970756/job/106025713310) stopped at API reference drift. E2E and Integration were still running when inspected.

Local raw log `.tmp/hs201-green/main-321-unit.log` SHA-256 `d98a0cc57afd95c876c7808f56a32f031e9be15bc7ae2aed214cbc8dceb29298`.

Local raw log `.tmp/hs201-green/main-321-docs.log` SHA-256 `c4fa86803088e74dc77139dae354b190d0ea1fafc076bb3c79f4a349e3dc089f`.

### Late weekly-brief assertion red

The 06:48:08Z capture repeats the full-run failure serially: the broad `\b00\b` assertion treats the valid generated time `00:48` as a zero counter. The product prints local HH:mm by design. No implementation edit has been made; settled scope is awaiting peer check.

### Workbench orientation during repair

`dw doctor` is healthy. `dw check holdspeak` reports this in-progress story’s evidence, plus six unrelated existing bookkeeping findings: Phase 101 evidence-story-04 paired with an unfinished story; missing final summaries for completed phases 152, 153, 154, 156 and 200. Story 08 closure removes its own finding. The others remain the phase ledger’s DW bookkeeping item Z6; they are not pytest failures or authorization to close historical phases.

### Captured run — 2026-09-20T06:52:13Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run python pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/fd_pressure.py 2>&1 | tee .tmp/hs201-green/fd-pressure-before.log | tail -40`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
                "mode": "neutral",
            },
        )
        envelope = service.claim_for_node("edge")[0]
        assert envelope["authority"]["decision"] == "allowed_by_active_grant"
        ledger_path = tmp_path / "edge-node.db"
        ready_read, ready_write = os.pipe()
        child = os.fork()
        if child == 0:
            try:
                os.close(ready_read)

                def transport(**kwargs):
                    send_text_to_pane(**kwargs)
                    os.write(ready_write, b"typed")
                    time.sleep(30)

                processor = NodeCommandProcessor(
                    node_id="edge",
                    targets=targets,
                    ledger=NodeReceiptLedger(ledger_path),
                    text_transport=transport,
                    audit=lambda **kwargs: 1,
                )
                child_result = processor.process(envelope)
                os.write(ready_write, f"RET:{child_result!r}".encode())
            except BaseException as exc:
                os.write(ready_write, f"ERR:{exc!r}".encode())
            finally:
                os._exit(0)
        os.close(ready_write)
        try:
>           readable, _, _ = select.select([ready_read], [], [], 10)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           ValueError: filedescriptor out of range in select()

tests/integration/test_process_input_real_hub.py:266: ValueError
=========================== short test summary info ============================
FAILED tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id
1 failed in 0.68s
```

Weekly peer follow-ups: exact-string search for `\b00\b` under tests/e2e found only this test’s comment and assertion; no other file is amended. The Mermaid CLI stack belongs to the explicit `test_mermaid_renders.py:118` prerequisite skip, not a hidden FAILED node. Daily-loop failures are at the proposal wait after summary completion (full trace lines 703 and 1110), a different cause from this timestamp assertion.

### Captured run — 2026-09-20T06:54:33Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run pytest -q -s tests/integration/test_process_input_real_hub.py 2>&1 | tee .tmp/hs201-green/send-serial-one.log | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
{"latency_ms": 200.59, "operation_id": "op_ae809d5fbbe74b909ee51f0227569166", "pane": "%4030", "receipt": "succeeded", "received": "REAL_PROCESS_INPUT_106_05"}
.{"aggregate": "indeterminate_after_node_reset", "command_id": "9f6d668d-97ed-4d64-bb9b-159ee4966475", "kernel_receipt": "indeterminate", "operation_id": "op_f3b286c5ff464be4a99b4166e2a83e75", "reconcile": "by_command_id", "sigkill": -9, "text_landed": "LANDED_BEFORE_SIGKILL_10605"}
.
2 passed in 4.03s
```

### Captured run — 2026-09-20T06:54:44Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run pytest -q -s tests/integration/test_process_input_real_hub.py 2>&1 | tee .tmp/hs201-green/send-serial-two.log | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
{"latency_ms": 81.23, "operation_id": "op_4596b97573fe4aeaaf425396956c4bf7", "pane": "%4032", "receipt": "succeeded", "received": "REAL_PROCESS_INPUT_106_05"}
.{"aggregate": "indeterminate_after_node_reset", "command_id": "e230a55f-37d5-45ca-81e8-6aaf4398a210", "kernel_receipt": "indeterminate", "operation_id": "op_f8601745ad4541f5b444b18381775e56", "reconcile": "by_command_id", "sigkill": -9, "text_landed": "LANDED_BEFORE_SIGKILL_10605"}
.
2 passed in 3.68s
```

### Captured run — 2026-09-20T06:57:52Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run python pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/fd_pressure.py 2>&1 | tee .tmp/hs201-green/fd-pressure-after.log | tail -9`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
descriptor pressure: 1050 open; highest=1052
{"aggregate": "indeterminate_after_node_reset", "command_id": "a57bcea9-0484-4833-a81b-9f18fbe67eed", "kernel_receipt": "indeterminate", "operation_id": "op_fa65c90ed5be4e78b1ccc0e8f9d7c9b1", "reconcile": "by_command_id", "sigkill": -9, "text_landed": "LANDED_BEFORE_SIGKILL_10605"}
.
1 passed in 0.46s
```

### Captured run — 2026-09-20T06:58:03Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run pytest -q tests/integration/test_process_input_real_hub.py 2>&1 | tee .tmp/hs201-green/send-file-after.log | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
..                                                                       [100%]
2 passed in 2.23s
```

### Captured run — 2026-09-20T06:58:54Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke 2>&1 | tee .tmp/hs201-green/remote-root-serial-one.log | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
..                                                                       [100%]
2 passed in 13.29s
```

### Interrupted-send assumption repaired

Root inspected the diff: only the select import and pipe-readiness wait changed. Capture 06:52:13Z fails the real SIGKILL node with 1,050 open descriptors; the identical durable probe passes at 06:57:52Z, followed by the full two-test file at 06:58:03Z. The probe closes all descriptors in finally, including failed runs. Existing landed bytes, kill status and by-command-id reconciliation assertions are unchanged. Two ordinary root serial file runs also passed (06:54:33Z and 06:54:44Z). This fixes an invalid platform assumption in the test wait, not descriptor accumulation.

### Captured run — 2026-09-20T06:59:30Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke 2>&1 | tee .tmp/hs201-green/remote-root-serial-two.log | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
..                                                                       [100%]
2 passed in 13.79s
```

### Captured run — 2026-09-20T07:00:04Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 0 tests/integration/test_hs174_runner_loopback.py tests/e2e/test_hs174_remote_settings_glass.py 2>&1 | tee .tmp/hs201-green/remote-root-polluter-before.log | tail -18`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded.
E           Call log:
E             - waiting for locator(".surface-ledger-primary").filter(has_text="test-glass-runner") to be detached
E               21 × locator resolved to visible <span class="surface-ledger-primary">test-glass-runner</span>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[1440]
FAILED tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[393]
2 failed, 6 passed in 46.01s
```

### Captured run — 2026-09-20T07:04:39Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run python pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/weekly_counter_canary.py 2>&1 | tee .tmp/hs201-green/weekly-canary-root.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
PASS 00:33 timestamp: timestamp accepted
PASS 08:00 timestamp: timestamp accepted
PASS 0 MEETINGS counter: rejected (brief-tw-meetings primary must start with a positive count: '0 MEETINGS')
PASS 00 ARMED counter: rejected (brief-tw-armed primary must start with a positive count: '00 ARMED')
```

### Captured run — 2026-09-20T07:04:41Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs175_rhythm_brief_glass.py 2>&1 | tee .tmp/hs201-green/weekly-after.log | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
...                                                                      [100%]
3 passed in 24.18s
```

### Captured run — 2026-09-20T07:04:55Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 0 tests/integration/test_hs174_runner_loopback.py tests/e2e/test_hs174_remote_settings_glass.py 2>&1 | tee .tmp/hs201-green/remote-root-polluter-after.log | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
........                                                                 [100%]
8 passed in 23.08s
```

### Weekly assertion and credential source verification

Weekly canary at 07:04:39Z executes the actual counter loop extracted from the glass test’s AST against rendered labels. Both legitimate timestamp cases pass; 0 MEETINGS and 00 ARMED raise the expected assertion. Root inspected the test diff: layout, NEXT, prose, gutter and ISO checks remain; absent BriefView now fails. The actual BriefView component pins both clock cases, positive MEETINGS/DUE and absent zero ARMED. The full glass file passes at 07:04:41Z. Root viewed weekly-brief-1440.png and weekly-brief-393.png.

Remote source proof is actual ordering, not an inferred singleton: both `test_happy_path_exit_0_and_transcript` and `test_pipeline_events_carry_remote_origin` in `test_hs174_runner_loopback.py` issue credentials without revoking them. Root quiet serial captures pass twice (13.29s and 13.79s); the complete producer → glass sequence fails both widths (2 failed, 6 passed, 46.01s), then passes all eight at 07:04:55Z. The new test uses the real settings API for the second credential and real /api/mcp authentication after the targeted revoke. The actual predecessor in the full worker remains unknown. This one fixture owns its state; the process-global store is not globally cleared.

### Captured run — 2026-09-20T07:04:55Z

- **Command:** `bash -o pipefail -c npm --prefix web run check 2>&1 | tee .tmp/hs201-green/web-check-final.log | tail -40`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
../holdspeak/static/_built/assets/LiveCore-KXP5h_F3.js                                    9.38 kB │ gzip:   3.67 kB
../holdspeak/static/_built/assets/ProcessCore-Cf4nGyiN.js                                 9.42 kB │ gzip:   3.60 kB
../holdspeak/static/_built/assets/ComponentsCore-BaWbJSDE.js                              9.97 kB │ gzip:   3.74 kB
../holdspeak/static/_built/assets/BufferResource-BK0BRSq9.js                             10.62 kB │ gzip:   2.80 kB
../holdspeak/static/_built/assets/CadenceCore-lZPNKI3l.js                                10.82 kB │ gzip:   3.68 kB
../holdspeak/static/_built/assets/BitmapFont-B4kNqckH.js                                 12.87 kB │ gzip:   4.71 kB
../holdspeak/static/_built/assets/webworkerAll-B2UTidj1.js                               15.48 kB │ gzip:   4.91 kB
../holdspeak/static/_built/assets/sceneKit-DiGkm6FV.js                                   16.55 kB │ gzip:   6.13 kB
../holdspeak/static/_built/assets/DoorCore-BTTQxjSi.js                                   17.50 kB │ gzip:   5.26 kB
../holdspeak/static/_built/assets/CanvasRenderer-D7Zs19Zw.js                             17.54 kB │ gzip:   5.88 kB
../holdspeak/static/_built/assets/ConciergeCore-CgP_l1ne.js                              18.62 kB │ gzip:   5.69 kB
../holdspeak/static/_built/assets/lanternGardenScene-xeGn5N5B.js                         18.98 kB │ gzip:   7.14 kB
../holdspeak/static/_built/assets/rainyCityScene-P7sWSGGp.js                             28.01 kB │ gzip:   9.68 kB
../holdspeak/static/_built/assets/PeopleCore-CBK4zXNY.js                                 28.21 kB │ gzip:   7.67 kB
../holdspeak/static/_built/assets/WebGPURenderer-QptYohdh.js                             38.99 kB │ gzip:  10.91 kB
../holdspeak/static/_built/assets/WorkbenchWindow-C6MSZQUS.js                            41.92 kB │ gzip:  13.72 kB
../holdspeak/static/_built/assets/browserAll-D8IPhRts.js                                 43.12 kB │ gzip:  11.33 kB
../holdspeak/static/_built/assets/RenderTargetSystem-C4AHXLcj.js                         46.38 kB │ gzip:  12.73 kB
../holdspeak/static/_built/assets/DictationCore-BSsEDfvV.js                              46.44 kB │ gzip:  14.83 kB
../holdspeak/static/_built/assets/SettingsCore-DroEEksJ.js                               46.91 kB │ gzip:  14.29 kB
../holdspeak/static/_built/assets/react-SZyUX699.js                                      48.46 kB │ gzip:  17.18 kB
../holdspeak/static/_built/assets/HistoryCore-Dp2MwkSy.js                                48.80 kB │ gzip:  14.81 kB
../holdspeak/static/_built/assets/WebGLRenderer-QcHRELN9.js                              68.80 kB │ gzip:  18.91 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-5sdaZHev.js                         160.98 kB │ gzip:  44.17 kB
../holdspeak/static/_built/assets/index-BMGTF3C7.js                                     219.31 kB │ gzip:  69.00 kB
../holdspeak/static/_built/assets/WorldStage-Cu-_mb_L.js                                338.63 kB │ gzip: 107.27 kB
../holdspeak/static/_built/assets/XtermPane-GJgyAXxm.js                                 364.14 kB │ gzip:  93.99 kB
../holdspeak/static/_built/assets/UnrealBloomPass-COc2GKT4.js                           558.38 kB │ gzip: 141.32 kB
../holdspeak/static/_built/assets/desk-DXTzoleD.js                                    1,312.52 kB │ gzip: 418.70 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.47s

> holdspeak-web@0.0.1 bundle:gate
> node scripts/check-bundle.mjs

bundle gate passed (Desk JS 1312518 B; Desk CSS 319765 B; source maps 0)
```

### Captured run — 2026-09-20T07:06:56Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n 4 --dist=worksteal tests/e2e/test_hs174_remote_settings_glass.py 2>&1 | tee .tmp/hs201-green/remote-root-n4.log | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
bringing up nodes...
bringing up nodes...

....                                                                     [100%]
4 passed in 10.46s
```

### Captured run — 2026-09-20T07:07:46Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run 2>&1 | tee .tmp/hs201-green/web-baseline-final.log | tail -15`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2601 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Final web verification


Final web check after the clock-state tests: exit 0 (DW 07:04:55Z).
React architecture guard passed (785 source files; zero framework residue).
 Test Files  274 passed (274)
      Tests  2601 passed (2601)
bundle gate passed (Desk JS 1312518 B; Desk CSS 319765 B; source maps 0)
Raw log SHA-256: 63d28a6a5c176cc8831993e951495ca5fc1a23425a460b070ba6ccc05304f628
Final web baseline capture 07:07:46Z: 2601 passed, 0 failed, 0 skipped; baseline-subset, zero branch-new.

Remote four-worker capture 07:06:56Z passes all four glass tests. Additional post-revoke shots retain the other credential after real bearer validation; root views these separately.

### Captured run — 2026-09-20T07:12:52Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" uv run python pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/daily_summary_canary.py 2>&1 | tee .tmp/hs201-green/daily-canary-root.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
Actual assertion lines: [1032, 1033]
PASS summary-only: actual assertions accept the current law
PASS forced plugin call: actual assertion rejected ['canary plugin call']
PASS forced proposal: actual assertion rejected [{'id': 'canary-proposal'}]
```

### Captured run — 2026-09-20T07:12:54Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" HOLDSPEAK_WRITE_SHOTS=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_phase200_daily_loop.py 2>&1 | tee .tmp/hs201-green/daily-root-after.log | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9113c1d1fc442ac908db29d8985d8d43d664af77

```text
..                                                                       [100%]
2 passed in 71.37s (0:01:11)
```

### Daily-loop current law and retained continuity

Root capture 07:12:54Z: both widths pass in 71.37s. Root AST comparison counts 67 old assertions and 79 new ones: only the old wait for two summary-produced proposals is replaced, with thirteen new predicates; every other old predicate remains. The real DecisionCapturePlugin and ActionOwnerEnforcerPlugin run with the existing admitted-dispatch test support (actual context/claim issuer), their returned structured data enters record_artifact, and the retained bridge creates the two fixture proposals. No copied raw INSERT shape is used. Root canary 07:12:52Z extracts the actual two empty-state assertions; a forced call or proposal fails them. A subsequent docstring-only clarification explicitly carves the named seed step out of NORMAL CONTROLS; the final full run imports that clarification.

Day 2 continuity is proven from a seeded day-1 state. The current first-use summary path does not create the decision or commitment that day 2 carries. No current owner creation path is proven by this rig. BACKLOG's “Phase 201 parked summary follow-through” is the return path. Muad'Dib withdrew the broader universal-absence claim in checks/story-08-d5-wording-muaddib.md; surviving legacy entries are also not proven to work.

Root viewed the six retained daily shots: NOT RUN, day-2 recall and day-2 preparation at both widths. Historical fixture output is visibly labelled in recall. Root also viewed both post-revoke shots: only other-glass-runner remains. These are isolated fixture tests, not the owner's attended sitting.

Before final input staging, root parked and restored 470 unrelated tracked rig artifacts with git show HEAD:path, including the other Phase 201 stories' images, and parked eleven new rig artifacts. Only story-08 proof assets are retained in the change.

### Captured run — 2026-09-20T07:16:21Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest --collect-only -q tests/integration/test_process_input_real_hub.py tests/e2e/test_hs174_remote_settings_glass.py tests/e2e/test_hs175_rhythm_brief_glass.py tests/e2e/test_phase200_daily_loop.py 2>&1 | tee .tmp/hs201-green/late-collect-root.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b10284bb104e9b27556fa618069f853f8c19b3aa

```text
tests/integration/test_process_input_real_hub.py::test_real_http_process_input_types_into_real_tmux
tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id
tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_off_state[1440]
tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_off_state[393]
tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[1440]
tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[393]
tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_rhythm_brief_row_with_calendar
tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section
tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmMondayBrief::test_no_calendar_monday_brief
tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[1440]
tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[393]

11 tests collected in 0.16s
```

### Captured run — 2026-09-20T07:16:35Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" /opt/homebrew/opt/python@3.12/bin/python3.12 pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/docs_ci.py 2>&1 | tee .tmp/hs201-green/docs-ci-final.log | tail -90`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b9d674320c6382bf5555cd6fe44f3318c15b1c74

```text
Python: 3.12.12 (main, Oct  9 2025, 11:07:00) [Clang 17.0.0 (clang-1700.3.19.1)]
T1: b9d674320c6382bf5555cd6fe44f3318c15b1c74
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/SRS.md docs/internal/philo/initial-findings.md docs/internal/philo/source-checklist.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_api_reference.py --check
API reference drift: docs/generated/api-reference.json
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/docs_ci.py", line 34, in <module>
    subprocess.run([sys.executable, *command], check=True)
  File "/opt/homebrew/Cellar/python@3.12/3.12.12/Frameworks/Python.framework/Versions/3.12/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/opt/homebrew/opt/python@3.12/bin/python3.12', 'scripts/philo_api_reference.py', '--check']' returned non-zero exit status 1.
```

### Final-input API regeneration

The 07:16:35Z docs capture correctly refused API-reference drift after the remote test added real API calls. Regeneration adds only that test path to five settings-route candidate lists (five JSON lines); no route, contract field, schema or Markdown output changes. Root reviewed the structural diff. The failed docs input tree b9d674320c6382bf5555cd6fe44f3318c15b1c74 is superseded by the next fresh T1 and all eleven commands.

### Captured run — 2026-09-20T07:17:48Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" /opt/homebrew/opt/python@3.12/bin/python3.12 pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-probes/docs_ci.py 2>&1 | tee .tmp/hs201-green/docs-ci-final.log | tail -90`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6c8c47bdfeeae64d3246cd592aa309a3a0e9f645

```text
Python: 3.12.12 (main, Oct  9 2025, 11:07:00) [Clang 17.0.0 (clang-1700.3.19.1)]
T1: 6c8c47bdfeeae64d3246cd592aa309a3a0e9f645
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/SRS.md docs/internal/philo/initial-findings.md docs/internal/philo/source-checklist.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_api_reference.py --check
API reference checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_boundary_census.py --check
Boundary candidate census checked
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/philo_config_reference.py --check
Configuration declaration reference is current
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
COMMAND: /opt/homebrew/opt/python@3.12/bin/python3.12 scripts/check_doc_coverage.py --check
Documentation coverage checked.
All eleven documentation CI commands passed.
```

### Captured run — 2026-09-20T07:18:40Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -vv -n 4 --dist=worksteal --ignore=tests/e2e/test_metal.py 2>&1 | tee .tmp/hs201-green/full-verified.log | tail -105`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 315f0ef264e90bda4f6c055584dfa5ef179a8345

```text
[gw1] [ 99%] PASSED tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[1440]
tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[393]
[gw0] [ 99%] PASSED tests/e2e/test_hs170_settings_hub_glass.py::test_settings_hub_open_verb_opens_surface
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200]
[gw3] [ 99%] PASSED tests/e2e/test_route_preflight.py::test_every_route_loads_without_page_errors
tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_ready_resolve_people_locked_1440
[gw1] [ 99%] PASSED tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[393]
tests/e2e/test_hs200_preparation_brief_glass.py::test_unavailable_model_refuses_and_keeps_the_purpose[1440]
[gw3] [ 99%] PASSED tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_ready_resolve_people_locked_1440
tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_ready_resolve_people_locked_393
[gw1] [ 99%] PASSED tests/e2e/test_hs200_preparation_brief_glass.py::test_unavailable_model_refuses_and_keeps_the_purpose[1440]
tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_not_set_up_1440
[gw3] [ 99%] PASSED tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_ready_resolve_people_locked_393
[gw2] [ 99%] XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900]
[gw1] [ 99%] PASSED tests/e2e/test_hs200_people_preparation_glass.py::TestPeoplePreparationGlass::test_not_set_up_1440
[gw0] [ 99%] XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900]
[gw2] [ 99%] XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900]
[gw0] [100%] XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900]

=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:17: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:160: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.76xDQ5OOzx/xdist-gw3/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.76xDQ5OOzx/xdist-gw3/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.76xDQ5OOzx/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:552: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:618: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:171: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:232: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:281: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:149: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:396: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:461: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:554: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:270: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:521: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:673: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:921: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1090: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:327: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:281: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:367: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-201-a/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
========== 11264 passed, 116 skipped, 4 xfailed in 1508.86s (0:25:08) ==========
```

## Closure accounting

Final `dw check holdspeak` has exactly the six pre-existing bookkeeping findings: Phase 101 evidence/story mismatch and missing final summaries for 152, 153, 154, 156 and 200. Story 08 introduces no remaining finding; the phase exit and story 07 are not closed. No source/test/metadata/generator edits followed the 07:17:48Z docs input tree. The staged delta check below is taken after the final shot copies and closure records.

### Captured run — 2026-09-20T07:50:14Z

- **Command:** `python3 -c import subprocess; t="6c8c47bdfeeae64d3246cd592aa309a3a0e9f645"; p=subprocess.check_output(["git","diff","--cached","--name-only",t],text=True).splitlines(); assert all(x.startswith("pm/roadmap/") for x in p),p; assert not subprocess.check_output(["git","diff","--name-only"],text=True).strip(); print("Verified docs input tree:",t); print("Only roadmap closure/shot changes after T1:",len(p)); print("\n".join(p)); print("No unstaged tracked changes at proof start.")`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9fdfe2fbb1327baee85ff954cd2b4556ff851ba0

```text
Verified docs input tree: 6c8c47bdfeeae64d3246cd592aa309a3a0e9f645
Only roadmap closure/shot changes after T1: 12
pm/roadmap/holdspeak/BACKLOG.md
pm/roadmap/holdspeak/README.md
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/guardrail-decision-box-1440.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/guardrail-decision-box-393.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/guardrail-row-1440.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/guardrail-row-393.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/taskresume-after-restart-1440.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots/taskresume-after-restart-393.png
pm/roadmap/holdspeak/phase-201-one-meeting-result/checks/story-08-late-built-muaddib.md
pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md
pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-08.md
pm/roadmap/holdspeak/phase-201-one-meeting-result/story-08-main-is-green.md
No unstaged tracked changes at proof start.
```

## Final counsel and lane record

Muad'Dib's final closure verdict is **RATIFY**, recorded in `checks/story-08-closure-muaddib.md`. He independently read the complete passing tail and verified the unchanged runtime inputs. Astra independently verified the identical normalized skip list, all 12 historical failing node IDs now passing, and the final shots. AC7's delivery separation is explicitly ratified; delivery remains required.

- **LANE:** HS-201-08, Astra, `feat/hs-201-green` in `wt-201-a`, base 321247d2. Main and wt-201-b untouched.
- **OUTCOME:** green locally; story 07 and the owner sitting remain the phase close. Gated commit, push and exact-title PR follow this verified record; no merge.
- **PROOF:** 11,264 passed, 116 skipped, four existing strict xfails; web 2,601 passed; eleven docs commands; focused red/green and both-width shots. Full capture 07:18:40Z.
- **LEDGER:** seeded day-1 continuity and fixture envelopes; parked production follow-through; guardrail reason hydration; observer fallback; inode identity; descriptor source and other singleton fixtures; generated-reference limits; six existing DW bookkeeping findings. See BACKLOG.
- **AMENDMENTS:** notifications are (a) clock setup, not (c); current-law daily loop preserves later continuity from explicit history; roadmaps, references and four late full-run families included; scheduler changes distribution only; AC7 separates performed checks from external delivery.
- **UNKNOWN:** branch CI, current owner creation path, and first-use observation. Local high-descriptor proof is not exercised by CI. A failed branch check reopens verification.
