# HS-21-02 — Unified AIPI Developer Workflow

- **Project:** holdspeak
- **Phase:** 21
- **Status:** done
- **Depends on:** HS-21-01
- **Unblocks:** Phase 22
- **Owner:** unassigned

## Problem

AIPI-Lite now lives inside the HoldSpeak checkout, but the practical workflow
still referenced the old sibling repo and borrowed its virtualenv. Developers
need one obvious way to run AIPI tests, operate the bridge, and flash firmware
from the unified repo without risking local secrets.

## Scope

### In

- Root helper scripts for AIPI setup, tests, bridge operation, and firmware
  commands.
- A unified workflow document for local config, tests, bridge operation, and
  firmware flashing.
- Update imported AIPI docs to point at the unified checkout workflow.
- Validate AIPI tests from `aipi-lite/.venv`.
- Phase 21 closeout.

### Out

- Repackaging the AIPI bridge into HoldSpeak's Python package.
- Live hardware flashing or real-device smoke.
- New device protocol behavior.
- Phase 22 companion UX implementation.

## Acceptance Criteria

- [x] `scripts/aipi_setup.sh` creates/updates `aipi-lite/.venv`.
- [x] `scripts/aipi_test.sh` runs AIPI tests from the unified checkout.
- [x] `scripts/aipi_bridge.sh` runs bridge commands from the unified checkout.
- [x] `scripts/aipi_firmware.sh` wraps ESPHome commands from the unified checkout.
- [x] Docs explain local `secrets.yaml` / `bridge.env` handling.
- [x] AIPI tests pass through the new script.

## Test Plan

- `scripts/aipi_setup.sh`
- `scripts/aipi_test.sh -q`
- `scripts/aipi_bridge.sh --help`
- `scripts/aipi_firmware.sh --help`
- `git check-ignore` for local AIPI config/build paths.
- `git diff --check`.

## Notes

- `scripts/aipi_setup.sh` installs AIPI dev requirements into
  `aipi-lite/.venv` and installs the current HoldSpeak checkout in editable
  mode so AIPI protocol-sync tests can import HoldSpeak's device models.
