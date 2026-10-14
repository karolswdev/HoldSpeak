# Tools and configuration — existing surface audit

DRAFT — HOLD FOR SHIP. UNCHECKED — awaiting Muad'Dib.

Base: `6e86c666ae15c23241f427ca98981a83c5978d92` (#1199). Read-only product audit. No product, test or package changes. Findings use current source and October 14 isolated-hub captures; October 13 designs are design evidence, not runtime evidence.

The main obstacle is still reaching first use: first run presents a 3.0 GB bundle before the speech-only job, and Engines puts the existing-server choices after downloads and six other jobs. The smaller Settings modules are more orderly at 1440, but the unseen Meetings module breaks at 393. Several action handlers also make claims that their persistence does not support.

## Evidence and limits

`G` below means `.tmp/evidence-shots/desk-sweep/`; `T` means `.tmp/surface-audit/tools/`. Root's single general run produced 109 PNGs and reported 106 passed / 3 existing xfails. I inspected this lane's faces, including wings and the scoped Engines/Accounts captures. This establishes rendering and the sweep's mechanical checks, not usable operations.

The authorized supplementary pass reused `test_desk_sweep`'s hub/browser fixtures and existing page/settle/open helpers, under `scripts/test_lock.py`, isolated HOME and machine-state switches. It captured eight poses at both widths, without starting download, discovery, dictation, credential or external-account actions. `T/capture.log`: `1 passed in 30.36s`; all 16 poses reported no page errors. The fixture seeds synthetic projects, calendar events, accounts and agent records. This is not the owner's DB or a wholly empty installation.

An early Engines wing image (`G/surface-settings-393-Engines.png`) is blank while the roster read is pending. The separately scoped `G/surface-settings@models-393.png` and supplemental lower capture are populated. I do **not** classify Engines as permanently blank. The new Settings host and the single Engines footer are present in current source (`SettingsCore.tsx:2387`, `:2522`); the old ghost and double-footer findings are not repeated.

## Ranked findings

### 1. First run makes the large bundle the first job

**Evidence:** `T/first-run-1440.png`, `T/first-run-393.png`; `web/src/desk/firstrun/FirstRun.tsx:198` offers **Set up local AI · 3.0 GB**. The 144 MB speech-only verb is conditional on `lanOpen || lanUsed` at `:217`. Speech alone enables First words at `:440`; the initial page nevertheless mounts Local AI, You, First words, Calendar, Connections and Agents at `:503`. At 393 the first screen ends in You; First words and Continue later are below it. The dark standalone cards also change the visual grammar from the Workbench desk (`firstrun.css:4`, `:32`).

**Owner cost:** a person who wants to dictate first is led toward downloading chat and search models before seeing the smallest usable path. A server owner must choose the network branch to expose that speech-only path. The six-card page introduces setup decisions before the first sentence.

**Fails:** Tenets **2, 3, 6, 7**; UX-CANON A.5 and A.12. **Repair:** make Set up speech the initial primary, keep First words adjacent to it, expose Use a server and local chat as explicit alternatives, and fold optional calendar/accounts/agent setup. Use the desk's current material. **Confidence:** high for rendered order and source conditions; download duration and a real microphone were not observed.

### 2. Engines hides the owner's existing-server route behind downloads

**Evidence:** `G/surface-settings@models-1440.png`, `G/surface-settings@models-393.png`, `T/engines-lower-1440.png`, `T/engines-lower-393.png`. Both initial views lead with speech setup and two local Qwen download cards. Find on LAN and Add an engine appear after Other jobs, including six unassigned rows. `web/src/features/runson/RunsOnCore.tsx:388` places those verbs in `engineFoot`, passed into the switchboard at `:459`; the first local preset becomes the primary at `:204`. The LAN capability is implemented; this is a placement finding.

**Owner cost:** the owner who already has a server sees a download recommendation first and must scroll past job configuration he cannot complete yet. The default 640 px Settings window gives the 1440 workstation the same long list problem as the phone (`web/src/desk/applications.ts:197`).

**Fails:** Tenets **2, 3, 7**; UX-CANON A.5. **Repair:** put Find on LAN / Add an engine immediately under No engine yet; follow with saved/found engines and an explicit Use it. Show job assignment after an engine exists. Fold the local download catalog under Download a local model. **Confidence:** high for both widths; discovery results, assignment and inference were not exercised.

### 3. Meetings settings controls overlap the next section at 393

**Evidence:** `T/settings-meetings-393.png` versus `T/settings-meetings-1440.png`. On the phone the Summary cycle, NO MODEL chip and Choose model button cross the Capture + export heading and Mic device label. The three controls are siblings in one `GadgetRow` at `web/src/pages/cores/SettingsCore.tsx:2036`; the next section begins at `:2063`. The library stacks the row below 420 px but leaves its gadget children in a single flex line (`web/src/desk/surface/gadgets.css:80`, `:87`).

**Owner cost:** the owner cannot read the setting boundaries reliably while choosing summary behavior or a capture device. This inner module was absent from the green wing sweep.

**Fails:** Tenets **5, 6**; UX-CANON D's content fitting. **Repair:** make the library row contain the controls' full painted and hit height; wrap or stack this multi-control group under the surface container breakpoint. Keep the following section below the completed row. **Confidence:** high for visible overlap; pointer ownership was not measured and is not claimed.

### 4. Rhythm has a no-effect choice and a false write receipt

**Evidence:** `G/surface-cadence-1440.png`, `G/surface-cadence-393.png` show COUNT ONLY and WRITTEN. Notification content is only React state (`web/src/pages/cores/CadenceCore.tsx:220`, `:547`); its only handler is `setNotifyContent`. The actual notification service always passes `notify_content=False` (`holdspeak/services/heartbeat_service.py:1011`). Separately, `putSetting` sets `writtenAt` before its PUT completes (`CadenceCore.tsx:243`), and the footer falls back to the last sweep time or the current clock when no edit occurred (`:675`). Run now / Generate use `try/finally` without an error receipt (`:250`, `:264`).

**Owner cost:** choosing ROOM NAMES changes the gadget without changing notifications and resets on remount. WRITTEN does not prove that any setting was saved; failed writes/runs have no truthful face-level result through these handlers.

**Fails:** Tenets **3, 7**; Constitution VI.1–3 and UX-CANON A.10–11. **Repair:** park Notification content until a real saved setting feeds the service. Set a write receipt only after the write succeeds; show Saving / Not saved and named run failures. Do not use wall time as a write timestamp. **Confidence:** high from complete handler-to-service source; refused writes and notification delivery were not injected or observed.

### 5. Speak's configuration door exposes debug output as the repair

**Evidence:** `G/surface-dictation-393-Configure_dictation.png` prints the complete temporary missing-model path, including artifact hash and GGUF filename, for about eight lines between Pipeline and Delivery. `web/src/pages/cores/dictation/Readiness.tsx:104` renders `warning.message` directly in the main sheet. Configuration stacks Readiness, Memory, Knowledge, Runtime, Hooks and Nudges (`web/src/pages/cores/DictationCore.tsx:50`), while the useful **Choose** repair already exists on Speak (`dictation/SpeakFace.tsx:385`).

**Owner cost:** the person looking for a fix is given an implementation path and several unrelated diagnostic sections; no action accompanies that warning. The missing-model diagnosis is useful, but the path is not the job.

**Fails:** Tenets **2, 3, 4**; UX-CANON A.3 and A.10. **Repair:** render Model missing plus the same scoped Choose engine repair used on Speak. Put the path and raw response under RAW. Fold nonessential diagnostics and keep only the current failure and its repair above them. **Confidence:** high for the observed error; actual repair and subsequent dictation were not run.

### 6. Commands discards the editor after a failed save

**Evidence:** face context `G/surface-commands-1440.png` / `G/surface-commands-393.png`; the failing action state is **source-only**. `web/src/pages/cores/CommandsCore.tsx:62` catches PUT failures and sets a message without returning failure or rethrowing. `save` then unconditionally calls `setEditing(null)` after `await persist(next)` at `:106`.

**Owner cost:** a rejected or unavailable save closes the well and drops the typed command from component state. The owner must reconstruct the keyword and payload to retry.

**Fails:** Tenets **3, 7**; Constitution VI.1 and UX-CANON A.10. **Repair:** return a success result from persistence and close the well only after success. Keep the draft and its fields beside a named failure. **Confidence:** high for control flow; failure behavior was not reproduced in a browser during this audit.

### 7. Setup and Guide duplicate the same readiness job with different repairs

**Evidence:** `G/surface-setup-1440.png`, `G/surface-setup-393.png`, `G/surface-settings@integration_destinations-1440-Guide.png`, `G/surface-settings-393-Guide.png`. Both read `/api/setup/status` (`web/src/pages/cores/SetupCore.tsx:41`, `RuntimeDocsCore.tsx:119`). Setup leads with BLOCKED and Test runtime, lays ready and failing checks in one long ledger and puts Get ready / Runs on in a separate Next step panel (`SetupCore.tsx:88`, `:176`). Guide already folds ready checks and places the engine repair on its failing row (`RuntimeDocsCore.tsx:74`, `:169`). At 393 Setup's Next step panel is below the long checks.

**Owner cost:** the owner must learn that Setup and Settings → Guide show the same underlying doctor with different actions. A failed engine check is directly fixable on one face and only an indirect side-panel door on the other.

**Fails:** Tenets **2, 3**; UX-CANON A.5 and A.10. **Repair:** let Guide's existing readiness component own both entry points; park the duplicate Setup body. Keep Get ready as a clear secondary action on that same readiness face and use Engines consistently. **Confidence:** high for current rendering and shared endpoint; runtime-test execution was not observed.

## Face coverage

“Rendered” means the named pose/first visible slice, not every scroll position or action. RAW folds remain source-only unless stated.

| Face | 1440 / 393 | Observed state and evidence | Missing state coverage |
|---|---|---|---|
| Settings home / More settings | Rendered / rendered | No engine, two accounts; `G/surface-settings-393.png`, `T/settings-more-{width}.png` | More ledger lower rows; save/error |
| Settings → Voice | Rendered / rendered | Defaults, empty symbols; `T/settings-voice-{width}.png` | Hotkey capture, added symbols, wake, RAW, writes |
| Settings → Sounds & Presence | Rendered / rendered | Browser voice, no server TTS extra; `T/settings-sounds-{width}.png` | Installed TTS, download/error, toggles |
| Settings → Wallpaper | Source-only host | Shared picker rendered through Places; `SettingsCore.tsx:1930` | This module's host, lower toggles, selections |
| Settings → Meetings | Rendered / rendered | No model, one calendar source; `T/settings-meetings-{width}.png` | Calendar edit/remove/snapshot, capture, writes, RAW |
| Settings → Rhythm | Rendered / rendered | Cadence defaults, morning Brief on; `T/settings-rhythm-{width}.png` | Writes, RAW, Telegram action |
| Settings → System | Rendered / rendered | Other devices off; `T/settings-system-{width}.png` | Remote credentials/receipts, desk reset, RAW |
| Settings → People | Source-only | `settingsPeople.tsx:72`, `:101` | Both rendered widths, access change/error, aliases |
| Settings → Engines | Rendered / rendered | No configured engine; local presets and lower controls; `G/surface-settings@models-{width}.png`, `T/engines-lower-{width}.png` | Saved/found engine, Add well, LAN results, download, assignment, Try it, error |
| Settings → Accounts / destinations | Rendered / rendered | Synthetic GitHub/Jira connected; Confluence/calendar not set; destination list at 1440; `G/surface-settings@integration_destinations-1440.png`, `G/surface-settings-393-Accounts.png` | Add account/destination, recheck failure, destination detail; 393 lower destination/credentials |
| Settings → Guide | Rendered / rendered | Five failing/warning checks; `G/surface-settings@integration_destinations-1440-Guide.png`, `G/surface-settings-393-Guide.png` | Show fix/RAW, Ready fold, Test runtime result |
| Setup | Rendered / rendered | Blocked, failure/warnings and ready rows; `G/surface-setup-{width}.png` | Runtime-test result, recovery, phone lower panel |
| First run | Rendered / rendered | Initial model/name/words cards; seeded calendar/accounts/agents; `T/first-run-{width}.png` | Wholly cold machine, download, LAN well, heard/kept/ready/errors; phone lower cards |
| Speak | Rendered / rendered | Speech missing, engine not set; `G/surface-dictation-{width}.png` | Real capture, landing, teach/result, configured engine/error |
| Speak → Journal / Learned / Blocks | Rendered / rendered | Empty journal/learning/block library; corresponding `G/surface-dictation-{width}-{Journal,Learned,Blocks}.png` | Populated rows, correction, forget, block add/edit |
| Speak → Configure | Source-only / rendered | Missing-model error in first slice; `G/surface-dictation-393-Configure_dictation.png` | 1440 door, lower Knowledge/Runtime/Hooks/Nudges, actions/RAW |
| Commands | Rendered / rendered | Disabled, empty; `G/surface-commands-{width}.png` | Editor/populated/test/delete, rejected save |
| Rhythm application | Rendered / rendered | Scheduled, quiet-held, populated Brief/projects, no loop rows; `G/surface-cadence-{width}.png` | Writes/refusals, sweep/generate result, active loops/reply |
| Activity → Records / Rules | Rendered / rendered | Empty; corresponding `G/surface-activity-{width}[-Rules].png` | Populated records/rules, filter/action results; gear Candidates/Connectors source-only |
| Context | Rendered / rendered | Empty editor; `G/surface-constitutional-context-{width}.png` | Saved/history/restore/failure; `ConstitutionalContextCore.tsx:158` still shows rev 0 / ~0 tokens |
| Places compatibility window | Rendered / rendered | Preset picker, first slice; `G/surface-places-{width}.png` | Choose/favorite, lower controls. Motion/sound remain exposed in source (`settingsWallpaper.tsx:128`) although Screen uses a still (`screen/Screen.tsx:132`) |
| Components internal gallery | Rendered / rendered | First specimen slice; `G/surface-components-{width}.png` | Lower specimens/interactive samples; no owner-job claim |
| Retired Engines/Accounts hosts; old routes | Parked hosts; routes source-only | Registry parks `surface-concierge` (`applications.ts:366`) and Accounts compatibility row (`:478`). `/models`, `/profiles` → Settings Engines; `/studio` → Settings; `/docs/dictation-runtime` → Guide (`routes.tsx:71`) | Deep-link press behavior not separately walked. Legacy Agents belongs to conductor audit |

No real microphone, LAN scan, model download, provider credentials, notification, command execution or owner desk was used. Populated speech history/learning, configured Engines, People preferences, and most refusal/action states remain unverified. The green sweep cannot fill these gaps.

## Smallest coherent repair order

1. Fix the current phone overlap and action truth: Meetings row fitting, Rhythm's false/no-effect controls, Commands' retained draft, and Speak's named repair.
2. Put server discovery ahead of the download catalog in Engines, then make first run use the same compact engine choice and speech-only start.
3. Fold Setup into the existing Guide readiness face. Keep the Components gallery internal; keep old route aliases as compatibility. Park Places' unsupported animation/sound controls and use the existing Wallpaper module for the actual still picker. Do not create another setup application.

## Recommended layout for the worst face: First run

Use one **Get ready** Desk window in the current Workbench material. Its first plate is **Speech**: one readiness line, the `huggingface.co` egress chip beside **Set up speech · 144 MB**, then First words in that same plate. After speech is present, **Dictate one sentence** becomes its primary; the returned sentence replaces the empty well and **Keep as note** becomes the next action. Put **Continue later / Open my desk** in the visible frame foot throughout.

Below Speech, show a compact **Engine** row with **Find on LAN** and **Add an engine**; a found result shows model/host and **Use it** inline. Fold the local chat/search catalog under **Download a local model**. Keep the **Your name** field beside the speech plate at 1440 and directly below it at 393. Calendar, Accounts and Agents fold under **More setup** with their current real controls. The 393 order is Speech → Your name → Engine → More setup; the first screen and fixed foot expose the first sentence and a way onto the desk. Preserve the existing operations and receipts; park the six-card primer layout. This is the audit's recommended direction, awaiting Muad'Dib and owner review.
