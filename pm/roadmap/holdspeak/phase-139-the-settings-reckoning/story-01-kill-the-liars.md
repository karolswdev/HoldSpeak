# HS-139-01 — Kill the liars

- **Project:** holdspeak
- **Phase:** 139
- **Status:** done
- **Depends on:** none
- **Unblocks:** 139-05
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

Five settings save values that nothing reads (census rows 2, 3, 4, 47,
51, 52) and two dials render twice writing the same config path (rows
83/87 vs 7/9). A dial that does nothing is a lie on glass — Article VI.

## Scope

- **In:** delete the dead controls AND their config fields + service
  validation: `ui.show_audio_meter` (config/ui.py:22), `ui.history_lines`
  (config/ui.py:23), `ui.theme` (config/ui.py; SettingsCore.tsx:450),
  `meeting.intel_queue_poll_seconds`,
  `meeting.intel_retry_failure_alert_percent`,
  `meeting.intel_retry_failure_hysteresis_minutes` (all unthreaded to
  IntelQueue — it runs on hardcoded defaults regardless). De-duplicate:
  Backend and Warm-on-start each render once (Models module keeps them;
  Transcription module's copies die — SettingsCore.tsx:467,469).
  Config.load proven tolerant of the now-unknown keys in an existing
  config.json.
- **Out:** wiring any dead dial up instead (the desk is dark by law;
  the queue constants are fine); any other module's controls.

## Acceptance criteria

- [ ] The six dead fields exist nowhere: not on glass, not in the config
  dataclasses, not in settings_service validation, not in the API schema.
- [ ] Backend and Warm-on-start appear exactly once each (Models).
- [ ] A pre-reckoning `config.json` containing the deleted keys loads
  without error and without resurrection (test proves it).
- [ ] No consumer anywhere read a killed field (grep receipts in the
  worker report; full suite green at the orchestrator's gate).

## Test plan

- **Unit:** settings service validation tests updated; a
  tolerant-load test with a legacy config.json fixture; existing
  settings route tests green.
- **Web:** settings vitest updated (no dead controls rendered).
