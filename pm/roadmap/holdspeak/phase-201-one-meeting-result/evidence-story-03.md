# Evidence - HS-201-03

- **Story:** HS-201-03 - The host is disclosed before the run and truthful after
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T23:10:39Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.g72JL6Hwco uv run --extra dev pytest -q tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_route_http.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/unit/test_intel_queue.py tests/unit/test_phase143_inference_route_plans.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 27.49s
```

### Captured run — 2026-09-19T23:13:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ajEAwuS5Tj PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin uv run --extra dev pytest -q -s tests/e2e/test_hs201_lane_a_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
SUMMARY meeting=lane-a-fixture text='The team reviewed the budget.'
RECEIPT after hub restart={'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_e15f88adeba9492a813c35abf08d136e', 'outcome': 'succeeded'}], 'job_id': 'ij_292d337016ca2219beabe6eff5588d014899715484f86f13d6367df6f250437e', 'meeting_id': 'lane-a-fixture', 'outcome': 'succeeded', 'receipt_id': 'rr_ace01de7a28c6b454fd006e1417a424b', 'selection_hash': 'sha256:1eaafdf1bfaa5febbfc0cc97a1c0bd95699036296a72ea0ac52c65223166cdf5'}
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a/meeting-after-restart-1440.png
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a/meeting-after-restart-393.png
.
1 passed in 8.30s
```

## Red contract and HTTP fences — Astra, pristine charter baseline

Astra compared every tracked `holdspeak/` file in `.tmp/hs201-baseline`
against `git show fdc3fc45:<path>`: zero mismatches. An extra new projection
module from an earlier worker probe was parked outside that snapshot before
this run. These are public API/read-model assertions against unmodified
pre-fix product code, not imports of the new helper.

Command: isolated HOME, explicit baseline PYTHONPATH and shared dev venv,
`uv run --no-sync python` imports the source printed below then calls
`pytest.main(["-q", "tests/unit/test_hs201_route_contract.py",
"tests/unit/test_hs201_route_http.py"])`.

```text
BASELINE SOURCE: /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/services/meeting_intel_service.py
FFFFFFFF                                                                 [100%]
=================================== FAILURES ===================================
_____ test_unresolved_route_is_unavailable_never_local_before_post[detail] _____

meeting_db = (<holdspeak.db.core.Database object at 0x10bee17f0>, MeetingState(id='disclosure-meeting', started_at=datetime.datetim...None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]))
reader = 'detail'

    @pytest.mark.parametrize("reader", ["detail", "ledger", "recovery"])
    def test_unresolved_route_is_unavailable_never_local_before_post(meeting_db, reader):
        db, meeting = meeting_db
        if reader == "detail":
            value = MeetingService(db).get_meeting(OWNER, meeting.id)
        elif reader == "ledger":
            value = MeetingService(db).list_meetings(OWNER)["meetings"][0]
        else:
            value = MeetingIntelService(db).get_recovery(OWNER, meeting.id)
>       route = value["planned_route"]
                ^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'planned_route'

tests/unit/test_hs201_route_contract.py:47: KeyError
_____ test_unresolved_route_is_unavailable_never_local_before_post[ledger] _____

meeting_db = (<holdspeak.db.core.Database object at 0x10bf54410>, MeetingState(id='disclosure-meeting', started_at=datetime.datetim...None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]))
reader = 'ledger'

    @pytest.mark.parametrize("reader", ["detail", "ledger", "recovery"])
    def test_unresolved_route_is_unavailable_never_local_before_post(meeting_db, reader):
        db, meeting = meeting_db
        if reader == "detail":
            value = MeetingService(db).get_meeting(OWNER, meeting.id)
        elif reader == "ledger":
            value = MeetingService(db).list_meetings(OWNER)["meetings"][0]
        else:
            value = MeetingIntelService(db).get_recovery(OWNER, meeting.id)
>       route = value["planned_route"]
                ^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'planned_route'

tests/unit/test_hs201_route_contract.py:47: KeyError
____ test_unresolved_route_is_unavailable_never_local_before_post[recovery] ____

meeting_db = (<holdspeak.db.core.Database object at 0x10bf99810>, MeetingState(id='disclosure-meeting', started_at=datetime.datetim...None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]))
reader = 'recovery'

    @pytest.mark.parametrize("reader", ["detail", "ledger", "recovery"])
    def test_unresolved_route_is_unavailable_never_local_before_post(meeting_db, reader):
        db, meeting = meeting_db
        if reader == "detail":
            value = MeetingService(db).get_meeting(OWNER, meeting.id)
        elif reader == "ledger":
            value = MeetingService(db).list_meetings(OWNER)["meetings"][0]
        else:
            value = MeetingIntelService(db).get_recovery(OWNER, meeting.id)
>       route = value["planned_route"]
                ^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'planned_route'

tests/unit/test_hs201_route_contract.py:47: KeyError
____ test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash ____

meeting_db = (<holdspeak.db.core.Database object at 0x10bf9e850>, MeetingState(id='disclosure-meeting', started_at=datetime.datetim...None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]))

    def test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash(meeting_db):
        db, meeting = meeting_db
        for profile in ("summary-first", "summary-fallback"):
            summary_profile(db, profile)
        assign_summary(db, ["summary-first", "summary-fallback"])
        service = MeetingIntelService(db)
>       first = service.get_recovery(OWNER, meeting.id)["planned_route"]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'planned_route'

tests/unit/test_hs201_route_contract.py:62: KeyError
__________ test_group_assignment_cannot_be_disclosed_as_service_route __________

meeting_db = (<holdspeak.db.core.Database object at 0x10bf9b390>, MeetingState(id='disclosure-meeting', started_at=datetime.datetim...None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]))

    def test_group_assignment_cannot_be_disclosed_as_service_route(meeting_db):
        db, meeting = meeting_db
        summary_profile(db, "summary-group-only")
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": "select-group", "expected_revision": 0,
            "scope": {"kind": "group", "group_id": "meetings"},
            "entries": [{"profile_id": "summary-group-only", "profile_revision": 1}],
        })
>       route = MeetingIntelService(db).get_recovery(OWNER, meeting.id)["planned_route"]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'planned_route'

tests/unit/test_hs201_route_contract.py:86: KeyError
_ test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run] _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8770/test_http_route_refusal_and_re0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10bf02f50>
path = '/api/meetings/http-route/intelligence/run'

    @pytest.mark.parametrize('path', [
        '/api/meetings/http-route/intelligence/run',
        '/api/intel/retry/http-route',
        '/api/meetings/http-route/intel-recovery/retry',
    ])
    def test_http_route_refusal_and_repair_use_disclosed_selection(tmp_path, monkeypatch, path):
        db = Database(tmp_path / 'route-http.db')
        db.meetings.save_meeting(MeetingState(
            id='http-route', title='HTTP route', started_at=datetime.now(),
            ended_at=datetime.now(), capture_status='finalized',
            segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
        ))
        summary_profile(db, 'http-summary')
        assign_summary(db, ['http-summary'])
        service = MeetingIntelService(db)
        monkeypatch.setattr('holdspeak.intel_queue_conductor.wake_intel_queue_conductor', lambda: False)
        app = FastAPI()
    
        @app.middleware('http')
        async def principal(request: Request, call_next):
            request.state.principal = OWNER
            return await call_next(request)
    
        app.include_router(build_intel_router(WebContext(
            get_state=lambda: {}, meeting_intel_service=service,
        )))
        with TestClient(app) as client:
            for body in ({}, {'expected_selection_hash': 'stale-selection'}):
                refused = client.post(path, json=body)
>               assert refused.status_code == 409, refused.text
E               AssertionError: {"jobId":"ij_03be70b7f6bef275a336a22907c72cb2499f4ddfd9f12241147348a08aae8067","state":"queued","host":"local","drainer":"absent","expectedWithinSeconds":null}
E               assert 200 == 409
E                +  where 200 = <Response [200 OK]>.status_code

tests/unit/test_hs201_route_http.py:45: AssertionError
_ test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route] _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8770/test_http_route_refusal_and_re1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10c128a50>
path = '/api/intel/retry/http-route'

    @pytest.mark.parametrize('path', [
        '/api/meetings/http-route/intelligence/run',
        '/api/intel/retry/http-route',
        '/api/meetings/http-route/intel-recovery/retry',
    ])
    def test_http_route_refusal_and_repair_use_disclosed_selection(tmp_path, monkeypatch, path):
        db = Database(tmp_path / 'route-http.db')
        db.meetings.save_meeting(MeetingState(
            id='http-route', title='HTTP route', started_at=datetime.now(),
            ended_at=datetime.now(), capture_status='finalized',
            segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
        ))
        summary_profile(db, 'http-summary')
        assign_summary(db, ['http-summary'])
        service = MeetingIntelService(db)
        monkeypatch.setattr('holdspeak.intel_queue_conductor.wake_intel_queue_conductor', lambda: False)
        app = FastAPI()
    
        @app.middleware('http')
        async def principal(request: Request, call_next):
            request.state.principal = OWNER
            return await call_next(request)
    
        app.include_router(build_intel_router(WebContext(
            get_state=lambda: {}, meeting_intel_service=service,
        )))
        with TestClient(app) as client:
            for body in ({}, {'expected_selection_hash': 'stale-selection'}):
                refused = client.post(path, json=body)
>               assert refused.status_code == 409, refused.text
E               AssertionError: {"success":true}
E               assert 200 == 409
E                +  where 200 = <Response [200 OK]>.status_code

tests/unit/test_hs201_route_http.py:45: AssertionError
_ test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry] _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8770/test_http_route_refusal_and_re2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10c151f40>
path = '/api/meetings/http-route/intel-recovery/retry'

    @pytest.mark.parametrize('path', [
        '/api/meetings/http-route/intelligence/run',
        '/api/intel/retry/http-route',
        '/api/meetings/http-route/intel-recovery/retry',
    ])
    def test_http_route_refusal_and_repair_use_disclosed_selection(tmp_path, monkeypatch, path):
        db = Database(tmp_path / 'route-http.db')
        db.meetings.save_meeting(MeetingState(
            id='http-route', title='HTTP route', started_at=datetime.now(),
            ended_at=datetime.now(), capture_status='finalized',
            segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
        ))
        summary_profile(db, 'http-summary')
        assign_summary(db, ['http-summary'])
        service = MeetingIntelService(db)
        monkeypatch.setattr('holdspeak.intel_queue_conductor.wake_intel_queue_conductor', lambda: False)
        app = FastAPI()
    
        @app.middleware('http')
        async def principal(request: Request, call_next):
            request.state.principal = OWNER
            return await call_next(request)
    
        app.include_router(build_intel_router(WebContext(
            get_state=lambda: {}, meeting_intel_service=service,
        )))
        with TestClient(app) as client:
            for body in ({}, {'expected_selection_hash': 'stale-selection'}):
                refused = client.post(path, json=body)
>               assert refused.status_code == 409, refused.text
E               AssertionError: {"success":true,"recovery":{"meeting_id":"http-route","visible":true,"state":"queued","headline":"Meeting saved · intelligence queued","completed":[{"label":"Meeting","detail":"Saved"},{"label":"Transcript","detail":"1 saved segment"}],"remaining":{"label":"Summary, topics, action items, and routed artifacts","detail":"Retry remaining requested."},"job":{"status":"queued","attempts":0,"requested_at":"2026-09-19T17:12:46.309050","updated_at":"2026-09-19T17:12:46.309050"},"actions":{"retry":false,"skip":true}}}
E               assert 200 == 409
E                +  where 200 = <Response [200 OK]>.status_code

tests/unit/test_hs201_route_http.py:45: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[detail]
FAILED tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[ledger]
FAILED tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[recovery]
FAILED tests/unit/test_hs201_route_contract.py::test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash
FAILED tests/unit/test_hs201_route_contract.py::test_group_assignment_cannot_be_disclosed_as_service_route
FAILED tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run]
FAILED tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route]
FAILED tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry]
8 failed in 1.73s
```

## Additional completion seam found during verification

The worker initially checked persisted summary/receipt but did not assert the
drainer's return value. Astra strengthened that assertion and found refusal
receipt code in the success completion method, where it raised after saving
the result. Astra moved that code to claim refusal, then reran the focused
suite (102 pass capture above). This was a surgical diagnosed seam fix.

```text
F                                                                        [100%]
=================================== FAILURES ===================================
____ test_real_queue_drainer_records_failed_primary_and_successful_fallback ____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8749/test_real_queue_drainer_record0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10a1a0050>

    def test_real_queue_drainer_records_failed_primary_and_successful_fallback(
        tmp_path: Path, monkeypatch
    ):
        """The receipt is projected from real admitted dispatches, not fabricated rows."""
        from tests.unit.test_meeting_deferred_admission import _queue_rig, _queued_meeting
    
        db, _broker, _initial_engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
        claim = ("language", "structured_output", _result_claim("meeting.deferred_analysis"))
        _profile(db, "receipt-first", claims=claim, modalities=("language", "text"))
        _profile(db, "receipt-second", claims=claim, modalities=("language", "text"))
        InferenceAssignmentService(db).set_assignment(
            OWNER,
            {
                "command_id": "receipt-two-leg-route",
                "expected_revision": 1,
                "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
                "entries": [
                    {"profile_id": "receipt-first", "profile_revision": 1},
                    {"profile_id": "receipt-second", "profile_revision": 1},
                ],
            },
        )
        meeting = _queued_meeting(db, "receipt-real-drainer")
        route = project_route(db, invocation_id=f"meeting:{meeting.id}")
        assert route["status"] == "ready" and len(route["legs"]) == 2
        db.intel.enqueue_intel_job(
            meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
        )
    
        calls: list[str] = []
    
        class _FailingEngine:
            active_provider = "stub-local"
            active_model = "receipt-first"
    
            def analyze(self, _transcript: str, *, stream: bool = False):
                assert stream is False
                calls.append("receipt-first")
                raise ProviderPermanentNoGeneration()
    
        class _SuccessfulEngine:
            active_provider = "stub-local"
            active_model = "receipt-second"
    
            def analyze(self, _transcript: str, *, stream: bool = False):
                assert stream is False
                calls.append("receipt-second")
                return IntelResult(
                    topics=["receipt"],
                    action_items=[ActionItem(task="Keep the receipt", owner="Me")],
                    summary="Fallback generated this summary.",
                    raw_response="{}",
                )
    
        failing, successful = _FailingEngine(), _SuccessfulEngine()
    
        def build_stub(**kwargs):
            path = str(kwargs.get("model_path") or "")
            return failing if "receipt-first" in path else successful
    
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", build_stub)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: successful)
    
        from holdspeak.intel_queue import process_next_intel_job
    
        # A successful terminal job is removed from the current-job read model; the
        # durable receipt and stub call log are the evidence that this drain turn ran.
>       assert process_next_intel_job() is True
E       assert False is True
E        +  where False = <function process_next_intel_job at 0x10a0c6200>()

tests/unit/test_hs201_run_receipt.py:232: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_run_receipt.py::test_real_queue_drainer_records_failed_primary_and_successful_fallback
1 failed in 0.79s
```

```text
.                                                                        [100%]
1 passed in 0.77s
```

## On glass and restart scope

The captured hub test uses the real HTTP routes, exact assignment service,
queue and kernel. Only the provider engine is a stub. It stops and starts
the real hub on the same isolated DB, then reads the same receipt and summary.
Astra inspected both screenshot files at 1440 and 393. The existing face shows
the saved transcript; it does not yet show the summary or new route controls.
Those are lane B story 04 work, not claimed here.

## Ratified proposal-pipeline amendment — actual regression

Muad’Dib ratified analysis-only manual runs; the Phase 200 plugin-to-Review
production entry on this path is deliberately parked. This is not inherited
debt. The old expectations failed at both widths with no plugin proposals.
The raw failure tail below is retained before the strict expected-failure
classification. Summary-ready preconditions remain active.

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_________________ test_meeting_to_reviewed_outcomes[1440-1200] _________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8772/test_meeting_to_reviewed_outco0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1088389d0>
width = 1440, height = 1200

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.timeout(420)
    @pytest.mark.parametrize("width,height", [(1440, 1200), (393, 900)])
    def test_meeting_to_reviewed_outcomes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
        _ensure_build()
        server, url = _boot_with_fast_retry(tmp_path, monkeypatch)
        engine = _scripted_engine()
        try:
            from holdspeak import intel_queue_conductor as conductor
            from holdspeak.db import get_database
    
            _wire_provider(monkeypatch, engine)
            assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"
    
            from playwright.sync_api import sync_playwright
    
            errors: list[str] = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": height})
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda err: errors.append(str(err)))
                _init_desk(page, url)
                project_id = _create_project(page, "Q4 platform", f"hs200-12-proj-{width}")
    
                # ── 1. REVIEW: the real import, the real trigger, the drainer ──
                m1 = _import_transcript(page, "Architecture review")
                _api(page, "POST", f"/api/projects/{project_id}/meetings/{m1}", token=TOKEN)
                run = _run_intelligence(page, m1)
                assert run["state"] == "queued" and run["drainer"] == "running", run
>               assert _wait(lambda: len(_review(page, m1)["proposals"]) == 5, timeout=90.0), (
                    _review(page, m1), engine.plugin_calls, _diagnose(m1),
                )
E               AssertionError: ({'coverage': {'observed_at': '2026-09-19T17:12:58.945899', 'read': 6, 'state': 'available', 'turns': 6}, 'extracted_a...g': {'intel_status': 'ready', 'intel_status_detail': 'Meeting intelligence ready.', 'segments': 6}, 'plugin_runs': []})
E               assert False
E                +  where False = _wait(<function test_meeting_to_reviewed_outcomes.<locals>.<lambda> at 0x10e447b00>, timeout=90.0)

tests/e2e/test_hs200_meeting_outcomes_glass.py:373: AssertionError
__________________ test_meeting_to_reviewed_outcomes[393-900] __________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8772/test_meeting_to_reviewed_outco1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1078423f0>
width = 393, height = 900

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.timeout(420)
    @pytest.mark.parametrize("width,height", [(1440, 1200), (393, 900)])
    def test_meeting_to_reviewed_outcomes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int) -> None:
        _ensure_build()
        server, url = _boot_with_fast_retry(tmp_path, monkeypatch)
        engine = _scripted_engine()
        try:
            from holdspeak import intel_queue_conductor as conductor
            from holdspeak.db import get_database
    
            _wire_provider(monkeypatch, engine)
            assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"
    
            from playwright.sync_api import sync_playwright
    
            errors: list[str] = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": height})
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda err: errors.append(str(err)))
                _init_desk(page, url)
                project_id = _create_project(page, "Q4 platform", f"hs200-12-proj-{width}")
    
                # ── 1. REVIEW: the real import, the real trigger, the drainer ──
                m1 = _import_transcript(page, "Architecture review")
                _api(page, "POST", f"/api/projects/{project_id}/meetings/{m1}", token=TOKEN)
                run = _run_intelligence(page, m1)
                assert run["state"] == "queued" and run["drainer"] == "running", run
>               assert _wait(lambda: len(_review(page, m1)["proposals"]) == 5, timeout=90.0), (
                    _review(page, m1), engine.plugin_calls, _diagnose(m1),
                )
E               AssertionError: ({'coverage': {'observed_at': '2026-09-19T17:14:32.287416', 'read': 6, 'state': 'available', 'turns': 6}, 'extracted_a...g': {'intel_status': 'ready', 'intel_status_detail': 'Meeting intelligence ready.', 'segments': 6}, 'plugin_runs': []})
E               assert False
E                +  where False = _wait(<function test_meeting_to_reviewed_outcomes.<locals>.<lambda> at 0x1104bfce0>, timeout=90.0)

tests/e2e/test_hs200_meeting_outcomes_glass.py:373: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_to_reviewed_outcomes[1440-1200]
FAILED tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_to_reviewed_outcomes[393-900]
2 failed in 187.68s (0:03:07)
```

### Captured run — 2026-09-19T23:48:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.UxY2QbQytK uv run --extra dev pytest -q tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_route_http.py tests/unit/test_hs201_route_counsel.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/unit/test_intel_queue.py tests/unit/test_phase143_inference_route_plans.py tests/unit/test_hs170_faces_wire.py tests/unit/test_phase200_intel_drain.py tests/e2e/test_hs201_route_execution.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d7c3b1026bf07853649353cd6242c5b2eea11fb

```text
........................................................................ [ 50%]
........................................................................ [100%]
144 passed in 60.23s (0:01:00)
```

## Actual execution fences on the pristine charter baseline

Astra re-ran these three probes independently. Production modules load from
the byte-checked `fdc3fc45` archive, not the active editable install. Only the
provider leaf and unrelated installed-plugin discovery are controlled. The old
queue cannot accept a planned route, so the test keeps disclosure in memory and
uses the existing SERVICE planner to derive its actual immutable destinations.
All failures below occur after actual provider dispatch, not at a missing
import, keyword, or unready fixture. Current-tree execution tests pass in the
144-test capture above, including zero calls after drift or an omitted leg.

```text
HS-201-03 baseline execution-fence probe
root=/Users/karol/dev/tools/wt-201-a
baseline=/Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline
commit=fdc3fc45bccf2b3b995ae9f4d13cb58691717a75
cwd=/Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline
HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-baseline-home-mm_w1514
PYTHONPATH=/Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline
UV_PROJECT_ENVIRONMENT=/Users/karol/dev/tools/wt-201-a/.venv
$ uv run --no-sync python -c '<module origins>'
returncode=0
MODULE_ORIGINS
holdspeak= /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/__init__.py
intel_queue= /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/intel_queue.py
db.intel= /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/db/intel.py
probe= /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/tests/e2e/test_hs201_execution_baseline_fences.py
sys.path[0:4]= ['', '/Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline', '/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python313.zip', '/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13']

$ uv run --no-sync pytest -q -s <three scoped tests>
returncode=1
FFF
=================================== FAILURES ===================================
_ test_baseline_dispatches_failed_primary_and_fallback_but_has_no_durable_run_receipt _

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8830/test_baseline_dispatches_faile0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10b8968b0>

    def test_baseline_dispatches_failed_primary_and_fallback_but_has_no_durable_run_receipt(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, library, _broker = _rig(tmp_path, monkeypatch)
        _provider(library, "execution-primary", "192.0.2.10")
        _provider(library, "execution-fallback", "192.0.2.11")
        _assign(db, ["execution-primary", "execution-fallback"], expected_revision=_assignment_revision(db))
        meeting = _meeting(db, "hs201-baseline-real-fallback")
        expected = _authority_route(db, f"meeting:{meeting.id}")
        job_id = _enqueue_old_queue(db, meeting)
        calls: list[str] = []
        _engine_leaf(monkeypatch, calls, {"execution-primary"})
    
        from holdspeak.intel_queue import process_next_intel_job
    
        assert process_next_intel_job() is True
        attempts = _actual_attempts(db, job_id)
        assert [(item["host"], item["outcome"]) for item in attempts] == [
            ("192.0.2.10", "failed"),
            ("192.0.2.11", "succeeded"),
        ], {"expected": expected, "calls": calls, "attempts": attempts}
        assert calls == ["execution-primary", "execution-fallback"]
        # This assertion is deliberately after real fallback dispatch.  The
        # baseline has canonical kernel receipts, but no durable HS-201 run receipt
        # carrying selection_hash and the two destination attempts.
>       assert _durable_run_receipt(db, job_id) == {
            "selection_hash": expected["selection_hash"],
            "outcome": "succeeded",
            "attempts": [
                {"host": "192.0.2.10", "outcome": "failed"},
                {"host": "192.0.2.11", "outcome": "succeeded"},
            ],
        }
E       AssertionError: assert None == {'attempts': [{'host': '192.0.2.10', 'outcome': 'failed'}, {'host': '192.0.2.11', 'outcome': 'succeeded'}], 'outcome': 'succeeded', 'selection_hash': 'sha256:9ab0f07c35a0111f166dc6df24e7c8bfec01317f0393dce46e687b38dfb3da77'}
E        +  where None = _durable_run_receipt(<holdspeak.db.core.Database object at 0x10b84acf0>, 'ij_0a1251e29a0eb8651ea17b3fc74cb060a59dafa8c835daa1c9f4578c92ca1bbe')

tests/e2e/test_hs201_execution_baseline_fences.py:326: AssertionError
____ test_baseline_assignment_change_after_binder_prepare_still_dispatches _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8830/test_baseline_assignment_chang0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x108662190>

    def test_baseline_assignment_change_after_binder_prepare_still_dispatches(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, library, _broker = _rig(tmp_path, monkeypatch)
        _provider(library, "drift-primary", "192.0.2.20")
        _provider(library, "drift-new", "192.0.2.21")
        _assign(db, ["drift-primary"], expected_revision=_assignment_revision(db))
        meeting = _meeting(db, "hs201-baseline-assignment-drift")
        disclosed = _authority_route(db, f"meeting:{meeting.id}")
        job_id = _enqueue_old_queue(db, meeting)
    
        original_prepare = MeetingDeferredQueueBinder.prepare
        changed = False
    
        def prepare_then_change(self: Any, job: Any, command_ids: Any) -> None:
            nonlocal changed
            original_prepare(self, job, command_ids)
            if not changed:
                changed = True
                _assign(db, ["drift-new"], expected_revision=_assignment_revision(db))
    
        monkeypatch.setattr(MeetingDeferredQueueBinder, "prepare", prepare_then_change)
        calls: list[str] = []
        _engine_leaf(monkeypatch, calls, set())
        from holdspeak.intel_queue import process_next_intel_job
    
        assert process_next_intel_job() is True
        attempts = _actual_attempts(db, job_id)
        assert changed is True
>       assert calls == [], {
            "disclosed": disclosed,
            "calls": calls,
            "attempts": attempts,
            "job_id": job_id,
        }
E       AssertionError: {'attempts': [{'deployment_revision_id': 'dep_d7ace9c0d7faebc7bf32580ccb463f40ebff3d34ca6e010540adf6d533826cbf', 'dest...52ddfcdfe0616f064210f50c677d73c7807'}, 'job_id': 'ij_be510c95f5d699f94a8c9c701991a4ef4511633759c12facdd417c82b5a242f6'}
E       assert ['drift-new'] == []
E         
E         Left contains one more item: 'drift-new'
E         Use -v to get more diff

tests/e2e/test_hs201_execution_baseline_fences.py:365: AssertionError
___ test_baseline_disclosure_without_third_leg_still_dispatches_outside_leg ____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8830/test_baseline_disclosure_witho0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10bdf0050>

    def test_baseline_disclosure_without_third_leg_still_dispatches_outside_leg(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, library, _broker = _rig(tmp_path, monkeypatch)
        profiles = ["undisclosed-one", "undisclosed-two", "undisclosed-three"]
        for index, profile_id in enumerate(profiles, 10):
            _provider(library, profile_id, f"192.0.2.{index}")
        _assign(db, profiles, expected_revision=_assignment_revision(db))
        meeting = _meeting(db, "hs201-baseline-undisclosed-third")
        full = _authority_route(db, f"meeting:{meeting.id}")
        disclosed = {**full, "legs": list(full["legs"][:2])}
        job_id = _enqueue_old_queue(db, meeting)
        calls: list[str] = []
        # Force the old fallback controller to reach the third assignment.  The
        # first two are the only disclosed legs; HS-201 must refuse before this
        # third provider receives the transcript.
        _engine_leaf(monkeypatch, calls, {"undisclosed-one", "undisclosed-two"})
        from holdspeak.intel_queue import process_next_intel_job
    
        assert process_next_intel_job() is True
        attempts = _actual_attempts(db, job_id)
        disclosed_profiles = [str(item["profile_id"]) for item in disclosed["legs"]]
>       assert calls == disclosed_profiles, {
            "disclosed": disclosed,
            "calls": calls,
            "attempts": attempts,
        }
E       AssertionError: {'attempts': [{'deployment_revision_id': 'dep_ba6425dd38a0877def64a7bcefbf523af96c32653c3731b0761c2ec808e61f42', 'dest...11', 'ordinal': 2, ...}], 'selection_hash': 'sha256:0163a806dae3b2010c6351e37e107af16700b408ac4dcdcf5964015a238611b9'}}
E       assert ['undisclosed...closed-three'] == ['undisclosed...isclosed-two']
E         
E         Left contains one more item: 'undisclosed-three'
E         Use -v to get more diff

tests/e2e/test_hs201_execution_baseline_fences.py:395: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_hs201_execution_baseline_fences.py::test_baseline_dispatches_failed_primary_and_fallback_but_has_no_durable_run_receipt
FAILED tests/e2e/test_hs201_execution_baseline_fences.py::test_baseline_assignment_change_after_binder_prepare_still_dispatches
FAILED tests/e2e/test_hs201_execution_baseline_fences.py::test_baseline_disclosure_without_third_leg_still_dispatches_outside_leg
3 failed in 2.62s


```

### Captured run — 2026-09-19T23:49:45Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.NGGPZ7BNru PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -s tests/e2e/test_hs201_lane_a_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d7c3b1026bf07853649353cd6242c5b2eea11fb

```text
SUMMARY meeting=lane-a-fixture text='The team reviewed the budget.'
RECEIPT after hub restart={'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_791d336763d041f88d3ae4246818f2ac', 'outcome': 'succeeded'}], 'job_id': 'ij_34bbb1dae229693969e11e31229160beb1ad4c20dc27cffd68bec9a666283157', 'meeting_id': 'lane-a-fixture', 'outcome': 'succeeded', 'receipt_id': 'rr_0f03f982f770d2ab9e90d251698dac72', 'selection_hash': 'sha256:a4e9869302ebc2e7bb0fd94f5eb79c6274b309efdd74ae81fa86922ccaa8e7fc'}
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a/meeting-after-restart-1440.png
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a/meeting-after-restart-393.png
.
1 passed in 12.93s
```

## Astra collection proof for the staged focused run

```text
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[detail]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[ledger]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[recovery]
tests/unit/test_hs201_route_contract.py::test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash
tests/unit/test_hs201_route_contract.py::test_group_assignment_cannot_be_disclosed_as_service_route
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_require_the_disclosed_hash_before_queueing
tests/unit/test_hs201_run_receipt.py::test_missing_or_stale_hash_refuses_before_request_or_provider
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[run]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[retry]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[recovery]
tests/unit/test_hs201_run_receipt.py::test_receipt_keeps_failed_and_fallback_dispatches_and_survives_restart
tests/unit/test_hs201_run_receipt.py::test_receipt_preserves_and_fails_a_destination_outside_the_disclosed_legs
tests/unit/test_hs201_run_receipt.py::test_real_queue_drainer_records_failed_primary_and_successful_fallback
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry]
tests/unit/test_hs201_route_counsel.py::test_missing_hash_does_not_replace_a_completed_run
tests/unit/test_hs201_route_counsel.py::test_missing_or_stale_hash_does_not_hide_a_queued_owner
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[running]
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[reserved]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intelligence/run]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/intel/retry/counsel-http]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intel-recovery/retry]
tests/unit/test_hs201_route_counsel.py::test_undisclosed_kernel_attempt_is_kept_and_fails_receipt
tests/unit/test_hs201_route_counsel.py::test_scheduled_retry_claim_refusal_has_no_terminal_receipt
tests/unit/test_hs201_route_counsel.py::test_mcp_run_requires_a_disclosed_hash_before_dispatch
tests/unit/test_hs201_route_counsel.py::test_meeting_list_resolves_global_route_once
tests/unit/test_meeting_deferred_admission.py::test_a_closed_live_session_is_never_revived
tests/unit/test_meeting_deferred_admission.py::test_stop_handoff_post_commit_cancels_do_not_serially_delay_stop
tests/unit/test_meeting_deferred_admission.py::test_stop_provider_known_settlement_activates_normal_bound_queue_claim
tests/unit/test_meeting_deferred_admission.py::test_settled_stop_handoff_skipped_by_owner_never_unknown_recovers
tests/unit/test_meeting_deferred_admission.py::test_stop_provider_unknown_dispatch_keeps_reservation_and_fresh_admits
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_executes_stored_service_member_and_completes_ledger
tests/unit/test_meeting_deferred_admission.py::test_pre_c_unbound_claim_is_cut_over_inert_and_only_a_fresh_descriptor_can_bind
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_replaces_legacy_stop_handoff_with_frozen_descriptor
tests/unit/test_meeting_deferred_admission.py::test_stop_and_recovery_replays_preserve_v3_handoff_leaf
tests/unit/test_meeting_deferred_admission.py::test_zero_frozen_bookmarks_omit_label_route_and_preserve_analysis
tests/unit/test_meeting_deferred_admission.py::test_live_bound_executor_lease_excludes_background_http_and_cli_competitors
tests/unit/test_meeting_deferred_admission.py::test_stale_takeover_reconciles_only_its_own_execution
tests/unit/test_meeting_deferred_admission.py::test_bound_executor_heartbeat_exception_fails_closed
tests/unit/test_meeting_deferred_admission.py::test_stale_executor_cannot_publish_or_settle_after_epoch_takeover
tests/unit/test_meeting_deferred_admission.py::test_stale_bound_executor_takeover_cas_allows_one_cross_connection_owner
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_commit_recovers_exact_owner_without_second_egress
tests/unit/test_meeting_deferred_admission.py::test_bound_publication_fence_supersedes_stale_result
tests/unit/test_meeting_deferred_admission.py::test_bound_deferred_kernel_refusal_is_terminal_with_one_attempt
tests/unit/test_meeting_deferred_admission.py::test_bound_retry_success_hides_failed_ancestor_from_all_ordinary_readers
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_operations_are_frozen_and_budgeted_per_instance
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_labels_preserve_duplicate_timestamp_identities
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_publication_skips_deleted_frozen_identity
tests/unit/test_meeting_deferred_admission.py::test_claim_refusal_terminalizes_and_unbounded_drain_continues
tests/unit/test_meeting_deferred_admission.py::test_reserved_successor_never_claims_before_old_parent_receipt
tests/unit/test_meeting_deferred_admission.py::test_receipted_successor_is_promoted_once_after_process_loss
tests/unit/test_meeting_deferred_admission.py::test_claim_admits_one_job_parent_with_base_and_plugin_children
tests/unit/test_meeting_deferred_admission.py::test_a_deduped_plugin_admits_no_child
tests/unit/test_meeting_deferred_admission.py::test_each_queue_retry_admits_a_new_job_parent
tests/unit/test_meeting_deferred_admission.py::test_a_returned_error_result_fails_the_base_child_and_keeps_the_queue_vocabulary
tests/unit/test_meeting_deferred_admission.py::test_an_executed_plugin_runs_on_the_engine_its_frozen_revision_built
tests/unit/test_meeting_deferred_admission.py::test_an_llm_plugin_with_no_admitted_handle_is_refused_by_name
tests/unit/test_meeting_deferred_admission.py::test_c2_plugin_child_uses_frozen_member_and_inner_output
tests/unit/test_meeting_deferred_admission.py::test_c2_plugin_revision_drift_refuses_without_plugin_child
tests/unit/test_meeting_deferred_admission.py::test_c2_unknown_plugin_id_refuses_claim_without_any_child
tests/unit/test_meeting_deferred_admission.py::test_c2_non_executed_plugin_gates_mint_no_child[deduped]
tests/unit/test_meeting_deferred_admission.py::test_c2_non_executed_plugin_gates_mint_no_child[fault]
tests/unit/test_meeting_deferred_admission.py::test_c2_persisted_disabled_plugin_skips_before_admission
tests/unit/test_meeting_deferred_admission.py::test_a_stop_displaced_job_runs_the_bookmark_and_title_children
tests/unit/test_meeting_deferred_admission.py::test_the_meeting_is_not_ready_until_the_displaced_work_settles
tests/unit/test_meeting_deferred_admission.py::test_a_normal_deferred_job_runs_no_title_or_bookmark_children
tests/unit/test_meeting_deferred_admission.py::test_no_transcript_material_reaches_the_kernel_journal_on_the_deferred_path
tests/unit/test_meeting_deferred_admission.py::test_stop_fences_live_bundle_before_return_and_rejects_late_ready
tests/unit/test_meeting_deferred_admission.py::test_unassigned_plugin_excluded_with_receipt_core_analysis_succeeds
tests/unit/test_meeting_deferred_admission.py::test_core_capability_missing_assignment_remains_terminal
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_repository_claim_enqueue_retry_release_and_ledger_are_job_keyed
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_worker_and_http_recovery_use_repository_contracts
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_projection_dtos_session_import_and_persistence_writers_are_pinned
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_plugin_job_family_is_separate_and_non_colliding
tests/unit/test_phase143_intel_queue_inventory.py::test_legacy_rows_migrate_to_deterministic_jobs_with_attempt_history_and_replay
tests/unit/test_phase143_intel_queue_inventory.py::test_legacy_migration_rollback_preserves_the_old_shape_and_rows
tests/unit/test_phase143_intel_queue_inventory.py::test_new_shape_immutability_unique_owner_and_ordinary_reader_selection
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_backoffs_unclassified_refusal_without_claim_or_spin
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_uses_deterministic_binding_and_competing_connections_one_owner
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_never_overlaps_legacy_running_owner_or_recovery_replay
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_transcript_fence_supersedes_and_links_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_staging_fence_supersedes_exact_bound_owner_and_links_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_retry_terminalizes_old_owner_and_records_linked_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_real_service_binder_cross_binds_one_claim_parent_and_bundle
tests/unit/test_phase143_intel_queue_inventory.py::test_real_service_binder_refusal_terminalizes_job_and_records_ledger
tests/unit/test_phase143_intel_queue_inventory.py::test_real_binder_policy_flip_between_prepare_and_claim_refuses_shell
tests/unit/test_intel_queue.py::test_worker_start_and_stop
tests/unit/test_intel_queue.py::test_compute_retry_delay_seconds_uses_exponential_backoff
tests/unit/test_intel_queue.py::test_retry_or_fail_job_requeues_bound_owner_before_max_attempts
tests/unit/test_intel_queue.py::test_retry_or_fail_job_terminalizes_bound_owner_after_max_attempts
tests/unit/test_intel_queue.py::test_compute_failure_rate_percent
tests/unit/test_intel_queue.py::test_failure_alert_hysteresis_triggers_once_per_incident
tests/unit/test_intel_queue.py::test_post_failure_alert_webhook_posts_json_payload
tests/unit/test_intel_queue.py::test_post_failure_alert_webhook_resolved_payload
tests/unit/test_intel_queue.py::test_transcript_refresh_releases_its_own_claim_without_enqueue_reset
tests/unit/test_phase143_inference_route_plans.py::test_pure_resolution_is_one_snapshot_zero_write_and_fast
tests/unit/test_phase143_inference_route_plans.py::test_disabled_leg_is_retained_as_frozen_preflight_unavailable
tests/unit/test_phase143_inference_route_plans.py::test_freeze_replay_and_restart_ignore_later_assignment_mutation
tests/unit/test_phase143_inference_route_plans.py::test_freeze_requests_are_closed_and_identity_collisions_are_named
tests/unit/test_phase143_inference_route_plans.py::test_command_pointer_tamper_and_operation_identity_collisions_refuse
tests/unit/test_phase143_inference_route_plans.py::test_recomputed_payload_hash_cannot_forge_retry_or_leg_evidence
tests/unit/test_phase143_inference_route_plans.py::test_cross_bound_assignment_profile_and_binding_tamper_refuses
tests/unit/test_phase143_inference_route_plans.py::test_legacy_adapter_is_pure_and_never_projects_locator_or_endpoint
tests/unit/test_phase143_inference_route_plans.py::test_legacy_adapter_refuses_unproved_structured_capability_before_writes
tests/unit/test_phase143_inference_route_plans.py::test_one_shot_hashes_private_material_and_attempt_ordinal_is_not_minted
tests/unit/test_phase143_inference_route_plans.py::test_executable_operation_refuses_without_registered_evidence_owner
tests/unit/test_phase143_inference_route_plans.py::test_malformed_or_capability_mismatched_provider_rolls_back_every_write
tests/unit/test_phase143_inference_route_plans.py::test_operation_reconstruction_refuses_missing_or_tampered_provider_source
tests/unit/test_phase143_inference_route_plans.py::test_recomputed_operation_and_normalized_leg_forgery_refuses
tests/unit/test_phase143_inference_route_plans.py::test_fourth_leg_is_an_exact_profile_deletion_dependency
tests/unit/test_phase143_inference_route_plans.py::test_authority_and_hub_local_sync_are_fail_closed
tests/unit/test_phase143_inference_route_plans.py::test_rails_service_policy_is_sealed_and_capability_only
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_summary_payload_no_transcript
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_summary_payload_with_transcript
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_meeting_state_to_dict_no_segments
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_meeting_state_to_dict_with_segments
tests/unit/test_hs170_faces_wire.py::TestIntelligenceRunRoute::test_refuses_without_transcript
tests/unit/test_hs170_faces_wire.py::TestIntelligenceRunRoute::test_enqueues_with_transcript
tests/unit/test_hs170_faces_wire.py::TestNeedsYouAggregate::test_sums_active_excludes_archived
tests/unit/test_hs170_faces_wire.py::TestSettingsHub::test_hub_returns_integers_default_false
tests/unit/test_phase200_intel_drain.py::test_the_conductor_starts_a_live_drainer_and_stop_joins_the_thread
tests/unit/test_phase200_intel_drain.py::test_a_second_start_in_one_process_is_a_no_op_returning_the_live_worker
tests/unit/test_phase200_intel_drain.py::test_a_process_that_does_not_own_the_database_starts_no_drainer
tests/unit/test_phase200_intel_drain.py::test_the_second_hub_refusal_is_the_real_lock_not_a_flag
tests/unit/test_phase200_intel_drain.py::test_run_intelligence_names_an_absent_drainer_instead_of_claiming_it_runs
tests/unit/test_phase200_intel_drain.py::test_run_intelligence_reports_a_running_drainer_and_wakes_it
tests/unit/test_phase200_intel_drain.py::test_the_drainer_computes_during_quiet_hours_and_notifies_nobody
tests/unit/test_phase200_intel_drain.py::test_a_failing_provider_retries_with_backoff_then_lands_failed_on_the_face
tests/unit/test_phase200_intel_drain.py::test_a_failing_job_with_no_routed_chain_still_reaches_its_ceiling
tests/unit/test_phase200_intel_drain.py::test_the_real_hub_lifespan_starts_drains_and_stops_the_intel_drainer
tests/unit/test_phase200_intel_drain.py::test_the_fence_trips_on_the_pre_fix_lifespan
tests/unit/test_phase200_intel_drain.py::test_a_finished_job_broadcasts_aftercare_ready_and_the_queue_frame
tests/unit/test_phase200_intel_drain.py::test_a_stuck_drainer_is_named_in_the_log_before_the_lock_is_released
tests/unit/test_phase200_intel_drain.py::test_the_hub_releases_the_database_only_after_the_conductors_are_stopped
tests/unit/test_phase200_intel_drain.py::test_the_model_host_is_restated_from_the_route_the_run_actually_takes
tests/unit/test_phase200_intel_drain.py::test_the_claim_planner_carries_the_recorded_host_onto_its_replacement_row
tests/unit/test_phase200_intel_drain.py::test_the_failure_alert_check_reads_the_real_database_surface
tests/unit/test_phase200_intel_drain.py::test_the_already_frozen_guard_holds_under_the_real_router
tests/unit/test_phase200_intel_drain.py::test_a_dead_cached_worker_is_replaced_not_returned
tests/unit/test_phase200_intel_drain.py::test_the_runtime_queue_frame_names_the_drainer
tests/e2e/test_hs201_route_execution.py::test_real_drainer_records_primary_failure_and_fallback_at_distinct_hosts_and_reopens
tests/e2e/test_hs201_route_execution.py::test_assignment_drift_after_binder_prepare_refuses_before_provider_dispatch
tests/e2e/test_hs201_route_execution.py::test_inconsistent_disclosure_missing_third_leg_refuses_all_provider_dispatch

144 tests collected in 0.91s

```

## Parked proposal expectations, live summary checks

Astra inspected the shared fixture and preserved assertions. Each fixture
proves import, disclosed hash, queue admission, the running drainer and a saved
ready summary before the strict xfail marker is added. The two proposal
scenarios remain distinct at both widths. Scoped worker output, read by Astra:

```text
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_summary_ready[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_summary_ready[393-900]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900]

6 tests collected in 0.18s
..xxxx
=========================== short test summary info ============================
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
2 passed, 4 xfailed in 394.76s (0:06:34)

```

The final orchestrator full suite also exercises these tests.

### Captured run — 2026-09-20T00:00:19Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.2RT3WhsEiF PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm /bin/zsh -c set -o pipefail; uv run --extra dev pytest -q -n auto --ignore=tests/e2e/test_metal.py | tee .tmp/hs201-full-suite-live.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 18f67176b9146ddd441b13c60b70687674c1230f

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................................................................ [  1%]
........................................................................ [  2%]
........................................................................ [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  5%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  7%]
ssssssssssssssssssssssssssss..........................ss......ss........ [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
.........................ssssssss.................F..................... [ 10%]
.......................................................ss....F.......... [ 10%]
........................................................................ [ 11%]
........................................................................ [ 12%]
..............................................................s......... [ 12%]
........................................................................ [ 13%]
....s................................................................... [ 14%]
........................................................................ [ 14%]
...............s........................................................ [ 15%]
........................................................................ [ 15%]
.........................................................s.............. [ 16%]
...................................................ss..............ss... [ 17%]
.......................F................................................ [ 17%]
..........................................................s............. [ 18%]
........................................................................ [ 19%]
........................................................................ [ 19%]
...................................s.................................... [ 20%]
........................................................................ [ 21%]
........................................................................ [ 21%]
.....................................sssss.............................. [ 22%]
..................................................................s..... [ 22%]
........................................................................ [ 23%]
...........................................................F............ [ 24%]
.........................................F.............................. [ 24%]
........................................................................ [ 25%]
..........................................s............................. [ 26%]
........................................................................ [ 26%]
............................................................ss.......... [ 27%]
........................................................................ [ 28%]
........................................................................ [ 28%]
........................................................................ [ 29%]
.......................................sss.............................. [ 29%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........s............................................................... [ 33%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 42%]
........................................................F............... [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
..F..................................................................... [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 50%]
........................................................................ [ 51%]
......................s................................................. [ 52%]
........................................................................ [ 52%]
...............F........................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
...................................s.................................... [ 55%]
........................................................................ [ 56%]
........................................................................ [ 56%]
......F................................................................. [ 57%]
.......................................................................F [ 57%]
........................................................................ [ 58%]
........................................................F............... [ 59%]
......s......................sss........................................ [ 59%]
........................................................................ [ 60%]
....................................................................F... [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 66%]
.......F................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
..........................F............................................. [ 70%]
........................................................................ [ 70%]
................................F....................................... [ 71%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 75%]
.......................................................s................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 77%]
......................................................s................. [ 78%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 91%]
........................................................................ [ 92%]
.................................s...................................... [ 92%]
........................................................................ [ 93%]
........................................................................ [ 94%]
........................................................................ [ 94%]
........................................................................ [ 95%]
....................s................................................... [ 96%]
........................................................................ [ 96%]
.......................F.......................x.......x..ssssssssssss.. [ 97%]
..sssssssss.......x...............ssss....ssssss.x.........FF......F.... [ 98%]
.....F..................................................ssssssssss.s.F.. [ 98%]
F..........F.F.......................................................... [ 99%]
........................................................................ [100%]
=================================== FAILURES ===================================
_________________ test_committed_manifest_matches_the_live_app _________________
[gw8] darwin -- Python 3.13.11 /Users/karol/dev/tools/wt-201-a/.venv/bin/python3

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
E         At index 139 diff: {'path': '/api/connections', 'methods': ['GET'], 'module': 'web.routes.connections', 'consumers': ['web']} != {'path': '/api/concierge/summary-selection', 'methods': ['POST'], 'module': 'web.routes.concierge', 'consumers': ['web']}
E         Right contains one more item: {'consumers': ['web'], 'methods': ['WS'], 'module': 'web.routes.system.voice_stream', 'path': '/ws/dictation/stream'}
E         Use -v to get more diff

tests/unit/test_api_surface.py:52: AssertionError
________ TestDatabaseShape.test_fresh_schema_matches_canonical_snapshot ________
[gw10] darwin -- Python 3.13.11 /Users/karol/dev/tools/wt-201-a/.venv/bin/python3

self = <tests.unit.test_db.TestDatabaseShape object at 0x113f86850>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8847/popen-gw10/test_fresh_schema_matches_cano0')
project_root = PosixPath('/Users/karol/dev/tools/wt-201-a')

    def test_fresh_schema_matches_canonical_snapshot(self, tmp_path, project_root: Path):
        """HS-31-04: the migration ladder was squashed to one canonical schema.
        A fresh build must match the committed snapshot exactly — any intended
        schema change must update tests/fixtures/db_schema_canonical.txt in the
        same commit, keeping the schema honest without a version ladder."""
        import re
        import sqlite3
        from holdspeak.db import Database
    
        Database(tmp_path / "schema_check.db")
        conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        actual = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
        ) + "\n"
        conn.close()
    
        snapshot = project_root / "tests" / "fixtures" / "db_schema_canonical.txt"
        expected = snapshot.read_text()
>       assert actual == expected, (
            "Fresh DB schema diverged from the canonical snapshot. If this change is "
            f"intended, regenerate {snapshot.relative_to(project_root)}."
        )
E       AssertionError: Fresh DB schema diverged from the canonical snapshot. If this change is intended, regenerate tests/fixtures/db_schema_canonical.txt.
E       assert "index idx_ac...ease'); END\n" == "index idx_ac...ease'); END\n"
E         
E         Skipping 76032 identical leading characters in diff, use -v to show
E         - ost TEXT, requested_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')), attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT )
E         + ost TEXT, planned_route_json TEXT, run_receipt_json TEXT, requested_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')), attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT )
E         ?          ++++++++++++++++++++++++++++++++++++++++++++++++
E           table intel_snapshots: CREATE TABLE intel_snapshots ( id...
E         
E         ...Full output truncated (217 lines hidden), use '-vv' to show

tests/unit/test_db.py:1755: AssertionError
____ test_meeting_transcription_children_join_the_existing_meeting_session _____
[gw8] darwin -- Python 3.13.11 /Users/karol/dev/tools/wt-201-a/.venv/bin/python3

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8847/popen-gw8/test_meeting_transcription_chi0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1154ab0e0>

    def test_meeting_transcription_children_join_the_existing_meeting_session(
        tmp_path, monkeypatch
    ):
        """A transcription interval is a child of the LIVE meeting.session parent."""
        from holdspeak.meeting_session.intel_admission import (
            SESSION_CHILD_BUDGET,
            SESSION_DEADLINE_SECONDS,
        )
        from holdspeak.meeting_session.transcribe_admission import session_child_budget
    
        def _budget() -> int:
            return session_child_budget(
                transcription=True,
                session_seconds=SESSION_DEADLINE_SECONDS,
                intelligence_budget=SESSION_CHILD_BUDGET,
            )
    
        db = Database(tmp_path / "meeting.db")
        # A Phase-B meeting parent freezes its live+speech route bundle before an
        # interval can become an admitted transcription child.
        from tests.unit.test_meeting_session_admission import _assign_bundle_routes
    
        _assign_bundle_routes(db)
        monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
        _configure(db)
        # HS-131-17 removed the session's provider preflight entirely; this session
        # runs with intelligence disabled anyway, so there is nothing left to stub.
        # Capture is outside this test's boundary and must not open host audio on CI.
        _silence_meeting_capture(monkeypatch)
    
        from holdspeak.meeting_session import MeetingSession
    
        impl = FakeImpl()
        session = MeetingSession(
            _transcriber(impl),
            intel_enabled=False,
            principal=Principal(PrincipalKind.OWNER, "meeting-owner"),
        )
        monkeypatch.setattr(session, "_transcribe_loop", lambda: None)
        state = session.start()
        assert state is not None
    
        parents = _parents(db, "meeting.session")
        assert len(parents) == 1
        # Phase B reserves the complete frozen live bundle: intelligence (4096),
        # speech preload (1), and its routed transcription allocation (17,286).
        # Keep the legacy helper's 8,418 calculation visible as historical-reader
        # coverage, but the new parent must carry the aggregate bundle budget.
        assert _budget() == 8418
>       assert int(parents[0]["child_budget"]) == 21_383
E       assert 17287 == 21383
E        +  where 17287 = int(17287)

tests/unit/test_dictation_session_admission.py:1324: A
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```


## Capture provenance clarification

The runs executed the combined lane worktree, not an isolated index snapshot.
The early captures stamped `387bab5d` are superseded for index provenance;
their raw output and original stamps are retained. No capture stamp was edited.
The quiet full suite used product/test index tree
`18f67176b9146ddd441b13c60b70687674c1230f`. Follow-up test-contract updates
and their focused verification are recorded below; no full-suite green is claimed.


## Quiet full suite — raw final tail

The capture above capped its output. The complete raw output is retained at
`audits/full-suite-astra.log`. The final failure list and totals are:

```text
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
FAILED tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
FAILED tests/unit/test_dictation_session_admission.py::test_meeting_transcription_children_join_the_existing_meeting_session
FAILED tests/unit/test_doc_drift_guard.py::test_docs_do_not_restore_retired_inference_setup_vocabulary
FAILED tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link
FAILED tests/integration/test_web_server.py::TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process
FAILED tests/integration/test_meeting_intel_recovery.py::test_partial_intel_names_retained_work_and_supports_retry_or_skip
FAILED tests/unit/test_phase143_meeting_live_cutover.py::test_stop_aftercare_upserts_one_legacy_deferred_row_for_bundle_and_record_only[False]
FAILED tests/unit/test_phase200_canon_guard.py::test_a_plain_run_writes_nothing_under_the_repo
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
FAILED tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_censused_site_has_one_capability_and_source_owner
FAILED tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused
FAILED tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[1440]
FAILED tests/e2e/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read[393]
FAILED tests/e2e/test_hs200_preparation_brief_glass.py::test_a_sent_and_answered_request_is_never_reported_as_nothing_sent
FAILED tests/e2e/test_hs200_preparation_brief_glass.py::test_stop_leaves_no_orphan_draft
FAILED tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[1440]
FAILED tests/e2e/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days[393]
FAILED tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_1440
FAILED tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_393
24 failed, 11159 passed, 125 skipped, 4 xfailed in 1642.14s (0:27:22)
```

### Captured run — 2026-09-20T00:38:39Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-pytest-nbxr7f2u PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -n auto tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_route_http.py tests/unit/test_hs201_route_counsel.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/unit/test_intel_queue.py tests/unit/test_phase143_inference_route_plans.py tests/unit/test_hs170_faces_wire.py tests/unit/test_phase200_intel_drain.py tests/e2e/test_hs201_route_execution.py tests/e2e/test_hs200_meeting_outcomes_glass.py tests/unit/test_api_surface.py tests/unit/test_db.py::TestDatabaseShape tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_phase143_inference_capability_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15a395aa43a2175568bb3ae20fa342a0202af45c

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 40%]
........................................................................ [ 80%]
.............................xx.x..x                                     [100%]
=========================== short test summary info ============================
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
176 passed, 4 xfailed in 113.17s (0:01:53)
```


## Final focused collection — Astra

All product and test source was staged for the final captures above. The tests
ran against the combined lane worktree. The post-full changes update old
contract expectations and tighten the proposal xfail boundary; product code
is unchanged from the full-suite snapshot.

```text
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[detail]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[ledger]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[recovery]
tests/unit/test_hs201_route_contract.py::test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash
tests/unit/test_hs201_route_contract.py::test_group_assignment_cannot_be_disclosed_as_service_route
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_require_the_disclosed_hash_before_queueing
tests/unit/test_hs201_run_receipt.py::test_missing_or_stale_hash_refuses_before_request_or_provider
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[run]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[retry]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[recovery]
tests/unit/test_hs201_run_receipt.py::test_receipt_keeps_failed_and_fallback_dispatches_and_survives_restart
tests/unit/test_hs201_run_receipt.py::test_receipt_preserves_and_fails_a_destination_outside_the_disclosed_legs
tests/unit/test_hs201_run_receipt.py::test_real_queue_drainer_records_failed_primary_and_successful_fallback
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry]
tests/unit/test_hs201_route_counsel.py::test_missing_hash_does_not_replace_a_completed_run
tests/unit/test_hs201_route_counsel.py::test_missing_or_stale_hash_does_not_hide_a_queued_owner
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[running]
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[reserved]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intelligence/run]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/intel/retry/counsel-http]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intel-recovery/retry]
tests/unit/test_hs201_route_counsel.py::test_undisclosed_kernel_attempt_is_kept_and_fails_receipt
tests/unit/test_hs201_route_counsel.py::test_scheduled_retry_claim_refusal_has_no_terminal_receipt
tests/unit/test_hs201_route_counsel.py::test_mcp_run_requires_a_disclosed_hash_before_dispatch
tests/unit/test_hs201_route_counsel.py::test_meeting_list_resolves_global_route_once
tests/unit/test_meeting_deferred_admission.py::test_a_closed_live_session_is_never_revived
tests/unit/test_meeting_deferred_admission.py::test_stop_handoff_post_commit_cancels_do_not_serially_delay_stop
tests/unit/test_meeting_deferred_admission.py::test_stop_provider_known_settlement_activates_normal_bound_queue_claim
tests/unit/test_meeting_deferred_admission.py::test_settled_stop_handoff_skipped_by_owner_never_unknown_recovers
tests/unit/test_meeting_deferred_admission.py::test_stop_provider_unknown_dispatch_keeps_reservation_and_fresh_admits
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_executes_stored_service_member_and_completes_ledger
tests/unit/test_meeting_deferred_admission.py::test_pre_c_unbound_claim_is_cut_over_inert_and_only_a_fresh_descriptor_can_bind
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_replaces_legacy_stop_handoff_with_frozen_descriptor
tests/unit/test_meeting_deferred_admission.py::test_stop_and_recovery_replays_preserve_v3_handoff_leaf
tests/unit/test_meeting_deferred_admission.py::test_zero_frozen_bookmarks_omit_label_route_and_preserve_analysis
tests/unit/test_meeting_deferred_admission.py::test_live_bound_executor_lease_excludes_background_http_and_cli_competitors
tests/unit/test_meeting_deferred_admission.py::test_stale_takeover_reconciles_only_its_own_execution
tests/unit/test_meeting_deferred_admission.py::test_bound_executor_heartbeat_exception_fails_closed
tests/unit/test_meeting_deferred_admission.py::test_stale_executor_cannot_publish_or_settle_after_epoch_takeover
tests/unit/test_meeting_deferred_admission.py::test_stale_bound_executor_takeover_cas_allows_one_cross_connection_owner
tests/unit/test_meeting_deferred_admission.py::test_bound_claim_commit_recovers_exact_owner_without_second_egress
tests/unit/test_meeting_deferred_admission.py::test_bound_publication_fence_supersedes_stale_result
tests/unit/test_meeting_deferred_admission.py::test_bound_deferred_kernel_refusal_is_terminal_with_one_attempt
tests/unit/test_meeting_deferred_admission.py::test_bound_retry_success_hides_failed_ancestor_from_all_ordinary_readers
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_operations_are_frozen_and_budgeted_per_instance
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_labels_preserve_duplicate_timestamp_identities
tests/unit/test_meeting_deferred_admission.py::test_bound_bookmark_publication_skips_deleted_frozen_identity
tests/unit/test_meeting_deferred_admission.py::test_claim_refusal_terminalizes_and_unbounded_drain_continues
tests/unit/test_meeting_deferred_admission.py::test_reserved_successor_never_claims_before_old_parent_receipt
tests/unit/test_meeting_deferred_admission.py::test_receipted_successor_is_promoted_once_after_process_loss
tests/unit/test_meeting_deferred_admission.py::test_claim_admits_one_job_parent_with_base_and_plugin_children
tests/unit/test_meeting_deferred_admission.py::test_a_deduped_plugin_admits_no_child
tests/unit/test_meeting_deferred_admission.py::test_each_queue_retry_admits_a_new_job_parent
tests/unit/test_meeting_deferred_admission.py::test_a_returned_error_result_fails_the_base_child_and_keeps_the_queue_vocabulary
tests/unit/test_meeting_deferred_admission.py::test_an_executed_plugin_runs_on_the_engine_its_frozen_revision_built
tests/unit/test_meeting_deferred_admission.py::test_an_llm_plugin_with_no_admitted_handle_is_refused_by_name
tests/unit/test_meeting_deferred_admission.py::test_c2_plugin_child_uses_frozen_member_and_inner_output
tests/unit/test_meeting_deferred_admission.py::test_c2_plugin_revision_drift_refuses_without_plugin_child
tests/unit/test_meeting_deferred_admission.py::test_c2_unknown_plugin_id_refuses_claim_without_any_child
tests/unit/test_meeting_deferred_admission.py::test_c2_non_executed_plugin_gates_mint_no_child[deduped]
tests/unit/test_meeting_deferred_admission.py::test_c2_non_executed_plugin_gates_mint_no_child[fault]
tests/unit/test_meeting_deferred_admission.py::test_c2_persisted_disabled_plugin_skips_before_admission
tests/unit/test_meeting_deferred_admission.py::test_a_stop_displaced_job_runs_the_bookmark_and_title_children
tests/unit/test_meeting_deferred_admission.py::test_the_meeting_is_not_ready_until_the_displaced_work_settles
tests/unit/test_meeting_deferred_admission.py::test_a_normal_deferred_job_runs_no_title_or_bookmark_children
tests/unit/test_meeting_deferred_admission.py::test_no_transcript_material_reaches_the_kernel_journal_on_the_deferred_path
tests/unit/test_meeting_deferred_admission.py::test_stop_fences_live_bundle_before_return_and_rejects_late_ready
tests/unit/test_meeting_deferred_admission.py::test_unassigned_plugin_excluded_with_receipt_core_analysis_succeeds
tests/unit/test_meeting_deferred_admission.py::test_core_capability_missing_assignment_remains_terminal
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_repository_claim_enqueue_retry_release_and_ledger_are_job_keyed
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_worker_and_http_recovery_use_repository_contracts
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_projection_dtos_session_import_and_persistence_writers_are_pinned
tests/unit/test_phase143_intel_queue_inventory.py::test_inventory_plugin_job_family_is_separate_and_non_colliding
tests/unit/test_phase143_intel_queue_inventory.py::test_legacy_rows_migrate_to_deterministic_jobs_with_attempt_history_and_replay
tests/unit/test_phase143_intel_queue_inventory.py::test_legacy_migration_rollback_preserves_the_old_shape_and_rows
tests/unit/test_phase143_intel_queue_inventory.py::test_new_shape_immutability_unique_owner_and_ordinary_reader_selection
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_backoffs_unclassified_refusal_without_claim_or_spin
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_uses_deterministic_binding_and_competing_connections_one_owner
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_never_overlaps_legacy_running_owner_or_recovery_replay
tests/unit/test_phase143_intel_queue_inventory.py::test_bound_claim_transcript_fence_supersedes_and_links_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_staging_fence_supersedes_exact_bound_owner_and_links_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_retry_terminalizes_old_owner_and_records_linked_fresh_job
tests/unit/test_phase143_intel_queue_inventory.py::test_real_service_binder_cross_binds_one_claim_parent_and_bundle
tests/unit/test_phase143_intel_queue_inventory.py::test_real_service_binder_refusal_terminalizes_job_and_records_ledger
tests/unit/test_phase143_intel_queue_inventory.py::test_real_binder_policy_flip_between_prepare_and_claim_refuses_shell
tests/unit/test_intel_queue.py::test_worker_start_and_stop
tests/unit/test_intel_queue.py::test_compute_retry_delay_seconds_uses_exponential_backoff
tests/unit/test_intel_queue.py::test_retry_or_fail_job_requeues_bound_owner_before_max_attempts
tests/unit/test_intel_queue.py::test_retry_or_fail_job_terminalizes_bound_owner_after_max_attempts
tests/unit/test_intel_queue.py::test_compute_failure_rate_percent
tests/unit/test_intel_queue.py::test_failure_alert_hysteresis_triggers_once_per_incident
tests/unit/test_intel_queue.py::test_post_failure_alert_webhook_posts_json_payload
tests/unit/test_intel_queue.py::test_post_failure_alert_webhook_resolved_payload
tests/unit/test_intel_queue.py::test_transcript_refresh_releases_its_own_claim_without_enqueue_reset
tests/unit/test_phase143_inference_route_plans.py::test_pure_resolution_is_one_snapshot_zero_write_and_fast
tests/unit/test_phase143_inference_route_plans.py::test_disabled_leg_is_retained_as_frozen_preflight_unavailable
tests/unit/test_phase143_inference_route_plans.py::test_freeze_replay_and_restart_ignore_later_assignment_mutation
tests/unit/test_phase143_inference_route_plans.py::test_freeze_requests_are_closed_and_identity_collisions_are_named
tests/unit/test_phase143_inference_route_plans.py::test_command_pointer_tamper_and_operation_identity_collisions_refuse
tests/unit/test_phase143_inference_route_plans.py::test_recomputed_payload_hash_cannot_forge_retry_or_leg_evidence
tests/unit/test_phase143_inference_route_plans.py::test_cross_bound_assignment_profile_and_binding_tamper_refuses
tests/unit/test_phase143_inference_route_plans.py::test_legacy_adapter_is_pure_and_never_projects_locator_or_endpoint
tests/unit/test_phase143_inference_route_plans.py::test_legacy_adapter_refuses_unproved_structured_capability_before_writes
tests/unit/test_phase143_inference_route_plans.py::test_one_shot_hashes_private_material_and_attempt_ordinal_is_not_minted
tests/unit/test_phase143_inference_route_plans.py::test_executable_operation_refuses_without_registered_evidence_owner
tests/unit/test_phase143_inference_route_plans.py::test_malformed_or_capability_mismatched_provider_rolls_back_every_write
tests/unit/test_phase143_inference_route_plans.py::test_operation_reconstruction_refuses_missing_or_tampered_provider_source
tests/unit/test_phase143_inference_route_plans.py::test_recomputed_operation_and_normalized_leg_forgery_refuses
tests/unit/test_phase143_inference_route_plans.py::test_fourth_leg_is_an_exact_profile_deletion_dependency
tests/unit/test_phase143_inference_route_plans.py::test_authority_and_hub_local_sync_are_fail_closed
tests/unit/test_phase143_inference_route_plans.py::test_rails_service_policy_is_sealed_and_capability_only
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_summary_payload_no_transcript
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_summary_payload_with_transcript
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_meeting_state_to_dict_no_segments
tests/unit/test_hs170_faces_wire.py::TestTranscriptWords::test_meeting_state_to_dict_with_segments
tests/unit/test_hs170_faces_wire.py::TestIntelligenceRunRoute::test_refuses_without_transcript
tests/unit/test_hs170_faces_wire.py::TestIntelligenceRunRoute::test_enqueues_with_transcript
tests/unit/test_hs170_faces_wire.py::TestNeedsYouAggregate::test_sums_active_excludes_archived
tests/unit/test_hs170_faces_wire.py::TestSettingsHub::test_hub_returns_integers_default_false
tests/unit/test_phase200_intel_drain.py::test_the_conductor_starts_a_live_drainer_and_stop_joins_the_thread
tests/unit/test_phase200_intel_drain.py::test_a_second_start_in_one_process_is_a_no_op_returning_the_live_worker
tests/unit/test_phase200_intel_drain.py::test_a_process_that_does_not_own_the_database_starts_no_drainer
tests/unit/test_phase200_intel_drain.py::test_the_second_hub_refusal_is_the_real_lock_not_a_flag
tests/unit/test_phase200_intel_drain.py::test_run_intelligence_names_an_absent_drainer_instead_of_claiming_it_runs
tests/unit/test_phase200_intel_drain.py::test_run_intelligence_reports_a_running_drainer_and_wakes_it
tests/unit/test_phase200_intel_drain.py::test_the_drainer_computes_during_quiet_hours_and_notifies_nobody
tests/unit/test_phase200_intel_drain.py::test_a_failing_provider_retries_with_backoff_then_lands_failed_on_the_face
tests/unit/test_phase200_intel_drain.py::test_a_failing_job_with_no_routed_chain_still_reaches_its_ceiling
tests/unit/test_phase200_intel_drain.py::test_the_real_hub_lifespan_starts_drains_and_stops_the_intel_drainer
tests/unit/test_phase200_intel_drain.py::test_the_fence_trips_on_the_pre_fix_lifespan
tests/unit/test_phase200_intel_drain.py::test_a_finished_job_broadcasts_aftercare_ready_and_the_queue_frame
tests/unit/test_phase200_intel_drain.py::test_a_stuck_drainer_is_named_in_the_log_before_the_lock_is_released
tests/unit/test_phase200_intel_drain.py::test_the_hub_releases_the_database_only_after_the_conductors_are_stopped
tests/unit/test_phase200_intel_drain.py::test_the_model_host_is_restated_from_the_route_the_run_actually_takes
tests/unit/test_phase200_intel_drain.py::test_the_claim_planner_carries_the_recorded_host_onto_its_replacement_row
tests/unit/test_phase200_intel_drain.py::test_the_failure_alert_check_reads_the_real_database_surface
tests/unit/test_phase200_intel_drain.py::test_the_already_frozen_guard_holds_under_the_real_router
tests/unit/test_phase200_intel_drain.py::test_a_dead_cached_worker_is_replaced_not_returned
tests/unit/test_phase200_intel_drain.py::test_the_runtime_queue_frame_names_the_drainer
tests/e2e/test_hs201_route_execution.py::test_real_drainer_records_primary_failure_and_fallback_at_distinct_hosts_and_reopens
tests/e2e/test_hs201_route_execution.py::test_assignment_drift_after_binder_prepare_refuses_before_provider_dispatch
tests/e2e/test_hs201_route_execution.py::test_inconsistent_disclosure_missing_third_leg_refuses_all_provider_dispatch
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_summary_ready[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_summary_ready[393-900]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200]
tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900]
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_api_surface.py::test_clients_only_call_served_routes
tests/unit/test_api_surface.py::test_manifest_is_not_vacuous
tests/unit/test_api_surface.py::test_extractors_see_the_real_call_sites
tests/unit/test_db.py::TestDatabaseShape::test_meeting_database_has_no_duplicate_method_definitions
tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
tests/unit/test_phase143_routing_authority_census.py::test_census_inventory_has_one_owner_for_each_mutable_family
tests/unit/test_phase143_routing_authority_census.py::test_census_anchors_current_routing_resolvers_and_legacy_assignment_writers
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_rejects_a_new_public_resolver_or_late_pointer_read
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopters_have_zero_python_resolution_forks
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopter_fork_scan_rejects_local_resolver_or_runner
tests/unit/test_phase143_routing_authority_census.py::test_profile_service_owner_gate_is_enforced_before_lookup_or_probe
tests/unit/test_phase143_routing_authority_census.py::test_path_bearing_profile_sync_seam_is_a_named_blocker_not_an_exception
tests/unit/test_phase143_routing_authority_census.py::test_phase_f_meeting_execution_surface_has_no_v1_resolver_or_direct_runner
tests/unit/test_phase143_routing_authority_census.py::test_legacy_assignment_writers_are_delete_work_and_acquisition_is_availability_only
tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified
tests/unit/test_phase143_surface_fallback_census.py::test_web_route_pointer_controls_are_classified_and_single_owned
tests/unit/test_phase143_surface_fallback_census.py::test_story143_workflow_aliases_decode_once_and_no_adopter_reopens_fake_fallback
tests/unit/test_phase143_surface_fallback_census.py::test_census_artifact_covers_every_guarded_surface_and_recovery_kind
tests/unit/test_phase143_surface_fallback_census.py::test_swift_retry_and_fallback_policy_sites_are_exact_and_fail_closed
tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed
tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner
tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers
tests/unit/test_phase143_inference_capability_census.py::test_phase143_semantic_census_rejects_new_ask_or_recipe_caller
tests/unit/test_phase143_inference_capability_census.py::test_phase143_swift_physical_leaves_remain_explicit_held_scope
tests/unit/test_phase143_inference_capability_census.py::test_phase143_swift_census_rejects_fallback_or_new_provider_open
tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_censused_site_has_one_capability_and_source_owner
tests/unit/test_phase143_inference_capability_census.py::test_phase143_physical_leaves_have_no_legacy_bypass

180 tests collected in 1.84s
```

### Captured run — 2026-09-20T00:47:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ikfcfAlmAw uv run --extra dev pytest -q tests/integration/test_web_server.py tests/integration/test_meeting_intel_recovery.py tests/unit/test_hs201_route_http.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b7d8063418406b22d4297be9f297c60a7adab5fd

```text
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 50.79s
```


## Integration caller migration — closure condition 4

Muad'Dib assigned A the two existing integration test files in the closure
check. Both create a compatible exact assignment, read the current route and
submit its hash. The 409 guard is unchanged. This is a test-only follow-up
after the full run. The capture above ran the combined lane worktree; its
index stamp is the story-03 staging subset, not isolated import provenance.

Before migration:

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
______ TestIntelQueueApiEndpoints.test_intel_jobs_list_retry_and_process _______

self = <tests.integration.test_web_server.TestIntelQueueApiEndpoints object at 0x10f79d810>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10f8488a0>
isolated_db = <holdspeak.db.core.Database object at 0x10f8b8050>
test_client = <starlette.testclient.TestClient object at 0x112380980>

    def test_intel_jobs_list_retry_and_process(self, monkeypatch, isolated_db, test_client):
        # Three REAL queue rows: one due now, one scheduled into the future,
        # one failed. The status filter, the aggregate summary and the retry
        # verb are all answered by the queue the hub actually reads.
        def _meeting(meeting_id: str, minute: int, title: str) -> None:
            isolated_db.meetings.save_meeting(
                MeetingState(
                    id=meeting_id,
                    started_at=datetime(2025, 1, 11, 10, minute, 0),
                    ended_at=datetime(2025, 1, 11, 10, minute + 20, 0),
                    title=title,
                    segments=[
                        TranscriptSegment(
                            text=f"{title} transcript", speaker="Me", start_time=0.0, end_time=6.0
                        )
                    ],
                )
            )
    
        _meeting("m-001", 0, "Weekly sync")
        _meeting("m-002", 5, "Design review")
        _meeting("m-003", 10, "Retro")
    
        # C1 retries and failures mutate an owned immutable descriptor, then
        # create a successor where appropriate. Arrange claims before their
        # lifecycle transitions instead of using the retired queued-row verbs.
        isolated_db.intel.enqueue_intel_job("m-002", transcript_hash="def456")
        assert isolated_db.intel.claim_next_intel_job() is not None
        isolated_db.intel.retry_intel_job(
            "m-002",
            "transient issue",
            retry_at=datetime.now() + timedelta(hours=1),
            attempt=1,
            max_attempts=3,
        )
    
        isolated_db.intel.enqueue_intel_job("m-003", transcript_hash="ghi789")
        assert isolated_db.intel.claim_next_intel_job() is not None
        isolated_db.intel.fail_intel_job("m-003", "permanent failure")
    
        isolated_db.intel.enqueue_intel_job("m-001", transcript_hash="abc123", reason="transient issue")
        isolated_db.intel.record_intel_job_attempt(
            "m-001",
            attempt=2,
            outcome="scheduled_retry",
            error="transient issue",
            retry_at=datetime(2025, 1, 11, 10, 35, 0),
        )
    
        # The drain seam is bound INTO the service at import
        # (`meeting_intel_service.py:9`), so that is the name to replace —
        # patching `holdspeak.intel_queue` never reached the caller.
        import holdspeak.services.meeting_intel_service as intel_service_module
    
        monkeypatch.setattr(intel_service_module, "drain_intel_queue", lambda *args, **kwargs: 3)
    
        jobs_response = test_client.get("/api/intel/jobs?status=queued&limit=5")
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()
        # The status filter is real: the failed job never appears.
        assert {job["meeting_id"] for job in jobs_data["jobs"]} == {"m-001", "m-002"}
        assert all(job["status"] == "queued" for job in jobs_data["jobs"])
        due = next(job for job in jobs_data["jobs"] if job["meeting_id"] == "m-001")
        assert due["status"] == "queued"
        assert due["retry_scheduled"] is False
        assert "retries_remaining" in due
        assert len(due["retry_history"]) == 1
        assert due["retry_history"][0]["outcome"] == "scheduled_retry"
        scheduled = next(job for job in jobs_data["jobs"] if job["meeting_id"] == "m-002")
        assert scheduled["retry_scheduled"] is True
        assert scheduled["next_retry_at"] is not None
    
        summary_response = test_client.get("/api/intel/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["total_jobs"] == 3
        assert summary_data["queued_jobs"] == 2
        assert summary_data["failed_jobs"] == 1
        assert summary_data["scheduled_retry_jobs"] == 1
        assert summary_data["next_retry_at"] is not None
    
        retry_response = test_client.post("/api/intel/retry/m-001")
>       assert retry_response.status_code == 200
E       assert 409 == 200
E        +  where 409 = <Response [409 Conflict]>.status_code

tests/integration/test_web_server.py:2263: AssertionError
______ test_partial_intel_names_retained_work_and_supports_retry_or_skip _______

client = <starlette.testclient.TestClient object at 0x113c94050>
db = <holdspeak.db.core.Database object at 0x112807ed0>

    def test_partial_intel_names_retained_work_and_supports_retry_or_skip(
        client, db
    ) -> None:
        meeting = _seed_failed_partial_intel(db)
    
        response = client.get(f"/api/meetings/{meeting.id}/intel-recovery")
        assert response.status_code == 200
        recovery = response.json()
        assert recovery["headline"] == "Meeting saved · intelligence incomplete"
        assert recovery["state"] == "partial"
        assert recovery["actions"] == {"retry": True, "skip": True}
        assert recovery["remaining"] == {
            "label": "Routed meeting intelligence",
            "detail": "Decision extraction timed out.",
        }
        assert recovery["completed"] == [
            {"label": "Meeting", "detail": "Saved"},
            {"label": "Transcript", "detail": "2 saved segments"},
            {
                "label": "Meeting analysis",
                "detail": "Summary, topics, and action items saved",
            },
            {"label": "Artifacts", "detail": "1 saved artifact"},
        ]
    
        skipped = client.post(f"/api/meetings/{meeting.id}/intel-recovery/skip")
        assert skipped.status_code == 200
        skipped_recovery = skipped.json()["recovery"]
        assert skipped_recovery["headline"] == "Meeting saved · intelligence skipped"
        assert skipped_recovery["actions"] == {"retry": True, "skip": False}
    
        retained = db.meetings.get_meeting(meeting.id)
        assert retained is not None
        assert retained.id == meeting.id
        assert retained.intel_status == "skipped"
        assert retained.intel_completed_at is None
        assert len(retained.segments) == 2
        assert retained.intel is not None
        assert db.plugins.list_artifacts(meeting.id)[0].id == "artifact-retained"
        assert db.intel.list_intel_job_attempts(meeting.id)[0].outcome == "skipped"
    
        retried = client.post(f"/api/meetings/{meeting.id}/intel-recovery/retry")
>       assert retried.status_code == 200
E       assert 409 == 200
E        +  where 409 = <Response [409 Conflict]>.status_code

tests/integration/test_meeting_intel_recovery.py:144: AssertionError
=========================== short test summary info ============================
FAILED tests/integration/test_web_server.py::TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process
FAILED tests/integration/test_meeting_intel_recovery.py::test_partial_intel_names_retained_work_and_supports_retry_or_skip
2 failed in 2.10s
```

Astra's broader collection (98 passed in the capture above):

```text
tests/integration/test_web_server.py::TestFormatDuration::test_format_seconds_only
tests/integration/test_web_server.py::TestFormatDuration::test_format_minutes_and_seconds
tests/integration/test_web_server.py::TestFormatDuration::test_format_hours_minutes_seconds
tests/integration/test_web_server.py::TestFormatDuration::test_format_negative_treated_as_zero
tests/integration/test_web_server.py::TestFormatDuration::test_format_float_truncated
tests/integration/test_web_server.py::TestFindFreePort::test_returns_valid_port
tests/integration/test_web_server.py::TestFindFreePort::test_returns_different_ports
tests/integration/test_web_server.py::TestFindFreePort::test_port_is_bindable
tests/integration/test_web_server.py::TestParseIsoDatetime::test_valid_iso_string
tests/integration/test_web_server.py::TestParseIsoDatetime::test_iso_with_microseconds
tests/integration/test_web_server.py::TestParseIsoDatetime::test_iso_with_timezone
tests/integration/test_web_server.py::TestParseIsoDatetime::test_empty_string_returns_none
tests/integration/test_web_server.py::TestParseIsoDatetime::test_none_returns_none
tests/integration/test_web_server.py::TestParseIsoDatetime::test_invalid_string_returns_none
tests/integration/test_web_server.py::TestParseIsoDatetime::test_non_string_returns_none
tests/integration/test_web_server.py::TestBroadcastMessage::test_to_dict
tests/integration/test_web_server.py::TestBroadcastMessage::test_immutable
tests/integration/test_web_server.py::TestWebSocketManager::test_connect_and_disconnect
tests/integration/test_web_server.py::TestWebSocketManager::test_broadcast_to_clients
tests/integration/test_web_server.py::TestWebSocketManager::test_close_all
tests/integration/test_web_server.py::TestDashboardEndpoint::test_returns_html
tests/integration/test_web_server.py::TestDashboardEndpoint::test_contains_holdspeak
tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_references_runtime_control_endpoints
tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_includes_device_health_surface
tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_includes_egress_posture_badge
tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_includes_idle_mode_guidance_markers
tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_bootstrap_prefers_runtime_status_payload
tests/integration/test_web_server.py::TestHealthEndpoint::test_returns_ok
tests/integration/test_web_server.py::TestDeviceHealthEndpoint::test_devices_health_returns_current_registry_snapshot
tests/integration/test_web_server.py::TestDeviceHealthEndpoint::test_devices_health_hides_unknown_values_as_null
tests/integration/test_web_server.py::TestCompanionStatusEndpoint::test_companion_status_reports_ready_agent_reply_components
tests/integration/test_web_server.py::TestCompanionStatusEndpoint::test_companion_status_accepts_tmux_reply_without_text_injection
tests/integration/test_web_server.py::TestCompanionStatusEndpoint::test_companion_status_reports_setup_blockers
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_select_sets_active_target
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_dismiss_removes_session_from_waiting
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_pin_marks_session_and_exempts_from_clear_stale
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_unpin_via_pin_false
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_select_unknown_session_returns_404
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_missing_fields_return_400
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_sessions_lists_the_full_live_set_not_just_awaiting
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_sessions_agent_filter
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_sessions_tombstones_are_included_then_filterable
tests/integration/test_web_server.py::TestCompanionControlEndpoints::test_sessions_dead_sessions_fall_out_of_the_live_set
tests/integration/test_web_server.py::TestApiStateEndpoint::test_returns_state
tests/integration/test_web_server.py::TestApiStateEndpoint::test_handles_empty_state
tests/integration/test_web_server.py::TestApiStateEndpoint::test_handles_exception
tests/integration/test_web_server.py::TestApiBookmarkEndpoint::test_creates_bookmark
tests/integration/test_web_server.py::TestApiBookmarkEndpoint::test_creates_bookmark_empty_label
tests/integration/test_web_server.py::TestApiBookmarkEndpoint::test_creates_bookmark_no_body
tests/integration/test_web_server.py::TestApiBookmarkEndpoint::test_handles_callback_exception
tests/integration/test_web_server.py::TestApiStopEndpoint::test_calls_stop_callback
tests/integration/test_web_server.py::TestApiStopEndpoint::test_handles_callback_exception
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_runtime_status_falls_back_to_state
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_runtime_status_prefers_explicit_meeting_active_flag
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_runtime_status_normalizes_callback_payload
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_meeting_start_not_supported_without_callback
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_meeting_stop_uses_stop_callback_by_default
tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_meeting_stop_prefers_on_meeting_stop_callback
tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints::test_get_intent_controls_returns_safe_default_without_callback
tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints::test_intent_profile_and_override_require_callbacks
tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints::test_intent_controls_round_trip_with_callbacks
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_intent_timeline_endpoint
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_plugin_runs_endpoint
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_artifacts_endpoint
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_meeting_export_endpoint_renders_handoff_formats
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_legacy_meeting_without_mir_history_rows_remains_loadable
tests/integration/test_web_server.py::TestMirHistoryApiEndpoints::test_cli_reroute_persistence_is_visible_in_timeline_api
tests/integration/test_web_server.py::TestMeetingMetadataEndpoints::test_meeting_patch_uses_runtime_update_callback
tests/integration/test_web_server.py::TestMeetingMetadataEndpoints::test_meeting_patch_falls_back_to_title_and_tags_callbacks
tests/integration/test_web_server.py::TestDashboardLifecycleStateTransitions::test_start_stop_start_cycle_hydrates_state_and_emits_ws_events
tests/integration/test_web_server.py::TestDashboardLifecycleStateTransitions::test_websocket_supports_ping_pong_keepalive
tests/integration/test_web_server.py::TestHistoryUiSmoke::test_history_page_contains_control_plane_tabs_and_handlers
tests/integration/test_web_server.py::TestHistoryUiSmoke::test_settings_route_serves_the_global_settings_page
tests/integration/test_web_server.py::TestCompanionUiSmoke::test_companion_page_is_the_agent_desk
tests/integration/test_web_server.py::TestCadenceUiSmoke::test_cadence_page_serves_with_sections
tests/integration/test_web_server.py::TestCadenceUiSmoke::test_cadence_page_js_calls_the_api
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_get_and_put_apply_runtime_callback
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_put_ignores_defaulted_keys
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_put_strips_legacy_cloud_base_url
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_put_rejects_invalid_retry_webhook_url
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_put_ignores_partial_retry_webhook_header
tests/integration/test_web_server.py::TestSettingsApiEndpoints::test_settings_put_rejects_invalid_retry_webhook_header_name
tests/integration/test_web_server.py::TestSpeakerApiEndpoints::test_speaker_endpoints
tests/integration/test_web_server.py::TestGlobalActionItemsApiEndpoints::test_action_item_endpoints_include_review_and_edit
tests/integration/test_web_server.py::TestGlobalActionItemsApiEndpoints::test_action_item_review_and_edit_validation
tests/integration/test_web_server.py::TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process
tests/integration/test_web_server.py::TestPluginRunQueueApiEndpoints::test_plugin_jobs_list_retry_and_cancel
tests/integration/test_web_server.py::TestPluginRunQueueApiEndpoints::test_plugin_jobs_process_requires_runtime_callback
tests/integration/test_web_server.py::TestPluginRunQueueApiEndpoints::test_plugin_jobs_process_uses_runtime_callback
tests/integration/test_web_server.py::TestMeetingWebServerProperties::test_url_before_start
tests/integration/test_web_server.py::TestMeetingWebServerProperties::test_host_default
tests/integration/test_web_server.py::TestMeetingWebServerLifecycle::test_start_returns_url
tests/integration/test_web_server.py::TestMeetingWebServerLifecycle::test_stop_clears_state
tests/integration/test_web_server.py::TestMeetingWebServerLifecycle::test_double_stop_safe
tests/integration/test_meeting_intel_recovery.py::test_partial_intel_names_retained_work_and_supports_retry_or_skip
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry]

98 tests collected in 0.52s
```

### Captured run — 2026-09-20T01:59:31Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6hWDOqCZ5J PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev python .tmp/hs201_followup_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
SUMMARY meeting=lane-a-fixture text='The team reviewed the budget.'
RECEIPT after hub restart={'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_f967dc74369343eb8d2ecdf21514afa0', 'outcome': 'succeeded'}], 'job_id': 'ij_1041afcad364d6f2d57b84b3d1e3649f85cc06ab0f9f70651438b0fd95c97590', 'meeting_id': 'lane-a-fixture', 'outcome': 'succeeded', 'receipt_id': 'rr_c75e02fb3e034fadcc3dcf146a64dbb9', 'selection_hash': 'sha256:333cef0e761a7f9f4cf4968ebf1b45901c2367247edd6af33471a2a108e57ec5'}
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup/meeting-after-restart-1440.png
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup/meeting-after-restart-393.png
.
1 passed in 17.65s
```

### Captured run — 2026-09-20T02:00:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Rvcv3zYKAw .venv/bin/python .tmp/hs201_followup_red.py tests/unit/test_hs201_refusal_history.py tests/e2e/test_hs201_dispatch_exception.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
BASELINE_HEAD=ae9edfde7460e3cfe81cb87b27ba6058af9f070e
BASELINE_DIRECTORY=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-tp588zqa
PRODUCT_IMPORT=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-tp588zqa/holdspeak/__init__.py
FEEE                                                                     [100%]
==================================== ERRORS ====================================
_ ERROR at setup of test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt _

fixturedef = <FixtureDef argname='_web_bundle_is_fresh' scope='session' baseid='tests/e2e'>
request = <SubRequest '_web_bundle_is_fresh' for <Function test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
                return (yield)
            if not _is_coroutine_or_asyncgen(fixturedef.func):
>               return (yield)
                        ^^^^^

/Users/karol/dev/tools/wt-201-a/.venv/lib/python3.13/site-packages/pytest_asyncio/plugin.py:730: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/conftest.py:23: in _web_bundle_is_fresh
    _ensure_build()
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def _ensure_build() -> None:
        """Build the web bundle if any web source is newer than the marker.
    
        Cross-process safe (fcntl lock under web/); once per process after
        the first check. Never trusts a marker older than the sources.
        """
        global _build_done
        if _build_done:
            return
        built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
        lock_path = REPO / "web" / ".glass-build.lock"
>       with open(lock_path, "w") as lock:
             ^^^^^^^^^^^^^^^^^^^^
E       FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-tp588zqa/web/.glass-build.lock'

tests/e2e/glass_infra.py:148: FileNotFoundError
_ ERROR at setup of test_settlement_failure_projects_dispatch_intent_as_indeterminate _

    @pytest.fixture(scope="session", autouse=True)
    def _web_bundle_is_fresh() -> None:
>       _ensure_build()

tests/e2e/conftest.py:23: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def _ensure_build() -> None:
        """Build the web bundle if any web source is newer than the marker.
    
        Cross-process safe (fcntl lock under web/); once per process after
        the first check. Never trusts a marker older than the sources.
        """
        global _build_done
        if _build_done:
            return
        built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
        lock_path = REPO / "web" / ".glass-build.lock"
>       with open(lock_path, "w") as lock:
             ^^^^^^^^^^^^^^^^^^^^
E       FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-tp588zqa/web/.glass-build.lock'

tests/e2e/glass_infra.py:148: FileNotFoundError
_ ERROR at setup of test_pre_send_refusal_keeps_the_receipt_empty_and_does_not_call_provider _

    @pytest.fixture(scope="session", autouse=True)
    def _web_bundle_is_fresh() -> None:
>       _ensure_build()

tests/e2e/conftest.py:23: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def _ensure_build() -> None:
        """Build the web bundle if any web source is newer than the marker.
    
        Cross-process safe (fcntl lock under web/); once per process after
        the first check. Never trusts a marker older than the sources.
        """
        global _build_done
        if _build_done:
            return
        built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
        lock_path = REPO / "web" / ".glass-build.lock"
>       with open(lock_path, "w") as lock:
             ^^^^^^^^^^^^^^^^^^^^
E       FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-tp588zqa/web/.glass-build.lock'

tests/e2e/glass_infra.py:148: FileNotFoundError
=================================== FAILURES ===================================
__________ test_failed_execution_survives_restart_and_later_refusals ___________

self = <holdspeak.services.meeting_intel_service.MeetingIntelService object at 0x110f2b0e0>
meeting_id = 'refusal-history', expected_selection_hash = None

    def _route_for_gesture(self, meeting_id: str, expected_selection_hash: str | None) -> dict[str, Any]:
        route = project_route(self._db, invocation_id=f"meeting:{meeting_id}")
        try:
>           require_expected_selection(route, expected_selection_hash)

holdspeak/services/meeting_intel_service.py:88: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

route = {'legs': [{'boundary': 'local', 'deployment_revision_id': 'dep2_e7a62dc8f9a8a01201b88657bb3bca368e2160b1560541e6c6c11f...: None, 'selection_hash': 'sha256:1f22eab7ef8178843ebddfc1823c1cea087834083d1267831f0128b38c9366b2', 'status': 'ready'}
expected = None

    def require_expected_selection(route: Mapping[str, Any], expected: Any) -> None:
        """Enforce the point-of-decision binding carried by a run gesture."""
        from .errors import ConflictError
    
        if route.get("status") != "ready":
            raise ConflictError("The summary route is not available.", code="route_unavailable")
        supplied = str(expected or "").strip()
        if not supplied:
>           raise ConflictError(
                "Check the summary route, then try again.",
                code="selection_hash_required",
            )
E           holdspeak.services.errors.ConflictError: Check the summary route, then try again.

holdspeak/services/meeting_route_projection.py:150: ConflictError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8963/test_failed_execution_survives0')

    def test_failed_execution_survives_restart_and_later_refusals(tmp_path: Path):
        db, meeting = _ready_db(tmp_path, "refusal-history")
        executed = _failed_execution(db, meeting.id)
        db_path = Path(db.db_path)
        db.close()
        db = Database(db_path)
        service = MeetingIntelService(db)
    
        refusal_ids: list[str] = []
        for expected_hash in (None, "stale-selection"):
            try:
>               service.run_intelligence(
                    OWNER,
                    meeting.id,
                    expected_selection_hash=expected_hash,
                )

tests/unit/test_hs201_refusal_history.py:70: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
holdspeak/services/observer.py:177: in sync_wrapper
    result = fn(self, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
holdspeak/services/meeting_intel_service.py:158: in run_intelligence
    route = self._route_for_gesture(meeting_id, expected_selection_hash)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <holdspeak.services.meeting_intel_service.MeetingIntelService object at 0x110f2b0e0>
meeting_id = 'refusal-history', expected_selection_hash = None

    def _route_for_gesture(self, meeting_id: str, expected_selection_hash: str | None) -> dict[str, Any]:
        route = project_route(self._db, invocation_id=f"meeting:{meeting_id}")
        try:
            require_expected_selection(route, expected_selection_hash)
        except ConflictError as exc:
            receipt = self._db.intel.record_route_refusal(
                meeting_id,
                planned_route=route,
                expected_selection_hash=expected_selection_hash,
                reason=str(exc),
            )
>           raise self._conflict(
                meeting_id,
                str(exc),
                code=exc.code,
                run_receipt=receipt,
                planned_route=route,
            ) from exc
E           holdspeak.services.errors.ConflictError: Check the summary route, then try again.

holdspeak/services/meeting_intel_service.py:96: ConflictError

During handling of the above exception, another exception occurred:

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8963/test_failed_execution_survives0')

    def test_failed_execution_survives_restart_and_later_refusals(tmp_path: Path):
        db, meeting = _ready_db(tmp_path, "refusal-history")
        executed = _failed_execution(db, meeting.id)
        db_path = Path(db.db_path)
        db.close()
        db = Database(db_path)
        service = MeetingIntelService(db)
    
        refusal_ids: list[str] = []
        for expected_hash in (None, "stale-selection"):
            try:
                service.run_intelligence(
                    OWNER,
                    meeting.id,
                    expected_selection_hash=expected_hash,
                )
            except ConflictError as exc:
                assert exc.code in {"selection_hash_required", "selection_drift"}
>               assert exc.context["run_receipt"] == executed
E               AssertionError: assert {'attempts': ...refused', ...} == {'attempts': ...'failed', ...}
E                 
E                 Omitting 1 identical items, use -vv to show
E                 Differing items:
E                 {'selection_hash': None} != {'selection_hash': 'sha256:1f22eab7ef8178843ebddfc1823c1cea087834083d1267831f0128b38c9366b2'}
E                 {'receipt_id': 'rr_8e9cdb3782dd8e21d83aacc23766aae8'} != {'receipt_id': 'rr_69c8ad81714afa37e17a1f4f8885c313'}
E                 {'attempts': []} != {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op-failed-primary', 'outcome': 'failed'}]}
E                 {'outcome': 'refused'} != {'outcome': 'failed'}...
E                 
E                 ...Full output truncated (2 lines hidden), use '-vv' to show

tests/unit/test_hs201_refusal_history.py:77: AssertionError
=========================== short test summary info ============================
ERROR tests/e2e/test_hs201_dispatch_exception.py::test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt
ERROR tests/e2e/test_hs201_dispatch_exception.py::test_settlement_failure_projects_dispatch_intent_as_indeterminate
ERROR tests/e2e/test_hs201_dispatch_exception.py::test_pre_send_refusal_keeps_the_receipt_empty_and_does_not_call_provider
FAILED tests/unit/test_hs201_refusal_history.py::test_failed_execution_survives_restart_and_later_refusals
1 failed, 3 errors in 2.86s
```

### Captured run — 2026-09-20T02:01:14Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.QOasZt8iqx .venv/bin/python .tmp/hs201_followup_red.py tests/unit/test_hs201_refusal_history.py tests/e2e/test_hs201_dispatch_exception.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
BASELINE_HEAD=ae9edfde7460e3cfe81cb87b27ba6058af9f070e
BASELINE_DIRECTORY=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-nhffu05w
PRODUCT_IMPORT=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-followup-red-nhffu05w/holdspeak/__init__.py
Backend-only baseline: skip unrelated automatic web asset build; no browser tests selected.
FFF.                                                                     [100%]
=================================== FAILURES ===================================
__________ test_failed_execution_survives_restart_and_later_refusals ___________

self = <holdspeak.services.meeting_intel_service.MeetingIntelService object at 0x10d3670e0>
meeting_id = 'refusal-history', expected_selection_hash = None

    def _route_for_gesture(self, meeting_id: str, expected_selection_hash: str | None) -> dict[str, Any]:
        route = project_route(self._db, invocation_id=f"meeting:{meeting_id}")
        try:
>           require_expected_selection(route, expected_selection_hash)

holdspeak/services/meeting_intel_service.py:88: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

route = {'legs': [{'boundary': 'local', 'deployment_revision_id': 'dep2_e7a62dc8f9a8a01201b88657bb3bca368e2160b1560541e6c6c11f...: None, 'selection_hash': 'sha256:e668b3c87af5f4e46fed705be070f1b72ba1744155b414b149e6ffeba088f997', 'status': 'ready'}
expected = None

    def require_expected_selection(route: Mapping[str, Any], expected: Any) -> None:
        """Enforce the point-of-decision binding carried by a run gesture."""
        from .errors import ConflictError
    
        if route.get("status") != "ready":
            raise ConflictError("The summary route is not available.", code="route_unavailable")
        supplied = str(expected or "").strip()
        if not supplied:
>           raise ConflictError(
                "Check the summary route, then try again.",
                code="selection_hash_required",
            )
E           holdspeak.services.errors.ConflictError: Check the summary route, then try again.

holdspeak/services/meeting_route_projection.py:150: ConflictError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8965/test_failed_execution_survives0')

    def test_failed_execution_survives_restart_and_later_refusals(tmp_path: Path):
        db, meeting = _ready_db(tmp_path, "refusal-history")
        executed = _failed_execution(db, meeting.id)
        db_path = Path(db.db_path)
        db.close()
        db = Database(db_path)
        service = MeetingIntelService(db)
    
        refusal_ids: list[str] = []
        for expected_hash in (None, "stale-selection"):
            try:
>               service.run_intelligence(
                    OWNER,
                    meeting.id,
                    expected_selection_hash=expected_hash,
                )

tests/unit/test_hs201_refusal_history.py:70: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
holdspeak/services/observer.py:177: in sync_wrapper
    result = fn(self, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
holdspeak/services/meeting_intel_service.py:158: in run_intelligence
    route = self._route_for_gesture(meeting_id, expected_selection_hash)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <holdspeak.services.meeting_intel_service.MeetingIntelService object at 0x10d3670e0>
meeting_id = 'refusal-history', expected_selection_hash = None

    def _route_for_gesture(self, meeting_id: str, expected_selection_hash: str | None) -> dict[str, Any]:
        route = project_route(self._db, invocation_id=f"meeting:{meeting_id}")
        try:
            require_expected_selection(route, expected_selection_hash)
        except ConflictError as exc:
            receipt = self._db.intel.record_route_refusal(
                meeting_id,
                planned_route=route,
                expected_selection_hash=expected_selection_hash,
                reason=str(exc),
            )
>           raise self._conflict(
                meeting_id,
                str(exc),
                code=exc.code,
                run_receipt=receipt,
                planned_route=route,
            ) from exc
E           holdspeak.services.errors.ConflictError: Check the summary route, then try again.

holdspeak/services/meeting_intel_service.py:96: ConflictError

During handling of the above exception, another exception occurred:

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8965/test_failed_execution_survives0')

    def test_failed_execution_survives_restart_and_later_refusals(tmp_path: Path):
        db, meeting = _ready_db(tmp_path, "refusal-history")
        executed = _failed_execution(db, meeting.id)
        db_path = Path(db.db_path)
        db.close()
        db = Database(db_path)
        service = MeetingIntelService(db)
    
        refusal_ids: list[str] = []
        for expected_hash in (None, "stale-selection"):
            try:
                service.run_intelligence(
                    OWNER,
                    meeting.id,
                    expected_selection_hash=expected_hash,
                )
            except ConflictError as exc:
                assert exc.code in {"selection_hash_required", "selection_drift"}
>               assert exc.context["run_receipt"] == executed
E               AssertionError: assert {'attempts': ...refused', ...} == {'attempts': ...'failed', ...}
E                 
E                 Omitting 1 identical items, use -vv to show
E                 Differing items:
E                 {'receipt_id': 'rr_035bfea8d48ae85972176e51d325bc6e'} != {'receipt_id': 'rr_7a7c81722997df2850194d2489a5316a'}
E                 {'selection_hash': None} != {'selection_hash': 'sha256:e668b3c87af5f4e46fed705be070f1b72ba1744155b414b149e6ffeba088f997'}
E                 {'job_id': 'ij_241e8f6c3036a921196e26e42767b720e0b884a17f6a92cdfc6632749984f19f'} != {'job_id': 'ij_f9fea4a0d2db09c3019094ed430bc2b0018eb822b247986c778d9b8ed9bb2059'}
E                 {'attempts': []} != {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op-failed-primary', 'outcome': 'failed'}]}...
E                 
E                 ...Full output truncated (2 lines hidden), use '-vv' to show

tests/unit/test_hs201_refusal_history.py:77: AssertionError
_____ test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8965/test_finalize_failure_keeps_th0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10d38be10>

    def test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, library, broker = _rig(tmp_path, monkeypatch)
        _provider(library, "dispatch-exception", "192.168.1.40")
        _assign(db, ["dispatch-exception"], expected_revision=0)
        meeting = _meeting(db, "hs201-dispatch-exception")
        route = project_route(db, invocation_id=f"meeting:{meeting.id}")
        db.intel.enqueue_intel_job(
            meeting.id,
            transcript_hash=meeting.transcript_hash(),
            reason="HS-201 dispatch exception",
            planned_route=route,
        )
    
        calls: list[str] = []
        _engine_leaf(monkeypatch, calls, set())
    
        def fail_after_provider(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("projection finalization failed")
    
        monkeypatch.setattr(broker.projection_stager, "finalize", fail_after_provider)
    
        from holdspeak.intel_queue import process_next_intel_job
    
        assert process_next_intel_job() is True
        assert calls == ["dispatch-exception"]
        receipt = db.intel.get_run_receipt(meeting.id)
        assert receipt is not None
        assert receipt["outcome"] == "failed"
>       assert len(receipt["attempts"]) == 1
E       assert 0 == 1
E        +  where 0 = len([])

tests/e2e/test_hs201_dispatch_exception.py:54: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue:intel_queue.py:120 Deferred intel failed for meeting hs201-dispatch-exception (attempt 1/6): retrying in 30s
ERROR    holdspeak.intel_queue:intel_queue.py:626 Bound deferred intel failed for meeting hs201-dispatch-exception: RuntimeError: projection finalization failed
______ test_settlement_failure_projects_dispatch_intent_as_indeterminate _______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8965/test_settlement_failure_projec0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10d2867b0>

    def test_settlement_failure_projects_dispatch_intent_as_indeterminate(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, library, broker = _rig(tmp_path, monkeypatch)
        _provider(library, "settlement-exception", "192.168.1.41")
        _assign(db, ["settlement-exception"], expected_revision=0)
        meeting = _meeting(db, "hs201-settlement-exception")
        route = project_route(db, invocation_id=f"meeting:{meeting.id}")
        db.intel.enqueue_intel_job(
            meeting.id,
            transcript_hash=meeting.transcript_hash(),
            reason="HS-201 settlement exception",
            planned_route=route,
        )
    
        calls: list[str] = []
        _engine_leaf(monkeypatch, calls, set())
    
        def fail_after_kernel_receipt(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("route settlement failed")
    
        monkeypatch.setattr(
            broker.inference_adoption_service.controller,
            "settle_attempt",
            fail_after_kernel_receipt,
        )
    
        from holdspeak.intel_queue import process_next_intel_job
    
        assert process_next_intel_job() is True
        assert calls == ["settlement-exception"]
        receipt = db.intel.get_run_receipt(meeting.id)
        assert receipt is not None
        assert receipt["outcome"] == "failed"
>       assert len(receipt["attempts"]) == 1
E       assert 0 == 1
E        +  where 0 = len([])

tests/e2e/test_hs201_dispatch_exception.py:96: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue:intel_queue.py:120 Deferred intel failed for meeting hs201-settlement-exception (attempt 1/6): retrying in 30s
ERROR    holdspeak.intel_queue:intel_queue.py:626 Bound deferred intel failed for meeting hs201-settlement-exception: RuntimeError: route settlement failed
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_refusal_history.py::test_failed_execution_survives_restart_and_later_refusals
FAILED tests/e2e/test_hs201_dispatch_exception.py::test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt
FAILED tests/e2e/test_hs201_dispatch_exception.py::test_settlement_failure_projects_dispatch_intent_as_indeterminate
3 failed, 1 passed in 3.78s
```

### Captured run — 2026-09-20T01:59:46Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.3n3wZC2cuq uv run --extra dev pytest -q tests/unit/test_hs201_refusal_history.py tests/e2e/test_hs201_dispatch_exception.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_route_counsel.py tests/unit/test_hs201_route_http.py tests/e2e/test_hs201_route_execution.py tests/unit/test_intel_queue.py tests/unit/test_phase200_intel_drain.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/integration/test_web_server.py tests/integration/test_meeting_intel_recovery.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
..                                                                       [100%]
218 passed in 136.55s (0:02:16)
```

### Captured run — 2026-09-20T02:03:39Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.T90FzAFyEV uv run --extra dev pytest -q tests/unit/test_backend_density_guard.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
..............................                                           [100%]
30 passed in 29.86s
```

### Captured run — 2026-09-20T02:04:44Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.JqXRFPLt1r uv run --extra dev pytest --collect-only -q tests/unit/test_hs201_refusal_history.py tests/e2e/test_hs201_dispatch_exception.py tests/unit/test_hs201_live_analysis_truth.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ac86851de893f21dda446d9bad60bd0070aaddfc

```text
tests/unit/test_hs201_refusal_history.py::test_failed_execution_survives_restart_and_later_refusals
tests/e2e/test_hs201_dispatch_exception.py::test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt
tests/e2e/test_hs201_dispatch_exception.py::test_settlement_failure_projects_dispatch_intent_as_indeterminate
tests/e2e/test_hs201_dispatch_exception.py::test_pre_send_refusal_keeps_the_receipt_empty_and_does_not_call_provider
tests/unit/test_hs201_live_analysis_truth.py::test_settings_wire_reports_live_analysis_off
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[runtime]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[egress]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[profiles]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[preflight]
tests/unit/test_hs201_live_analysis_truth.py::test_setup_trust_and_inventory_scope_live_analysis_off
tests/unit/test_hs201_live_analysis_truth.py::test_legacy_intel_write_is_ignored_and_dictation_settings_stay_intact
tests/unit/test_hs201_live_analysis_truth.py::test_cloud_preflight_does_not_probe_legacy_meeting_endpoint

12 tests collected in 1.22s
```


## Counsel follow-up — executed receipt history and dispatch exceptions

`run_receipt` retains the latest receipt with actual/pending dispatch attempts;
`last_refusal` carries the separate no-call refusal. The fields reach meeting
detail/list/recovery and the 409 response. Restart, missing/stale hashes, a later
successful receipt, and per-job identity are fenced. Post-provider projection
failure retains the succeeded attempt; settlement failure retains an
`indeterminate` dispatch intent. A pre-send refusal remains empty.

Root archived `ae9edfde` run: three expected assertion failures and one pre-send
control pass. The initial root baseline attempt also hit three unrelated asset
setup errors; those are not the dispatch RED proof. The next captured baseline
skipped only the irrelevant web build and reached both provider-contact fences.
Current root receipt/queue/HTTP suite: 218 passed. Guards: 30 passed, with only
source-line anchors and one retired display read updated. No new schema.

Both follow-up shots were inspected: saved fixture transcript, RAN and THIS
DEVICE at 1440 and 393 after a real isolated hub restart. The API retained the
fixture summary and execution receipt. These are existing-face integration
shots; B owns presentation of the new refusal field. No owner-desk or real
model-quality claim is made.

The archived baseline runner used for the raw red captures is reproduced here.
It adds only the new tests to committed production code and prints its import
path. It does not change the lane worktree.

```python
from pathlib import Path
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

root = Path.cwd()
baseline = Path(tempfile.mkdtemp(prefix="hs201-followup-red-"))
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
archive = subprocess.check_output(["git", "archive", head, "holdspeak", "tests", "pyproject.toml", "docs/trust-destinations.json"])
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(baseline, filter="data")
for test in sys.argv[1:]:
    shutil.copyfile(root / test, baseline / test)
env = {**os.environ, "HOME": tempfile.mkdtemp(prefix="hs201-red-home-"), "PYTHONPATH": str(baseline)}
python = str(root / ".venv/bin/python")
print(f"BASELINE_HEAD={head}\nBASELINE_DIRECTORY={baseline}", flush=True)
subprocess.run([python, "-c", "import holdspeak; print('PRODUCT_IMPORT=' + holdspeak.__file__)"], cwd=baseline, env=env, check=True)
runner = "import tests.e2e.glass_infra as glass; glass._build_done=True; import pytest, sys; raise SystemExit(pytest.main(['-q', *sys.argv[1:]]))"
print("Backend-only baseline: skip unrelated automatic web asset build; no browser tests selected.", flush=True)
result = subprocess.run([python, "-c", runner, *sys.argv[1:]], cwd=baseline, env=env)
raise SystemExit(result.returncode)
```

The glass runner imports `tests.e2e.test_hs201_lane_a_glass`, sets its `SHOTS`
to `assets/lane-a-followup` under this phase, and calls `pytest.main` on that
module with `-q -s`. Its capture supplies isolated HOME and the browser cache.

### Captured run — 2026-09-20T02:09:14Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.uJBYsIFdmz PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -n auto tests/unit/test_hs201_refusal_history.py tests/e2e/test_hs201_dispatch_exception.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_route_counsel.py tests/unit/test_hs201_route_http.py tests/e2e/test_hs201_route_execution.py tests/unit/test_intel_queue.py tests/unit/test_phase200_intel_drain.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_intel_queue_inventory.py tests/integration/test_web_server.py tests/integration/test_meeting_intel_recovery.py tests/unit/test_hs201_live_analysis_truth.py tests/unit/test_doctor_command.py tests/unit/test_doctor_runtime_profiles.py tests/unit/test_doctor_config_honesty.py tests/unit/test_setup_status.py tests/unit/test_setup_status_doctor_drift.py tests/unit/test_trust_destinations.py tests/unit/test_hs201_record_speech_only.py tests/unit/test_hs201_record_stop_hook.py tests/e2e/test_hs201_record_transcript.py tests/unit/test_dictation_session_admission.py tests/unit/test_backend_density_guard.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 854e4ef205c41c86164395c5b8c11e9223d97bf0

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 53%]
........................................................................ [ 71%]
..........s.......s...........ss...s..................sssss.........s... [ 89%]
.................................Meeting checkpoint failed: '_FixtureRecorder' object has no attribute 'trim_before'
........                                [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
390 passed, 11 skipped in 35.91s
```

### Captured run — 2026-09-20T02:10:13Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6hKNAfoUNs uv run --extra dev pytest -q tests/unit/test_doc_drift_guard.py tests/uat/test_build_ledger.py tests/uat/test_ledger.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 854e4ef205c41c86164395c5b8c11e9223d97bf0

```text
..................................                                       [100%]
34 passed in 1.79s
```


Post-merge runs above use follow-up product commit `a07d4bb5` plus incoming
main `675401a8`; the merge brings no product-source edits. The 390-test focused
suite passed with 11 optional-engine skips. The 34 documentation/ledger tests
also passed. No full-suite green is inferred from these focused runs.

### Captured run — 2026-09-20T03:43:08Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.yVanONFoy4 PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q --tb=short tests/uat/test_egress_cloud.py::test_cloud_card_names_target_and_remains_unexecuted tests/unit/test_mesh_liveness_surfaces.py::test_doctor_runtime_profiles_names_the_mesh_node`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 971ed9ba68da4bc83c5b013786b51190c758d8f5

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_____________ test_cloud_card_names_target_and_remains_unexecuted ______________
tests/uat/test_egress_cloud.py:45: in test_cloud_card_names_target_and_remains_unexecuted
    treatment = real_manager.apply_recipe(run.id, "egress-cloud-card")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
uat/conductor/runs.py:396: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
uat/conductor/induction/recipes.py:240: in apply
    raise RecipeVerifyError(
E   uat.conductor.induction.recipes.RecipeVerifyError: recipe 'egress-cloud-card' failed to verify: egress_scope_is: egress scope='local', endpoints=[] (want 'cloud' target containing 'api.openai.com')
_______________ test_doctor_runtime_profiles_names_the_mesh_node _______________
tests/unit/test_mesh_liveness_surfaces.py:194: in test_doctor_runtime_profiles_names_the_mesh_node
    assert "meeting intel: profile 'Pocket 4B' (mesh node 'walk-edge')" in check.detail
E   assert "meeting intel: profile 'Pocket 4B' (mesh node 'walk-edge')" in 'Live analysis is off for Record; no dictation pipeline is enabled.'
E    +  where 'Live analysis is off for Record; no dictation pipeline is enabled.' = DoctorCheck(name='Runtime profiles', status='PASS', detail='Live analysis is off for Record; no dictation pipeline is enabled.', fix=None).detail
=========================== short test summary info ============================
FAILED tests/uat/test_egress_cloud.py::test_cloud_card_names_target_and_remains_unexecuted
FAILED tests/unit/test_mesh_liveness_surfaces.py::test_doctor_runtime_profiles_names_the_mesh_node
2 failed in 5.29s
```

### Captured run — 2026-09-20T04:05:41Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.VLZ0jhrvVK PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest --collect-only -q tests/unit/test_hs201_summary_egress.py tests/unit/test_hs201_summary_doctor.py tests/unit/test_hs201_live_analysis_truth.py tests/unit/test_mesh_liveness_surfaces.py tests/unit/test_doctor_runtime_profiles.py tests/unit/test_doctor_command.py tests/unit/test_doctor_config_honesty.py tests/unit/test_doctor_observer.py tests/unit/test_setup_status.py tests/unit/test_setup_status_doctor_drift.py tests/unit/test_trust_destinations.py tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_route_counsel.py tests/unit/test_hs201_route_http.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_refusal_history.py tests/unit/test_hs201_summary_assignment.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_backend_density_guard.py tests/uat/test_egress_cloud.py tests/uat/test_decks.py tests/uat/test_recipes_parse.py tests/uat/test_no_holdspeak_import.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 971ed9ba68da4bc83c5b013786b51190c758d8f5

```text
tests/unit/test_hs201_summary_egress.py::test_summary_display_enriches_project_route_without_changing_public_route
tests/unit/test_hs201_summary_egress.py::test_trust_reports_assigned_summary_route_even_when_legacy_intel_is_off
tests/unit/test_hs201_summary_egress.py::test_legacy_cloud_fields_without_assignment_do_not_claim_summary
tests/unit/test_hs201_summary_doctor.py::test_doctor_names_assigned_summary_route_and_ignores_legacy_pointer
tests/unit/test_hs201_summary_doctor.py::test_doctor_quietly_names_unavailable_summary
tests/unit/test_hs201_summary_doctor.py::test_doctor_trust_inventory_uses_the_assigned_summary_route
tests/unit/test_hs201_live_analysis_truth.py::test_settings_wire_reports_live_analysis_off
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[runtime]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[egress]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[profiles]
tests/unit/test_hs201_live_analysis_truth.py::test_doctor_reports_live_analysis_off_for_record[preflight]
tests/unit/test_hs201_live_analysis_truth.py::test_setup_trust_and_inventory_scope_live_analysis_off
tests/unit/test_hs201_live_analysis_truth.py::test_legacy_intel_write_is_ignored_and_dictation_settings_stay_intact
tests/unit/test_hs201_live_analysis_truth.py::test_cloud_preflight_does_not_probe_legacy_meeting_endpoint
tests/unit/test_mesh_liveness_surfaces.py::test_models_rows_carry_mesh_liveness
tests/unit/test_mesh_liveness_surfaces.py::test_stale_worker_reads_offline_with_age
tests/unit/test_mesh_liveness_surfaces.py::test_non_mesh_rows_are_untouched
tests/unit/test_mesh_liveness_surfaces.py::test_ask_against_offline_mesh_node_is_an_immediate_409
tests/unit/test_mesh_liveness_surfaces.py::test_ask_against_live_mesh_node_proceeds
tests/unit/test_mesh_liveness_surfaces.py::test_inference_targets_list_reflects_mesh_liveness
tests/unit/test_mesh_liveness_surfaces.py::test_doctor_mesh_edges_states
tests/unit/test_mesh_liveness_surfaces.py::test_doctor_runtime_profiles_names_the_mesh_node
tests/unit/test_doctor_runtime_profiles.py::test_endpoint_egress_shapes
tests/unit/test_doctor_runtime_profiles.py::test_the_scattered_egress_sites_use_the_one_constructor
tests/unit/test_doctor_runtime_profiles.py::test_run_egress_default_cloud_reports_the_effective_endpoint
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_pass_names_dictation_pipeline
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_unset_reports_hub_default
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_dangling_is_a_visible_warn
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_requires_key_without_key_names_the_env
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_requires_key_with_key_passes
tests/unit/test_doctor_runtime_profiles.py::test_runtime_profiles_nothing_enabled_is_a_quiet_pass
tests/unit/test_doctor_runtime_profiles.py::test_intel_egress_is_off_for_ordinary_web_record
tests/unit/test_doctor_runtime_profiles.py::test_intel_egress_unset_detail_is_off
tests/unit/test_doctor_runtime_profiles.py::test_dictation_runtime_adopted_profile_reports_it
tests/unit/test_doctor_runtime_profiles.py::test_dictation_runtime_dangling_profile_warns_with_reason
tests/unit/test_doctor_command.py::test_check_hotkey_wayland_failure_is_warn
tests/unit/test_doctor_command.py::test_check_hotkey_non_wayland_failure_is_fail
tests/unit/test_doctor_command.py::test_transcription_backend_failure_surfaces_fix
tests/unit/test_doctor_command.py::test_run_doctor_command_strict_treats_warnings_as_failure
tests/unit/test_doctor_command.py::test_cloud_preflight_is_off_without_an_api_key
tests/unit/test_doctor_command.py::test_cloud_preflight_is_off_when_the_legacy_endpoint_is_unreachable
tests/unit/test_doctor_command.py::test_cloud_preflight_does_not_check_the_legacy_model
tests/unit/test_doctor_command.py::test_cloud_preflight_stays_off_when_the_legacy_model_is_available
tests/unit/test_doctor_command.py::test_dictation_runtime_check_pass_when_pipeline_disabled
tests/unit/test_doctor_command.py::test_dictation_runtime_check_warn_when_backend_unresolvable
tests/unit/test_doctor_command.py::test_dictation_runtime_check_warn_when_model_missing
tests/unit/test_doctor_command.py::test_dictation_runtime_check_pass_when_model_available
tests/unit/test_doctor_command.py::test_dictation_runtime_check_pass_for_openai_compatible
tests/unit/test_doctor_command.py::test_project_context_check_pass_when_pipeline_disabled
tests/unit/test_doctor_command.py::test_project_context_check_pass_when_project_detected
tests/unit/test_doctor_command.py::test_project_context_check_warn_when_no_project_detected
tests/unit/test_doctor_command.py::test_runtime_counters_check_pass_when_pipeline_disabled
tests/unit/test_doctor_command.py::test_runtime_counters_check_reports_snapshot_when_enabled
tests/unit/test_doctor_command.py::test_dictation_compile_check_pass_when_pipeline_disabled
tests/unit/test_doctor_command.py::test_dictation_compile_check_pass_when_no_blocks_file
tests/unit/test_doctor_command.py::test_dictation_compile_check_pass_for_valid_blocks
tests/unit/test_doctor_command.py::test_dictation_compile_check_warn_when_compiler_raises
tests/unit/test_doctor_command.py::test_mir_routing_check_pass_when_router_disabled
tests/unit/test_doctor_command.py::test_mir_routing_check_pass_when_enabled_with_valid_profile
tests/unit/test_doctor_command.py::test_mir_routing_check_warn_for_unknown_profile
tests/unit/test_doctor_command.py::test_mir_routing_check_never_returns_fail
tests/unit/test_doctor_command.py::test_mir_telemetry_check_smoke_passes
tests/unit/test_doctor_command.py::test_check_connector_packs_passes_with_only_first_party
tests/unit/test_doctor_command.py::test_check_connector_packs_warns_on_user_pack_errors
tests/unit/test_doctor_command.py::test_run_connector_packs_listing_returns_zero_with_no_errors
tests/unit/test_doctor_command.py::test_run_connector_packs_listing_returns_one_when_errors_present
tests/unit/test_doctor_config_honesty.py::test_database_check_absent_is_pass
tests/unit/test_doctor_config_honesty.py::test_database_check_current_is_pass
tests/unit/test_doctor_config_honesty.py::test_database_check_newer_stamp_is_still_pass
tests/unit/test_doctor_config_honesty.py::test_database_check_unreadable_is_warn
tests/unit/test_doctor_config_honesty.py::test_config_default_carries_current_version
tests/unit/test_doctor_config_honesty.py::test_config_roundtrips_version
tests/unit/test_doctor_config_honesty.py::test_config_without_version_is_coerced_forward
tests/unit/test_doctor_config_honesty.py::test_config_newer_version_is_kept_and_flagged
tests/unit/test_doctor_config_honesty.py::test_doctor_config_check_flags_newer_config
tests/unit/test_doctor_observer.py::test_check_observer_healthy_on_fresh_db
tests/unit/test_doctor_observer.py::test_check_observer_reports_event_count
tests/unit/test_setup_status.py::test_sections_mirror_doctor_checks_one_to_one
tests/unit/test_setup_status.py::test_overall_blocked_on_any_fail
tests/unit/test_setup_status.py::test_overall_needs_attention_on_warn_only
tests/unit/test_setup_status.py::test_overall_ready_when_all_pass
tests/unit/test_setup_status.py::test_unknown_status_is_normalized
tests/unit/test_setup_status.py::test_primary_action_points_at_the_fail
tests/unit/test_setup_status.py::test_primary_action_is_first_dictation_when_ready_and_first_run
tests/unit/test_setup_status.py::test_no_primary_action_when_ready_and_already_succeeded
tests/unit/test_setup_status.py::test_first_run_true_with_no_database
tests/unit/test_setup_status.py::test_first_run_flips_after_milestone_and_survives_restart
tests/unit/test_setup_status.py::test_milestone_mark_is_idempotent
tests/unit/test_setup_status.py::test_trust_default_is_local_only
tests/unit/test_setup_status.py::test_trust_keeps_legacy_cloud_off_and_preserves_actuators
tests/unit/test_setup_status.py::test_presence_tier_macos_is_hud
tests/unit/test_setup_status.py::test_presence_tier_wayland_gnome_is_notification
tests/unit/test_setup_status.py::test_status_read_skips_network_by_default
tests/unit/test_setup_status_doctor_drift.py::test_every_real_doctor_check_becomes_a_section
tests/unit/test_setup_status_doctor_drift.py::test_a_failing_check_surfaces_as_a_blocking_section
tests/unit/test_setup_status_doctor_drift.py::test_skip_network_returns_cloud_preflight_as_record_off
tests/unit/test_trust_destinations.py::test_registry_is_complete_and_inventory_is_secret_free
tests/unit/test_trust_destinations.py::test_doctor_uses_registry_names_for_enabled_destinations
tests/unit/test_trust_destinations.py::test_default_inventory_has_no_external_destination_enabled
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[detail]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[ledger]
tests/unit/test_hs201_route_contract.py::test_unresolved_route_is_unavailable_never_local_before_post[recovery]
tests/unit/test_hs201_route_contract.py::test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash
tests/unit/test_hs201_route_contract.py::test_group_assignment_cannot_be_disclosed_as_service_route
tests/unit/test_hs201_route_counsel.py::test_missing_hash_does_not_replace_a_completed_run
tests/unit/test_hs201_route_counsel.py::test_missing_or_stale_hash_does_not_hide_a_queued_owner
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[running]
tests/unit/test_hs201_route_counsel.py::test_protected_state_wins_before_hash_fence[reserved]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intelligence/run]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/intel/retry/counsel-http]
tests/unit/test_hs201_route_counsel.py::test_all_http_route_refusals_expose_the_same_contract[/api/meetings/counsel-http/intel-recovery/retry]
tests/unit/test_hs201_route_counsel.py::test_undisclosed_kernel_attempt_is_kept_and_fails_receipt
tests/unit/test_hs201_route_counsel.py::test_scheduled_retry_claim_refusal_has_no_terminal_receipt
tests/unit/test_hs201_route_counsel.py::test_mcp_run_requires_a_disclosed_hash_before_dispatch
tests/unit/test_hs201_route_counsel.py::test_meeting_list_resolves_global_route_once
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intelligence/run]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/intel/retry/http-route]
tests/unit/test_hs201_route_http.py::test_http_route_refusal_and_repair_use_disclosed_selection[/api/meetings/http-route/intel-recovery/retry]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_require_the_disclosed_hash_before_queueing
tests/unit/test_hs201_run_receipt.py::test_missing_or_stale_hash_refuses_before_request_or_provider
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[run]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[retry]
tests/unit/test_hs201_run_receipt.py::test_all_run_entry_points_preserve_record_only_no_assignment_reason[recovery]
tests/unit/test_hs201_run_receipt.py::test_receipt_keeps_failed_and_fallback_dispatches_and_survives_restart
tests/unit/test_hs201_run_receipt.py::test_receipt_preserves_and_fails_a_destination_outside_the_disclosed_legs
tests/unit/test_hs201_run_receipt.py::test_real_queue_drainer_records_failed_primary_and_successful_fallback
tests/unit/test_hs201_refusal_history.py::test_failed_execution_survives_restart_and_later_refusals
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_writes_exact_capability_with_real_profile_revision_and_preserves_speech
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_rejects_stale_profile_revision_after_profile_head_moves
tests/unit/test_hs201_summary_assignment.py::test_summary_projection_names_the_engine_that_service_will_run
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_reports_revision_conflict_without_silent_success
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_reports_partial_failure_for_incompatible_text_profile
tests/unit/test_hs201_summary_assignment.py::test_speech_assignment_cannot_use_text_only_profile
tests/unit/test_hs201_summary_assignment.py::test_summary_proposal_never_offers_text_only_engine_to_speech
tests/unit/test_hs201_summary_assignment.py::test_summary_selection_then_real_queue_binder_freezes_selected_revision
tests/unit/test_hs201_summary_assignment.py::test_model_library_connection_keeps_assignment_rows_byte_equivalent
tests/unit/test_phase143_routing_authority_census.py::test_census_inventory_has_one_owner_for_each_mutable_family
tests/unit/test_phase143_routing_authority_census.py::test_census_anchors_current_routing_resolvers_and_legacy_assignment_writers
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_rejects_a_new_public_resolver_or_late_pointer_read
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopters_have_zero_python_resolution_forks
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopter_fork_scan_rejects_local_resolver_or_runner
tests/unit/test_phase143_routing_authority_census.py::test_profile_service_owner_gate_is_enforced_before_lookup_or_probe
tests/unit/test_phase143_routing_authority_census.py::test_path_bearing_profile_sync_seam_is_a_named_blocker_not_an_exception
tests/unit/test_phase143_routing_authority_census.py::test_phase_f_meeting_execution_surface_has_no_v1_resolver_or_direct_runner
tests/unit/test_phase143_routing_authority_census.py::test_legacy_assignment_writers_are_delete_work_and_acquisition_is_availability_only
tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified
tests/unit/test_phase143_surface_fallback_census.py::test_web_route_pointer_controls_are_classified_and_single_owned
tests/unit/test_phase143_surface_fallback_census.py::test_story143_workflow_aliases_decode_once_and_no_adopter_reopens_fake_fallback
tests/unit/test_phase143_surface_fallback_census.py::test_census_artifact_covers_every_guarded_surface_and_recovery_kind
tests/unit/test_phase143_surface_fallback_census.py::test_swift_retry_and_fallback_policy_sites_are_exact_and_fail_closed
tests/unit/test_backend_density_guard.py::test_web_runtime_core_stays_boot_only
tests/unit/test_backend_density_guard.py::test_meeting_session_core_stays_lifecycle_only
tests/unit/test_backend_density_guard.py::test_runtime_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_meeting_session_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_guard_would_catch_a_regrown_module
tests/unit/test_backend_density_guard.py::test_phase79_package_inits_stay_composition_only
tests/unit/test_backend_density_guard.py::test_phase79_package_modules_stay_single_concern
tests/uat/test_egress_cloud.py::test_cloud_card_names_target_and_remains_unexecuted
tests/uat/test_decks.py::test_all_required_decks_present
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[bad-endpoint]
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[cloud-egress]
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[golden-43]
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[golden-local]
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[mesh-node]
tests/uat/test_decks.py::test_deck_roundtrips_through_config_load[no-model]
tests/uat/test_decks.py::test_bad_endpoint_points_at_dead_port
tests/uat/test_decks.py::test_golden_43_wired_to_the_lan
tests/uat/test_decks.py::test_no_model_is_local_and_quiet
tests/uat/test_decks.py::test_cloud_egress_names_endpoint_but_keeps_actuators_closed
tests/uat/test_decks.py::test_unknown_deck_raises
tests/uat/test_recipes_parse.py::test_smoke_recipes_present
tests/uat/test_recipes_parse.py::test_recipes_parse_and_declare_a_deck
tests/uat/test_recipes_parse.py::test_intel_recipes_flagged_requires_intel
tests/uat/test_recipes_parse.py::test_first_run_recipe_unlinks_caches
tests/uat/test_recipes_parse.py::test_first_run_probe_does_not_treat_optional_llm_as_a_readiness_gate
tests/uat/test_recipes_parse.py::test_include_cycle_refuses_at_load
tests/uat/test_recipes_parse.py::test_include_order_is_deps_first
tests/uat/test_recipes_parse.py::test_unknown_recipe_raises
tests/uat/test_recipes_parse.py::test_mesh_dispatch_recipe_present_and_composes
tests/uat/test_recipes_parse.py::test_cloud_egress_recipe_is_local_and_composes_seeded_control
tests/uat/test_recipes_parse.py::test_every_recipe_probe_kind_resolves
tests/uat/test_no_holdspeak_import.py::test_conductor_source_never_imports_holdspeak
tests/uat/test_no_holdspeak_import.py::test_importing_conductor_does_not_load_holdspeak

184 tests collected in 1.17s
```

### Captured run — 2026-09-20T04:06:08Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.mJJ81Y8OWy PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -n auto --tb=short tests/unit/test_hs201_summary_egress.py tests/unit/test_hs201_summary_doctor.py tests/unit/test_hs201_live_analysis_truth.py tests/unit/test_mesh_liveness_surfaces.py tests/unit/test_doctor_runtime_profiles.py tests/unit/test_doctor_command.py tests/unit/test_doctor_config_honesty.py tests/unit/test_doctor_observer.py tests/unit/test_setup_status.py tests/unit/test_setup_status_doctor_drift.py tests/unit/test_trust_destinations.py tests/unit/test_hs201_route_contract.py tests/unit/test_hs201_route_counsel.py tests/unit/test_hs201_route_http.py tests/unit/test_hs201_run_receipt.py tests/unit/test_hs201_refusal_history.py tests/unit/test_hs201_summary_assignment.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_backend_density_guard.py tests/uat/test_egress_cloud.py tests/uat/test_decks.py tests/uat/test_recipes_parse.py tests/uat/test_no_holdspeak_import.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 971ed9ba68da4bc83c5b013786b51190c758d8f5

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 39%]
........................................................................ [ 78%]
........................................                                 [100%]
184 passed in 13.30s
```

### Captured run — 2026-09-20T04:06:33Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.nHrl17Oi8N PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -s tests/e2e/test_hs201_summary_trust_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 971ed9ba68da4bc83c5b013786b51190c758d8f5

```text
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup2/summary-trust-1440.png
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup2/summary-trust-393.png
DISCOVERY_CALLS ['https://api.openai.com/v1']
ROUTE_EXECUTIONS 0
PAGE_ERRORS []
.
1 passed in 6.95s
```

### Captured run — 2026-09-20T04:07:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.hr2pMdCxgU PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q -s tests/e2e/test_hs201_summary_trust_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 971ed9ba68da4bc83c5b013786b51190c758d8f5

```text
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup2/summary-trust-1440.png
SHOT /Users/karol/dev/tools/wt-201-a/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup2/summary-trust-393.png
DISCOVERY_CALLS ['https://api.openai.com/v1']
ROUTE_EXECUTIONS 0
PAGE_ERRORS []
.
1 passed in 7.29s
```


## Follow-up 2 — classification and disclosure contract

See [Astra's audit](audits/followup2-astra.md) for the a/b/c table and exact
source anchors. Both caller-named failures are **b** product regressions.
The **a** fixture migrations select modern summary assignments instead of
retired live-analysis pointers; the target/model/node assertions remain.
No failure is classified **c**. The original two-failure red capture at
`2026-09-20T03:43:08Z` precedes product edits in this session.

The SERVICE planned route is still the selection authority. Display labels
come from its exact immutable revisions; public leg keys and selection hash
stay unchanged. Summary egress is independent of live analysis being off.
The UAT recipe now requires its isolated provider-discovery fixture and
refuses ordinary invocation before making a provider call. This evidence
proves disclosure and unexecuted proposals, not live OpenAI readiness.

Additional worker doctor red tail, read by Astra (before doctor repair):

```text
FAILED tests/unit/test_mesh_liveness_surfaces.py::test_doctor_runtime_profiles_names_the_mesh_node
FAILED tests/unit/test_hs201_summary_doctor.py::test_doctor_names_assigned_summary_route_and_ignores_legacy_pointer
2 failed in 0.91s
```

Root's captured focused suite: **184 passed in 13.30s**. The glass walk uses
the real isolated hub and public selection route. Its discovery leaf is
stubbed; `ROUTE_EXECUTIONS 0`, `PAGE_ERRORS []`. The settled Trust window
shows `api.openai.com` at 1440 and 393. The 393 badge itself still clips its
label; that face concern is handed to lane B. No owner desk state was used.
No story flips or fresh full-suite claim.
