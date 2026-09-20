# Evidence - HS-201-02

- **Story:** HS-201-02 - Record works with no summary model
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:49:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.LZ4m9Bgdze uv run --extra dev pytest -q tests/unit/test_hs201_record_speech_only.py tests/e2e/test_hs201_record_transcript.py tests/unit/test_meeting_session_admission.py tests/unit/test_speech_side_door_admission.py tests/unit/test_transcriber_init_race.py tests/unit/test_backend_density_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
............................................................             [100%]
60 passed in 8.79s
```

## Lane A acceptance boundary

The ordinary web Record callback requests capture and speech only. Fixture WAV
capture saves a non-empty final transcript and closes the speech parent. Stop
creates neither a summary job nor an auto-title job, including when a text
engine exists and the meeting has no title. Missing speech preserves the
`no_assignment` cause through the Record read model and Retry.

The face token and its shot are lane B story 01 work under the owner's explicit
file split. This evidence closes no face criterion and no owner sitting.
`lane-a-handoff.md` names the fields B must render.

## Red fences before implementation

The worker ran the new tests before the corresponding product edits, with
`HOME=$(mktemp -d) uv run --extra dev pytest -q` and the named tests below.
The four failures cover speech-only admission, saved transcript/parent closure,
no text work on Stop, and wrong-cause Retry. The separate runtime fence catches
the default-config web callback that still enabled intelligence.

### hs201-02-red-all-fences.log

```text
FFFF                                                                     [100%]
=================================== FAILURES ===================================
____________ test_speech_only_recording_admits_without_text_routes _____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8622/test_speech_only_recording_adm0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10ab6df30>

    def test_speech_only_recording_admits_without_text_routes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A speech assignment is sufficient when intelligence is disabled."""
        db, session = _speech_only_session(tmp_path, monkeypatch)
    
        state = session.start()
    
        assert state.capture_status == "recording"
>       assert state.transcription_status == "active"
E       AssertionError: assert 'record_only' == 'active'
E         
E         - active
E         + record_only

tests/unit/test_hs201_record_speech_only.py:161: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    holdspeak.meeting_session:intel_admission.py:211 meeting session admission refused: no_assignment (No model assignment can be frozen.)
____ test_speech_only_stop_saves_transcript_and_closes_parent_without_queue ____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8622/test_speech_only_stop_saves_tr0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1082de2c0>

    def test_speech_only_stop_saves_transcript_and_closes_parent_without_queue(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db, session = _speech_only_session(tmp_path, monkeypatch)
        state = session.start()
    
        stopped = session.stop()
    
        assert stopped.capture_status == "finalized"
>       assert [segment.text for segment in stopped.segments] == ["fixture speech transcript"]
E       AssertionError: assert [] == ['fixture speech transcript']
E         
E         Right contains one more item: 'fixture speech transcript'
E         Use -v to get more diff

tests/unit/test_hs201_record_speech_only.py:179: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    holdspeak.meeting_session:intel_admission.py:211 meeting session admission refused: no_assignment (No model assignment can be frozen.)
WARNING  holdspeak.meeting_session:transcribe_loop.py:79 meeting transcription interval dropped: no_assignment
_____ test_speech_only_ignores_available_text_engine_until_summary_gesture _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8622/test_speech_only_ignores_avail0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10adce7b0>

    def test_speech_only_ignores_available_text_engine_until_summary_gesture(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Available text routes do not become live or Stop work by implication."""
        db, session = _speech_and_text_session(tmp_path, monkeypatch)
        state = session.start()
    
        assert session._route_bundle is not None
>       assert {
            member["capability_id"] for member in session._route_bundle["members"]
        } == {"speech.transcribe", "speech.preload"}
E       AssertionError: assert {'meeting.aut...h.transcribe'} == {'speech.prel...h.transcribe'}
E         
E         Extra items in the left set:
E         'meeting.auto_title'
E         'meeting.bookmark_label'
E         'meeting.live_analysis'
E         Use -v to get more diff

tests/unit/test_hs201_record_speech_only.py:202: AssertionError
____ test_retry_preserves_no_assignment_reason_instead_of_empty_transcript _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8622/test_retry_preserves_no_assign0')

    def test_retry_preserves_no_assignment_reason_instead_of_empty_transcript(
        tmp_path: Path,
    ) -> None:
        db = Database(tmp_path / "hs201-refusal.db")
        meeting = MeetingState(
            id="hs201-no-assignment",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            intel_status="refused",
            intel_status_detail="Meeting intelligence refused: no_assignment. Recording continues.",
            transcription_status="record_only",
            transcription_status_detail={
                "family": "meeting-route-assignments",
                "reason_code": "no_assignment",
                "repair": "repair_meeting_route_assignment",
            },
        )
        db.meetings.save_meeting(meeting)
    
        with pytest.raises(Exception) as refused:
            MeetingIntelService(db).retry_job(OWNER, meeting.id)
    
>       assert getattr(refused.value, "code", None) == "no_assignment"
E       AssertionError: assert 'empty' == 'no_assignment'
E         
E         - no_assignment
E         + empty

tests/unit/test_hs201_record_speech_only.py:234: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_record_speech_only.py::test_speech_only_recording_admits_without_text_routes
FAILED tests/unit/test_hs201_record_speech_only.py::test_speech_only_stop_saves_transcript_and_closes_parent_without_queue
FAILED tests/unit/test_hs201_record_speech_only.py::test_speech_only_ignores_available_text_engine_until_summary_gesture
FAILED tests/unit/test_hs201_record_speech_only.py::test_retry_preserves_no_assignment_reason_instead_of_empty_transcript
4 failed in 0.94s
```

### hs201-02-runtime-red.log

```text
F                                                                        [100%]
=================================== FAILURES ===================================
____ test_web_record_constructs_capture_only_session_before_summary_gesture ____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10ee0a060>

    def test_web_record_constructs_capture_only_session_before_summary_gesture(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The normal Record callback does not opt into live text intelligence."""
        from holdspeak.runtime import meeting_glue
    
        captured: dict[str, Any] = {}
    
        class _State:
            id = "hs201-runtime-meeting"
            title = None
            tags: list[str] = []
            web_url = None
            calendar_event_id = None
            devices: list[Any] = []
    
            def to_dict(self) -> dict[str, Any]:
                return {"id": self.id, "title": self.title, "tags": self.tags}
    
        class _Session:
            def __init__(self, **kwargs: Any) -> None:
                captured.update(kwargs)
                self._state = _State()
    
            @property
            def is_active(self) -> bool:
                return True
    
            @property
            def state(self) -> _State:
                return self._state
    
            def start(self) -> _State:
                return self._state
    
            def attach_device(self, *_args: Any, **_kwargs: Any) -> None:
                return None
    
            def set_title(self, title: str) -> None:
                self._state.title = title
    
            def set_tags(self, tags: list[str]) -> None:
                self._state.tags = tags
    
        class _Floor:
            active_owner = None
    
            def acquire(self, _owner: str) -> bool:
                return True
    
            def release(self, _owner: str) -> None:
                return None
    
        meeting_config = SimpleNamespace(
            intent_segment_probe_enabled=False,
            mic_label="Me",
            remote_label="Remote",
            mic_device=None,
            system_audio_device=None,
            intel_enabled=True,
            intel_realtime_model="",
            intel_provider="local",
            intel_deferred_enabled=True,
            intel_cloud_reasoning_effort=None,
            intel_cloud_store=False,
            diarization_enabled=False,
            diarize_mic=False,
            cross_meeting_recognition=False,
        )
        harness = meeting_glue.MeetingGlueMixin.__new__(meeting_glue.MeetingGlueMixin)
        harness.meeting_lock = threading.Lock()
        harness.meeting_session = None
        harness.transcriber = _FixtureTranscriber()
        harness.config = SimpleNamespace(
            meeting=meeting_config,
            model=SimpleNamespace(backend="auto", name="base"),
        )
        harness.device_registry = SimpleNamespace(get=lambda _id: None)
        harness.voice_session = _Floor()
        harness.runtime_url = None
        harness.state_lock = threading.Lock()
        harness.pending_title = None
        harness.pending_calendar_event_id = None
        harness.pending_tags = None
        harness.pending_intent_windows = []
        harness.pending_plugin_runs = []
        harness.preview_window_seq = 0
        harness.runtime_status = {"last_error": ""}
        harness._ensure_transcriber_loaded = lambda **_kwargs: harness.transcriber
        harness._set_runtime_activity = lambda *_args, **_kwargs: None
        harness._broadcast_intel_status = lambda: None
        harness._apply_updated_config = lambda: None
        harness._on_meeting_segment = lambda *_args, **_kwargs: None
        harness._on_meeting_intel = lambda *_args, **_kwargs: None
        harness._on_meeting_broadcast = lambda *_args, **_kwargs: None
        harness._emit_audio_level = lambda *_args, **_kwargs: None
        monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder)
        monkeypatch.setattr("holdspeak.runtime.meeting_glue.MeetingSession", _Session)
        monkeypatch.setattr(
            "holdspeak.intel.providers.effective_intel_cloud",
            lambda _config: SimpleNamespace(
                reason="", model="", api_key_env="OPENAI_API_KEY", base_url=None
            ),
        )
    
        result = harness._start_meeting(principal=OWNER)
    
        assert result["id"] == "hs201-runtime-meeting"
>       assert captured["intel_enabled"] is False
E       assert True is False

tests/unit/test_hs201_record_speech_only.py:390: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_record_speech_only.py::test_web_record_constructs_capture_only_session_before_summary_gesture
1 failed in 0.33s
```

## Dictation classification — c, not reproduced

The audit's historical transcriber-race failure did not reproduce. This lane
changes neither the dictation implementation nor its race tests. Astra ran all
three tests twice against the pre-fix charter snapshot `fdc3fc45`, with the
baseline source path printed in the same Python process that invoked pytest.
Both runs passed. Current focused runs also pass. Classification **c** means
historical/environmental or test-run context remains unknown; it is not a claim
that a particular historical cause was diagnosed.

Baseline command (from `.tmp/hs201-baseline`): isolated HOME, explicit baseline
PYTHONPATH, shared dev venv through `UV_PROJECT_ENVIRONMENT`, `uv run --no-sync
python` importing the baseline module then `pytest.main(["-q",
"tests/unit/test_transcriber_init_race.py"])`.

```text
BASELINE SOURCE: /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/__init__.py
...                                                                      [100%]
3 passed in 1.66s
```

```text
BASELINE SOURCE: /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/__init__.py
...                                                                      [100%]
3 passed in 1.61s
```

### Captured run — 2026-09-19T23:06:58Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.VjBgJBeLfx uv run --extra dev pytest -q tests/unit/test_hs201_record_speech_only.py tests/e2e/test_hs201_record_transcript.py tests/unit/test_meeting_session_admission.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_speech_side_door_admission.py tests/unit/test_transcriber_init_race.py tests/unit/test_backend_density_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 24.79s
```

## Stop queue fence isolated by Astra

The admission assertion was moved after Stop so the baseline run proves the
queue fence itself fails: a text job exists before any summary gesture. The
fixture meeting is untitled and all text routes are assigned. Command: isolated
HOME and explicit baseline PYTHONPATH, `uv run --no-sync python` invoking
pytest on the single node shown below against charter `fdc3fc45`.

```text
BASELINE SOURCE: /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/meeting_session/intel_admission.py
F                                                                        [100%]
=================================== FAILURES ===================================
_____ test_speech_only_ignores_available_text_engine_until_summary_gesture _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8766/test_speech_only_ignores_avail0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10cab1220>

    def test_speech_only_ignores_available_text_engine_until_summary_gesture(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Available text routes do not become live or Stop work by implication."""
        db, session = _speech_and_text_session(tmp_path, monkeypatch)
        state = session.start()
    
        stopped = session.stop()
>       assert db.intel.get_intel_job(stopped.id) is None
E       AssertionError: assert IntelJob(meeting_id='8d84fa10', status='queued', transcript_hash='468d999e403017dc6ea2bd8bc6c0735c98b8629d5d522bcf7343...56=None, executor_lease_token=None, executor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued') is None
E        +  where IntelJob(meeting_id='8d84fa10', status='queued', transcript_hash='468d999e403017dc6ea2bd8bc6c0735c98b8629d5d522bcf7343...56=None, executor_lease_token=None, executor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued') = get_intel_job('8d84fa10')
E        +    where get_intel_job = <holdspeak.db.intel.IntelRepository object at 0x10cb57cb0>.get_intel_job
E        +      where <holdspeak.db.intel.IntelRepository object at 0x10cb57cb0> = <holdspeak.db.core.Database object at 0x10cb57620>.intel
E        +    and   '8d84fa10' = MeetingState(id='8d84fa10', started_at=datetime.datetime(2026, 9, 19, 17, 11, 36, 503223), ended_at=datetime.datetime(..., capture_checkpoint_seconds=0.064445, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]).id

tests/unit/test_hs201_record_speech_only.py:247: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_record_speech_only.py::test_speech_only_ignores_available_text_engine_until_summary_gesture
1 failed in 0.49s
```

## Actual Web Stop hook — red before the seam fix

The session Stop fence did not cover `MeetingRuntimeMixin._stop_active_meeting`.
Its post-save legacy hook still enqueued work for both automatic settings.
Astra drove the real hook with a saved isolated meeting and Room link. No
provider or owner state was used.

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_______ test_web_stop_never_auto_enqueues_before_summary_gesture[every] ________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8788/test_web_stop_never_auto_enque0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10f448b00>
mode = 'every'

    @pytest.mark.parametrize('mode', ['every', 'room_linked'])
    def test_web_stop_never_auto_enqueues_before_summary_gesture(tmp_path, monkeypatch, mode):
        db = Database(tmp_path / 'stop-hook.db')
        state = MeetingState(
            id='stop-hook', title='', started_at=datetime.now(), ended_at=datetime.now(),
            capture_status='finalized', segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
        )
        db.meetings.save_meeting(state)
        _seed_project(db, 'room-fixture')
        _link_meeting_project(db, state.id, 'room-fixture')
        cfg = Config()
        cfg.meeting.intelligence_auto = mode
        monkeypatch.setattr(Config, 'load', lambda: cfg)
        monkeypatch.setattr('holdspeak.db.get_database', lambda: db)
    
        class Runtime(MeetingGlueMixin, RoutingGlueMixin):
            pass
    
        runtime = Runtime()
        runtime.state_lock = Lock()
        runtime.meeting_lock = Lock()
        runtime.runtime_status = {}
        runtime.recording_ticker = Mock()
        runtime.device_stats_cycle = {}
        runtime.voice_session = Mock()
        runtime._set_runtime_activity = Mock()
        runtime._flush_deferred_plugin_runs_to_db = lambda: {}
        runtime._persist_pending_mir_history = lambda _: {}
        runtime._synthesize_and_persist_artifacts = lambda _: {}
        runtime._associate_meeting_with_projects = lambda _: {'projects_associated': 1}
        runtime.meeting_session = SimpleNamespace(
            is_active=True, state=state, stop=lambda: state,
            save=lambda: SimpleNamespace(database_saved=True, json_saved=False, json_path=None, intel_job_enqueued=False),
        )
        result = runtime._stop_active_meeting(allow_runtime_fallback=False)
        assert result['save_error'] is None
        assert result['save']['database_saved'] is True
>       assert db.intel.get_intel_job(state.id) is None
E       AssertionError: assert IntelJob(meeting_id='stop-hook', status='queued', transcript_hash='8a9a2c96244727912984e907c71696454f11734f060e1965ffc...ecutor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued', planned_route=None, run_receipt=None) is None
E        +  where IntelJob(meeting_id='stop-hook', status='queued', transcript_hash='8a9a2c96244727912984e907c71696454f11734f060e1965ffc...ecutor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued', planned_route=None, run_receipt=None) = get_intel_job('stop-hook')
E        +    where get_intel_job = <holdspeak.db.intel.IntelRepository object at 0x10f3cbb60>.get_intel_job
E        +      where <holdspeak.db.intel.IntelRepository object at 0x10f3cbb60> = <holdspeak.db.core.Database object at 0x10f3cb380>.intel
E        +    and   'stop-hook' = MeetingState(id='stop-hook', started_at=datetime.datetime(2026, 9, 19, 17, 25, 23, 221771), ended_at=datetime.datetime...=None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]).id

tests/unit/test_hs201_record_stop_hook.py:54: AssertionError
____ test_web_stop_never_auto_enqueues_before_summary_gesture[room_linked] _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8788/test_web_stop_never_auto_enque1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10f44ad70>
mode = 'room_linked'

    @pytest.mark.parametrize('mode', ['every', 'room_linked'])
    def test_web_stop_never_auto_enqueues_before_summary_gesture(tmp_path, monkeypatch, mode):
        db = Database(tmp_path / 'stop-hook.db')
        state = MeetingState(
            id='stop-hook', title='', started_at=datetime.now(), ended_at=datetime.now(),
            capture_status='finalized', segments=[TranscriptSegment('Send the report.', 'Me', 0.0, 1.0)],
        )
        db.meetings.save_meeting(state)
        _seed_project(db, 'room-fixture')
        _link_meeting_project(db, state.id, 'room-fixture')
        cfg = Config()
        cfg.meeting.intelligence_auto = mode
        monkeypatch.setattr(Config, 'load', lambda: cfg)
        monkeypatch.setattr('holdspeak.db.get_database', lambda: db)
    
        class Runtime(MeetingGlueMixin, RoutingGlueMixin):
            pass
    
        runtime = Runtime()
        runtime.state_lock = Lock()
        runtime.meeting_lock = Lock()
        runtime.runtime_status = {}
        runtime.recording_ticker = Mock()
        runtime.device_stats_cycle = {}
        runtime.voice_session = Mock()
        runtime._set_runtime_activity = Mock()
        runtime._flush_deferred_plugin_runs_to_db = lambda: {}
        runtime._persist_pending_mir_history = lambda _: {}
        runtime._synthesize_and_persist_artifacts = lambda _: {}
        runtime._associate_meeting_with_projects = lambda _: {'projects_associated': 1}
        runtime.meeting_session = SimpleNamespace(
            is_active=True, state=state, stop=lambda: state,
            save=lambda: SimpleNamespace(database_saved=True, json_saved=False, json_path=None, intel_job_enqueued=False),
        )
        result = runtime._stop_active_meeting(allow_runtime_fallback=False)
        assert result['save_error'] is None
        assert result['save']['database_saved'] is True
>       assert db.intel.get_intel_job(state.id) is None
E       AssertionError: assert IntelJob(meeting_id='stop-hook', status='queued', transcript_hash='8a9a2c96244727912984e907c71696454f11734f060e1965ffc...ecutor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued', planned_route=None, run_receipt=None) is None
E        +  where IntelJob(meeting_id='stop-hook', status='queued', transcript_hash='8a9a2c96244727912984e907c71696454f11734f060e1965ffc...ecutor_lease_epoch=0, executor_lease_expires_at=None, lifecycle_posture='queued', planned_route=None, run_receipt=None) = get_intel_job('stop-hook')
E        +    where get_intel_job = <holdspeak.db.intel.IntelRepository object at 0x10f3b7610>.get_intel_job
E        +      where <holdspeak.db.intel.IntelRepository object at 0x10f3b7610> = <holdspeak.db.core.Database object at 0x10f3b6990>.intel
E        +    and   'stop-hook' = MeetingState(id='stop-hook', started_at=datetime.datetime(2026, 9, 19, 17, 25, 23, 810589), ended_at=datetime.datetime...=None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]).id

tests/unit/test_hs201_record_stop_hook.py:54: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[every]
FAILED tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[room_linked]
2 failed in 2.21s

```

The fix parks that hook outside ordinary Web Stop. The focused verification:

```text
...........................................                              [100%]
43 passed in 21.89s

```

### Captured run — 2026-09-19T23:44:43Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.cHTMx3qz4d uv run --extra dev pytest -q tests/unit/test_hs201_record_speech_only.py tests/unit/test_hs201_record_stop_hook.py tests/e2e/test_hs201_record_transcript.py tests/unit/test_meeting_session_admission.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_speech_side_door_admission.py tests/unit/test_transcriber_init_race.py tests/unit/test_backend_density_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 808c441bab59d51a4c9ec296f26e9280f25c077d

```text
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 30.92s
```

## Astra collection proof for the staged focused run

```text
tests/unit/test_hs201_record_speech_only.py::test_speech_only_recording_admits_without_text_routes
tests/unit/test_hs201_record_speech_only.py::test_no_speech_assignment_records_named_refusal_immediately
tests/unit/test_hs201_record_speech_only.py::test_speech_only_stop_saves_transcript_and_closes_parent_without_queue
tests/unit/test_hs201_record_speech_only.py::test_speech_only_ignores_available_text_engine_until_summary_gesture
tests/unit/test_hs201_record_speech_only.py::test_retry_preserves_no_assignment_reason_instead_of_empty_transcript
tests/unit/test_hs201_record_speech_only.py::test_web_record_constructs_capture_only_session_before_summary_gesture
tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[every]
tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[room_linked]
tests/e2e/test_hs201_record_transcript.py::test_record_fixture_wav_saves_nonempty_transcript_without_summary_model
tests/unit/test_meeting_session_admission.py::test_start_admits_complete_live_bundle_with_exact_aggregate_budget[requested0-17286-21383]
tests/unit/test_meeting_session_admission.py::test_start_admits_complete_live_bundle_with_exact_aggregate_budget[requested1-34570-38667]
tests/unit/test_meeting_session_admission.py::test_unicode_registered_device_freezes_as_evidence_and_rejects_undeclared_source
tests/unit/test_meeting_session_admission.py::test_route_refusal_keeps_raw_capture_in_durable_record_only
tests/unit/test_meeting_session_admission.py::test_recorder_start_failure_fences_committed_bundle
tests/unit/test_meeting_session_admission.py::test_late_transcriber_construction_failure_keeps_raw_capture_record_only
tests/unit/test_meeting_session_admission.py::test_factoryless_transcription_records_honest_record_only_status
tests/unit/test_meeting_session_admission.py::test_live_bundle_journal_never_contains_transcript_material
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
tests/unit/test_speech_side_door_admission.py::test_text_entry_is_fresh_bounded_and_never_plans_mic_capabilities
tests/unit/test_speech_side_door_admission.py::test_browser_egress_disclosure_and_execution_proof_share_the_resolver
tests/unit/test_speech_side_door_admission.py::test_entry_admission_refuses_missing_cross_session_and_ended_handles_before_build
tests/unit/test_speech_side_door_admission.py::test_provider_pre_fence_preserves_the_exact_revocation_reason
tests/unit/test_speech_side_door_admission.py::test_post_claim_kernel_refusal_returns_through_the_safe_named_channel
tests/unit/test_speech_side_door_admission.py::test_shared_helper_refuses_before_the_runtime_factory_can_be_reached
tests/unit/test_speech_side_door_admission.py::test_open_text_entry_uses_only_the_middleware_principal_and_one_snapshot
tests/unit/test_speech_side_door_admission.py::test_session_fence_is_built_once_before_the_session_is_published
tests/unit/test_speech_side_door_admission.py::test_browser_lexical_preview_mints_no_speech_parent
tests/unit/test_speech_side_door_admission.py::test_disconnect_watcher_cancels_preview_and_late_publication_loses
tests/unit/test_speech_side_door_admission.py::test_publication_fence_has_one_winner_in_both_cancellation_orderings
tests/unit/test_speech_side_door_admission.py::test_durable_publication_claim_blocks_direct_cross_process_mutations
tests/unit/test_speech_side_door_admission.py::test_failed_publication_release_recovers_in_the_live_process
tests/unit/test_speech_side_door_admission.py::test_expiry_reaper_defers_across_a_live_publication_claim
tests/unit/test_speech_side_door_admission.py::test_warrant_revocation_waits_for_durable_publication_release
tests/unit/test_speech_side_door_admission.py::test_durable_publication_claim_serializes_controller_cancellation
tests/unit/test_speech_side_door_admission.py::test_final_preview_publication_settles_success_before_disconnect_can_cancel
tests/unit/test_speech_side_door_admission.py::test_cli_derives_the_provided_bearer_against_the_hub_credential_only
tests/unit/test_speech_side_door_admission.py::test_top_level_cli_threads_one_snapshot_through_auth_and_execution
tests/unit/test_speech_side_door_admission.py::test_frozen_endpoint_construction_ignores_mutated_runtime_placement
tests/unit/test_speech_side_door_admission.py::test_keyless_frozen_endpoint_does_not_reintroduce_a_profile_secret_slot
tests/unit/test_speech_side_door_admission.py::test_local_construction_freezes_the_dictation_artifact_not_mutated_config
tests/unit/test_speech_side_door_admission.py::test_concrete_local_revision_rejects_a_different_loader_on_the_same_path
tests/unit/test_speech_side_door_admission.py::test_generic_local_profile_binds_an_existing_dotted_mlx_directory
tests/unit/test_speech_side_door_admission.py::test_local_identity_preserves_a_dotted_mlx_artifact_name
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[apple-mlx]
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[apple-import-failure-falls-back]
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[llama-fallback]
tests/unit/test_speech_side_door_admission.py::test_provider_capability_map_plans_target_detection_as_rewrite_and_no_whisper
tests/unit/test_speech_side_door_admission.py::test_fatal_speech_signals_escape_but_ordinary_stage_failures_are_degraded
tests/unit/test_speech_side_door_admission.py::test_model_target_detector_preserves_provider_failure_reason
tests/unit/test_speech_side_door_admission.py::test_cancel_after_text_processing_prevents_the_voice_command_effect
tests/unit/test_speech_side_door_admission.py::test_cancel_before_live_publication_suppresses_preview_typing_and_callback[preview]
tests/unit/test_speech_side_door_admission.py::test_cancel_before_live_publication_suppresses_preview_typing_and_callback[desktop-typing]
tests/unit/test_speech_side_door_admission.py::test_entry_exposes_indeterminate_terminal_state_instead_of_a_success_string
tests/unit/test_transcriber_init_race.py::test_concurrent_ensure_builds_exactly_one_transcriber
tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation
tests/unit/test_transcriber_init_race.py::test_every_mlx_transcriber_shares_one_pinned_thread
tests/unit/test_backend_density_guard.py::test_web_runtime_core_stays_boot_only
tests/unit/test_backend_density_guard.py::test_meeting_session_core_stays_lifecycle_only
tests/unit/test_backend_density_guard.py::test_runtime_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_meeting_session_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_guard_would_catch_a_regrown_module
tests/unit/test_backend_density_guard.py::test_phase79_package_inits_stay_composition_only
tests/unit/test_backend_density_guard.py::test_phase79_package_modules_stay_single_concern

106 tests collected in 1.28s

```


## Capture provenance clarification

The runs executed the combined lane worktree, not an isolated index snapshot.
The early captures stamped `387bab5d` are superseded for index provenance;
their raw output and original stamps are retained. No capture stamp was edited.
The quiet full suite used product/test index tree
`18f67176b9146ddd441b13c60b70687674c1230f`. Follow-up test-contract updates
and their focused verification are recorded below; no full-suite green is claimed.

### Captured run — 2026-09-20T00:38:36Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs201-pytest-vsfphvs8 PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --extra dev pytest -q tests/unit/test_hs201_record_speech_only.py tests/unit/test_hs201_record_stop_hook.py tests/e2e/test_hs201_record_transcript.py tests/unit/test_meeting_session_admission.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_speech_side_door_admission.py tests/unit/test_transcriber_init_race.py tests/unit/test_backend_density_guard.py tests/unit/test_dictation_session_admission.py tests/unit/test_phase143_meeting_live_cutover.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15a395aa43a2175568bb3ae20fa342a0202af45c

```text
........................................................................ [ 36%]
.......................................s........ss...ss................. [ 73%]
.........s......sssss...............................                     [100%]
=========================== short test summary info ============================
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
185 passed, 11 skipped in 50.55s
```


## Final focused collection — Astra

All product and test source was staged for the final captures above. The tests
ran against the combined lane worktree. The post-full changes update old
contract expectations and tighten the proposal xfail boundary; product code
is unchanged from the full-suite snapshot.

```text
tests/unit/test_hs201_record_speech_only.py::test_speech_only_recording_admits_without_text_routes
tests/unit/test_hs201_record_speech_only.py::test_no_speech_assignment_records_named_refusal_immediately
tests/unit/test_hs201_record_speech_only.py::test_speech_only_stop_saves_transcript_and_closes_parent_without_queue
tests/unit/test_hs201_record_speech_only.py::test_speech_only_ignores_available_text_engine_until_summary_gesture
tests/unit/test_hs201_record_speech_only.py::test_retry_preserves_no_assignment_reason_instead_of_empty_transcript
tests/unit/test_hs201_record_speech_only.py::test_web_record_constructs_capture_only_session_before_summary_gesture
tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[every]
tests/unit/test_hs201_record_stop_hook.py::test_web_stop_never_auto_enqueues_before_summary_gesture[room_linked]
tests/e2e/test_hs201_record_transcript.py::test_record_fixture_wav_saves_nonempty_transcript_without_summary_model
tests/unit/test_meeting_session_admission.py::test_start_admits_complete_live_bundle_with_exact_aggregate_budget[requested0-17286-21383]
tests/unit/test_meeting_session_admission.py::test_start_admits_complete_live_bundle_with_exact_aggregate_budget[requested1-34570-38667]
tests/unit/test_meeting_session_admission.py::test_unicode_registered_device_freezes_as_evidence_and_rejects_undeclared_source
tests/unit/test_meeting_session_admission.py::test_route_refusal_keeps_raw_capture_in_durable_record_only
tests/unit/test_meeting_session_admission.py::test_recorder_start_failure_fences_committed_bundle
tests/unit/test_meeting_session_admission.py::test_late_transcriber_construction_failure_keeps_raw_capture_record_only
tests/unit/test_meeting_session_admission.py::test_factoryless_transcription_records_honest_record_only_status
tests/unit/test_meeting_session_admission.py::test_live_bundle_journal_never_contains_transcript_material
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
tests/unit/test_speech_side_door_admission.py::test_text_entry_is_fresh_bounded_and_never_plans_mic_capabilities
tests/unit/test_speech_side_door_admission.py::test_browser_egress_disclosure_and_execution_proof_share_the_resolver
tests/unit/test_speech_side_door_admission.py::test_entry_admission_refuses_missing_cross_session_and_ended_handles_before_build
tests/unit/test_speech_side_door_admission.py::test_provider_pre_fence_preserves_the_exact_revocation_reason
tests/unit/test_speech_side_door_admission.py::test_post_claim_kernel_refusal_returns_through_the_safe_named_channel
tests/unit/test_speech_side_door_admission.py::test_shared_helper_refuses_before_the_runtime_factory_can_be_reached
tests/unit/test_speech_side_door_admission.py::test_open_text_entry_uses_only_the_middleware_principal_and_one_snapshot
tests/unit/test_speech_side_door_admission.py::test_session_fence_is_built_once_before_the_session_is_published
tests/unit/test_speech_side_door_admission.py::test_browser_lexical_preview_mints_no_speech_parent
tests/unit/test_speech_side_door_admission.py::test_disconnect_watcher_cancels_preview_and_late_publication_loses
tests/unit/test_speech_side_door_admission.py::test_publication_fence_has_one_winner_in_both_cancellation_orderings
tests/unit/test_speech_side_door_admission.py::test_durable_publication_claim_blocks_direct_cross_process_mutations
tests/unit/test_speech_side_door_admission.py::test_failed_publication_release_recovers_in_the_live_process
tests/unit/test_speech_side_door_admission.py::test_expiry_reaper_defers_across_a_live_publication_claim
tests/unit/test_speech_side_door_admission.py::test_warrant_revocation_waits_for_durable_publication_release
tests/unit/test_speech_side_door_admission.py::test_durable_publication_claim_serializes_controller_cancellation
tests/unit/test_speech_side_door_admission.py::test_final_preview_publication_settles_success_before_disconnect_can_cancel
tests/unit/test_speech_side_door_admission.py::test_cli_derives_the_provided_bearer_against_the_hub_credential_only
tests/unit/test_speech_side_door_admission.py::test_top_level_cli_threads_one_snapshot_through_auth_and_execution
tests/unit/test_speech_side_door_admission.py::test_frozen_endpoint_construction_ignores_mutated_runtime_placement
tests/unit/test_speech_side_door_admission.py::test_keyless_frozen_endpoint_does_not_reintroduce_a_profile_secret_slot
tests/unit/test_speech_side_door_admission.py::test_local_construction_freezes_the_dictation_artifact_not_mutated_config
tests/unit/test_speech_side_door_admission.py::test_concrete_local_revision_rejects_a_different_loader_on_the_same_path
tests/unit/test_speech_side_door_admission.py::test_generic_local_profile_binds_an_existing_dotted_mlx_directory
tests/unit/test_speech_side_door_admission.py::test_local_identity_preserves_a_dotted_mlx_artifact_name
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[apple-mlx]
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[apple-import-failure-falls-back]
tests/unit/test_speech_side_door_admission.py::test_auto_local_identity_freezes_one_deterministic_engine_and_artifact[llama-fallback]
tests/unit/test_speech_side_door_admission.py::test_provider_capability_map_plans_target_detection_as_rewrite_and_no_whisper
tests/unit/test_speech_side_door_admission.py::test_fatal_speech_signals_escape_but_ordinary_stage_failures_are_degraded
tests/unit/test_speech_side_door_admission.py::test_model_target_detector_preserves_provider_failure_reason
tests/unit/test_speech_side_door_admission.py::test_cancel_after_text_processing_prevents_the_voice_command_effect
tests/unit/test_speech_side_door_admission.py::test_cancel_before_live_publication_suppresses_preview_typing_and_callback[preview]
tests/unit/test_speech_side_door_admission.py::test_cancel_before_live_publication_suppresses_preview_typing_and_callback[desktop-typing]
tests/unit/test_speech_side_door_admission.py::test_entry_exposes_indeterminate_terminal_state_instead_of_a_success_string
tests/unit/test_transcriber_init_race.py::test_concurrent_ensure_builds_exactly_one_transcriber
tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation
tests/unit/test_transcriber_init_race.py::test_every_mlx_transcriber_shares_one_pinned_thread
tests/unit/test_backend_density_guard.py::test_web_runtime_core_stays_boot_only
tests/unit/test_backend_density_guard.py::test_meeting_session_core_stays_lifecycle_only
tests/unit/test_backend_density_guard.py::test_runtime_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_meeting_session_modules_stay_single_concern
tests/unit/test_backend_density_guard.py::test_guard_would_catch_a_regrown_module
tests/unit/test_backend_density_guard.py::test_phase79_package_inits_stay_composition_only
tests/unit/test_backend_density_guard.py::test_phase79_package_modules_stay_single_concern
tests/unit/test_dictation_session_admission.py::test_hold_press_admits_exactly_one_dictation_session
tests/unit/test_dictation_session_admission.py::test_hold_release_seals_the_deadline_to_release_plus_drain
tests/unit/test_dictation_session_admission.py::test_release_before_admission_completes_cancels_the_parent
tests/unit/test_dictation_session_admission.py::test_refused_press_tears_the_capture_down
tests/unit/test_dictation_session_admission.py::test_wake_capture_admits_one_bounded_wake_session
tests/unit/test_dictation_session_admission.py::test_phase_d_default_cold_wake_runs_its_complete_routed_bundle
tests/unit/test_dictation_session_admission.py::test_phase_d_faster_whisper_constructs_after_frozen_local_route_then_transcribes
tests/unit/test_dictation_session_admission.py::test_phase_d_faster_whisper_deferred_warm_settles_before_first_speak_to_fill
tests/unit/test_dictation_session_admission.py::test_disabled_wake_configuration_admits_nothing
tests/unit/test_dictation_session_admission.py::test_wake_authority_revision_tracks_the_configured_fields
tests/unit/test_dictation_session_admission.py::test_phase_d_wake_revision_is_parent_evidence_not_principal_schema_drift
tests/unit/test_dictation_session_admission.py::test_transcribe_runs_one_child_naming_the_frozen_revision
tests/unit/test_dictation_session_admission.py::test_empty_audio_creates_no_child
tests/unit/test_dictation_session_admission.py::test_transcribe_without_a_live_context_refuses_before_the_backend
tests/unit/test_dictation_session_admission.py::test_phase_d_day_one_standalone_speak_to_fill_uses_the_migrated_route
tests/unit/test_dictation_session_admission.py::test_phase_d_couples_speech_and_writing_markers_for_one_complete_pipeline
tests/unit/test_dictation_session_admission.py::test_explicit_get_model_is_one_preload_sibling_before_the_transcribe_child
tests/unit/test_dictation_session_admission.py::test_failed_get_model_then_silent_fallback_are_two_preload_children
tests/unit/test_dictation_session_admission.py::test_every_preload_candidate_failing_refuses_without_transcribing
tests/unit/test_dictation_session_admission.py::test_pre_session_warm_uses_the_assigned_speech_route_not_the_legacy_knob
tests/unit/test_dictation_session_admission.py::test_authorized_pre_session_warm_runs_as_the_preload_service
tests/unit/test_dictation_session_admission.py::test_no_audio_or_transcript_reaches_any_kernel_row
tests/unit/test_dictation_session_admission.py::test_meeting_transcription_children_join_the_existing_meeting_session
tests/unit/test_dictation_session_admission.py::test_meeting_interval_without_a_live_parent_drops_before_whisper
tests/unit/test_dictation_session_admission.py::test_the_plan_freezes_ordered_per_capability_revisions
tests/unit/test_dictation_session_admission.py::test_paired_device_capture_admits_its_own_narrow_session
tests/unit/test_dictation_session_admission.py::test_browser_open_admits_one_parent_for_every_utterance
tests/unit/test_dictation_session_admission.py::test_phase_d_browser_interval_keeps_its_full_capture_budget
tests/unit/test_dictation_session_admission.py::test_a_client_supplied_parent_id_is_refused
tests/unit/test_dictation_session_admission.py::test_the_inactivity_lease_refreshes_only_inside_a_real_whisper_claim
tests/unit/test_dictation_session_admission.py::test_a_lapsed_lease_forces_the_interval_closed_by_name
tests/unit/test_dictation_session_admission.py::test_closing_the_interval_cancels_and_closes_the_parent
tests/unit/test_dictation_session_admission.py::test_speak_to_fill_joins_an_interval_and_stands_alone_outside_one
tests/unit/test_dictation_session_admission.py::test_a_cancelled_hold_discards_text_before_preview_and_delivery
tests/unit/test_dictation_session_admission.py::test_a_stop_during_the_browser_open_cancels_the_admitted_parent
tests/unit/test_dictation_session_admission.py::test_a_claim_after_the_lease_lapsed_refuses_and_never_dispatches
tests/unit/test_dictation_session_admission.py::test_a_provider_returning_after_the_seal_publishes_nothing
tests/unit/test_dictation_session_admission.py::test_a_revoked_warrant_fences_the_session_through_the_durable_read
tests/unit/test_dictation_session_admission.py::test_the_one_shot_pipeline_runs_as_children_of_its_own_parent
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_threads_the_live_admission
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_closes_the_parent_failed_when_the_pipeline_raises
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_never_turns_a_fatal_signal_into_raw_success[session-refusal]
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_never_turns_a_fatal_signal_into_raw_success[provider-failure]
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_reports_an_indeterminate_parent_close[success]
tests/unit/test_dictation_session_admission.py::test_the_http_pipeline_route_reports_an_indeterminate_parent_close[refusal]
tests/unit/test_dictation_session_admission.py::test_the_ws_final_pass_runs_under_the_intervals_admission
tests/unit/test_dictation_session_admission.py::test_the_ws_final_pass_sends_an_error_not_raw_text_for_a_fatal_signal
tests/unit/test_dictation_session_admission.py::test_mutable_preload_knobs_cannot_change_the_frozen_parentless_source
tests/unit/test_dictation_session_admission.py::test_stopping_the_wake_listener_cancels_the_in_flight_capture
tests/unit/test_dictation_session_admission.py::test_a_hold_whose_tail_raised_closes_the_parent_failed
tests/unit/test_dictation_session_admission.py::test_the_kick_off_thread_closes_the_parent_with_the_tails_outcome
tests/unit/test_dictation_session_admission.py::test_a_wake_session_whose_pipeline_raised_closes_failed
tests/unit/test_dictation_session_admission.py::test_the_pipeline_route_admits_no_legacy_browser_pipeline_operation
tests/unit/test_dictation_session_admission.py::test_the_egress_label_follows_the_frozen_revision_off_this_machine
tests/unit/test_dictation_session_admission.py::test_phase_f_routed_text_entry_uses_provider_route_egress_without_transcription
tests/unit/test_dictation_session_admission.py::test_phase_d_local_transcription_route_reports_local_egress
tests/unit/test_dictation_session_admission.py::test_phase_d_nonlocal_historical_speech_refuses_before_construction_or_dispatch[mesh]
tests/unit/test_dictation_session_admission.py::test_phase_d_nonlocal_historical_speech_refuses_before_construction_or_dispatch[private_network]
tests/unit/test_dictation_session_admission.py::test_phase_d_egress_refuses_a_missing_frozen_transcription_entry
tests/unit/test_dictation_session_admission.py::test_a_classify_only_pipeline_reports_the_classify_revisions_boundary
tests/unit/test_dictation_session_admission.py::test_a_stop_between_wake_admission_and_registration_cancels_the_parent
tests/unit/test_phase143_meeting_live_cutover.py::test_meeting_assignment_migration_copies_exact_saved_profile_and_replays
tests/unit/test_phase143_meeting_live_cutover.py::test_deferred_meeting_migration_is_narrow_marker_driven_and_replays
tests/unit/test_phase143_meeting_live_cutover.py::test_deferred_meeting_migration_refuses_blank_saved_profile_without_marker
tests/unit/test_phase143_meeting_live_cutover.py::test_blank_or_cloud_legacy_meeting_values_never_guess_an_assignment
tests/unit/test_phase143_meeting_live_cutover.py::test_speech_recognition_without_a_saved_profile_refuses_without_preload_assignment
tests/unit/test_phase143_meeting_live_cutover.py::test_builtin_local_whisper_migration_creates_one_visible_bound_profile_and_replays
tests/unit/test_phase143_meeting_live_cutover.py::test_migrated_local_whisper_bootstraps_ready_and_transcribes_first_meeting[auto]
tests/unit/test_phase143_meeting_live_cutover.py::test_migrated_local_whisper_bootstraps_ready_and_transcribes_first_meeting[mlx]
tests/unit/test_phase143_meeting_live_cutover.py::test_mlx_candidate_walk_runs_inside_one_meeting_preload_sequence
tests/unit/test_phase143_meeting_live_cutover.py::test_migrated_mlx_preload_failure_keeps_raw_capture_durably_record_only
tests/unit/test_phase143_meeting_live_cutover.py::test_meeting_transcription_routes_actual_canonical_bytes_and_exact_result
tests/unit/test_phase143_meeting_live_cutover.py::test_deferred_faster_whisper_constructor_is_one_derived_preload_child
tests/unit/test_phase143_meeting_live_cutover.py::test_meeting_transcription_refuses_a_device_absent_from_the_frozen_set
tests/unit/test_phase143_meeting_live_cutover.py::test_meeting_transcription_timeout_is_unknown_and_never_starts_a_second_model
tests/unit/test_phase143_meeting_live_cutover.py::test_live_bundle_routes_analysis_label_and_title_after_receipt_election
tests/unit/test_phase143_meeting_live_cutover.py::test_replaying_identical_live_material_reuses_the_elected_execution
tests/unit/test_phase143_meeting_live_cutover.py::test_assignment_edit_after_meeting_bundle_freeze_does_not_retarget_route
tests/unit/test_phase143_meeting_live_cutover.py::test_live_analysis_controller_owns_compatibility_retry_then_fallback
tests/unit/test_phase143_meeting_live_cutover.py::test_meeting_kernel_refusal_is_terminal_without_retry_or_fallback
tests/unit/test_phase143_meeting_live_cutover.py::test_stop_fences_every_bundle_member_refuses_reservation_and_survives_restart
tests/unit/test_phase143_meeting_live_cutover.py::test_stop_discards_a_late_routed_live_result_and_signals_its_child
tests/unit/test_phase143_meeting_live_cutover.py::test_stop_aftercare_upserts_one_legacy_deferred_row_for_bundle_and_record_only[True]
tests/unit/test_phase143_meeting_live_cutover.py::test_stop_aftercare_upserts_one_legacy_deferred_row_for_bundle_and_record_only[False]
tests/unit/test_phase143_meeting_live_cutover.py::test_stop_aftercare_predicate_does_not_enqueue_empty_meeting
tests/unit/test_phase143_meeting_live_cutover.py::test_frozen_speech_deployment_replaces_mutable_large_instance_before_execution
tests/unit/test_phase143_meeting_live_cutover.py::test_removed_locator_free_speech_revision_requires_migration_provenance
tests/unit/test_phase143_meeting_live_cutover.py::test_mlx_preload_sequence_stops_before_a_second_physical_call_after_cancellation
tests/unit/test_phase143_meeting_live_cutover.py::test_unavailable_frozen_live_member_stays_queued_not_live
tests/unit/test_phase143_meeting_live_cutover.py::test_persisted_v1_plan_is_displayable_history_without_a_resume_route

196 tests collected in 0.83s
```
