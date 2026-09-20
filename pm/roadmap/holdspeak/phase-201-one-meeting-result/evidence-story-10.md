# Evidence - HS-201-10

- **Story:** HS-201-10 - Import does not run the summary by itself
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-20T05:48:45Z

- **Command:** `uv run pytest -q tests/unit/test_hs201_import_no_auto_summary.py -p no:randomly`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
FFFF..                                                                   [100%]
=================================== FAILURES ===================================
_____ test_audio_import_with_intel_on_enqueues_nothing_and_contacts_nobody _____

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9139/test_audio_import_with_intel_o0')
db = <holdspeak.db.core.Database object at 0x10b0b0050>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10b002520>

    def test_audio_import_with_intel_on_enqueues_nothing_and_contacts_nobody(
        tmp_path, db, monkeypatch
    ):
        """The fence: intelligence ON, a real transcript, and still no run."""
        wav = _aged(tmp_path / "standup.wav", FIXTURE_WAV, days=108)
        probe = ProviderProbe()
    
        result = import_meeting(
            wav,
            db=db,
            transcriber=FakeTranscriber(["the quick brown fox jumps over the lazy dog"]),
            config=_config(),
        )
    
        # Nothing queued: the queue is empty and has nothing to hand a provider.
>       assert result.intel_job_enqueued is False
E       AssertionError: assert True is False
E        +  where True = ImportResult(state=MeetingState(id='6ee48a05', started_at=datetime.datetime(2026, 6, 3, 23, 48, 47, 306161), ended_at=... intel_job_enqueued=True, windows_total=1, windows_empty=0, duration_seconds=2.7946875, warnings=[], speakers_found=[]).intel_job_enqueued

tests/unit/test_hs201_import_no_auto_summary.py:129: AssertionError
____________ test_transcript_import_with_intel_on_enqueues_nothing _____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9139/test_transcript_import_with_in0')
db = <holdspeak.db.core.Database object at 0x10b343390>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10b35b100>

    def test_transcript_import_with_intel_on_enqueues_nothing(tmp_path, db, monkeypatch):
        path = tmp_path / "weekly sync.vtt"
        path.write_text(VTT)
        probe = ProviderProbe()
    
        result = import_transcript(path, db=db, config=_config())
    
>       assert result.intel_job_enqueued is False
E       AssertionError: assert True is False
E        +  where True = ImportResult(state=MeetingState(id='b91e6eb9', started_at=datetime.datetime(2026, 9, 19, 23, 48, 47, 682456), ended_at...ob_enqueued=True, windows_total=0, windows_empty=0, duration_seconds=9.0, warnings=[], speakers_found=['Priya', 'Sam']).intel_job_enqueued

tests/unit/test_hs201_import_no_auto_summary.py:151: AssertionError
_____________ test_an_imported_meeting_is_dated_the_import_moment ______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9139/test_an_imported_meeting_is_da0')
db = <holdspeak.db.core.Database object at 0x10b460b90>

    def test_an_imported_meeting_is_dated_the_import_moment(tmp_path, db):
        """Defect 10: a file copied to disk in June dated the meeting JUN 03."""
        before = datetime.now()
        wav = _aged(tmp_path / "old recording.wav", FIXTURE_WAV, days=108)
        mtime = datetime.fromtimestamp(wav.stat().st_mtime)
    
        state = import_meeting(
            wav, db=db, transcriber=FakeTranscriber(["hello"]), config=_config()
        ).state
    
>       assert state.started_at >= before
E       AssertionError: assert datetime.datetime(2026, 6, 3, 23, 48, 47, 859163) >= datetime.datetime(2026, 9, 19, 23, 48, 47, 858945)
E        +  where datetime.datetime(2026, 6, 3, 23, 48, 47, 859163) = MeetingState(id='3879a5bb', started_at=datetime.datetime(2026, 6, 3, 23, 48, 47, 859163), ended_at=datetime.datetime(2...=None, capture_checkpoint_seconds=0.0, provenance='desktop', calendar_event_id=None, sync_modified_at=None, devices=[]).started_at

tests/unit/test_hs201_import_no_auto_summary.py:168: AssertionError
_______ test_transcription_status_is_final_once_the_transcript_is_final ________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9139/test_transcription_status_is_f0')
db = <holdspeak.db.core.Database object at 0x10b4811d0>

    def test_transcription_status_is_final_once_the_transcript_is_final(tmp_path, db):
        """Defect 11: `active` after the transcript was final and would never move."""
        wav = _aged(tmp_path / "final.wav", FIXTURE_WAV, days=1)
        state = import_meeting(
            wav, db=db, transcriber=FakeTranscriber(["hello"]), config=_config()
        ).state
        from holdspeak import meeting_import
    
>       assert meeting_import.TRANSCRIPTION_COMPLETE == TRANSCRIPTION_COMPLETE
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: module 'holdspeak.meeting_import' has no attribute 'TRANSCRIPTION_COMPLETE'

tests/unit/test_hs201_import_no_auto_summary.py:200: AttributeError
=========================== short test summary info ============================
FAILED tests/unit/test_hs201_import_no_auto_summary.py::test_audio_import_with_intel_on_enqueues_nothing_and_contacts_nobody
FAILED tests/unit/test_hs201_import_no_auto_summary.py::test_transcript_import_with_intel_on_enqueues_nothing
FAILED tests/unit/test_hs201_import_no_auto_summary.py::test_an_imported_meeting_is_dated_the_import_moment
FAILED tests/unit/test_hs201_import_no_auto_summary.py::test_transcription_status_is_final_once_the_transcript_is_final
4 failed, 2 passed in 2.75s
```

### Captured run — 2026-09-20T06:10:18Z

- **Command:** `uv run pytest -q tests/unit/test_hs201_import_no_auto_summary.py tests/unit/test_meeting_import.py tests/unit/test_transcript_import_engine.py tests/unit/test_phase143_intel_queue_inventory.py tests/integration/test_meeting_import_parity.py tests/integration/test_web_meeting_import_api.py tests/integration/test_web_transcript_import_api.py -p no:randomly`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
....................................................                     [100%]
52 passed in 12.78s
```

### Captured run — 2026-09-20T06:10:38Z

- **Command:** `uv run pytest -q -s tests/e2e/test_hs201_summary_face_glass.py -p no:randomly -k import`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
FIXTURE core_path_smoke_16k.wav 2.79s mtime=2026-06-04 00:10:40.483775
IMPORT POST /api/meetings/import (no started_at_ms)
IMPORTED 5a1389ac segments=1
AFTER IMPORT jobs=[] analyzed=[] intel_status=disabled started_at=2026-09-20 00:10:43.810177 transcription_status=complete
ROW Imported standupSEP 20 · OFFSEP 20·3 S·9 WORDS·OFFTHIS DEVICERun summary
PLANNED host=same_device hash=sha256:382bcba76d0beece757a5ef68b63a412a2712e66d9ed6b398aa00c6026529f56
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-row-length-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-row-length-393.png
DETAIL HEAD Imported standupSEP 20·3 S·SUMMARY OFF
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-done-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-done-393.png
RUN POST {'path': '/api/meetings/5a1389ac/intelligence/run', 'body': '{"expected_selection_hash":"sha256:382bcba76d0beece757a5ef68b63a412a2712e66d9ed6b398aa00c6026529f56"}'}
RECEIPT {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_1f30ee7a2d8a4b34baaf75890f908671', 'outcome': 'succeeded'}], 'job_id': 'ij_f8af4086f9a7e56a2ce56d169528f3332bcd15878def266672622d9af3b682cf', 'meeting_id': '5a1389ac', 'outcome': 'succeeded', 'receipt_id': 'rr_fe7d3bafc75cea5bc734b3ce546a40c2', 'selection_hash': 'sha256:382bcba76d0beece757a5ef68b63a412a2712e66d9ed6b398aa00c6026529f56'}
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-after-run-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots/import-after-run-393.png
.
1 passed, 1 deselected in 10.90s
```

### Captured run — 2026-09-20T06:10:55Z

- **Command:** `uv run pytest -q -s tests/e2e/test_hs201_summary_producer_chain.py -p no:randomly`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
..ENGINE stub endpoint=http://127.0.0.1:9000/v1 model=provider/model
.ENGINE lan endpoint=http://192.168.1.43:8080/v1 model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
LAN SUMMARY 'The recording contains only a placeholder sentence with no substantive meeting content.'
LAN RECEIPT {'attempts': [{'host': '192.168.1.43', 'leg_ordinal': 1, 'operation_id': 'op_e4715a66b7ad43f2b8bfaa93aa976e53', 'outcome': 'succeeded'}], 'job_id': 'ij_2d16e199677f7f91adc0f50034131f700e85b391b1cc259d59c4db66471f0d82', 'meeting_id': '502435a4', 'outcome': 'succeeded', 'receipt_id': 'rr_4d32007b410538a59c0b22aab76c18c9', 'selection_hash': 'sha256:a31f28feb61b9127b011d72da577e9063a961e3bcd41f93be5ba925ef376ad35'}
.
4 passed in 3.15s
```

### Captured run — 2026-09-20T06:10:59Z

- **Command:** `bash -c cd web && npx vitest run src/pages/cores/history/__tests__/importLengthAndDate.test.tsx src/pages/cores/history/__tests__/importSectionStart.test.tsx && npx tsc --noEmit -p tsconfig.json && echo "TYPECHECK CLEAN"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  2 passed (2)
      Tests  7 passed (7)
   Start at  00:10:59
   Duration  813ms (transform 457ms, setup 162ms, import 672ms, tests 156ms, environment 420ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.19.1
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.19.1
npm notice To update run: npm install -g npm@11.19.1
npm notice
TYPECHECK CLEAN
```

## Correction (counsel round, HS-201-09 worker)

The story file said the six fences in
`tests/unit/test_hs201_import_no_auto_summary.py` were "all red first".
The captured pre-fix run above reads `4 failed, 2 passed in 2.75s`: four
were red, two held before the fix as well. The story file is corrected;
no capture in this file was touched.
