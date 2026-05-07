# AIPI-Lite Integration — Phase 0/1 Notes

Working branch: `aipi-lite-integration`. This file is a living scratchpad that
captures the audio-capture path map and the proposed grafting points before any
code lands. Discuss, edit in-place; once we agree on shape, implementation
PRs reference back here.

## TL;DR

The HoldSpeak audio pipeline is **already** structured around two pluggable
concepts that map perfectly to remote devices:

1. `AudioRecorder` (voice-typing path) — single mic stream
2. `MeetingRecorder` (meetings path) — already dual-stream (`mic_chunks` +
   `system_chunks`) with per-segment speaker labels

Adding an AIPI-Lite device just means:

- A `RemoteAudioRecorder` that satisfies the same `start_recording()` /
  `stop_recording()` contract as the current `AudioRecorder` but consumes
  pushed audio instead of opening a sounddevice stream
- A FastAPI WebSocket at `/api/devices/audio` that accepts PCM frames + control
  messages from the bridge running alongside the AIPI-Lite firmware
- A `DeviceRegistry` so multiple devices can register with labels (becomes
  per-segment `speaker` attribution for free)

HoldSpeak does **not** need to expose external endpoints. The bridge is the
LAN-facing layer; HoldSpeak stays bound to 127.0.0.1.

## Audio capture path — code map

### Voice typing (push-to-talk)

```
holdspeak/audio.py
  └─ AudioRecorder
       start_recording()   → opens sd.InputStream with a callback that pushes
                              float32 mono frames into self._frames
       stop_recording()    → returns concatenated 16k mono float32 ndarray
                              (resamples if device rate ≠ 16k)
```

`AudioRecorder` is a tiny wrapper (~215 lines, one class). Its API is small
enough that a `RemoteAudioRecorder` sibling can satisfy the same shape.

Consumers:
- `holdspeak/controller.py` — orchestrates the hold-to-record gesture
- `holdspeak/hotkey.py` — global hotkey bound to start/stop on the recorder

### Meetings (continuous, dual-stream)

```
holdspeak/meeting_session.py
  └─ MeetingSession
       start()     → creates MeetingRecorder, kicks off transcribe loop
       stop()      → finalizes, runs MIR pipeline, persists
       _recorder.get_pending_chunks(...) → (mic_chunks, system_chunks)
       _transcribe_chunks(mic_chunks, system_chunks, final=False)
                   → feeds Transcriber, builds TranscriptSegment list,
                     each segment has a `speaker` field
```

`MeetingState` already carries `mic_label = "Me"` and `remote_label = "Remote"`,
and `TranscriptSegment.speaker` is per-segment. Per-device labels would
plug in here naturally.

### STT

`holdspeak/transcribe.py` — `Transcriber` is backend-agnostic (mlx-whisper on
darwin/arm64, faster-whisper on Linux). Consumes ndarrays. Doesn't care about
the audio source. **No changes needed for device support.**

### Existing FastAPI surface (web_server.py)

Already wired:
- `POST /api/meeting/start` — line 774
- `POST /api/meeting/stop` — line 794
- `POST /api/bookmark` — line 730
- `POST /api/stop` — line 799
- `GET /api/state`, `/api/runtime/status`
- WebSocket support already in via `uvicorn[standard]`

Adding a `WebSocket /api/devices/audio` is a new route, not a new server.

## Where AIPI-Lite hardware fits

| AIPI-Lite event | Existing HoldSpeak action |
|---|---|
| Press button (hold-to-talk) | Start `RemoteAudioRecorder`; on release, hand the frames to the same flow that voice-typing uses |
| Triple-tap (toggle continuous) | `POST /api/meeting/start` or `/api/meeting/stop` |
| Long-press during a meeting | `POST /api/bookmark` (`MeetingState.get_context_around()` already exists for "what happened around this mark") |
| Continuous-mode VAD utterance | Append to the device's stream as a `mic_chunk` |
| HoldSpeak event (e.g., "Saved" or action-item identified) | Bridge → device's `update_screen` API service → LCD |

The maps to existing primitives — no new mental model.

## Proposed grafting points (Phase 1)

### 1. New module: `holdspeak/device_audio.py`

```python
class RemoteAudioRecorder(AudioRecorder):
    """Drop-in replacement for AudioRecorder that consumes pushed PCM
    frames from a registered remote device instead of opening a local
    sounddevice stream. Shares concatenation/resample logic with the
    parent."""

    def __init__(self, device_id: str, *, sample_rate: int = 16_000):
        super().__init__(sample_rate=sample_rate)
        self.device_id = device_id

    def start_recording(self) -> None:
        # No sounddevice. Just arm the buffer.
        ...

    def push(self, pcm: np.ndarray) -> None:
        # Called by the WebSocket handler on each incoming frame.
        ...

    def stop_recording(self) -> np.ndarray:
        # Same return contract as AudioRecorder.stop_recording.
        ...


class DeviceRegistry:
    """Tracks connected AIPI-Lite (or compatible) devices, their labels,
    and their RemoteAudioRecorder instances. One registry per HoldSpeak
    runtime."""
    ...
```

### 2. New route: `WebSocket /api/devices/audio`

```python
@app.websocket("/api/devices/audio")
async def device_audio(ws: WebSocket):
    # Handshake: device sends {type: "hello", device_id, label, psk}
    # Stream: alternating control + audio frames
    #   {type: "start"} / {type: "stop"} / binary PCM frames (16k mono s16)
    # Server may push {type: "status", text: "..."} for LCD updates
```

Auth: shared PSK in handshake. Bound to 127.0.0.1 same as the rest of
HoldSpeak. The bridge running on the same machine consumes this; it's the
bridge that handles LAN-facing concerns.

### 3. Per-device label routing

Wire `DeviceRegistry.get(device_id).label` into the `speaker` field of new
`TranscriptSegment`s. `MeetingState` already supports `mic_label` and
`remote_label`; we add either:
- A `device_labels: dict[str, str]` map, or
- A `Speakers` registry with N labels (more honest for >2 sources)

### 4. Bridge protocol translator

Lives next to `bridge.py` (in the AIPI-Lite repo). Reads ESPHome `voice_assistant`
events, opens a single `wss://localhost/api/devices/audio` connection per
configured device, forwards audio + control messages, listens for status
push-back to forward to the device's `update_screen` API service.

## Open questions before code

1. **Connector pack vs. native module.** `holdspeak/connector_packs/` exists.
   Is "remote audio device" conceptually a connector pack (configurable, hot-
   loadable) or a first-class core feature? My read: core feature — too tightly
   coupled to the audio capture path to be a pack. But worth a glance at the
   pack contract to be sure.
2. **Auth model.** PSK in handshake is the simplest viable thing. Per-device
   PSKs let you revoke a single device. Shared PSK is operationally easier.
   Probably per-device, with a small CLI to issue them.
3. **Backpressure.** What happens when the WebSocket buffers fill? PCM at 16k
   mono s16 is 32 KB/s — modest, but a single laggy device shouldn't stall
   the meeting transcribe loop. Likely: per-device bounded queue, drop oldest
   on overflow, log.
4. **Discovery.** mDNS announce of `_holdspeak._tcp` so the bridge can find
   HoldSpeak without static config. Optional but nice.
5. **Hotkey vs button.** Today the hotkey starts `AudioRecorder`. A device
   button starts a `RemoteAudioRecorder`. Should they be mutually exclusive
   per-meeting, or coexist (so you can hotkey-mark while a device is also
   capturing)? My read: coexist — they're different streams.

## Phase 0 (no code changes, get audio flowing today)

Skip all the above and have the bridge feed a virtual PipeWire source. HoldSpeak
captures it as its mic input. Loses status push-back and per-device labeling,
but proves the audio path end-to-end in ~1 hour. Useful as a smoke test before
investing in Phase 1.

```bash
# On the laptop running HoldSpeak:
pactl load-module module-null-sink sink_name=aipi sink_properties=device.description="AIPI-Lite"
# Bridge then writes decoded PCM to "aipi" via paplay or pw-cat.
# HoldSpeak picks up the auto-monitor source as a mic option.
```

## Decision needed

Phase 0 first (smoke test, ~1 hour) → then Phase 1 (cleanest architecture, ~few
days)? Or skip 0 and go straight to 1? I lean toward 0 first — it de-risks the
audio-quality assumptions before we touch HoldSpeak code.
