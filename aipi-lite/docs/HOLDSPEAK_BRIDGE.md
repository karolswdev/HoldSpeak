# AIPI-Lite ↔ HoldSpeak Bridge Runbook

This is the canonical guide for running the AIPI-Lite as a HoldSpeak
satellite — voice typing into whatever app is focused on the HoldSpeak
host, and meeting recording with per-device-labeled transcripts. The
bridge process (the `bridge/` package, run via `python -m bridge`) is a thin async forwarder between the
device's ESPHome API and HoldSpeak's `/api/devices/audio` WebSocket.

---

## 1. Architecture overview

```
┌──────────────┐   ESPHome API    ┌──────────┐   /api/devices/audio   ┌────────────┐
│  AIPI-Lite   │  (aioesphomeapi) │  bridge  │   (websockets, JSON +  │  HoldSpeak │
│  (ESP32-S3)  │ ◄──────────────► │   .py    │ ◄────────────────────► │   web      │
│ mic / button │                  │  package │   16 kHz mono int16    │  runtime   │
└──────────────┘                  └──────────┘                        └────────────┘
```

The bridge is **stateless**: HoldSpeak owns sessions, meetings, and
the typing/transcription pipeline. The bridge only translates events:

- Right-button press → WS `start` control frame.
- Mic frames → WS binary frames.
- Right-button release → WS `stop` control frame + ESPHome
  `VOICE_ASSISTANT_RUN_END` event so the firmware's `on_end` re-arms
  in continuous mode.
- Inbound `error: session_busy` → "Busy" on the LCD via the
  firmware's `update_screen` API service.

Wire contract: see HoldSpeak's
`~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`. Don't duplicate it
here — that doc is canonical.

---

## 2. Prerequisites

- **HoldSpeak** running on the host where you want voice typing
  to land. See `~/dev/HoldSpeak/README.md` for install. Minimum:
  the `holdspeak` web runtime up (`holdspeak web`).
- **AIPI-Lite** flashed with the production firmware. See
  [`PROVISIONING.md`](./PROVISIONING.md) for first-time flash and
  network provisioning.
- **Python 3.10+** with `pip` or `uv` for the bridge venv.
- USB-C cable to the AIPI-Lite *only for reflashing or recovery*;
  the bridge talks to the device over the network.

---

## 3. First-time setup

1. **Clone + venv:**

   ```bash
   git clone https://github.com/karolswdev/AIPI-Lite-Voice-Bridge.git
   cd AIPI-Lite-Voice-Bridge
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. **Get HoldSpeak's host + port + PSK:**

   ```bash
   # On the HoldSpeak host:
   holdspeak device-psk show     # prints the configured PSK
   ```

   The port is in HoldSpeak's startup log
   (`Uvicorn running on http://127.0.0.1:<port>`). For phase 14
   the runtime binds to `127.0.0.1` only — run the bridge on the
   same machine.

3. **Configure the bridge:**

   ```bash
   cp bridge.env.example bridge.env
   # edit bridge.env: fill HOLDSPEAK_PORT and HOLDSPEAK_PSK
   ```

   Required fields: `HOLDSPEAK_PORT`, `HOLDSPEAK_PSK`.
   Sensible defaults exist for the rest. See `bridge.env.example`
   for the full schema and inline comments.

4. **Smoke-test both endpoints:**

   ```bash
   .venv/bin/python3 -m bridge --check
   ```

   - **Exit 0**: device + HoldSpeak handshakes both succeeded.
   - **Exit 1**: stderr names which endpoint failed and decodes
     the failure (e.g. `4003 PSK mismatch — check HOLDSPEAK_PSK`).

5. **Run for real:**

   ```bash
   .venv/bin/python3 -m bridge
   ```

   The bridge logs JSON events via `structlog` to stdout. Keep
   it running in a terminal, a `tmux` window, or daemonise per
   §6.

---

## 4. Voice typing

With the bridge running:

1. **Focus a target app** on the HoldSpeak host (text editor,
   browser address bar, chat box — whatever you'd type into).
2. **Press and hold the right button** on the AIPI-Lite. The
   firmware's `on_press` updates the LCD to `Listening...`.
3. **Speak** while holding the button.
4. **Release the button.** LCD flips to `Thinking...`. Audio
   captured during the press is transcribed on the HoldSpeak
   side and typed (clipboard + Cmd/Ctrl-V) into the focused app
   on the host.

Latency: ~1.5–2 s end-to-end on the happy path
(release → text typed). Whisper-bound; the bridge itself adds
nothing measurable.

### Continuous mode (always-listening)

Triple-tap the right button to toggle. The LCD top label flips
between `Hold-to-talk` and `Always listening`. In continuous
mode, the firmware re-arms `voice_assistant.start` after each
session, which from HoldSpeak's POV is a stream of back-to-back
voice-typing turns. Triple-tap again to disable.

This is a **device-side affordance** — HoldSpeak doesn't know
about it. Each turn is its own session-and-typed-text round.

### "Busy" on the LCD

If the host hotkey or another device is already in a
voice-typing session, pressing the right button shows `Busy`
on the LCD. The firmware's `on_release` overrides it to
`Thinking...` on release; the next press cycle works normally.

---

## 5. Recording a meeting with the device

HoldSpeak's Meeting Mode is the same audio channel the bridge is
already feeding — to attach the device to a meeting, you just
include its `device_id` in the meeting-start payload.

### Steps

1. **Make sure the bridge is running** and the device is
   connected (LCD shows the normal mode label, not `Setup-AP`).
2. **Start the meeting** from HoldSpeak. Either:
   - Web UI: open the HoldSpeak dashboard, click "Start Meeting,"
     pick the device from the attached-devices list, hit start.
   - Or curl:

     ```bash
     curl -X POST http://127.0.0.1:<port>/api/meeting/start \
          -H 'Content-Type: application/json' \
          -d '{"devices":["aipi-1"]}'
     ```

3. **Speak naturally.** Audio streams continuously into HoldSpeak
   regardless of button state — meetings own the recorder. Per
   HS-14-06, button presses during an active meeting are
   server-side no-ops (HoldSpeak ignores attached-device
   `start`/`stop` frames while the meeting is recording).
4. **End the meeting** from the HoldSpeak dashboard. HoldSpeak
   transcribes per-segment and runs its meeting-intelligence
   pipeline (topics, action items, summary) either inline or via
   the deferred queue — see `~/dev/HoldSpeak/holdspeak/intel.py`
   for which path your install uses.
5. **The transcript** shows segments tagged with the device's
   label (`DEVICE_LABEL` from `bridge.env`, defaults to
   `DEVICE_ID`). Multi-device meetings tag each segment with the
   right speaker.

### What the LCD shows during a meeting

The 128×128 LCD is split into three zones, each with one owner:

| Zone | Owner | What you see |
|---|---|---|
| Top-left (`mode_label`) | Firmware | `HOLD` / `CONT` / `AP` / `RST` — the physical mode |
| Top-right (`link_label`) | Bridge | `[--]` / `[..]` / `[OK]` — WS connection state |
| Bottom (`ai_response_label`) | Bridge | HoldSpeak status text + an ASCII state symbol |

**Link indicator** is bridge-driven on every WS state transition:

- `[--]` — bridge is up but the WS is down (initial state, or in backoff between reconnect attempts).
- `[..]` — connecting / handshaking right now.
- `[OK]` — connected and handshake complete.

If you see `[--]` while the bridge process is running, check
`journalctl` — most likely HoldSpeak is unreachable and the bridge
is in `reconnect_with_backoff`.

**Activity line** is the bottom label. It shows whatever HoldSpeak
sends in a `status` frame, plus a small ASCII symbol the bridge
picks from the leading word of the status text:

| HoldSpeak `status.text` | Bottom label paints | Symbol |
|---|---|---|
| `Listening...` | `Listening...  >>` | mic hot |
| `Recording 12:34` | `Recording 12:34   *` | meeting recording |
| `Transcribing...` | `Transcribing...  ==` | post-stop, awaiting text |
| `Bookmark @ 47s` | `Bookmark @ 47s  \!//` | gesture acknowledgment |
| `Saving meeting...` | `Saving meeting...  ...` | end-of-meeting work |
| (anything else) | `<text>  ─` | unknown / generic |

**Sticky vs. flash semantics.** HoldSpeak's `status.ttl_ms` field
controls how the bridge holds the paint:

- `ttl_ms = 0` → **sticky**: stays until HoldSpeak sends a different
  status. Used for stable states like `Recording 12:34`.
- `ttl_ms > 0` → **flash**: paints, then reverts to the last sticky
  after `ttl_ms` milliseconds. Used for one-off acknowledgments
  like `Bookmark @ 47s`.

Two synthetic flashes are bridge-side, not from HoldSpeak:

- `error: session_busy` from HoldSpeak → flash `Busy  [?]` for 3 s.
- Any other `error` frame → flash `Error: <reason>  /!\` for 5 s.

**Mode label** stays firmware-owned. The bridge never paints it. If
you ever want HoldSpeak to drive the top label, that's a separate
firmware-side change adding a second API service.

---

## 6. Daemonising the bridge

A starter `systemd` unit lives at `scripts/aipi-bridge.service`.
It supports both system-wide and rootless installs.

**Rootless (default; recommended):** the unit ships with `%h` paths so
no editing is needed if your checkout is at `~/AIPI-Lite-Voice-Bridge`
with a venv at `./.venv`.

```bash
mkdir -p ~/.config/systemd/user
cp scripts/aipi-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now aipi-bridge

# Logs:
journalctl --user -u aipi-bridge -f
```

**System-wide:** `%h` doesn't expand in system services, so edit
`WorkingDirectory=`, both `ExecStart` paths, and `ReadWritePaths=` to
absolute paths, set `User=` to the account that owns `bridge.env`,
flip `WantedBy=` from `default.target` back to `multi-user.target`,
then:

```bash
sudo cp scripts/aipi-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aipi-bridge

# Logs:
journalctl -u aipi-bridge -f
```

**macOS:** ship a `launchd` plist instead. Not included here;
contributions welcome. In the meantime, `tmux` + a long-lived
shell works fine.

**Docker:** also out of scope for v1. The dependency footprint
is small enough that a venv install is the recommended path.

---

## 7. PSK rotation

When you rotate HoldSpeak's PSK, the bridge needs the new value:

```bash
# On the HoldSpeak host:
holdspeak device-psk rotate
holdspeak device-psk show

# On the bridge host:
$EDITOR bridge.env       # update HOLDSPEAK_PSK
sudo systemctl restart aipi-bridge   # or systemctl --user
```

Rotation takes effect on the *next* WebSocket connection; the
existing connection (if any) stays up until something else tears
it down. To force re-auth with the new PSK immediately, restart
the bridge.

The bridge logs `disconnect.holdspeak code=4003` if it tries to
hand-shake with a stale PSK. The reconnect loop will keep
retrying — fix `bridge.env` and restart.

---

## 8. Troubleshooting

| Symptom | First thing to check |
|---|---|
| `--check` exits 1 with `holdspeak_port: Field required` | `bridge.env` not populated; copy `bridge.env.example` and fill in `HOLDSPEAK_PORT` + `HOLDSPEAK_PSK`. |
| `--check` reports `4003 PSK mismatch` | Run `holdspeak device-psk show` on the HoldSpeak host and copy the value into `HOLDSPEAK_PSK`. |
| `--check` reports `4009 duplicate label` | Another device (or a previous bridge process that didn't unregister cleanly) is using the same `DEVICE_LABEL`. Pick a unique label or wait a few seconds for the old session to time out. |
| `--check` reports `ConnectionRefusedError` on the device endpoint | The AIPI-Lite isn't reachable. Check `aipi.local` resolves (`ping aipi.local`); confirm the device is on the same network; if needed, set `ESPHOME_HOST` to the IP. |
| `--check` reports `ConnectionRefusedError` on the holdspeak endpoint | HoldSpeak isn't running or isn't bound to the configured host:port. Start `holdspeak web` and confirm the port. |
| Press button, no text typed | Check the bridge log for `control.start.sent` and `control.stop.sent`. If `start.sent` is missing, the device isn't reaching the bridge; if `stop.sent` is missing, the firmware fired start but never stop. If both are present but no text appears on the host, look at HoldSpeak's logs for transcription errors. |
| LCD top-right shows `[--]` while bridge is running | WS to HoldSpeak is down. Bridge is in `reconnect_with_backoff` — see `journalctl` for `disconnect.holdspeak.*` events. Resolves once HoldSpeak is reachable. |
| LCD stuck on `Listening... >>` | The firmware fired `voice_assistant.start` but never `stop`. Triple-tap the right button to toggle continuous mode off, or power-cycle the device. |
| Bridge logs `audio.queue.overflow` repeatedly | HoldSpeak isn't draining frames fast enough (might be paused, slow, or the WS is wedged). The bridge will recover when HoldSpeak does; an `audio.queue.overflow.recovered` log fires when drainage resumes. If overflow is persistent on a healthy HoldSpeak, file an issue. |
| Bridge logs `reconnect target=holdspeak attempt=N` repeatedly | HoldSpeak is down or unreachable. Confirm with `curl http://<host>:<port>/`. The bridge backs off exponentially (1s, 2s, 4s, 8s, 16s, 30s cap) and reconnects when HoldSpeak comes back. |
| `audio-loopback` mode runs but no transcript appears in HoldSpeak | Expected. A 440 Hz sine has no semantic content; HoldSpeak should accept it without errors and produce no transcription. The mode is for verifying the WS audio path is alive, not for testing transcription. |
| `--send-test-audio` says `expected mono WAV, got 2 channels` | The WAV must be 16 kHz mono int16 LE. Convert with `ffmpeg -i input.wav -ac 1 -ar 16000 -sample_fmt s16 output.wav`. |

### Useful debug knobs

```bash
LOG_LEVEL=DEBUG .venv/bin/python3 -m bridge
```

The bridge's logs are JSON via `structlog`. Pipe to `jq` for
human reading:

```bash
.venv/bin/python3 -m bridge 2>&1 | jq .
```

The two standalone modes are also handy:

- `python3 -m bridge --send-test-audio path/to/test.wav` — one-shot WAV
  streaming, bypasses the device leg. Verifies the HoldSpeak
  WS + transcription path in isolation.
- `python3 -m bridge --audio-loopback` — continuous 440 Hz sine,
  bypasses the device leg. Verifies the WS audio path is alive
  without engaging Whisper.

---

## 9. Remote gesture testing (AIPI-4-07)

When the device is physically out of reach (across the house, in the
basement, etc.) but you need to verify a gesture path end-to-end, the
bridge ships dev-infra `--press` subcommands that fire ESPHome
`simulate_*` services. Same code path as a real button press from the
bridge's perspective; needs LAN access to the device's API port.

```bash
# Bookmark gesture (100 ms left-button press). During an active
# meeting → adds a bookmark in HoldSpeak's transcript at the press
# timestamp + flashes "Bookmark" on the LCD. Outside a meeting →
# logs `event.suppressed reason=not_in_meeting`; no transcript change.
python -m bridge --press left-short

# Long left-button press (6 s). Bridge's classifier ignores it
# (above the 500 ms short-press threshold); useful for confirming
# the long-press path doesn't fire a bookmark.
python -m bridge --press left-long

# 3 s of audio capture via voice_assistant.start / voice_assistant.stop.
# Bridge forwards the audio to HoldSpeak, which transcribes + types
# into the focused host app — same path as a real right-button hold.
python -m bridge --press voice-typing
```

**Prerequisite:** firmware must be flashed from `aipi.yaml` ≥ AIPI-4-07
(adds the `simulate_left_press` + `simulate_voice_typing` API services
and the `left_button_sim` template binary_sensor). Run `python -m
bridge --check` to confirm — the services list in `check.device.ok`
should include both `simulate_*` entries.

`--press` opens its own ESPHome API connection (the long-running
bridge can stay up; both clients coexist). It exits 0 on success / 1
on missing-service / 1 on connection error. The CLI waits
`duration_ms / 1000 + 0.5 s` after `execute_service` before
disconnecting — the wait avoids a race where the firmware's
state-publish loses to an immediate connection close (observed live
2026-05-10 with 100 ms presses silently dropping).

---

## Source canon

- Bridge: [`bridge/`](../bridge/) (run `python -m bridge`),
  [`holdspeak_proto.py`](../holdspeak_proto.py)
- Bridge config schema: [`bridge.env.example`](../bridge.env.example)
- Firmware: [`aipi.yaml`](../aipi.yaml) — the device's ESPHome
  config (audio, LCD, button mappings, `update_screen` service)
- Provisioning: [`PROVISIONING.md`](./PROVISIONING.md)
- Roadmap: [`pm/roadmap/aipi-lite/`](../pm/roadmap/aipi-lite/) —
  full phase + story breakdowns, decisions, risks
- HoldSpeak protocol (canonical): `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`
- HoldSpeak device-side implementation:
  `~/dev/HoldSpeak/holdspeak/device_audio.py`,
  `~/dev/HoldSpeak/holdspeak/device_audio_ws.py`,
  `~/dev/HoldSpeak/holdspeak/voice_typing.py`
