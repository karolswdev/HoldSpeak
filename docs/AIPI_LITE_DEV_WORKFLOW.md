# AIPI-Lite Developer Workflow

<p align="center">
  <img src="assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="280">
</p>

The AIPI-Lite companion is a portable ESPHome-based device for meeting capture,
coding-agent replies, and status feedback. Put it on Wi-Fi, including a phone
hotspot when needed, and HoldSpeak can use the bridge for real-time meeting
transcription and intelligence.

With Claude/Codex hooks enabled, HoldSpeak can show when an agent is waiting
for your answer. AIPI-Lite can surface that prompt state, cycle waiting
sessions, and let you speak the reply back into the selected coding session.
Remote control works when the device can reach your HoldSpeak bridge over a
network path you control, such as home Wi-Fi, hotspot, VPN, or a private tunnel.

Hardware links:

- [Official AIPI Lite product page](https://aipi.com/products/aipi-lite)
- [Amazon listing](https://www.amazon.com/dp/B0FQNNVV36)

This is the unified-checkout workflow for the AIPI-Lite firmware and bridge.
The source lives in `aipi-lite/`; helper scripts live at repo root in
`scripts/`.

## Local Files

These files are intentionally local and ignored:

- `aipi-lite/secrets.yaml`: ESPHome Wi-Fi/API secrets used at firmware compile time.
- `aipi-lite/bridge.env`: Python bridge runtime config.
- `aipi-lite/.venv/`: AIPI bridge/test Python environment.
- `aipi-lite/.esphome/`: ESPHome build/cache output.

Start from the checked-in templates:

```bash
cp aipi-lite/secrets.yaml.example aipi-lite/secrets.yaml
cp aipi-lite/bridge.env.example aipi-lite/bridge.env
```

Confirm they are ignored before editing:

```bash
git check-ignore -v aipi-lite/secrets.yaml aipi-lite/bridge.env
```

## Python Bridge Environment

Create or update the AIPI bridge environment:

```bash
scripts/aipi_setup.sh
```

This installs `aipi-lite/requirements-dev.txt` into `aipi-lite/.venv`.
It also installs the current HoldSpeak checkout in editable mode inside that
venv so AIPI protocol-sync tests can import HoldSpeak's device contract
models.

Run tests:

```bash
scripts/aipi_test.sh -q
```

Run one test file:

```bash
scripts/aipi_test.sh tests/test_settings.py -q
```

## Bridge Operation

Start HoldSpeak first:

```bash
holdspeak web --no-open
```

Populate `aipi-lite/bridge.env` with at least `HOLDSPEAK_PORT` and
`HOLDSPEAK_PSK`. The PSK comes from:

```bash
holdspeak device-psk show
```

Check both endpoints:

```bash
scripts/aipi_bridge.sh --check
```

Run the bridge:

```bash
scripts/aipi_bridge.sh
```

Useful diagnostics:

```bash
scripts/aipi_bridge.sh --audio-loopback
scripts/aipi_bridge.sh --send-test-audio path/to/16khz-mono-int16.wav
```

## Firmware

Install ESPHome once:

```bash
pipx install esphome
```

Compile:

```bash
scripts/aipi_firmware.sh compile aipi.yaml
```

Flash over USB:

```bash
scripts/aipi_firmware.sh run aipi.yaml --device /dev/ttyACM0
```

Follow logs:

```bash
scripts/aipi_firmware.sh logs aipi.yaml
```

For provisioning details, see `aipi-lite/docs/PROVISIONING.md`.

## Current Boundary

The AIPI bridge remains a separate Python environment under `aipi-lite/.venv`.
That keeps ESPHome/aioesphomeapi pins out of HoldSpeak's main runtime while
still making tests and operation first-class from the unified checkout.

## See also

- [Device Protocol](DEVICE_PROTOCOL.md): the remote-audio WebSocket protocol the
  bridge speaks.
- [Agent Hook Install](AGENT_HOOK_INSTALL.md): wire agent replies through to the
  device.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): what the device controls.
