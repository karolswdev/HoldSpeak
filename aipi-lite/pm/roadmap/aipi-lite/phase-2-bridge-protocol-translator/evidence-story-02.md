# Evidence — AIPI-2-02 — Audio Forwarding: Mic Frames → WS Binary

- **Shipped:** 2026-05-07 (initial); UDP fix 2026-05-08
- **Commit:** `bd7a107` (`feat(bridge): AIPI-2-02 audio forwarding + smoke-test CLI modes`) + `9ff88a6` (`fix(bridge): switch audio path to UDP — voice_assistant is UDP-first`)
- **Owner:** karol

## Files touched

- `bridge.py` (later `bridge/audio.py` + `bridge/device.py` + `bridge/holdspeak.py` post-AIPI-2-08):
  - `synth_sine_pcm` + `read_wav_pcm` helpers (16 kHz mono int16 strict validation).
  - `DeviceLeg._handle_va_audio` (API-path enqueue, later removed in AIPI-2-08 as dead code).
  - `DeviceLeg._udp_listener` (added 2026-05-08 in the UDP fix; binds `0.0.0.0:UDP_AUDIO_PORT`, drains datagrams into the audio queue).
  - `HoldSpeakLeg.session()` gathers heartbeat / receiver / audio-sender / 1s metrics-ticker tasks.
  - `_metrics_ticker` emits `audio.bytes_forwarded` once per second only when frames moved.
  - CLI flags `--send-test-audio <wav>` (real-time-paced WAV streamer) + `--audio-loopback` (continuous 440 Hz sine).
- `bridge.env.example` — added `udp_audio_port=50000` field (UDP fix).
- `tests/test_audio.py` — 9 cases on `synth_sine_pcm` + `read_wav_pcm` (length, amplitude, validation, stereo/SR/bit-depth rejection).

## Verification artifacts

```
$ .venv/bin/python -m pytest -q tests/test_audio.py
9 passed

$ .venv/bin/python -m pytest -q
98 passed in 2.80s
```

**Live HoldSpeak verification (2026-05-08, post-UDP-fix):**

- Voice typing: button-press → speak → release → text typed into focused host app within ~2 s of release.
- Meeting attach via `POST /api/meeting/start {"devices":["aipi-1"]}` streams audio continuously; meeting transcript shows per-segment entries tagged with the device's `DEVICE_LABEL`.
- Per-source attribution working in the meeting view: `[Karol]` / `[Me]` / `[Remote]` correctly resolved.

This live trace is the load-bearing live-verification anchor for the phase — the audio data path is the integration spine; if it works end-to-end, the handshake (story 01), control mapping (story 03), config (story 04), and meeting attach (story 05) all worked at the same instant.

## Acceptance criteria — re-checked

- [x] `audio.bytes_forwarded` log emitted at most once per second — `HoldSpeakLeg._metrics_ticker` only emits when the per-window byte counter is non-zero. Verified by 1 s WAV producing exactly one tick.
- [x] HoldSpeak shows audio received on the device channel — verified live 2026-05-08 (transcripts arrived).
- [x] `--send-test-audio` mode shipped: strict WAV validation, real-time pacing (3200 B / 100 ms), drains inbound `status` frames briefly post-stop. End-to-end transcription verified via the live trace above (the device's mic path is the same code).
- [x] `--audio-loopback` mode shipped: 1 s of 440 Hz sine, continuous send with per-10-frames progress log, clean Ctrl-C tearing down. Sine stream produces no transcription on HoldSpeak (HoldSpeak ignores pure tones); confirmed on the same live session.
- [x] Audio-queue overflow handling: `put_nowait` + structured-warn on first drop + every 100th + a `recovered` log when drainage resumes. `AUDIO_QUEUE_MAXSIZE = 500`. Code path inspected; no overflow observed in the live trace (mic capture rate is well below queue drain rate).
- [x] Pre-session drain: `HoldSpeakLeg.session()` drains the queue + logs `audio.queue.drained_before_session` with the chunk count. Window counters reset per session.

## Deviations from plan

- **UDP fix (2026-05-08).** Originally designed `_handle_va_start` to return `None` (intending "use API audio"). Live test surfaced that ESPHome's `voice_assistant` is UDP-first and the API-audio fallback isn't wired in this firmware — bridge logged subscribe.ok and start.ok on press but zero `audio.bytes_forwarded`. Same-day fix added a UDP listener task and `_handle_va_start` now returns the UDP port. Lesson saved to `~/.claude/projects/-home-karol-dev-esp32-AIPI-Lite-Voice-Bridge/memory/feedback-esphome-voice-assistant-udp.md`.
- The API-audio path (`_handle_va_audio`) was kept as a backup at this story but **deleted in AIPI-2-08** as documented dead code (doesn't fire for stock ESPHome firmware).

## Follow-ups

- None outstanding for the audio path. Mic-level meter (RMS bar pushed to LCD activity slot) is teed up in AIPI-2-07's notes as a candidate followup; needs API-roundtrip cost measurement before commit.
