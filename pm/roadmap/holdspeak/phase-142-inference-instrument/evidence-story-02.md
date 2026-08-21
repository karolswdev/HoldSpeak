# Evidence - HSEGHS001HS104-142-02

- **Story:** HSEGHS001HS104-142-02 - Artifact Acquisition and Activation
- **Status:** done
- **Date:** 2026-08-21

## Proof

### Captured run — 2026-08-21T15:59:15Z

- **Command:** `uv run pytest -q tests/unit/test_inference_model_acquisition.py tests/unit/test_inference_setup_capability_truth.py tests/unit/test_deployment_revisions.py tests/unit/test_inference_runner.py tests/unit/test_inference_targets.py tests/unit/test_one_path_census.py tests/unit/test_one_path_cardinality.py tests/unit/test_one_path_context.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_phase133_auth.py tests/unit/test_db.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d131bc047940074eaae00fb1adb3e72b1c4b9efd

```text
........................................................................ [ 25%]
........................................................................ [ 51%]
........................................................................ [ 77%]
..............................................................           [100%]
278 passed in 94.21s (0:01:34)
```

### Captured run — 2026-08-21T16:01:39Z

- **Command:** `zsh -lc cd web && source "$HOME/.nvm/nvm.sh" && nvm use 22 --silent && npx vitest run src/pages/cores/__tests__/InferenceCapabilityPanel.test.tsx src/pages/cores/__tests__/settingsModels.test.tsx src/pages/cores/__tests__/SettingsCore.test.tsx && npm run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d131bc047940074eaae00fb1adb3e72b1c4b9efd

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  30 passed (30)
   Start at  10:01:39
   Duration  2.04s (transform 349ms, setup 131ms, import 551ms, tests 1.34s, environment 554ms)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1488 modules transformed.
rendering chunks...
[plugin vite:reporter]
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/store/compositorSlice.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/App.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ThoughtEntry.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/lanes/AgentsLane.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RunsOnPicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/dictation/UtteranceWell.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/history/ImportSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter]
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/ask.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/chat.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/voice/intentRouter.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter]
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/FinishThoughtsLane.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ThoughtEntry.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/lanes/MeetingsLane.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EditorAIBar.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/PersonaChat.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/infoContract.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/keymap.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/ProjectMemoryCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter]
(!) /Users/karol/dev/tools/HoldSpeak/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.43 kB
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
../holdspeak/static/_built/assets/PeopleCore-BoMvzdLl.css                                 2.33 kB │ gzip:   0.71 kB
../holdspeak/static/_built/assets/XtermPane-DDGTF8rc.css                                  3.62 kB │ gzip:   0.99 kB
../holdspeak/static/_built/assets/DictationCore-Da6f2DtU.css                              3.91 kB │ gzip:   0.97 kB
../holdspeak/static/_built/assets/index-CpeFMis4.css                                     90.71 kB │ gzip:  30.70 kB
../holdspeak/static/_built/assets/desk-DuF9eoaE.css                                     236.59 kB │ gzip:  36.38 kB
../holdspeak/static/_built/assets/webworkerAll-DGEa-ab6.js                                0.16 kB │ gzip:   0.16 kB │ map:     0.66 kB
../holdspeak/static/_built/assets/browserAll-BTueJSLh.js                                  0.25 kB │ gzip:   0.20 kB │ map:     1.67 kB
../holdspeak/static/_built/assets/WelcomePage-BP-7jfZE.js                                 0.43 kB │ gzip:   0.31 kB │ map:     1.13 kB
../holdspeak/static/_built/assets/core-layout-CiE1O0n1.js                                 0.49 kB │ gzip:   0.30 kB │ map:     3.05 kB
../holdspeak/static/_built/assets/PresencePage-DcTXzrPA.js                                0.61 kB │ gzip:   0.41 kB │ map:     1.64 kB
../holdspeak/static/_built/assets/core-hooks-BRlCHA_8.js                                  0.62 kB │ gzip:   0.41 kB │ map:     3.60 kB
../holdspeak/static/_built/assets/pageSupport-D-L6nQkS.js                                 0.81 kB │ gzip:   0.49 kB │ map:     4.58 kB
../holdspeak/static/_built/asse
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-21T16:01:51Z

- **Command:** `uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py tests/e2e/test_hs142_model_acquisition_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d131bc047940074eaae00fb1adb3e72b1c4b9efd

```text
....                                                                     [100%]
4 passed in 14.50s
```
