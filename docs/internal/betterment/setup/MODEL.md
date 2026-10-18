# Settings and setup: the code map

Status: read from code on 2026-10-17 at the head of the owner's desk
(`217001b2e`). All paths are under the repository root. Engines is mapped in
`../engines/MODEL.md` and is left out here.

## 1. What each feature is in data

### Settings

- **One config file**, `~/.config/holdspeak/config.json`
  (`holdspeak/config/core.py:39-40`). The `Config` dataclass has the top-level
  keys `hotkey, model, ui, meeting, dictation, device, presence, wake_word,
  mesh, cadence, cadence_telegram, rails_observer, thoughts, calendar, owner,
  people` (`core.py:283-311`).
- **One write path**: `PUT /api/settings`
  (`holdspeak/web/routes/system/settings.py:115`) →
  `SettingsService.update_settings` (`holdspeak/services/settings_service.py:290`).
  It deep-merges the patch, refuses a stale `_revision` with 409
  (`:320-337`), and drops retired keys without a word (`:385-400`).
- **Secrets** go through `/api/settings/secrets/{id}`
  (`settings_secrets.py:33-57`) into the paths `credential_service.py` names
  in `SECRET_PATHS`.
- **The face**: `web/src/pages/cores/SettingsCore.tsx` (2,618 lines) with
  `settingsPrefs.tsx` (647), `settingsPeople.tsx` (191), `settingsTts.tsx`
  (136), `settingsWallpaper.tsx` (132), `settingsBespoke.tsx` (100). Four
  wings, `settings / models / integrations / guide`
  (`SettingsCore.tsx:251-256`). The home is an index of "Open …" rows in two
  lists, Work and Desk (`settingsPrefs.tsx:516-528`).
- **The hub summary** behind the index is `GET /api/settings/hub`
  (`system/settings.py:144-355`), and MCP `settings.hub` is a second copy of
  the same read (`holdspeak/mcp/tools.py:1165-1241`).

Rows by section (each writes `PUT /api/settings` unless noted):

| Section | Rows → key |
|---|---|
| Voice | push-to-talk `hotkey`; language `model.language`; preview `dictation.preview_before_type`; voice commands `dictation.macros.enabled`; wake word `wake_word.*`; spoken symbols `dictation.spoken_symbols`; Advanced `dictation.pipeline.*`, `model.transcribe_timeout_seconds` |
| Meetings | make summary `meeting.intelligence_auto`; Change engine → opens Engines; mic `meeting.mic_device`; system audio; auto-record `meeting.auto_record`; **calendar** `calendar.sources` (Add feed, Import image → `POST /api/calendar/snapshot`, Add calendar → opens Accounts); auto export; about 20 Advanced rows (`SettingsCore.tsx:2314-2391`) |
| Rhythm | `cadence.enabled/pressure/quiet_hours_start/quiet_hours_end/max_nudges`; morning brief `cadence.brief_enabled/brief_hour`; `cadence_telegram.enabled` |
| Engines | renders `RunsOnCore` (`features/runson`); `settingsModels.tsx` is dead (`SettingsCore.tsx:58-59`) |
| Accounts | `ConnectionsPane` + `Destinations` + a Credentials fold |
| Sounds & Presence | `ui.desk_sounds`, `presence.enabled/mascot`; server voice `POST /api/tts/download` |
| Wallpaper | **browser storage only**: `hs.desk.atmosphere`, `.favorites`, `.sound` |
| People | `owner.name`, `owner.aliases`; agent access `PUT /api/settings/people-access` → `people.mcp_access` |
| System | Other devices `PUT /api/settings/remote*`; device name `mesh.device_name`; Reset desk |
| Index | Posture `PUT /api/authority/control-mode` (`SettingsCore.tsx:1645`) |

### Accounts

- **Face**: `web/src/pages/cores/connections/ConnectionsPane.tsx` (614),
  `Destinations.tsx` (627), `api.ts` (182).
- **Reads**: `GET /api/connections` (`connection.list`, a stored read,
  `holdspeak/web/routes/connections.py:43`).
- **Check**: `POST /api/connections/{provider}/recheck` with a `ref`
  (`connection.recheck`, `connections.py:62-99` →
  `connections_service.py:190-221`). GitHub runs `gh auth status`
  (`github_provider.py:249`). Jira and Confluence run `acli … auth switch
  --site --email` and then `auth status` (`jira_provider.py:587`, `:656`;
  `confluence_provider.py:285`, `:351`). The switch changes acli's active
  account and is not undone.
- **Add**: Jira and Confluence take Site and Email and store a
  disconnected row (`jira_provider.py:464-506`); the sign-in is a command
  to copy (`ConnectionsPane.tsx:192`, `:254`, `:324`). GitHub has only the
  `gh auth login` command (`:221`).
- **Detection without a process**: `gh`'s `hosts.yml`
  (`onboarding_service.py:88-131`) and acli's
  `~/.config/acli/{jira,confluence}_config.yaml`
  (`jira_provider.py:1757-1802`).
- **Destinations** (Send) sit in the same section and pick accounts from the
  same list (`Destinations.tsx:437`).
- **MCP**: `connection.list`, `connection.recheck`, `provider.list`,
  `provider.github_*`, `provider.jira_*` (with `jira_add_connection`),
  `provider.confluence_*` (no `confluence_add_connection`, although the route
  exists, `providers.py:474`) (`holdspeak/mcp/families/project.py:661-828`,
  `:1010`, `:1021`).

### First run and Setup

- **First run**: `web/src/desk/firstrun/FirstRun.tsx` (518) with its cards:
  `SpeechSetup` (160), `useFirstTake` (318, First words), `localAi` (275) and
  `LanServer` (44) in the Chat engines fold, then You (`ownerName`,
  `OwnerAliasField`), `CalendarCard` (254) + `calendarStep` (384),
  `ConnectionsCard` (157) + `connectionsStep` (117), `AgentsCard` (222) +
  `agentsStep` (139), and `Found` (158, engine proposals) (`FirstRun.tsx:455-509`).
- **Detection services**: `holdspeak/services/onboarding_service.py` (898):
  `connections_detect` (`:321-377`, files only), `connections_use`
  (`:407-441`, runs the check), `agents_detect` (`:696-800`, PATH, sign-in
  files, hooks files, tmux), `agents_use` → kernel operation
  `agent_hooks.install`. `HOLDSPEAK_AGENT_STATE=off` makes the agent reads
  answer `not_read` (`:559-583`).
- **The LAN scan** is a separate, owner-pressed operation
  (`holdspeak/services/lan_engine_discovery.py:1-8`). Concierge detection
  does not scan, so the first run's Found card is empty unless an engine is
  already known (`inference_default_service.py:721-763`).
- **Done**: `handoff()` posts `/api/desk/seed` (this is what puts the seed
  note on a fresh desk) and then `PUT /api/setup/onboarding {disposition}`
  (`FirstRun.tsx:414-419`) → table `onboarding_state`. The first run shows
  while `first_run and disposition is None` (`holdspeak/setup_status.py:335`).
  Reopen: a client flag (`desk/firstrun/reopen.ts`).
- **Setup app**: `SetupCore` renders `RuntimeDocsCore`
  (`web/src/pages/cores/SetupCore.tsx:199-201`), which is also the
  Settings ▸ Guide wing. Its rows come from `collect_doctor_checks`
  (`holdspeak/commands/doctor.py:1352`) through `/api/setup/status`.
- **`holdspeak doctor`** runs the same list, then the running hub
  (`doctor.py:1647-1666`). It does not check `gh` or `acli`.
- **Agents card**: installs hooks only, into `~/.claude/settings.json` and
  `~/.codex/hooks.json` (`holdspeak/agent_context/hooks.py:18-48`), and trusts
  the Codex hooks through Codex's own config writer
  (`onboarding_service.py:602-631`). It writes **no MCP server entry** for
  his own Claude Code or Codex. MCP config is written only per launch for
  agents the desk starts (`holdspeak/delivery/agent_mcp.py:44-70`). There is
  no `holdspeak --skill` and no skill file for agents.

### The menu rows (`web/src/desk/applications.ts`)

| Row | Line | Reached by |
|---|---|---|
| Change places | `:59` | ⌘⇧P, Search |
| Settings | `:179` | HoldSpeak menu, ⌃4, Search |
| Rhythm | `:224` | Search only (Go ▸ Tools is never drawn) |
| Setup | `:251` | HoldSpeak menu, Search |
| Engines | `:358` (`open-concierge`), `:458` (`configure-runs-on`) | HoldSpeak menu; both parked, both open `settings:models` |
| Accounts | `:469` (`configure-integrations`) | HoldSpeak menu; parked, opens `settings:integrations` |

The HoldSpeak menu is `MARK_APPLICATION_COMMANDS` (`applications.ts:508`).

## 2. Duplicates and dead parts

| What | Where | Effect |
|---|---|---|
| Two quiet-hours stores | `cadence.quiet_hours_*` in the config file (`cadence_service.py:56`) and the heartbeat policy `quiet_start/quiet_end` in the database (`heartbeat_service.py:101-146`), written by the Rhythm window (`CadenceCore.tsx:170`, `:244`) | Settings ▸ Rhythm and the Rhythm window can disagree |
| Wallpaper twice | `ChangePlacesCore.tsx:8`, `:49` renders the same `WallpaperModule` | Two homes, one store |
| Setup three times | first run, Setup app, Settings ▸ Guide (same component), `holdspeak doctor` | Different words for the same checks |
| Calendar three times | Settings ▸ Meetings, Accounts ▸ Calendar (`ConnectionsPane.tsx:600-606`), first-run Calendar card (`/api/onboarding/calendar/use`) | Three ways to add one feed |
| Engine choice in four places | Engines; Meetings ▸ Change engine; Accounts ▸ Runs on; first-run `Use this for summaries` (sets the global default, and speech inherits it) | The first-run press breaks speech (RECON §1) |
| Two recheck routes | `/api/connections/{p}/recheck` and `/api/providers/.../recheck` (`providers.py:134`, `:288`, `:506`) | Two paths for one check |
| Two settings-hub reads | the route and MCP `settings.hub` | Can drift |
| Two hooks installs | `holdspeak agent-hook install` (`cli_entry.py:28`) and the Agents card | Same function (`hooks.py:347`), fine |
| Owner name twice | first-run You and Settings ▸ People, the same `useOwnerName` hook | Fine in data; two faces |
| Dead | `settingsModels.tsx`; `ParkedSetupCore` (`SetupCore.tsx:30`); `features/project-room/_parked/setup/api.ts` | – |
| Not saved | Other devices: `PUT /api/settings/remote` keeps the value in memory (`holdspeak/web/routes/mcp_http.py:392-404`) | The switch resets when the hub restarts |
| `Voice LIVE` | `settings.py:250` reads only `dictation.pipeline.enabled` | LIVE with no speech model |

## 3. Constraints (do not change)

- The config path and its top-level keys; the `SECRET_PATHS` ids; the
  `_revision` token.
- Wing ids `settings / models / integrations / guide` and the module aliases
  in `settingsPrefs.tsx:66-78`: deep links use them. A new face can map them
  to new places; it must not break them.
- Browser storage keys `hs.desk.atmosphere*`; the policy id `heartbeat`; the
  `onboarding_state` dispositions `completed / dismissed / needs_help`; the
  milestone `first_dictation_success`.
- Env names `HOLDSPEAK_TEST_NO_REAL_CLI`, `HOLDSPEAK_AGENT_STATE`,
  `HOLDSPEAK_CHANNEL_KEYSTORE_FILE`, `HOLDSPEAK_MCP_PEOPLE_ACCESS`.
- MCP names `settings.get/update/hub`, `provider.*`, `connection.*`; kernel
  operations `agent_hooks.install`, `people_access.set`,
  `calendar.open_settings`.
- Saved window ids `surface-settings`, `surface-concierge`, `surface-setup`,
  `surface-cadence`, `surface-places`: a parked app keeps its id so that a
  saved desk opens the new home.
- The LAN scan stays an owner press (`lan_engine_discovery.py:1-8`). Setup
  may make that press one of the presses he already makes; it may not scan
  by itself (see `DESIGN.md` decision 2).
