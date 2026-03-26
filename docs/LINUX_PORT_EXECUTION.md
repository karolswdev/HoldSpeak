## HoldSpeak Linux Port: execution coordination

This document coordinates parallel work on Linux support. It complements `docs/LINUX_PORT_PLAN.md` (research/strategy) with concrete, parallelizable tasks, deliverables, and a definition of done.

### Scope / definition of done (baseline)

Baseline means:
- `uv pip install -e '.[linux]'` works on Ubuntu/Debian without requiring Apple-only deps.
- `holdspeak` launches and the TUI is usable.
- Voice typing works at least when HoldSpeak is focused (even if global hotkey and cross-app paste injection are limited on Wayland).
- `holdspeak meeting --setup` provides Linux instructions, and mic-only meeting capture works.
- System-audio capture works on PipeWire/PulseAudio machines when a monitor source exists (via PortAudio device *or* `ffmpeg` Pulse input fallback).
- CI includes a Linux smoke import/test that never downloads a model.

Non-goals for baseline:
- Perfect global hotkeys on Wayland for all compositors.
- Tray/menu-bar parity with macOS `rumps` mode.

### Branching / integration guidance

To reduce merge conflicts, split work into small PRs/branches aligned with workstreams below, and land them in this order:
1) Packaging + backend selection (unblocks Linux install)
2) Linux audio loopback capture + meeting UX
3) Wayland/X11 fallbacks + diagnostics UX
4) CI smoke tests + docs polish

### Workstreams (can run in parallel)

#### Workstream A — Packaging + transcription backend selection

Goal: Linux install and transcription backend selection are correct and predictable.

Deliverables:
- `pyproject.toml` uses a platform marker for `mlx-whisper` and introduces a `linux` extra for `faster-whisper`.
- `holdspeak/transcribe.py` supports `backend=auto|mlx|faster-whisper` and produces actionable errors when backends aren’t installed.
- `README.md` has Linux install instructions that match actual behavior.

Checklist:
- `pip/uv` on Linux never tries to install `mlx-whisper`.
- `Transcriber(backend="auto")` chooses MLX only on `darwin/arm64`, otherwise attempts `faster-whisper`.
- Errors say what to install (`.[linux]`) rather than generic import traces.

#### Workstream B — Linux system-audio capture (PipeWire/PulseAudio)

Goal: meeting mode can record “what you hear” reliably on Linux (with clear setup guidance).

Deliverables:
- `holdspeak/audio_devices.py` discovers the default sink monitor source via `pactl` when available.
- `holdspeak/meeting.py` can capture system audio via:
  - a PortAudio input device (if visible to `sounddevice`), or
  - `ffmpeg -f pulse -i <source>.monitor` fallback when PortAudio can’t see monitor sources.
- `holdspeak meeting --setup` prints Linux-appropriate instructions and a detected monitor source when possible.

Checklist:
- Works on PipeWire with `pipewire-pulse` (common default).
- Works on PulseAudio.
- Fails gracefully when `pactl` is missing and provides instructions.

#### Workstream C — Wayland/X11 fallbacks (hotkey + paste injection)

Goal: HoldSpeak remains usable when `pynput` can’t do global hooks or cross-app paste (common on Wayland).

Deliverables:
- TUI provides a focused-only “hold-to-talk” binding that does not require global key hooks.
- Diagnostics screen clearly reports:
  - `XDG_SESSION_TYPE`, `WAYLAND_DISPLAY`, `DISPLAY`
  - whether global hotkey is enabled/disabled and why
  - whether text injection is enabled/disabled and why
- Text injection behavior is explicit on Wayland (e.g., “copied to clipboard; paste manually”).

Checklist:
- On Wayland with `pynput` disabled, user can still record/transcribe via in-app control.
- User-facing messaging explains limitations without crashing.

#### Workstream D — CI + Linux smoke tests

Goal: Linux regressions are caught early without requiring real audio devices or model downloads.

Deliverables:
- `.github/workflows/test.yml` installs the correct dependency set for Linux unit tests (do not require MLX).
- A smoke test that imports key modules and exercises lightweight logic:
  - import `holdspeak.transcribe.Transcriber`
  - verify backend selection logic
  - verify Linux monitor-source parsing doesn’t explode when `pactl` absent

Checklist:
- Ubuntu CI passes without GPU/audio hardware.
- Tests avoid downloading Whisper models (mark/skip anything that would).

### Linux host verification (karol@192.168.1.75)

Run this on the Linux machine after Workstream A lands:
- Optional: run `scripts/linux_smoke.sh` for a quick non-GUI sanity check.
- Install OS deps: PortAudio dev headers, `ffmpeg`, clipboard helper (`xclip`/`wl-clipboard`), `pactl`/PipeWire Pulse compatibility.
- `uv pip install -e '.[linux]'`
- `python -c "from holdspeak.transcribe import Transcriber; print('import ok')"`
- `holdspeak meeting --setup`
- (If X11) verify hotkey + paste injection; (if Wayland) verify focused-only fallback path.

If something needs a screen (TUI behavior), coordinate with the laptop session for visual confirmation.
