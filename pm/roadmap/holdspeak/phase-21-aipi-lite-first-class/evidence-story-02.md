# Evidence — HS-21-02 Unified AIPI Developer Workflow

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-21-02](./story-02-unified-aipi-developer-workflow.md)

## What changed

- Added root AIPI helper scripts:
  - `scripts/aipi_setup.sh`
  - `scripts/aipi_test.sh`
  - `scripts/aipi_bridge.sh`
  - `scripts/aipi_firmware.sh`
- Added [AIPI-Lite Developer Workflow](../../../../docs/AIPI_LITE_DEV_WORKFLOW.md).
- Updated the imported AIPI README and bridge runbook to use the unified
  checkout.
- Updated the systemd service template path to the unified checkout layout.
- Closed Phase 21 with a final summary.

## Validation

```bash
scripts/aipi_setup.sh
```

Result:

```text
AIPI-Lite environment ready: /home/karol/dev/HoldSpeak/aipi-lite/.venv
```

```bash
scripts/aipi_test.sh -q
```

Result:

```text
163 passed in 7.53s
```

```bash
scripts/aipi_bridge.sh --help
scripts/aipi_firmware.sh --help
```

Result: both commands printed usage and exited 0.

```bash
git check-ignore -v aipi-lite/secrets.yaml aipi-lite/bridge.env aipi-lite/.venv/bin/python aipi-lite/.esphome/foo
```

Result:

```text
aipi-lite/.gitignore:1:secrets.yaml  aipi-lite/secrets.yaml
aipi-lite/.gitignore:2:bridge.env    aipi-lite/bridge.env
aipi-lite/.gitignore:4:.venv/        aipi-lite/.venv/bin/python
aipi-lite/.gitignore:3:.esphome/     aipi-lite/.esphome/foo
```

```bash
git diff --check
```

Result: passed.

## Notes

- First `scripts/aipi_test.sh -q` run failed because the AIPI venv did not
  include HoldSpeak's core dependencies, and protocol-sync tests import
  `holdspeak.device_audio.DeviceHandshake`. `scripts/aipi_setup.sh` now installs
  the current HoldSpeak checkout in editable mode into `aipi-lite/.venv`.
- Live firmware flashing was not run; `scripts/aipi_firmware.sh --help`
  validates the wrapper, and the doc records the flash commands.
