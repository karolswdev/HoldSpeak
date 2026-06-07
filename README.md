# HoldSpeak

<p align="center">
  <img src="docs/assets/pixellab/holdspeak-mark.png" alt="HoldSpeak logo — a held key with rising soundwaves" width="120">
</p>

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Tests](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml/badge.svg)](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)

Voice input for macOS and Linux — hold a key, speak, release. Local-first and private by default, with optional cloud intelligence when you want it. Works standalone as a voice typing tool or wired into meeting mode, AI agents, and the AIPI-Lite companion device.

> **Status: early / pre-release.** HoldSpeak is mature in features but not yet
> published to PyPI — install from source (below). APIs, config, and defaults may
> still change. Feedback and contributions welcome.

## What it does

**Voice typing** — hold your configured hotkey, speak, release. Text appears in any app. Punctuation commands (`"period"`, `"comma"`, etc.) work out of the box. When you say `"clipboard"` inside a dictated phrase, HoldSpeak replaces that word with the current clipboard text.

**Meeting mode** — dual-stream capture (mic + system audio), live transcript with speaker labels, AI-extracted topics and action items, web dashboard, deferred intel queue for homelab/cloud models.

**Intelligent dictation** — project-aware pipeline that routes utterances through intent classification, project KB enrichment, and LLM rewriting before text lands in the destination app. Adapts output for Codex, Claude, terminal, browser, or editor. Every dictation is kept in a local-only **journal** (said → typed → routed → latency) you can review, **correct in the moment** (one tap teaches the copilot), and **replay** through the current pipeline to watch it learn — see [Dictation journal, corrections & replay](docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay).

**Desktop presence** *(opt-in)* — an ambient, native status surface so you can see what the copilot is doing (*listening / transcribing / typing*) while you dictate into another app, without the dashboard on screen. A floating HUD on macOS and X11/wlroots; a focus-safe tray glyph + in-place notification everywhere. Off by default, never steals keyboard focus. Flip it on from **Settings** (or `presence.enabled` in your config) — a `HOLDSPEAK_DESKTOP_PRESENCE=1` env var still force-enables it for headless launches. See [Desktop Presence](docs/INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status).

## Workflow Map

| Voice typing | Meeting intelligence | Project-aware typing |
| --- | --- | --- |
| ![Pixel art microphone with hold-to-talk waves](docs/assets/pixellab/hold-to-talk-microphone.png) | ![Pixel art meeting notebook with action items](docs/assets/pixellab/meeting-intelligence-notebook.png) | ![Pixel art code editor connected to local context](docs/assets/pixellab/project-aware-typing.png) |
| Hold the hotkey, speak, release, and insert text into the active app. | Capture meetings, review transcripts, accept actions, and export local handoffs. | Use `.hs/` project context and agent hooks to shape rough speech into useful prompts. |

## Intelligence Pipeline

<p align="center">
  <img src="docs/assets/pixellab/operator-working-loop.gif" alt="Animated pixel art operator working at a terminal while companion and task cards update" width="280">
</p>

HoldSpeak turns speech into transcript context, reviewable actions, summaries,
and coding-agent replies while the local runtime stays in control.

## AIPI-Lite Companion

<p align="center">
  <img src="docs/assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="260">
</p>

The optional AIPI-Lite companion is a portable ESPHome-based device you can
carry between rooms. Put it on Wi-Fi, including a phone hotspot when needed,
and it can provide meeting capture controls and status feedback while
HoldSpeak handles real-time transcription and intelligence.

It also works as a coding-agent companion. With Claude/Codex hooks enabled,
HoldSpeak can notify the device when an agent is waiting for your answer; you
can speak the reply through AIPI-Lite and have HoldSpeak route it back into the
active coding session. For remote use, the device and bridge still need a
network path you control, such as home Wi-Fi, hotspot, VPN, or another private
tunnel.

Buy hardware from the [official AIPI Lite product page](https://aipi.com/products/aipi-lite)
or the [Amazon listing](https://www.amazon.com/dp/B0FQNNVV36). Firmware,
bridge setup, and verification live in [AIPI-Lite Developer Workflow](docs/AIPI_LITE_DEV_WORKFLOW.md).

## Platform support

| Capability | macOS 14+ (Apple Silicon) | Linux X11 | Linux Wayland |
|---|---|---|---|
| Voice typing | ✅ | ✅ | ✅ |
| Global hotkey | ✅ | ✅ | ⚠️ Best effort |
| Cross-app typing | ✅ | ✅ | ⚠️ Best effort |
| Meeting mode | ✅ | ✅ | ✅ |
| System audio capture | ✅ BlackHole | ✅ Pulse/PipeWire | ✅ Pulse/PipeWire |

Wayland sessions often block global hooks and synthetic typing. HoldSpeak falls back to clipboard paste for injection.

## Quickstart

HoldSpeak installs from source (it isn't on PyPI yet). The one-liner clones via
the install script; `doctor` checks your setup, then `holdspeak` launches the web
runtime:

```bash
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash
holdspeak doctor   # verify mic permissions + backends
holdspeak          # launch the web runtime
```

Or from a clone (using [`uv`](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/karolswdev/HoldSpeak.git && cd HoldSpeak
uv pip install -e .
holdspeak doctor && holdspeak
```

Optional extras (install only what you need):

```bash
# Meeting mode with AI intelligence
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash -s -- --with-meeting

# Intelligent dictation — pick one backend
uv pip install -e '.[dictation-mlx]'      # Apple Silicon (MLX)
uv pip install -e '.[dictation-llama]'    # Cross-platform (GGUF)
uv pip install -e '.[dictation-openai]'   # OpenAI-compatible endpoint
```

The dictation/meeting LLM is **bring-your-own** — GGUF in-process, MLX on Apple
Silicon, or any OpenAI-compatible endpoint. See [`docs/MODELS.md`](docs/MODELS.md)
for the contract and current model suggestions.

## Where to go next

| I want to… | Read this |
|---|---|
| Browse all the docs | [Documentation index](docs/README.md) |
| Get it running and verify my setup | [Getting Started](docs/GETTING_STARTED.md) |
| Choose / configure a model | [Models — bring your own](docs/MODELS.md) |
| See the dictation copilot turn speech into a project-grounded task | [The Dictation Copilot](docs/DICTATION_COPILOT.md) |
| Set up project-aware dictation for Codex / Claude | [Intelligent Typing Setup](docs/INTELLIGENT_TYPING_GUIDE.md) |
| See an on-desktop status while dictating into another app | [Desktop Presence](docs/INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status) |
| Review, correct, and replay past dictations | [Dictation journal, corrections & replay](docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay) |
| Use meeting mode and configure AI intelligence | [Meeting Mode Guide](docs/MEETING_MODE_GUIDE.md) |
| Wire up the AIPI-Lite companion device | [AIPI-Lite Developer Workflow](docs/AIPI_LITE_DEV_WORKFLOW.md) |
| Install Claude / Codex agent hooks | [Agent Hook Install](docs/AGENT_HOOK_INSTALL.md) |
| Understand what's stored and what can leave my machine | [Security & Privacy](docs/SECURITY.md) |

## Meeting intelligence plugins

When you record or save a meeting, HoldSpeak can turn the transcript into
structured, reviewable artifacts. A saved meeting flows through **multi-intent
routing (MIR)** — the transcript is scored for intent (architecture, delivery,
product, incident, comms), a plugin chain is selected for the active profile, and
each plugin calls your configured **OpenAI-compatible LLM** to produce a typed
artifact. Artifacts are persisted and rendered **read-only** in the web UI at
`/history` (diagrams as inline SVG; everything else as structured lists/tables).

Plugins run on **saved/recorded meetings**, not live, and are gated on an `llm`
capability — with no LLM endpoint configured they're skipped, not failed. Nothing
leaves your machine beyond the LLM endpoint you point at (local or LAN is fine).

HoldSpeak ships **14 built-in plugins**, all producing real LLM-backed artifacts:

| Plugin | Produces | Fires on (profile / intent) |
|---|---|---|
| `mermaid_architecture` | Architecture diagram (Mermaid → SVG) | architecture |
| `adr_drafter` | Architecture Decision Records | architecture |
| `requirements_extractor` | Requirements (functional / non-functional / constraint / acceptance) | architecture, default |
| `action_owner_enforcer` | Action items with owner/due-date gap flags | delivery, default |
| `milestone_planner` | Milestone plan (targets, deliverables, dependencies) | delivery |
| `dependency_mapper` | Dependency map (directed edges) | delivery |
| `decision_capture` | Decisions + open questions | default (every meeting) |
| `scope_guard` | Scope review (in-scope / out-of-scope / scope-creep) | product |
| `customer_signal_extractor` | Customer signals (request / pain / praise / churn-risk) | product |
| `incident_timeline` | Ordered incident timeline | incident |
| `runbook_delta` | Runbook changes (added / modified / removed) | incident |
| `risk_heatmap` | Risk register (impact / likelihood / mitigation / owner) | incident |
| `stakeholder_update_drafter` | Stakeholder update (headline + highlights / risks / next steps) | comms |
| `decision_announcement_drafter` | Decision announcements (title / audience / message) | comms |

Beyond read-only artifacts, plugins can also **propose actions**. An
**actuator** is the plugin system's third kind: instead of an artifact it proposes
an external side effect (file a ticket, post an update) that only happens after an
explicit, audited, **per-action human approval** — and what runs is exactly what
was previewed. Real **write connectors** (file a GitHub issue, POST to a webhook)
run behind a per-connector **permission manifest** so a connector can only do what
it declared, and proposals can be approved **live** during the meeting. Actuators
are **off by default** (a per-project gate + allow-list). See the
[Actuators](docs/PLUGIN_AUTHORING.md#actuators) section of the authoring guide.

Want to write your own? The [Plugin Authoring guide](docs/PLUGIN_AUTHORING.md)
walks the full contract — the `HostPlugin` protocol, the prompt → LLM → parse →
structured-output pattern, the `llm` capability gate, registering a renderer,
joining a chain, and the actuator approval flow. The design rationale lives in the
plugin RFC:
[`docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`](docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md).
For configuring meeting intelligence (endpoints, routing), see the
[Meeting Mode Guide](docs/MEETING_MODE_GUIDE.md).

## Configuration

Config file: `~/.config/holdspeak/config.json`

```json
{
  "hotkey": { "key": "alt_r", "display": "Right Option" },
  "model": { "name": "base", "warm_on_start": true, "backend": "auto" }
}
```

`model.backend` — `"auto"` picks MLX on Apple Silicon when available, otherwise `faster-whisper`. Override with `"mlx"` or `"faster-whisper"`.

Full configuration reference (meeting intel, dictation pipeline, cloud endpoints, MIR routing) is in the relevant guide docs above.

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup
(`uv`, the git hooks, the test command) and the commit-contract workflow. Recent
changes are tracked in [`CHANGELOG.md`](CHANGELOG.md).

## License

Licensed under the **Apache License 2.0** — see [`LICENSE`](LICENSE).
