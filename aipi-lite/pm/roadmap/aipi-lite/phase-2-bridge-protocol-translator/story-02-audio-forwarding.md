# AIPI-2-02 - Audio Forwarding: Mic Frames → WS Binary

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01
- **Unblocks:** AIPI-2-03, AIPI-2-05
- **Owner:** karol

## Problem

The skeleton (story-01) handshakes with HoldSpeak but doesn't move
audio. This story plumbs the data path: ESPHome's `voice_assistant`
component already streams 16 kHz mono int16 PCM bytes to the bridge
via aioesphomeapi events; we forward those bytes verbatim to the
HoldSpeak WebSocket as binary frames. **No resampling.** HoldSpeak's
`RemoteAudioRecorder.push(bytes)` expects exactly that format.

## Scope

### In

- Subscribe to ESPHome `voice_assistant` audio events on the device
  leg. Verify the event shape against the device — the aioesphomeapi
  surface here is the under-documented part.
- Forward each chunk's raw bytes as a WS binary frame to HoldSpeak.
  No buffering, no transformation, no resampling.
- A bridge-side metric (logged once per second when audio is
  flowing): `bytes_forwarded`, `frames_forwarded`. Lets us confirm
  the path is alive without dumping every frame.
- A `--audio-loopback` debug flag that fakes a steady tone (1 s of
  16k mono int16 sine wave at 440 Hz, sent every second) instead of
  reading from the device. Useful for verifying the HoldSpeak side
  in isolation when the device is offline.
- A CLI smoke-test path: `python3 bridge.py --send-test-audio
  <wav-file>` connects, performs handshake, sends `start`, streams
  the WAV's PCM data as WS binary frames, sends `stop`, exits.
  Decouples audio-path verification from button-event mapping
  (story-03).

### Out

- Button events triggering start/stop (story-03).
- Voice-typing session arbitration logic — that's HoldSpeak's job;
  the bridge just sends frames.
- Audio-format conversion. If voice_assistant emits anything other
  than 16k mono int16 LE, surface that as a story-blocker risk and
  reach for a different capture mechanism.

## Acceptance Criteria

- [x] When audio flows from the device, the bridge logs
  `audio.bytes_forwarded` (with `bytes_forwarded` and
  `frames_forwarded` fields) **at most once per second** —
  `HoldSpeakLeg._metrics_ticker` runs on a 1 s cadence and emits
  only when frames moved during the window. Verified via the
  ticker's unit logic; the integration emit is exercised in
  `--send-test-audio` (a 1 s WAV produces exactly one tick).
- [ ] HoldSpeak's logs show audio being received on the device
  channel (`device.audio.queue` or `RemoteAudioRecorder.push`
  markers). **Pending HoldSpeak running.**
- [x] `--send-test-audio path/to/test.wav` mode shipped:
  validates the WAV format strictly (mono, 16-bit, 16 kHz),
  performs the handshake, sends `start`, streams chunks at
  real-time pace (3200 B / 100 ms), sends `stop`, then briefly
  drains inbound `status` frames so the transcription snippet
  is captured. **Pending HoldSpeak running** for end-to-end
  transcription verification.
- [x] `--audio-loopback` mode shipped: synthesizes 1 s of 440 Hz
  sine via `synth_sine_pcm`, performs the handshake, sends
  `start`, then loops sending the chunk every second with a
  per-10-frames progress log. Ctrl-C triggers a clean `stop` +
  close. **Pending HoldSpeak running** for the "no decode
  errors, no transcription" verification.
- [x] Bridge handles `audio_queue` overflow gracefully:
  `DeviceLeg._handle_va_audio` uses `put_nowait` and structured-
  warns once on the first dropped chunk + every 100th
  thereafter, plus a `recovered` log when drainage resumes. No
  crash on overflow. Bound: `AUDIO_QUEUE_MAXSIZE = 500`.
- [x] On session start, `HoldSpeakLeg.session()` drains any
  pre-session audio from the queue and logs
  `audio.queue.drained_before_session` with the chunk count.
  Reset of `_bytes_window`/`_frames_window` ensures metrics
  are per-session, not cumulative.

Unit tests: `tests/test_audio.py` — 9 cases covering
`synth_sine_pcm` (length, amplitude bounds, validation, short
durations) and `read_wav_pcm` (round-trip, stereo rejection,
sample-rate rejection, bit-depth rejection). All pass.
35/35 total tests pass.

### 2026-05-08 — UDP fix (post-live-test)

First live test against HoldSpeak surfaced that the audio path
**did not work** as originally designed: `_handle_va_start`
returned `None` intending "use API audio," but ESPHome's
`voice_assistant` is UDP-first and the API-audio fallback isn't
wired in this firmware. Symptom: bridge logged
`subscribe.voice_assistant.ok` and `device.voice_assistant.start`
on press but **zero `audio.bytes_forwarded`** events; aioesphomeapi
emitted a stray `Server could not be started` to stdout.

Fix landed same-day:
- New `Settings.udp_audio_port` (default 50000), exposed in
  `bridge.env.example`.
- `DeviceLeg._udp_listener` task bound to `0.0.0.0:UDP_AUDIO_PORT`
  drains UDP datagrams into the shared audio queue.
- `_handle_va_start` returns the UDP port instead of `None`.
- Refactored `_handle_va_audio` (API path, kept as a backup) and
  the new UDP listener to share `_enqueue_audio_bytes`.

Verified end-to-end against live HoldSpeak: voice typing transcribes
and types into the focused host app within ~2 s of release; meeting
attach (`POST /api/meeting/start {"devices":["aipi-1"]}`) streams
audio continuously and produces per-segment transcripts labeled with
the device's identity. Full `[Karol]`/`[Me]`/`[Remote]` per-source
attribution working.

Lesson saved to memory:
`memory/feedback-esphome-voice-assistant-udp.md` — return a UDP
port from `handle_va_start`; returning `None` breaks the audio
path silently.

## Test Plan

- **Unit:** none — this story is pure I/O glue. Behaviour is verified
  in integration.
- **Integration (manual):**
  1. With HoldSpeak + bridge running (story-01 skeleton green):
  2. Use a known-good WAV file:
     `python3 bridge.py --send-test-audio docs/samples/hello-world.wav`
  3. Verify HoldSpeak transcribes "hello world" (or whatever the
     WAV contains) and types it into the focused app on the host.
  4. Run with `--audio-loopback` for 30 s; verify no errors on
     either side; verify HoldSpeak's transcription stays empty (it
     should ignore a pure tone).
  5. With a real device wired (after AIPI-1 hardware verification
     lands): manually trigger `voice_assistant.start` via the API,
     speak, observe the bytes-forwarded counter increment.

## Notes

- **The aioesphomeapi voice_assistant audio-event API is the risk
  point.** Spike at the start of this story:
  ```python
  client.subscribe_voice_assistant(handle_audio, handle_event)
  ```
  Read aioesphomeapi's source to confirm the audio-handler signature
  (likely `(audio_bytes: bytes) -> None`). If the API surface
  doesn't exist or doesn't deliver raw frames, fall back to:
  - A custom ESPHome service that exposes mic frames as binary
    chunks via the API, OR
  - Triggering `voice_assistant.start` and reading the resulting
    events (current `bridge.py` does this — see the existing
    `event_handler` in `bridge.py` lines ~80-130).
- The current `bridge.py` already handles this audio path
  (around `on_voice_assistant_audio`). Extract that pattern; the
  rewrite is mostly removing the buffering + faster-whisper call,
  not figuring out where the bytes come from.
- **Do not buffer.** Push every chunk to the WS as it arrives.
  HoldSpeak's `RemoteAudioRecorder.push` already does its own bounded
  buffering; an extra layer in the bridge adds latency for no gain.
- HoldSpeak server enforces a 2 s default audio queue. If the
  bridge sends faster than HoldSpeak transcribes, frames get
  drop-oldest-ed. That's HoldSpeak's design; the bridge just logs
  the overflow signal.
