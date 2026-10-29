# HoldSpeak

**An agentic-first, web-based AI operating system for your work.**

Turn a spoken thought, a meeting, or a project question into work your agents can carry forward.
One Desk connects your notes, people, projects, and coding agents, from the first idea to the next action.
It runs on your machine. You use it in a browser.

![The HoldSpeak Desk, with project notes behind an Ask answer that cites meetings, decisions, and tasks.](docs/assets/readme/desk-project-room.jpg)

*Ask “Is the ledger cutover still on track?” and follow the answer back to the work behind it.*

[Get started](#quick-start) · [Explore the flows](#what-can-you-do-with-it) · [Programs](#run-a-goal-as-a-program) · [Documentation](docs/README.md) · [Contribute](CONTRIBUTING.md)

Open source · [Apache 2.0](LICENSE) · Version 0.4, pre-alpha

## A Desk where AI can work with you

Write, speak, ask, delegate, and review in the same place.
Your Notes, Meetings, Projects, decisions, and saved conversations give each next step a starting point.

**Agentic-first** means AI can use tools to act on your work.
Ask, coding agents, Programs, and Automations connect to the same Desk services.

The Desk takes its cues from Amiga Workbench: objects, drawers, movable windows, menus, and a dock.
Arrange the tools around the work you are doing.
Choose local models, endpoints on your network, cloud APIs, or supported agent CLIs.

## What can you do with it?

| Start here | Carry it forward |
| --- | --- |
| **“I have an idea.”** | Speak or write a Note, develop the thought, find tasks, and prepare a brief. |
| **“We just decided this.”** | Turn a meeting into decisions, owners, actions, and a project update. |
| **“What is blocking us?”** | Ask across your work, open the sources, and make the next task. |
| **“Build this.”** | Hand a task to Claude Code, Codex, or pi in a separate worktree. |
| **“Take this goal through.”** | Plan a Program with steps, dependencies, agents, and checks. |
| **“Do this every Friday.”** | Configure an Automation that prepares a draft from the week's work. |
| **“What do I owe my team?”** | Review commitments, prepare for a 1:1, and follow through. |

### From a thought to a useful result

Capture an idea as a Note. Select **Develop this thought** to refine it with AI.
Ask questions, compare options, and keep the result editable.
Use **Find the tasks** when the idea is ready to become work.

Ask about a Note, Meeting, Project, person, or your whole Desk.
With a tool-capable engine, Ask can read more permitted records and act during the turn.
Open **References** to inspect the sources, then save a result, make a task, or prepare a send.
The conversation is saved as a Thread from the first answer, so you can continue it later.

For example: develop a service migration idea, record the decision, and hand its implementation task to an agent.
The same source material can support each step.

[Notes and thought development](docs/USER_GUIDE.md#develop-a-thought) · [Ask and conversations](docs/AGENTS_AND_THREADS.md) · [Architecture work](docs/ARCHITECTURE_WORK.md)

### From a meeting to the next action

![Today on the Desk, showing work that needs attention and a meeting flow from preparation to follow-up.](docs/assets/readme/desk-meeting-review.jpg)

*Prepare, record, review, and follow up. Today brings the work that needs you into view.*

Record microphone and system audio, or import a recording or transcript.
Run meeting intelligence to extract decisions, requirements, action owners, risks, and other outputs.
HoldSpeak includes **14 built-in plugins**. Each needs an engine assignment to run.

Review the proposed outcomes, link the meeting to a Project, and carry an action into a task or agent brief.
Before the next meeting, return to its open commitments.
Calendar integration and scheduled recording are available when configured.

[Meeting mode](docs/MEETING_MODE_GUIDE.md) · [Meeting intelligence](docs/MEETING_INTELLIGENCE.md) · [Aftercare](docs/MEETING_AFTERCARE.md)

### Hand work to a coding agent

![The Agents window lists a Claude Code task with an open pull request, ended sessions, and installed Claude Code, Codex, and pi profiles.](docs/assets/readme/agents.png)

*See the task, the agent, and its latest state. Open the work when it needs your attention.*

Select **Hand to agent** on a task, Note, decision, Meeting, Artifact, or Project item.
Inspect the brief, repository, branch, and worktree before launch.
HoldSpeak starts the selected Claude Code, Codex, or pi profile in a separate Git worktree.

Follow progress, read terminal output, and answer questions by text or voice.
Set how many agents can work at once; **Start when one is free** queues the next handoff.
Existing Claude Code and Codex sessions can also report to the Desk through hooks.

This flow needs a project repository, the installed agent CLI, and tmux.
Review the changes and results before you treat the task as finished.

[Coder integration](docs/CODER_INTEGRATION.md) · [Agent hook setup](docs/AGENT_HOOK_INSTALL.md)

### Run a goal as a Program

![A Program shows three implementation steps, check and review results, a pull request ready for a merge decision, and findings that need an answer.](docs/assets/programs/program-your-turn-1440.png)

*Give a goal several steps. Keep each step's work, checks, findings, and decisions visible. Check and pull request states shown here use a test fixture.*

Use a Program for work that needs more than one handoff.
Choose the repository, steps, dependencies, agents, and checks.
Each step gets its own worktree.
Configured gates can carry it through work, check, review, pull request, and merge.

Templates include **Fast cycle**, **Build and review**, **Race**, **Overnight on the home box**, and **From the desk**.
The Control level sets how routine decisions proceed.
Questions and findings that need you return through **Your turn** and **Needs you**.
A handover Note retains the state and decisions.

If an agent reaches its usage limit, a configured fallback can continue on the same step, branch, and worktree.
Use **Overnight on the home box** to run pi on an idle home engine, with Claude Code as reviewer.

[Programs guide](docs/programs.md)

### Lead projects and people from the same place

![A Project Room shows its current risk, a late milestone, this week's concerns, an Ask field, and the Write update action.](docs/assets/readme/project.png)

*Review what needs you, ask a project question, or select **Write update**.*

Project Rooms bring open work, decisions, commitments, and recent changes together.
Connect GitHub, Jira, or Confluence sources, then ask about the Project or select **Write update**.
Review the draft and its sources before you send it to a saved destination.

People keeps context for reports and peers.
Prepare for a 1:1 with open commitments on both sides.
Confidential People material has a separate encrypted store and specific access rules.

Built first for a software architect who leads people and projects.

[Project Rooms](docs/PROJECT_ROOMS.md) · [People](docs/USER_GUIDE.md#people) · [People security](docs/PEOPLE_SECURITY.md)

### Make useful work repeat

Set an Automation's sources, instruction, engine or agent, trigger, and output.
For example: prepare a Friday update from the week's meetings and put the draft in your Inbox.
Run it once, inspect the result, then enable a schedule or supported event.
A scheduled job needs the hub running when it is due.

Runs retain their results and execution history.
With memory enabled, an Automation can retain its own working memory between runs.
A destination output prepares a send for your review.
Project Watches and the Project Steward can also bring connected work back to your attention.

[Automations](docs/AUTOMATION.md) · [Project Watches and Steward](docs/PROJECT_ROOMS.md#use-the-steward) · [Cadence](docs/CADENCE.md)

### Take the Desk with you

<p align="center">
  <img src="docs/assets/readme/ask-mobile.png" width="320" alt="Ask in a phone-sized browser, with an answer and source references." />
  <img src="docs/assets/programs/program-running-393.png" width="320" alt="A Program in a phone-sized browser, with step states and a question to answer." />
</p>

*The browser Desk adapts to a phone, with full-width windows and a Back control.*

You can also work by voice.
Hold Right Option on macOS or Right Alt on Linux, speak, and release to type into the focused app.
The dictation pipeline can use project context and your selected engine to refine the text.

With Calls set up, phone your Desk, authenticate, and ask about work, add a task, or write a Note.
Confirm proposed sends by voice. The completed conversation becomes a Note.

[Voice typing](docs/USER_GUIDE.md#voice-typing) · [Calls and The Line](docs/calls.md) · [Phone and reach-you rules](docs/phone.md)

*Screenshots show sample workspaces from the repository's October 2026 captures. Program check and pull request states use test fixtures.*

## Your work, your engines

The local hub stores your work. Speech recognition runs locally with Whisper.
There is no required HoldSpeak account or cloud service, and the product has no telemetry.

Choose a different engine for each kind of work in **Settings > Engines**:

| Engine path | Runs through |
| --- | --- |
| **Local models** | GGUF or MLX, with the appropriate runtime |
| **Your endpoints** | An OpenAI-compatible server on your network or a cloud provider |
| **Agent CLIs** | Installed Claude Code, Codex, pi, or Gemini CLI presets and their configured providers |

A CLI used as an engine answers Desk requests. A coding handoff starts a separate repository session.
Cloud engines and connectors can send data outside your machine; check the engine and destination for the job.
External providers can require accounts and charge for use.

Saved work becomes searchable memory. Meaning search adds local embeddings when enabled.
References, tool results, run records, and Receipts help you inspect what happened.
**Secure**, **Normal**, and **YOLO** control authority for eligible operations within configured scope.

[Models](docs/MODELS.md) · [Memory](docs/RELATIONSHIP_AWARE_MEMORY.md) · [Control modes](docs/AUTHORITY.md) · [Security](docs/SECURITY.md)

## Connect it to the rest of your work

Use MCP to give an external agent access to permitted Desk operations.
The full catalogue has **306 tools across 52 families**; each caller receives only its allowed tools.
The local sidecar serves clients such as Claude Code, Codex, and Cursor.
Reach adds scoped Streamable HTTP access when enabled.

Send saved work to a folder, GitHub, Jira, Confluence, email, or Slack through configured destinations.
Extend HoldSpeak with meeting plugins, connectors, actuators, agent personas, and voice commands.

[MCP reference](docs/MCP_SIDECAR.md) · [Integrations](docs/INTEGRATIONS.md) · [Plugin authoring](docs/PLUGIN_AUTHORING.md) · [System architecture](docs/SYSTEM_ARCHITECTURE.md)

## Quick start

For a source install, use Python 3.10+, Git, [uv](https://docs.astral.sh/uv/), npm, and Node.js 22.12+.
The local model runtime also needs CMake and a C++ compiler.

```sh
git clone https://github.com/karolswdev/HoldSpeak.git
cd HoldSpeak
uv venv
source .venv/bin/activate
uv pip install -e .
holdspeak
```

On Linux, use `uv pip install -e '.[linux]'` for the install step.
Open the URL printed by the hub.

1. Follow Setup to prepare speech and your engines.
2. Keep a dictated sentence as a Note, or continue to the Desk and type one.
3. Choose an engine in **Settings > Engines**, then ask about the Note.
4. Import a meeting, create a Project, or connect an agent when you are ready.

Run `holdspeak doctor` to check missing dependencies and setup problems.
The [Getting Started guide](docs/GETTING_STARTED.md) covers system packages, permissions, and optional extras.

**Platforms:** macOS on Apple Silicon and Linux. Wayland text insertion is best effort and depends on the compositor.
System audio capture needs BlackHole on macOS or PulseAudio/PipeWire on Linux.
Windows is not supported today.

HoldSpeak is pre-alpha. Interfaces, defaults, and APIs can change.
Model quality and tool support depend on the engine.
Recording, integrations, agent launches, and scheduled work need their dependencies and a running hub.
Published packages can differ from this repository's `main` branch.

## Go deeper

| You want to | Start with |
| --- | --- |
| Try your first flow | [Getting Started](docs/GETTING_STARTED.md) |
| Use HoldSpeak each day | [User Guide](docs/USER_GUIDE.md), [Desk guide](docs/WEB_DESK.md) |
| Choose engines and data boundaries | [Models](docs/MODELS.md), [Security](docs/SECURITY.md) |
| Build with agents | [Coder integration](docs/CODER_INTEGRATION.md), [Programs](docs/programs.md), [MCP](docs/MCP_SIDECAR.md) |
| Understand the implementation | [Architecture](docs/ARCHITECTURE.md), [repository map](docs/generated/REPOSITORY_MAP.md) |
| Contribute | [Contributing](CONTRIBUTING.md), [change history](CHANGELOG.md) |

Browse the [full documentation index](docs/README.md).
