# Workbench picker adoption audit

DRAFT — awaiting Muad'Dib. Source census at base `91275406b`, with the
Thread adoption described below. Paths in the tables start at `web/src/`;
line anchors are from the base unless a row says otherwise. Shared kit
changes can move their anchors.

## Coverage and ownership

The active source census found 46 CycleGadget JSX callsites, one legacy
Signal Select callsite, and one raw face select. The raw face was the
Thread elicitation enum. Two further native select implementations belonged
to the shared kit: `components/signal/Signal.tsx:129` and
`desk/surface/gadgets.tsx:180`.

The census used a TypeScript AST walk of active `.ts/.tsx/.js/.jsx` sources
under `web/src`, excluding test/spec, parked and generated paths. Searches
also checked aliases, `HTMLSelectElement`, DOM/React `createElement`, HTML
injection and `web/index.html`, `web/public`, and `web/scripts`. No aliased
picker import or additional native select construction was found. The
non-JSX `createElement` calls create receipts, buttons, canvas, input,
audio, links and measurement spans; none creates a select. Test scaffolds,
parked faces and the gallery's repeated rendered instances are not extra
source callsites.

After the scoped change, the Thread enum is the 47th CycleGadget callsite.
Interview retains the sole legacy Select callsite and adopts through its
shared wrapper. No face owns popup code. Settings also has four `cyc(...)`
uses of its one CycleGadget helper; these are listed separately below.

## Complete face census

`Disabled` below means the control's existing disabled condition. The
option column names any unavailable row and lists with unbounded size or
labels. A dash means the callsite supplies no disabled condition. Every
CycleGadget inherits the shared off-roster rule: retain and name an unknown
current value without writing a replacement. Static lists can still receive
old values from persisted configuration; dynamic rosters can lose entries.

| Source | Label | Value and writer owned by face | Options and size | Disabled |
| --- | --- | --- | --- | --- |
| `desk/components/DeliveryBoard.tsx:223` | Agent | `profileId` → `setProfileId` | Profile roster; unbounded labels/list | — |
| `desk/components/InfoWindow.tsx:222` | `p.label ?? p.key` | `p.value(o)` → `p.set(o,next)` | Property choices from objects/items; unbounded | — |
| `desk/components/InterviewPanel.tsx:57` | Section, external label/id | `state.section` → `change({kind:"section",section})` | `state.sections`; unbounded names/list; legacy Select | `disabled || pending` |
| `desk/components/RepoWindow.tsx:197` | Branch | `branch` → existing checkout/refresh/retry chain | Branch roster; unbounded names/list | — |
| `desk/components/ScheduleCreateWindow.tsx:177` | Mode | `mode` → `setMode` | Once / Recurring | — |
| `desk/components/ScheduleCreateWindow.tsx:208` | Duration | `duration` → `setDuration` | 15/30/60/90/120 minute values | — |
| `desk/components/SessionPullout.tsx:229` | Node | `targetNode || ""` → steering `setTargetNode(v || null)` | Empty = this Mac, then node roster; unbounded names/list | No nodes |
| `desk/pullouts/ThreadPullout.tsx:191` | Schema title/key; required `*` | `String(values[key] ?? "")` → `handleChange(key,next)` | Empty `--`, then exact `String(v)` enum values; schema-sized/unbounded labels; migrated at line 190 | — |
| `desk/pullouts/editors/RecipeEditor.tsx:96` | Knowledge | `f.kbId` → `set("kbId","kb_id",value)` | Empty = No Knowledge, then knowledge roster; unbounded | — |
| `desk/thought-workspace/ProjectWell.tsx:43` | Project | `projectId` → `setProjectId` | Project roster; fallback Untitled project; unbounded | `busy` |
| `desk/thought-workspace/TaskWell.tsx:69` | Who | `owner` → `setOwner` | Me + named people; unbounded names/list | `busy` |
| `features/project-room/ProjectRoomCore.tsx:2302` | Result | `"answer"` → `onPrepare(prompt)` only for brief | Answer / Preparation brief | — |
| `features/project-room/prepare/PreparePosture.tsx:165` | Result | `"brief"` → `onResultChange(ctrl.purpose)` only for answer | Same two result options | — |
| `meetings/MeetingSendWell.tsx:43` | Document | `kind` → existing destination carryover, formPick, keepPlace, setKind | Summary / Digest / Follow-up via `MEETING_FORMS` | — |
| `pages/cores/CadenceCore.tsx:374` | Sweep interval | String minutes → `putSetting({sweep_every_minutes:parseInt(v,10)})` | 5/15/30/60 minutes | `saving || sweeping` |
| `pages/cores/CadenceCore.tsx:437` | Runner host | `settings.runs_on || "local"` → `putSetting({runs_on:v})` | Local + remote host roster; unbounded | `saving || sweeping` |
| `pages/cores/CadenceCore.tsx:559` | Notification mode | `settings.notify` → `putSetting({notify:v})` | off / edge / every_sweep | `saving || sweeping` |
| `pages/cores/CalendarSnapshotReviewCore.tsx:231` | Event weekday | `event.weekday` → `updateEvent(index,{weekday:next})` | Seven weekday values; repeated event rows | — |
| `pages/cores/CommandsCore.tsx:242` | Command behavior | Macro action kind → existing `setEditing` nested update | open_url / launch_app / shell / type_text | — |
| `pages/cores/ComponentsCore.tsx:143` | Gallery pick | `cycle` → `setCycle` | Automatic / On device / Held; **Held unavailable** | — |
| `pages/cores/ConstitutionalContextCore.tsx:121` | Version history | `version` → exitHistory / restoreRevision | current + revision history; unbounded list | — |
| `pages/cores/LiveCore.tsx:502` | Intent routing preset | Profile → existing profile PUT and reload | auto / off / balanced / aggressive | — |
| `pages/cores/ModelLibraryCore.tsx:393` | Hosted provider | `hosted.family` → `setHosted` | OpenRouter / Anthropic | — |
| `pages/cores/ModelLibraryCore.tsx:415` | Endpoint provider | `endpoint.family` → `setEndpoint` | OpenAI-compatible / Private endpoint / Future backend | — |
| `pages/cores/PeopleCore.tsx:1292` | Visibility | `visibility` → `setVisibility` | Leader private / Shared | — |
| `pages/cores/PeopleCore.tsx:1296` | Project | `projectId` → `setProjectId` | Project roster; unbounded names/list | — |
| `pages/cores/PeopleCore.tsx:1325` | Workbench | `workbenchId` → `setWorkbenchId` | Workbench roster; unbounded names/list | — |
| `pages/cores/SettingsCore.tsx:960` | Remote transport | ON/OFF → `toggleEnabled` | OFF / ON | `toggleBusy || loading` |
| `pages/cores/SettingsCore.tsx:1200` | Access | `issuePalette` → `setIssuePalette` | PROJECT / SWEEP / DESK / ALL | — |
| `pages/cores/SettingsCore.tsx:1208` | Expires after | `issueTtl` → `setIssueTtl` | 43200/86400/604800/2592000 seconds | — |
| `pages/cores/SettingsCore.tsx:1704` | Generic `cyc` label | `val(path)` as string/empty → `update(path,next)` | Caller options; four uses below | — |
| `pages/cores/SettingsCore.tsx:1871` | Attachment | `entry.attach ?? "none"` → `patchSymbol(index,{attach:next})` | none / left / right / both; repeated symbol rows | — |
| `pages/cores/SettingsCore.tsx:2027` | Auto-record mode | `autoRecordValue` → `update(["meeting","auto_record"],next)` | off / room_linked / all_calendar | — |
| `pages/cores/SettingsCore.tsx:2094` | Auto-run the summary | `autoVal` → `update(["meeting","intelligence_auto"],next)` | off / room_linked / every | — |
| `pages/cores/SettingsCore.tsx:2239` | Export format | String export format, default markdown → config update | txt / markdown / json / srt | — |
| `pages/cores/connections/Destinations.tsx:204` | Channel | `d.channel` → existing EMPTY draft + channel update | Folder / GitHub / Jira / Confluence / Email / Slack | — |
| `pages/cores/connections/Destinations.tsx:220` | Kind | `d.kind` → draft `set({kind})` | issue / pr | — |
| `pages/cores/connections/Destinations.tsx:227` | Jira account | `jiraAcc` → `set({jiraAccount:v})` | `site|email` values, `site · email` labels; unbounded and long | — |
| `pages/cores/connections/Destinations.tsx:239` | Confluence account | `confAcc` → `set({confAccount:v})` | Same account value/label format; unbounded and long | — |
| `pages/cores/connections/Destinations.tsx:248` | Provider | `d.provider` → clear key refusal + draft provider update | Canonical `EMAIL_PROVIDERS` table | — |
| `pages/cores/dictation/Blocks.tsx:104` | Block scope | `scope` → `setScope` | global / project | — |
| `pages/cores/dictation/SpeakFace.tsx:549` | Aim | `deck.aim` → `deck.pickAim` | focused / agent / field | — |
| `pages/cores/dictation/SpeakFace.tsx:620` | Correction field | `deck.correctionKind` → `deck.pickCorrectionKind` | text / intent / target | — |
| `pages/cores/dictation/SpeakFace.tsx:642` | Correction target/intent | `deck.correctionValue` → `deck.setCorrectionValue` | Target overrides or intent block roster; long/unbounded. Existing deck normalizes value to roster | — |
| `pages/cores/history/DoorSection.tsx:57` | Queue status | `queueStatus` → set + scheduled intel/plugin reload | pending / running / failed / complete | — |
| `pages/cores/history/MeetingDetail.tsx:483` | Who? | `draft.owner` → `setDraft(row,"owner",value)` | Empty Who? + Me + named people; unbounded names/list | `data.busy` |
| `pages/cores/history/MeetingsConfig.tsx:96` | Export format | String export format, default txt → `update("export_format",next)` | txt / markdown / json / srt | — |
| `pages/cores/settingsPrefs.tsx:562` | Control posture | `posture` → `onPosture` | Canonical CONTROL_MODES with labels | `postureBusy` |

### Settings helper uses

| Source | Label and path | Options |
| --- | --- | --- |
| `pages/cores/SettingsCore.tsx:1818` | Language, `model.language` | auto + full Whisper language catalog; long list; code values and name/code labels |
| `pages/cores/SettingsCore.tsx:1829` | Action, `wake_word.action` | preview / type |
| `pages/cores/SettingsCore.tsx:2293` | Routing profile, `meeting.routing_profile` | balanced / architect / delivery / product / incident |
| `pages/cores/SettingsCore.tsx:2345` | Pressure, `cadence.pressure` | gentle / normal / aggressive |

## Scoped adoption and verification

Thread now composes CycleGadget. The existing external label and required
asterisk remain, and the same label/asterisk is the control's accessible
name. Empty `--`, all `String(v)` values, and the `handleChange` writer are
preserved. No validation, other field species, submit logic or form state
changed. The former select CSS stays parked in place.

Interview requires no face edit: its label/id, value, disabled state and
event writer already fit the legacy wrapper, which the kit lane owns.

The focused files are `desk/__tests__/ThreadToolRows.test.tsx` (elicitation
rendering), `desk/__tests__/askai.app.test.tsx` (Submit/Decline through the
real thread store), and `desk/__tests__/InterviewPanel.test.tsx` (section
writer and disabled control). One new regression in askai checks the blank
sentinel, required name, exact enum string values and explicit Submit
payload. It failed before adoption because the raw select had no accessible
name: `1 failed | 9 skipped (10)` in `adoption-before.log`.

Collection used the isolated-HOME lock helper:

```sh
.venv/bin/python .tmp/workbench-pickers/locked.py adoption-collect --web ./node_modules/.bin/vitest list src/desk/__tests__/ThreadToolRows.test.tsx src/desk/__tests__/askai.app.test.tsx src/desk/__tests__/InterviewPanel.test.tsx
```

It exited 0 and listed 65 tests. Relevant collected names include:

```text
src/desk/__tests__/askai.app.test.tsx > Ask AI: the decision box sends the owner's decision > elicitation enums keep their empty choice and submit the selected string value
src/desk/__tests__/ThreadToolRows.test.tsx > ThreadPullout tool rows > renders elicitation form with Submit / Decline
src/desk/__tests__/InterviewPanel.test.tsx > Interview controls > revisits one section with the current revision before reloading
src/desk/__tests__/InterviewPanel.test.tsx > Interview controls > disables configuration controls while the conversation is running
```

The same helper ran exactly those three files with `vitest run` and
`--maxWorkers=1`; `adoption-tests.log` ended:

```text
 Test Files  3 passed (3)
      Tests  65 passed (65)
   Start at  00:02:40
   Duration  3.43s (transform 603ms, setup 177ms, import 1.15s, tests 1.21s, environment 659ms)
```

Logs are under `.tmp/workbench-pickers/`. This run verified face adoption
against the shared core present at that time; the root lane runs the
combined check after kit integration. No pytest, build, full suite or
browser walk ran in this lane.

Source census proves callsite coverage, not live behavior on every face.
The root lane owns the combined quick check, shared popup review and
production shots at 1440 and 393. No owner visual acceptance is inferred.
