# Evidence - HS-93-09

- **Story:** HS-93-09 - The owner can live here
- **Status:** done
- **Date:** 2026-07-16

## Proof

### Captured run — 2026-07-16T06:13:48Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text
ssssssssssssssssssssss...ssssssssss..................................... [  1%]
..................................................................s..... [  3%]
........................................................................ [  5%]
.........................................ss............................. [  7%]
........................................................................ [  9%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 14%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
.................................................                        [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-7509ad04
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_import.py", line 325, in _persist_import
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
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/core.py", line 1247, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 1044, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 995, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/meetings.py", line 440, in get_meeting
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
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
3830 passed, 37 skipped, 1 warning in 829.77s (0:13:49)
```

### Captured run — 2026-07-16T06:27:40Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text

> holdspeak-web@0.0.1 check
> npm run guard:architecture && npm run typecheck && npm run test:web && npm run build


> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (120 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  36 passed (36)
      Tests  198 passed (198)
   Start at  00:27:43
   Duration  7.92s (transform 550ms, setup 1.13s, import 2.22s, tests 2.23s, environment 7.21s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 531 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                   0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2    4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2        4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2        4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2    4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2    4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2            4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2            5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2            5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2             5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2     5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2     5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff    5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2             5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2             5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff    5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff     5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff         5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff     5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff     5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff         5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff             6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff             6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff             6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff      6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff      7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff              7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff              7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff              7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2    7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2    7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2              7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                 7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2              7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                 7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                 7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2              7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff               9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                  9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff               9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff               9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                  9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                 10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff    10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2         10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff    10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2         10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2         10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2    11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2    12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2    12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2        12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2        13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2        13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff          13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff          13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff          13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff         16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff     16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff     16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff     16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff         16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff         16.99 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2       21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2       21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff        27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff        28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                 30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                 31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                 31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2            35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2            36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2            36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff             47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff             48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff             48.67 kB
../holdspeak/static/_built/assets/desk-DNRAqDj8.css                                    59.92 kB │ gzip:  10.47 kB
../holdspeak/static/_built/assets/index-DuXbFgaV.css                                   99.26 kB │ gzip:  31.92 kB
../holdspeak/static/_built/assets/WelcomePage-DrXgxUl0.js                               0.43 kB │ gzip:   0.31 kB │ map:     1.13 kB
../holdspeak/static/_built/assets/PresencePage-C6dw2KWK.js                              0.89 kB │ gzip:   0.52 kB │ map:     2.46 kB
../holdspeak/static/_built/assets/StudioPage-BgtIs5Kw.js                                1.25 kB │ gzip:   0.70 kB │ map:     2.80 kB
../holdspeak/static/_built/assets/CompanionPage-CNP185it.js                             2.13 kB │ gzip:   1.01 kB │ map:     5.80 kB
../holdspeak/static/_built/assets/RuntimeDocsPage-DAAoLbqz.js                           2.32 kB │ gzip:   1.00 kB │ map:     4.29 kB
../holdspeak/static/_built/assets/SetupPage-Bhg7z5H3.js                                 2.40 kB │ gzip:   1.10 kB │ map:     7.85 kB
../holdspeak/static/_built/assets/pageSupport-PShRh2SU.js                               2.87 kB │ gzip:   1.37 kB │ map:    10.71 kB
../holdspeak/static/_built/assets/ActivityPage-XkCOj2I9.js                              3.40 kB │ gzip:   1.50 kB │ map:    12.09 kB
../holdspeak/static/_built/assets/CadencePage-BIpMvmr-.js                               3.47 kB │ gzip:   1.52 kB │ map:    11.53 kB
../holdspeak/static/_built/assets/ComponentsPage-Dqw6FSIf.js                            4.25 kB │ gzip:   1.66 kB │ map:    10.53 kB
../holdspeak/static/_built/assets/CommandsPage-hnxTXs9o.js                              4.33 kB │ gzip:   1.83 kB │ map:    15.47 kB
../holdspeak/static/_built/assets/ProfilesPage-C-M297cm.js                              4.93 kB │ gzip:   1.96 kB │ map:    17.04 kB
../holdspeak/static/_built/assets/LivePage-DxXI-rqs.js                                  7.03 kB │ gzip:   2.66 kB │ map:    23.80 kB
../holdspeak/static/_built/assets/WorkbenchPage-D_w674VM.js                             8.05 kB │ gzip:   3.33 kB │ map:    29.26 kB
../holdspeak/static/_built/assets/SettingsPage-B6VIjtn7.js                              8.40 kB │ gzip:   3.33 kB │ map:    29.73 kB
../holdspeak/static/_built/assets/HistoryPage-DAN48WZZ.js                              14.49 kB │ gzip:   4.85 kB │ map:    52.22 kB
../holdspeak/static/_built/assets/DictationPage-C4BhPpcA.js                            16.36 kB │ gzip:   5.17 kB │ map:    53.95 kB
../holdspeak/static/_built/assets/react-Cqq31Jag.js                                    48.49 kB │ gzip:  17.21 kB │ map:   484.26 kB
../holdspeak/static/_built/assets/index-Cd-pncef.js                                   194.39 kB │ gzip:  61.41 kB │ map:   900.22 kB
../holdspeak/static/_built/assets/desk-yMJV7J6I.js                                    322.62 kB │ gzip: 101.16 kB │ map: 1,431.50 kB
✓ built in 1.44s
```

### Captured run — 2026-07-16T06:27:53Z

- **Command:** `swift test --package-path apple`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text
Building for debugging...
[0/7] Write sources
[5/7] Write swift-version-39B54973F684ADAB.txt
[7/9] Compiling Contracts MissionControl.swift
[8/9] Emitting module Contracts
[9/14] Compiling Providers HTTPDesktopClient+Projections.swift
[10/14] Compiling Providers HTTPDesktopClient+Steering.swift
[11/14] Compiling Providers HTTPDesktopClient+Inbox.swift
[12/14] Compiling Providers HTTPDesktopClient+Authority.swift
[13/14] Emitting module Providers
[14/21] Compiling RuntimeCore MeetingAudioStore.swift
[15/21] Emitting module RuntimeCore
[16/21] Compiling ProvidersTests MeshInboxClientTests.swift
[17/21] Compiling ProvidersTests SteeringClientTests.swift
[18/21] Compiling ProvidersTests ProjectionClientTests.swift
[19/21] Compiling ProvidersTests AuthorityClientTests.swift
[20/21] Emitting module ProvidersTests
[21/24] Emitting module RuntimeCoreTests
[22/24] Compiling RuntimeCoreTests MeetingCaptureTests.swift
[23/24] Compiling RuntimeCoreTests SlidingWindowTests.swift
Build complete! (3.14s)
Test Suite 'All tests' started at 2026-07-16 00:27:57.930.
Test Suite 'HoldSpeakMobilePackageTests.xctest' started at 2026-07-16 00:27:57.931.
Test Suite 'ADRCandidatesTests' started at 2026-07-16 00:27:57.931.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' passed (0.005 seconds).
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' passed (0.000 seconds).
Test Suite 'ADRCandidatesTests' passed at 2026-07-16 00:27:57.937.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.005 (0.006) seconds
Test Suite 'ActivityClientTests' started at 2026-07-16 00:27:57.937.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' passed (0.007 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesEmptyWhenTrackingOff]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesEmptyWhenTrackingOff]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesHTTPErrorThrows]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesHTTPErrorThrows]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testBriefingDecodesDigest]' started.
Test Case '-[ProvidersTests.ActivityClientTests testBriefingDecodesDigest]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testBriefingNilWhenAbsent]' started.
Test Case '-[ProvidersTests.ActivityClientTests testBriefingNilWhenAbsent]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testDismissNudgeHitsKeyedPath]' started.
Test Case '-[ProvidersTests.ActivityClientTests testDismissNudgeHitsKeyedPath]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgePostsRealIntRecordId]' started.
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgePostsRealIntRecordId]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' started.
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' passed (0.000 seconds).
Test Suite 'ActivityClientTests' passed at 2026-07-16 00:27:57.948.
	 Executed 9 tests, with 0 failures (0 unexpected) in 0.011 (0.011) seconds
Test Suite 'AftercareClientTests' started at 2026-07-16 00:27:57.948.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' passed (0.002 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' passed (0.001 seconds).
Test Suite 'AftercareClientTests' passed at 2026-07-16 00:27:57.953.
	 Executed 7 tests, with 0 failures (0 unexpected) in 0.004 (0.005) seconds
Test Suite 'ArtifactCorrectionTests' started at 2026-07-16 00:27:57.953.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' passed (0.000 seconds).
Test Suite 'ArtifactCorrectionTests' passed at 2026-07-16 00:27:57.954.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ArtifactGenerationEngineTests' started at 2026-07-16 00:27:57.954.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' passed (0.000 seconds).
Test Suite 'ArtifactGenerationEngineTests' passed at 2026-07-16 00:27:57.955.
	 Executed 4 tests, with 0 failures (0 unexpected) in 0.001 (0.002) seconds
Test Suite 'ArtifactsClientTests' started at 2026-07-16 00:27:57.955.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' passed (0.000 seconds).
Test Suite 'ArtifactsClientTests' passed at 2026-07-16 00:27:57.956.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'AskClientTests' started at 2026-07-16 00:27:57.956.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' started.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' started.
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' started.
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' passed (0.000 seconds).
Test Suite 'AskClientTests' passed at 2026-07-16 00:27:57.958.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.001 (0.002) seconds
Test Suite 'AudioTests' started at 2026-07-16 00:27:57.958.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' started.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' started.
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' started.
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' passed (0.000 seconds).
Test Suite 'AudioTests' passed at 2026-07-16 00:27:57.958.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.000 (0.001) seconds
Test Suite 'AuthorityClientTests' started at 2026-07-16 00:27:57.958.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' started.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' passed (0.001 seconds).
Test Suite 'AuthorityClientTests' passed at 2026-07-16 00:27:57.959.
	 Executed 1 test, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'BlueprintInterpreterTests' started at 2026-07-16 00:27:57.959.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testAsyncStreamSurfaceYieldsEvents]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testAsyncStreamSurfaceYieldsEvents]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBlueprintAndEventsAreCodable]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBlueprintAndEventsAreCodable]' passed (0.003 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesFalsePathWhenConditionFails]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesFalsePathWhenConditionFails]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesTruePathWhenConditionHolds]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testBranchTakesTruePathWhenConditionHolds]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testDataResolutionPullsUpstreamValueAndSubstitutesInput]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testDataResolutionPullsUpstreamValueAndSubstitutesInput]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testExecutionEventStreamEmitsExpectedOrderedSequence]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testExecutionEventStreamEmitsExpectedOrderedSequence]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testForEachRunsBodyExactlyNTimes]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testForEachRunsBodyExactlyNTimes]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureFallbackPolicyRecovers]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureFallbackPolicyRecovers]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureRetriesThenFailsWithoutCrash]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureRetriesThenFailsWithoutCrash]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureSkipPolicyCarriesInput]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testModelFailureSkipPolicyCarriesInput]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testValidationRejectsDataTypeMismatch]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testValidationRejectsDataTypeMismatch]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopIsBoundedByMaxIterations]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopIsBoundedByMaxIterations]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopStopsWhenConditionFails]' started.
Test Case '-[RuntimeCoreTests.BlueprintInterpreterTests testWhileLoopStopsWhenConditionFails]' passed (0.000 seconds).
Test Suite 'BlueprintInterpreterTests' passed at 2026-07-16 00:27:57.966.
	 Executed 13 tests, with 0 failures (0 unexpected) in 0.007 (0.007) seconds
Test Suite 'BlueprintWireTests' started at 2026-07-16 00:27:57.966.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' passed (0.002 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' passed (0.000 seconds).
Test Suite 'BlueprintWireTests' passed at 2026-07-16 00:27:57.970.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.003 (0.004) seconds
Test Suite 'BubblePlacementTests' started at 2026-07-16 00:27:57.970.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBackInTheStreamSnapsBack]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBackInTheStreamSnapsBack]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBelowTheStreamIsLoose]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropBelowTheStreamIsLoose]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropOnTackZoneTacks]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testDropOnTackZoneTacks]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testPlainPlacementIsTheDefaultBelowTheFold]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testPlainPlacementIsTheDefaultBelowTheFold]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BubblePlacementTests testTackZoneWinsEvenAboveThePinFloor]' started.
Test Case '-[RuntimeCoreTests.BubblePlacementTests testTackZoneWinsEvenAboveThePinFloor]' passed (0.000 seconds).
Test Suite 'BubblePlacementTests' passed at 2026-07-16 00:27:57.971.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'CardLayoutTests' started at 2026-07-16 00:27:57.971.
Test Case '-[RuntimeCoreTests.CardLayoutTests testClampWidthHoldsTheReadableRange]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testClampWidthHoldsTheReadableRange]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyCentersEachRow]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyCentersEachRow]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyEmptyIsEmpty]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyEmptyIsEmpty]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyFlowsIntoRows]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyFlowsIntoRows]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyPlacesEveryCardBelowTheStreamAndOnScreen]' started.
Test Case '-[RuntimeCoreTests.CardLayoutTests testTidyPlacesEveryCardBelowTheStreamAndOnScreen]' passed (0.000 seconds).
Test Suite 'CardLayoutTests' passed at 2026-07-16 00:27:57.972.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ChangeSetToleranceTests' started at 2026-07-16 00:27:57.972.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' passed (0.001 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' passed (0.002 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' passed (0.000 seconds).
Test Suite 'ChangeSetToleranceTests' passed at 2026-07-16 00:27:57.976.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'ChunkedExtractionTests' started at 2026-07-16 00:27:57.976.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetIsMonotonicInRAM]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetIsMonotonicInRAM]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetReturnsCeilingWhenRAMIsAmple]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetReturnsCeilingWhenRAMIsAmple]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetShrinksOnConstrainedDeviceAndNeverExceedsRAM]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testBudgetShrinksOnConstrainedDeviceAndNeverExceedsRAM]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testChunkedExtractionWindowsThenMergesAcrossWindows]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testChunkedExtractionWindowsThenMergesAcrossWindows]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupCollapsesCrossWindowDuplicatesKeepingHigherConfidence]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupCollapsesCrossWindowDuplicatesKeepingHigherConfidence]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupKeepsDifferentTypesSeparate]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testDedupKeepsDifferentTypesSeparate]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testEmptyTranscriptYieldsNoWindows]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testEmptyTranscriptYieldsNoWindows]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testNeedsChunkingThreshold]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testNeedsChunkingThreshold]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testOversizedSegmentIsSplitSoEveryWindowFitsBudget]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testOversizedSegmentIsSplitSoEveryWindowFitsBudget]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testShortTranscriptDoesNotChunk]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testShortTranscriptDoesNotChunk]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtract
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-16T06:27:58Z

- **Command:** `uv build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text
Building source distribution...
npm warn deprecated whatwg-encoding@3.1.1: Use @exodus/bytes instead for a more spec-conformant and faster implementation

added 198 packages, and audited 199 packages in 2s

35 packages are looking for funding
  run `npm fund` for details

1 low severity vulnerability

To address all issues, run:
  npm audit fix

Run `npm audit` for details.

> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 531 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                   0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2    4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2        4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2        4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2    4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2    4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2            4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2            5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2            5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2             5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2     5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2     5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff    5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2             5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2             5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff    5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff     5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff         5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff     5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff     5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff         5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff             6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff             6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff             6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff      6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff      7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff              7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff              7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff              7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2    7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2    7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2              7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                 7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2              7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                 7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                 7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2              7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff               9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                  9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff               9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff               9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                  9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                 10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff    10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2         10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff    10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2         10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2         10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2    11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2    12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2    12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2        12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2        13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2        13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff          13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff          13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff          13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff         16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff     16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff     16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff     16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff         16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff         16.99 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2       21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2       21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff        27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff        28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                 30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                 31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                 31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2            35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2            36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2            36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff             47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff             48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff             48.67 kB
../holdspeak/static/_built/assets/desk-DNRAqDj8.css                                    59.92 kB │ gzip:  10.47 kB
../holdspeak/static/_built/assets/index-DuXbFgaV.css                                   99.26 kB │ gzip:  31.92 kB
../holdspeak/static/_built/assets/WelcomePage-DrXgxUl0.js                               0.43 kB │ gzip:   0.31 kB │ map:     1.13 kB
../holdspeak/static/_built/assets/PresencePage-C6dw2KWK.js                              0.89 kB │ gzip:   0.52 kB │ map:     2.46 kB
../holdspeak/static/_built/assets/StudioPage-BgtIs5Kw.js                                1.25 kB │ gzip:   0.70 kB │ map:     2.80 kB
../holdspeak/static/_built/assets/CompanionPage-CNP185it.js                             2.13 kB │ gzip:   1.01 kB │ map:     5.80 kB
../holdspeak/static/_built/assets/RuntimeDocsPage-DAAoLbqz.js                           2.32 kB │ gzip:   1.00 kB │ map:     4.29 kB
../holdspeak/static/_built/assets/SetupPage-Bhg7z5H3.js                                 2.40 kB │ gzip:   1.10 kB │ map:     7.85 kB
../holdspeak/static/_built/assets/pageSupport-PShRh2SU.js                               2.87 kB │ gzip:   1.37 kB │ map:    10.71 kB
../holdspeak/static/_built/assets/ActivityPage-XkCOj2I9.js                              3.40 kB │ gzip:   1.50 kB │ map:    12.09 kB
../holdspeak/static/_built/assets/CadencePage-BIpMvmr-.js                               3.47 kB │ gzip:   1.52 kB │ map:    11.53 kB
../holdspeak/static/_built/assets/ComponentsPage-Dqw6FSIf.js                            4.25 kB │ gzip:   1.66 kB │ map:    10.53 kB
../holdspeak/static/_built/assets/CommandsPage-hnxTXs9o.js                              4.33 kB │ gzip:   1.83 kB │ map:    15.47 kB
../holdspeak/static/_built/assets/ProfilesPage-C-M297cm.js                              4.93 kB │ gzip:   1.96 kB │ map:    17.04 kB
../holdspeak/static/_built/assets/LivePage-DxXI-rqs.js                                  7.03 kB │ gzip:   2.66 kB │ map:    23.80 kB
../holdspeak/static/_built/assets/WorkbenchPage-D_w674VM.js                             8.05 kB │ gzip:   3.33 kB │ map:    29.26 kB
../holdspeak/static/_built/assets/SettingsPage-B6VIjtn7.js                              8.40 kB │ gzip:   3.33 kB │ map:    29.73 kB
../holdspeak/static/_built/assets/HistoryPage-DAN48WZZ.js                              14.49 kB │ gzip:   4.85 kB │ map:    52.22 kB
../holdspeak/static/_built/assets/DictationPage-C4BhPpcA.js                            16.36 kB │ gzip:   5.17 kB │ map:    53.95 kB
../holdspeak/static/_built/assets/react-Cqq31Jag.js                                    48.49 kB │ gzip:  17.21 kB │ map:   484.26 kB
../holdspeak/static/_built/assets/index-Cd-pncef.js                                   194.39 kB │ gzip:  61.41 kB │ map:   900.22 kB
../holdspeak/static/_built/assets/desk-yMJV7J6I.js                                    322.62 kB │ gzip: 101.16 kB │ map: 1,431.50 kB
✓ built in 1.45s
Building wheel from source distribution...
npm warn deprecated whatwg-encoding@3.1.1: Use @exodus/bytes instead for a more spec-conformant and faster implementation

added 198 packages, and audited 199 packages in 2s

35 packages are looking for funding
  run `npm fund` for details

1 low severity vulnerability

To address all issues, run:
  npm audit fix

Run `npm audit` for details.

> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 531 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/.cache/uv/sdists-v9/.tmp6ux6ZV/holdspeak-0.4.0/web/src/desk/ask.ts is dynamically imported by /Users/karol/.cache/uv/sdists-v9/.tmp6ux6ZV/holdspeak-0.4.0/web/src/desk/chat.ts but also statically imported by /Users/karol/.cache/uv/sdists-v9/.tmp6ux6ZV/holdspeak-0.4.0/web/src/desk/components/AskPanel.tsx, /Users/karol/.cache/uv/sdists-v9/.tmp6ux6ZV/holdspeak-0.4.0/web/src/desk/components/PersonaChat.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                   0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2    4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2        4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2        4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2    4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2    4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2            4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2            5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2            5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2             5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2     5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2     5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff    5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2             5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2             5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff    5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff     5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff         5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff     5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff     5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff         5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff             6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff             6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff             6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff      6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff      7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff              7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff              7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff              7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2    7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2    7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2              7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                 7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2              7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                 7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                 7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2              7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff               9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                  9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff               9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff               9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                  9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                 10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff    10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2         10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff    10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2         10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2         10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2    11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2    12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2    12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2        12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2        13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2        13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff          13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff          13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff          13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff         16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff     16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff     16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff     16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff         16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff         16.99 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2       21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2       21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff        27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff        28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                 30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                 31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                 31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2            35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2            36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2            36.26 kB
../holdspeak/static/_built/assets/inter-latin-
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-16T06:28:22Z

- **Command:** `.githooks/dw check holdspeak`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text
ERROR pm/roadmap/holdspeak/phase-93-effortless-holdspeak: all stories are done but final-summary.md is missing
```

### Captured run — 2026-07-16T06:29:17Z

- **Command:** `.githooks/dw check holdspeak`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca0a5c013488a06665c2bb4a14ccfb6635ae37a0

```text
dw check: ok
```
