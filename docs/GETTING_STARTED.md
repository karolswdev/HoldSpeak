# HoldSpeak Getting Started

<p align="center">
  <img src="assets/pixellab/hold-to-talk-microphone.png" alt="Pixel art microphone with hold-to-talk waves" width="128">
</p>

Five minutes from install to speaking a sentence into another app: that is
this guide's whole job. After you install and run `holdspeak doctor`, setup
is three moves, in this order:

1. **Seed the desk.** A fresh install is an empty floor. One press, or
   `holdspeak seed`, puts six drawers and two starter notes on it.
2. **Set the dial.** Settings, Models is the one place endpoint and model
   identity is edited: a destination list, and a Runs on picker per feature.
3. **Hold the key.** Hold the hotkey anywhere, speak, release, and the words
   land in the app you were in. The Speak window is the same act with a face.

Voice typing is the foundation everything else (the dictation pipeline,
meetings) builds on, so get move 3 working before you turn anything else on.

## 1. Install

From a checkout:

```bash
uv pip install -e .
```

Linux users should install system audio dependencies first:

```bash
sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
uv pip install -e '.[linux]'
```

If you want meeting intelligence or local llama.cpp meeting analysis:

```bash
uv pip install -e '.[meeting]'
```

## 2. Run Diagnostics

Run:

```bash
holdspeak doctor
```

Fix anything marked as failing before debugging higher-level features.
The most important checks are microphone access, transcription backend,
hotkey support, text insertion support, web runtime, and optional LLM
runtime status. `doctor` also reports the database schema and config state,
so you know it is healthy before and after an upgrade.

Later, when you upgrade HoldSpeak, you can snapshot your data first with
`holdspeak backup` and put a snapshot back with `holdspeak restore`. Upgrades
are safe by default; see [`RELEASING.md`](RELEASING.md) for what happens to your
data on a version change.

## 3. Start HoldSpeak

Run:

```bash
holdspeak
```

This starts the local web runtime on loopback (`127.0.0.1`). On a fresh install
the terminal points you at the Desk and your first words:

```text
HoldSpeak web runtime is running at: http://127.0.0.1:PORT
  → Welcome! Say your first words on the Desk: open http://127.0.0.1:PORT/
```

## 4. Move 1: seed the desk

A fresh install is an empty floor. Nothing is seeded at boot: you ask for it.

Press **Seed the desk** on the empty floor, or run:

```bash
holdspeak seed
```

Either way you get six drawers (ADRs, Meetings, Rules, Decisions, Reference,
Inbox) and two starter notes filed into them: an **ADR template** and
**Working rules**. The seed upserts by deterministic id, so running it twice
leaves one desk, and it only ever touches its own objects.

To go back to that state later, open **Settings, Desk** and arm **Reset to
seed**. It states what it clears (notes, knowledge, agents, workflows,
drawers, layout) and what it keeps (meetings, journal, settings, Runs on
targets) before you confirm, then reports `TOMBSTONED N · SEEDED M`. The
deletions are tombstones, so a paired device cannot resurrect the clutter.

## 5. Move 2: set the dial

Open **Settings, Models**. This is the only face that edits endpoint and model
identity.

1. Under **Destinations**, add a target: a name, a kind (`ENDPOINT`,
   `THIS DEVICE`, `PAIRED`, `MESH`), its base URL, its model, and its context
   window. A lamp reports readiness, and the key column reads `SET` or
   `UNSET`.
2. If the destination needs a key, put it in the environment as
   `HOLDSPEAK_PROFILE_<ID>_KEY`. The key is never stored in the destination
   and never syncs; the hub joins it to the request at run time. A destination
   never borrows another one's key.
3. Press **PROBE** to test the dictation leg against the selected
   destination.
4. Under **Runs on**, point each feature at a destination: dictation,
   meetings, and rails. Leaving one on `HUB DEFAULT` runs it on the hub's own
   engine, which you configure in the same module (backend `AUTO` / `MLX` /
   `LLAMA.CPP`, model, context window, warm on start, idle eviction).

The old config fields (`meeting.intel_cloud_*`, `dictation.runtime.openai_compatible_*`)
no longer configure anything. An upgrade reads a configured legacy endpoint
once, turns it into a destination named `legacy-intel` or `legacy-dictation`,
and points the matching feature at it. After that the destination is the truth.
The legacy key environment variable deliberately does not carry over: give the
new destination its own `HOLDSPEAK_PROFILE_<ID>_KEY`.

See [Models (bring your own)](MODELS.md) for what to run, and
[Inference destinations](INFERENCE_TARGETS.md) for the API contract.

## 6. The Desk, in passing

A returning user lands on **the Desk** (there is no wizard): your
meetings, notes, knowledge bases, and agents as objects in a spatial world.
Tap an object to open it in place, drag it onto a zone to file it, press the
orb to record, and ask an agent from the rail: its answer lands on the desk
as an artifact you can open, trace (`via` the agent that made it), and file.
Every input takes speech: hold the mic, talk, release (the hub's own local
Whisper transcribes; nothing leaves your machine's runtime). A fresh desk says what
HoldSpeak is and offers your next action. If something later needs
attention, the **Setup window** (deep link `/setup`) is the calm health
surface, and the egress
badge in the Desk's corner always shows what can leave your machine.

The web surface IS the Desk: every mode opens as a window on it. The menu
(top left) and the tool shelf open Dictation, Meetings, Studio, Settings,
and the rest as floating windows you can drag, resize, snap to an edge,
minimize to the dock, or maximize. Nothing navigates away from the Desk.

Old route addresses still work as deep links; each lands on the Desk with
the matching window open:

| Deep link | Opens the window |
| --- | --- |
| `/welcome` | A compatibility route to the same first-words atom the Desk shows |
| `/` | The Desk itself: your primitives as a spatial world (record, create, open, file, run) |
| `/dictation` | Speak: the TALK key and its Aim row, the journal, learning, pre-briefing. An optional preview mode (Settings, Voice) shows each dictation on a card first: Type it commits, Discard drops it. |
| `/history` | Meetings: capture or import, the archive, aftercare |
| `/studio` | Studio: the advanced tier (Workbench, Cadence, Commands, and more) |
| `/settings` | Settings (sectioned and searchable) |
| `/setup` | Setup and health: readiness plus the single next step |

## 7. Move 3: hold the key

The flagship act, on the global hotkey:

1. Start HoldSpeak with `holdspeak`.
2. Click into a text field in another app.
3. Hold the configured hotkey.
4. Speak.
5. Release the hotkey.

Default hotkey:

- macOS: Right Option
- Linux: Right Alt

If global hotkeys or synthetic typing are blocked, keep the HoldSpeak window
focused and use the focused hold-to-talk fallback.

The same act has a face on the Desk. Open **Speak** (deep link `/dictation`)
and it delivers for real through the same route, pipeline, journal, and
kernel warrant as the hotkey:

- **Aim** says where a released **TALK** sends the words: `FOCUSED APP`
  types into the app you were in, `AGENT` delivers into a coder session that
  is waiting, and `THIS FIELD` just fills the well below. The pick is
  remembered.
- Aimed at `AGENT` it refuses when no session is awaiting (`NO AGENT
  AWAITING`) rather than free-typing into whatever happens to be focused.
  Other refusals read the same way: `NO FOCUSED APP`, `NO TYPING DRIVER`,
  `KERNEL REFUSED`.
- The receipt reports release-to-landed latency in milliseconds.
- **REHEARSE** is the explicit dry run. It previews the pipeline and delivers
  nothing, and it is never what a plain release does.

### The open mic

**OPEN MIC** is the latch next to TALK, for when you do not want to hold
anything:

- **One grant.** The browser is asked for the microphone once and the grant is
  kept. Between utterances the session suspends (the audio context suspends
  and the tracks are disabled, so nothing is captured) rather than asking
  again. A pause longer than 15 seconds releases the device on its own.
- **Utterances land the same way.** A voice-activity detector on this machine
  decides where each utterance starts and ends (energy with hysteresis and a
  700 ms hangover, 300 ms of pre-roll so the first phoneme survives). Each one
  goes through the same transcription route, the same Aim, and the same
  delivery contract as a held release, so an ambient utterance and a held one
  are indistinguishable downstream. Speech shorter than 350 ms is a cough, not
  words: it is dropped. An empty transcript is dropped silently, without
  spending a delivery, a journal row, or a receipt.
- **Holding wins.** TALK, the global hotkey, and any mic on the Desk preempt
  the open mic: while a hold is live the ambient path is gated off and its
  in-flight utterance is discarded. One floor, one owner, the same as the
  physical key.
- **The lamp does not lie.** The Desk chrome carries a mic lamp that reads
  `Mic idle`, `Mic open`, `Mic speech`, or `Mic held` from every room. It is
  absent only when the device is genuinely released, so its presence is the
  honest signal that audio is live. Pressing OPEN MIC again stops the tracks
  for real; it does not mute them.
- **The floor is shared with the rest of the machine.** The browser claims the
  same one-at-a-time audio floor the hotkey, the meeting recorder, and the
  wake listener use, on a lease it heartbeats. If a meeting holds it, the claim
  is refused with the owner named (`FLOOR HELD MEETING`) and the device never
  opens. If a meeting takes it mid-session, the mic goes down first and the
  room tells you who took it. The lease means a closed tab cannot wedge your
  hotkey.

A browser that cannot capture audio shows OPEN MIC disabled with the reason on
it, rather than hiding it. Serving the hub over plain HTTP to another machine
is the usual cause: browsers withhold the microphone outside a secure origin,
so reach it over localhost or HTTPS.

> **Tip: see what the copilot is doing without the dashboard.** Turn on **desktop
> presence** in **Settings** (or set `presence.enabled` in your config) to get an
> ambient, native surface (a floating HUD on macOS and X11, a tray glyph plus
> notification everywhere). It shows whether it's listening, transcribing, or typing
> while you dictate into another app, and it never takes keyboard focus. For a
> headless launch you can force it on with `HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak`.
> See [Desktop Presence](DICTATION_PIPELINE_GUIDE.md#11-desktop-presence-ambient-on-desktop-status).

## 8. Use Punctuation Commands

Say punctuation naturally:

| Say | Inserts |
| --- | --- |
| `period` or `full stop` | `.` |
| `comma` | `,` |
| `question mark` | `?` |
| `exclamation mark` | `!` |
| `new line` | line break |
| `new paragraph` | blank line |

You can add your own spoken symbols, and pin transcription to your
language, under **Settings, Voice typing**. The
[User Guide](USER_GUIDE.md) covers both.

Example:

```text
hello comma can you review this question mark
```

becomes:

```text
Hello, can you review this?
```

## 9. Use Clipboard Insertion

Say `clipboard` inside a dictated phrase when you want HoldSpeak to splice in
the current clipboard text. The word `clipboard` is removed from the output and
replaced with the clipboard contents.

Example:

```text
Taking a look at this clipboard could you refactor it?
```

If the clipboard contains a code block, that code is inserted into the same
dictated request before HoldSpeak types or pastes it.

## 10. Set Up A Project Root

Open:

```text
/dictation
```

Use the **Project root** bar to select the repository you are actively working
in. This lets HoldSpeak find project blocks, project knowledge, `.hs/` context,
and agent-hook state.

Good project markers include:

- `.git/`
- `pyproject.toml`
- `package.json`
- `.holdspeak/`
- `.hs/`

## 11. Enable The Dictation Pipeline Later

Do not enable the dictation LLM pipeline until basic typing is working.
When ready, continue with:

- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md)
- [User Guide](USER_GUIDE.md)

## 12. Where To Go Next

Once hold-to-talk feels natural, the rest is one setting away each:

- **Hands-free**: [the wake word](USER_GUIDE.md#the-wake-word) listens for a
  phrase and previews the result before anything is typed.
- **Your language**: [the spoken language setting](USER_GUIDE.md#speak-your-language) pins any of
  Whisper's 99 languages, and [the spoken-symbol dictionary](USER_GUIDE.md#punctuation)
  types your own vocabulary.
- **Spoken actions**: [voice commands](VOICE_COMMANDS.md) map a keyword to a
  real action.
- **Meetings**: [the Meeting Mode Guide](MEETING_MODE_GUIDE.md) covers live
  capture, importing recordings or transcripts you already have, and the
  aftercare that closes the loop.
- **From another device**: an iPad [companion](USER_GUIDE.md#companions) drives
  both modes over the hub's local API: dictate into your desk, read a meeting
  back with its artifacts and sources, and approve a proposal.

## Troubleshooting

| Symptom | Likely cause | First fix |
| --- | --- | --- |
| Hotkey does nothing | OS blocked global hooks | Run `holdspeak doctor`; try focused fallback |
| Text does not appear | Synthetic typing blocked | Try clipboard/manual paste fallback |
| Transcription is unavailable | Missing backend/model | Run `holdspeak doctor` |
| Web UI does not open | Browser auto-open disabled or blocked | Visit the printed local URL manually |
| Project is wrong | Started from another cwd | Set Project root in the Dictation window |

## See also

- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): once basic voice typing
  works, turn on the project-aware copilot.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): meeting-specific setup and capture.
- [Models (bring your own)](MODELS.md): pick and point at an LLM.
- [Inference destinations](INFERENCE_TARGETS.md): the destination contract behind
  Settings, Models.
- [Security & Privacy](SECURITY.md): what's stored and what can leave your machine.
