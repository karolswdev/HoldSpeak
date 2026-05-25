# Phase 21 — Final Summary

- **Phase opened:** 2026-05-24
- **Phase closed:** 2026-05-24
- **Chunks shipped:** 2

## Goal — was it met?

Original goal:

> Make AIPI-Lite a first-class part of the HoldSpeak repository so firmware, bridge, protocol, and companion UX work can be developed and reviewed together.

**Yes.** The AIPI-Lite firmware, Python bridge, docs, tests, local roadmap, and
assets now live under `aipi-lite/`. The unified checkout has root helper
scripts for setup, tests, bridge operation, and ESPHome firmware commands.
Local `secrets.yaml`, `bridge.env`, `.venv`, and `.esphome` state are ignored.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md).

## Exit criteria — final state

- [x] AIPI-Lite firmware and bridge source exist under `aipi-lite/` — [evidence-story-01](./evidence-story-01.md).
- [x] `aipi-lite/secrets.yaml` and `aipi-lite/bridge.env` are ignored by Git — [evidence-story-01](./evidence-story-01.md).
- [x] Import provenance is documented — [evidence-story-01](./evidence-story-01.md).
- [x] Follow-up developer workflow is defined: run tests, flash firmware, and operate bridge from the unified checkout — [evidence-story-02](./evidence-story-02.md).
- [x] `final-summary.md` records the handoff into Phase 22 — this file.

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-21-01 | Import AIPI-Lite tree | `93ae98a` | 2026-05-24 |
| HS-21-02 | Unified AIPI developer workflow | this working set | 2026-05-24 |

## Ready now

- AIPI source: `aipi-lite/`
- Setup: `scripts/aipi_setup.sh`
- Tests: `scripts/aipi_test.sh -q`
- Bridge: `scripts/aipi_bridge.sh --check` and `scripts/aipi_bridge.sh`
- Firmware: `scripts/aipi_firmware.sh compile aipi.yaml` and
  `scripts/aipi_firmware.sh run aipi.yaml --device /dev/ttyACM0`
- Workflow docs: [AIPI-Lite Developer Workflow](../../../../docs/AIPI_LITE_DEV_WORKFLOW.md)

## Handoff

The next phase should be the product-defining AIPI companion UX phase. The
substrate is now together in one repo, so the work can cross firmware,
bridge, HoldSpeak runtime, and PMO in one place.

Likely first decisions:

- companion state model;
- gesture contract;
- LCD polling/push cadence;
- voice reply flow into waiting Claude/Codex;
- live hardware dogfood as the acceptance gate.

## Final asset / test posture

- AIPI setup: `scripts/aipi_setup.sh` — environment ready at
  `aipi-lite/.venv`.
- AIPI tests: `scripts/aipi_test.sh -q` — `163 passed in 7.53s`.
- Bridge wrapper: `scripts/aipi_bridge.sh --help` — passed.
- Firmware wrapper: `scripts/aipi_firmware.sh --help` — passed.
- Ignore checks for local config/build state — passed.
- Diff hygiene: `git diff --check` — passed.
