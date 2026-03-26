## HoldSpeak on Linux: research + implementation plan

### Execution coordination (parallel work)

For a concrete, parallelizable task breakdown (workstreams, definition of done, and Linux host verification checklist), see:
- `docs/LINUX_PORT_EXECUTION.md`

For the broader macOS + Linux execution plan (milestones, acceptance gates, and cross-platform DoD), see:
- `docs/CROSS_PLATFORM_ROADMAP.md`

### Executive summary (what blocks Linux today)

HoldSpeak is *close* to being cross-platform at the TUI layer (Textual) and basic mic capture (PortAudio via `sounddevice`), but several “core” pieces are currently macOS/Apple-Silicon-centric:

- **Transcription backend**: `holdspeak/transcribe.py` is built on **`mlx-whisper`** (MLX), which is **Apple Silicon only**.
- **System audio capture** (“remote participants”): assumes **BlackHole** (macOS virtual device).
- **Menu bar mode**: `rumps` + macOS APIs (mac-only; should stay optional).
- **Text injection**: `TextTyper` assumes **Cmd+V** semantics; Linux should be **Ctrl+V** and may differ on Wayland.
- **Global hotkey**: `pynput` works reliably on **X11**, but **Wayland** support is limited/spotty (by design).

To port to Linux cleanly, we should introduce a small **platform abstraction layer** and then implement Linux backends for the above.

---

### Goals / Non-goals

**Goals**
- Run `holdspeak` on Linux with a solid baseline:
  - mic recording + transcription
  - TUI (quake-style ultrawide) fully functional
  - saved meetings and playback of stored samples
- Provide a path to “full meeting mode” on Linux:
  - system audio capture (loopback/monitor)
  - diarization and speaker history
  - web dashboard

**Non-goals (initially)**
- Linux tray / menu-bar replacement for `rumps` (nice-to-have later).
- Perfect global hotkey on Wayland for every compositor (may require compositor-specific APIs).

---

### Target Linux environments (decisions needed)

These choices affect feasibility and time:

1) **Audio stack**: PipeWire (modern default) vs PulseAudio vs ALSA-only  
   - Recommended target: **PipeWire + PulseAudio compatibility** (most distros).

2) **Display server**: X11 vs Wayland  
   - Recommended target: support **X11 fully**, provide **degraded behavior on Wayland**:
     - allow “in-app” hold-to-speak (while TUI focused)
     - optional external helpers for global hotkey and typing (e.g., `wtype`)

3) **Transcription backend**: CPU-only vs CUDA  
   - Recommended: **CPU baseline** (works everywhere), optionally **CUDA acceleration**.

---

### Platform abstraction layer (proposed)

Create a minimal “platform services” module, so OS-specific logic is concentrated and testable.

Suggested interfaces:

1) `TranscriptionBackend`
- `load(model: str, language: str | None) -> None`
- `transcribe(audio_f32_16khz: np.ndarray) -> str`
- Backends:
  - `mlx_whisper` (macOS/arm64)
  - `faster_whisper` (Linux CPU/CUDA)
  - (optional) `whispercpp` (Linux CPU) if we want no Torch/CTranslate2

2) `AudioLoopbackProvider` (system audio)
- `is_available() -> bool`
- `get_default_loopback_device() -> int | str | None`
- macOS backend: BlackHole (existing logic)
- Linux backend: PipeWire/PulseAudio “monitor of default sink” (see below)

3) `GlobalHotkeyProvider`
- `start(on_press, on_release, key: str) -> None`
- `stop() -> None`
- Linux X11: `pynput` works (existing)
- Linux Wayland: fallback to “focused TUI only” or optional helper (see below)

4) `TextInjectionProvider`
- `paste(text: str) -> None`
- macOS: clipboard + Cmd+V (existing)
- Linux X11: clipboard + Ctrl+V (pynput)
- Linux Wayland: clipboard set + instruct user to paste manually, or optional `wtype`

5) `AudioPlaybackProvider`
- Already mostly present via `afplay`/`ffplay`/`mpv`; on Linux we can also try `pw-play`/`paplay`/`aplay`.

We can implement this as `holdspeak/platform/` with:
- `detect.py` (capabilities + environment detection)
- `macos.py`, `linux.py` (service implementations)
- `__init__.py` exposing a single `get_services()` entrypoint.

---

### Linux backend research notes (how to do each feature)

#### 1) Transcription (replace MLX on Linux)

**Recommended backend: `faster-whisper`**
- Pros: good accuracy, fast CPU int8, optional CUDA, widely used.
- Cons: heavier dependency chain (CTranslate2 + potentially CUDA libs).

Alternative: `openai-whisper` (Torch)
- Pros: common, flexible.
- Cons: heavier, slower on CPU.

Alternative: `whisper.cpp` bindings
- Pros: single-binary vibe, easy packaging if we vendor.
- Cons: quality/feature variance depending on build flags; Python bindings differ.

Implementation approach:
- Keep the app-facing API the same (`Transcriber.transcribe(np.ndarray) -> str`).
- Add a backend selector:
  - On macOS arm64: default to MLX
  - On Linux: default to faster-whisper
  - Provide config knob: `transcription.backend = auto|mlx|faster_whisper|...`

#### 2) System audio capture (“remote participants”)

On Linux, system audio capture typically means “record what’s playing” using:
- **PulseAudio**: monitor source for the default sink  
  - discover via `pactl info` + `pactl list short sources`
  - monitor sources are usually named like `alsa_output...monitor`
- **PipeWire** (via PulseAudio compatibility layer): same `pactl` approach usually works.

Implementation approach:
- Add `find_linux_monitor_source()` which returns a *name* and/or maps it to a `sounddevice` device.
- We already support passing a device name; we can extend matching to handle monitor source names.
- Provide a `holdspeak meeting --setup` flow that on Linux:
  - detects `pactl` presence
  - prints explicit instructions and the detected default monitor source
  - suggests installing `pavucontrol` to choose monitor if detection fails

#### 3) Global hotkey

Reality check:
- On **X11**, `pynput` global hooks are generally fine.
- On **Wayland**, global keyboard hooks are intentionally restricted and may not work.

Implementation approach:
- Detect Wayland via `WAYLAND_DISPLAY` (and/or `XDG_SESSION_TYPE=wayland`).
- If Wayland:
  - show a clear warning in Diagnostics/Help
  - fallback to in-app bindings (record while HoldSpeak has focus)
  - optionally support user-installed helpers:
    - compositor-specific global shortcuts calling `holdspeak --toggle-record` (future CLI)
    - `ydotool`/`wtype` depending on security posture (often requires elevated privileges)

#### 4) Text injection (typing into the active app)

On Linux X11:
- Clipboard set: `pyperclip` works if `xclip` or `xsel` installed.
- Paste: simulate `Ctrl+V` via `pynput`.

On Wayland:
- Clipboard: may work depending on provider; often needs `wl-clipboard` (`wl-copy`/`wl-paste`).
- Paste simulation: use `wtype` (external), or require manual paste.

Implementation approach:
- Make paste modifier key platform-dependent (`Cmd` vs `Ctrl`).
- Add a Linux “clipboard provider” preference:
  - try `pyperclip`
  - fallback to `wl-copy`/`wl-paste` if present (Wayland)
  - fallback to “copy only + notify user to paste”

#### 5) Menu bar / tray

Current `rumps` macOS menubar mode should remain mac-only.
Linux alternatives:
- AppIndicator / StatusNotifierItem (varies by DE)
- likely a separate “phase 2” project

---

### Packaging changes required (important)

Today, Linux installs will fail because `mlx-whisper` is in `project.dependencies`.

We should:
- Move `mlx-whisper` behind a platform marker or extra:
  - Example: `mlx-whisper; platform_system == "Darwin" and platform_machine == "arm64"`
- Add a Linux transcription extra:
  - `holdspeak[linux] = ["faster-whisper>=X", ...]`
- Consider making diarization optional:
  - `holdspeak[diarization] = ["resemblyzer>=0.1.3; python_version < \"3.12\""]`

Resulting UX:
- macOS: `uv pip install -e '.[mac,meeting]'` (or keep defaults if marker is used)
- Linux: `uv pip install -e '.[linux,meeting]'`

---

### Testing / CI plan

1) Add CI jobs for Linux (Ubuntu):
- `pytest -q` with MLX/Metal tests skipped automatically
- run unit + integration tests that don’t require real audio devices

2) Add explicit markers:
- anything that requires macOS-only components (`mlx`, `rumps`, BlackHole) should be marked `requires_macos`.

3) Add a Linux “smoke” test:
- instantiate transcriber backend (mock model if needed)
- enumerate audio devices (no capture)
- run screenshot harness to verify TUI renders.

---

### Proposed implementation roadmap (phased)

**Phase A — “Runs on Linux” baseline**
1) Introduce platform services module + backend selection.
2) Add `faster-whisper` backend and make MLX optional.
3) Make `TextTyper` modifier key platform-aware (Cmd vs Ctrl).
4) Gate menubar mode behind platform check.
5) Update docs with Linux install + known limitations.

**Phase B — Meeting mode parity**
1) Linux loopback detection (monitor sources) + setup UX.
2) Improve error messaging when loopback isn’t available.
3) Validate diarization dependencies on Linux and document.

**Phase C — Wayland quality**
1) In-app “hold to record” (focused only) as first-class path.
2) Optional integrations (`wtype`, `wl-clipboard`) with clear setup.
3) (Optional) CLI “record start/stop” command for compositor shortcuts.

---

### Questions to answer before coding

1) Which distros are we targeting first? (Ubuntu/Fedora/Arch?)
2) Must we support Wayland global hotkey, or is X11-first acceptable?
3) Is CPU-only transcription acceptable initially, or do we need CUDA from day one?
4) For system audio: should we require users to configure a monitor source, or should we ship an ffmpeg-based capture fallback?
