# iPad companion

The iPad app is a client of the HoldSpeak runtime. It is not a second hub. The runtime on your computer stays the owner of records and receipts.

The app connects to the runtime over your own network (LAN or Tailscale) with a base URL and an optional Bearer token. There is no hosted relay. The app is built from source. It has no App Store release.

## What you can do

| Task | Runtime route |
|---|---|
| Dictate a note | `POST /api/dictation/remote` |
| List, start, and stop meetings | `GET /api/meetings`, `POST /api/meeting/start`, `POST /api/meeting/stop` |
| Import a recording or transcript | `POST /api/meetings/import` (multipart) |
| Review and decide meeting proposals | `GET /api/meetings/{meeting_id}/proposals`, `POST /api/meetings/{meeting_id}/proposals/{proposal_id}/decision` |
| See and select coding sessions | `GET /api/coders/status`, `POST /api/coders/select`, `POST /api/coders/dismiss`, `POST /api/coders/pin`, `GET /api/coders/sessions` |
| Reply to or steer a coding session | `POST /api/coders/{key}/steer`, `arm`, `disarm`, `keys`, `kill`, and `GET /api/coders/{key}/peek` |
| Review activity nudges and the briefing | `GET /api/activity/nudges`, `POST /api/activity/nudges/select`, `POST /api/activity/nudges/{nudge_id}/dismiss`, `GET /api/activity/briefing` |
| Run saved recipes and chains | `POST /api/recipes/{recipe_id}/run`, `POST /api/chains/{chain_id}/run` |

The client is `HTTPDesktopClient` in `apple/Sources/Providers/Desktop/`. A response that is not 2xx raises a typed HTTP error. A payload that does not parse is reported as malformed.

## Dictation

`VoiceNoteComposer` (`apple/Sources/RuntimeCore/Companion/VoiceNoteComposer.swift`) runs this sequence:

1. Record audio on the device.
2. Transcribe on the device.
3. Show the text. You can edit it.
4. Send the reviewed text to the runtime.

Your Send action is the approval. The app sends text, not audio. Each request has a stable ID. If the app retries, the runtime returns the first receipt. The runtime refuses a different payload under the same ID.

## Meetings and proposals

The app captures meetings, reads transcripts and artifacts, and imports local files. An import enters the same pipeline as any other meeting.

A decision on a proposal does not run the action. The runtime applies its own policy to the action.

## Mesh serving

In **Settings**, **Serve my models to the mesh** is off by default. When on, the app takes signed work from the runtime and runs it with the model on the device. The model and its key stay on the device. The app serves only while it is open.

## Build

See `apple/README.md` for the build, tests, and the device scripts. The Swift package needs macOS 14 or iOS 17 and Swift tools 6.0. To install on a device, run `apple/scripts/meeting-capture-device.sh`.

## See also

- `apple/ARCHITECTURE.md`
- [Architecture](ARCHITECTURE.md)
