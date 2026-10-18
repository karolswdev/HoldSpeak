# Settings and setup: betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 54 shots,
2026-10-17) and `MODEL.md` (the code map). Companions: `../engines/DESIGN.md`
(Engines is designed there and is not repeated here), `../mcp/DESIGN.md`
(the desk's tools), `../agents/DESIGN.md` (the HoldSpeak skill, AG13),
`../daily/DESIGN.md` (notices).

Cluster H, the part that is not Engines: INVENTORY rows 36 (Settings), 37
(Accounts) and 38 (First run and Setup).

## 1. The job

Owner, 2026-10-05: strong defaults, "batteries included". Owner, 2026-08-17:
"setup flows must be joyful". Owner, 2026-10-17: "the most advanced Agentic
OS in the world", and he keeps hitting walls.

He opens **Setup** once, on a fresh desk, and again when something stops
working. He wants a working desk in minutes, without a manual and without a
terminal: speech that types, an engine for the AI work, his GitHub, his Jira
sites and Confluence, his calendar, his three people, and his own Claude Code
and Codex able to use the desk. He closes it when every line says it works,
or says in words what is still missing.

He opens **Settings** when he wants to change one preference (quiet hours,
the push-to-talk key, auto-record, the wallpaper). He closes it when the
change is saved and he did not have to look for it.

He opens **Accounts** when he adds a Jira site or something stops working.
He closes it when each account says it works.

## 2. What it is today

The full walk is in `RECON.md`. In short:

| Job | Today | Shots |
|---|---|---|
| Fresh desk to a working desk | About **25 presses, a LAN URL typed from memory, and two windows**, about 5 minutes. The found accounts and agents are in a closed fold called *Optional setup*. The LAN engine is not looked for. People are not in setup. And one press (`Use this for summaries`) wires speech to a chat server, so Engines then says `1 BROKEN` | `00-first-open-*`, `02-optional-open-full-1440.png`, `06-server-used-1440.png`, `11-3-settings-engines-1440.png` |
| Connect accounts he already signed in to | Works: one `Use it` per account, 4 s each. On a Mac with no sign-in he is told to copy `acli jira auth login --site <site> --email <email> --token` into a terminal | `21-his-mac-connections-used-1440.png`, `02-optional-open-full-1440.png` |
| Let his agents use the desk | `Install hooks`. His own Claude Code and Codex get hooks, but not the desk's tools and not a skill | `22-his-mac-hooks-installed-1440.png` |
| Change one preference | Settings opens on an index of nine `Open …` rows in a small window. Each section is a sub-page with `« Settings` at the bottom. Four wings. A Posture switch on the index | `10-settings-open-*`, `11-*` |
| Know it works | Settings says `Voice ● LIVE` while Setup says `Speech model · Not working`. The Rhythm row says `EVERY 15 MIN` while its section says `CADENCE Off`. Setup shows yellow `Check` chips that look like buttons and do nothing | `10-settings-open-1440.png`, `12-setup-menu-item-1440.png` |

What works: detection is real and good. The hub finds `gh`'s account, both
Jira sites and Confluence from their own files, finds Claude Code, Codex, pi
and tmux and whether they are signed in, and connects an account in 4 s.

## 3. Why it fails

1. **Setup asks instead of offering.** HoldSpeak already knows what is on
   his Mac, but first run leads with a download, hides what it found in a
   fold called *Optional*, wants one press per thing, never looks on his
   network, and leaves out his people (`00-first-open-1440.png`,
   `02-optional-open-full-1440.png`). "Batteries included" means *found, and
   on in one press*. Today it means *ask him about each battery*.
2. **One job has three or four homes, and the homes disagree.** Setup is the
   first run, the Setup app, Settings ▸ Guide and `holdspeak doctor`.
   Calendar is in Meetings, in Accounts and in first run. Rhythm is a window
   and a Settings section with two stores of quiet hours. Wallpaper is two
   apps. The engine for a job is set in Engines, in Meetings, in Accounts
   and in first run (RECON §2, "Homes counted"). Every extra home is one more
   face that must be fixed each time, which is why Settings broke so often
   this week (INVENTORY row 36).
3. **The faces do not tell the truth.** `Voice LIVE` reads a switch, not
   speech. `Use this for summaries` sets every job, speech included. `Check`
   is a chip, not a check. `Unreachable` can mean "we did not run gh". `Runs
   on THIS DEVICE` is shown when nothing runs on this device (RECON §2, "What
   does not agree"). A setup face that is wrong cannot earn trust, and trust
   is the reason he opens it.
4. **Settings is a second operating system.** It has its own index, wings,
   sub-pages and back button. It holds things that are not preferences: an
   engine row (`Runs on 4 of 7 assigned`) inside Accounts, a calendar block
   inside Meetings, a Guide that is the Setup app. A preference is two to
   four presses deep, in a 640x600 window (`10-settings-open-1440.png`).
5. **Agents are an afterthought.** For an agentic OS, the most important
   setup line is "my own Claude Code and Codex can use my desk". Today that
   line installs hooks (so the desk can watch them) and nothing that lets
   them act: no MCP server entry, no skill (`MODEL.md` §1).
6. **Signing in is sent to the terminal.** A new Jira site means copying a
   command with three blanks. And Check on a Jira row silently switches
   acli's active account (`MODEL.md` §1).

## 4. The design

### The concept

Three sentences, one for each face:

> **Setup** shows what HoldSpeak found on this Mac and turns it on in one
> press. It is the same window on the first day and every later day.
>
> **Settings** holds each of his preferences once, on one page.
>
> **A property of a thing stays on the thing.** An automation's When, a
> project's sources, an engine's model and a person's 1:1 rhythm live on
> that automation, project, engine or person. Settings never holds a copy.

The rule that decides where a control goes:

| If it is … | Its one home is … | Example |
|---|---|---|
| a fact about this Mac that HoldSpeak can find | **Setup** | gh is signed in; Claude Code is installed; the LAN engine answers |
| a preference about him or the whole desk | **Settings** | quiet hours, push-to-talk key, wallpaper, auto-record |
| an outside account | **Settings ▸ Accounts** (Setup shows the found ones with the same row) | Jira on acme-platform |
| which engine does which job | **Engines** (`../engines/DESIGN.md`) | meeting summaries on OpenRouter |
| a property of one object | **that object's window** | the Friday automation's schedule |

A feature window that has preferences shows one verb, **Settings**, in its
More menu. It opens Settings scrolled to its section, with the section lit.
It never draws a second copy of the controls.

### The words

| He sees | It replaces |
|---|---|
| **Setup** (title: "Set up HoldSpeak") | Get ready, Guide, "6 things need you", Test runtime |
| **Found on this Mac** | Optional setup, `SIGNED IN · 4`, `3 AGENTS FOUND` |
| **Use everything found** | (new) one press for every found row |
| **Works** / **Does not work: \<reason in words\>** | the yellow `Check` chip, Not working, Unreachable, Never checked, SIGN-IN UNKNOWN |
| **Speech**, **Engine**, **Accounts**, **Calendar**, **Agents**, **You and your people** | Speech model, Chat engines, Server or local chat, Where AI runs, Connections, Coding agents, Dictation AI model |
| **Let my agents use HoldSpeak** | Install hooks, "Hooks tell HoldSpeak when …" |
| **Uses your desk** | HOOKS |
| **Open my desk** | Continue later |
| **Notices** | Rhythm (the settings), Cadence, Pressure, Sweep |
| **Quiet hours** (one pair) | Quiet from / Quiet until (twice, two stores) |
| **Check** | Recheck, Retry, Check again, Test runtime |
| **Sign in** | Copy (a command), Sign-in command |
| **Agents act** (Secure · Normal · YOLO) | Posture |
| **Wallpaper** | Change places, Places |

### Setup

One window. The found things are the face. Each row is one thing, what
HoldSpeak found, its state in words, the egress chip where the press goes
out, and one verb.

Desktop (1440), the first open on his Mac:

```
┌ Set up HoldSpeak ──────────────────────────────── [ Use everything found ] ┐
│                                                                            │
│ FOUND ON THIS MAC                                                          │
│  ◖ Speech      Whisper base · 144 MB · runs on this Mac   HUGGINGFACE.CO [ Set up ] │
│  ◆ Engine      Qwen 3.8 27B · 192.168.1.43            YOUR NETWORK  [ Use ]  │
│  ◆ Engine      Claude Code · signed in                   ANTHROPIC  [ Add ]  │
│  ◆ Engine      Codex · signed in                            OPENAI  [ Add ]  │
│  ⑂ GitHub      karolswdev                                GITHUB.COM [ Use ]  │
│  ◇ Jira        karol@acme.example · acme             ACME.ATLASSIAN… [ Use ]  │
│  ◇ Jira        karol@acme.example · acme-platform    ACME-PLATFORM…  [ Use ]  │
│  ▤ Confluence  karol@acme.example · acme             ACME.ATLASSIAN… [ Use ]  │
│  ▦ Calendar    Work · Personal (this Mac)                           [ Use ]  │
│  ◉ Agents      Claude Code · Codex · pi        [ Let my agents use HoldSpeak ] │
│                                                                            │
│ YOU AND YOUR PEOPLE                                                        │
│  Your name     Karol                                              🎤       │
│  Your people   Mira Okafor, Theo Lindqvist, Jun Park              🎤 [ Add ] │
│                (from your calendar: 1:1 with Mira · 1:1 with Theo)         │
│                                                                            │
│ ▸ Not found (2): a model on this Mac (3 GB), an OpenRouter key             │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Use everything found** presses every row's verb, top to bottom, in one
  press. Each row turns to `● Works` as its press lands, so he watches the
  desk come alive. A row that fails says why in words and keeps its verb.
  What it includes is decision 1.
- **Speech** is the first row and the only download it starts by default. It
  shows the size and the host.
- **Engine rows** come from Engines' Found list (`../engines/DESIGN.md`,
  slice E2) and from the network look (decision 2). The LAN engine row says
  which jobs it takes: "Everything else", never speech. Speech always stays
  on this Mac.
- **Accounts rows** are the same component as the rows in Settings ▸
  Accounts. Two Jira rows for two sites show the site in the row, not only
  in the chip.
- **Calendar** reads his Mac's calendars (EventKit) and lists them by name.
  The press asks macOS for access once.
- **Agents**: one press for all found agents (see "Let my agents use
  HoldSpeak" below). Per agent, the row unfolds to show what each one got.
- **Your people** is one field. Typed or spoken names, separated by commas,
  each become a Person (a direct report by default; he changes that on
  People). When the calendar is in, recurring 1:1 events offer the names
  ("from your calendar: 1:1 with Mira"), and one press adds them.
- **Not found** is a closed fold with what HoldSpeak could not find, each
  with its one way in (download the local model; paste an OpenRouter key).
  It is absent when there is nothing in it.
- No section shows a count of zero. No row shows a verb that cannot work.

When every row works, the head becomes the finale:

```
┌ Set up HoldSpeak ──────────────────────────────────────────────────────────┐
│  Ready, Karol.                                                              │
│  Speech works · 3 engines · 4 accounts · 2 calendars · 3 people ·           │
│  Claude Code and Codex use your desk                                        │
│                                   [ Say one sentence ]   [ Open my desk ]   │
│  (the rows, folded to one line each, below)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Say one sentence** is today's First words, in place: he speaks, the text
appears under the button, and it is kept as a note. **Open my desk** closes
Setup and opens Today.

**Later opens** (HoldSpeak ▸ Setup, or a Needs-you setup row): the same
window. Rows that work fold into one line ("Works: speech, 3 engines, 4
accounts, calendar, agents"). Rows that do not work are on top, each with
its reason and its one fix. A new thing found since the last open (a new
acli site, a new CLI) shows under Found with its verb.

Phone (393): the same rows, one per line, the value under the label, and the
verb on the right. **Use everything found** is fixed at the bottom of the
window.

### Let my agents use HoldSpeak

One press, for each found agent (Claude Code, Codex, pi):

1. **Hooks**, as today, so the desk sees when the agent works, waits or
   stops.
2. **The desk's tools**: HoldSpeak's MCP server (`holdspeak-mcp`) is added to
   the agent's own user configuration, so his hand-run sessions can read his
   meetings, people, projects and decisions and write notes and drafts. Sends,
   settings and authority still stop for his press (`../mcp/DESIGN.md`).
3. **The skill**: `holdspeak --skill` (designed in `../agents/DESIGN.md`,
   slice AG13) is installed where the agent loads skills, so the agent knows
   how to work on his desk in its first turn.

The row then says, per agent: `Claude Code · uses your desk · tools ·
skill`. Unfolded, it has **Stop using my desk** (removes all three). The
Agents section of Settings shows the same rows.

### Settings

One page in one window, at least 880x720 at 1440. A short section index on
the left; the page scrolls on the right. No index of "Open …" buttons, no
wings, no sub-pages, no back button. Every row edits in place and saves at
once; the foot says `Saved 20:18`.

Desktop (1440):

```
┌ Settings ─────────────────────────────────────────────────────────────────┐
│ You         │ YOU                                                         │
│ Speak       │  Name               Karol                               🎤  │
│ Meetings    │  Also called        KS · Karol S.                       🎤  │
│ Notices     │ SPEAK                                                       │
│ Accounts    │  Speech             Whisper base · this Mac       ● Works   │
│ Agents      │  Push to talk       ⌥R                                      │
│ Desk        │  Language           Auto                                ▾   │
│ This Mac    │  Preview before typing      Off                             │
│             │  Voice commands     Off      Wake word  Off                 │
│             │  ▸ Spoken symbols   ▸ More                                  │
│             │ MEETINGS                                                    │
│             │  Make a summary     After every meeting                 ▾   │
│             │  Summaries run on   Qwen 3.8 27B · your network   Engines ›  │
│             │  Record by itself   Room meetings                       ▾   │
│             │  Microphone         System default                      ▾   │
│             │  Export             Off                                     │
│             │  ▸ More                                                     │
│             │ NOTICES                                                     │
│             │  Notify me          On the edge                         ▾   │
│             │  Quiet hours        22:00 – 08:00                           │
│             │  Daily brief        06:00                         On        │
│             │  Desk sounds        On                                      │
│             │  ▸ More                                                     │
│             │ ACCOUNTS  (see below)                                       │
│             │ AGENTS                                                      │
│             │  Claude Code        uses your desk · tools · skill  ● Works │
│             │  Codex              hooks only            [ Let it use … ]  │
│             │  Agents act         Secure · Normal · YOLO                  │
│             │  People for agents  Off · Read · Read and write             │
│             │ DESK                                                        │
│             │  Wallpaper          (the gallery, in place)                 │
│             │  Motion             On       Presence  Off                  │
│             │ THIS MAC                                                    │
│             │  Engines            3 engines              Engines ›        │
│             │  Setup              all works              Setup ›          │
│             │  Other devices      Off                                     │
│             │  Name of this Mac   Karol's MacBook                         │
│             │  Reset the desk     [ Reset… ]                              │
└────────────────────────────────────────────────────────────── Saved 20:18 ┘
```

- **Each section holds only preferences.** Engines and Setup are rows that
  open their own windows; they are not copied in.
- **More** folds hold today's Advanced rows, unchanged, closed by default.
- **Search finds rows.** ⌘K "quiet" lists `Quiet hours · Settings` and opens
  Settings at that row, lit. Every row label is in the palette.
- **The section index** marks a section that has a problem (for example
  `Accounts ●` when an account does not work), and nothing else.
- **Speech's line tells the truth**: it reads whether speech works, not a
  switch.

Phone (393): one column. The section index becomes a row of section words
at the top of the window that wraps (no sideways scroll). A choice opens as
a list under its row, never as a modal.

### Accounts (a section of Settings)

```
│ ACCOUNTS                                                                  │
│  ⑂ GitHub      karolswdev · github.com         ● Works · 2 min ago  [ Check ] │
│  ◇ Jira        karol@acme.example · acme             ● Works        [ Check ] │
│  ◇ Jira        karol@acme.example · acme-platform    ● Works        [ Check ] │
│  ▤ Confluence  karol@acme.example · acme             ● Works        [ Check ] │
│  ▦ Calendar    Work · Personal (this Mac)            ● Works                │
│  ▦ Calendar    Team on-call (link)                   ● Works                │
│  ✉ Email       karol@… (SMTP)                        ● Works        [ Check ] │
│  Found on this Mac: Jira · karol@contoso.example · contoso     [ Use ]     │
│                                                    [ Add an account ]     │
```

- **One row per account and site.** The state is in words: `Works`, `Not
  signed in`, `Signed in as another account`, `Could not check: gh is not
  installed`, `Could not check: <the CLI's own words>`. The egress chip sits
  on the Check verb, where the check goes out.
- **Check** runs the CLI's own status read, and then **leaves acli on the
  account it was on before**. It never changes the account he uses in his
  terminal.
- **Pressing a row** unfolds it in place: what uses this account (projects,
  automations, Send destinations), **Sign in again**, **Remove**.
- **Add an account** unfolds tiles: GitHub, Jira, Confluence, Calendar,
  Email, Slack. Jira asks Site and Email, then **Sign in** opens a terminal
  pane in place that runs the CLI's own sign-in (`gh auth login --web`,
  `acli jira auth login …`). When the CLI finishes, Check runs by itself and
  the row says Works. He never copies a command. Signing in stays the CLI's
  job; HoldSpeak never reads or stores the token.
- **Calendar has its one home here.** Settings ▸ Meetings no longer has a
  calendar block; first-run's Calendar card is the same row.
- **Destinations** (Send) stay where `../send/` will put them. Until then
  they keep their place below Accounts, and each account row says how many
  destinations use it.
- **Removed from Accounts**: the `Runs on 4 of 7 assigned` row (Engines owns
  it) and the Credentials fold (each secret moves onto the row of the
  service that uses it: the email key on Email, the webhook on Slack).

### Rhythm and Wallpaper: one home each

- **Rhythm** stops being a window. Its preferences are Settings ▸ Notices:
  notify me, quiet hours (one store, the one the notices loop reads), the
  daily brief time, desk sounds. The sweep interval and its Run now go
  behind More and RAW. The cadence loops become Automations (PLAN §2;
  `../workbench/DESIGN.md`). Search "Rhythm" opens Settings ▸ Notices.
  Telegram becomes a row in Accounts.
- **Wallpaper** lives in Settings ▸ Desk. The Change places app is parked;
  ⌘⇧P opens Settings at Wallpaper (Recon R7: cut Places as an app).
- Saved desks that hold `surface-cadence` or `surface-places` open the new
  home.

### Setup by command and by asking

- `holdspeak setup` prints the same rows in the terminal, with the same
  words. `holdspeak setup --yes` presses Use everything found.
  `holdspeak doctor` stays, and prints the same rows plus the hub checks.
  An architect who lives in the terminal can install and set up without
  opening a window.
- MCP: `setup.status` (the rows) and `setup.use` (one row or all found).
  `setup.use` is CONFIG, so in a Thread it stops for his press; from his
  own Claude Code with the owner credential it just works, under the
  existing classes (`../mcp/DESIGN.md`). An agent he asks "set up my desk"
  can therefore do it.
- Settings rows are already on MCP (`settings.get`, `settings.update`).

### What each press does

| Verb | Where | One press does |
|---|---|---|
| **Use everything found** | Setup head | Presses every Found row's verb in order; each row shows Works or its reason |
| **Set up** (Speech) | Setup | Downloads the speech model (size and host shown) and checks it; the row says Works |
| **Use** (an engine) | Setup | Adds the engine and makes it the engine for Everything else; speech stays on this Mac |
| **Add** (an agent engine) | Setup | Adds Claude Code or Codex as an engine (`../engines/` E2) |
| **Use** (an account) | Setup, Accounts | Adds the account and checks it; Works in about 4 s |
| **Let my agents use HoldSpeak** | Setup, Settings ▸ Agents | Hooks + MCP server entry + skill for each found agent; each row says what it got |
| **Stop using my desk** | an unfolded agent row | Removes the hooks, the MCP entry and the skill for that agent |
| **Add** (your people) | Setup | Makes a Person for each name; they appear in People at once |
| **Say one sentence** | Setup finale | Records one sentence and shows the text; keeps it as a note |
| **Open my desk** | Setup finale | Closes Setup and opens Today |
| **Check** | an account row | Runs the status read; restores acli's previous account; shows Works or the reason |
| **Sign in** | Add an account, a row that is not signed in | Opens a terminal pane in place with the CLI's sign-in; Check runs when it ends |
| **Remove** | an unfolded account row | Removes the account from HoldSpeak (not from the CLI); Undo for 8 s |
| **Settings** | a feature window's More menu | Opens Settings at that feature's section |
| **Engines ›**, **Setup ›** | Settings | Opens that window |

### What is removed or parked (nothing is deleted)

| Thing | Where it goes |
|---|---|
| Get ready (first-run card) | Becomes the Setup window, opened on first launch |
| Settings ▸ Guide wing | Removed; Setup is in the HoldSpeak menu and in Settings ▸ This Mac |
| The Settings index of `Open …` rows, the wings, `« Settings` | Replaced by the one page |
| Setup's `Check` chips, `Test runtime`, `Trust destinations`, `People keystore` (shown only when it is a real problem) | Words on the row, or behind RAW |
| The Rhythm window | Parked; Search "Rhythm" opens Settings ▸ Notices |
| Change places | Parked; ⌘⇧P opens Settings ▸ Desk |
| Calendar block in Settings ▸ Meetings | Accounts |
| `Runs on 4 of 7 assigned` in Accounts; `Change engine` in Meetings | Engines (a fact line with `Engines ›`) |
| `Use this for summaries` in first run | Setup's engine row `Use` (Everything else, never speech) |
| `Continue later` | `Open my desk` (and the window can be closed like any window) |
| The seed note that first run puts on the desk (`/api/desk/seed`) | Not part of Setup; PLAN track T3 moves the seed notes |
| The Credentials fold | Each secret on its service's row |

## 5. Decisions for the owner

1. **What "Use everything found" includes.** Recommended: every found row,
   including the 144 MB speech download and adding Claude Code and Codex as
   engines, and his agents' access to the desk. Never the 3 GB local model
   (that stays in Not found, one press of its own). It is one press of his,
   and each row still shows its egress chip.
2. **Setup looks on his network when it opens.** The LAN scan is an owner
   press today by design (`lan_engine_discovery.py:1-8`): it sends GET
   requests to private addresses only, and reads no key. Recommended: yes,
   look once each time Setup opens, and show the result as a Found row. It
   is his own network, and a hidden press is the reason his LAN engine was
   not found (Tenet 1: no over-engineering for safety).
3. **His hand-run agents get the desk's tools with his own authority.**
   "Let my agents use HoldSpeak" writes HoldSpeak's MCP server into his own
   Claude Code and Codex configuration. Those sessions then act as the
   owner, under the same rules as today's owner MCP client: egress, authority
   and config stop for his press. Recommended: yes, per agent, with Stop
   using my desk to undo it.

This design also applies the PLAN §2 ruling "Configuration → Settings"
with one sharpening: Settings holds **preferences**; a property of one
object stays on that object. That is how the ruling already works for
Automations and Engines, so it is not a new ruling.

## 6. How we know it worked

On a fresh desk on his own Mac (gh and acli signed in, Claude Code and
Codex installed, the LAN engine up), he:

- opens HoldSpeak, presses **Use everything found**, types or says his
  three people, and presses **Open my desk**: **at most 4 presses and one
  field, under 3 minutes plus the speech download, in one window**;
- then dictates a sentence that types, asks a question that the LAN engine
  answers, and sees his Jira sites in a new project's sources, with no
  question to us;
- opens his own Claude Code in a terminal and asks it "what did Mira commit
  to this week?", and it answers from the desk.

Later:

- He changes his quiet hours from anywhere in **2 presses** (⌘K "quiet",
  then the value), and Notices, Today and the notices loop agree.
- He adds a third Jira site in **at most 4 presses and two fields**,
  without copying a command.
- No two faces disagree about a fact: Speech, Rhythm, an account, an engine.
