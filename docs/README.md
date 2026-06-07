# HoldSpeak documentation

HoldSpeak is a local, private, hold-to-talk voice typing tool for macOS and
Linux, plus a meeting mode with AI-extracted intel and a project-aware
intelligent-typing layer. This page is the map. Pick a journey.

> New here? Start with the [main README](../README.md) for the pitch and a
> quickstart, then follow **Start here** below.

## Start here

- **[Getting Started](./GETTING_STARTED.md)**: install, grant permissions, and land
  your first hold-to-talk dictation in another app.

## Dictate: voice typing and the intelligent copilot

- **[User Guide](./USER_GUIDE.md)**: the day-to-day. Workflows, the web runtime, and
  how the two halves (typing and meetings) fit together.
- **[Intelligent Typing Setup](./INTELLIGENT_TYPING_GUIDE.md)**: the project-aware
  pipeline. Intent routing, project-KB enrichment, target profiles, LLM rewriting.
- **[The Dictation Copilot](./DICTATION_COPILOT.md)**: see it work. Rough speech
  becomes a project-grounded coding-agent task, with a demo you can reproduce.
- **[Dictation journal, corrections & replay](./INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay)**:
  the local-only record of every dictation. Fix a misfire in the moment, then replay
  it to watch the copilot improve.
- **[Desktop Presence](./INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status)**:
  an opt-in, native, focus-safe status surface (a macOS HUD, a Linux tray and
  notification) that shows whether it's listening, transcribing, or typing while you
  dictate elsewhere.
- **[Models (bring your own)](./MODELS.md)**: the model contract. GGUF in-process,
  MLX on Apple Silicon, or any OpenAI-compatible endpoint.

## Meet: meeting intelligence

- **[Meeting Mode Guide](./MEETING_MODE_GUIDE.md)**: capture mic and system audio
  together, get a live transcript with speaker labels, and review AI-extracted
  topics, actions, and artifacts at `/history`.

## Extend: build on it

- **[Plugin Authoring](./PLUGIN_AUTHORING.md)**: write a meeting-intel plugin. The
  `HostPlugin` contract, prompt to LLM to structured output, rendering, chains, and
  the actuator propose/approve/execute flow.
- **[Connector Development](./CONNECTOR_DEVELOPMENT.md)**: build a local activity
  connector (the `cli_enrichment` / `pipeline` / other kinds).
- **[Agent Hook Install](./AGENT_HOOK_INSTALL.md)**: wire Claude/Codex agent hooks
  into the intelligent-typing layer.
- **[Firefox Extension Guide](./FIREFOX_EXTENSION_GUIDE.md)**: the browser activity
  connector.
- **[AIPI-Lite Developer Workflow](./AIPI_LITE_DEV_WORKFLOW.md)** and **[Device
  Protocol](./DEVICE_PROTOCOL.md)**: the portable companion device. The firmware and
  bridge workflow, and the remote-audio WebSocket protocol.

## Operate & Trust

- **[Security & Privacy](./SECURITY.md)**: the threat model. What's stored, the trust
  boundaries, and exactly what can (and can't) leave your machine.

## Internal / historical plans

Design RFCs, phase specs, and cross-platform/port planning live in
**[`internal/`](./internal/)**. They're kept for provenance and contributor
context, not as user-facing guides, and some describe work in progress or already
shipped. Also there: the docs working notes,
**[`internal/DOCS_STYLE.md`](./internal/DOCS_STYLE.md)** (voice and page skeleton)
and **[`internal/DOC_AUDIT_2026-06.md`](./internal/DOC_AUDIT_2026-06.md)** (the
accuracy audit and canonical facts). A few highlights:

- `internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`: the parent plugin-system RFC.
- `internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`: the DIR-01 dictation pipeline spec.
- `internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md`: the MIR-01 meeting-side routing spec.
- `internal/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`: the web-first runtime migration.
- `internal/CROSS_PLATFORM_ROADMAP.md`, `internal/LINUX_PORT_PLAN.md`: platform work.
- `internal/RELEASE_HARDENING_CHECKLIST.md`: the release-gate checklist.

> The project's planning of record (roadmap, phases, evidence) lives under
> [`pm/roadmap/holdspeak/`](../pm/roadmap/holdspeak/), not here.
