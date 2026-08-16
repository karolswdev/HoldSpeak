# Evidence - HS-132-04

- **Story:** HS-132-04 - One utterance, one pipeline
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:33:23Z

- **Command:** `env HOME=/tmp/hs132-04-home uv run pytest -q tests/unit/test_one_pipeline_run.py tests/unit/test_dictation_session_admission.py tests/unit/test_web_routes_remote_dictation.py tests/unit/test_speak_room_delivery.py tests/unit/test_voice_command_dispatch.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** efb1c89eac13c657e7e0cecebfa8185515034115

```text
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 15.36s
```

## Orchestrator notes

- Web proof (not in the captured pytest run): 51 vitest green across
  micStreamSession/MicButton/speakRoom/openMicDeck/speakToFill; tsc clean;
  one_path_census re-run green under the orchestrator (141 passed total).
- Three rounds: round 1 shipped the raw:true delivery + WS pipeline flag;
  round 2 restored voice-macro parity at exactly one pass (fence-elected
  dispatch on the WS final for delivery sessions; field fills never
  dispatch; a fired command consumes the utterance per the hotkey
  contract); round 3 wired the fired-command receipt into the Speak deck
  register (COMMAND · <preview>; failure branch honest).
- Accepted follow-ups on the ledger (recorded, unfixed): re-delivering
  already-piped well text takes a second pass (only the release path
  carries the receipt); REHEARSE on a spoken utterance dry-runs the piped
  text; desktop hold-key speak-to-fill seam untouched (out of scope).
- FirstWords' retained-audio retry now inherits pipeline:false — correct
  for a field fill; noted as a behavior change outside the owned set.
