# Evidence - HS-151-07

- **Story:** HS-151-07 - The fired-session admission (the attended leg's rider)
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-30T06:36:43Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_phase151_fired_session_admission.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_web_server_conductor_wiring.py tests/unit/test_scheduled_recording_conductor.py tests/unit/test_scheduled_recording_routes.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c37b2d9ec17170d0067078f67517edba757c597a

```text
........................................................................ [ 60%]
...............................................                          [100%]
119 passed in 40.95s
```

## Orchestrator triage — 2026-08-30 (~02:00)

- The counsel-ruled ~30-line fix verified by my own hand (95 focused
  green incl. the four new pins and every ladder suite): the meeting
  admission pre-checks the capability:speech.transcribe head;
  absent → a three-route bundle, no preload declaration, raw capture
  continues, and transcription_status="record_only" with
  reason_code=transcription_no_speech_assignment persists durably —
  the silent-empty-transcript era ends. The bundle service untouched.
- The P1/P3 precondition RESOLVED: migrate_startup_legacy_assignments
  (runtime.py:168-172 → inference_adoption_service.py:2020-2226)
  creates the speech.transcribe head AT BROKER STARTUP on any HOME
  with an importable whisper backend (mlx on this Mac) —
  empirically verified on a pure fresh HOME. The attended HOMEs'
  missing head despite this (wire-before-boot sequencing) is the
  replay's first check — visible either way now.
- Defect ledger for this story: #10 (the bedrock) FIXED with honest
  degradation; #7/#8/#9's fixes rode the prior commit and the
  counsel KEPT all of tonight's groundwork unamended.
