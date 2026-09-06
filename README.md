# HoldSpeak

HoldSpeak connects voice typing, meetings, project records, and AI work on one Desk.
You choose the models, data sources, and authority for each kind of work.

Use it to dictate into an editor, prepare a decision brief, review a meeting, or direct a Coder session.
The **Interview** mode helps you describe your work and develop useful suggestions through a conversation.

These documents describe the code on `main`. A published release can have fewer features.
See the [change history](CHANGELOG.md) for release information.

## Start here

Read [Getting Started](docs/GETTING_STARTED.md) for platform requirements and installation options.
For a source installation, install Python 3.10 or later, `uv`, and Node.js 22.12 or later first.
The Python build hook also builds the Web app.

```sh
git clone https://github.com/karolswdev/HoldSpeak.git
cd HoldSpeak
uv venv
source .venv/bin/activate
uv pip install -e .
holdspeak
```

On Linux, use `uv pip install -e '.[linux]'` for the transcription backend.
System audio dependencies and desktop permissions depend on your platform.

1. Open the local URL that HoldSpeak prints.
2. Select **Dictate one sentence**.
3. Edit the transcript if necessary.
4. Select **Copy** or **Keep as Note**.

This first result creates the initial Desk contents.
If capture fails, use the recovery action on the screen or run `holdspeak doctor`.

## What you can do

| Task | How HoldSpeak helps | Guide |
| --- | --- | --- |
| Dictate into another app | Hold the global hotkey, speak, then release it to insert text. | [Voice typing](docs/USER_GUIDE.md#voice-typing) |
| Refine a coding prompt | Use project facts, project context, and an optional model in the dictation pipeline. | [Dictation pipeline](docs/DICTATION_PIPELINE_GUIDE.md) |
| Teach a dictation correction | Select **Wrong** on a result, correct the words or the route, then **Teach**. The next dictation that carries the phrase is corrected. | [Speak](docs/USER_GUIDE.md#speak) |
| Review a meeting | Record or import a meeting. Review the transcript, decisions, action items, and artifacts. | [Meeting mode](docs/MEETING_MODE_GUIDE.md) |
| Develop your working context | Revisit Interview sections for goals, Projects, cadences, decisions, and delegation. | [Interview](docs/INTERVIEW.md) |
| Prepare architecture work | Draft a decision brief, review questions, or an agent brief from available records. | [Architecture work recipes](docs/ARCHITECTURE_WORK.md) |
| Follow project changes | Connect Project sources and configure supported Watches. | [Project Rooms](docs/PROJECT_ROOMS.md) |
| Find earlier work | Search Notes, Meetings, Decisions, Threads, Project items, Workbench results, and Cadence loops from one Desk memory window. Connected evidence arrives with the relationship that reached it. | [Relationship-aware memory](docs/RELATIONSHIP_AWARE_MEMORY.md) |
| Let the calendar set the clock | Connect an ICS calendar. See the week on the arrival, arm recordings before meetings under your consent, and read the weekly brief. | [The clock](docs/USER_GUIDE.md#the-clock) |
| Direct AI work | Use Threads, Workflows, Coder steering, or an MCP client. | [Automation](docs/AUTOMATION.md) |
| Change your workspace | Select a place, save favorites, or use **Settle in**. | [Places](docs/ENVIRONMENTS.md) |

## The Desk

The **arrival** shows work that needs you, unfinished Thoughts, a brief, and recent Meetings.
The **Floor** shows your records as objects that you can open, move, and file in Zones.
Speak, Meetings, Settings, and other tools open in Desk windows.

Threads save your conversation on the hub.
Your sent prompt appears before the answer arrives. Routine tool calls stay inside the collapsed **Actions** control.
Requests for a decision, tool questions, and failures remain visible.
You can keep a reply as a separate Note or Artifact.

Interview uses the existing Thread conversation and MCP tools.
It saves context with source references and records suggestions that you can revisit.
**Try draft** sends a request for a manual draft. **Keep idea** saves your choice about a suggestion.
Neither action installs a recurring automation.

The current Interview supports manual preparation and the existing Project setup path.
General agent delegation and recurring setup through Interview remain outside this increment.
Model quality also varies. Check source claims, assumptions, and draft placeholders before you use a result.

## Models and data

Open **Settings > Models** to use the **Concierge**.
It detects engines and proposes an assignment for each capability group.
Check the engine and host for each group before you select **Use these**.
Use **Adjust** for individual capability assignments.
See [Models](docs/MODELS.md) for local runtimes and endpoint setup.

HoldSpeak stores its database on the hub. Whisper transcription runs on the hub.
Configured model endpoints, providers, remote clients, and outbound actions can transfer data to other systems.
The boundary and Receipt for a run identify where that work went.
See [Security & Privacy](docs/SECURITY.md) for storage, credentials, and network boundaries.

The default Control mode is **YOLO**.
Eligible actions to configured destinations can execute without another HoldSpeak approval prompt.
**Secure** and **Normal** provide different approval rules.
See [Control modes](docs/AUTHORITY.md) before you configure actions with external effects.

## Platform support

| Capability | macOS on Apple Silicon | Linux X11 | Linux Wayland |
| --- | --- | --- | --- |
| Whisper transcription | MLX Whisper | faster-whisper | faster-whisper |
| Global hotkey and text insertion | Requires desktop permissions | Supported | Depends on compositor restrictions |
| Meeting capture | Microphone and optional BlackHole system audio | Microphone and PulseAudio/PipeWire system audio | Microphone and PulseAudio/PipeWire system audio |

The Web app also accepts browser microphone input.
On Wayland, clipboard paste can provide an alternative when direct text insertion is unavailable.
See [Getting Started](docs/GETTING_STARTED.md) for setup and recovery.

## Extend HoldSpeak

The [MCP sidecar](docs/MCP_SIDECAR.md) exposes 222 tools across 40 families.
It shares the product service layer. A tool name does not grant permission to execute it.
Some live delivery operations require the running Web runtime and are absent from the sidecar.

Meeting intelligence includes 14 built-in plugins.
You can add [meeting plugins](docs/PLUGIN_AUTHORING.md) or [activity connectors](docs/CONNECTOR_DEVELOPMENT.md).
[Automation](docs/AUTOMATION.md) explains the available triggers, execution paths, and limits.

## Companions

The [iPad app](apple/README.md) connects to a HoldSpeak hub for capture and review.
[AIPI-Lite](docs/AIPI_LITE_DEV_WORKFLOW.md) provides a portable device for meeting controls and spoken replies.
Both depend on the hub and its configured capabilities.

## Configuration and recovery

The main configuration file is `~/.config/holdspeak/config.json`.
Use Settings for normal configuration changes.
Run `holdspeak backup` before an upgrade when you need a recoverable snapshot.
See [Release and recovery](docs/RELEASING.md) before you use `holdspeak restore`.

## Contributing

See [Contributing](CONTRIBUTING.md) for development setup, documentation rules, checks, and the commit workflow.
The [documentation index](docs/README.md) links the user guides and technical references.

## License

HoldSpeak uses the [Apache License 2.0](LICENSE).

## See also

- [Getting Started](docs/GETTING_STARTED.md): install and capture your first sentence.
- [User Guide](docs/USER_GUIDE.md): operate the product each day.
- [Architecture](docs/ARCHITECTURE.md): understand the runtime and data flow.
- [Documentation index](docs/README.md): find a task, reference, or internal specification.
