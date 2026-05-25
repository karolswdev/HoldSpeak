# AIPI-Lite Import Note

This directory makes the AIPI-Lite firmware and bridge a first-class part of
the HoldSpeak checkout.

Imported from local sibling checkout:

- **Source path:** `/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`
- **Source branch:** `mine`
- **Source HEAD:** `f3d289f`
- **Imported into:** `aipi-lite/`

The import intentionally includes the current local working tree from the
source checkout, including uncommitted changes to:

- `aipi.yaml`
- `bridge.env.example`
- `bridge/device.py`
- `bridge/settings.py`
- `tests/test_device_methods.py`
- `tests/test_settings.py`
- `ascii_zoo.yaml`
- `zoo_sounds/*.wav`

Local runtime/config files may exist here for development, but they must not be
tracked:

- `aipi-lite/secrets.yaml`
- `aipi-lite/bridge.env`
- `aipi-lite/.esphome/`
- `aipi-lite/.venv/`

Both the root `.gitignore` and `aipi-lite/.gitignore` ignore the sensitive
local config files.
