# HoldSpeak Getting Started

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

This starts the local web runtime on loopback (`127.0.0.1`). The browser UI is
the main cockpit for dictation, meetings, history, runtime configuration, and
project context.

Useful routes:

| Route | Purpose |
| --- | --- |
| `/` | Runtime dashboard |
| `/dictation` | Dictation readiness, blocks, project context, runtime, dry-run |
| `/history` | Meeting history and artifacts |
| `/docs/dictation-runtime` | Runtime backend setup help |

## 4. Try Basic Voice Typing

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

## 5. Use Punctuation Commands

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

## 6. Set Up A Project Root

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

## 7. Enable Intelligent Typing Later

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
