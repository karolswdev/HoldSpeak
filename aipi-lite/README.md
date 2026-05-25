# AIPI-Lite Voice Bridge

> A small physical surface for [HoldSpeak](https://github.com/karolswdev/HoldSpeak):
> press a button, talk, and have the transcript typed into whatever
> app is focused on the host. The hardware is the AIPI-Lite ESP32-S3
> robot (also known as Xorigin / XiaoZhi); this repo contains its
> ESPHome firmware (`aipi.yaml`) and the host-side Python bridge
> (`bridge/`) that connects it to a HoldSpeak instance.

## Architecture

```
┌──────────────┐   ESPHome API + UDP    ┌──────────┐   /api/devices/audio   ┌────────────┐
│  AIPI-Lite   │  (aioesphomeapi /      │  bridge  │   (websockets, JSON +  │  HoldSpeak │
│  (ESP32-S3)  │   16 kHz mono int16    │   .py    │    16 kHz mono int16)  │   web      │
│ mic / button │   PCM datagrams)       │          │                        │  runtime   │
└──────────────┘                        └──────────┘                        └────────────┘
                                              │                                   │
                                       structured logs                       voice typing
                                       (stdout JSON)                         + meeting mode
```

**One-way audio flow.** The device captures mic audio over I2S,
streams it as UDP datagrams to the bridge process, and the bridge forwards
those datagrams as binary frames over a WebSocket to HoldSpeak.
HoldSpeak owns transcription (`faster-whisper`), voice typing
(clipboard + Cmd/Ctrl-V into the focused app), and meeting recording.
The bridge is **stateless** — it only translates events.

**Control mapping.**

- Right button press → WS `start` frame (claims a HoldSpeak voice-typing session).
- Mic frames → WS binary frames.
- Right button release → WS `stop` frame + `VOICE_ASSISTANT_RUN_END` to the firmware.
- Triple-tap right button → toggle continuous "always-listening" mode.
- Long-press left button → enter Wi-Fi setup AP for reprovisioning.
- HoldSpeak → device LCD push-back (e.g. `Busy`) via the firmware's `update_screen` API service.

The bridge is a small Python package split across focused modules
(`settings`, `audio`, `lcd`, `reconnect`, `device`, `holdspeak`, `cli`).
Runs as a `systemd` unit
or in a `tmux` window — no Docker, no DB, no external dependencies
beyond a HoldSpeak instance.

## Repo layout

| Path | What |
|---|---|
| `aipi.yaml` | ESPHome firmware — hardware wiring, button gestures, LCD widgets, voice_assistant + Wi-Fi/captive-portal/Improv-WiFi provisioning. |
| `bridge/` | The forwarder package (`bridge.device.DeviceLeg` + `bridge.holdspeak.HoldSpeakLeg`). Connects to the device's ESPHome API + binds a UDP audio listener; relays both onto HoldSpeak's `/api/devices/audio` WebSocket. Run with `python -m bridge`. |
| `holdspeak_proto.py` | Pydantic models mirroring HoldSpeak's wire contract (`extra="forbid"` so drift fails loudly). |
| `bridge.env.example` | All bridge config knobs with defaults + comments. Copy to `bridge.env` (gitignored). |
| `tests/` | `pytest` suite — protocol model round-trips, audio helpers, reconnect/backoff. |
| `scripts/aipi-bridge.service` | Systemd unit (rootless or system-wide). |
| `docs/HOLDSPEAK_BRIDGE.md` | **Operations runbook** — first-time setup, daemonising, PSK rotation, troubleshooting table. |
| `docs/PROVISIONING.md` | Captive-portal + Improv-WiFi flow + factory reset. |
| `docs/DEVICE_AUDIO_OUTPUT.md` | Recovery doc for the deliberately-removed device-side speaker stack (EMI dance, ES8311 mute, octal PSRAM). |
| `pm/roadmap/aipi-lite/` | Phase + story breakdowns. |

## Quick start

```bash
git clone https://github.com/karolswdev/AIPI-Lite-Voice-Bridge.git
cd AIPI-Lite-Voice-Bridge
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure: at minimum HOLDSPEAK_PORT and HOLDSPEAK_PSK.
cp bridge.env.example bridge.env
$EDITOR bridge.env

# Smoke-test both endpoints.
.venv/bin/python3 -m bridge --check

# Run for real.
.venv/bin/python3 -m bridge
```

`--check` exits 1 with a decoded reason on PSK mismatch, duplicate
device label, ESPHome unreachable, or HoldSpeak unreachable. Logs are
JSON via `structlog` to stdout — pipe to `jq` for human reading.

The bridge also has two standalone debug modes:

- `python3 -m bridge --send-test-audio path.wav` — handshake → start →
  stream a 16 kHz mono int16 WAV → stop → exit. Verifies the
  HoldSpeak audio path without a real device.
- `python3 -m bridge --audio-loopback` — continuous 440 Hz sine. Verifies
  the WS is alive without engaging Whisper.

For the full operations guide (daemonising, PSK rotation,
multi-device meetings, the troubleshooting table) see
[`docs/HOLDSPEAK_BRIDGE.md`](docs/HOLDSPEAK_BRIDGE.md).

## Project status

- **Phase 1 — Provisioning:** implementation-complete on disk;
  hardware verification + close-out is the open item. Multi-SSID +
  captive portal + BLE + serial + factory-reset gestures are all
  wired in `aipi.yaml`.
- **Phase 2 — Bridge protocol translator:** in-progress; pairs
  with HoldSpeak HS-14. The thin-forwarder rewrite is on `main`;
  hardware end-to-end smoke + close-out remaining.
- **Phase 3 — Cross-network transport:** scaffolding open. TLS
  (`wss://`), tunnel/VPN choice, PSK lifecycle. Pairs with HoldSpeak
  HS-15.

Roadmap detail: [`pm/roadmap/aipi-lite/`](pm/roadmap/aipi-lite/).

## A note to the community

This bridge represents what we came up with to solve some brutal
memory fragmentation, state-machine deadlocks, and EMI interference
hurdles with the ESP32-S3 audio pipeline on AIPI-Lite. The earlier
version of this repo was a self-contained STT/LLM/TTS loop
(`faster-whisper` + DeepSeek + `gTTS` over an HTTP server); the
current code on `main` is the AIPI-2 rewrite that splits the AI
runtime into HoldSpeak and reduces this side to a thin protocol
translator. If you arrived here from an older fork or a stale link,
the device-audio-output knowledge from the original loop is preserved
in [`docs/DEVICE_AUDIO_OUTPUT.md`](docs/DEVICE_AUDIO_OUTPUT.md) — the
EMI dance and ES8311 quirks were load-bearing and deserve to be
findable.

Pull requests, forks, and ideas are welcome.

## Acknowledgements

This build stands on the shoulders of giants.

- **Robert Lipe** — phenomenal deep-dive engineering and
  documentation on the AIPI hardware and I2S/I2C interfacing:
  https://www.robertlipe.com/449-2/
- **sticks918** — foundational ESPHome configurations and the
  AIPI-Lite repository that made this custom integration possible:
  https://github.com/sticks918/AIPI-Lite-ESPHome
