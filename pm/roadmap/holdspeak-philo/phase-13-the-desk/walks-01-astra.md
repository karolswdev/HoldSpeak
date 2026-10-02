# B0 actual runs — DRAFT, UNCHECKED — awaiting Muad'Dib

Every row is one `scripts/graph_walk.py run` invocation, not a direct Playwright walk. Astra read the observation and all its shots before the next invocation. The original directory is `.tmp/graph-walk/philo-13-01/<label>/<timestamp-case>/`; linked copies keep that directory structure. Every file hash is in [manifest.json](assets/story-01-walks/manifest.json). The observations are unedited. Product revision is `b870df2d`, dirty with this lane's atlas/rig work; product code and built bundle remain from `27b915538`. These are not runs on merged main.

| Path | Width | Rig verdict | Observation (shots in same folder) |
|---|---|---|---|
| chain | 1440 | blocked | [chain-1440-r4](assets/story-01-walks/final/chain-1440-r4/20261002T022602Z-case.p13.chain.pullout-astra-1440/observation.json) |
| chain | 393 | blocked | [chain-393-r2](assets/story-01-walks/final/chain-393-r2/20261002T022651Z-case.p13.chain.pullout-astra-393/observation.json) |
| roadmap | 1440 | blocked | [roadmap-1440-r1](assets/story-01-walks/final/roadmap-1440-r1/20261002T023023Z-case.p13.roadmap.window-astra-1440/observation.json) |
| roadmap | 393 | blocked | [roadmap-393-r1](assets/story-01-walks/final/roadmap-393-r1/20261002T023104Z-case.p13.roadmap.window-astra-393/observation.json) |
| repository | 1440 | fail | [repository-1440-r3](assets/story-01-walks/final/repository-1440-r3/20261002T023553Z-case.p13.repository.window-astra-1440/observation.json) |
| repository | 393 | pass | [repository-393-r2](assets/story-01-walks/final/repository-393-r2/20261002T023517Z-case.p13.repository.window-astra-393/observation.json) |
| dossier | 1440 | pass | [dossier-1440-r1](assets/story-01-walks/final/dossier-1440-r1/20261002T023709Z-case.p13.delivery.dossier_window-astra-1440/observation.json) |
| dossier | 393 | fail | [dossier-393-r1](assets/story-01-walks/final/dossier-393-r1/20261002T023743Z-case.p13.delivery.dossier_window-astra-393/observation.json) |
| coder | 1440 | blocked | [coder-1440-r1](assets/story-01-walks/final/coder-1440-r1/20261002T023915Z-case.p13.coder.pullout-astra-1440/observation.json) |
| coder | 393 | blocked | [coder-393-r1](assets/story-01-walks/final/coder-393-r1/20261002T024004Z-case.p13.coder.pullout-astra-393/observation.json) |
| calendar | 1440 | blocked | [calendar-1440-r2](assets/story-01-walks/final/calendar-1440-r2/20261002T024211Z-case.p13.calendar.snapshot_window-astra-1440/observation.json) |
| calendar | 393 | blocked | [calendar-393-r1](assets/story-01-walks/final/calendar-393-r1/20261002T024248Z-case.p13.calendar.snapshot_window-astra-393/observation.json) |
| terminal | 1440 | pass | [terminal-1440-r1](assets/story-01-walks/final/terminal-1440-r1/20261002T024329Z-case.p13.delivery.terminal_window-astra-1440/observation.json) |
| terminal | 393 | fail | [terminal-393-r1](assets/story-01-walks/final/terminal-393-r1/20261002T024412Z-case.p13.delivery.terminal_window-astra-393/observation.json) |
| zone | 1440 | blocked | [zone-1440-r1](assets/story-01-walks/final/zone-1440-r1/20261002T024858Z-case.p13.directory.zone-astra-1440/observation.json) |
| zone | 393 | blocked | [zone-393-r1](assets/story-01-walks/final/zone-393-r1/20261002T025027Z-case.p13.directory.zone-astra-393/observation.json) |
| info | 1440 | blocked | [info-1440-r1](assets/story-01-walks/final/info-1440-r1/20261002T025101Z-case.p13.info.window-astra-1440/observation.json) |
| info | 393 | blocked | [info-393-r1](assets/story-01-walks/final/info-393-r1/20261002T025156Z-case.p13.info.window-astra-393/observation.json) |

The verdicts are 3 pass, 3 fail, 12 blocked. [Findings](findings-01-astra.md) distinguish product failures from input/rig limits. The three passes are Repository at 393, Dossier at 1440, and Terminal at 1440. They certify the named close/reload/reopen and readable-content checks; visual defects outside those checks remain ledgered.

Inputs: real directory/chain HTTP producers; real temporary Git/DW repository for Roadmap/Repository/Delivery; real agent-hook ingestion of a declared transcript input for Coder; real isolated tmux factory-spawn for Terminal; native Calendar file chooser. All 18 DB paths were verified below their run HOME. The phone contexts use native touch. Info's right-button step explicitly blocks instead of falling back to mouse. Calendar has no vision model in engine-none mode. The Zone control does not accept this case's focus/tap. No full engine success or native touch completion is claimed for those blocked legs.
