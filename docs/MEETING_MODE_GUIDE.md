# Meeting Mode guide

Meeting Mode captures a meeting, saves a transcript when a speech model is
available, and lets you run intelligence and follow-through from the saved
record. Capture, model work, and outbound actions are separate. A meeting can
be useful even when transcription or intelligence is unavailable.

## Contents

1. [Quick start](#quick-start)
2. [Set up system audio](#set-up-system-audio)
3. [Record a meeting](#record-a-meeting)
4. [After the meeting](#after-the-meeting)
5. [Import a recording or transcript](#import-a-recording-or-transcript)
6. [Find meetings](#find-meetings)
7. [Where your transcript goes](#where-your-transcript-goes)
8. [Intent routing](#intent-routing)
9. [Settings](#settings)
10. [HTTP API](#http-api)
11. [Troubleshooting](#troubleshooting)

## Quick start

Start the hub, then open **Meetings** and select **Record meeting**.

```console
holdspeak meeting --setup
holdspeak
```

1. Open the **Record** wing.
2. Select **Start meeting**.
3. Set the title and tags in **Meeting details**.
4. Add a bookmark when you need to find a moment again.
5. Select **Stop meeting**.

The browser uses `POST /api/meeting/start` and `POST /api/meeting/stop`.
The hub creates the meeting before audio arrives. A capture interruption leaves
the saved checkpoint and a recovery state. It does not claim a complete meeting.

## Set up system audio

The recorder has a microphone stream and a system-audio stream. The system
stream contains remote participants when the operating system exposes a monitor
device.

- On macOS, use BlackHole 2ch in a Multi-Output Device.
- On Linux, use a PulseAudio or PipeWire monitor source.
- Use headphones to reduce microphone echo.

### macOS Multi-Output Device

1. Open **Audio MIDI Setup**.
2. Create a Multi-Output Device with your speakers or headphones and
   **BlackHole 2ch**.
3. Set the new device as the system sound output.

### Check the setup

```console
holdspeak meeting --setup
holdspeak meeting --list-devices
```

Set `meeting.mic_device` or `meeting.system_audio_device` when automatic device
selection is not correct. If the system stream is unavailable, the recorder can
continue with the microphone and reports the reduced capture state.

## Record a meeting

The live face shows the capture state and the current egress information.
HoldSpeak does not run meeting intelligence while audio is being captured.

1. Select **Start meeting**.
2. Speak and let the recorder collect the microphone and system streams.
3. Add a bookmark with a short name when a moment matters.
4. Select **Stop meeting** and wait for the terminal capture state.

When the local Whisper backend is available, HoldSpeak transcribes audio in the
hub. A missing local speech backend does not make a summary. It leaves the saved
audio checkpoint available for recovery, subject to capture retention rules.

The terminal recorder is a smaller path:

### Terminal recorder

```console
holdspeak meeting
```

Use the browser path when you need review, intelligence, aftercare, or the
meeting API. The WebSocket `/ws` carries live segments, bookmarks, status, and
completion events to the face.

## After the meeting

Open the saved meeting in **Meetings**. The **Outcomes**, **Review**, **Record**,
and **Artifacts** wings read the same saved meeting and service state.

### Summary

Select **Run summary** when a route is available. The route is chosen from the
model assignments, not from the legacy `meeting.intel_provider` value. The host
chip and the terminal receipt identify the selected host. A remote endpoint,
CLI engine, or mesh node is an egress boundary for transcript text.

The summary can be queued. Use **Retry** or **Skip** on recovery state. The CLI
queue commands are:

```console
holdspeak intel
holdspeak intel --process
holdspeak intel --retry MEETING_ID
```

### Review proposals

Intelligence can create proposed decisions, action items, and typed artifacts.
Review the proposal and its transcript evidence before you keep it.

- **Confirm** keeps the proposal.
- **Edit** changes its text or action-item owner and due date.
- **Dismiss** rejects it.
- **Open evidence** moves to the source segment.

**Accept reviewed** confirms all eligible proposals. This review step is about
the saved record. It is not a universal approval gate for later sends or tools.

### Decide

Use **Decide** to save a decision linked to the meeting and its Project. The
decision is a Desk record and remains available to later Threads and agents.

### Send

Aftercare can prepare **Summary**, **Digest**, or **Follow-up** documents. The
document preview names the destination. Sending uses the channel operation
policy: **YOLO** is the default control mode for eligible fixed destinations,
while hard invariants, destination binding, and receipts always apply. **Secure**
and **Normal** can require a review or a scoped grant.

The send route does not prove delivery until its terminal receipt says so. A
GitHub issue request is a separate proposal at
`POST /api/meetings/{meeting_id}/aftercare/file-issue`.

### Read the transcript

The **TRANSCRIPT** section shows segments, time, speaker, and evidence links.
Speaker labels are capture metadata. HoldSpeak does not infer a person's
identity merely because a label resembles a People record.

### Artifacts

The **Artifacts** wing lists typed results from the intent router and plugin
runs. See [Meeting intelligence](MEETING_INTELLIGENCE.md).

### Export

`GET /api/meetings/{meeting_id}/export?format=markdown` or `json` downloads a
local export. It includes the transcript, summary, review state, timestamps, and
artifacts. Export does not publish the file.

### Park a meeting

Select **Park** to hide a meeting without deleting it. Restore it from the
parked strip or with the meeting restore route.

## Import a recording or transcript

The browser and CLI import paths create a normal meeting record:

```console
holdspeak import path/to/meeting.wav --title "Q3 kickoff" --tag imported
holdspeak import path/to/meeting.vtt --tag imported
```

`.wav` works directly. Other audio formats need `ffmpeg`. `.vtt`, `.srt`, and
`.txt` imports do not transcribe. A recording receives one speaker label unless
the input is a transcript with speaker data. HoldSpeak does not retain the
source audio file after import.

An empty or unreadable import is refused. Summary scheduling still depends on
the configured intelligence setting and an assigned route.

## Find meetings

The Meetings list and `GET /api/meetings` search transcript text. Use `search`,
`date_from`, `date_to`, `speaker`, `tag`, and `has_open_actions`. Filters
apply on the server, so they are not limited to the visible page.

## Where your transcript goes

Meeting rows, segments, bookmarks, summaries, proposals, and receipts are
stored in the main SQLite database. Capture checkpoints use the meeting capture
journal. People content uses its separate encrypted store.

Speech transcription uses the local Whisper backend. Summary and assigned
plugins can send transcript text to their model hosts.

Meeting model work uses the assigned route for each capability. Check the primary and fallback hosts in **HoldSpeak > Engines**. The retained `meeting.intel_provider` value is a legacy migration input. It does not select a current route or prevent egress.

- Add and assign models in **HoldSpeak > Engines**. See [Models](MODELS.md).
- Engines shows where each job runs before you pick its engine; the Meetings window does not repeat the host on its rows (owner ruling 2026-10-25). A hover title on **Run summary** names the host. The receipt shows the hosts that HoldSpeak contacted.
- `holdspeak doctor` checks the meeting settings.
- If a summary cannot run, HoldSpeak queues it and retries with a growing delay.
  Tune it with `meeting.intel_retry_base_seconds`, `meeting.intel_retry_max_seconds`, and `meeting.intel_retry_max_attempts`.
- To check the queue, run `holdspeak intel`. Use `--process` to run queued jobs now and `--retry MEETING_ID` to requeue one.

See [Security](SECURITY.md) for what HoldSpeak stores.

## Intent routing

The intent router scores saved transcript text against the configured intents.
It can select several plugins. The `balanced`, `architect`, `delivery`,
`product`, and `incident` options are routing presets, not model identities.

Use **Preview route** or the CLI dry run to inspect routing without writing the
meeting:

```console
holdspeak intel --route-dry-run MEETING_ID --profile architect
holdspeak intel --reroute MEETING_ID --profile incident --override-intents incident,comms
```

The reroute saves a named reroute window. A plugin without an assignment is
skipped and the reason is recorded.

## Settings

Use **Settings ▸ Meetings** for supported changes. The active configuration file is
`~/.config/holdspeak/config.json`.
[Configuration reference](CONFIGURATION_REFERENCE.md) lists every key. These `meeting` keys matter most:

| Key | Default | Purpose |
| --- | --- | --- |
| `mic_device` | `null` | Microphone name. `null` uses the system default. |
| `system_audio_device` | `null` | System audio device, for example `BlackHole 2ch`. `null` finds it. |
| `mic_label`, `remote_label` | `Me`, `Remote` | Speaker labels for the two streams. |
| `auto_export` | `false` | Terminal recorder only: save the transcript when the meeting ends. |
| `export_format` | `markdown` | `txt`, `markdown`, or `json` for the terminal recorder. |
| `intel_enabled` | `true` | Allows summaries. |
| `intelligence_auto` | `every` | When to run the summary by itself: `every`, `room_linked`, or `off`. |
| `intel_provider` | `local` | Legacy migration input. Use the model assignments to select current routes. |
| `intel_realtime_model` | local starter model | Path to a GGUF model for local runs. |
| `intel_summary_model` | `null` | Larger local model for the summary. `null` uses the main one. |
| `intel_deferred_enabled` | `true` | Queue the summary when no model is ready. |
| `routing_profile` | `balanced` | Intent routing preset. |
| `intent_router_enabled` | `false` | Intent router switch. `holdspeak doctor` reports it. |
| `disabled_plugins` | `[]` | Plugin ids to skip. |
| `allow_actuators`, `allowed_actuators` | `true`, `["*"]` | Master switch and allow list for actions that leave HoldSpeak. |
| `webhook_allowed_hosts` | `["*"]` | Hosts a webhook action can reach. |
| `diarization_enabled` | `false` | Label speakers in system audio. |
| `diarize_mic` | `false` | Label speakers in the microphone stream. |
| `similarity_threshold` | `0.75` | Speaker match threshold, `0.0` to `1.0`. |
| `auto_record` | `off` | Record calendar events that have a meeting link: `off`, `all_calendar`, or `room_linked`. |

The old `intel_cloud_*` keys are read once for migration. Do not use them. Assign models in **HoldSpeak > Engines**.

## HTTP API

The hub exposes these meeting surfaces. Authentication and route rights still
apply.

| Route | Purpose |
| --- | --- |
| `POST /api/meeting/start`, `POST /api/meeting/stop` | Start and stop live capture. |
| `PATCH /api/meeting`, `POST /api/bookmark` | Update details and add a bookmark. |
| `GET /api/meetings`, `GET /api/meetings/{id}` | List and read meetings. |
| `POST /api/meetings/import`, `POST /api/meetings/{id}/transcribe` | Import or transcribe. |
| `POST /api/meetings/{id}/intelligence/run` | Queue intelligence. |
| `GET /api/meetings/{id}/intel-recovery` | Inspect recovery; `/retry` and `/skip` act on it. |
| `GET /api/meetings/{id}/aftercare` | Read deterministic digest data. |
| `GET /api/meetings/{id}/followup-draft` | Build a follow-up draft. |
| `GET /api/meetings/{id}/artifacts` | Read plugin artifacts. |
| `GET /api/meetings/{id}/export` | Download a local export. |
| `WS /ws` | Receive live meeting events. |

## Troubleshooting

| Problem | Action |
| --- | --- |
| BlackHole not found | Run `brew install blackhole-2ch`. Restart **Audio MIDI Setup**. Run `holdspeak meeting --list-devices`. |
| No remote audio | Check the monitor device and run `holdspeak meeting --setup`. |
| No **Run summary** | Read the **NO SUMMARY ROUTE** reason and assign a model route. |
| Summary is queued | Run `holdspeak intel --process` or inspect the recovery state. |
| Capture is recoverable | Stop the hub cleanly, inspect the capture state, then use `/capture/recover`. |
| Endpoint fails | Check its URL, credential, model name, and egress chip. |
| Transcript is poor | Check microphone permission and the assigned speech model. |
| Browser does not load | Run `holdspeak doctor` and check the local runtime URL. |
| The summary is slow | Use a smaller model or assign a smaller quantization to Meetings. |
| The summary fails on an endpoint | Read the error on the meeting. Check the host, key, model name, and `/v1` API prefix in **HoldSpeak > Engines**. |
| Memory use is high | Use a smaller quantization or assign a smaller model to Meetings. |

## See also

- [Meeting intelligence](MEETING_INTELLIGENCE.md)
- [Meeting aftercare](MEETING_AFTERCARE.md)
- [Meeting architecture](MEETING_ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Models](MODELS.md)
