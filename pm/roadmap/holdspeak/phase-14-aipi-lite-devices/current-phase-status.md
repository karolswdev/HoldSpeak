# Phase 14 - AIPI-Lite Devices: Remote Audio Ingest Substrate

**Phase closed:** 2026-05-07. See [final-summary.md](./final-summary.md). This file is now frozen per PMO contract §6.

**Last updated:** 2026-05-07 (HS-14-08 shipped — phase closed; protocol doc + final summary published).

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
| HS-14-03 | PSK auth + handshake protocol | done | [story-03-auth-handshake.md](./story-03-auth-handshake.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-14-04 | `/api/devices/audio` WebSocket + backpressure | done | [story-04-audio-ingest-websocket.md](./story-04-audio-ingest-websocket.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-14-05 | Voice-typing path consumes remote audio | done | [story-05-voice-typing-remote.md](./story-05-voice-typing-remote.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-14-06 | Meeting path accepts device streams + per-segment device_id | done | [story-06-meeting-device-streams.md](./story-06-meeting-device-streams.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-14-07 | Server → device status push-back protocol | done | [story-07-status-pushback.md](./story-07-status-pushback.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-14-08 | Phase exit + DoD + protocol docs + cross-network deferral | done | [story-08-dod.md](./story-08-dod.md) | [evidence-story-08.md](./evidence-story-08.md) |

## Where we are

HS-14-01 + HS-14-02 + HS-14-03 shipped 2026-05-07. The substrate
now has:

- `holdspeak/audio.py:AudioSource` — runtime-checkable Protocol
  over `start_recording` / `stop_recording`. `AudioRecorder`
  conforms structurally with no inheritance change.
- `holdspeak/device_audio.py:RemoteAudioRecorder` — pushed-PCM
  source with bounded internal buffer + drop-oldest + structured
  warning log on overflow.
- `holdspeak/device_audio.py:DeviceRegistry` + `DeviceDescriptor`
  — thread-safe in-memory registry; label uniqueness enforced via
  typed `DuplicateLabelError`; idempotent unregister; copy-on-read.
- `MeetingWebServer` accepts an optional `device_registry` and
  exposes it via `app.state.device_registry`; `run_web_runtime`
  creates the singleton and passes it in.
- `holdspeak/device_audio.py` handshake protocol —
  `DeviceHandshake` Pydantic model (strict / `extra=forbid`),
  `parse_handshake`, `verify_psk` (constant-time via
  `hmac.compare_digest`), and the WebSocket close-code
  constants `WS_CLOSE_INVALID_HANDSHAKE` (4001),
  `WS_CLOSE_PSK_MISMATCH` (4003), `WS_CLOSE_DUPLICATE_LABEL`
  (4009). Typed `InvalidHandshakeError` / `PskMismatchError`
  exceptions carry the close code so HS-14-04 can map cleanly
  without re-deriving the policy.
- `holdspeak/config.py:DeviceConfig` — new top-level
  `Config.device.psk: str`. Generated lazily on first use by
  `ensure_device_psk`; `rotate_device_psk` regenerates +
  persists.
- `holdspeak device-psk show` / `rotate` CLI subcommand.

Test coverage: 61 new unit cases across
`test_remote_audio_recorder.py`, `test_audio_source_contract.py`,
`test_device_registry.py`, and `test_device_handshake.py`.
Regression sweep on audio + controller + web_runtime + config is
162/162 green.

The companion AIPI-Lite repo (`/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`,
branch `mine`) already has a working ESP32-S3 firmware + Python bridge that
runs an end-to-end voice loop against a local Qwen3.5-9B server; this phase
turns that integration around so HoldSpeak (not the bridge's standalone
LLM/TTS) becomes the consumer of the device audio. Cross-repo coordination
notes live in each story under "Notes / open questions".

**HS-14-04 (2026-05-07):** `/api/devices/audio` WebSocket route is
live. New module `holdspeak/device_audio_ws.py` exposes
`register_device_audio_routes(app, *, device_registry, get_psk,
on_chunk)`; `MeetingWebServer` calls it during `_create_app` and
accepts `device_psk_provider` + `on_device_audio_chunk` kwargs.
Handshake → PSK verify → `registry.register()` → `hello-ack`;
dispatch loop honours `start` / `stop` / `heartbeat` JSON control
frames and binary PCM frames. Stop-frame audio is fanned out to a
caller-supplied `on_chunk(device_id, ndarray)` consumer (HS-14-05
/ HS-14-06 will plug the voice-typing and meeting paths in).
Client disconnect (clean or rude) drops in-flight audio, stops
the recorder, and unregisters the device. `RemoteAudioRecorder`
gained a `device_id` kwarg + `buffered_bytes` property; overflow
logs once per burst as `device.queue.overflow` with `device_id` +
`dropped_bytes`. `DeviceRegistry.active()` now refreshes
`queue_depth` from each live recorder.

Test coverage: 14 new integration cases in
`tests/integration/test_device_audio_ingest.py` (handshake
success, 4001 bad-handshake/missing-field/extra-field, 4003 bad
PSK, 4009 duplicate label, push-then-stop ndarray emission,
heartbeat last_seen refresh, clean disconnect, mid-recording
disconnect drops audio, overflow drops oldest with single log,
`active()` reflects live queue depth, PSK rotation takes effect
on reconnect). 218/218 green on the sweep across audio + device +
controller + web_runtime + config + intel_streaming.

Pickup: HS-14-05 (voice-typing path consumes remote audio) is
next; the `on_chunk` hook is the integration point.

**HS-14-05 (2026-05-07):** Voice-typing path now consumes remote
audio. New module `holdspeak/voice_typing.py` with
`VoiceTypingSession` — a one-at-a-time arbiter shared between
the local hotkey and any registered device. `begin(source,
owner)` starts the source under lock; concurrent claims return
`False` (silent for the hotkey, surfaced to the device as a
`{"type": "error", "code": "session_busy", ...}` frame).
`end(owner)` stops the source and returns the captured ndarray;
`cancel(owner)` is the disconnect-cleanup path.

`device_audio_ws.register_device_audio_routes` gained
`on_voice_start` / `on_voice_stop` / `on_voice_cancel`
handlers. When set, the WS dispatcher delegates start/stop
semantics to them (instead of the legacy direct
`recorder.start_recording()` / `recorder.stop_recording()` +
`on_chunk` path used by HS-14-04 tests). On disconnect, the
teardown runs `on_voice_cancel(device_id)` first so a session
this device owned is dropped before the recorder is torn down.

`MeetingWebServer` forwards three new constructor kwargs.
`run_web_runtime` constructs a single shared `VoiceTypingSession`
and wires:
- the local hotkey → `voice_session.begin(local_recorder,
  owner="hotkey")`,
- the device WS → `voice_session.begin(device_recorder,
  owner=f"device:{device_id}")`,
- shared transcribe+type extracted into `_transcribe_and_type`
  so both paths land in the same Whisper / `text_processor` /
  `TextTyper` pipeline.

Test coverage: 11 unit cases on `VoiceTypingSession` (begin /
end / mismatched owner / no-active-session / failed-source /
cancel / blank-owner / concurrent-begins-serialize) +
4 integration cases on the WS path (full pipeline end-to-end
with fake STT and mock typer; concurrent device receives
`session_busy`; mid-session disconnect cancels cleanly; legacy
`on_chunk` path still works when voice handlers are absent).
232/232 green on the audio + device + voice + controller +
web_runtime + config + intel_streaming sweep.

Pickup: HS-14-06 (meeting path accepts device streams +
per-segment `device_id`) is next; HS-14-07 (server → device
status push) and HS-14-08 (DoD) close the phase.

**HS-14-06 (2026-05-07):** Meeting path now accepts device
streams. `TranscriptSegment.device_id: Optional[str] = None`
flows through `to_dict`; legacy mic + system segments preserve
`None`. `MeetingState.devices: list[DeviceDescriptor]` (with a
JSON-safe shim that handles datetime → ISO conversion) is
captured at attach time and round-trips through `to_dict`.

`RemoteAudioRecorder.drain()` returns and clears the buffer
without stopping the recording; the meeting drains pushed PCM
on the same cadence as the mic / system streams.
`MeetingRecorder` gained `register_device_stream` /
`unregister_device_stream` / `device_label` /
`registered_device_ids` / `get_pending_device_chunks`. The
recorder doesn't capture device audio itself — the WS route
pushes via `RemoteAudioRecorder.push` and the meeting polls.

`MeetingSession` gained `attach_device(descriptor, source)` /
`detach_device(device_id)` / `is_device_attached(device_id)`.
`_transcribe_chunks` accepts a `device_chunks: dict[str,
list[AudioChunk]]` kwarg and emits per-device `TranscriptSegment`s
with `device_id` set and `speaker` resolved to the device's
registered label. The transcription loop and the final-flush
path both drain device streams so audio captured between the
last poll and meeting stop still surfaces in the transcript.

`POST /api/meeting/start` accepts an optional Pydantic body
`{devices: [device_id...]}`. `web_runtime._start_meeting`
validates each id against `device_registry.get(...)` *before*
spinning up the session; an unknown id raises
`_UnknownDeviceError`, which the route maps to 404 with the
offending `device_id` in the JSON body. After the session
starts, attach loops over the validated descriptors.

Voice handlers (HS-14-05) now respect meeting attachment:
when a meeting is active, `_on_device_voice_start` returns
`True` (no-op) for an attached device — the meeting already
owns the recorder lifecycle — and returns `False` (yields
`session_busy` to the device) for any non-attached device.
`_on_device_voice_stop` is a no-op for attached devices for
the same reason. Meetings own audio routing; voice typing
holds the floor only when no meeting is active.

Test coverage: 4 new unit cases on `RemoteAudioRecorder.drain`,
2 round-trip cases on `MeetingState.devices`, 1
`device_id`-on-segment case, and 7 integration cases in
`tests/integration/test_device_meeting_session.py` (attach
records descriptor + starts source; device chunks become
labeled segments via `_transcribe_chunks`; legacy mic
segments keep `device_id=None`; detach stops + unregisters;
`POST /api/meeting/start` passes `devices` to `on_start`;
unknown id → 404 with the id in the body; legacy no-body
call still works). 319/319 green on the full sweep.

Pickup: HS-14-07 (server → device status push) is next;
HS-14-08 closes the phase.

**HS-14-07 (2026-05-07):** Server → device status push and
device → server events. New module
`holdspeak/device_status.py:DeviceStatusEmitter` — thread-safe
registry of per-device sender callables with optional
``{label}`` substitution against the `DeviceRegistry`.
`device_audio_ws._serve_device_audio` runs an async writer
task per connection; status sends from any thread go through
``loop.call_soon_threadsafe`` onto an asyncio queue and out
as ``{type: "status", text, ttl_ms}`` JSON frames.
Disconnect cleanup unregisters the emitter, drains the queue,
and cancels the writer.

Inbound ``{type: "event", name, at}`` frames dispatch through
a new ``EventHandler`` callback. ``MeetingWebServer`` forwards
both via `device_status_emitter` + `on_device_event`
constructor kwargs (with a default in-process emitter so
existing tests keep working). `run_web_runtime` creates the
shared emitter, threads it into the server, and emits at the
canonical sites: ``Listening...`` on device voice-start,
``Thinking...`` + transcript snippet on stop (the
transcript-complete callback piggybacks on
``_transcribe_and_type``'s new ``on_complete`` hook),
``Recording 00:00`` on meeting start (broadcast to attached
devices), ``Bookmark @ 47s`` on bookmark, ``Saving meeting...``
on stop. Inbound ``long_press`` on an attached device fires
``MeetingSession.add_bookmark`` and broadcasts the bookmark
status back.

Test coverage: 8 unit cases on `DeviceStatusEmitter`
(send-without-registered / register+send / unregister drops
sender / send swallows raises / broadcast counts / label
substitution / fallback to device_id / `active_device_ids`)
plus 7 integration cases covering outbound (handshake →
emitter.send → device receives the JSON; label + ttl
round-trip; full Listening → Thinking → snippet sequence
through the WS) and inbound events (dispatch with `at`,
without `at`, and event-without-name ignored), plus
disconnect-unregisters. 334/334 green on the full sweep.

Manual hardware verification (acceptance bullet 5) is
deferred to HS-14-08's DoD pass — recorded in the story file.

Pickup: HS-14-08 closes the phase (DoD + protocol docs +
cross-network deferral note).

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
