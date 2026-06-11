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
  pipeline. Intent routing, project-facts enrichment, target profiles, LLM rewriting.
- **[Project knowledge: facts + context](./INTELLIGENT_TYPING_GUIDE.md#5-set-up-project-knowledge)**:
  teach the copilot about a repo. Facts (the `project.yaml` KB, stamped in verbatim)
  and context (the `.hs/` files an optional rewrite reads) are two different things;
  this is what each is and how to set up both.
- **[The Dictation Copilot](./DICTATION_COPILOT.md)**: see it work. Rough speech
  becomes a project-grounded coding-agent task, with a demo you can reproduce.
- **[Voice Commands](./VOICE_COMMANDS.md)**: map a spoken keyword to a real action.
  Say a keyword while dictating and HoldSpeak opens a URL, launches an app, runs a
  shell command, or types a snippet instead of typing the words. Off by default, you
  configure every command, and each one is limited to exactly the action you gave it.
- **[Activity Pre-Briefing](./ACTIVITY_PREBRIEFING.md)**: a quiet read of what you
  touched recently, above the dictation cockpit. At most three source-cited cards,
  dismissible, never acting on their own. One action pins a record so your next
  dictation can use it as context. Gated by the activity tracking toggle: off means
  no cards.
- **[The learning loop: journal, correct, see what it learned, replay](./INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay)**:
  the local-only loop that gets better at your voice. Fix a misfire in one tap, see
  the honest "learned from N similar" count in the "What HoldSpeak learned" digest,
  and replay an utterance to watch the routing change. The proof, not the promise.
- **[Desktop Presence](./INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status)**:
  an opt-in, native, focus-safe status surface (a macOS HUD, a Linux tray and
  notification) that shows whether it's listening, transcribing, or typing while you
  dictate elsewhere. Optionally with
  **[Qlippy, the mascot](./INTELLIGENT_TYPING_GUIDE.md#qlippy-the-mascot-optional)**:
  an ambient pixel-art dock plus one-at-a-time cards for the moments that need
  you (approvals, results, learning, meeting follow-ups), each with plain
  privacy answers. He never acts on his own.
- **[Models (bring your own)](./MODELS.md)**: the model contract. GGUF in-process,
  MLX on Apple Silicon, or any OpenAI-compatible endpoint.

## Meet: meeting intelligence

- **[Meeting Mode Guide](./MEETING_MODE_GUIDE.md)**: capture mic and system audio
  together, get a live transcript with speaker labels, review AI-extracted topics,
  actions, and artifacts at `/history`, then close the loop with aftercare: see
  what is still open, decided, or changed since last time, jump to the transcript
  moment that justifies a result, file an accepted action as a human-approved
  issue, and draft the follow-up. Import recordings and transcripts you
  already have (web upload or `holdspeak import`; vtt and srt keep their real
  timestamps and speaker names) and filter the archive by date, speaker, tag,
  and open actions.

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
