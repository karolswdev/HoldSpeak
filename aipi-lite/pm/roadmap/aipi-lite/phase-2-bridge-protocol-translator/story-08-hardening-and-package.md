# AIPI-2-08 - Hardening, Package Split, Test Infrastructure

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01..06 (the spine being in place)
- **Unblocks:** —
- **Owner:** karol

## Problem

Post-AIPI-2-06 the bridge had a working spine but a long list of
small-but-real correctness, observability, and infrastructure gaps
surfaced during a thorough review. Rather than amend each existing
story, this is a portmanteau hardening pass that closes them
together: bug fixes, test coverage on previously-untested code paths,
a structural split of the 1500-LOC `bridge.py` into a focused
package, deeper `--check`, and lint + CI scaffolding so future
contributors can't quietly regress what shipped.

## Scope

### In — Bug fixes (correctness)

- **UDP source-IP allowlist.** `_udp_listener_session` now accepts
  datagrams only from IPs `_refresh_allowed_ips` resolved from
  `aipi_host`. Closes a real attack: anyone on the LAN could push
  PCM to UDP 50000 and have it forwarded as the user's voice
  ("follow me out of the home LAN" hotspot scenarios make this
  non-theoretical).
- **UDP listener wrapped in `reconnect_with_backoff`.** Single
  transient `OSError` no longer permanently silences audio.
- **`SO_REUSEADDR` on the UDP listener** — clean rebind through
  TIME_WAIT after a crash/restart.
- **Loud bind errors** with structured remediation hints
  (EADDRINUSE → `ss -ulnp` cue + UDP_AUDIO_PORT advice; EACCES →
  pick a port ≥ 1024).
- **`subscribe_voice_assistant` failure now fatal.** Was silent
  warning + proceed; bridge looked healthy but no audio ever
  flowed. Promotes to ERROR + disconnects so `ReconnectLogic`
  reschedules.
- **`HoldSpeakLeg.session()` `gather` → `wait(FIRST_COMPLETED)`.**
  Plain gather hung on server-close until the next 15 s heartbeat
  fired. Now tears down promptly.
- **`ConnectionClosedOK` vs `ConnectionClosedError` split.** Clean
  close resets backoff; abrupt close engages exponential. Was
  treating every close as clean → flapping HoldSpeak got tight
  retry loops.
- **Empty `HOLDSPEAK_PSK` rejected at config load time.**
  `SecretStr("")` is truthy at the Pydantic-required level; an
  empty PSK silently passed config validation and only failed
  downstream at handshake.
- **`update_screen` / `update_link` service handles cached on
  connect** rather than re-fetched per LCD paint (one
  `list_entities_services` roundtrip, not N).
- **`--check` deepened**: also binds + releases the UDP audio port
  (catches port conflicts), lists firmware services + warns when
  `update_screen`/`update_link` are missing (catches outdated
  firmware), validates that HoldSpeak's `hello-ack` echoes back
  the configured `device_id` (catches a bridge pointing at the
  wrong HoldSpeak instance).
- **Fire-and-forget tasks held in `_pending_tasks` set + auto-removed
  on done.** CPython's `asyncio.create_task` returns a
  weak-ref-collectable Task; without a strong ref GC can eat it
  before run.
- **`websockets.ConnectionClosed.code/reason` deprecation cleared**
  via a `_close_code_reason(exc)` helper that reads `exc.rcvd` /
  `exc.sent`.
- **`_handle_va_audio` (API audio path) deleted.** Documented as
  "rare cases" but per memory + hands-on testing it doesn't fire
  for stock ESPHome firmware. Dead code with pretensions.

### In — Structural

- **`bridge.py` (1500 LOC) split into a `bridge/` package** with
  one role per module:
  - `bridge/settings.py` — `Settings` + `load_settings`
  - `bridge/logging_setup.py` — `configure_logging`
  - `bridge/audio.py` — `synth_sine_pcm`, `read_wav_pcm`, queue
    sizes, sample-rate constants
  - `bridge/lcd.py` — link/activity constants + symbol picker +
    formatter
  - `bridge/reconnect.py` — `_backoff_seconds`,
    `reconnect_with_backoff`, `_close_code_reason`
  - `bridge/device.py` — `DeviceLeg`
  - `bridge/holdspeak.py` — `HoldSpeakLeg`
  - `bridge/cli.py` — `_run`, `_check`, `_send_test_audio`,
    `_audio_loopback`, `main`
  - `bridge/__init__.py` — re-exports preserving `from bridge import X`
    for callers + tests
  - `bridge/__main__.py` — entrypoint for `python -m bridge`
- **Systemd unit shifts to `python -m bridge`** + `%h` paths (was
  `bridge.py` + hardcoded `/home/karol`). Rootless install needs
  no editing if the checkout is at `~/AIPI-Lite-Voice-Bridge`.
- **`scripts/aipi-bridge.service` drops `ExecStartPre=--check`.**
  Bridge's own reconnect loop handles transient HoldSpeak
  unavailability fine; pre-check made startup brittle on reboots
  where systemd-resolved or HoldSpeak isn't up yet.

### In — Tests, lint, CI

- **Test suite grows 35 → 98** across:
  - `tests/test_holdspeak_leg.py` — fake `websockets.serve` server
    fixture exercising handshake, audio + control forwarding,
    server-pushed status/error frames, clean + abrupt close, link
    transitions.
  - `tests/test_device_leg.py` — UDP allowlist (accept/drop/empty),
    bind-failure raise, resolver hiccup preserves prior allowlist.
  - `tests/test_device_methods.py` — mock-APIClient coverage of
    `update_screen`, `update_link`, `_cache_lcd_services`,
    `_handle_va_start`/`_stop`, `_enqueue_control` overflow,
    `_on_disconnect` cache invalidation.
  - `tests/test_dispatch.py` — direct `_dispatch` unit tests:
    sticky, flash, revert, mid-flash cancellation, error variants,
    malformed payloads, unknown types.
  - `tests/test_lcd_helpers.py` — symbol picker + formatter
    (parametrised across the canonical state strings).
  - `tests/test_settings.py` — empty PSK rejection, log-level
    normalisation, label fallback.
  - `tests/test_protocol_sync.py` — opt-in cross-repo schema
    drift test against `~/dev/HoldSpeak/holdspeak/device_audio.py`.
    Skips cleanly when the sibling repo isn't checked out.
- **`ruff` lint** with a conservative starter rule set
  (`E F I B C4 UP ISC`); 39 findings auto-fixed at adoption.
  Pinned to 0.15.12 in `requirements-dev.txt`.
- **`coverage` measurement** via `coverage.py`: 62 % overall,
  100 % on `holdspeak_proto`, 59 % on `bridge.*`. Remaining gap
  is the CLI entrypoints (`_run`, `_check`, `_send_test_audio`,
  `_audio_loopback`) which require either real hardware or
  expensive mocking; deliberately not chased to 100 %.
- **`requirements-dev.txt`** splits test deps from runtime
  (`pytest`, `pytest-asyncio`, `ruff`).
- **GitHub Actions CI** at `.github/workflows/ci.yml`:
  `ruff check` + `pytest -v` on push + PR; Python 3.10 / 3.11 /
  3.12 matrix; concurrency cancellation so stale runs get killed.

### In — Cleanup

- **`docs/DEVICE_AUDIO_OUTPUT.md`** captures the device-side
  speaker stack that came out of `aipi.yaml`: octal PSRAM
  rationale, EMI dance via GPIO9 toggle, ES8311 deep-mute via
  raw I2C, mic-gain analog path, paste-back YAML for the
  removed services. Future "HoldSpeak speaks back" story doesn't
  rediscover the workarounds.
- **Speaker / `media_player` / `prepare_speaker` / `restore_mic`
  removed** from `aipi.yaml` (the bridge architecture never plays
  back). `speaker_enable` GPIO held `restore_mode: ALWAYS_OFF` +
  `internal: true` so the amp can't accidentally power up and
  bleed EMI into the analog mic.
- **Probe `pm/probes/aipi-1-05-left-button.yaml` deleted** —
  served its purpose 2026-05-07; PMO's "delete probes after they
  resolve" rule applies.
- **`debug_mic.wav`** local artefact removed.
- **`requirements.txt`** pinned to `==` (was `>=`/bare). Lock
  surface for repro.
- **README + HOLDSPEAK_BRIDGE.md** updated for `python -m bridge`,
  the package layout, and the new LCD pushback behaviour.

### Out

- A coverage threshold gate in CI. Legitimate gaps (CLI
  entrypoints) would force either a too-low bar or hand-mocking
  with poor return on maintenance cost. Re-add if the legs ever
  decompose further.
- mypy. Ruff catches the cheap things; static type-checking is
  worth its own story once the package layout settles.
- pyproject.toml + a publishable distribution. Bridge runs from
  source today; packaging is its own concern when usage warrants.
- Lock files (`uv.lock` / `pip-compile`). Pinned `requirements.txt`
  is enough for now.

## Acceptance Criteria

- [x] All bug fixes above land + pass tests; no regressions in
  the 35-test pre-existing suite.
- [x] `bridge.py` is gone; `bridge/` package replaces it with the
  module layout above. `python -m bridge --help` works;
  `from bridge import X` still resolves (re-exports).
- [x] `tests/` runs 98 cases under `pytest -q`; `ruff check .`
  reports clean.
- [x] CI workflow in `.github/workflows/ci.yml` runs lint + tests
  on push/PR (Python 3.10/3.11/3.12 matrix). **Workflow file in
  place; first GitHub Actions run pending push.**
- [x] `--check` mode now also verifies UDP port bindable +
  firmware service availability + ack `device_id` echo.
- [x] `docs/DEVICE_AUDIO_OUTPUT.md` documents the removed
  speaker stack including paste-back YAML.
- [x] Systemd unit + runbook updated for `python -m bridge`.
- [ ] Live-hardware verification of the new `--check` paths
  alongside AIPI-2-01..05 verification.

## Test Plan

- **Unit + integration:** existing `pytest -q` suite (98 cases).
- **Lint:** `.venv/bin/ruff check .` exits 0.
- **CLI smoke:**
  - `python -m bridge --help` — argparse surface.
  - `python -m bridge --check` against the live device + an
    absent HoldSpeak — should now also surface UDP-bind /
    firmware-service-availability.
  - `python -m bridge --send-test-audio path.wav` — unchanged
    behaviour, exercised via the package entrypoint.

## Notes

- **Story 08 isn't a feature story.** It's the kind of pass
  that's hard to scope but pays back the next time someone reads
  the codebase or onboards. Tracking it as a discrete story
  keeps the "what shipped" record honest rather than burying
  the work in commit-message footnotes.
- **The package split's awkward bit:** `test_reconnect.py`
  monkey-patches `_backoff_seconds`. Module split means the
  patch needs to target `bridge.reconnect._backoff_seconds`
  (where the function actually lives), not the re-export on
  `bridge`. Updated; documented in the test comment so a future
  refactor doesn't repeat the trap.
- **What got deferred from this pass:**
  - Module-level docstrings still reference "story 01" /
    "story 02" markers; they're historically accurate but rot
    over time. Cleanup is cheap, just not in scope here.
  - The CLI entrypoints (`_run`, `_check`, etc.) remain integration
    code with no automated coverage. A "fake everything" test
    layer is doable but expensive.
  - `holdspeak_proto.py` could move into `bridge.protocol` for
    consistency. Held off because it's already a single tight
    file and external callers (the protocol-sync test) import it
    by name.
- **CI matrix Python versions** are 3.10 (project minimum per
  HOLDSPEAK_BRIDGE.md §2) → 3.12 (dev environment). 3.13 is
  intentionally not in the matrix yet — wait for it to be the
  default before committing CI cycles.
