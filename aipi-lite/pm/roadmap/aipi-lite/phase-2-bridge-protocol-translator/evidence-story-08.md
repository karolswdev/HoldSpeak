# Evidence — AIPI-2-08 — Hardening, Package Split, Test Infrastructure

- **Shipped:** 2026-05-10 (working tree)
- **Commit:** pending close-out commit on branch `mine` (working-tree base `9ff88a6`).
- **Owner:** karol

## Files touched

### Structural — `bridge.py` (1500 LOC) → `bridge/` package

```
bridge/
  __init__.py        93 LOC   re-exports for `from bridge import X`
  __main__.py        10 LOC   `python -m bridge` entry point
  settings.py        93 LOC   Settings + load_settings (incl. empty-PSK rejection)
  logging_setup.py   29 LOC   configure_logging
  audio.py           87 LOC   synth_sine_pcm, read_wav_pcm, queue/SR constants
  lcd.py             63 LOC   link/activity constants + symbol picker + formatter
  reconnect.py       98 LOC   _backoff_seconds, reconnect_with_backoff, _close_code_reason
  device.py         436 LOC   DeviceLeg
  holdspeak.py      427 LOC   HoldSpeakLeg
  cli.py            466 LOC   _run, _check, _send_test_audio, _audio_loopback, main
                  ——————
                  1802 LOC total (was 1500 in monolith bridge.py — net +20% from re-exports + module headers + per-file imports)
```

### Bug fixes (correctness)

- `bridge/device.py`: UDP source-IP allowlist (`_refresh_allowed_ips` resolves from `aipi_host`); `_udp_listener` wrapped in `reconnect_with_backoff`; `SO_REUSEADDR`; loud `EADDRINUSE`/`EACCES` errors with structured remediation hints; `subscribe_voice_assistant` failure now fatal; `_handle_va_audio` (API-audio dead-code path) deleted.
- `bridge/holdspeak.py`: `gather` → `wait(FIRST_COMPLETED)` so server-close tears down promptly (was hanging on next 15s heartbeat); `ConnectionClosedOK`/`ConnectionClosedError` split (clean reset / abrupt backoff); `update_screen`/`update_link` service handles cached on connect; fire-and-forget tasks held in `_pending_tasks` set + auto-removed on done; `websockets.ConnectionClosed.code/reason` deprecation cleared via `_close_code_reason(exc)` reading `exc.rcvd`/`exc.sent`.
- `bridge/settings.py`: empty `HOLDSPEAK_PSK` rejected at config load (was silently passing Pydantic-required because `SecretStr("")` is truthy at that level).
- `bridge/cli.py`: `--check` deepened — also binds + releases UDP audio port; lists firmware services + warns when `update_screen`/`update_link` are missing; validates `hello-ack` echoes the configured `device_id`.

### Tests, lint, CI

- 35 → 98 tests across 8 test files (`test_audio`, `test_models`, `test_reconnect`, `test_holdspeak_leg`, `test_device_leg`, `test_device_methods`, `test_dispatch`, `test_lcd_helpers`, `test_settings`, `test_protocol_sync`).
- `ruff` 0.15.12 with rule set `E F I B C4 UP ISC`; 39 findings auto-fixed at adoption.
- `coverage.py`: 62% overall, 100% on `holdspeak_proto`, 59% on `bridge.*`. Gap is CLI entrypoints (`_run`/`_check`/`_send_test_audio`/`_audio_loopback`) — deliberately not chased to 100%.
- `requirements-dev.txt` — new. Splits test deps (`pytest`, `pytest-asyncio`, `ruff`) from runtime.
- `requirements.txt` — re-pinned to `==`.
- `.github/workflows/ci.yml` — new. `ruff check` + `pytest -v` on push + PR; Python 3.10/3.11/3.12 matrix; concurrency cancellation.

### Cleanup

- `docs/DEVICE_AUDIO_OUTPUT.md` — new. Recovery doc for the removed device speaker stack: octal PSRAM rationale, EMI dance via GPIO9 toggle, ES8311 deep-mute via raw I2C, mic-gain analog path, paste-back YAML.
- `aipi.yaml` — speaker / `media_player` / `prepare_speaker` / `restore_mic` removed; `speaker_enable` GPIO held `restore_mode: ALWAYS_OFF` + `internal: true`.
- `pm/probes/aipi-1-05-left-button.yaml` — deleted (probe served its purpose 2026-05-07).
- `debug_mic.wav` — deleted.
- `scripts/aipi-bridge.service` — switched to `python -m bridge` + `%h` paths; dropped `ExecStartPre=--check` (made startup brittle on reboots where systemd-resolved or HoldSpeak isn't up yet).

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
98 passed in 2.80s

$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/python -m bridge --help
usage: __main__.py [-h] [--check | --send-test-audio WAV | --audio-loopback]
AIPI-Lite ↔ HoldSpeak bridge

options:
  -h, --help            show this help message and exit
  --check               Connect to both endpoints, run handshake, exit 0 on
                        success.
  --send-test-audio WAV
                        Stream a 16 kHz mono int16 WAV to HoldSpeak as a one-
                        shot test, then exit. Bypasses the device leg.
  --audio-loopback      Continuously stream a 440 Hz sine wave to HoldSpeak.
                        Bypasses the device leg. Exit on Ctrl-C.
```

```
$ wc -l bridge/*.py
   87 bridge/audio.py
  466 bridge/cli.py
  436 bridge/device.py
  427 bridge/holdspeak.py
   93 bridge/__init__.py
   63 bridge/lcd.py
   29 bridge/logging_setup.py
   10 bridge/__main__.py
   98 bridge/reconnect.py
   93 bridge/settings.py
 1802 total
```

## Acceptance criteria — re-checked

- [x] All bug fixes land + pass tests; no regressions in the 35-test pre-existing suite — 98/98 passing (35 originals + 63 new).
- [x] `bridge.py` gone; `bridge/` package replaces it; `python -m bridge --help` works; `from bridge import X` re-exports preserved — verified.
- [x] `pytest -q` runs 98 cases; `ruff check .` clean — verified above.
- [~] CI workflow runs lint + tests on push/PR (3.10/3.11/3.12 matrix) — `.github/workflows/ci.yml` present; **first GitHub Actions run pending the close-out push**.
- [x] `--check` deepened: UDP port bind, firmware service availability, ack `device_id` echo — code path inspected; unit-tested partially in `tests/test_settings.py` + `tests/test_holdspeak_leg.py`. Live-`--check` trace deferred to phase final-summary's open list.
- [x] `docs/DEVICE_AUDIO_OUTPUT.md` documents removed speaker stack + paste-back YAML — file present.
- [x] Systemd unit + runbook updated for `python -m bridge` — verified.
- [~] **Live-hardware verification of new `--check` paths deferred** — hardware not co-located 2026-05-10.

## Deviations from plan

- Module-level docstrings still reference "story 01" / "story 02" markers (historically accurate but rot over time). Cleanup explicitly out of scope per the story's "What got deferred" notes.
- CLI entrypoints remain integration code with no automated coverage — explicit decision, recorded in story notes.
- `holdspeak_proto.py` not moved into `bridge.protocol` — held off because external callers (`tests/test_protocol_sync.py`) import it by name.

## Follow-ups

- First CI run (lands when the close-out commit gets pushed).
- mypy adoption — explicit follow-up story candidate once package layout settles.
- Coverage threshold gate — deferred until the legs decompose further.
- pyproject.toml + a publishable distribution — defer until usage warrants.
- Live `--check` against the deepened paths once hardware is back in reach.
