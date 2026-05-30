# HoldSpeak Device Protocol

**Status:** phase-14 substrate. LAN-only. Cross-network reach
(TLS, tunnels, public URL) is the subject of phase 15.

This document specifies the WebSocket protocol that lets an
external device — the AIPI-Lite ESP32-S3 robot, or any
compatible client — feed audio into HoldSpeak's voice-typing
and meeting paths. The on-host implementation lives in
`holdspeak/device_audio.py`, `holdspeak/device_audio_ws.py`,
`holdspeak/device_status.py`, `holdspeak/voice_typing.py`,
and the route registration in `holdspeak/web_server.py`. See
those modules for the source of truth.

## 1. Endpoint

```
ws://<host>:<port>/api/devices/audio
```

The web runtime (`holdspeak web`, or just `holdspeak`) binds
to `127.0.0.1`. Cross-network reach is phase 15; for now an
AIPI-Lite-side bridge running on the same LAN as HoldSpeak
forwards device audio over this loopback WebSocket.

## 2. Handshake (first frame)

The device opens the WebSocket and sends exactly one JSON
text frame as its first message:

```json
{
  "type": "hello",
  "device_id": "aipi-1",
  "label": "Karol",
  "psk": "<the configured device PSK>",
  "version": 1
}
```

Field rules (Pydantic v2, `extra="forbid"`,
`str_strip_whitespace=True`):

| field | type | required | rules |
|---|---|---|---|
| `type` | `"hello"` | yes | exact literal |
| `device_id` | str | yes | non-empty after strip; unique per active device |
| `label` | str | yes | non-empty after strip; speaker label on transcripts |
| `psk` | str | yes | non-empty after strip; compared with the configured PSK via `hmac.compare_digest` |
| `version` | int | yes | currently `1`; future revisions may bump this |

**Auth:** the PSK is generated lazily on first run and stored
in `~/.config/holdspeak/config.json` under `device.psk`.
View / rotate from the CLI:

```
$ holdspeak device-psk show
$ holdspeak device-psk rotate
```

`hmac.compare_digest` is the comparison primitive. An empty
PSK on either side is treated as a mismatch (so a freshly-
installed instance with no PSK on disk cannot be
authenticated by sending an empty string).

**Server response (success):** the server replies with a JSON
text frame:

```json
{"type": "hello-ack", "device_id": "aipi-1", "label": "Karol"}
```

After the ack, the device may send control + binary audio
frames (§3, §4).

**Server response (failure):** the server closes the
WebSocket with an application close code (§5). No reply
frame is sent before the close.

## 3. Control frames (text JSON)

After the handshake, every text frame is a control message.
Frames the server understands:

### 3.1 `start`

```json
{"type": "start"}
```

Begins a recording session. Behavior depends on context:
- **No meeting active:** the device claims a voice-typing
  session via the shared `VoiceTypingSession`. If another
  owner already holds the session, the server replies with
  `{type: "error", code: "session_busy", reason: "..."}`.
- **Meeting active and this device is attached
  (`POST /api/meeting/start {devices:[id]}`):** the
  recorder is already running for the meeting; the start
  frame is acknowledged with no side effect.
- **Meeting active and this device is NOT attached:**
  same `session_busy` reply.

### 3.2 `stop`

```json
{"type": "stop"}
```

Ends the voice-typing recording. The server transcribes the
buffered audio, types it via the local `TextTyper` (or
clipboard fallback), and pushes status to the device's LCD
(§6). For a meeting-attached device this frame is a no-op
(the meeting owns the recorder lifecycle).

### 3.3 `heartbeat`

```json
{"type": "heartbeat"}
```

Refreshes the device's `last_seen` in the registry. The
runtime exposes it via `/api/runtime/status` once that
surface lands. No reply.

### 3.4 `event` (device → server)

```json
{"type": "event", "name": "long_press", "at": 47.5}
```

Reports a device-side gesture. `at` is a numeric
device-side timestamp anchor (any int / float, optional —
defaults to `null` server-side).

Currently honored:
- `long_press` during an active meeting where the device is
  attached: fires `MeetingSession.add_bookmark(...)` with
  auto-labeling, then broadcasts a `Bookmark @ Xs` status
  to every attached device.

Other names are accepted, logged, and ignored (the protocol
ferries them but only `long_press` has a binding in v1).
Frames missing `name` are dropped with a warning log.

### 3.5 `device_health`

```json
{"type": "device_health", "battery_pct": 84, "rssi_dbm": -57, "at": 1234}
```

Reports the device's last-known battery and WiFi health.
The server stores the latest valid value in the in-memory
device registry and projects the same values onto active
meeting device descriptors when the device is attached.

| field | type | required | rules |
|---|---|---|---|
| `type` | `"device_health"` | yes | exact literal |
| `battery_pct` | int | yes | `0..100`; invalid values are dropped, not clamped |
| `rssi_dbm` | int | yes | `-120..0`; invalid values are dropped, not clamped |
| `at` | int | yes | device-side timestamp |

The WebSocket stays open when a health frame is malformed;
HoldSpeak logs and drops only that frame. Current values are
available from:

```text
GET /api/devices/health
```

Each device object includes `battery_pct`, `rssi_dbm`, and
`last_health_at` when the device has sent a health frame.

### 3.6 `query`

```json
{"type": "query", "name": "last_segment", "at": 1235}
```

Requests server state for display on the device. Supported query
names:

| name | response |
|---|---|
| `last_segment` | most recent finalized active-meeting segment from this device, as a regular `status` frame with `ttl_ms: 5000` |
| `agent_status` | most recent Claude/Codex hook-captured agent question, prefixed with agent/project context, as a regular `status` frame with `ttl_ms: 7000`; returns `No agent waiting` when none is fresh |
| `agent_question` | most recent Claude/Codex hook-captured agent question without the status prefix, as a regular `status` frame with `ttl_ms: 7000`; returns `No agent waiting` when none is fresh |

If there is no active meeting segment from this device, the
server replies:

```json
{"type": "status", "text": "No transcript yet", "ttl_ms": 5000}
```

Unknown names receive a visible status response from the web
runtime:

```json
{"type": "status", "text": "Unknown query: current_topic", "ttl_ms": 3000}
```

Malformed query frames are logged and dropped; the WebSocket
stays open.

### 3.7 Unknown control types

Logged and dropped. The server does **not** close the
connection; a misbehaving client doesn't kill its own audio
session.

## 4. Audio frames (binary)

After `start`, the device pushes raw PCM as binary
WebSocket frames. The wire format is fixed:

- 16 kHz mono, int16 little-endian.
- No header / framing — each frame's bytes are appended to
  the recorder's pushed-audio buffer.
- Odd trailing bytes (incomplete sample) are dropped.
- Frames pushed before `start` or after `stop` are silently
  dropped (the WebSocket may race the device's stop signal
  and we don't want to close the connection over a tail
  frame).

A non-default wire rate (e.g. 8 kHz) is supported defensively:
`RemoteAudioRecorder(wire_sample_rate=8_000)` resamples on
the way out. The bridge is expected to do rate-matching on
its side, so the resample path stays a safety net.

**Backpressure:** each device has a bounded internal ring
of pushed frames (default 2 s of audio @ 16 k mono = 64 KB).
On overflow, the **oldest** frame is dropped and a single
structured warning is logged per overflow burst:

```
holdspeak.audio.remote WARNING device.queue.overflow
    device_id=aipi-1
    dropped_samples=...
    dropped_bytes=...
    cap_samples=...
    buffered_samples=...
    max_buffer_seconds=2.0
    wire_sample_rate=16000
```

## 5. Close codes

The server uses application close codes from the 4xxx range
on handshake-time failures:

| code | meaning |
|---|---|
| 4001 | Invalid handshake — payload missing fields, malformed JSON, unknown extra fields, or wrong `type` literal |
| 4003 | PSK mismatch — the device's PSK didn't match the configured value |
| 4009 | Duplicate label — another active device is already using this label |

Constants live at `holdspeak/device_audio.py:`
`WS_CLOSE_INVALID_HANDSHAKE`, `WS_CLOSE_PSK_MISMATCH`,
`WS_CLOSE_DUPLICATE_LABEL`. Typed exceptions
(`InvalidHandshakeError`, `PskMismatchError`,
`DuplicateLabelError`) carry the close code as a class
attribute so the route does
`await ws.close(code=exc.code)` without re-deriving the
policy.

Routine WebSocket close (1000) on either side simply tears
the connection down; the server unregisters the device from
the registry and cancels any in-flight voice-typing
session. Audio buffered between the last drain and the
disconnect is discarded.

## 6. Server → device status messages

The server pushes status updates onto the same WebSocket so
the device can show them on its LCD:

```json
{"type": "status", "text": "Listening...", "ttl_ms": 0}
```

| field | type | meaning |
|---|---|---|
| `type` | `"status"` | exact literal |
| `text` | str | the message; `{label}` is substituted with the device's registered label |
| `ttl_ms` | int | display TTL in milliseconds; `0` means "until the next status" |

### 6.1 Voice-typing turn

| trigger | text | ttl_ms |
|---|---|---|
| `start` accepted, voice session begun | *(no pushback — TX arrow glyph in firmware top-right indicates recording)* | — |
| `stop` produced ≥ 0.1 s of audio, transcription kicked off | *(no pushback — absence of TX arrow signals processing)* | — |
| Transcription completed | `<first 150 chars of transcript>` | 4000 |

AIPI-4-13 (2026-05): `Listening...` and `Thinking...` pushbacks were
removed because they clobbered the bottom widget's persistent
meeting/idle text. The device's firmware-side TX label glyph (top-right
`↑` during right-button hold) now carries that state signal instead.

Note: the transcript snippet fires *outside* the local-typing
try-block, so the device sees the snippet even if local
typing failed (e.g., Wayland blocked synthetic typing).

### 6.2 Meeting

| trigger | text | ttl_ms |
|---|---|---|
| Meeting starts with this device attached | `Recording 00:00` | 0 |
| **Periodic tick during meeting (HS-17-05, currently every 1 s)** | `Recording MM:SS` | 0 |
| **Finalized transcript segment (HS-17-08 / HS-17-13)** | `<speaker>: <text>` (bounded to the server LCD payload ceiling) | 3000 |
| Bookmark added (web button or `long_press` event) | `Bookmark @ <seconds>s` | 2500 |
| Meeting stop initiated | `Saving meeting...` | 0 |

The periodic Recording-tick (HS-17-05, 2026-05-10) fires every
1 second while a meeting has at least one attached device. Format
`Recording MM:SS`, sticky (`ttl_ms: 0`) so it overwrites the previous
sticky activity until the next tick. The ticker stops cleanly on
meeting stop (the `Saving meeting...` frame is the last status seen
by the device). Cap: MM clamps to `99` at 100+ minute meetings —
cosmetic concession to LCD width.

Transcript pushback filters the clearest Whisper silence/noise
hallucinations before painting the device LCD (`...`, all-punctuation
strings, repeated single-word artifacts, and known short phrases such
as `thanks for watching`). The durable meeting transcript is not
filtered by this display-only rule.

### 6.3 Errors during a session

```json
{"type": "error", "code": "session_busy", "reason": "another voice-typing session is already active"}
```

Currently the only `error` code is `session_busy` (§3.1).
The connection is **not** closed on this error — the device
can wait and retry on the next button press.

## 7. End-to-end example

A device-driven voice-typing turn from handshake to
typed-text-on-host:

```
device → server  {"type":"hello","device_id":"aipi-1","label":"Karol",
                  "psk":"<psk>","version":1}
server → device  {"type":"hello-ack","device_id":"aipi-1","label":"Karol"}

device → server  {"type":"start"}
server → device  {"type":"status","text":"Listening...","ttl_ms":0}

device → server  <16 ms of int16 LE PCM bytes>
device → server  <16 ms of int16 LE PCM bytes>
device → server  <16 ms of int16 LE PCM bytes>
... (more PCM frames as the user holds the button)

device → server  {"type":"stop"}
server → device  {"type":"status","text":"Thinking...","ttl_ms":0}

(server runs Whisper, applies text_processor punctuation,
 types via TextTyper)

server → device  {"type":"status","text":"Hello world.","ttl_ms":4000}

(connection stays open; idle until the next start)
```

A meeting flow with one attached device + a long-press
bookmark:

```
(device already connected via the handshake above; meeting
 owner POSTs /api/meeting/start {"devices":["aipi-1"]} via
 a separate HTTP call)

server → device  {"type":"status","text":"Recording 00:00","ttl_ms":0}

device → server  <PCM frames continuously while attendee speaks>

device → server  {"type":"event","name":"long_press","at":47.5}
server → device  {"type":"status","text":"Bookmark @ 47s","ttl_ms":2500}

(meeting owner clicks Stop on the web dashboard)
server → device  {"type":"status","text":"Saving meeting...","ttl_ms":0}
```

## 8. What phase 15 will need to revisit

- **TLS termination point.** Phase 14 is plain `ws://` on
  loopback. Phase 15's tunnel layer (Tailscale / Cloudflare
  Tunnel / WireGuard) terminates TLS somewhere; the
  WebSocket route may need to read forwarded headers to
  preserve client-IP for audit logging.
- **PSK rotation under reconnect.** Today rotation takes
  effect on the *next* connection because `get_psk` is
  called per handshake. Cross-network reconnects may take
  longer to drain old sessions — sharing PSKs across many
  devices on different networks needs revocation, not just
  rotation.
- **Per-device PSKs.** Phase 14 uses a single shared secret.
  Phase 15+ should issue per-device PSKs once HoldSpeak
  ships to a second install or the user wants to revoke a
  single device.
- **Tunnel-vs-direct addressing.** The bridge currently
  speaks to `127.0.0.1`. Cross-network deployments need a
  resolution layer (mDNS for LAN, tunnel hostname for WAN).
- **Per-device labels persisting across networks.** The
  registry is in-memory; devices re-register on reconnect.
  If the user's labels diverge across home / office /
  coffee-shop networks, the server-side label registry will
  need to persist (currently each reconnect is a clean
  slate).
