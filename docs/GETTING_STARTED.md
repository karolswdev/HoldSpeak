# HoldSpeak Getting Started

<p align="center">
  <img src="assets/pixellab/hold-to-talk-microphone.png" alt="Pixel art microphone with hold-to-talk waves" width="128">
</p>

Five minutes from install to speaking a sentence into another app: that is
this guide's whole job. Voice typing is the foundation everything else
(the dictation pipeline, meetings) builds on, so get this working first;
the deeper guides pick up where it ends.

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
the terminal points you straight at the welcome wizard:

```text
HoldSpeak web runtime is running at: http://127.0.0.1:PORT
  → Welcome! Get set up in a minute: open http://127.0.0.1:PORT/welcome
```

## 4. The welcome wizard

A fresh launch opens **`/welcome`**, a full-screen, step-by-step wizard that
takes you from install to your first words, **no file editing**:

1. **Welcome**: what HoldSpeak does (voice typing *and* meeting notes).
2. **Permissions**: a live check of microphone, text insertion, and the hotkey
   (they turn green as you grant them).
3. **Model**: pick your intelligence level (Basic / Apple MLX / GGUF /
   OpenAI-compatible), each with a one-click **Test**. Basic needs nothing.
4. **First dictation**: hold your hotkey, speak, release; it celebrates
   **"✓ It worked"** live and shows your transcript.
5. **Desktop presence**: flip a switch (no env var) for the ambient HUD.
6. **You're set**: jump into dictation, a meeting, or the copilot.

![The HoldSpeak welcome wizard: a full-screen first-run screen headlined "Hold a key. Speak. Watch it type." with a step rail (Welcome · Permissions · Model · First dictation · Presence · You're set) and a "Get started" button; the footer reads "Local · 127.0.0.1".](assets/screenshots/welcome.png)

*The `/welcome` wizard on a fresh install. It takes you from a fresh clone to a verified first dictation, with no file editing.*

A returning user lands on **the Desk** instead (the wizard never nags): your
meetings, notes, knowledge bases, and agents as objects in a spatial world.
Tap an object to open it in place, drag it onto a zone to file it, press the
orb to record, and ask an agent from the rail: its answer lands on the desk
as an artifact you can open, trace (`via` the agent that made it), and file.
Every input takes speech: hold the mic, talk, release (the hub's own local
Whisper transcribes; nothing leaves your machine's runtime). A fresh desk says what
HoldSpeak is and offers your next action. If something later needs
attention, **`/setup`** is the calm Setup and health surface, and the egress
badge in the Desk's corner always shows what can leave your machine.

The web surface is the Desk plus three rooms reached from its menu: the two
modes (**Dictation**, **Meetings**) and **Studio** for the advanced tools.
Everything else nests under one of those.

Useful routes:

| Route | Purpose |
| --- | --- |
| `/welcome` | The first-run wizard: the single arrival on a fresh install |
| `/` | The Desk: your primitives as a spatial world (record, create, open, file, run) |
| `/dictation` | Dictation mode: voice typing, the journal, learning, pre-briefing. An optional preview mode (Settings, Voice) shows each dictation on a card first: Type it commits, Discard drops it. |
| `/history` | Meetings mode: capture or import, the archive, aftercare |
| `/studio` | Studio: the advanced tier (Workbench, Cadence, Commands, and more) |
| `/settings` | Global settings (sectioned and searchable; open from the ⚙) |
| `/setup` | Setup and health: readiness plus the single next step |

## 5. Try Basic Voice Typing

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

> **Tip: see what the copilot is doing without the dashboard.** Turn on **desktop
> presence** in **Settings** (or set `presence.enabled` in your config) to get an
> ambient, native surface (a floating HUD on macOS and X11, a tray glyph plus
> notification everywhere). It shows whether it's listening, transcribing, or typing
> while you dictate into another app, and it never takes keyboard focus. For a
> headless launch you can force it on with `HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak`.
> See [Desktop Presence](DICTATION_PIPELINE_GUIDE.md#11-desktop-presence-ambient-on-desktop-status).

## 6. Use Punctuation Commands

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

## 7. Use Clipboard Insertion

Say `clipboard` inside a dictated phrase when you want HoldSpeak to splice in
the current clipboard text. The word `clipboard` is removed from the output and
replaced with the clipboard contents.

Example:

```text
Taking a look at this clipboard could you refactor it?
```

If the clipboard contains a code block, that code is inserted into the same
dictated request before HoldSpeak types or pastes it.

## 8. Set Up A Project Root

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

## 9. Enable The Dictation Pipeline Later

Do not enable the dictation LLM pipeline until basic typing is working.
When ready, continue with:

- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md)
- [User Guide](USER_GUIDE.md)

## 10. Where To Go Next

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
| Project is wrong | Started from another cwd | Set Project root in `/dictation` |

## See also

- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): once basic voice typing
  works, turn on the project-aware copilot.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): meeting-specific setup and capture.
- [Models (bring your own)](MODELS.md): pick and point at an LLM.
- [Security & Privacy](SECURITY.md): what's stored and what can leave your machine.
