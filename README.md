# HoldSpeak

One local copilot, two modes.
Dictation types anywhere and learns how you work.
Meetings end with decisions, actions, and follow-ups instead of a recording.
Both modes feed one Desk that also holds your Projects, your people, your calendar, and your agents.

*Hold a key, speak, it types. Record a meeting, it closes the loop. All local.*

HoldSpeak is for a developer or architect who leads other people.
Whisper runs on your machine. The models are yours: a local GGUF or MLX model, or an OpenAI-compatible endpoint that you choose.
Each consequential write records a Receipt.
An agent can act only through the operations and grants that you give it.

> **Status:** these documents describe the code on `main`. This is not a release.
> The project is before its first real use (pre-alpha). Defaults and APIs still change.
> See the [change history](CHANGELOG.md) for release information.

## What you can do

### Speak: voice typing that learns

| Task | How HoldSpeak helps | Guide |
| --- | --- | --- |
| Dictate into another app | Hold the global hotkey, speak, and release it. The text goes into the focused field. | [Voice typing](docs/USER_GUIDE.md#voice-typing) |
| Refine a coding prompt | The dictation pipeline adds project facts and context, and can rewrite with your model. | [Dictation pipeline](docs/DICTATION_PIPELINE_GUIDE.md) |
| Teach a correction | Select **Wrong** on a result, correct it, then select **Teach**. The next matching dictation is corrected. | [Speak](docs/USER_GUIDE.md#speak) |
| See what it learned | The dictation journal, the correction memory, and the learning digest show each rule and when it fired. | [Speak](docs/USER_GUIDE.md#speak) |
| Speak commands | Voice commands and the wake word run defined actions. | [Voice commands](docs/VOICE_COMMANDS.md) |

### Meetings: the loop closes

| Task | How HoldSpeak helps | Guide |
| --- | --- | --- |
| Capture a meeting | Record the microphone and system audio, or use meeting import for recordings and transcript files. | [Meeting mode](docs/MEETING_MODE_GUIDE.md) |
| Get decisions and actions | Meeting intelligence runs 14 built-in plugins on your model. Each proposal waits for **Confirm**. | [Meeting intelligence](docs/MEETING_INTELLIGENCE.md) |
| Follow up | Meeting aftercare shows what is open, decided, and changed since the last meeting. | [Meeting aftercare](docs/MEETING_AFTERCARE.md) |
| File an action | An actuator proposes an external action, such as an issue. It runs only as previewed. | [Actuators](docs/ACTUATOR_DEVELOPMENT.md) |
| Let the calendar set the clock | Connect an ICS calendar. See the week on the arrival, arm recordings before meetings, and read the weekly brief. | [The clock](docs/USER_GUIDE.md#the-clock) |

### Projects and people: the work you lead

| Task | How HoldSpeak helps | Guide |
| --- | --- | --- |
| Keep one room per Project | A Project Room shows its sources, health rows, People in the Room, and what needs you. | [Project Rooms](docs/PROJECT_ROOMS.md) |
| Watch sources | Project-scoped Watches observe repositories, issues, and meetings for changes. | [Project Rooms](docs/PROJECT_ROOMS.md) |
| Send a weekly update | HoldSpeak prepares the drafted update from the Room's records. You review it before it goes out. | [Prepared work](docs/USER_GUIDE.md#prepared-work-preparation-review-and-the-weekly-update) |
| Let the steward work | The steward's hand takes bounded external actions, such as a reviewer nudge, under your Control mode. | [The steward's hand](docs/USER_GUIDE.md#the-stewards-hand) |
| Prepare for a 1:1 | The People ledger records reports and peers. The 1:1 card collects open items before you meet. | [People](docs/USER_GUIDE.md#people) |
| Read Jira and Confluence | The Atlassian connectors use your local `acli` sign-in, for many accounts and sites. | [Integrations](docs/INTEGRATIONS.md) |
| Review open loops | Cadence reviews unresolved work and prepares next actions. The Heartbeat sweep runs it on a schedule. | [Cadence](docs/CADENCE.md) |

### The Desk: one place to work

| Task | How HoldSpeak helps | Guide |
| --- | --- | --- |
| Start the day | The arrival shows what needs you, unfinished Thoughts, a brief, the WEEK strip, and recent Meetings. | [The Desk](docs/WEB_DESK.md) |
| Arrange your records | The Floor shows records as objects. Move them and file them in Zones. | [The Desk](docs/WEB_DESK.md) |
| Develop a thought | Open a Thought and refine it with sources and a model. | [Develop a thought](docs/USER_GUIDE.md#develop-a-thought) |
| Talk to your records | Threads keep a saved conversation with sources and tools. Keep a reply as a Note or an Artifact. | [Threads](docs/USER_GUIDE.md#threads) |
| Describe your work | Interview mode asks about your goals, Projects, cadences, and decisions, and saves the context. | [Interview](docs/INTERVIEW.md) |
| Find earlier work | Search Notes, Meetings, Decisions, Threads, and Project items from one memory window. | [Relationship-aware memory](docs/RELATIONSHIP_AWARE_MEMORY.md) |
| Prepare architecture work | Draft a decision brief, review questions, or an agent brief from your records. | [Architecture work](docs/ARCHITECTURE_WORK.md) |
| Change the room | Select one of the Places, or use **Settle in** for a quiet view. | [Places](docs/ENVIRONMENTS.md) |

## You stay in control

- **Local first.** The database and Whisper transcription stay on the hub. See [Security & Privacy](docs/SECURITY.md).
- **Your models.** The Concierge in **Settings > Models** finds your engines and proposes an assignment per capability. See [Models](docs/MODELS.md).
- **Receipts.** An operation that files or decides records a Receipt, and a refused operation records its refusal. See [Kernel](docs/KERNEL.md).
- **Control modes.** The default is **YOLO**. For supported external writes, **Normal** and **Secure** require approval or a scoped grant. See [Control modes](docs/AUTHORITY.md).
- **Egress is named.** A model endpoint, a connector, a remote client, or an outbound action can send data off the hub. The badge and the Receipt name the destination.
- **Honest limits.** `holdspeak doctor` reports what is broken. Upgrades back up the database first. See [Release and recovery](docs/RELEASING.md).

## Agents and MCP

One service layer declares each operation. HTTP, MCP, and the test rig reach the same operation, with the same authority checks and the same Receipts.

- The [MCP sidecar](docs/MCP_SIDECAR.md) exposes 248 tools across 43 families. It is a stdio proxy to the hub's `/api/mcp` endpoint.
- A tool name does not grant permission. An agent acts only under the palette and grants that you give it. To let an agent file notes and record decisions, select **Allow filing** on its row in Settings, Remote Access. Select **Stop filing** to end the grant.
- [Reach](docs/USER_GUIDE.md#reach) lets a remote agent connect with a scoped credential (a palette and a time limit, shown once).
- [Reach Runner](docs/REACH_RUNNER.md) requests a Heartbeat sweep and steward runs from another machine.
- Threads, Workflows, and Coder steering direct AI work from the Desk. See [Automation](docs/AUTOMATION.md) and [Agents and Threads](docs/AGENTS_AND_THREADS.md).
- You can add [meeting plugins](docs/PLUGIN_AUTHORING.md) and [activity connectors](docs/CONNECTOR_DEVELOPMENT.md).

## Start here

Read [Getting Started](docs/GETTING_STARTED.md) for platform requirements and installation options.
For a source installation, install Python 3.10 or later, `uv`, and Node.js 22.12 or later first.
The Python build hook also builds the Web app.
The base install also builds the local model runtime (llama.cpp). This step needs a C++ compiler.

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

The main configuration file is `~/.config/holdspeak/config.json`.
Use Settings for normal changes.
Run `holdspeak backup` before an upgrade.

## Platform support

| Capability | macOS on Apple Silicon | Linux X11 | Linux Wayland |
| --- | --- | --- | --- |
| Whisper transcription | MLX Whisper | faster-whisper | faster-whisper |
| Global hotkey and text insertion | Requires desktop permissions | Supported | Depends on compositor restrictions |
| Meeting capture | Microphone and optional BlackHole system audio | Microphone and PulseAudio/PipeWire system audio | Microphone and PulseAudio/PipeWire system audio |

The Web app also accepts browser microphone input.
There is no Windows support today.
The [iPad app](apple/README.md) and [AIPI-Lite](docs/AIPI_LITE_DEV_WORKFLOW.md) connect to a hub. The iPad track is dormant.

## How it compares (mid-2026)

| Tool or category | They do better | HoldSpeak does better | Pick them if |
| --- | --- | --- | --- |
| OS dictation (Apple Dictation, Windows Voice Typing) | Zero setup, free, always there | Your own models, the learning loop, meetings | You dictate occasionally |
| Local Whisper menu-bar apps (superwhisper, MacWhisper, VoiceInk) | Simpler setup, polished single-purpose UX | Local LLM rewriting, the visible learning loop, meetings, Linux | You want local transcription on a Mac and nothing else |
| AI dictation services (Wispr Flow, Aqua Voice) | Strong accuracy and editing UX, no model management | Everything local, open source, no subscription, meetings | Your voice in their cloud is acceptable to you |
| Talon | The deepest hands-free coding control; mature ecosystem | Prose dictation with LLM rewriting, meetings, a lower learning curve | You need full hands-free computer control |
| Raw Whisper tooling (whisper.cpp, faster-whisper) | Total control, minimal surface | A product: typing, routing, journal, meetings, a Desk | You enjoy building your own pipeline |

The trade-offs: HoldSpeak is 0.x. The smart parts need a local model or an endpoint you provide.
Setup is heavier than a menu-bar app. Wayland limits global hotkeys to best effort.

## Read next

- [What is HoldSpeak?](docs/WHAT_IS_HOLDSPEAK.md): the product in one page.
- [User Guide](docs/USER_GUIDE.md): operate the product each day.
- [Use cases](docs/USE_CASES.md): choose a workflow by the result you need.
- [Architecture](docs/ARCHITECTURE.md): the runtime and data flow.
- [Documentation index](docs/README.md): every guide and reference.
- Graph join (`docs/generated/graph.json`; run `scripts/gen_docs.sh` to write it): which triggers reach which actions.

## Contributing and license

See [Contributing](CONTRIBUTING.md) for development setup, checks, and the commit workflow.
HoldSpeak uses the [Apache License 2.0](LICENSE).
