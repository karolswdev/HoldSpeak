# Settings and setup: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked
three jobs as a first-time user at 1440x900 and 393x852, and I fixed
nothing. The shots are in `shots/` (54 files). The rig is in the
footnote.[^rig]

The jobs I walked:

1. **First run.** From a fresh desk to a working desk: speech, an engine,
   his accounts, his agents, his people.
2. **Settings.** Open it, read it, change one thing in each section.
3. **Accounts.** Connect GitHub, two Jira sites and Confluence, and know that
   they work.

Two desks:

- **The empty desk** (hub 8841): a fresh HOME with nothing signed in. It
  is what a stranger meets.
- **His Mac** (hub 8842): a fresh HOME that looks like his machine. `gh` is
  signed in as `karolswdev`, `acli` knows two Jira sites
  (`acme.atlassian.net`, `acme-platform.atlassian.net`) and one Confluence
  site, and Claude Code and Codex are signed in. The four CLIs are **stubs**
  that answer from files. No real sign-in was read and nothing went to
  GitHub or Atlassian, so a "connected" state on this desk proves the face,
  not the account.

The LAN engine (`qwen3.8-27b` at `192.168.1.43:8080`) was real.

## 1. First run

### What he sees first

The desk opens behind a card called **Get ready**
(`00-first-open-1440.png`, `00-first-open-393.png`). It has two boxes and two
closed folds:

- **Speech**: `HUGGINGFACE.CO`, `Set up speech · 144 MB`.
- **First words**: grey, `WAITS FOR SPEECH`, `Dictate one sentence`.
- `▸ Chat engines` (closed).
- `▸ Optional setup` (closed).
- `Continue later` (top right).

Nothing on the card says what HoldSpeak found on this Mac. On his Mac it
found a GitHub account, two Jira sites, a Confluence site, Claude Code,
Codex, pi and tmux. All of that is inside the closed **Optional setup** fold
(`20-his-mac-optional-1440.png`).

### Friction log

"Presses" counts presses and typed fields. "Wait" is measured. "Est." is my
estimate for a first-time user who reads each screen.

| # | Step | What I pressed | What I saw (exact words) | What he expects | Where it stops | Presses | Wait / est. | Shots |
|---|---|---|---|---|---|---|---|---|
| 1 | Open the desk | Load | `Get ready`, `Speech`, `Set up speech · 144 MB`, `First words`, `WAITS FOR SPEECH`, `▸ Chat engines`, `▸ Optional setup` | "HoldSpeak found these things; turn them on?" | The found things are hidden in a closed fold called *Optional* | 0 | 4 s / 15 s | `00-first-open-*` |
| 2 | Speech | (not pressed: a 144 MB download from huggingface.co leaves the machine; the rig sends nothing out) | – | One press, then it works | Not walked: unknown | – | – | `00-first-open-*` |
| 3 | Find an engine | `▸ Chat engines` | `Server or local chat`, rows `Speech whisper-base-mlx 144 MB`, `Meaning search nomic-embed-text v1.5 146 MB`, `Chat Quick local Qwen 2.7 GB`, `Set up local AI · 3.0 GB`, `Use a server` | "Your LAN engine is at 192.168.1.43. Use it?" | No search of the network. The LAN scan exists, but only in Settings ▸ Engines (`Find on LAN`) | 1 | – / 20 s | `01-chat-engines-open-*` |
| 4 | Use the LAN engine | `Use a server`, typed `http://192.168.1.43:8080/v1`, `Check`, `Use this for summaries` | `SERVER ADDRESS`, `KEY optional`, `I OWN THIS SERVER`, then `● READY qwen3.8-27b TOOLS`, then `USING · QWEN3.8-27B · SUMMARIES · NOW THE DEFAULT` | Found for him, or at least one field | He must know the URL with `/v1`. The press says "for summaries" and sets **every** job (below) | 3 + a URL | Check 4 s / 60 s | `03-use-a-server-1440.png`, `05-server-checked-1440.png`, `06-server-used-1440.png` |
| 5 | Open the found things | `▸ Optional setup` | Cards **You**, **Calendar**, **Connections**, **Agents** | These on top, not optional | The card that matters most for an architect is folded | 1 | – / 10 s | `02-optional-open-full-1440.png` |
| 6 | Connect accounts (his Mac) | `Use it` four times | `SIGNED IN · 4`, rows `GitHub gh · karolswdev`, `Jira acli · karol@acme.example` (twice), `Confluence acli · karol@acme.example`, then `CONNECTED · 4` | One press for all four | Works, and it is good. Four presses for one decision. The two Jira rows read the same; the site is only in the chip | 4 | 4 s each, 16 s / 30 s | `20-his-mac-optional-*`, `21-his-mac-connections-used-1440.png` |
| 7 | Connect accounts (empty desk) | read | `NO SIGN-IN FOUND`, `gh auth login [Copy]`, `acli jira auth login --site <site> --email <email> --token [Copy]`, `Check again` | A Sign in press | He is sent to a terminal to type a command with three blanks | 0 | – / 2–5 min outside | `02-optional-open-full-1440.png` |
| 8 | Agents | `Install hooks` | `Hooks tell HoldSpeak when Claude Code or Codex works, waits or stops.` Rows: `INSTALLED`, `SIGNED IN`, `HOOKS`. After the press: Claude Code `● HOOKS`, Codex still `○ HOOKS` with no reason | "Let my agents use HoldSpeak" | The press installs hooks only. His own Claude Code and Codex do not get the desk's tools or a skill. Codex failed with no words (in the rig, the Codex stub cannot answer the trust call, so the real result is unknown) | 1 | 5 s / 20 s | `22-his-mac-hooks-installed-1440.png` |
| 9 | Calendar | read | `Reads your meetings, so HoldSpeak can record the next one.`, `CALENDAR URL https://…/calendar.ics`, `Add` | His Mac calendars, found | The rig turns macOS calendar reads off, so only the link field shows. On his Mac the card reads EventKit first: not walked, unknown | 0 | – | `02-optional-open-full-1440.png` |
| 10 | His name | read | `YOUR NAME`, `ALSO CALLED` | – | Fine | 1 field | – | `02-optional-open-full-1440.png` |
| 11 | His people | (not in first run) Dock ▸ People, `Set up People`, then for each person `Add person`, name, `Direct report`, `Add` | `Set up People · Encrypted, local-only relationship context`, then `RELATIONSHIPS`, `Add a person to start` | People in the first run, ideally found in his calendar | Not part of setup at all. 14 presses for three people, in another window | 14 | 3 s + 7 s / 60 s | `24-people-fresh-*`, `26-people-setup-pressed-1440.png`, `27-people-three-1440.png` |
| 12 | Leave | `Continue later` | The desk with a seed note `Weekly update` | `Open my desk` | "Later" when he is done | 1 | 3 s | `07-desk-after-continue-1440.png` |

**Total on his Mac**: about **25 presses, one URL typed from memory, and two
windows** to reach speech, one engine, four accounts, hooks and three people.
About 5 minutes if he knows the LAN URL by heart, and longer if he does not.
And the result is broken (next section).

### The press that broke speech

`Use this for summaries` in step 4 did more than its words say. It made
the LAN server **the default for every job**. Speech to text inherits
the default, and a chat server cannot transcribe. Settings ▸ Engines then
said `Speech to text · runs on 192.168.1.43`, `TOOL INCOMPATIBLE [Choose]`,
and at the top `4 READY · 2 LIMITED · 1 BROKEN`
(`11-3-settings-engines-1440.png`). The hub's assignment list shows the same
LAN profile on all seven groups, `speech_recognition` included.[^assign]

## 2. Settings

### How he gets there

On the desk: **HoldSpeak** menu ▸ `Settings ⌃4`, `Engines`, `Accounts`,
`Setup` (`08-holdspeak-menu-1440.png`). Settings and Setup use the same `⚙`
icon. On the phone, the four rows are only under the HoldSpeak logo. The
launcher's Apps list does not have them (`25-phone-holdspeak-menu-393.png`).

### What he sees

The window opens at about 640x600 on a 1440 desk, so it shows five rows
(`10-settings-open-1440.png`). It has four wings (`SETTINGS`, `ENGINES`,
`ACCOUNTS`, `GUIDE`). The first wing is an index of nine rows, each with an
`Open …` button:

| Row | The fact it shows | What is behind `Open` |
|---|---|---|
| Voice | `● LIVE AUTO` | push-to-talk key, a language list of about 100 entries, preview, voice commands, wake word, spoken symbols, Advanced (`11-0-settings-voice-1440.png`) |
| Meetings | `○ SUMMARY SET ON · AFTER EVERY MEETING` | make summary, the summary engine with `Change engine`, microphone, auto-record, **a calendar block** (`Add calendar`, `Add feed`, `Import image`), auto export (`11-1-settings-meetings-1440.png`) |
| Rhythm | `EVERY 15 MIN NEXT 20:33` | `CADENCE Enabled Off`, `Pressure`, `Quiet from 22 h`, `Quiet until 8 h`, `Max nudges /day`, `MORNING BRIEF On, Make at 6 h`, `TELEGRAM` (`11-2-settings-rhythm-1440.png`) |
| Engines | `1 engine · Default set` | the Engines face (cluster H, `engines/`) |
| Accounts | `None connected` | GitHub, Jira, Confluence, **Calendar**, **Runs on 4 of 7 assigned**, Destinations, Credentials (`11-4-settings-accounts-1440.png`) |
| Sounds & Presence | `Desk sounds on` | desk sounds, presence, mascot, browser voice, server voice |
| Wallpaper | `Quiet Desk` | twelve wallpapers, Motion |
| People | `AGENTS CAN READ PEOPLE` | your name, also called, agent access (`OFF READ READ AND WRITE`) |
| System | `OTHER DEVICES: OFF` | other devices, reset desk, Advanced |
| Posture | `Secure Normal YOLO` | (on the index itself) |

To come back from a section he presses `« Settings` at the bottom of the
window.

### What does not agree

| The face says | Another face says | Shots |
|---|---|---|
| Settings ▸ Voice: `● LIVE` | Setup: `Speech model · No speech model yet · Not working`. First run: `Set up speech`. The LIVE chip reads only whether the dictation pipeline is switched on, not whether speech works.[^live] | `10-settings-open-1440.png`, `12-setup-menu-item-1440.png` |
| Settings index ▸ Rhythm: `EVERY 15 MIN NEXT 20:33` | Settings ▸ Rhythm: `CADENCE Enabled Off` | `10-settings-open-1440.png`, `11-2-settings-rhythm-1440.png` |
| Settings ▸ Rhythm: quiet 22 h to 8 h (`cadence.*` in the config file) | The Rhythm window: `QUIET 22:00–08:00` (the heartbeat policy in the database). Two stores; they agree only by chance | `31-rhythm-window-1440.png` |
| The Rhythm window: `Runs on THIS DEVICE` | The only engine is the LAN server | `31-rhythm-window-1440.png` |
| Setup: `Dictation AI model · The clean-up model is not on this device yet` | Settings ▸ Engines: `Dictation clean-up · Qwen3.8 27B · on 192.168.1.43` | `12-setup-menu-item-1440.png`, `11-3-settings-engines-1440.png` |
| Settings index ▸ Meetings: `○ SUMMARY SET ON` with a hollow (idle) lamp | Settings ▸ Meetings: the summary engine is set, `192.168.1.43 · LAN` | `10-settings-open-1440.png`, `11-1-settings-meetings-1440.png` |

### Homes counted

| Thing | Homes today | Shots |
|---|---|---|
| Calendar | Settings ▸ Meetings ▸ CALENDAR; Settings ▸ Accounts ▸ Calendar; first run ▸ Calendar | `11-1-*`, `11-4-*`, `02-optional-open-full-1440.png` |
| Rhythm | Settings ▸ Rhythm; the Rhythm window (Search only) | `11-2-*`, `30-search-rhythm-1440.png`, `31-rhythm-window-1440.png` |
| Wallpaper | Settings ▸ Wallpaper; Change places (⌘⇧P) | `11-6-*`, `32-change-places-1440.png` |
| The engine for a job | Engines; Settings ▸ Meetings (`Change engine`); Settings ▸ Accounts (`Runs on 4 of 7 assigned`); first run (`Use this for summaries`) | `11-1-*`, `11-4-*`, `06-server-used-1440.png` |
| Setup | first run (`Get ready`); HoldSpeak ▸ Setup; Settings ▸ Guide (the same component as Setup); `holdspeak doctor` | `12-setup-menu-item-1440.png` |
| His name | first run ▸ You; Settings ▸ People | `02-*`, `11-7-*` |

## 3. Setup (HoldSpeak ▸ Setup)

`Setup` opens a window titled `6 things need you`, with `Get ready` and
`Test runtime` buttons (`12-setup-menu-item-1440.png`, `33-setup-393.png`).
The rows are:

- `Speech model · No speech model yet · ● Not working`, `Set up speech · 144 MB`
- `Trust destinations · Data can go to Meeting summary · Check`
- `Where AI runs · 1 ready. Some places for AI are not set up or not available · Check [Choose engines]`
- `Dictation AI model · The clean-up model is not on this device yet · Check [Choose engines]`
- `People keystore · A test keystore is in use. Do not use it for real data · Check` (a rig fact: the rig uses a file keystore)
- `Coding agents · Some agent hooks are not installed · Check [Show the fix]`

`Check` is a yellow status chip that looks like a button. Three rows have no
verb. `Trust destinations` and `Data can go to Meeting summary` are words he
would not use.

`holdspeak doctor` prints the same list as text (27 passed, 5 warnings, 1
failed) and then checks the running hub. It does not check `gh` or `acli`.

## 4. Accounts

On the empty desk (`11-4-settings-accounts-1440.png`):

- **GitHub**: `○ Never checked`, `GITHUB.COM`, `Recheck`. After `Recheck`:
  `Unreachable · Checked now` with `Retry` (`15-accounts-github-recheck-1440.png`).
  In this rig the guard refuses to run a real `gh`, and the face calls that
  "Unreachable". On his Mac it runs `gh auth status`. Not walked: unknown.
- **Jira**: `○ Never checked`, `Add account`. The form asks `Site` and
  `Email`, then shows a `Sign-in command` to copy (`16-accounts-jira-add-1440.png`).
- **Confluence**: the same.
- **Calendar**: `○ Not set up`, `Choose calendar`.
- **Runs on**: `4 of 7 assigned`, `Choose engines`. This is an Engines fact in
  the Accounts list.
- **Destinations 1**: `HoldSpeak folder ~/Documents/HoldSpeak/Sent FILE`.
- **Credentials**: a closed `Advanced` fold.

On his Mac, after the four first-run presses, Settings ▸ Accounts agrees
with the first-run card: GitHub `karolswdev ✓ Connected`, two Jira rows,
Confluence, each with the site chip and `Recheck`
(`23-his-mac-settings-accounts-1440.png`, `23-his-mac-settings-accounts-393.png`).
This part works.

One hidden effect: **Recheck on a Jira or Confluence row switches acli's
active account** (`acli jira auth switch`) and leaves it switched. If he uses
`acli` in his terminal after a Recheck, it may point at the other site.[^switch]

## 5. What worked

- Detection is real and good. The hub reads `gh`'s and `acli`'s own files
  without starting a process, and finds every account, both Jira sites
  included. It reads Claude Code's and Codex's sign-in files, finds pi and
  tmux, and offers one press for each.
- `Use it` on an account connects it and checks it in 4 s, and Settings ▸
  Accounts agrees at once.
- The LAN `Check` took 4 s and named the model and its tool support.
- People take four presses per person, with no form to fill.

## 6. Unknown (not walked)

- The speech download and the first sentence (no download in the rig).
- EventKit calendars on his Mac (macOS reads are off in the rig).
- A real `gh auth status` and `acli` sign-in, and the Codex hook trust on a
  real Codex.
- One console error on the empty desk: `Failed to load resource: 503` while
  Change places was open. Its route is not known.

## Summary

The product already knows most of what a working desk needs: his accounts,
his agents and his engine are on the Mac, and the hub can read them. The
first run hides them in a fold called Optional, asks one press per thing,
does not look for the LAN engine, leaves out his people, and gives his agents
hooks and nothing else. One of its presses breaks speech and says it did
something smaller. Settings is a second app with its own index, wings and
back button. Rhythm, Wallpaper, Calendar, the engine for a job, and Setup
itself each have two to four homes, and the homes disagree about the facts.

[^rig]: Isolated hubs started with `scripts/graph_walk.py serve --scheduler`
    from the code of the owner's desk worktree
    (`wt-daily-delight-delivery-20261017`, `217001b2e`, the merge of #1247;
    its web and services match main `b746549b8` except
    `holdspeak/web/routes/setup.py`), with `_isolated_hub_env` (a scratch
    `HOME` from `mktemp -d`, every isolation switch). Port 8841: the empty
    desk, `HOLDSPEAK_AGENT_STATE=off`. Port 8842: "his Mac",
    `HOLDSPEAK_AGENT_STATE=on` with `CLAUDE_CONFIG_DIR` and `CODEX_HOME`
    inside the scratch HOME, built by `rig/make_his_machine.sh` (gh
    `hosts.yml`, acli `jira_config.yaml` and `confluence_config.yaml`, Claude
    and Codex sign-in files with no real token, and stub `gh`, `acli`,
    `claude` and `codex` on `PATH` inside the scratch HOME, which the
    `cli_guard` lets run because they sit under the temp root). The real LAN
    engine `qwen3.8-27b` at `192.168.1.43:8080` was added through the first-run
    face. People were added through the face. No meetings were seeded: no
    setup step reads them. Chromium headless through Playwright
    (`rig/walk.py`, one step file per walk in `rig/steps/`), 1440x900 and
    393x852 (mobile, touch, scale 2). `holdspeak doctor` was run once with
    the same isolated environment; it found the 8841 hub through the owner
    lock in the scratch HOME. Both hubs stopped, both scratch HOMEs and the
    browser profiles removed afterwards.
[^assign]: `GET /api/inference/assignments` on hub 8841 after the press: the
    rows `global`, `thoughts_notes`, `writing_dictation`,
    `speech_recognition`, `meetings`, `agents_tools` and `background` each
    name `engine-192-168-1-43-8080`. The press label is in
    `web/src/features/concierge/ConciergeCore.tsx:546`.
[^live]: `holdspeak/web/routes/system/settings.py:250` sets
    `voice_live = config.dictation.pipeline.enabled`;
    `web/src/pages/cores/settingsPrefs.tsx:501` draws it as `LIVE`.
[^switch]: `holdspeak/services/jira_provider.py:587` and `:656` (switch,
    then status), and `holdspeak/services/confluence_provider.py:285`, `:351`.
