# Evidence - PHILO-4-04

- **Story:** PHILO-4-04 - The triaged headline (the generated snapshot vs the current triage state)
- **Status:** done
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-24T14:13:11Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin:/Library/Apple/usr/bin:/Users/karol/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/codex-path:/Users/karol/.codex/tmp/arg0/codex-arg0fETbyu:/Users/karol/.kimi-code/bin:/Users/karol/.opencode/bin:/Users/karol/.local/bin:/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/dev/code/delivery-workbench/plugin/bin:/Users/karol/.claude/plugins/cache/claude-plugins-official/swift-lsp/1.0.0/bin HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.xwM61lzZlB npm_config_cache=/Users/karol/.npm npm --prefix web run build`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text

> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1690 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/InterviewPanel.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/ThreadComposer.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/RoomActions.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/windowCommands.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/gl/atmosphereActivity.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/infoContract.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/keymap.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/newThought.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/shared/ThreadsSection.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/useDeskChangedRefresh.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/ChangePlacesCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/threads.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/verbRegistry.ts but also statically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/callLoopWiring.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/CallChip.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/hooks/useChatImport.ts, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/shared/ThreadsSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-4-04/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

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
../holdspeak/static/_built/assets/rainy-masonry-DIBtQ-m6.webp                            17.21 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-V6pRDFza.woff2         21.17 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-500-normal-BWZEU5yA.woff2         21.83 kB
../holdspeak/static/_built/assets/inter-latin-400-normal-C38fXH4l.woff2                  23.66 kB
../holdspeak/static/_built/assets/inter-latin-500-normal-Cerq10X2.woff2                  24.27 kB
../holdspeak/static/_built/assets/inter-latin-600-normal-LgqL8muc.woff2                  24.45 kB
../holdspeak/static/_built/assets/jetbrains-mono-latin-400-normal-6-qcROiO.woff          27.50 kB
../holdspeak/static/_built/assets/jetb
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-24T14:13:51Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin:/Library/Apple/usr/bin:/Users/karol/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/codex-path:/Users/karol/.codex/tmp/arg0/codex-arg0fETbyu:/Users/karol/.kimi-code/bin:/Users/karol/.opencode/bin:/Users/karol/.local/bin:/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/dev/code/delivery-workbench/plugin/bin:/Users/karol/.claude/plugins/cache/claude-plugins-official/swift-lsp/1.0.0/bin HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.AZBKj16CNN PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 1440 --engine none --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
[glass_infra] web bundle rebuilt in 4.6s
PASS: live
BRAIN: astra
SOURCE: e4cf7d086dc0ef30f0f5b128267d79ec787a0209 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-B9eRs6XW.js'] hub=http://127.0.0.1:57394 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-107g6skr/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141351Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141351Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}
```

### Captured run — 2026-09-24T14:14:45Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin:/Library/Apple/usr/bin:/Users/karol/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/codex-path:/Users/karol/.codex/tmp/arg0/codex-arg0fETbyu:/Users/karol/.kimi-code/bin:/Users/karol/.opencode/bin:/Users/karol/.local/bin:/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/dev/code/delivery-workbench/plugin/bin:/Users/karol/.claude/plugins/cache/claude-plugins-official/swift-lsp/1.0.0/bin HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.qrrwTKwz8m PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 393 --engine none --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
PASS: live
BRAIN: astra
SOURCE: e4cf7d086dc0ef30f0f5b128267d79ec787a0209 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-B9eRs6XW.js'] hub=http://127.0.0.1:57461 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ayo8wh6i/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141445Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141445Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}
```

### Captured run — 2026-09-24T14:15:59Z

- **Command:** `python3 docs/internal/philo/phase-4/headline/verify_observations.py pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141351Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T141445Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/observation.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
[
  {
    "run_id": "20260924T141351Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440",
    "case_id": "case.philo404.arrival_triaged_headline.all_handled",
    "viewport": 1440,
    "verdict": "PASS",
    "revision": "e4cf7d086dc0ef30f0f5b128267d79ec787a0209",
    "dirty": true,
    "brief_id": "brief-2bf0736a436247bca83091c351bf3503",
    "headline": "2 decisions waiting.",
    "arrival_rows": 2,
    "handled_states": {
      "brief-item-79f9bb513f214866a2d16312e22494e5": "acknowledged",
      "brief-item-e3d1367463cf4575b08b729b841b83ef": "deferred"
    },
    "headline_and_stored_items_unchanged": true,
    "stored_shelf_matches_face": true,
    "isolated_db": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-107g6skr/.local/share/holdspeak/holdspeak.db",
    "handled_line_geometry": {
      "x": 256,
      "y": 364,
      "w": 928,
      "h": 18
    },
    "all_nine_hit_points_owned": true,
    "initial_feedback": {
      "elapsed_s": 0.94,
      "text": "ALL 2 HANDLED",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}"
    },
    "terminal_outcome": {
      "state": "settled",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}",
      "pending_marker": null,
      "pending_marker_present": null,
      "elapsed_s": 1.081,
      "first_satisfied_at_s": 0.94,
      "completion_bound_s": 30.0,
      "late_result_s": null,
      "within_bound": true
    }
  },
  {
    "run_id": "20260924T141445Z-case.philo404.arrival_triaged_headline.all_handled-astra-393",
    "case_id": "case.philo404.arrival_triaged_headline.all_handled",
    "viewport": 393,
    "verdict": "PASS",
    "revision": "e4cf7d086dc0ef30f0f5b128267d79ec787a0209",
    "dirty": true,
    "brief_id": "brief-a8775c0a58214360b24e5c93638e9029",
    "headline": "2 decisions waiting.",
    "arrival_rows": 2,
    "handled_states": {
      "brief-item-fca842d468314110a78da5664dccf9c2": "deferred",
      "brief-item-16516e37c2444626bb5eb6752013ca65": "acknowledged"
    },
    "headline_and_stored_items_unchanged": true,
    "stored_shelf_matches_face": true,
    "isolated_db": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ayo8wh6i/.local/share/holdspeak/holdspeak.db",
    "handled_line_geometry": {
      "x": 12,
      "y": 371,
      "w": 369,
      "h": 18
    },
    "all_nine_hit_points_owned": true,
    "initial_feedback": {
      "elapsed_s": 0.932,
      "text": "ALL 2 HANDLED",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}"
    },
    "terminal_outcome": {
      "state": "settled",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}",
      "pending_marker": null,
      "pending_marker_present": null,
      "elapsed_s": 1.065,
      "first_satisfied_at_s": 0.932,
      "completion_bound_s": 30.0,
      "late_result_s": null,
      "within_bound": true
    }
  }
]
```

### Captured run — 2026-09-24T14:16:16Z

- **Command:** `python3 docs/internal/philo/phase-4/headline/verify_lane.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text

collect-python: ['uv', 'run', '--no-sync', 'pytest', '--collect-only', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
tests/unit/test_philo4_04_headline_storage.py::test_compose_fixture_has_the_ratified_headline
tests/unit/test_philo4_04_headline_storage.py::test_real_generate_shelf_and_latest_preserve_all_six_rows
tests/unit/test_brief_shelf.py::test_shelf_is_empty_before_any_triage
tests/unit/test_brief_shelf.py::test_acknowledge_survives_a_fresh_read
tests/unit/test_brief_shelf.py::test_defer_replaces_an_earlier_state
tests/unit/test_brief_shelf.py::test_clearing_returns_the_item_to_untouched
tests/unit/test_brief_shelf.py::test_unknown_item_and_state_are_refused_by_name
tests/unit/test_brief_shelf.py::test_shelf_routes_round_trip
tests/unit/test_brief_shelf.py::test_shelf_route_refusals_name_the_cause
tests/unit/test_philo_4_01_generate.py::test_empty_brief_headline_is_no_changes
tests/unit/test_philo_4_01_generate.py::test_next_day_generate_keeps_the_old_brief_triage
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_is_a_two_row_face_walk
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_reads_latest_for_retention
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_ux_canon_ratchet.py::test_ratchet
tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
tests/unit/test_ux_canon_ratchet.py::test_ceiling_carries_its_date_and_reason
tests/unit/test_ux_canon_ratchet.py::test_healing
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
tests/unit/test_evidence_scratch_guard.py::test_allowlist_files_exist

90 tests collected in 0.70s


green-python: ['uv', 'run', '--no-sync', 'pytest', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
........................................................................ [ 80%]
............F.....                                                       [100%]
=================================== FAILURES ===================================
_________________________________ test_ratchet _________________________________

    def test_ratchet():
        """For every rule, the current hit count must be <= the ceiling count.
    
        Failure message names the rule, the delta, and the faces whose count
        rose — so a developer sees exactly what to fix.
        """
        ceiling = json.loads(CEILING_PATH.read_text())
        result = _get_scan()
        totals = result["totals"]
        face_rule_counts = result["face_rule_counts"]
        ceiling_faces = ceiling.get("faces", {})
    
        regressions: list[str] = []
        for rule, current in totals["per_rule"].items():
            ceiling_val = ceiling["per_rule"].get(rule, 0)
            if current > ceiling_val:
                delta = current - ceiling_val
                risen: list[str] = []
                for face, counts in face_rule_counts.items():
                    face_current = counts.get(rule, 0)
                    face_ceiling = ceiling_faces.get(face, {}).get(rule, 0)
                    if face_current > face_ceiling:
                        risen.append(f"  {face}: {face_ceiling} -> {face_current}")
                detail = "\n".join(risen) if risen else "  (no single face rose)"
                regressions.append(
                    f"{rule}: ceiling {ceiling_val} -> current {current} (+{delta})\n{detail}"
                )
    
>       assert not regressions, (
            "UX canon ratchet broken — new violations introduced:\n\n"
            + "\n\n".join(regressions)
            + "\n\nFix the violations, or if this is a deliberate trade-off, "
            "run: python scripts/ux_canon_scan.py --write-ceiling tests/ux_canon_ceiling.json"
        )
E       AssertionError: UX canon ratchet broken — new violations introduced:
E         
E         A8: ceiling 25 -> current 26 (+1)
E           ChairHome: 0 -> 1
E         
E         Fix the violations, or if this is a deliberate trade-off, run: python scripts/ux_canon_scan.py --write-ceiling tests/ux_canon_ceiling.json
E       assert not ['A8: ceiling 25 -> current 26 (+1)\n  ChairHome: 0 -> 1']

tests/unit/test_ux_canon_ratchet.py:89: AssertionError
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: "\(" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\("? A raw string is also an option.
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/unit/test_ux_canon_ratchet.py::test_ratchet - AssertionError: UX...
1 failed, 89 passed, 2 warnings in 3.71s
```

### Captured run — 2026-09-24T14:19:15Z

- **Command:** `python3 docs/internal/philo/phase-4/headline/verify_lane.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text

collect-python: ['uv', 'run', '--no-sync', 'pytest', '--collect-only', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
tests/unit/test_philo4_04_headline_storage.py::test_compose_fixture_has_the_ratified_headline
tests/unit/test_philo4_04_headline_storage.py::test_real_generate_shelf_and_latest_preserve_all_six_rows
tests/unit/test_brief_shelf.py::test_shelf_is_empty_before_any_triage
tests/unit/test_brief_shelf.py::test_acknowledge_survives_a_fresh_read
tests/unit/test_brief_shelf.py::test_defer_replaces_an_earlier_state
tests/unit/test_brief_shelf.py::test_clearing_returns_the_item_to_untouched
tests/unit/test_brief_shelf.py::test_unknown_item_and_state_are_refused_by_name
tests/unit/test_brief_shelf.py::test_shelf_routes_round_trip
tests/unit/test_brief_shelf.py::test_shelf_route_refusals_name_the_cause
tests/unit/test_philo_4_01_generate.py::test_empty_brief_headline_is_no_changes
tests/unit/test_philo_4_01_generate.py::test_next_day_generate_keeps_the_old_brief_triage
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_is_a_two_row_face_walk
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_reads_latest_for_retention
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_ux_canon_ratchet.py::test_ratchet
tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
tests/unit/test_ux_canon_ratchet.py::test_ceiling_carries_its_date_and_reason
tests/unit/test_ux_canon_ratchet.py::test_healing
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
tests/unit/test_evidence_scratch_guard.py::test_allowlist_files_exist

90 tests collected in 0.66s


green-python: ['uv', 'run', '--no-sync', 'pytest', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
........................................................................ [ 80%]
..................                                                       [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: "\(" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\("? A raw string is also an option.
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
90 passed, 2 warnings in 3.78s


collect-rendered: ['node_modules/.bin/vitest', 'list', 'src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx', 'src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx', 'src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx', 'src/desk/chair/__tests__/briefReceiptRendered202.test.tsx', 'src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx', 'src/desk/chair/__tests__/decisionRows.philo402.test.tsx']
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > shows the newest decision first with an honest cap and fold
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > keeps the result ordered after Generate replaces an existing brief
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > draws Generate in the head while a day-one row is untriaged
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > disables Generate while the read is open
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > says GENERATING… in the status slot and disables Generate while it runs
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > names a failed generation with no Retry and Generate enabled
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > says NO ANSWER when the generation got no response
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > keeps Retry on a failed read, with Generate in the head
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > keeps the badge, the caption and the receipt through every transition
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > never touches the old rows' triage when it generates
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > draws Generate on the quiet branch (every row triaged), not Generate again
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > puts a failed generation in the place of No brief yet
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says No brief yet only when the read answered null
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says READING… while the read is open
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > names a failed read with its status and Retry reads again
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says NO ANSWER when the fetch got no response
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > puts the period and the generated date under a populated brief
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > puts the date under an empty brief's headline too
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > shows an empty brief's own words and keeps Generate after a reload
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > names the destination on the row, before the press
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > still shows the receipt after the brief arrives and fills the face
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > keeps the receipt when the brief has nothing untriaged
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's badge (HS-202-02) > names the destination the hub actually uses
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's badge (HS-202-02) > carries the local scope, not a bare chip
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > says nothing before the verb is pressed
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > names what was built and when
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > never counts zero (UX-CANON A.8)
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > states one item in the singular
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the real six-row headline and date, then names all six handled
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > does not count THIS WEEK toward the Arrival handled line
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > withholds the line while one Arrival row is still untriaged
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > does not claim handling when a hidden raw-id Arrival row has no shelf
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps No changes bare without a zero handled count
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line in place while Generate is open
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line after generation failure
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line beside the same-day success receipt


green-rendered: ['node_modules/.bin/vitest', 'run', 'src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx', 'src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx', 'src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx', 'src/desk/chair/__tests__/briefReceiptRendered202.test.tsx', 'src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx', 'src/desk/chair/__tests__/decisionRows.philo402.test.tsx', '--maxWorkers=2']

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-04/web


 Test Files  6 passed (6)
      Tests  36 passed (36)
   Start at  08:19:22
   Duration  1.93s (transform 673ms, setup 273ms, import 1.39s, tests 722ms, environment 1.04s)



philo_graph_reference: ['uv', 'run', '--no-sync', 'python', 'scripts/philo_graph_reference.py', '--check']
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


philo_api_reference: ['uv', 'run', '--no-sync', 'python', 'scripts/philo_api_reference.py', '--check']
API reference drift: docs/generated/api-reference.json
```

### Captured run — 2026-09-24T14:20:09Z

- **Command:** `python3 docs/internal/philo/phase-4/headline/verify_lane.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text

collect-python: ['uv', 'run', '--no-sync', 'pytest', '--collect-only', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
tests/unit/test_philo4_04_headline_storage.py::test_compose_fixture_has_the_ratified_headline
tests/unit/test_philo4_04_headline_storage.py::test_real_generate_shelf_and_latest_preserve_all_six_rows
tests/unit/test_brief_shelf.py::test_shelf_is_empty_before_any_triage
tests/unit/test_brief_shelf.py::test_acknowledge_survives_a_fresh_read
tests/unit/test_brief_shelf.py::test_defer_replaces_an_earlier_state
tests/unit/test_brief_shelf.py::test_clearing_returns_the_item_to_untouched
tests/unit/test_brief_shelf.py::test_unknown_item_and_state_are_refused_by_name
tests/unit/test_brief_shelf.py::test_shelf_routes_round_trip
tests/unit/test_brief_shelf.py::test_shelf_route_refusals_name_the_cause
tests/unit/test_philo_4_01_generate.py::test_empty_brief_headline_is_no_changes
tests/unit/test_philo_4_01_generate.py::test_next_day_generate_keeps_the_old_brief_triage
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_is_a_two_row_face_walk
tests/unit/test_philo4_04_atlas_contracts.py::test_triaged_headline_case_reads_latest_for_retention
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_ux_canon_ratchet.py::test_ratchet
tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
tests/unit/test_ux_canon_ratchet.py::test_ceiling_carries_its_date_and_reason
tests/unit/test_ux_canon_ratchet.py::test_healing
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
tests/unit/test_evidence_scratch_guard.py::test_allowlist_files_exist

90 tests collected in 0.69s


green-python: ['uv', 'run', '--no-sync', 'pytest', '-q', 'tests/unit/test_philo4_04_headline_storage.py', 'tests/unit/test_brief_shelf.py', 'tests/unit/test_philo_4_01_generate.py', 'tests/unit/test_philo4_04_atlas_contracts.py', 'tests/unit/test_philo_graph_atlas.py', 'tests/unit/test_ux_canon_ratchet.py', 'tests/unit/test_evidence_scratch_guard.py']
........................................................................ [ 80%]
..................                                                       [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: "\(" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\("? A raw string is also an option.
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
90 passed, 2 warnings in 3.65s


collect-rendered: ['node_modules/.bin/vitest', 'list', 'src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx', 'src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx', 'src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx', 'src/desk/chair/__tests__/briefReceiptRendered202.test.tsx', 'src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx', 'src/desk/chair/__tests__/decisionRows.philo402.test.tsx']
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > draws Generate in the head while a day-one row is untriaged
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > disables Generate while the read is open
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > says GENERATING… in the status slot and disables Generate while it runs
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > names a failed generation with no Retry and Generate enabled
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > says NO ANSWER when the generation got no response
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > keeps Retry on a failed read, with Generate in the head
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > keeps the badge, the caption and the receipt through every transition
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > never touches the old rows' triage when it generates
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > draws Generate on the quiet branch (every row triaged), not Generate again
src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx > PHILO-4-01: Generate is always reachable on the Arrival > puts a failed generation in the place of No brief yet
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > shows the newest decision first with an honest cap and fold
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > keeps the result ordered after Generate replaces an existing brief
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the real six-row headline and date, then names all six handled
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > does not count THIS WEEK toward the Arrival handled line
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > withholds the line while one Arrival row is still untriaged
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > does not claim handling when a hidden raw-id Arrival row has no shelf
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps No changes bare without a zero handled count
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line in place while Generate is open
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line after generation failure
src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx > the triaged Arrival headline > keeps the line beside the same-day success receipt
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > shows an empty brief's own words and keeps Generate after a reload
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > names the destination on the row, before the press
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > still shows the receipt after the brief arrives and fills the face
src/desk/chair/__tests__/briefReceiptRendered202.test.tsx > Generate is badged before and receipted after (counsel 2) > keeps the receipt when the brief has nothing untriaged
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says No brief yet only when the read answered null
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says READING… while the read is open
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > names a failed read with its status and Retry reads again
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > says NO ANSWER when the fetch got no response
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > puts the period and the generated date under a populated brief
src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx > the BRIEF section: absent, loading, did not load, dated > puts the date under an empty brief's headline too
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's badge (HS-202-02) > names the destination the hub actually uses
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's badge (HS-202-02) > carries the local scope, not a bare chip
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > says nothing before the verb is pressed
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > names what was built and when
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > never counts zero (UX-CANON A.8)
src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx > the brief's receipt (HS-202-02) > states one item in the singular


green-rendered: ['node_modules/.bin/vitest', 'run', 'src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx', 'src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx', 'src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx', 'src/desk/chair/__tests__/briefReceiptRendered202.test.tsx', 'src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx', 'src/desk/chair/__tests__/decisionRows.philo402.test.tsx', '--maxWorkers=2']

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-04/web


 Test Files  6 passed (6)
      Tests  36 passed (36)
   Start at  08:20:16
   Duration  1.94s (transform 682ms, setup 273ms, import 1.41s, tests 731ms, environment 1.03s)



philo_graph_reference: ['uv', 'run', '--no-sync', 'python', 'scripts/philo_graph_reference.py', '--check']
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


philo_api_reference: ['uv', 'run', '--no-sync', 'python', 'scripts/philo_api_reference.py', '--check']
API reference checked


philo_boundary_census: ['uv', 'run', '--no-sync', 'python', 'scripts/philo_boundary_census.py', '--check']
Boundary candidate census checked


diff-check: ['git', 'diff', '--check']

Evidence churn: no ' M' paths under pm/roadmap/holdspeak/
```

### Captured run — 2026-09-24T14:20:54Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin:/Library/Apple/usr/bin:/Users/karol/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/codex-path:/Users/karol/.codex/tmp/arg0/codex-arg0fETbyu:/Users/karol/.kimi-code/bin:/Users/karol/.opencode/bin:/Users/karol/.local/bin:/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/dev/code/delivery-workbench/plugin/bin:/Users/karol/.claude/plugins/cache/claude-plugins-official/swift-lsp/1.0.0/bin HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.uDTyFRuUsz PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 1440 --engine none --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
[glass_infra] web bundle rebuilt in 4.5s
PASS: live
BRAIN: astra
SOURCE: e4cf7d086dc0ef30f0f5b128267d79ec787a0209 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:57622 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-_w35k8y9/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142054Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142054Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}
```

### Captured run — 2026-09-24T14:21:58Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin:/Library/Apple/usr/bin:/Users/karol/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/codex-path:/Users/karol/.codex/tmp/arg0/codex-arg0fETbyu:/Users/karol/.kimi-code/bin:/Users/karol/.opencode/bin:/Users/karol/.local/bin:/Users/karol/.nvm/versions/node/v22.21.0/bin:/Users/karol/dev/code/delivery-workbench/plugin/bin:/Users/karol/.claude/plugins/cache/claude-plugins-official/swift-lsp/1.0.0/bin HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HVgXhvDYQH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.philo404.arrival_triaged_headline.all_handled --brain astra --viewport 393 --engine none --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
PASS: live
BRAIN: astra
SOURCE: e4cf7d086dc0ef30f0f5b128267d79ec787a0209 dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-yOpsX1bz.js'] hub=http://127.0.0.1:57651 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zlpjv41k/.local/share/holdspeak/holdspeak.db engine=none
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142158Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142158Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/after.png']
NOTE: predicate: 'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}
```

### Captured run — 2026-09-24T14:22:40Z

- **Command:** `python3 docs/internal/philo/phase-4/headline/verify_observations.py pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142054Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-04-shots/20260924T142158Z-case.philo404.arrival_triaged_headline.all_handled-astra-393/observation.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ed91bf5c197d9d4ae76f43cc648d7670b8519ca1

```text
[
  {
    "run_id": "20260924T142054Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440",
    "case_id": "case.philo404.arrival_triaged_headline.all_handled",
    "viewport": 1440,
    "verdict": "PASS",
    "revision": "e4cf7d086dc0ef30f0f5b128267d79ec787a0209",
    "dirty": true,
    "brief_id": "brief-74e1d402996a45ba90a4ab6c1cebb75f",
    "headline": "2 decisions waiting.",
    "arrival_rows": 2,
    "handled_states": {
      "brief-item-ab74e466adfc4b848ba92b4eaf88b5d7": "deferred",
      "brief-item-69b58b7e9cb2402e80615af9d30e5df7": "acknowledged"
    },
    "headline_and_stored_items_unchanged": true,
    "stored_shelf_matches_face": true,
    "isolated_db": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-_w35k8y9/.local/share/holdspeak/holdspeak.db",
    "handled_line_geometry": {
      "x": 256,
      "y": 364,
      "w": 928,
      "h": 18
    },
    "all_nine_hit_points_owned": true,
    "initial_feedback": {
      "elapsed_s": 0.939,
      "text": "ALL 2 HANDLED",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}"
    },
    "terminal_outcome": {
      "state": "settled",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 364, 'w': 928, 'h': 18}",
      "pending_marker": null,
      "pending_marker_present": null,
      "elapsed_s": 1.081,
      "first_satisfied_at_s": 0.939,
      "completion_bound_s": 30.0,
      "late_result_s": null,
      "within_bound": true
    }
  },
  {
    "run_id": "20260924T142158Z-case.philo404.arrival_triaged_headline.all_handled-astra-393",
    "case_id": "case.philo404.arrival_triaged_headline.all_handled",
    "viewport": 393,
    "verdict": "PASS",
    "revision": "e4cf7d086dc0ef30f0f5b128267d79ec787a0209",
    "dirty": true,
    "brief_id": "brief-ba9ce5af35ea4ba9930ae6ad3eb707bc",
    "headline": "2 decisions waiting.",
    "arrival_rows": 2,
    "handled_states": {
      "brief-item-ff6da03c5a8e4647957541a3ad2f546c": "deferred",
      "brief-item-e3cd3e8cd5fb4dd395eb0aac79745684": "acknowledged"
    },
    "headline_and_stored_items_unchanged": true,
    "stored_shelf_matches_face": true,
    "isolated_db": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zlpjv41k/.local/share/holdspeak/holdspeak.db",
    "handled_line_geometry": {
      "x": 12,
      "y": 371,
      "w": 369,
      "h": 18
    },
    "all_nine_hit_points_owned": true,
    "initial_feedback": {
      "elapsed_s": 0.938,
      "text": "ALL 2 HANDLED",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}"
    },
    "terminal_outcome": {
      "state": "settled",
      "predicate_satisfied": true,
      "reading": "'ALL 2 HANDLED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 371, 'w': 369, 'h': 18}",
      "pending_marker": null,
      "pending_marker_present": null,
      "elapsed_s": 1.079,
      "first_satisfied_at_s": 0.938,
      "completion_bound_s": 30.0,
      "late_result_s": null,
      "within_bound": true
    }
  }
]
```

## Verification boundary and close

Astra read the final 90 Python / 36 rendered test outputs and inspected the
final before/after shots at 1440 and 393. The three story acceptance boxes
are supported by the [lane report](../../../../docs/internal/philo/phase-4/headline/lane-report.md)
and [readback proof](../../../../docs/internal/philo/phase-4/headline/observation-proof.json).
The failed earlier captures are retained: the A8 source guard was corrected
without changing the ceiling, and generated references were refreshed. The
final verification capture at `2026-09-24T14:20:09Z` exits 0. The final
observation verifier capture at `2026-09-24T14:22:40Z` exits 0.

Only scoped tests ran, under isolated HOMEs; no metal test or full suite.
The rig used real producer routes and face gestures in isolated hubs; no
model was needed. The owner's sitting was waived and no owner observation
is claimed. PR #627 remains open for Muad'Dib's counsel on built.
