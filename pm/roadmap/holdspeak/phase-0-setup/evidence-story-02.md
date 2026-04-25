# Evidence — HS-0-02 (Fix vanilla `holdspeak` install)

**Captured:** 2026-04-25.
**Reference machine:** Darwin 25.2.0 (arm64), Python 3.13.11, `.venv` rebuilt via `uv sync --python 3.13`.

## pyproject diff (relevant excerpts)

Core deps now contain:

```toml
dependencies = [
    "mlx-whisper>=0.4.0; sys_platform == 'darwin' and platform_machine == 'arm64'",
    "sounddevice>=0.4.6",
    "numpy>=1.24.0",
    "pynput>=1.7.6",
    "pyperclip>=1.8.2",
    "textual>=0.50.0",
    # Web runtime is the default `holdspeak` command, so its deps live in core.
    # `uvicorn[standard]` pulls in websockets/uvloop/httptools/watchfiles.
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
]
```

`[meeting]` extra now contains only LLM/intel deps (no `fastapi`, no `uvicorn`):

```toml
meeting = [
    "llama-cpp-python>=0.2.0",
    "openai>=1.0.0",
    "resemblyzer>=0.1.3",
]
```

Version bumped to `0.2.1`.

## Doctor check passes (new row included)

```
$ holdspeak doctor
HoldSpeak Doctor
===============
[PASS] Runtime: Darwin 25.2.0 (arm64), Python 3.13.11
[PASS] Config: Loaded /Users/karol/.config/holdspeak/config.json
[PASS] Microphone: Default input: MacBook Pro Microphone (index 1)
[PASS] Transcription backend: `auto` resolves to `mlx`
[PASS] Web runtime: fastapi, uvicorn, and websockets are importable
[WARN] Meeting intelligence runtime: llama-cpp-python is not available
[PASS] Cloud intel preflight: Skipped (provider mode `local`)
[PASS] Global hotkey: Hotkey listener initialized for `alt_r`
[PASS] Text injection: Keyboard injection backend initialized
[PASS] Clipboard backend: Platform default clipboard backend
[PASS] ffmpeg: Detected in PATH
[PASS] pactl: Not required on this platform
[WARN] System audio capture: System-audio capture source not configured

Summary: 11 passed, 2 warnings, 0 failed
```

The new row is `[PASS] Web runtime: fastapi, uvicorn, and websockets are importable`. Two warnings remain (`Meeting intelligence runtime` and `System audio capture`) — both are pre-existing optional-feature warnings, not regressions caused by HS-0-02.

## Doctor unit tests pass

```
$ .venv/bin/python -m pytest tests/ -k doctor -q
.........                                                                [100%]
9 passed, 781 deselected in 0.75s
```

## Smoke run — no WebSocket warning spam

```
$ holdspeak &  # then sleep 3, then kill
$ cat /tmp/hs_smoke.log
This process is not trusted! Input event monitoring will not be possible until it is added to accessibility clients.
```

The lone remaining line is the macOS Accessibility prompt (a real OS prerequisite, not a packaging bug). Pre-fix output additionally contained ≥5 lines of `Unsupported upgrade request / No supported WebSocket library detected`. That spam is gone.
