# Device Protocol

This page defines the WebSocket protocol between a device and the HoldSpeak runtime. The AIPI-Lite bridge uses it. Any compatible client can use it.

The source is in `holdspeak/device_audio.py`, `holdspeak/device_audio_ws.py`, `holdspeak/device_status.py`, and `holdspeak/runtime/device_glue.py`. The source is the final authority.

The runtime binds to `127.0.0.1` by default. The client must run on the same machine, or reach the runtime through a tunnel that you set up.

## 1. Endpoint

```
ws://<host>:<port>/api/devices/audio
```

This route has no Bearer token. The PSK in the handshake authenticates the device.

## 2. Handshake

The client sends one JSON text frame first:

```json
{"type": "hello", "device_id": "aipi-1", "label": "Karol", "psk": "<PSK>", "version": 1}
```

| Field | Type | Rules |
|---|---|---|
| `type` | `"hello"` | Exact value. |
| `device_id` | string | Not empty. Unique for each active device. |
| `label` | string | Not empty. HoldSpeak uses it as the speaker label in transcripts. |
| `psk` | string | Not empty. Compared with the configured PSK in constant time. |
| `version` | integer | Currently `1`. |

The runtime rejects unknown fields. It trims whitespace in strings. An empty PSK never matches.

The runtime creates the PSK on first use. It stores the PSK in the config file under `device.psk`. Manage it with:

```
holdspeak device-psk show
holdspeak device-psk rotate
```

A rotation applies to the next connection.

On success, the runtime replies:

```json
{"type": "hello-ack", "device_id": "aipi-1", "label": "Karol"}
```

On failure, the runtime closes the socket with a close code. It sends no reply frame.

| Code | Meaning |
|---|---|
| 4001 | The handshake is not valid. A field is missing, the JSON is malformed, a field is unknown, or `type` is wrong. |
| 4003 | The PSK does not match. |
| 4009 | Another active device uses this label. |

The constants are `WS_CLOSE_INVALID_HANDSHAKE`, `WS_CLOSE_PSK_MISMATCH`, and `WS_CLOSE_DUPLICATE_LABEL` in `holdspeak/device_audio.py`.

When the socket closes, the runtime removes the device and cancels its voice-typing session. It discards audio that it did not process.

## 3. Control frames (client to runtime)

After the handshake, every text frame is a JSON control frame. The runtime logs and drops an unknown or malformed frame. It does not close the socket.

### `start`

```json
{"type": "start"}
```

Starts a recording.

- No meeting is active: the device takes the voice-typing session. If another owner holds it, the runtime replies with a `session_busy` error. If a waiting coding session cannot receive text, the runtime sends the status `No reply target` and the same error.
- A meeting is active and the device is attached: the recorder already runs. The runtime does nothing.
- A meeting is active and the device is not attached: the runtime replies with `session_busy`.

Attach a device to a meeting with `POST /api/meeting/start` and `{"devices": ["<device_id>"]}`.

### `stop`

```json
{"type": "stop"}
```

Ends the voice-typing recording. The runtime transcribes the audio and types the text on the host. If typing is not possible, the runtime uses the clipboard. For an attached device, `stop` does nothing. The meeting controls the recorder.

### `heartbeat`

```json
{"type": "heartbeat"}
```

Refreshes the last-seen time of the device. The runtime sends no reply.

### `event`

```json
{"type": "event", "name": "long_press", "at": 47.5}
```

Reports a device gesture. `at` is an optional device timestamp. Two names have an action, and only during a meeting with the device attached. `long_press` adds a bookmark and sends `Bookmark @ <seconds>s` to every attached device. `double_left_click` sends the next meeting-statistics view to this device. The runtime ignores other names.

### `device_health`

```json
{"type": "device_health", "battery_pct": 84, "rssi_dbm": -57, "at": 1234}
```

| Field | Type | Rules |
|---|---|---|
| `battery_pct` | integer | 0 to 100. |
| `rssi_dbm` | integer | -120 to 0. |
| `at` | integer | Device timestamp. |

The runtime drops a frame with a value out of range. It keeps the socket open. Read the latest values with `GET /api/devices/health`. Each device object has `battery_pct`, `rssi_dbm`, and `last_health_at`.

### `query`

```json
{"type": "query", "name": "last_segment", "at": 1235}
```

The runtime answers with a `status` frame.

| Name | Answer | `ttl_ms` |
|---|---|---|
| `last_segment` | The last final meeting segment from this device. If none exists, `No transcript yet`. | 5000 |
| `agent_status` | The question a Claude or Codex session waits on, with the agent and project. If none is fresh, `No agent waiting` (`ttl_ms` 3000). | 7000 |
| `agent_question` | The same question without the prefix. If none is fresh, `No agent waiting`. | 7000 |
| `agent_next` | Like `agent_status`, for the next waiting session. | 7000 |

An unknown name gets `Unknown query: <name>` with `ttl_ms` 3000.

## 4. Audio frames (binary)

After `start`, the client sends raw PCM as binary frames.

- Format: 16 kHz, mono, signed 16-bit little-endian.
- No header. The runtime appends each frame to the recording.
- The runtime drops a trailing odd byte.
- The runtime drops frames that arrive before `start` or after `stop`.

The runtime can resample a different wire rate. The bridge must send 16 kHz.

Each device has a buffer of 2 seconds of audio. When the buffer is full, the runtime drops the oldest frames. It logs one `device.queue.overflow` warning for each burst.

## 5. Status frames (runtime to device)

```json
{"type": "status", "text": "Recording 00:42", "ttl_ms": 0}
```

| Field | Meaning |
|---|---|
| `text` | The text for the LCD. The runtime replaces `{label}` with the device label. The runtime limits the length to 150 characters. |
| `ttl_ms` | Display time in milliseconds. `0` means until the next status. |

### Voice typing

| Event | Text | `ttl_ms` |
|---|---|---|
| `start` accepted | No status. The firmware shows its own recording symbol. | - |
| `stop` with at least 0.1 s of audio | No status. | - |
| Transcription done | The first 150 characters of the transcript. | 4000 |

The runtime sends the transcript text even when typing on the host fails.

### Meeting

| Event | Text | `ttl_ms` |
|---|---|---|
| Meeting starts with the device attached | `Recording 00:00` | 0 |
| Every second | `Recording MM:SS` | 0 |
| Final transcript segment | `<speaker>: <text>` | 3000 |
| Bookmark added | `Bookmark @ <seconds>s` | 2500 |
| Meeting stop begins | `Saving meeting...` | 0 |

`MM` stops at 99. The runtime does not show a segment on the LCD that is silence or noise from the transcriber, such as `...` or `thanks for watching`. The saved transcript keeps those segments.

### Errors

```json
{"type": "error", "code": "session_busy", "reason": "another voice-typing session is already active"}
```

`session_busy` is the only error code. The socket stays open. The device can try again.

## 6. Example

```
device -> runtime  {"type":"hello","device_id":"aipi-1","label":"Karol","psk":"<PSK>","version":1}
runtime -> device  {"type":"hello-ack","device_id":"aipi-1","label":"Karol"}
device -> runtime  {"type":"start"}
device -> runtime  <binary PCM frames>
device -> runtime  {"type":"stop"}
runtime -> device  {"type":"status","text":"Hello world.","ttl_ms":4000}
```

## See also

- [AIPI-Lite companion](AIPI_LITE.md)
- [AIPI-Lite Developer Workflow](AIPI_LITE_DEV_WORKFLOW.md)
- [Security & Privacy](SECURITY.md)
