# Phase 14 - AIPI-Lite Devices: Remote Audio Ingest Substrate

**Last updated:** 2026-05-07 (HS-14-02 shipped — `DeviceRegistry` + `DeviceDescriptor` landed and wired into the web runtime).

## Goal

Establish the on-host audio ingestion substrate that lets external network
devices (the AIPI-Lite ESP32-S3 robot, and any compatible client) push audio
into HoldSpeak's existing voice-typing and meeting pipelines.

The architecture is already most of the way there: `AudioRecorder` and
`MeetingRecorder` are small, focused, and the meeting pipeline is *already*
dual-stream with per-segment speaker labels (`mic_chunks` + `system_chunks`,
`TranscriptSegment.speaker`). What's missing is a way to plug audio in from
something other than a local `sounddevice` stream.

This phase extracts a small audio-source protocol, adds a
`RemoteAudioRecorder` that consumes pushed PCM frames, lights up an audio
ingest WebSocket route, makes per-device speaker labels first-class, and
wires both the voice-typing and meeting paths to use it.

The phase is **same-LAN only**. Cross-network reach (the user "calling home"
to HoldSpeak from a coffee shop / work network with the AIPI-Lite in their
bag) is real and important, but it is **explicitly deferred to phase 15**.
The substrate landed here is designed so that phase 15 can swap in a
tunnel/relay layer without redesigning the protocol.

## Scope

- **In:**
  - `holdspeak/audio.py`: extract an `AudioSource` Protocol/ABC; keep
    `AudioRecorder` as the local-mic implementation.
  - New `holdspeak/device_audio.py` (or similar): `RemoteAudioRecorder`
    consuming pushed PCM frames; `DeviceRegistry` with lifecycle and
    per-device descriptor (id, label, last-seen, queue depth).
  - PSK-based auth: a single shared secret per HoldSpeak install,
    stored in the existing settings store. Per-device PSKs are out of
    scope for this phase (see "Out").
  - New FastAPI WebSocket `/api/devices/audio`: handshake →
    control + binary PCM frames; server can push status messages
    back. Bound to 127.0.0.1 like the rest of HoldSpeak — the
    AIPI-Lite repo's bridge handles LAN-facing exposure.
  - Voice-typing path (`controller.py` + `hotkey.py`): can consume a
    `RemoteAudioRecorder` interchangeably with `AudioRecorder`.
  - Meeting path (`meeting_session.py` + `MeetingRecorder`): accepts
    one or more registered device streams in addition to the local
    mic + system audio. `TranscriptSegment.speaker` resolves to the
    device's registered label.
  - `TranscriptSegment` carries `device_id` (nullable; `null` for the
    legacy local-mic stream).
  - Backpressure policy: per-device bounded queue (default 2 s of
    audio @ 16k mono s16 = ~64 KB), drop-oldest on overflow, log to
    structured runtime status.
  - `/api/runtime/status` extension: active device count, per-device
    queue depth, last-seen timestamp.
  - `docs/DEVICE_PROTOCOL.md`: the WS protocol spec — handshake
    schema, control messages, audio frame format, status push-back,
    error/close codes.

- **Out:**
  - **Cross-network reach** — Tailscale / Cloudflare Tunnel / WireGuard
    / public WAN exposure / mDNS-Funnel. **Phase 15.** Trigger to
    revisit: phase 14 substrate is stable on local LAN and the user
    is ready to take a device off the home network.
  - Per-device PSKs / federation / multi-tenant. Single shared secret
    in phase 14; per-device PSKs revisit when more than one
    HoldSpeak install needs to authorize different devices.
  - AIPI-Lite firmware multi-SSID / AP-mode portable WiFi config.
    Phase 15 (paired with the cross-network work).
  - Wake-word / on-device VAD enhancements. Out of scope; the
    bridge's existing `webrtcvad` segmenter is adequate.
  - Designer-handoff UI work (history view of devices,
    device-management page). The substrate stays API-only in phase
    14; a UI surface lands in phase 16 once we know the actual
    multi-device usage shape.
  - >2 simultaneous devices in one meeting. The architecture
    supports it; UX/UI polish for 3+ defers until the user actually
    runs that configuration.

## Exit criteria (evidence required)

- [ ] `holdspeak/audio.py:AudioSource` Protocol exists; both
  `AudioRecorder` (local mic) and `RemoteAudioRecorder` implement it
  and pass the same shape contract test.
- [ ] `pytest tests/unit/test_remote_audio_recorder.py` runs ≥ 6 cases
  green covering: start/stop without errors, push-then-stop returns
  concatenated audio, queue overflow drops oldest with a logged
  warning, stop without start raises, pushed-then-resampled path
  produces 16k float32, frames after stop are ignored.
- [ ] `pytest tests/integration/test_device_audio_ingest.py` runs an
  end-to-end PCM round-trip through the WebSocket route (handshake
  → control start → PCM frames → control stop → transcript out)
  using a fake STT to keep the test hermetic.
- [ ] `pytest tests/integration/test_device_meeting_session.py` runs
  a meeting end-to-end with one local-mic stream + one device stream
  and asserts `TranscriptSegment.speaker` correctly distinguishes
  by device label.
- [ ] AIPI-Lite + bridge can voice-type a sentence and run a 5-min
  meeting with per-device speaker labels (manual; transcript saved
  with `device_id` set on remote segments). Evidence: paste the
  saved meeting JSON snippet showing labeled segments.
- [ ] `GET /api/runtime/status` includes the new
  `devices: [{id, label, last_seen, queue_depth}]` block, verified
  by an integration test.
- [ ] `docs/DEVICE_PROTOCOL.md` ships, including a WS handshake
  example, an audio frame description, and a status-push example.
- [ ] No regressions: full sweep
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` is green at
  ≥ phase-13 baseline (1406 / 13 skipped).
- [ ] `final-summary.md` records the cross-network deferral with
  the explicit trigger and a one-liner pointing at phase 15.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-14-01 | AudioSource Protocol + RemoteAudioRecorder | done | [story-01-audio-source-protocol.md](./story-01-audio-source-protocol.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-14-02 | DeviceRegistry + device descriptor model | done | [story-02-device-registry.md](./story-02-device-registry.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-14-03 | PSK auth + handshake protocol | backlog | [story-03-auth-handshake.md](./story-03-auth-handshake.md) | — |
| HS-14-04 | `/api/devices/audio` WebSocket + backpressure | backlog | [story-04-audio-ingest-websocket.md](./story-04-audio-ingest-websocket.md) | — |
| HS-14-05 | Voice-typing path consumes remote audio | backlog | [story-05-voice-typing-remote.md](./story-05-voice-typing-remote.md) | — |
| HS-14-06 | Meeting path accepts device streams + per-segment device_id | backlog | [story-06-meeting-device-streams.md](./story-06-meeting-device-streams.md) | — |
| HS-14-07 | Server → device status push-back protocol | backlog | [story-07-status-pushback.md](./story-07-status-pushback.md) | — |
| HS-14-08 | Phase exit + DoD + protocol docs + cross-network deferral | backlog | [story-08-dod.md](./story-08-dod.md) | — |

## Where we are

HS-14-01 + HS-14-02 shipped 2026-05-07. The substrate now has:

- `holdspeak/audio.py:AudioSource` — runtime-checkable Protocol
  over `start_recording` / `stop_recording`. `AudioRecorder`
  conforms structurally with no inheritance change.
- `holdspeak/device_audio.py:RemoteAudioRecorder` — pushed-PCM
  source with bounded internal buffer + drop-oldest + structured
  warning log on overflow.
- `holdspeak/device_audio.py:DeviceRegistry` + `DeviceDescriptor`
  — thread-safe in-memory registry with `register` / `unregister`
  / `get` / `active` / `touch` / `recorder_for`. Label uniqueness
  enforced via typed `DuplicateLabelError`. Same-id re-register
  raises (`DeviceRegistryError`); unregister of an unknown id is
  a no-op (logged at info). `register` rejects blank id/label.
- `MeetingWebServer` accepts an optional `device_registry` and
  exposes it via `app.state.device_registry`; `run_web_runtime`
  creates the singleton and passes it in.

Test coverage: 36 new unit cases across
`test_remote_audio_recorder.py`, `test_audio_source_contract.py`,
and `test_device_registry.py`. Regression sweep on
audio + controller + web_runtime is 76/76 green.

The companion AIPI-Lite repo (`/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`,
branch `mine`) already has a working ESP32-S3 firmware + Python bridge that
runs an end-to-end voice loop against a local Qwen3.5-9B server; this phase
turns that integration around so HoldSpeak (not the bridge's standalone
LLM/TTS) becomes the consumer of the device audio. Cross-repo coordination
notes live in each story under "Notes / open questions".

Pickup: HS-14-03 (PSK auth + handshake protocol) is next.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `AudioRecorder` and `RemoteAudioRecorder` can't share enough behavior to make the Protocol meaningful — too much divergence on lifecycle (sd callback vs pushed frames) | medium | Keep the Protocol minimal: `start()`, `stop() -> ndarray`, and let consumers be agnostic to the source. Don't try to share the actual capture mechanism. | If the Protocol grows past 4 methods, switch to a thin facade pattern and accept light duplication. |
| WebSocket can't sustain steady audio under realistic LAN packet loss / WiFi roaming | medium | Bridge already speaks UDP for ESPHome's voice_assistant; the WS path here is the **ingest** boundary, not the device-to-bridge boundary. The bridge buffers + retries on the WS side. | If steady-state ingest drops > 1% of audio frames over a 10-min meeting, switch the audio sub-stream to a chunked HTTP POST (server-acked) and keep WS for control + status. |
| Per-device PSK absence means a compromised device can impersonate any other on the same install | low (single-user product, LAN-only this phase) | Single-user model + LAN scope makes this acceptable for now. Document it. | If shipping to >1 user / install pre-phase-15, fast-track per-device PSKs. |
| Speaker label collisions when two devices register with the same label | low | DeviceRegistry rejects a registration whose label clashes with an active device's label. | If a real user wants to legitimately overload labels (e.g., "Me" on two devices for redundancy), introduce a `device_role` and split label from role. |
| Backpressure policy (drop-oldest) is wrong for some workloads (e.g., a very latency-tolerant note-taking flow that prefers waiting over losing audio) | low | Default drop-oldest; expose policy via per-device settings later. | If user reports lost transcript content from drops, add a queue-grow-then-block alternative behind a setting. |

## Decisions made (this phase)

- 2026-05-07 — **PSK auth, single shared secret, stored in existing settings store** — simplest viable thing for a single-user / LAN-scope phase. Per-device PSKs revisit at phase 15. — author: PMO + agent.
- 2026-05-07 — **Audio format: 16 kHz mono int16 little-endian on the wire; converted to float32 inside `RemoteAudioRecorder`** — matches what `AudioRecorder` already produces (post-conversion) and what ESPHome's `i2s_audio` emits. No resampling on the device. — author: agent.
- 2026-05-07 — **WebSocket transport, not gRPC or raw UDP** — FastAPI / `uvicorn[standard]` already pulls websockets; no new server stack; works through future tunnels (phase 15) trivially. — author: agent.
- 2026-05-07 — **`TranscriptSegment.device_id` is nullable** — preserves backward-compat with the local-mic path; `null` means "the legacy local mic / system audio". — author: agent.

## Decisions deferred

- **Cross-network reach (Tailscale vs Cloudflare Tunnel vs WireGuard vs custom relay)** — phase 15 owns this. Trigger to revisit: phase 14 substrate is closed *and* the user has surfaced a concrete deployment scenario (which device, which networks, when). Default if no decision: ship phase 14 LAN-only, document the gap, revisit when needed.
- **Per-device PSKs** — phase 16+. Trigger: HoldSpeak ships to a second install OR the user wants to revoke a single device. Default if no decision: shared PSK persists.
- **Multi-device meeting fan-in UI (the operator-facing view of N device streams during a meeting)** — phase 16. Trigger: > 2 simultaneous devices configured by the user in real use. Default: API-only, devices visible via `/api/runtime/status`.
- **Bridge architecture (does it stay external-process Python, or fold into HoldSpeak as a connector_pack?)** — re-evaluate after phase 14 ships. Trigger: phase 15 cross-network work might want the bridge to live inside HoldSpeak so the tunnel termination is in one place. Default: stays external for now.
