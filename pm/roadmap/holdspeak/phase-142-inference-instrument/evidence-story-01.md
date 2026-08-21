# Evidence - HSEGHS001HS104-142-01

- **Story:** HSEGHS001HS104-142-01 - Capability Truth
- **Status:** done
- **Date:** 2026-08-21

## Proof

# Evidence — Capability Truth

This dossier records the read-only inference setup projection, signed catalog, HTTP/MCP parity, Models integration, writer-race closure, and two-width real-browser proof.

## Scope proof

- Server-owned signed preset catalog and pure owner-only projection.
- Bounded GGUF/MLX inspection with explicit execution support and no locator disclosure.
- Projection-driven Models surface with one selection group and one action seat.
- Durable serialized Settings patch writer for confirmed route changes.
- No acquisition, download, model load, benchmark, or new inference runtime in Story 01.

### Captured run — 2026-08-21T14:09:25Z

- **Command:** `uv run pytest -q tests/unit/test_inference_setup_capability_truth.py tests/unit/test_inference_targets.py tests/unit/test_mcp_phase133_auth.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_mcp_thoughts.py tests/unit/test_setup_runtime.py tests/unit/test_setup_status.py tests/unit/test_setup_status_doctor_drift.py tests/unit/test_api_surface.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e4a65374519353a6b62909e925f22c90343575b1

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 6.29s
```

### Captured run — 2026-08-21T14:09:45Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin:/usr/sbin:/sbin npm --prefix web exec -- vitest --root web run src/pages/cores/__tests__/SettingsCore.test.ts src/pages/cores/__tests__/InferenceCapabilityPanel.test.tsx src/pages/cores/__tests__/settingsModels.test.tsx --maxWorkers=1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e4a65374519353a6b62909e925f22c90343575b1

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  33 passed (33)
   Start at  08:09:45
   Duration  2.71s (transform 280ms, setup 89ms, import 496ms, tests 1.40s, environment 510ms)
```

### Captured run — 2026-08-21T14:09:54Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin:/usr/sbin:/sbin npm --prefix web run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e4a65374519353a6b62909e925f22c90343575b1

```text

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
../holdspeak/s
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-21T14:10:04Z

- **Command:** `uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py -x`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e4a65374519353a6b62909e925f22c90343575b1

```text
..                                                                       [100%]
2 passed in 7.06s
```

## Visual proof

- [Desktop capability truth](./assets/story-01/models-capability-truth-1440.png)
- [Mobile capability truth](./assets/story-01/models-capability-truth-393.png)
- [Desktop configured route](./assets/story-01/models-capability-truth-configured-1440.png)
- [Mobile configured route](./assets/story-01/models-capability-truth-configured-393.png)

The isolated browser walk verifies one action seat, server-ordered inert radio
selection, durable confirmed route mutation, secret clearing/non-disclosure,
44 px mobile targets, no horizontal overflow, initial mobile viewport position,
and a fresh desktop window tall enough to show the selected choice and action
seat together.

## Review result

Backend/application authority and web/product implementation received final
independent RATIFY rulings after the catalog, inspection, MCP discovery,
Settings writer concurrency, 393 opening position, and desktop geometry audits.
