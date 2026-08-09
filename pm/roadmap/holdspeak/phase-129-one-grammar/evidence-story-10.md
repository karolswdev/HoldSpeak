# Evidence - HS-129-10

- **Story:** HS-129-10 - Tokens green and the dead paths
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T22:01:11Z

- **Command:** `npm --prefix web run tokens:gate`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d038040ffd285ef4e5344855e8d839055f3b4b85

```text

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (12 allow-listed exceptions, all in use)
```

### Captured run — 2026-08-08T22:01:12Z

- **Command:** `uv run pytest -q tests/unit/test_delivery_read_model.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d038040ffd285ef4e5344855e8d839055f3b4b85

```text
....................                                                     [100%]
20 passed in 4.62s
```

### Captured run — 2026-08-08T22:01:17Z

- **Command:** `npm --prefix web run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d038040ffd285ef4e5344855e8d839055f3b4b85

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```

### Captured run — 2026-08-08T22:01:22Z

- **Command:** `npm --prefix web run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d038040ffd285ef4e5344855e8d839055f3b4b85

```text

> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1450 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/voice/intentRouter.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/store/compositorSlice.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/App.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RunsOnPicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/UtteranceWell.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ImportSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/infoContract.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/keymap.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/ReceiptsView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2      4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2          4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2          4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2      4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2      4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2              4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2              5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2              5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2               5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2       5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2       5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff      5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2               5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2               5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff      5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff       5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff           5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff       5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff       5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff           5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff               6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff               6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff               6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff        6.98 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DJqRU3vO.woff        7.02 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-KugGGMne.woff                7.06 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-2j5mBUwD.woff                7.19 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-B8X0CLgF.woff                7.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-Bc8Ftmh3.woff2      7.34 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-Cut-4mMH.woff2      7.53 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-obahsSVq.woff2                7.71 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-B4URO6DV.woff2                   7.78 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-BasfLYem.woff2                7.90 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-BIZE56-Y.woff2                   7.92 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-plRanbMR.woff2                   7.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-CWCymEST.woff2                7.97 kB
../holdspeak/static/_built/assets/inter-cyrillic-400-normal-HOLc17fK.woff                 9.78 kB
../holdspeak/static/_built/assets/inter-greek-400-normal-q2sYcFCs.woff                    9.92 kB
../holdspeak/static/_built/assets/inter-cyrillic-600-normal-4D_pXhcN.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-cyrillic-500-normal-CxZf_p3X.woff                 9.94 kB
../holdspeak/static/_built/assets/inter-greek-500-normal-Xzm54t5V.woff                    9.98 kB
../holdspeak/static/_built/assets/inter-greek-600-normal-BZpKdvQh.woff                   10.03 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-400-normal-fXTG6kC5.woff      10.13 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-BQZuk6qB.woff2           10.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-ext-500-normal-ckzbgY84.woff      10.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-B0yAr1jD.woff2           10.43 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Dfes3d0z.woff2           10.48 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-BQnZhY3m.woff2      11.99 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-DUe3BAxM.woff2      12.27 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-DxxdqCpr.woff2      12.29 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-RjhwGPKo.woff2          12.84 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-DjKNqYRj.woff2          13.28 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-lFbtlQH6.woff2          13.31 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-400-normal-DQukG94-.woff            13.34 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-500-normal-BmqWE9Dz.woff            13.45 kB
../holdspeak/static/_built/assets/inter-cyrillic-ext-600-normal-Bcila6Z-.woff            13.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-700-normal-CwsQ-cCU.woff           16.42 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-700-normal-HVCqSBdx.woff       16.46 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-600-normal-VcznFIpX.woff       16.73 kB
../holdspeak/static/_built/assets/space-grotesk-latin-ext-500-normal-3dgZTiw9.woff       16.79 kB
../holdspeak/static/_built/assets/space-grotesk-latin-600-normal-BflQw4A9.woff           16.88 kB
../holdspeak/static/_built/assets/space-grotesk-latin-500-normal-CNSSEhBt.woff           16.99 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-CJOVTJB7.woff          28.21 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-CyCys3Eg.woff                   30.70 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-CiBQ2DWP.woff                   31.26 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-BL9OpVg8.woff                   31.28 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-C1nco2VV.woff2              35.00 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-CV4jyFjo.woff2              36.02 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-D2bJ5OIk.woff2              36.26 kB
../holdspeak/static/_built/assets/inter-latin-ext-400-normal-77YHD8bZ.woff               47.56 kB
../holdspeak/static/_built/assets/inter-latin-ext-500-normal-BxGbmqWO.woff               48.49 kB
../holdspeak/static/_built/assets/inter-latin-ext-600-normal-CIVaiw4L.woff               48.67 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-cE2vkmv2.css                  0.50 kB │ gzip:   0.23 kB
../holdspeak/static/_built/assets/XtermPane-DDGTF8rc.css                                  3.62 kB │ gzip:   0.99 kB
../holdspeak/static/_built/assets/DictationCore-Da6f2DtU.css                              3.91 kB │ gzip:   0.97 kB
../holdspeak/static/_built/assets/index-DOFxvxtU.css                                     90.13 kB │ gzip:  30.57 kB
../holdspeak/static/_built/assets/desk-BoPVmnFs.css                                     189.22 kB │ gzip:  28.76 kB
../holdspeak/static/_built/assets/webworkerAll-CCnhxrG2.js                                0.16 kB │ gzip:   0.16 kB │ map:     0.66 kB
../holdspeak/static/_built/assets/browserAll-zkKycc4I.js                                  0.25 kB │ gzip:   0.20 kB │ map:     1.67 kB
../holdspeak/static/_built/assets/WelcomePage-D5D09sKP.js                                 0.43 kB │ gzip:   0.31 kB │ map:     1.13 kB
../holdspeak/static/_built/assets/core-layout-DFQBDjih.js                                 0.49 kB │ gzip:   0.30 kB │ map:     3.05 kB
../holdspeak/static/_built/assets/PresencePage-CR2990E2.js                                0.61 kB │ gzip:   0.41 kB │ map:     1.64 kB
../holdspeak/static/_built/assets/core-hooks-Ct2al37-.js                                  0.62 kB │ gzip:   0.41 kB │ map:     3.60 kB
../holdspeak/static/_built/assets/pageSupport-p4Y6-Bmm.js                                 0.81 kB │ gzip:   0.49 kB │ map:     4.58 kB
../holdspeak/static/_built/assets/SetupCore-CePaGqz1.js                                   2.17 kB │ gzip:   1.09 kB │ map:     8.66 kB
../holdspeak/static/_built/assets/helpers-D-uWXHJ8.js                                     2.20 kB │ gzip:   1.01 kB │ map:     7.66 kB
../holdspeak/static/_built/assets/CadenceCore-oluD12Li.js                                 2.76 kB │ gzip:   1.30 kB │ map:    11.05 kB
../holdspeak/static/_built/assets/WorkbenchesHomeCore-BNxkkppk.js                         3.03 kB │ gzip:   1.39 kB │ map:    10.50 kB
../holdspeak/static/_built/assets/CompanionCore-xed67H9X.js                               3.04 kB │ gzip:   1.37 kB │ map:    11.57 kB
../holdspeak/static/_built/assets/ConstitutionalContextCore-Bd55Oc0c.js                   3.30 kB │ gzip:   1.51 kB │ map:    11.58 kB
../holdspeak/static/_built/assets/ActivityCore-Dpy91YKE.js                                3.33 kB │ gzip:   1.48 kB │ map:    12.75 kB
../holdspeak/static/_built/assets/CommandsCore-C_VglkB9.js                                4.01 kB │ gzip:   1.74 kB │ map:    15.14 kB
../holdspeak/static/_built/assets/ComponentsCore-BvMiVpeW.js                              4.67 kB │ gzip:   1.99 kB │ map:    13.81 kB
../holdspeak/static/_built/assets/LiveCore-BslwaP-P.js                                    7.12 kB │ gzip:   2.97 kB │ map:    28.73 kB
../holdspeak/static/_built/assets/ProcessCore-KAyg-Lxm.js                                 9.43 kB │ gzip:   3.63 kB │ map:    39.77 kB
../holdspeak/static/_built/assets/ProjectMemoryCore-CVr5JdbR.js                          10.95 kB │ gzip:   4.14 kB │ map:    41.59 kB
..
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
