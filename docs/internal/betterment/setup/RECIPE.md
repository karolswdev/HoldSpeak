# Settings and setup: the recipe

Each slice is one PR in the fast cycle (`CLAUDE.md`): quick check, merge,
the main watcher runs the whole suite, Astra reviews after the merge. The
order is chosen so that each merge leaves the desk better and never
half-broken. Read `DESIGN.md` first; `MODEL.md` has the file map.

Dependencies on other recipes:

- **Engines** (`../engines/RECIPE.md`): ST3 uses E2 (Found on this Mac) for
  the agent-engine rows. ST3 can ship without it; the agent-engine rows then
  appear when E2 lands.
- **Agents** (`../agents/RECIPE.md`): ST6 uses AG13 (`holdspeak --skill`).
- **Automations** (`../workbench/RECIPE.md`): ST1 parks the Rhythm window's
  loops only after Automations can hold them; until then the loops stay
  reachable behind RAW.

Paths below: `web/` is `web/src/`, `hs/` is `holdspeak/`.

## ST0. Tell the truth

- **Goal**: every setup and settings fact he reads is true; no press breaks
  speech.
- **Files**: `hs/web/routes/system/settings.py` (`:250`, the hub summary);
  `web/pages/cores/settingsPrefs.tsx` (`:501-515`);
  `web/features/concierge/ConciergeCore.tsx` (`:546`, the first-run LAN
  press) and the service it calls; `web/pages/cores/SetupCore.tsx` /
  `RuntimeDocsCore`; `hs/web/routes/mcp_http.py` (`:392-404`).
- **Changes**:
  - The Voice fact reads whether speech works (the speech model state that
    Setup reads), not `dictation.pipeline.enabled`. Words: `Works`, `Speech
    is not set up`, `Voice typing off`.
  - The first-run LAN press is labelled **Use** and makes the server the
    engine for Everything else. Speech to text never inherits a chat
    server: before writing, ask the existing `fit` read
    (`inference_assignment_service.py`, `fit`) and leave out every group
    the engine cannot serve. Engines then shows no `TOOL INCOMPATIBLE` and
    no `BROKEN` after this press.
  - The Rhythm fact on the Settings index and the Rhythm section read the
    same store (the heartbeat policy the notices loop reads).
  - Setup rows: the yellow `Check` chip becomes the state in words (`Works`,
    `Does not work: …`). A row with no verb that fixes it says only its
    state.
  - Other devices is saved in the config file, not in memory.
- **Done when**: on a fresh rig hub, pressing the first-run LAN `Use` leaves
  Settings ▸ Engines with no broken row, at 1440 and 393; Settings ▸ Voice
  says `Speech is not set up` while Setup says the same; restarting the hub
  keeps Other devices on.
- **Tests**: T1 `tests/integration/test_desk_settings.py` (the hub summary
  facts; Other devices survives a restart); T1 a hub test that the LAN use
  leaves `speech_recognition` unassigned; T2
  `web/desk/firstrun/__tests__/firstrun.app.test.tsx` on a recorded hub
  answer; T3 the desk sweep.
- **Not in this slice**: any layout change; moving any control.

## ST1. One home each: Rhythm, Wallpaper, Calendar, the engine line

- **Goal**: each of these has one home, and every old door opens it.
- **Files**: `web/desk/applications.ts` (`:59`, `:224`, `:358`, `:458`,
  `:469`); `web/pages/cores/SettingsCore.tsx` (the Meetings calendar block,
  the Accounts `Runs on` row); `web/pages/cores/connections/ConnectionsPane.tsx`
  (`:600-606`); `hs/services/heartbeat_service.py` and
  `hs/services/cadence_service.py` (quiet hours).
- **Changes**:
  - Park the Rhythm window and Change places (`park` in the manifest,
    nothing deleted). Their ids (`surface-cadence`, `surface-places`), Search
    words and ⌘⇧P open Settings at Rhythm and at Wallpaper.
  - Quiet hours: one store. The Settings row writes the heartbeat policy;
    `cadence_service` reads it. The `cadence.quiet_hours_*` keys are left in
    place and no longer read (retired-key path, `settings_service.py:385-400`).
  - The sweep interval and its Run now move behind Advanced in the Rhythm
    section. The cadence loops stay reachable behind RAW until Automations
    can hold them.
  - Calendar: remove the block from Settings ▸ Meetings; Accounts ▸ Calendar
    is its home.
  - Remove `Runs on 4 of 7 assigned` from Accounts. In Meetings, the engine
    becomes a fact line "Summaries run on …" with **Engines ›**.
- **Done when**: Search "Rhythm" and "Change places" each open the
  Settings section; ⌘⇧P opens Wallpaper; a saved desk with the old windows
  opens the new home; changing quiet hours in Settings changes what the
  heartbeat reads; Meetings has no calendar block. At 1440 and 393.
- **Tests**: T1 `tests/integration/test_desk_parked.py` (the parked ids
  open the new home); T1 a heartbeat unit test that reads the one store; T2
  `web/pages/cores/__tests__/rhythm.app.test.tsx` updated to the new home;
  T3 sweep.
- **Not in this slice**: the one-page layout (ST7); renaming Rhythm to
  Notices (ST7).

## ST2. Accounts that say Works, and Check that does not move acli

- **Goal**: each account row says in words whether it works, and checking a
  Jira row never changes the account he uses in his terminal.
- **Files**: `hs/services/connections_service.py` (`:190-221`);
  `hs/services/jira_provider.py` (`:587`, `:656`);
  `hs/services/confluence_provider.py` (`:285`, `:351`);
  `web/pages/cores/connections/ConnectionsPane.tsx`.
- **Changes**:
  - Before the switch, read acli's current profile from its config file
    (`read_acli_profiles` already reads `current`); after the status read,
    switch back to it.
  - Row state words: `Works`, `Not signed in`, `Signed in as another
    account`, `Could not check: <reason>`. A refused CLI (the test guard)
    says `Could not check: gh was not run`, never `Unreachable`.
  - Each row shows the site in the row (two Jira sites are told apart).
  - Accounts lists **Found on this Mac**: acli or gh accounts in their files
    that HoldSpeak does not use yet, each with **Use** (the existing
    `connections_use`).
  - Pressing a row unfolds what uses it (projects, destinations), **Sign in
    again** (today's command, until ST8), **Remove** with Undo.
- **Done when**: on a rig hub with stub `acli` and two Jira profiles,
  Check on the second site leaves the stub's current profile on the first;
  a third profile added to the stub's file appears under Found and Use
  connects it in one press. At 1440 and 393.
- **Tests**: T1 `tests/integration/test_desk_connections.py` (switch-back,
  found list, state words); T2
  `web/pages/cores/__tests__/connections-pane.test.tsx` on recorded answers;
  T3 sweep.
- **Not in this slice**: signing in without a terminal (ST8).

## ST3. Setup is one window of found things

- **Goal**: on first launch he sees what HoldSpeak found, each with one
  press, in one window that is also HoldSpeak ▸ Setup.
- **Files**: `hs/services/setup_service.py` (a `found()` read);
  `hs/web/routes/setup.py`; `web/desk/firstrun/FirstRun.tsx` and its cards;
  `web/pages/cores/SetupCore.tsx`; `web/pages/cores/SettingsCore.tsx`
  (remove the Guide wing).
- **Changes**:
  - `setup_service.found()` returns one list of rows from the reads that
    exist: speech state, engine proposals and Engines' Found (E2 when it
    lands), `connections_detect`, the calendar read, `agents_detect`, and
    the owner name. Each row: kind, label, detail, state (`found`, `works`,
    `does_not_work` with a reason), egress host, verb. It reads files only
    (no process, no network), as today.
  - The window "Set up HoldSpeak": Found on this Mac, You and your people
    (name only in this slice), Not found (folded). Each row's verb calls
    today's route for it (`/api/setup/local-ai`, the engine use, the
    connections use, the calendar use, the agents use).
  - The first launch opens this window; HoldSpeak ▸ Setup opens it later. On
    later opens, working rows fold into one line, problems first.
  - The finale: "Ready, \<name\>." with Say one sentence (today's First
    words) and Open my desk (opens Today). `Continue later` goes.
  - The Settings Guide wing is removed; its deep link opens Setup.
  - `holdspeak doctor` prints the same rows first (it already shares
    `collect_doctor_checks`; map its words to the row words).
- **Done when**: on the "his Mac" rig (`rig/make_his_machine.sh`), the first
  open lists GitHub, two Jira sites, Confluence, Claude Code, Codex and pi
  with their verbs; each Use turns its row to Works; Open my desk opens
  Today. On the empty rig, Found holds Speech only and Not found holds the
  rest. At 1440 and 393.
- **Tests**: T1 `tests/integration/test_desk_firstrun.py` (`found()` on the
  stub HOME, and on an empty HOME); T2
  `web/desk/firstrun/__tests__/firstrun.app.test.tsx` on a recorded `found()`
  answer, pressing Use through to the rendered Works; T3 sweep (Setup is in
  `applications.ts`).
- **Not in this slice**: Use everything found and the network look (ST4);
  people (ST5); agents' tools (ST6).

## ST4. Use everything found, and the look on his network

- **Goal**: one press turns on everything found, and his LAN engine is
  found without him knowing its address.
- **Files**: `web/desk/firstrun/FirstRun.tsx` (or the new Setup window);
  `hs/services/setup_service.py`; `hs/services/lan_engine_discovery.py`
  (called, not changed).
- **Changes**:
  - **Use everything found** in the head presses each Found row's verb in
    order and shows each row's result as it lands (decision 1 says what it
    includes; the default leaves out the 3 GB model).
  - When Setup opens, it runs the LAN look once (decision 2) and adds each
    answering server as an engine row: model name, host, YOUR NETWORK.
    With decision 2 answered no, the row is **Look on my network** with one
    press.
- **Done when**: on the "his Mac" rig with the real LAN engine reachable,
  Setup shows `Engine · qwen3.8-27b · 192.168.1.43`; one press of Use
  everything found leaves every row Works (speech excluded in the rig: no
  download) in under 30 s. At 1440 and 393.
- **Tests**: T1 the LAN look with a recorded server answer
  (`HOLDSPEAK_WIRE_WRITE` pattern); T2 the press through to all rows
  rendered Works on recorded answers; T3 sweep.
- **Not in this slice**: cloud services (OpenRouter keys stay in Not found).

## ST5. Your people in Setup

- **Goal**: his three people exist before he opens the desk.
- **Files**: the Setup window; `hs/services/people_service.py` (create,
  called through today's route); the calendar read.
- **Changes**:
  - **Your people**: one field with the mic. Comma-separated names become
    Persons (direct report by default) with one press of Add.
  - When the calendar is in, recurring events that read "1:1 with \<name\>"
    (or have one other attendee) offer the names. Check first what today's
    calendar read returns (titles only, or attendees): **unknown**. If it is
    titles only, use the titles.
  - If People needs its one-time setup (`Set up People`, the keystore), the
    Add press does it first.
- **Done when**: typing "Mira Okafor, Theo Lindqvist, Jun Park" and Add
  makes three Persons that People lists at once; with a calendar holding
  "1:1 with Mira" weekly, Mira is offered. At 1440 and 393.
- **Tests**: T1 the people creation through the Setup route; T2 the field
  through to the rendered names; T3 sweep.
- **Not in this slice**: relationship kinds other than direct report.

## ST6. Let my agents use HoldSpeak

- **Goal**: his own Claude Code and Codex can use his desk after one press.
- **Files**: `hs/services/onboarding_service.py` (`agents_use`);
  `hs/agent_context/hooks.py`; the kernel operation `agent_hooks.install`
  (or a sibling); `web/desk/firstrun/AgentsCard.tsx` (or the Setup row).
- **Changes**:
  - The press installs, per found agent: hooks (as today), HoldSpeak's MCP
    server in the agent's own user config, and the skill from AG13.
  - The MCP entry runs `holdspeak-mcp` (the owner credential, loopback
    only, as `.mcp.json` does in this repo). Check first how each CLI adds a
    user-scope server today (`claude mcp add --scope user …`; Codex's
    `config.toml` `[mcp_servers]` or `codex mcp add`): **unknown, read the
    current CLI help before writing**. Write through the CLI's own command
    where one exists, as the Codex hook trust already does.
  - The row says what each agent got (`uses your desk · tools · skill`);
    Stop using my desk removes all three.
  - Rig: `CLAUDE_CONFIG_DIR` and `CODEX_HOME` inside the scratch HOME, as
    today; never the owner's files.
- **Done when**: on the "his Mac" rig, one press writes the hooks, the MCP
  entry and the skill under the scratch HOME's Claude and Codex folders;
  Stop removes them; a failure says why in words (the Codex trust failure
  today shows only `○ HOOKS`). At 1440 and 393.
- **Tests**: T1 the files written under an isolated HOME and removed again;
  T2 the row through to the rendered words; T3 sweep.
- **Not in this slice**: agents the desk launches (they already get tools
  per launch); exporting automations as skills.

## ST7. Settings is one page

- **Goal**: every preference is one scroll or one search away, in one
  window, with no sub-pages.
- **Files**: `web/pages/cores/SettingsCore.tsx`, `settingsPrefs.tsx`,
  `settingsPeople.tsx`, `settingsWallpaper.tsx`, `settingsTts.tsx`;
  `web/desk/applications.ts` (palette rows for settings).
- **Changes**:
  - One page with sections You, Speak, Meetings, Notices, Accounts, Agents,
    Desk, This Mac, in that order, and a section index (left at 1440, a
    wrapping row of words at 393). Remove the `Open …` index, the wings and
    `« Settings`. Map the old module ids and wing ids
    (`settingsPrefs.tsx:66-78`) to section anchors, so every deep link still
    lands.
  - Rename on the face: Rhythm → Notices; Posture → Agents act; Voice →
    Speak. Desk sounds, presence and mascot move into Desk; notify, quiet
    hours, daily brief and max nudges into Notices; Telegram into Accounts.
  - Advanced rows stay, in a **More** fold per section.
  - Every row label is a palette entry that opens Settings at that row, lit.
  - Each feature window with preferences gets **Settings** in its More menu
    (Speak, Meetings, Today for Notices).
  - The window opens at least 880x720 at 1440.
- **Done when**: ⌘K "quiet" opens Settings at Quiet hours in 2 presses;
  every old deep link (`settings:models`, `settings:integrations`,
  `settings:rhythm`, …) lands on its section; no sub-page exists. At 1440
  and 393, the sweep finds no clipping and no overlap.
- **Tests**: T2 `settings.app.test.tsx` (new, one file for the app,
  replacing the scattered `settings*.test.tsx` checks it covers; the old
  files are parked, not deleted); T1 `tests/integration/test_desk_settings.py`
  for the deep links; T3 sweep.
- **Not in this slice**: new preferences; Engines' own face.

## ST8. Sign in without a terminal

- **Goal**: he adds a GitHub or Jira account without copying a command.
- **Files**: `web/pages/cores/connections/ConnectionsPane.tsx`; the desk's
  terminal pane (the Conductor's xterm and tmux path); a small route that
  starts the sign-in in a pane.
- **Changes**:
  - **Sign in** opens a terminal pane in place under the row, running the
    CLI's own sign-in: `gh auth login --web --hostname <host>`; for Jira and
    Confluence, acli's sign-in for that site and email. Check acli's current
    flags for a browser sign-in first: **unknown**.
  - When the process ends, Check runs by itself and the row says Works or
    the CLI's own words.
  - HoldSpeak starts the CLI and shows its pane. It never reads the token.
- **Done when**: on a rig with stub `gh` that "signs in" by writing its
  `hosts.yml`, pressing Sign in shows the pane, and the row turns Works when
  the stub exits. At 1440 and 393.
- **Tests**: T1 the route starts the stub in the isolated tmux; T4 one
  browser test for the pane's keys (a real terminal needs keys); T3 sweep.
- **Not in this slice**: Slack and email sign-in (they keep their key
  fields).

## ST9. Setup from the terminal and by asking

- **Goal**: he, or an agent he asks, can set up the desk without the window.
- **Files**: `hs/cli_entry.py` (`holdspeak setup`); `hs/mcp/families/`
  (a `setup` family); `hs/mcp/tool_authority.py`.
- **Changes**:
  - `holdspeak setup` prints the Setup rows with the same words;
    `--yes` presses Use everything found and prints each result.
  - MCP `setup.status` (READ) and `setup.use` (CONFIG: one row id or `all`).
    In a Thread, `setup.use` stops for his press; from his own Claude Code
    (owner credential) it runs.
- **Done when**: on the "his Mac" rig, `holdspeak setup --yes` connects the
  four accounts and installs the agents' access, and the Setup window then
  shows them as Works; `setup.status` through MCP returns the same rows.
- **Tests**: T1 the CLI output and the MCP tools against the isolated hub.
- **Not in this slice**: new kinds of found things.

## Order and why

ST0 first: it fixes the broken speech and the wrong facts without moving
anything. ST1 removes the duplicate homes, which is what made Settings
fragile. ST2 makes Accounts trustworthy, and ST3 reuses its row. ST3 to ST6
build the Setup window, one ability at a time; each is useful alone. ST7
reshapes Settings once its contents are settled. ST8 and ST9 are the
ambitious edge: no terminal for sign-in, and setup by command or by asking.
