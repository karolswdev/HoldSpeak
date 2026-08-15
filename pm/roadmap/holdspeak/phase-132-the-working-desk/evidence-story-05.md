# Evidence - HS-132-05

- **Story:** HS-132-05 - The streaming mic is honest
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:57:06Z

- **Command:** `env HOME=/tmp/hs132-05-vhome uv run pytest -q tests/unit/test_streaming_mic_honesty.py tests/unit/test_one_pipeline_run.py tests/unit/test_dictation_session_admission.py tests/unit/test_browser_mic_pipeline.py tests/unit/test_audio_floor_open_mic.py tests/unit/test_voice_typing_session.py tests/unit/test_one_path_census.py tests/unit/test_web_vocabulary_guard.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a8810c739b1847d2c273c58651f3ac0dfc5d38a5

```text
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed in 60.10s (0:01:00)
```

## Orchestrator notes

- Web proof (not in the captured run): 45 vitest green across
  micStreamSession/MicButton/dictationRecovery/speakRoom under the
  orchestrator's own run.
- Design ruling executed (default adopted; owner may overrule at the
  sitting): per-chunk transcription DELETED — chunks accumulate for one
  Whisper pass per utterance, off the hotkey's transcription_lock; the
  dead onPartial plumbing is stripped. The one-path census count moved
  100 → 99 with the deletion documented; zero findings.
- Two extra real bugs found by the new tests and fixed: the start-frame →
  first-chunk gap was unheartbeated, and (pre-existing) a mid-stream
  refusal fell through and sent a final behind an already-delivered
  error.
- Retained audio: PCM persisted at final send AND on error/socket-drop,
  cleared on any final; 16MB cap (~8 min) aligned with pendingVoice and
  the transcribe route; UI claim gated on session.retained().
- Named refusals ride reason/failure_category/mic_interval end to end; a
  lost floor is audio_floor_lost + closed interval; an empty final can
  never overwrite a named failure as no_speech. The MicButton em-dash
  vocabulary offense fixed per the addendum (guard green).
- The lamp: drainHold() moves the buffer without touching the graph —
  one beginHold, one endHold, no mid-capture suspend.
