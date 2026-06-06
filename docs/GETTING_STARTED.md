# HoldSpeak Getting Started

<p align="center">
  <img src="assets/pixellab/hold-to-talk-microphone.png" alt="Pixel art microphone with hold-to-talk waves" width="128">
</p>

This guide gets HoldSpeak installed, running, and typing into another app.
Use it first; then move to the intelligent-typing guide when basic voice
typing works.

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
runtime status.

## 3. Start HoldSpeak

Run:

```bash
holdspeak
```

This starts the local web runtime on loopback (`127.0.0.1`). On a fresh install
the terminal points you straight at the guided setup:

```text
HoldSpeak web runtime is running at: http://127.0.0.1:PORT
  → First-run setup: open http://127.0.0.1:PORT/setup — N things need attention
    Next: <the single next step>
```

## 4. Open Setup — the guided home

Open **`/setup`** (a fresh install opens it for you). It's a single, calm
checklist driven by `holdspeak doctor` under the hood — **no file editing**:

- one **headline** ("Everything's ready" / "N things need attention") + a
  progress bar;
- exactly **one primary action** — the single next step to fix;
- a **"Try your first dictation"** guide that confirms text landing in another
  app (it celebrates "✓ It worked" live), an **optional model assistant** (Basic
  / Apple MLX / GGUF / OpenAI-compatible, each with a one-click **Test**), and a
  **presence** step;
- a **Privacy** chip in the header (on every page) that shows, at a glance, what
  can leave your machine — click it for the full Trust & Privacy panel.

A healthy returning user lands on the normal dashboard instead — setup never nags.

Useful routes:

| Route | Purpose |
| --- | --- |
| `/setup` | The guided first-run home — readiness, one next step, first dictation |
| `/` | Runtime dashboard |
| `/settings` | Global settings (open from the ⚙ on any page) |
| `/dictation` | Dictation readiness, blocks, project context, runtime, dry-run |
| `/history` | Meeting history and artifacts |

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

> **Tip — see what the copilot is doing without the dashboard.** Launch with
> `HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak` to get an ambient, native presence
> surface (a floating HUD on macOS / X11, a tray glyph + notification
> everywhere) that shows *listening / transcribing / typing* while you dictate
> into another app — and never steals keyboard focus. See
> [Desktop Presence](INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status).

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

## 9. Enable Intelligent Typing Later

Do not enable the dictation LLM pipeline until basic typing is working.
When ready, continue with:

- [Intelligent Typing Setup](INTELLIGENT_TYPING_GUIDE.md)
- [User Guide](USER_GUIDE.md)

## Troubleshooting

| Symptom | Likely cause | First fix |
| --- | --- | --- |
| Hotkey does nothing | OS blocked global hooks | Run `holdspeak doctor`; try focused fallback |
| Text does not appear | Synthetic typing blocked | Try clipboard/manual paste fallback |
| Transcription is unavailable | Missing backend/model | Run `holdspeak doctor` |
| Web UI does not open | Browser auto-open disabled or blocked | Visit the printed local URL manually |
| Project is wrong | Started from another cwd | Set Project root in `/dictation` |

For meeting-specific setup, see [Meeting Mode Guide](MEETING_MODE_GUIDE.md).
