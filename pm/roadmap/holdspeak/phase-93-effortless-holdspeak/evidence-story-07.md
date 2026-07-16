# Evidence - HS-93-07

- **Story:** HS-93-07 - Secure, Normal, or YOLO
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T00:40:06Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cece26045a44408e46698abfb0626b7d82077e12

```text
ssssssssssssssssssssss...ssssssssss..................................... [  1%]
..................................................................s..... [  3%]
......s................................................................. [  5%]
....................................s..ss............................... [  7%]
........................................................................ [  9%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
................................ss..........s........................... [ 22%]
........................................................................ [ 24%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
......................                                                   [100%]
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
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: proof LLM unreachable
SKIPPED [1] tests/integration/test_rails_observer_live.py:39: proof LLM unreachable
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/uat/test_induction_integration_43.py:50: .43 LAN endpoint unreachable
SKIPPED [1] tests/uat/test_induction_integration_43.py:60: .43 LAN endpoint unreachable
SKIPPED [1] tests/uat/test_mesh_dispatch.py:52: .43 LAN endpoint unreachable
3798 passed, 42 skipped in 475.48s (0:07:55)
```

### Captured run — 2026-07-16T00:48:30Z

- **Command:** `npm --prefix web run check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cece26045a44408e46698abfb0626b7d82077e12

```text

> holdspeak-web@0.0.1 check
> npm run guard:architecture && npm run typecheck && npm run test:web && npm run build


> holdspeak-web@0.0.1 guard:architecture
> node scripts/guard-architecture.mjs

React architecture guard passed (113 source files; zero framework residue).

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  31 passed (31)
      Tests  166 passed (166)
   Start at  18:48:34
   Duration  10.72s (transform 511ms, setup 1.44s, import 2.10s, tests 1.54s, environment 11.44s)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 529 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                   0.90 kB │ gzip:  0.43 kB
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
../holdspeak/static/_built/assets/desk-C1IUCiLk.css                                    54.26 kB │ gzip:  9.48 kB
../holdspeak/static/_built/assets/index-Cu9BqMtU.css                                  100.52 kB │ gzip: 32.04 kB
../holdspeak/static/_built/assets/WelcomePage-BA2BTqVD.js                               0.43 kB │ gzip:  0.31 kB │ map:     1.13 kB
../holdspeak/static/_built/assets/PresencePage-Db01gLQ1.js                              0.89 kB │ gzip:  0.52 kB │ map:     2.46 kB
../holdspeak/static/_built/assets/StudioPage-CO4nPqt-.js                                1.16 kB │ gzip:  0.66 kB │ map:     2.54 kB
../holdspeak/static/_built/assets/CompanionPage-DTvysBOM.js                             2.13 kB │ gzip:  1.01 kB │ map:     5.80 kB
../holdspeak/static/_built/assets/RuntimeDocsPage-Dy4l-q5V.js                           2.32 kB │ gzip:  1.00 kB │ map:     4.29 kB
../holdspeak/static/_built/assets/SetupPage-DAgWpw3y.js                                 2.40 kB │ gzip:  1.10 kB │ map:     7.85 kB
../holdspeak/static/_built/assets/pageSupport-gj29KS9M.js                               2.68 kB │ gzip:  1.31 kB │ map:     9.79 kB
../holdspeak/static/_built/assets/ActivityPage-6RmDaEGN.js                              3.40 kB │ gzip:  1.50 kB │ map:    12.09 kB
../holdspeak/static/_built/assets/CadencePage-C8Xguxub.js                               3.47 kB │ gzip:  1.52 kB │ map:    11.53 kB
../holdspeak/static/_built/assets/ComponentsPage-BGZR9vp3.js                            4.22 kB │ gzip:  1.63 kB │ map:    10.50 kB
../holdspeak/static/_built/assets/CommandsPage-CXS8eLL7.js                              4.33 kB │ gzip:  1.83 kB │ map:    15.47 kB
../holdspeak/static/_built/assets/ProfilesPage-s0HfLOxy.js                              4.85 kB │ gzip:  1.91 kB │ map:    16.67 kB
../holdspeak/static/_built/assets/LivePage-Czt4YVin.js                                  7.03 kB │ gzip:  2.66 kB │ map:    23.80 kB
../holdspeak/static/_built/assets/WorkbenchPage-B0a8La1e.js                             8.03 kB │ gzip:  3.31 kB │ map:    29.19 kB
../holdspeak/static/_built/assets/SettingsPage-o7g5X1_r.js                              8.24 kB │ gzip:  3.29 kB │ map:    29.43 kB
../holdspeak/static/_built/assets/HistoryPage-DekxoH2y.js                              14.46 kB │ gzip:  4.80 kB │ map:    51.83 kB
../holdspeak/static/_built/assets/DictationPage-CAzo1dpT.js                            15.70 kB │ gzip:  4.88 kB │ map:    51.22 kB
../holdspeak/static/_built/assets/react-Cqq31Jag.js                                    48.49 kB │ gzip: 17.21 kB │ map:   484.26 kB
../holdspeak/static/_built/assets/index-CqB7xuCd.js                                   194.36 kB │ gzip: 61.41 kB │ map:   899.91 kB
../holdspeak/static/_built/assets/desk-GTt4ca7a.js                                    310.06 kB │ gzip: 96.56 kB │ map: 1,377.75 kB
✓ built in 2.46s
```

### Captured run — 2026-07-16T02:36:09Z

- **Command:** `swift test --package-path apple`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cece26045a44408e46698abfb0626b7d82077e12

```text
Building for debugging...
[0/4] Write sources
[2/4] Write swift-version-39B54973F684ADAB.txt
[4/6] Emitting module RuntimeCore
[5/6] Compiling RuntimeCore MeetingAudioStore.swift
[6/7] Compiling RuntimeCore MeetingCapture.swift
[7/12] Emitting module InferenceLlamaTests
[8/12] Compiling RuntimeCoreTests SlidingWindowTests.swift
[9/12] Emitting module RuntimeCoreTests
[10/12] Compiling RuntimeCoreTests MeetingCaptureTests.swift
[10/12] Write Objects.LinkFileList
[11/12] Linking HoldSpeakMobilePackageTests
Build complete! (3.37s)
Test Suite 'All tests' started at 2026-07-15 20:36:13.698.
Test Suite 'HoldSpeakMobilePackageTests.xctest' started at 2026-07-15 20:36:13.699.
Test Suite 'ADRCandidatesTests' started at 2026-07-15 20:36:13.699.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRCandidatesValidate]' passed (0.004 seconds).
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' started.
Test Case '-[RuntimeCoreTests.ADRCandidatesTests testADRDoesNotFabricate]' passed (0.001 seconds).
Test Suite 'ADRCandidatesTests' passed at 2026-07-15 20:36:13.704.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.005 (0.005) seconds
Test Suite 'ActivityClientTests' started at 2026-07-15 20:36:13.704.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgeContractDecodesEveryServerField]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' started.
Test Case '-[ProvidersTests.ActivityClientTests testActivityNudgesDecodeServerShapeWithCitations]' passed (0.006 seconds).
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
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgePostsRealIntRecordId]' passed (0.001 seconds).
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' started.
Test Case '-[ProvidersTests.ActivityClientTests testSelectNudgeUnknownIdThrows]' passed (0.001 seconds).
Test Suite 'ActivityClientTests' passed at 2026-07-15 20:36:13.715.
	 Executed 9 tests, with 0 failures (0 unexpected) in 0.010 (0.011) seconds
Test Suite 'AftercareClientTests' started at 2026-07-15 20:36:13.715.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercare404Throws]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareClientGETsAndDecodes]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' started.
Test Case '-[ProvidersTests.AftercareClientTests testAftercareDigestDecodesFaithfully]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' started.
Test Case '-[ProvidersTests.AftercareClientTests testEmptyDigestDecodes]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssue400Throws]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssueErrorEnvelopeDecodesOn400]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' started.
Test Case '-[ProvidersTests.AftercareClientTests testFileAftercareIssuePostsAndDecodesProposal]' passed (0.001 seconds).
Test Suite 'AftercareClientTests' passed at 2026-07-15 20:36:13.720.
	 Executed 7 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'ArtifactCorrectionTests' started at 2026-07-15 20:36:13.720.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testCorrectedProducesSameTypeDraftWithVoiceProvenance]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' started.
Test Case '-[RuntimeCoreTests.ArtifactCorrectionTests testPromptFusesOriginalCorrectionAndTranscript]' passed (0.000 seconds).
Test Suite 'ArtifactCorrectionTests' passed at 2026-07-15 20:36:13.720.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ArtifactGenerationEngineTests' started at 2026-07-15 20:36:13.720.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testBatchIsResilientPerType]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testEmitsSchemaValidArtifact]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testMalformedOutputIsRecoverable]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' started.
Test Case '-[RuntimeCoreTests.ArtifactGenerationEngineTests testNeverAutoAccepts]' passed (0.000 seconds).
Test Suite 'ArtifactGenerationEngineTests' passed at 2026-07-15 20:36:13.722.
	 Executed 4 tests, with 0 failures (0 unexpected) in 0.001 (0.002) seconds
Test Suite 'ArtifactsClientTests' started at 2026-07-15 20:36:13.722.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testConfidenceIsOptionalAndEmptySourcesDecode]' passed (0.000 seconds).
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' started.
Test Case '-[ProvidersTests.ArtifactsClientTests testDecodesEnvelopeWithConfidenceAndSources]' passed (0.000 seconds).
Test Suite 'ArtifactsClientTests' passed at 2026-07-15 20:36:13.723.
	 Executed 2 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'AskClientTests' started at 2026-07-15 20:36:13.723.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' started.
Test Case '-[ProvidersTests.AskClientTests testLocalRunDecodesWithoutHost]' passed (0.001 seconds).
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' started.
Test Case '-[ProvidersTests.AskClientTests testNon2xxThrows]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' started.
Test Case '-[ProvidersTests.AskClientTests testRunStepPostsThePromptAndDecodesTheHonestEgress]' passed (0.000 seconds).
Test Suite 'AskClientTests' passed at 2026-07-15 20:36:13.724.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.001 (0.002) seconds
Test Suite 'AudioTests' started at 2026-07-15 20:36:13.724.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' started.
Test Case '-[ProvidersTests.AudioTests testAccumulatorIsBoundedAndCountsDrops]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' started.
Test Case '-[ProvidersTests.AudioTests testCaptureToWavPipeline]' passed (0.000 seconds).
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' started.
Test Case '-[ProvidersTests.AudioTests testWavHeaderIs16kMonoPCM16]' passed (0.000 seconds).
Test Suite 'AudioTests' passed at 2026-07-15 20:36:13.725.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.000 (0.001) seconds
Test Suite 'AuthorityClientTests' started at 2026-07-15 20:36:13.725.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' started.
Test Case '-[ProvidersTests.AuthorityClientTests testAuthorityPolicyDecodesTheSharedVersionedPosture]' passed (0.000 seconds).
Test Suite 'AuthorityClientTests' passed at 2026-07-15 20:36:13.726.
	 Executed 1 test, with 0 failures (0 unexpected) in 0.000 (0.001) seconds
Test Suite 'BlueprintInterpreterTests' started at 2026-07-15 20:36:13.726.
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
Test Suite 'BlueprintInterpreterTests' passed at 2026-07-15 20:36:13.733.
	 Executed 13 tests, with 0 failures (0 unexpected) in 0.007 (0.007) seconds
Test Suite 'BlueprintWireTests' started at 2026-07-15 20:36:13.733.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testBranchingBlueprintMatchesTheGoldenFixture]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testGraphJSONValueRoundTripsIntoWorkflowDefinition]' passed (0.002 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testLinearBlueprintMatchesTheGoldenFixture]' passed (0.001 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testRunsOnAbsentStaysAbsentOnTheWire]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' started.
Test Case '-[RuntimeCoreTests.BlueprintWireTests testWireShapeIsTheHubContract]' passed (0.000 seconds).
Test Suite 'BlueprintWireTests' passed at 2026-07-15 20:36:13.738.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.005 (0.005) seconds
Test Suite 'BubblePlacementTests' started at 2026-07-15 20:36:13.738.
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
Test Suite 'BubblePlacementTests' passed at 2026-07-15 20:36:13.739.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'CardLayoutTests' started at 2026-07-15 20:36:13.739.
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
Test Suite 'CardLayoutTests' passed at 2026-07-15 20:36:13.740.
	 Executed 5 tests, with 0 failures (0 unexpected) in 0.001 (0.001) seconds
Test Suite 'ChangeSetToleranceTests' started at 2026-07-15 20:36:13.740.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testANovelTypeDropsOneRecordNotTheWholeSet]' passed (0.001 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testCleanSetsReportZeroUndecoded]' passed (0.002 seconds).
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' started.
Test Case '-[ContractsTests.ChangeSetToleranceTests testRunOutputIsAKnownArtifactType]' passed (0.000 seconds).
Test Suite 'ChangeSetToleranceTests' passed at 2026-07-15 20:36:13.744.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.004 (0.004) seconds
Test Suite 'ChunkedExtractionTests' started at 2026-07-15 20:36:13.744.
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
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitOversizedInterpolatesTimingMonotonically]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitOversizedInterpolatesTimingMonotonically]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextHardCutsAnUnbrokenSpan]' started.
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests testSplitTextHardCutsAnUnbrokenSpan]' passed (0.000 seconds).
Test Case '-[RuntimeCoreTests.ChunkedExtractionTests test
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
