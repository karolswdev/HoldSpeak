# AIPI-Lite Developer Workflow

<p align="center">
  <img src="assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="280">
</p>

This page shows how to build, test, and run the AIPI-Lite bridge and firmware from the HoldSpeak checkout. For what the device does, see [AIPI-Lite companion](AIPI_LITE.md).

The source is in `aipi-lite/`. The helper scripts are in `scripts/`.

## 1. Create the local files

Git ignores these files:

- `aipi-lite/secrets.yaml`: Wi-Fi and API secrets for the firmware build.
- `aipi-lite/bridge.env`: settings for the bridge.
- `aipi-lite/.venv/`: the bridge and test Python environment.
- `aipi-lite/.esphome/`: ESPHome build cache.

Copy the templates:

```bash
cp aipi-lite/secrets.yaml.example aipi-lite/secrets.yaml
cp aipi-lite/bridge.env.example aipi-lite/bridge.env
```

Confirm that Git ignores them:

```bash
git check-ignore -v aipi-lite/secrets.yaml aipi-lite/bridge.env
```

## 2. Create the bridge environment

```bash
scripts/aipi_setup.sh
```

The script installs `aipi-lite/requirements-dev.txt` into `aipi-lite/.venv`. It also installs this checkout in editable mode. The protocol-sync tests need it.

## 3. Run the tests

```bash
scripts/aipi_test.sh -q
scripts/aipi_test.sh tests/test_settings.py -q
```

The second command runs one file.

## 4. Run the bridge

1. Start HoldSpeak:

   ```bash
   holdspeak web --no-open
   ```

2. Read the port from the startup output. Read the PSK:

   ```bash
   holdspeak device-psk show
   ```

3. Set `HOLDSPEAK_PORT` and `HOLDSPEAK_PSK` in `aipi-lite/bridge.env`.
4. Check both endpoints:

   ```bash
   scripts/aipi_bridge.sh --check
   ```

5. Start the bridge:

   ```bash
   scripts/aipi_bridge.sh
   ```

Diagnostics:

```bash
scripts/aipi_bridge.sh --audio-loopback
scripts/aipi_bridge.sh --send-test-audio path/to/16khz-mono-int16.wav
```

`bridge.env.example` lists every setting, such as `ESPHOME_HOST`, `DEVICE_ID`, `DEVICE_LABEL`, and `UDP_AUDIO_PORT`.

## 5. Build and flash the firmware

Install ESPHome once:

```bash
pipx install esphome
```

Then run:

```bash
scripts/aipi_firmware.sh compile aipi.yaml
scripts/aipi_firmware.sh run aipi.yaml --device /dev/ttyACM0
scripts/aipi_firmware.sh logs aipi.yaml
```

The commands compile, flash over USB, and follow the logs. For provisioning, see `aipi-lite/docs/PROVISIONING.md`.

## See also

- [Device Protocol](DEVICE_PROTOCOL.md): the WebSocket protocol the bridge speaks.
- [Agent Hook Install](AGENT_HOOK_INSTALL.md): show agent questions on the device.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): what the device controls.
