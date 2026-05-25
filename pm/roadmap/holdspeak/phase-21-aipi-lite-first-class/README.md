# Phase 21 — AIPI-Lite First-Class Integration

**Status:** in-progress (opened 2026-05-24).

Phase 21 pulls the AIPI-Lite firmware and bridge into the HoldSpeak checkout so
device-side work can move in lockstep with the HoldSpeak runtime, protocol, and
PMO history.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `story-01-import-aipi-lite-tree.md` — first-class source import.
- `../../../aipi-lite/README.md` — AIPI-Lite firmware and bridge overview.
- `../../../aipi-lite/aipi.yaml` — ESPHome firmware.
- `../../../aipi-lite/bridge/` — Python bridge package.

## Phase boundaries

This phase owns repository integration, import hygiene, and the immediate
developer workflow needed to work on AIPI and HoldSpeak together. It does not
yet replace the bridge packaging, redesign firmware gestures, or add new
runtime protocol behavior.
