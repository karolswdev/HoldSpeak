# Meeting Mode guide

Meeting Mode records your microphone and the audio of remote participants.
It transcribes the meeting on your machine. After the meeting, HoldSpeak makes a summary
and proposes decisions and action items. You review them and keep what is right.

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

```bash
brew install blackhole-2ch    # macOS only
holdspeak meeting --setup     # check system audio
holdspeak                     # start the web runtime
```

1. Open the **Meetings** window.
2. Open the **Record** wing and select **Record meeting**.
3. Select **Start meeting**.
4. Select **Stop meeting** when the meeting ends.

## Set up system audio

You need one source for remote audio. HoldSpeak always records your microphone.

- **macOS:** Install BlackHole 2ch. Then create a Multi-Output Device.
- **Linux:** HoldSpeak uses a PulseAudio or PipeWire monitor source. No install is needed.

### macOS Multi-Output Device

1. Open **Audio MIDI Setup**.
2. Select **+**, then **Create Multi-Output Device**.
3. Select your speakers or headphones and **BlackHole 2ch**.
4. Right-click the new device. Select **Use This Device For Sound Output**.

### Check the setup

```bash
holdspeak meeting --setup          # reports whether system audio is ready
holdspeak meeting --list-devices   # lists all audio devices
```

To select a device by name, set `meeting.system_audio_device` or `meeting.mic_device`.
With no name set, HoldSpeak finds the device by itself.

Use headphones. Speakers cause an echo in the microphone.

## Record a meeting

Start the web runtime:

```bash
holdspeak              # opens the browser
holdspeak web --no-open   # headless: no browser opens
```

The **Record meeting** button opens the live face. The same face is at `/live`.

1. Select **Start meeting**. Recording starts on the microphone and the system audio.
2. The transcript appears with speaker labels. Your microphone is labeled **Me**. Remote audio is labeled **Remote**.
3. Set the **Title** and **Tags** in **Meeting details**.
4. To mark a moment, add a bookmark. Type a name in **Name this moment**.
5. Select **Stop meeting**. HoldSpeak saves the meeting.

The meeting record exists before the first audio arrives. If HoldSpeak stops in the middle of a capture,
the meeting keeps its last saved audio. The meeting shows a **Capture** state that says what happened.

If no speech model is ready, HoldSpeak records the audio only. It does not make a transcript.

The live face has two more sections behind the gear (**Configure meeting**):

- **Intent routing**: See [Intent routing](#intent-routing).
- **Summary**: Shows the summary state and where the summary runs.

Live analysis is off during recording. HoldSpeak makes the summary after you stop.

### Terminal recorder

`holdspeak meeting` records in the terminal. Press Ctrl+C to stop and transcribe.
Use the web runtime for the full workflow.

## After the meeting

Open the meeting in the **Meetings** window. The **Meetings** window has four wings:
**Outcomes**, **Review**, **Record**, and **Artifacts**.

### Summary

The summary holds a short overview and a list of topics.

- By default, HoldSpeak runs the summary after each meeting that has a transcript and an assigned model.
  Set **Auto-run the summary** in **Settings** to change this. The key is `meeting.intelligence_auto`.
  Values: `every` (default), `room_linked`, and `off`.
- To run it yourself, select **Run summary** on the meeting.
- A host chip beside **Run summary** names where the text goes. A fallback shows as `+ FALLBACK <host>`.
- With no route, the chip says **NO SUMMARY ROUTE** and gives the reason. **Run summary** is then absent.
- If a run fails, select **Retry** or **Skip**.

When the summary finishes, HoldSpeak shows a **Meeting ready** card.
Select **Open proposals** on the card to go to the meeting.

### Review proposals

The summary job also proposes decisions and action items. The **TO REVIEW** count shows how many wait for you.
Select **Review** to open the **Review** wing.

Each proposal shows its source in the transcript and its state. For each proposal:

- **Confirm** keeps it.
- **Edit** changes the text. For an action item, you can add the owner and the due date.
- **Dismiss** rejects it.
- **Open evidence** scrolls the transcript to the source segment.

**Accept reviewed** confirms all proposals that are ready.

An owner is a name from the transcript, or one of two reserved names. `Me` is the speaker.
`Remote` is the counterpart. An unknown owner stays **Unknown** until you supply one.

### Decide

Select **Decide** on a meeting to record a decision. Type the title and select **Save**.
The decision links to the meeting and its Project.

### Send

When a meeting has a summary, a **Send** section appears. Use the **Document** control to choose
**Summary**, **Digest**, or **Follow-up**.

- **Summary** is the summary text.
- **Digest** lists the open items by owner, the decisions, and the change since the previous meeting.
- **Follow-up** is a plain draft: decisions, open items with owners, and the change since last time.

HoldSpeak builds a Digest and a Follow-up from your saved data on your machine. It uses no model for them.

Pick a destination and send. The destination, the control mode, and your approvals decide when the message leaves.
See [Execution destinations](EXECUTION_DESTINATIONS.md) and [Control modes](AUTHORITY.md).
For Slack, save a channel destination first. The old Slack webhook setting in `meeting.slack_webhook_url` has no effect.

A **Send** shows the exact message before it posts. A failed send is recorded on the meeting.

To file an accepted action item as a GitHub issue, use `POST /api/meetings/{meeting_id}/aftercare/file-issue`.
The call makes a proposal. It runs `gh issue create` with your own `gh` login.

### Read the transcript

The **TRANSCRIPT** section shows each segment with its time and speaker.
**Open evidence** and decision links scroll to the right segment.

### Artifacts

The **Artifacts** wing lists typed results from the intent router plugins: requirements, decisions,
risks, and more. See [Meeting intelligence](MEETING_INTELLIGENCE.md).

### Export

The footer of a selected meeting has an **MD** button. It downloads the meeting as Markdown.
The export route also gives `json`. A download holds the transcript, the summary,
action item review state, source timestamps, and artifacts. An export stays local.
It does not publish to any other system.

The terminal recorder can save a transcript by itself. Set `meeting.auto_export` to `true`
and set `meeting.export_format` to `txt`, `markdown`, or `json`.
The file goes to `~/Documents`.

### Park a meeting

Select **Park** in the footer to hide a meeting. HoldSpeak does not delete it. The **PARKED** strip lists parked meetings. Restore one from there.

## Import a recording or transcript

You can import a recording or a transcript file. The import becomes a normal meeting.

From the browser:

1. Open the **Meetings** window and the **Record** wing.
2. Drop the file in the drop area, or browse for it.
3. Optionally set **Title**, **Speaker**, and **Tags**.
4. Select **Import**.

From the shell:

```bash
holdspeak import path/to/recording.wav --title "Q3 kickoff" --speaker "Team call" --tag imported
holdspeak import path/to/meeting.vtt --tag imported
```

| Input | Formats | Notes |
| --- | --- | --- |
| Recording | `.wav` | Works without extra tools. |
| Recording | `.mp3`, `.m4a`, `.aac`, `.ogg`, `.opus`, `.flac`, `.webm`, `.mp4` | Needs `ffmpeg` on your PATH. Without it, the import fails with a message. |
| Transcript | `.vtt`, `.srt`, `.txt` | No transcription. A long meeting imports in seconds. |

Rules for imports:

- HoldSpeak transcribes a recording on your machine in windows of 30 seconds. It does not keep the audio file.
- A recording gets one speaker label. The default is **Recording**. HoldSpeak does not guess speakers.
- A transcript keeps the speaker names and times that the file has. WebVTT `<v Name>` tags and `Name:` prefixes become speaker labels.
  A file with no names gets one label. The default is **Transcript**. A `.txt` file has no times, so HoldSpeak spreads the segments evenly.
- A file with no readable content is refused. An import never makes an empty meeting.
- The meeting start time is the time of the import.
- An import does not run the summary. Select **Run summary** on the meeting.

## Find meetings

The **Meetings** list searches the full transcript text. Filters narrow the list on the server, so they cover
all meetings, not only the visible ones:

- **Date range**: from and to dates.
- **Speaker**: meetings where the speaker has segments.
- **Tag**: meetings with the tag.
- **HAS OPEN ACTIONS**: meetings that still have open action items.

Filters combine with each other and with the search text.

## Where your transcript goes

HoldSpeak transcribes on your machine. The summary and assigned plugins can send text to their model hosts.

Meeting model work uses the assigned route for each capability. Check the primary and fallback hosts in **Settings > Models**. The retained `meeting.intel_provider` value is a legacy migration input. It does not select a current route or prevent egress.

- Add and assign models in **Settings > Models**. See [Models](MODELS.md).
- The host chip beside **Run summary** shows the destination before you run. The receipt shows the hosts that HoldSpeak contacted.
- `holdspeak doctor` checks the meeting settings. The live face shows an egress chip: whether the text stays on this device.
- If a summary cannot run, HoldSpeak queues it and retries with a growing delay.
  Tune it with `meeting.intel_retry_base_seconds`, `meeting.intel_retry_max_seconds`, and `meeting.intel_retry_max_attempts`.
- To check the queue, run `holdspeak intel`. Use `--process` to run queued jobs now and `--retry MEETING_ID` to requeue one.

See [Security](SECURITY.md) for what HoldSpeak stores.

## Intent routing

The intent router reads the transcript and scores it against intents:
architecture, delivery, product, incident, and comms. The scores pick which plugins run on the summary job.
One meeting can have several intents. See [Meeting intelligence](MEETING_INTELLIGENCE.md).

- The summary job routes by the words in the transcript. It always starts from the `balanced` preset.
- A plugin runs only when it has a model assignment. Without one, HoldSpeak skips it and records the reason.
- Presets: `balanced` (default), `architect`, `delivery`, `product`, and `incident`.
  Set `meeting.routing_profile` for previews. The live face also has an **Intent routing** control.
- **Preview route** on the live face tests routing on text you type. It does not touch the live meeting.
- **Intent router** in the Meetings settings sets `meeting.intent_router_enabled`. It is off by default.

Saved meetings show the intent timeline and the plugin runs.

To test routing on a saved meeting from the shell:

```bash
holdspeak intel --route-dry-run MEETING_ID --profile architect
holdspeak intel --reroute MEETING_ID --profile incident --override-intents incident,comms
```

- `--route-dry-run` prints JSON. It writes nothing.
- `--reroute` needs `--profile`. It saves one reroute window named `MEETING_ID:cli-reroute`.

## Settings

Use **Settings** in the browser when you can. The file is `~/.config/holdspeak/config.json`.
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

The old `intel_cloud_*` keys are read once for migration. Do not use them. Assign models in **Settings > Models**.

## HTTP API

The web runtime serves these routes on `127.0.0.1`. [API reference](API_REFERENCE.md) has the full list.

**Live**

| Route | Purpose |
| --- | --- |
| `GET /api/runtime/status` | Runtime state and egress posture. |
| `GET /api/state` | Current meeting state. |
| `POST /api/meeting/start`, `POST /api/meeting/stop` | Start and stop a meeting. |
| `PATCH /api/meeting` | Update the title and tags. |
| `POST /api/bookmark` | Add a bookmark. |
| `GET /api/intents/control` | Intent routing state. |
| `PUT /api/intents/profile`, `PUT /api/intents/override` | Set the preset and a manual intent set. |
| `POST /api/intents/preview` | Preview routing without saving. |
| `PATCH /api/action-items/{item_id}` (also `/review`, `/edit`) | Change a live action item. |

**Saved meetings**

| Route | Purpose |
| --- | --- |
| `GET /api/meetings` | List meetings. Takes `search`, `date_from`, `date_to`, `speaker`, `tag`, `has_open_actions`. |
| `GET /api/meetings/facets` | Filter values. |
| `GET /api/meetings/{meeting_id}` | One meeting. |
| `GET /api/meetings/{meeting_id}/export?format=markdown\|json` | Download. |
| `POST /api/meetings/import` | Import a recording or transcript. |
| `POST /api/meetings/{meeting_id}/intelligence/run` | Queue a summary. Send `expected_selection_hash` from the planned route. |
| `GET /api/meetings/{meeting_id}/intel-recovery` | Summary recovery state. Also `/retry` and `/skip`. |
| `GET /api/meetings/{meeting_id}/outcome-review` | Proposals for review. |
| `POST /api/meetings/{meeting_id}/proposals/accept-reviewed` | Confirm the ready proposals. |
| `GET /api/meetings/{meeting_id}/artifacts` | Plugin artifacts. |
| `GET /api/meetings/{meeting_id}/intent-timeline` | Intent windows. |
| `GET /api/meetings/{meeting_id}/plugin-runs` | Plugin run history. |
| `GET /api/meetings/{meeting_id}/aftercare` | Open items, decisions, and the change since the previous meeting. |
| `GET /api/meetings/{meeting_id}/followup-draft` | The follow-up draft. |
| `POST /api/meetings/{meeting_id}/aftercare/file-issue` | Propose a GitHub issue. |
| `GET /api/all-action-items` | Action items across meetings. |
| `GET /api/speakers`, `PATCH /api/speakers/{speaker_id}` | Speakers. |

**Queues**

| Route | Purpose |
| --- | --- |
| `GET /api/intel/jobs`, `GET /api/intel/summary` | Summary queue. |
| `POST /api/intel/process`, `POST /api/intel/retry/{meeting_id}` | Run or requeue. |
| `GET /api/plugin-jobs`, `GET /api/plugin-jobs/summary` | Plugin queue. |
| `POST /api/plugin-jobs/process` | Run due plugin jobs. |
| `POST /api/plugin-jobs/{job_id}/retry-now`, `.../cancel` | Retry or cancel one job. |

**WebSocket**

`WS /ws` pushes live events. It needs owner access. Send the text `ping` to get `pong`.
Events include `segment`, `intel_status`, `intel_complete`, `duration`, `bookmark`,
`meeting_started`, `stopped`, and `aftercare_ready`.

## Troubleshooting

| Problem | Action |
| --- | --- |
| BlackHole not found | Run `brew install blackhole-2ch`. Restart **Audio MIDI Setup**. Run `holdspeak meeting --list-devices`. |
| No remote audio | Set the Multi-Output Device as the system output. Check **BlackHole 2ch** in it. Run `holdspeak meeting --setup`. |
| No **Run summary** button | Read the **NO SUMMARY ROUTE** reason. Assign a model in **Settings > Models**. |
| The summary is slow | Use a smaller model. Use a GPU. HoldSpeak uses Metal on Apple Silicon. |
| The summary fails on an endpoint | Read the error on the meeting. Check the host, the key, and the model name in **Settings > Models**. Check that the base URL ends with the API prefix, often `/v1`. |
| The page does not load | Run `holdspeak doctor`. Check the URL that the runtime printed. Check that nothing blocks localhost. |
| Poor transcript quality | Check microphone permission. Reduce noise. Use a larger speech model in **Settings**. |
| Memory use is high | Use a smaller quantization. Assign a smaller model to meetings. |

## See also

- [Getting Started](GETTING_STARTED.md)
- [Models](MODELS.md)
- [Meeting intelligence](MEETING_INTELLIGENCE.md)
- [Meeting aftercare](MEETING_AFTERCARE.md)
- [Meeting architecture](MEETING_ARCHITECTURE.md)
- [Plugin authoring](PLUGIN_AUTHORING.md)
- [Security](SECURITY.md)
