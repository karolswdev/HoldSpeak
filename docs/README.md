# HoldSpeak documentation

HoldSpeak is a local, private, hold-to-talk voice typing tool for macOS and
Linux — plus a meeting mode with AI-extracted intel and a project-aware
intelligent-typing layer. This folder is the documentation index.

> New to the project? Start with the [main README](../README.md) for install +
> a quickstart, then follow the **Start here** path below.

## Start here (user journey)

1. **[Getting Started](./GETTING_STARTED.md)** — install, permissions, and your
   first hold-to-talk dictation.
2. **[User Guide](./USER_GUIDE.md)** — day-to-day workflows and the web runtime.
3. **[Meeting Mode Guide](./MEETING_MODE_GUIDE.md)** — dual-stream capture, live
   transcript, and AI-extracted topics / action items.
4. **[Models](./MODELS.md)** — the bring-your-own-model contract: GGUF in-process,
   MLX on Apple Silicon, or any OpenAI-compatible endpoint.
5. **[Intelligent Typing Guide](./INTELLIGENT_TYPING_GUIDE.md)** — project-aware
   local rewriting, target profiles, and the dictation pipeline.
   - **[The Dictation Copilot](./DICTATION_COPILOT.md)** — see it work: rough
     speech → a project-grounded coding-agent task, with a reproducible demo.
   - **[Desktop Presence](./INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status)**
     — an opt-in, native, on-desktop status surface (macOS HUD · Linux tray +
     notification) so you can see *listening / transcribing / typing* while
     dictating into another app.
6. **[Security & Privacy](./SECURITY.md)** — what's stored, trust boundaries, and
   what can (and can't) leave your machine.

## Reference & integrations

- **[Agent Hook Install](./AGENT_HOOK_INSTALL.md)** — wiring Claude/Codex agent
  hooks into the intelligent-typing layer.
- **[Plugin Authoring](./PLUGIN_AUTHORING.md)** — writing a meeting-intel
  plugin (the `HostPlugin` contract, prompt → LLM → structured output,
  rendering, and chains).
- **[Connector Development](./CONNECTOR_DEVELOPMENT.md)** — building local
  activity connectors.
- **[Firefox Extension Guide](./FIREFOX_EXTENSION_GUIDE.md)** — the browser
  activity connector.
- **[Device Protocol](./DEVICE_PROTOCOL.md)** — the AIPI-Lite remote-audio device
  protocol.
- **[AIPI-Lite Dev Workflow](./AIPI_LITE_DEV_WORKFLOW.md)** — the unified
  firmware + bridge developer workflow.

## Internal / historical plans

Design RFCs, phase specs, and cross-platform/port planning live in
**[`internal/`](./internal/)**. These are kept for provenance and contributor
context — they are *not* user-facing guides and may describe work in progress or
already shipped. Highlights:

- `internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — the parent plugin-system RFC.
- `internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — DIR-01 dictation pipeline spec.
- `internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — MIR-01 meeting-side routing spec.
- `internal/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — the web-first runtime migration.
- `internal/CROSS_PLATFORM_ROADMAP.md`, `internal/LINUX_PORT_PLAN.md` — platform work.
- `internal/RELEASE_HARDENING_CHECKLIST.md` — release-gate checklist.

> The project's planning of record (roadmap, phases, evidence) lives under
> [`pm/roadmap/holdspeak/`](../pm/roadmap/holdspeak/), not here.
